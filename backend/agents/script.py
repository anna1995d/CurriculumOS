"""
Script Drafter agent — one instance per module, all run in parallel.

Autonomy: DRAFT — scripts feed directly into the reviewer layer without
a separate human approval checkpoint. The human sees scripts during conflict resolution.

Input  (node.input_data): module (dict from outline), audience_profile, topic_map
Output: module_id, module_title, total_duration_minutes, sections[], transition_in/out,
        materials_needed
"""

import json
from typing import Any, Dict

from agents.base import BaseAgent
from models import AutonomyLevel, TaskGraphNode


class ScriptAgent(BaseAgent):
    autonomy = AutonomyLevel.DRAFT

    async def run(self, node: TaskGraphNode, pipeline_id: str, **kwargs: Any) -> Dict[str, Any]:
        d = node.input_data
        module = d.get("module", {})
        audience = d.get("audience_profile", {})
        topic_map = d.get("topic_map", {})

        # Relevant concepts for this module
        all_concepts = topic_map.get("concepts", [])
        module_concepts = module.get("concepts_covered", [])
        relevant = [c for c in all_concepts if c.get("name") in module_concepts]
        if not relevant:
            relevant = all_concepts[:3]  # fallback: top 3 if no explicit match

        audience_summary = audience.get("profile_summary", "general professional audience")
        example_types = audience.get("recommended_example_types", ["real-world scenarios"])
        engagement = audience.get("engagement_strategies", ["interactive exercises"])
        attention_span = audience.get("attention_span_minutes", 20)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert course content writer who creates detailed, engaging lesson scripts. "
                    "Write for the instructor — this is a speaker guide, not a student handout. "
                    "Return your response as a JSON object."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Write a lesson script for this module.\n\n"
                    f"MODULE:\n"
                    f"  Title: {module.get('title')}\n"
                    f"  Duration: {module.get('duration_minutes')} minutes\n"
                    f"  Activity type: {module.get('activity_type', 'mixed')}\n"
                    f"  Learning objectives: {json.dumps(module.get('learning_objectives', []))}\n"
                    f"  Concepts to cover: {json.dumps(module_concepts)}\n\n"
                    f"AUDIENCE:\n"
                    f"  {audience_summary}\n"
                    f"  Attention span: ~{attention_span} min before needing a break or activity\n"
                    f"  Preferred examples: {json.dumps(example_types)}\n"
                    f"  Engagement strategies: {json.dumps(engagement)}\n\n"
                    f"CONCEPT DEPTH GUIDANCE:\n{json.dumps(relevant, indent=2)}\n\n"
                    f"CONTEXT:\n"
                    f"  Transition in: {module.get('transition_note', 'start of course')}\n\n"
                    "Return a JSON object with exactly these keys:\n"
                    "{\n"
                    '  "module_id": "string",\n'
                    '  "module_title": "string",\n'
                    '  "total_duration_minutes": 0,\n'
                    '  "sections": [\n'
                    '    {\n'
                    '      "title": "string",\n'
                    '      "duration_minutes": 0,\n'
                    '      "speaker_notes": "string — what the instructor says and does",\n'
                    '      "key_points": ["string"],\n'
                    '      "examples": [{"type": "analogy|case_study|demo|exercise", "content": "string"}],\n'
                    '      "activity": {"type": "string", "description": "string", "duration_minutes": 0} or null\n'
                    "    }\n"
                    "  ],\n"
                    '  "transition_in": "string — how this module connects to the previous one",\n'
                    '  "transition_out": "string — how to bridge to the next module",\n'
                    '  "materials_needed": ["string"]\n'
                    "}\n\n"
                    f"Target total duration: {module.get('duration_minutes')} minutes. "
                    "Include at least one activity or engagement break every "
                    f"{attention_span} minutes. Use concrete, specific examples appropriate for this audience."
                ),
            },
        ]

        result = await self.call_llm_json(messages, temperature=0.6, max_tokens=4000)

        # Ensure module_id is set
        result.setdefault("module_id", module.get("id", node.id))
        result.setdefault("module_title", module.get("title", "Unknown Module"))

        await self.log(
            pipeline_id=pipeline_id,
            node_id=node.id,
            node_type=node.type,
            action=f"Drafted script for '{result.get('module_title')}'",
            reasoning=(
                f"Script has {len(result.get('sections', []))} sections, "
                f"{result.get('total_duration_minutes', '?')} min total."
            ),
            confidence=0.8,
        )

        return result
