"""
Outline Generator agent.

Autonomy: DRAFT — presented to the human for approval before scripting begins.
Human checkpoint: user can reorder, edit, remove, or add modules.

Input  (node.input_data): topic_map, audience_profile, catalog_overlap, plus
                          the original brief fields (via orchestrator kwargs)
Output: modules list + pedagogical notes + awaiting_human flag
"""

import json
from typing import Any, Dict

from agents.base import BaseAgent
from models import AutonomyLevel, TaskGraphNode


class OutlineAgent(BaseAgent):
    autonomy = AutonomyLevel.DRAFT

    async def run(self, node: TaskGraphNode, pipeline_id: str, **kwargs: Any) -> Dict[str, Any]:
        d = node.input_data
        topic_map = d.get("topic_map", {})
        audience = d.get("audience_profile", {})
        overlap = d.get("catalog_overlap", {})

        # Pull brief fields passed through by orchestrator
        brief = d.get("brief", {})
        balance = brief.get("balance", d.get("balance", 0.5))
        duration = brief.get("duration", d.get("duration", "full-day"))
        objectives = brief.get("learning_objectives", d.get("learning_objectives", []))

        # Summarise overlap warnings for the prompt
        overlap_note = ""
        if overlap.get("max_overlap_score", 0) > 0:
            overlap_note = (
                f"Note: catalog search found up to {overlap.get('max_overlap_score')}% overlap "
                f"with existing courses. Reuse suggestions: "
                f"{json.dumps([r.get('reuse_suggestion') for r in overlap.get('reusable_modules', [])])}"
            )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert instructional designer creating a structured course outline. "
                    "Apply sound pedagogical principles: prerequisites before dependent concepts, "
                    "appropriate cognitive load per module, and a balance between conceptual and "
                    "hands-on content. Return your response as a JSON object."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Create a course outline from the following inputs.\n\n"
                    f"TOPIC MAP (concepts to cover):\n{json.dumps(topic_map, indent=2)}\n\n"
                    f"AUDIENCE PROFILE:\n{json.dumps(audience, indent=2)}\n\n"
                    f"COURSE PARAMETERS:\n"
                    f"  Duration: {duration}\n"
                    f"  Desired balance (0=conceptual, 1=hands-on): {balance}\n"
                    f"  Overall learning objectives: {json.dumps(objectives)}\n"
                    + (f"\nCATALOG NOTES:\n{overlap_note}\n" if overlap_note else "") +
                    "\nReturn a JSON object with exactly these keys:\n"
                    "{\n"
                    '  "modules": [\n'
                    '    {\n'
                    '      "id": "m1",\n'
                    '      "title": "string",\n'
                    '      "learning_objectives": ["string"],\n'
                    '      "duration_minutes": 0,\n'
                    '      "activity_type": "lecture|workshop|discussion|lab|mixed",\n'
                    '      "prerequisite_concepts": ["string — concepts taught in earlier modules"],\n'
                    '      "concepts_covered": ["string"],\n'
                    '      "transition_note": "how this connects to the next module"\n'
                    "    }\n"
                    "  ],\n"
                    '  "total_duration_minutes": 0,\n'
                    '  "pedagogical_notes": ["string — observations about the outline structure"],\n'
                    '  "pedagogical_warnings": ["string — issues found (cognitive overload, orphan '
                    'modules, balance mismatch); empty list if none"],\n'
                    '  "balance_achieved": 0.0\n'
                    "}\n\n"
                    "Self-check before returning:\n"
                    "1. No concept is used before it is introduced.\n"
                    "2. Each module maps to at least one overall learning objective.\n"
                    "3. Cognitive load per module is reasonable (max ~5 new concepts).\n"
                    "4. The balance_achieved value reflects the actual conceptual/hands-on ratio."
                ),
            },
        ]

        result = await self.call_llm_json(messages, temperature=0.4, max_tokens=3000)

        n_modules = len(result.get("modules", []))
        warnings = result.get("pedagogical_warnings", [])

        await self.log(
            pipeline_id=pipeline_id,
            node_id=node.id,
            node_type=node.type,
            action=f"Generated {n_modules}-module outline — awaiting human approval",
            reasoning=(
                f"Draft outline has {n_modules} modules, "
                f"{result.get('total_duration_minutes', '?')} min total. "
                + (f"Pedagogical warnings: {warnings}" if warnings else "No pedagogical warnings.")
            ),
            confidence=0.8,
        )

        result["awaiting_human"] = True
        return result
