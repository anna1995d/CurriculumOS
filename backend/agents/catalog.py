"""
Catalog Search agent.

Autonomy: FULL — but sets should_block_outline=True in output if overlap > 70%.
The orchestrator reads that flag and blocks/escalates accordingly.

Input  (node.input_data): topic_area, description, learning_objectives
Output: overlap_analysis, reusable_modules, max_overlap_score, should_block_outline, recommendation
"""

import json
from typing import Any, Dict

from agents.base import BaseAgent
from database import get_all_courses
from models import AutonomyLevel, TaskGraphNode

BLOCK_THRESHOLD = 70


class CatalogAgent(BaseAgent):
    autonomy = AutonomyLevel.FULL

    async def run(self, node: TaskGraphNode, pipeline_id: str, **kwargs: Any) -> Dict[str, Any]:
        d = node.input_data

        # Load catalog fresh from DB
        catalog = await get_all_courses()

        # Build a compact catalog summary for the prompt
        catalog_summary = []
        for course in catalog:
            modules = [m["title"] for m in course.get("modules", [])]
            catalog_summary.append({
                "id": course["id"],
                "title": course["title"],
                "topic_area": course["topic_area"],
                "audience": course["audience"],
                "duration": course["duration"],
                "modules": modules,
            })

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a curriculum strategist. Compare a new course proposal against an "
                    "existing catalog and identify overlaps, reuse opportunities, and duplication risks. "
                    "Return your response as a JSON object."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Compare this new course proposal against the existing catalog.\n\n"
                    f"NEW COURSE:\n"
                    f"  Topic area: {d.get('topic_area')}\n"
                    f"  Description: {d.get('description')}\n"
                    f"  Learning objectives: {json.dumps(d.get('learning_objectives', []))}\n\n"
                    f"EXISTING CATALOG:\n{json.dumps(catalog_summary, indent=2)}\n\n"
                    "Return a JSON object with exactly these keys:\n"
                    "{\n"
                    '  "overlap_analysis": [\n'
                    '    {"course_id": 0, "course_title": "string",\n'
                    '     "overlap_score": 0-100,\n'
                    '     "overlapping_topics": ["string"],\n'
                    '     "overlap_reason": "string"}\n'
                    "  ],\n"
                    '  "reusable_modules": [\n'
                    '    {"course_id": 0, "module_title": "string",\n'
                    '     "relevance": "string", "reuse_suggestion": "string"}\n'
                    "  ],\n"
                    '  "max_overlap_score": 0,\n'
                    '  "is_likely_duplicate": false,\n'
                    '  "recommendation": "string — what to do given the overlap findings"\n'
                    "}\n\n"
                    "Score overlap_score 0-100: 0=no overlap, 100=identical content.\n"
                    "Only include courses with overlap_score > 0."
                ),
            },
        ]

        result = await self.call_llm_json(messages, temperature=0.2, max_tokens=2000)

        max_score = result.get("max_overlap_score", 0)
        should_block = max_score > BLOCK_THRESHOLD
        result["should_block_outline"] = should_block

        if should_block:
            result["awaiting_human"] = True
            action = f"Catalog overlap {max_score}% exceeds threshold — outline blocked, escalating to human"
            confidence = 0.95
        else:
            action = f"Catalog search complete — max overlap {max_score}%"
            confidence = 0.9

        await self.log(
            pipeline_id=pipeline_id,
            node_id=node.id,
            node_type=node.type,
            action=action,
            reasoning=(
                result.get("recommendation", "")
                + (f" Blocking outline: {should_block}." if should_block else "")
            ),
            confidence=confidence,
        )

        return result
