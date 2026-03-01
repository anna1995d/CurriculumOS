"""
Pedagogy Reviewer agent.

Autonomy: ADVISORY — flags issues; cannot modify the script.

Input  (node.input_data): script (dict), audience_profile (dict), outline (dict)
Output: reviewer_type, module_id, verdict, confidence, findings[], reasoning
"""

import json
from typing import Any, Dict

from agents.base import BaseAgent
from models import AutonomyLevel, TaskGraphNode


class PedagogyReviewAgent(BaseAgent):
    autonomy = AutonomyLevel.ADVISORY

    async def run(self, node: TaskGraphNode, pipeline_id: str, **kwargs: Any) -> Dict[str, Any]:
        d = node.input_data
        script = d.get("script", {})
        audience = d.get("audience_profile", {})
        outline = d.get("outline", {})

        module_id = script.get("module_id", node.id)
        module_title = script.get("module_title", "Unknown Module")

        attention_span = audience.get("attention_span_minutes", 20)
        knowledge_gaps = audience.get("knowledge_gaps", [])
        preferred = audience.get("preferred_modalities", [])

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an instructional designer and learning scientist. "
                    "Review course content for pedagogical effectiveness — cognitive load, "
                    "engagement, clarity, prerequisite flow, and activity quality. "
                    "You CANNOT modify the script — only flag issues. "
                    "Return your response as a JSON object."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Review this lesson script for pedagogical effectiveness.\n\n"
                    f"MODULE: {module_title}\n\n"
                    f"SCRIPT:\n{json.dumps(script, indent=2)}\n\n"
                    f"AUDIENCE CONTEXT:\n"
                    f"  Attention span: ~{attention_span} minutes\n"
                    f"  Knowledge gaps: {json.dumps(knowledge_gaps)}\n"
                    f"  Preferred modalities: {json.dumps(preferred)}\n\n"
                    f"OUTLINE CONTEXT (for flow):\n{json.dumps(outline, indent=2)}\n\n"
                    "Check for:\n"
                    "  1. Cognitive overload (too many new concepts in one section)\n"
                    "  2. Engagement gaps (long stretches without interaction)\n"
                    "  3. Prerequisites assumed but not yet taught\n"
                    "  4. Unclear explanations for this audience's knowledge level\n"
                    "  5. Activities that are mismatched to learning objectives\n"
                    "  6. Weak or missing transitions between sections\n\n"
                    "Return a JSON object with exactly these keys:\n"
                    "{\n"
                    '  "reviewer_type": "pedagogy",\n'
                    '  "module_id": "string",\n'
                    '  "verdict": "approve | flag | reject",\n'
                    '  "confidence": 0.0-1.0,\n'
                    '  "findings": [\n'
                    '    {\n'
                    '      "severity": "info | warning | critical",\n'
                    '      "category": "cognitive_load | engagement | prerequisites | clarity | activity | transitions",\n'
                    '      "description": "what is wrong",\n'
                    '      "suggestion": "how to fix it"\n'
                    '    }\n'
                    "  ],\n"
                    '  "reasoning": "string — overall pedagogical assessment"\n'
                    "}\n\n"
                    "If there are no issues, return an empty findings list and verdict approve."
                ),
            },
        ]

        result = await self.call_llm_json(messages, temperature=0.2, max_tokens=1500)
        result["module_id"] = module_id

        n_findings = len(result.get("findings", []))
        await self.log(
            pipeline_id=pipeline_id,
            node_id=node.id,
            node_type=node.type,
            action=f"Pedagogy review: {result.get('verdict', 'unknown')} ({n_findings} findings)",
            reasoning=result.get("reasoning", ""),
            confidence=result.get("confidence", 0.8),
        )

        return result
