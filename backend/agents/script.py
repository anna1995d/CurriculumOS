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

        duration_min = module.get("duration_minutes", 30)
        # One section per ~12 minutes; speaker notes at ~120 words/min of section time.
        target_sections = max(2, round(duration_min / 12))
        words_per_section = max(300, round((duration_min / target_sections) * 120))

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert course designer and instructional writer. "
                    "You write verbatim instructor scripts — full sentences the instructor says out loud, "
                    "not slide bullets or brief notes. Think of it as a stage play script for a lecture: "
                    "every explanation, question asked to the audience, analogy, worked example, and "
                    "transition is written out in full. Bullet points are acceptable only inside "
                    "key_points arrays, never in speaker_notes. Return your response as a JSON object."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Write a detailed instructor script for this module.\n\n"
                    f"MODULE:\n"
                    f"  Title: {module.get('title')}\n"
                    f"  Duration: {duration_min} minutes\n"
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
                    f"DEPTH AND LENGTH REQUIREMENTS (strictly enforced):\n"
                    f"  - Create {target_sections} sections that together fill the full {duration_min} minutes.\n"
                    f"  - Each section's speaker_notes must be at least {words_per_section} words.\n"
                    f"  - speaker_notes is the verbatim script of what the instructor says — continuous "
                    f"prose, not a list. E.g.: 'Good morning everyone. Before we dive in, quick question "
                    f"for the room — has anyone here tried to...'. Include rhetorical questions, think-alouds, "
                    f"pauses for the audience, explicit time calls, and step-by-step walkthroughs.\n"
                    f"  - Insert an activity or engagement break at least once every {attention_span} minutes.\n"
                    f"    Activity descriptions must be detailed enough for a first-time instructor to run.\n"
                    f"  - examples[].content must be fully elaborated — not just a title.\n\n"
                    "Return a JSON object with exactly these keys:\n"
                    "{\n"
                    '  "module_id": "string",\n'
                    '  "module_title": "string",\n'
                    '  "total_duration_minutes": 0,\n'
                    '  "sections": [\n'
                    '    {\n'
                    '      "title": "string",\n'
                    '      "duration_minutes": 0,\n'
                    f'      "speaker_notes": "string — verbatim instructor prose, min {words_per_section} words",\n'
                    '      "key_points": ["string — 4-6 concise takeaway bullets"],\n'
                    '      "examples": [{"type": "analogy|case_study|demo|exercise", "content": "string — full elaborated example"}],\n'
                    '      "activity": {"type": "string", "description": "string — full runbook for instructor", "duration_minutes": 0} or null\n'
                    "    }\n"
                    "  ],\n"
                    '  "transition_in": "string — 2-3 sentences the instructor says to open this module",\n'
                    '  "transition_out": "string — 2-3 sentences to close and preview the next module",\n'
                    '  "materials_needed": ["string"]\n'
                    "}\n\n"
                    f"The script must be rich enough that a first-time instructor can deliver "
                    f"the full {duration_min} minutes by reading it. Do not truncate — write everything out."
                ),
            },
        ]

        result = await self.call_llm_json(messages, temperature=0.6, max_tokens=8000)

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
