"""
Pipeline Orchestrator.

Responsibilities:
  1. generate_initial_graph()  — deterministic 5-node graph from a CourseBrief.
  2. generate_module_graph()   — dynamic per-module nodes added after outline approval.
  3. PipelineOrchestrator.run() — full async execution engine:
       - dispatches agents in dependency order
       - runs parallel layers with asyncio.gather
       - pauses at AWAITING_HUMAN nodes via asyncio.Event (events.py)
       - persists state and broadcasts WebSocket updates after every status change
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List

from agents.audience import AudienceAgent
from agents.catalog import CatalogAgent
from agents.conflict import ConflictAgent
from agents.outline import OutlineAgent
from agents.research import ResearchAgent
from agents.review_business import BusinessReviewAgent
from agents.review_pedagogy import PedagogyReviewAgent
from agents.review_technical import TechnicalReviewAgent
from agents.script import ScriptAgent
from database import get_pipeline, update_pipeline_nodes, update_pipeline_status
from events import get_node_event
from models import (
    AutonomyLevel,
    CourseBrief,
    NodeStatus,
    NodeType,
    TaskGraphNode,
)
from ws_manager import ws_manager

# ─── Fixed node IDs for the initial graph ─────────────────────────────────────

NODE_ORCHESTRATOR = "node-orchestrator"
NODE_RESEARCH = "node-research"
NODE_AUDIENCE = "node-audience"
NODE_CATALOG = "node-catalog"
NODE_OUTLINE = "node-outline"


# ─── Graph generation ─────────────────────────────────────────────────────────


def generate_initial_graph(brief: CourseBrief) -> List[TaskGraphNode]:
    """Return the fixed 5-node graph for any brief (orchestrator through outline)."""
    return [
        TaskGraphNode(
            id=NODE_ORCHESTRATOR,
            type=NodeType.ORCHESTRATOR,
            label="Orchestrator",
            status=NodeStatus.COMPLETED,
            autonomy=AutonomyLevel.FULL,
            input_data=brief.model_dump(mode="json"),
            dependencies=[],
            reasoning=(
                "Analyzed the course brief and generated the pipeline graph. "
                "Human reviews and approves the plan before execution begins."
            ),
        ),
        TaskGraphNode(
            id=NODE_RESEARCH,
            type=NodeType.RESEARCH,
            label="Core Topic Research",
            autonomy=AutonomyLevel.FULL,
            input_data={
                "topic_area": brief.topic_area,
                "description": brief.description,
                "learning_objectives": brief.learning_objectives,
                "duration": brief.duration,
            },
            dependencies=[NODE_ORCHESTRATOR],
            reasoning="Generates topic map — key concepts, subtopics, prerequisite chain.",
        ),
        TaskGraphNode(
            id=NODE_AUDIENCE,
            type=NodeType.AUDIENCE,
            label="Audience Analysis",
            autonomy=AutonomyLevel.RECOMMEND,
            input_data={
                "audience": brief.audience,
                "prerequisites": brief.prerequisites,
                "class_size": brief.class_size,
                "balance": brief.balance,
            },
            dependencies=[NODE_ORCHESTRATOR],
            reasoning="Generates audience profile. Requires human confirmation before use downstream.",
        ),
        TaskGraphNode(
            id=NODE_CATALOG,
            type=NodeType.CATALOG,
            label="Catalog Search",
            autonomy=AutonomyLevel.FULL,
            input_data={
                "topic_area": brief.topic_area,
                "description": brief.description,
                "learning_objectives": brief.learning_objectives,
            },
            dependencies=[NODE_ORCHESTRATOR],
            reasoning="Searches existing catalog for overlaps. Blocks outline if overlap > 70%.",
        ),
        TaskGraphNode(
            id=NODE_OUTLINE,
            type=NodeType.OUTLINE,
            label="Outline Generator",
            autonomy=AutonomyLevel.DRAFT,
            dependencies=[NODE_RESEARCH, NODE_AUDIENCE, NODE_CATALOG],
            reasoning="Generates structured course outline. Requires human approval before scripting.",
        ),
    ]


def generate_module_graph(outline_output: Dict[str, Any]) -> List[TaskGraphNode]:
    """
    Generate per-module nodes after the outline is approved.
    For each module: script → (tech + ped + biz reviews in parallel) → conflict.
    """
    modules = outline_output.get("modules", [])
    new_nodes: List[TaskGraphNode] = []

    for i, module in enumerate(modules):
        mid = module.get("id", f"module-{i}")
        title = module.get("title", f"Module {i + 1}")

        script_id = f"node-script-{mid}"
        tech_id = f"node-review-tech-{mid}"
        ped_id = f"node-review-ped-{mid}"
        biz_id = f"node-review-biz-{mid}"
        conflict_id = f"node-conflict-{mid}"

        new_nodes += [
            TaskGraphNode(
                id=script_id, type=NodeType.SCRIPT,
                label=f"Script: {title}", autonomy=AutonomyLevel.DRAFT,
                input_data={"module": module}, dependencies=[NODE_OUTLINE],
                reasoning=f"Drafts lesson script for '{title}'.",
            ),
            TaskGraphNode(
                id=tech_id, type=NodeType.REVIEW_TECHNICAL,
                label=f"Technical Review: {title}", autonomy=AutonomyLevel.ADVISORY,
                dependencies=[script_id],
                reasoning="Reviews script for factual accuracy and correct terminology.",
            ),
            TaskGraphNode(
                id=ped_id, type=NodeType.REVIEW_PEDAGOGY,
                label=f"Pedagogy Review: {title}", autonomy=AutonomyLevel.ADVISORY,
                dependencies=[script_id],
                reasoning="Reviews script for cognitive load, engagement, and clarity.",
            ),
            TaskGraphNode(
                id=biz_id, type=NodeType.REVIEW_BUSINESS,
                label=f"Business Review: {title}", autonomy=AutonomyLevel.ADVISORY,
                dependencies=[script_id],
                reasoning="Reviews script for objective alignment, ROI, and scope.",
            ),
            TaskGraphNode(
                id=conflict_id, type=NodeType.CONFLICT,
                label=f"Conflict Resolution: {title}", autonomy=AutonomyLevel.ESCALATE,
                dependencies=[tech_id, ped_id, biz_id],
                reasoning="Merges agreements; surfaces disagreements for human decision.",
            ),
        ]

    return new_nodes


# ─── Execution engine ─────────────────────────────────────────────────────────


class PipelineOrchestrator:
    """
    Drives the full pipeline lifecycle for one pipeline_id.

    Instantiate, then await run() as a background asyncio task.
    Requires ws_manager to be importable from ws_manager.py.
    """

    # Class-level lock registry — one lock per pipeline
    _locks: Dict[str, asyncio.Lock] = {}

    def __init__(self, pipeline_id: str, brief: CourseBrief) -> None:
        self.pipeline_id = pipeline_id
        self.brief = brief
        if pipeline_id not in self._locks:
            self._locks[pipeline_id] = asyncio.Lock()
        self._lock = self._locks[pipeline_id]

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _broadcast(self, message: Dict[str, Any]) -> None:
        await ws_manager.broadcast(self.pipeline_id, message)

    async def _save_node_state(self, node_id: str, updates: Dict[str, Any]) -> None:
        """Fetch → patch → save. Protected by per-pipeline lock."""
        async with self._lock:
            pipeline = await get_pipeline(self.pipeline_id)
            nodes = pipeline["nodes"]
            for n in nodes:
                if n["id"] == node_id:
                    n.update(updates)
                    break
            await update_pipeline_nodes(self.pipeline_id, json.dumps(nodes))

    async def _get_node(self, node_id: str) -> Dict[str, Any]:
        pipeline = await get_pipeline(self.pipeline_id)
        return next((n for n in pipeline["nodes"] if n["id"] == node_id), {})

    async def _wait_for_human(self, node_id: str) -> None:
        """
        Block until the human approves/edits/decides on this node.
        Returns immediately if the node is already marked completed
        (handles the case where approval arrives before we start waiting).
        """
        node = await self._get_node(node_id)
        if node.get("status") in ("completed", NodeStatus.COMPLETED):
            return
        await get_node_event(self.pipeline_id, node_id).wait()

    async def _run_node(self, node_id: str, agent: Any, **extra_inputs: Any) -> None:
        """
        Execute one agent:
          1. Merge extra_inputs into the node's input_data and mark RUNNING.
          2. Call agent.run().
          3. Read awaiting_human flag from output → set AWAITING_HUMAN or COMPLETED.
          4. Persist and broadcast on every transition.
        Errors set the node to ERROR and re-raise so asyncio.gather surfaces them.
        """
        # Load current node dict
        pipeline = await get_pipeline(self.pipeline_id)
        node_dict = next((n for n in pipeline["nodes"] if n["id"] == node_id), None)
        if node_dict is None:
            raise ValueError(f"Node {node_id} not found in pipeline {self.pipeline_id}")

        # Merge any extra context the orchestrator is passing
        if extra_inputs:
            node_dict["input_data"] = {**node_dict.get("input_data", {}), **extra_inputs}

        await self._save_node_state(node_id, {
            "input_data": node_dict["input_data"],
            "status": NodeStatus.RUNNING,
            "started_at": datetime.utcnow().isoformat(),
        })
        await self._broadcast({"type": "node_status_changed", "node_id": node_id, "status": "running"})

        node = TaskGraphNode(**node_dict)
        node.status = NodeStatus.RUNNING

        try:
            output = await agent.run(node, self.pipeline_id)
            awaiting = output.pop("awaiting_human", False)
            new_status = NodeStatus.AWAITING_HUMAN if awaiting else NodeStatus.COMPLETED

            updates: Dict[str, Any] = {"status": new_status, "output_data": output}
            if new_status == NodeStatus.COMPLETED:
                updates["completed_at"] = datetime.utcnow().isoformat()

            await self._save_node_state(node_id, updates)
            await self._broadcast({
                "type": "node_status_changed",
                "node_id": node_id,
                "status": new_status.value,
                "output_data": output,
            })

        except Exception as exc:
            await self._save_node_state(node_id, {
                "status": NodeStatus.ERROR,
                "output_data": {"error": str(exc)},
                "completed_at": datetime.utcnow().isoformat(),
            })
            await self._broadcast({
                "type": "node_status_changed",
                "node_id": node_id,
                "status": "error",
                "error": str(exc),
            })
            raise

    # ── Main execution loop ───────────────────────────────────────────────────

    async def run(self) -> None:
        """
        Full pipeline execution flow:

          Layer 2 (parallel): research + audience + catalog
            ↓ wait for audience human confirmation
            ↓ if catalog blocks → set outline BLOCKED, wait for catalog decision
          Layer 3: outline
            ↓ wait for outline human approval
            ↓ expand graph with per-module nodes
          Layer 4 (parallel): all script agents
          Layer 5 (parallel): all reviewers (3 × N)
          Layer 6 (parallel): all conflict resolvers
            ↓ wait for all conflict human decisions
          Pipeline complete
        """
        try:
            # ── Layer 2: parallel research + audience + catalog ────────────────
            await asyncio.gather(
                self._run_node(NODE_RESEARCH, ResearchAgent()),
                self._run_node(NODE_AUDIENCE, AudienceAgent()),
                self._run_node(NODE_CATALOG, CatalogAgent()),
            )

            # Wait for audience human confirmation (RECOMMEND node always pauses)
            await self._wait_for_human(NODE_AUDIENCE)

            # Check if catalog flagged a blocking overlap
            catalog_node = await self._get_node(NODE_CATALOG)
            catalog_output = catalog_node.get("output_data", {})
            if catalog_output.get("should_block_outline"):
                # Mark outline as BLOCKED and wait for human to clear catalog
                await self._save_node_state(NODE_OUTLINE, {
                    "status": NodeStatus.BLOCKED,
                    "blocked_by": NODE_CATALOG,
                })
                await self._broadcast({
                    "type": "node_status_changed",
                    "node_id": NODE_OUTLINE,
                    "status": "blocked",
                })
                # Catalog is already AWAITING_HUMAN — wait for the human's decision
                await self._wait_for_human(NODE_CATALOG)
                # Restore outline to PENDING so it can run
                await self._save_node_state(NODE_OUTLINE, {
                    "status": NodeStatus.PENDING,
                    "blocked_by": None,
                })

            # ── Layer 3: outline ───────────────────────────────────────────────
            research_output = (await self._get_node(NODE_RESEARCH)).get("output_data", {})
            audience_output = (await self._get_node(NODE_AUDIENCE)).get("output_data", {})

            await self._run_node(
                NODE_OUTLINE,
                OutlineAgent(),
                topic_map=research_output,
                audience_profile=audience_output,
                catalog_overlap=catalog_output,
                brief=self.brief.model_dump(mode="json"),
            )

            # Wait for outline human approval (DRAFT node pauses)
            await self._wait_for_human(NODE_OUTLINE)

            # ── Expand graph with per-module nodes ────────────────────────────
            outline_node = await self._get_node(NODE_OUTLINE)
            outline_output = outline_node.get("output_data", {})
            module_nodes = generate_module_graph(outline_output)

            if not module_nodes:
                # Outline produced no modules — complete with a warning
                await update_pipeline_status(
                    self.pipeline_id, "completed",
                    completed_at=datetime.utcnow().isoformat(),
                )
                await self._broadcast({"type": "pipeline_completed", "warning": "Outline had no modules."})
                return

            # Append new nodes to the pipeline
            pipeline = await get_pipeline(self.pipeline_id)
            all_nodes = pipeline["nodes"] + [n.model_dump(mode="json") for n in module_nodes]
            async with self._lock:
                await update_pipeline_nodes(self.pipeline_id, json.dumps(all_nodes))
            await self._broadcast({
                "type": "graph_expanded",
                "new_nodes": [n.model_dump(mode="json") for n in module_nodes],
            })

            modules = outline_output.get("modules", [])
            module_ids = [m.get("id", f"module-{i}") for i, m in enumerate(modules)]

            # ── Layer 4: all scripts in parallel ──────────────────────────────
            await asyncio.gather(*[
                self._run_node(
                    f"node-script-{mid}",
                    ScriptAgent(),
                    audience_profile=audience_output,
                    topic_map=research_output,
                )
                for mid in module_ids
            ])

            # ── Layer 5: all reviewers in parallel (3 × N) ───────────────────
            brief_dict = self.brief.model_dump(mode="json")
            reviewer_tasks = []
            for mid in module_ids:
                script_output = (await self._get_node(f"node-script-{mid}")).get("output_data", {})
                reviewer_tasks += [
                    self._run_node(f"node-review-tech-{mid}", TechnicalReviewAgent(),
                                   script=script_output, topic_map=research_output),
                    self._run_node(f"node-review-ped-{mid}", PedagogyReviewAgent(),
                                   script=script_output, audience_profile=audience_output,
                                   outline=outline_output),
                    self._run_node(f"node-review-biz-{mid}", BusinessReviewAgent(),
                                   script=script_output, catalog_overlap=catalog_output,
                                   brief=brief_dict),
                ]
            await asyncio.gather(*reviewer_tasks)

            # ── Layer 6: all conflict resolvers in parallel ───────────────────
            conflict_tasks = []
            for mid in module_ids:
                tech_out = (await self._get_node(f"node-review-tech-{mid}")).get("output_data", {})
                ped_out = (await self._get_node(f"node-review-ped-{mid}")).get("output_data", {})
                biz_out = (await self._get_node(f"node-review-biz-{mid}")).get("output_data", {})
                conflict_tasks.append(
                    self._run_node(f"node-conflict-{mid}", ConflictAgent(),
                                   review_technical=tech_out,
                                   review_pedagogy=ped_out,
                                   review_business=biz_out)
                )
            await asyncio.gather(*conflict_tasks)

            # Wait for all conflict human decisions
            await asyncio.gather(*[
                self._wait_for_human(f"node-conflict-{mid}") for mid in module_ids
            ])

            # ── Done ──────────────────────────────────────────────────────────
            await update_pipeline_status(
                self.pipeline_id, "completed",
                completed_at=datetime.utcnow().isoformat(),
            )
            await self._broadcast({"type": "pipeline_completed"})

        except Exception as exc:
            await update_pipeline_status(self.pipeline_id, "failed")
            await self._broadcast({"type": "pipeline_error", "error": str(exc)})
            raise
