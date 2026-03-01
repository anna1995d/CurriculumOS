"""
Conflict Resolution agent.

Autonomy: ESCALATE — merges agreements; explicitly refuses to resolve subjective
disagreements; surfaces options for the human.

Input  (node.input_data): review_technical, review_pedagogy, review_business (all dicts)
Output: module_id, agreements[], disagreements[], summary + awaiting_human flag

Conflict classification:
  factual    — one reviewer is objectively correct → AI resolves
  priority   — agree on fact, disagree on importance → AI surfaces trade-off
  subjective — different values or perspectives → AI explicitly refuses to decide
"""

import json
from typing import Any, Dict

from agents.base import BaseAgent
from models import AutonomyLevel, TaskGraphNode


class ConflictAgent(BaseAgent):
    autonomy = AutonomyLevel.ESCALATE

    async def run(self, node: TaskGraphNode, pipeline_id: str, **kwargs: Any) -> Dict[str, Any]:
        d = node.input_data
        tech = d.get("review_technical", {})
        ped = d.get("review_pedagogy", {})
        biz = d.get("review_business", {})

        module_id = tech.get("module_id") or ped.get("module_id") or biz.get("module_id") or node.id

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a conflict resolution facilitator for an AI course development system. "
                    "You have received three independent reviews of a lesson script. "
                    "Your job is to:\n"
                    "  1. Identify where all reviewers AGREE and merge into unified recommendations.\n"
                    "  2. Identify where reviewers DISAGREE and classify each disagreement:\n"
                    "     - factual: one reviewer is objectively correct (resolve it yourself)\n"
                    "     - priority: same fact, different importance (surface the trade-off)\n"
                    "     - subjective: different values/perspectives (explicitly refuse to decide)\n"
                    "  3. For priority/subjective disagreements, generate 2-3 concrete human decision options.\n"
                    "  4. NEVER pretend to resolve a subjective disagreement. Name the tension and step back.\n"
                    "Return your response as a JSON object."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Analyse these three reviews of module '{module_id}' and produce a conflict report.\n\n"
                    f"TECHNICAL REVIEW (verdict: {tech.get('verdict', 'unknown')}):\n"
                    f"Findings: {json.dumps(tech.get('findings', []), indent=2)}\n"
                    f"Reasoning: {tech.get('reasoning', '')}\n\n"
                    f"PEDAGOGY REVIEW (verdict: {ped.get('verdict', 'unknown')}):\n"
                    f"Findings: {json.dumps(ped.get('findings', []), indent=2)}\n"
                    f"Reasoning: {ped.get('reasoning', '')}\n\n"
                    f"BUSINESS REVIEW (verdict: {biz.get('verdict', 'unknown')}):\n"
                    f"Findings: {json.dumps(biz.get('findings', []), indent=2)}\n"
                    f"Reasoning: {biz.get('reasoning', '')}\n\n"
                    "Return a JSON object with exactly these keys:\n"
                    "{\n"
                    '  "module_id": "string",\n'
                    '  "overall_verdicts": {"technical": "string", "pedagogy": "string", "business": "string"},\n'
                    '  "agreements": [\n'
                    '    {"topic": "string", "shared_recommendation": "string"}\n'
                    "  ],\n"
                    '  "disagreements": [\n'
                    '    {\n'
                    '      "topic": "string",\n'
                    '      "positions": {"technical": "string", "pedagogy": "string", "business": "string"},\n'
                    '      "conflict_type": "factual | priority | subjective",\n'
                    '      "ai_resolution": "string or null — only set for factual conflicts",\n'
                    '      "ai_assessment": "string — why the AI cannot resolve this (for priority/subjective)",\n'
                    '      "human_options": ["string — concrete decision option for the human"]\n'
                    '    }\n'
                    "  ],\n"
                    '  "summary": "string — brief overall assessment of the three reviews"\n'
                    "}\n\n"
                    "Important: if there are no disagreements, return an empty disagreements list. "
                    "For factual conflicts you resolve, set ai_resolution and leave human_options empty. "
                    "For priority/subjective, leave ai_resolution null and provide 2-3 human_options."
                ),
            },
        ]

        result = await self.call_llm_json(messages, temperature=0.2, max_tokens=2000)
        result["module_id"] = module_id

        n_agree = len(result.get("agreements", []))
        n_disagree = len(result.get("disagreements", []))
        needs_human = n_disagree > 0

        await self.log(
            pipeline_id=pipeline_id,
            node_id=node.id,
            node_type=node.type,
            action=(
                f"Conflict analysis: {n_agree} agreements, {n_disagree} disagreements"
                + (" — escalating to human" if needs_human else " — all resolved")
            ),
            reasoning=result.get("summary", ""),
            confidence=0.85,
        )

        # Always escalate to human so they can review the full report
        result["awaiting_human"] = True
        return result
