"""
Core Topic Research agent.

Autonomy: FULL — acts and logs; no human checkpoint.

Input  (node.input_data): topic_area, description, learning_objectives, duration
Output: concepts, prerequisite_chain, coverage_warnings, suggested_module_count
"""

import json
from typing import Any, Dict

from agents.base import BaseAgent
from models import AutonomyLevel, TaskGraphNode

_DURATION_GUIDANCE = {
    "1hr talk":  "~2 hours total; max 3-4 concepts, surface level only",
    "half-day":  "~3-4 hours; 4-6 concepts, overview depth",
    "full-day":  "~6-7 hours; 6-8 concepts, moderate depth",
    "multi-day": "2-3 days; 8-12 concepts, deep coverage possible",
}


class ResearchAgent(BaseAgent):
    autonomy = AutonomyLevel.FULL

    async def run(self, node: TaskGraphNode, pipeline_id: str, **kwargs: Any) -> Dict[str, Any]:
        d = node.input_data
        duration_hint = _DURATION_GUIDANCE.get(d.get("duration", ""), "unknown duration")

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert curriculum designer and subject matter expert. "
                    "Produce a structured topic map for a course. "
                    "Return your response as a JSON object."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Produce a topic map for this course brief.\n\n"
                    f"Topic area: {d.get('topic_area')}\n"
                    f"Description: {d.get('description')}\n"
                    f"Learning objectives: {json.dumps(d.get('learning_objectives', []))}\n"
                    f"Duration: {d.get('duration')} ({duration_hint})\n\n"
                    "Return a JSON object with exactly these keys:\n"
                    "{\n"
                    '  "concepts": [\n'
                    '    {"name": "string", "importance": 1-5, "description": "one sentence",\n'
                    '     "subtopics": ["string"], "depth": "intro|overview|deep", "estimated_minutes": 0}\n'
                    "  ],\n"
                    '  "prerequisite_chain": [{"concept": "string", "required_before": ["string"]}],\n'
                    '  "coverage_warnings": ["string or empty list"],\n'
                    '  "suggested_module_count": 0\n'
                    "}\n\n"
                    "Order concepts by importance descending. Only include concepts achievable "
                    "within the duration. Flag any scope concern as a coverage_warning."
                ),
            },
        ]

        result = await self.call_llm_json(messages, temperature=0.3, max_tokens=2048)

        warnings = result.get("coverage_warnings", [])
        await self.log(
            pipeline_id=pipeline_id,
            node_id=node.id,
            node_type=node.type,
            action="Generated topic map",
            reasoning=(
                f"Identified {len(result.get('concepts', []))} concepts for "
                f"'{d.get('topic_area')}'. "
                + (f"Coverage warnings: {warnings}" if warnings else "No scope warnings.")
            ),
            confidence=0.9,
        )

        return result
