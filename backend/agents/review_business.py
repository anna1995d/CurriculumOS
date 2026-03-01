"""
Business Alignment Reviewer agent.

Autonomy: ADVISORY — flags issues; cannot modify the script.

Input  (node.input_data): script (dict), catalog_overlap (dict), brief (dict)
Output: reviewer_type, module_id, verdict, confidence, findings[], reasoning
"""

import json
from typing import Any, Dict

from agents.base import BaseAgent
from models import AutonomyLevel, TaskGraphNode


class BusinessReviewAgent(BaseAgent):
    autonomy = AutonomyLevel.ADVISORY

    async def run(self, node: TaskGraphNode, pipeline_id: str, **kwargs: Any) -> Dict[str, Any]:
        d = node.input_data
        script = d.get("script", {})
        overlap = d.get("catalog_overlap", {})
        brief = d.get("brief", {})

        module_id = script.get("module_id", node.id)
        module_title = script.get("module_title", "Unknown Module")

        reusable = overlap.get("reusable_modules", [])
        max_overlap = overlap.get("max_overlap_score", 0)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a curriculum strategist reviewing course content for business alignment. "
                    "Assess whether the content delivers on stated objectives, represents good ROI, "
                    "avoids unnecessary duplication of existing material, and stays within scope. "
                    "You CANNOT modify the script — only flag issues. "
                    "Return your response as a JSON object."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Review this lesson script for business alignment.\n\n"
                    f"MODULE: {module_title}\n\n"
                    f"SCRIPT:\n{json.dumps(script, indent=2)}\n\n"
                    f"ORIGINAL BRIEF:\n"
                    f"  Title: {brief.get('title', 'Unknown')}\n"
                    f"  Learning objectives: {json.dumps(brief.get('learning_objectives', []))}\n"
                    f"  Audience: {brief.get('audience', 'Unknown')}\n"
                    f"  Duration: {brief.get('duration', 'Unknown')}\n"
                    f"  Outcome description: {brief.get('outcome_description', '')}\n\n"
                    f"CATALOG OVERLAP CONTEXT:\n"
                    f"  Max overlap with existing courses: {max_overlap}%\n"
                    f"  Reusable modules found: {json.dumps([r.get('module_title') for r in reusable])}\n\n"
                    "Check for:\n"
                    "  1. Misalignment with the stated learning objectives\n"
                    "  2. Scope creep (content beyond what the brief requested)\n"
                    "  3. Poor ROI (too much time on low-value content given the duration)\n"
                    "  4. Rebuilding content that already exists in the catalog\n"
                    "  5. Audience mismatch (content pitched at wrong level)\n\n"
                    "Return a JSON object with exactly these keys:\n"
                    "{\n"
                    '  "reviewer_type": "business",\n'
                    '  "module_id": "string",\n'
                    '  "verdict": "approve | flag | reject",\n'
                    '  "confidence": 0.0-1.0,\n'
                    '  "findings": [\n'
                    '    {\n'
                    '      "severity": "info | warning | critical",\n'
                    '      "category": "alignment | scope_creep | roi | duplication | audience_fit",\n'
                    '      "description": "what is wrong",\n'
                    '      "suggestion": "how to fix it"\n'
                    '    }\n'
                    "  ],\n"
                    '  "reasoning": "string — overall business alignment assessment"\n'
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
            action=f"Business review: {result.get('verdict', 'unknown')} ({n_findings} findings)",
            reasoning=result.get("reasoning", ""),
            confidence=result.get("confidence", 0.8),
        )

        return result
