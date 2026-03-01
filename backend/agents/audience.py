"""
Audience Analysis agent.

Autonomy: RECOMMEND — output is presented to the human for confirmation.
Human checkpoint: "Does this match your understanding of this audience?"

Input  (node.input_data): audience, prerequisites, class_size, balance
Output: audience profile dict + awaiting_human flag
"""

import json
from typing import Any, Dict

from agents.base import BaseAgent
from models import AutonomyLevel, TaskGraphNode

_BALANCE_LABEL = {
    (0.0, 0.3): "mostly conceptual / lecture-based",
    (0.3, 0.7): "balanced mix of theory and hands-on",
    (0.7, 1.01): "heavily hands-on / workshop style",
}


def _balance_label(balance: float) -> str:
    for (lo, hi), label in _BALANCE_LABEL.items():
        if lo <= balance < hi:
            return label
    return "balanced"


class AudienceAgent(BaseAgent):
    autonomy = AutonomyLevel.RECOMMEND

    async def run(self, node: TaskGraphNode, pipeline_id: str, **kwargs: Any) -> Dict[str, Any]:
        d = node.input_data
        balance = d.get("balance", 0.5)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert instructional designer specialising in audience analysis. "
                    "Generate a realistic, specific audience profile for a course. "
                    "Return your response as a JSON object."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Generate an audience profile for this course.\n\n"
                    f"Audience type: {d.get('audience')}\n"
                    f"Stated prerequisites: {json.dumps(d.get('prerequisites', []))}\n"
                    f"Class size: {d.get('class_size')}\n"
                    f"Desired balance: {balance} ({_balance_label(balance)})\n\n"
                    "Return a JSON object with exactly these keys:\n"
                    "{\n"
                    '  "profile_summary": "2-3 sentence description of this audience",\n'
                    '  "assumed_knowledge": ["string — what they already know"],\n'
                    '  "knowledge_gaps": ["string — what they likely lack"],\n'
                    '  "pain_points": ["string — frustrations or fears relevant to this topic"],\n'
                    '  "preferred_modalities": ["string — e.g. case studies, live demos, exercises"],\n'
                    '  "attention_span_minutes": 0,\n'
                    '  "recommended_example_types": ["string — types of examples that resonate"],\n'
                    '  "engagement_strategies": ["string — how to keep this audience engaged"],\n'
                    '  "red_flags": ["string — common misconceptions to address proactively; empty if none"]\n'
                    "}\n\n"
                    "Be specific to this audience type — avoid generic advice."
                ),
            },
        ]

        result = await self.call_llm_json(messages, temperature=0.5, max_tokens=1500)

        await self.log(
            pipeline_id=pipeline_id,
            node_id=node.id,
            node_type=node.type,
            action="Generated audience profile — awaiting human confirmation",
            reasoning=(
                f"Produced audience profile for '{d.get('audience')}' learners. "
                "Flagged for human review before use downstream (RECOMMEND autonomy)."
            ),
            confidence=0.75,
        )

        result["awaiting_human"] = True
        return result
