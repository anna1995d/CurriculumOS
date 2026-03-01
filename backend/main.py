"""
CurriculumOS — FastAPI backend entry point.

Startup: initializes SQLite schema + seeds dummy catalog.

Changes from scaffolding:
  • ConnectionManager moved to ws_manager.py (shared with orchestrator).
  • start_pipeline launches PipelineOrchestrator.run() as a background asyncio task.
  • approve/edit/decide endpoints call signal_node_ready() to unblock the orchestrator.
  • chat endpoint implemented with per-node LLM context injection.
"""

import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL
from database import (
    create_pipeline,
    get_all_courses,
    get_decision_log,
    get_pipeline,
    init_db_sync,
    log_decision,
    update_pipeline_nodes,
    update_pipeline_status,
)
from dummy_catalog import seed_catalog
from events import signal_node_ready
from models import (
    BriefSubmitRequest,
    BriefSubmitResponse,
    ChatRequest,
    CourseBrief,
    HumanApproveRequest,
    HumanDecideRequest,
    HumanEditRequest,
    NodeStatus,
)
from orchestrator import PipelineOrchestrator, generate_initial_graph
from ws_manager import ws_manager


# ─── Startup ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db_sync()
    seed_catalog()
    yield


# ─── App ──────────────────────────────────────────────────────────────────────


app = FastAPI(
    title="CurriculumOS API",
    description=(
        "AI-powered course development pipeline with a transparent, "
        "human-in-the-loop agent graph."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Helpers ──────────────────────────────────────────────────────────────────


async def _get_pipeline_or_404(pipeline_id: str) -> Dict[str, Any]:
    pipeline = await get_pipeline(pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline


def _find_node(nodes: list, node_id: str) -> Dict[str, Any]:
    node = next((n for n in nodes if n["id"] == node_id), None)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


# ─── Routes ───────────────────────────────────────────────────────────────────


@app.post("/api/brief", response_model=BriefSubmitResponse)
async def submit_brief(body: BriefSubmitRequest):
    """
    Accept a completed course brief, generate the initial task graph,
    persist the pipeline, and return a pipeline_id.
    """
    pipeline_id = str(uuid.uuid4())
    brief = body.brief

    nodes = generate_initial_graph(brief)
    nodes_json = json.dumps([n.model_dump(mode="json") for n in nodes])

    await create_pipeline(pipeline_id=pipeline_id, brief_json=brief.model_dump_json())
    await update_pipeline_nodes(pipeline_id, nodes_json)

    await log_decision(
        pipeline_id=pipeline_id,
        node_id="node-orchestrator",
        node_type="orchestrator",
        action="Generated initial task graph",
        reasoning=(
            f"Analyzed brief for '{brief.title}' and created {len(nodes)} pipeline nodes. "
            "Awaiting user review and approval before execution starts."
        ),
        confidence=1.0,
        autonomy_level="full",
    )

    return BriefSubmitResponse(
        pipeline_id=pipeline_id,
        message=(
            f"Pipeline created with {len(nodes)} nodes. "
            "Review the graph and click Start to begin execution."
        ),
    )


@app.get("/api/pipeline/{pipeline_id}")
async def get_pipeline_state(pipeline_id: str):
    """Return the full pipeline state: brief, all nodes, and status."""
    return await _get_pipeline_or_404(pipeline_id)


@app.post("/api/pipeline/{pipeline_id}/start")
async def start_pipeline(pipeline_id: str):
    """
    Transition the pipeline to 'running' and launch the orchestrator
    as a background asyncio task.
    """
    pipeline = await _get_pipeline_or_404(pipeline_id)

    if pipeline["status"] != "created":
        raise HTTPException(
            status_code=400,
            detail=f"Pipeline is already '{pipeline['status']}' and cannot be started again.",
        )

    await update_pipeline_status(
        pipeline_id,
        status="running",
        started_at=datetime.utcnow().isoformat(),
    )
    await ws_manager.broadcast(
        pipeline_id, {"type": "pipeline_started", "pipeline_id": pipeline_id}
    )

    # Reconstruct CourseBrief from stored JSON
    brief = CourseBrief(**pipeline["brief"])

    # Launch orchestrator as a fire-and-forget background task
    orchestrator = PipelineOrchestrator(pipeline_id=pipeline_id, brief=brief)
    asyncio.create_task(orchestrator.run())

    return {"message": "Pipeline started", "pipeline_id": pipeline_id}


@app.get("/api/node/{node_id}")
async def get_node(
    node_id: str,
    pipeline_id: str = Query(..., description="The pipeline this node belongs to"),
):
    """Return a single node's full detail including output_data."""
    pipeline = await _get_pipeline_or_404(pipeline_id)
    return _find_node(pipeline["nodes"], node_id)


@app.post("/api/node/{node_id}/approve")
async def approve_node(node_id: str, body: HumanApproveRequest):
    """Human approves a DRAFT or RECOMMEND node without changes."""
    pipeline = await _get_pipeline_or_404(body.pipeline_id)
    nodes = pipeline["nodes"]
    node = _find_node(nodes, node_id)

    node["status"] = NodeStatus.COMPLETED
    node["completed_at"] = datetime.utcnow().isoformat()

    await update_pipeline_nodes(body.pipeline_id, json.dumps(nodes))
    await log_decision(
        pipeline_id=body.pipeline_id,
        node_id=node_id,
        node_type=node["type"],
        action="Human approved node output",
        reasoning="User reviewed the output and approved without changes.",
        confidence=1.0,
        autonomy_level=node["autonomy"],
        human_override=True,
        human_decision="approved",
    )
    await ws_manager.broadcast(
        body.pipeline_id, {"type": "node_approved", "node_id": node_id}
    )

    # Unblock the orchestrator
    signal_node_ready(body.pipeline_id, node_id)

    return {"message": "Node approved", "node_id": node_id}


@app.post("/api/node/{node_id}/edit")
async def edit_node(node_id: str, body: HumanEditRequest):
    """Human edits a node's output_data and approves the revised version."""
    pipeline = await _get_pipeline_or_404(body.pipeline_id)
    nodes = pipeline["nodes"]
    node = _find_node(nodes, node_id)

    node["output_data"] = body.edited_output
    node["status"] = NodeStatus.COMPLETED
    node["completed_at"] = datetime.utcnow().isoformat()

    await update_pipeline_nodes(body.pipeline_id, json.dumps(nodes))
    await log_decision(
        pipeline_id=body.pipeline_id,
        node_id=node_id,
        node_type=node["type"],
        action="Human edited and approved node output",
        reasoning="User made changes to the AI's output before approving.",
        confidence=1.0,
        autonomy_level=node["autonomy"],
        human_override=True,
        human_decision="edited_and_approved",
    )
    await ws_manager.broadcast(
        body.pipeline_id, {"type": "node_edited", "node_id": node_id}
    )

    # Unblock the orchestrator
    signal_node_ready(body.pipeline_id, node_id)

    return {"message": "Node edited and approved", "node_id": node_id}


@app.post("/api/node/{node_id}/decide")
async def decide_on_conflict(node_id: str, body: HumanDecideRequest):
    """Human records a decision on a conflict node."""
    pipeline = await _get_pipeline_or_404(body.pipeline_id)
    nodes = pipeline["nodes"]
    node = _find_node(nodes, node_id)

    if body.decisions:
        node["output_data"]["human_decisions"] = body.decisions
        summary = f"{len(body.decisions)} disagreement(s) resolved"
    else:
        node["output_data"]["human_decision"] = body.decision
        summary = body.decision or "resolved"

    node["status"] = NodeStatus.COMPLETED
    node["completed_at"] = datetime.utcnow().isoformat()

    await update_pipeline_nodes(body.pipeline_id, json.dumps(nodes))
    await log_decision(
        pipeline_id=body.pipeline_id,
        node_id=node_id,
        node_type=node["type"],
        action="Human resolved conflict",
        reasoning=summary,
        confidence=1.0,
        autonomy_level=node["autonomy"],
        human_override=True,
        human_decision=summary,
    )
    await ws_manager.broadcast(
        body.pipeline_id, {"type": "conflict_resolved", "node_id": node_id}
    )

    # Unblock the orchestrator
    signal_node_ready(body.pipeline_id, node_id)

    return {"message": "Decision recorded", "node_id": node_id}


@app.get("/api/log/{pipeline_id}")
async def get_log(pipeline_id: str):
    """Return all decision log entries for a pipeline, newest first."""
    entries = await get_decision_log(pipeline_id)
    return {"pipeline_id": pipeline_id, "entries": entries}


@app.post("/api/chat/{node_id}")
async def chat_with_node(node_id: str, body: ChatRequest):
    """
    Free-form chat with any node's agent context.
    Injects the node's label, type, autonomy, input_data, output_data, and reasoning
    into the system prompt so the LLM answers with full node context.
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured.")

    pipeline = await _get_pipeline_or_404(body.pipeline_id)
    node = _find_node(pipeline["nodes"], node_id)

    system_prompt = (
        f"You are the '{node.get('label')}' agent in an AI course development pipeline.\n"
        f"Node type: {node.get('type')}\n"
        f"Autonomy level: {node.get('autonomy')}\n"
        f"Current status: {node.get('status')}\n"
        f"Your reasoning: {node.get('reasoning', 'Not provided')}\n\n"
        "Your input data:\n"
        f"{json.dumps(node.get('input_data', {}), indent=2)}\n\n"
        "Your output data:\n"
        f"{json.dumps(node.get('output_data', {}), indent=2)}\n\n"
        "Answer questions about your work. Be specific and reference your actual outputs. "
        "If asked to make changes, explain what you would do differently and why, "
        "but note that changes must be made through the edit endpoint."
    )

    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": body.message},
        ],
        temperature=0.7,
        max_tokens=1024,
    )

    return {
        "node_id": node_id,
        "node_label": node.get("label"),
        "response": response.choices[0].message.content,
    }


@app.get("/api/catalog")
async def get_catalog():
    """Return the full dummy course catalog for transparency."""
    courses = await get_all_courses()
    return {"courses": courses, "total": len(courses)}


# ─── WebSocket ────────────────────────────────────────────────────────────────


@app.websocket("/ws/pipeline/{pipeline_id}")
async def websocket_pipeline(websocket: WebSocket, pipeline_id: str):
    """
    Live pipeline updates. On connect, sends current pipeline state.
    Subsequent updates are pushed by the orchestrator via ws_manager.broadcast().
    """
    await ws_manager.connect(pipeline_id, websocket)
    try:
        pipeline = await get_pipeline(pipeline_id)
        if pipeline:
            await websocket.send_json({"type": "pipeline_state", "data": pipeline})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(pipeline_id, websocket)
