"""
Technical Fidelity Reviewer agent.

Autonomy: ADVISORY — flags issues; cannot modify the script.

Input  (node.input_data): script (dict), topic_map (dict)
Output: reviewer_type, module_id, verdict, confidence, findings[], reasoning
"""

import json
from typing import Any, Dict

from agents.base import BaseAgent
from models import AutonomyLevel, TaskGraphNode


class TechnicalReviewAgent(BaseAgent):
    autonomy = AutonomyLevel.ADVISORY

    async def run(self, node: TaskGraphNode, pipeline_id: str, **kwargs: Any) -> Dict[str, Any]:
        d = node.input_data
        script = d.get("script", {})
        topic_map = d.get("topic_map", {})

        module_id = script.get("module_id", node.id)
        module_title = script.get("module_title", "Unknown Module")

        # Extract concept depth targets for comparison
        concepts = topic_map.get("concepts", [])
        concept_guide = {c["name"]: c for c in concepts if "name" in c}

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a domain expert and technical reviewer for educational content. "
                    "Your job is to identify factual errors, inappropriate complexity, incorrect "
                    "terminology, and simplifications that introduce misconceptions. "
                    "You CANNOT modify the script — only flag issues. "
                    "Return your response as a JSON object."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Review this lesson script for technical accuracy.\n\n"
                    f"MODULE: {module_title}\n\n"
                    f"SCRIPT:\n{json.dumps(script, indent=2)}\n\n"
                    f"EXPECTED CONCEPT DEPTHS:\n{json.dumps(concept_guide, indent=2)}\n\n"
                    "Check for:\n"
                    "  1. Factual errors or outdated information\n"
                    "  2. Incorrect or inconsistent terminology\n"
                    "  3. Examples that are technically unsound or misleading\n"
                    "  4. Oversimplifications that create misconceptions\n"
                    "  5. Complexity mismatches (too advanced or too simplistic for the stated depth)\n\n"
                    "Return a JSON object with exactly these keys:\n"
                    "{\n"
                    '  "reviewer_type": "technical",\n'
                    '  "module_id": "string",\n'
                    '  "verdict": "approve | flag | reject",\n'
                    '  "confidence": 0.0-1.0,\n'
                    '  "findings": [\n'
                    '    {\n'
                    '      "severity": "info | warning | critical",\n'
                    '      "category": "accuracy | terminology | complexity | example | misconception",\n'
                    '      "description": "what is wrong",\n'
                    '      "suggestion": "how to fix it"\n'
                    '    }\n'
                    "  ],\n"
                    '  "reasoning": "string — overall technical assessment"\n'
                    "}\n\n"
                    "approve = no significant technical issues\n"
                    "flag = issues present but fixable with minor edits\n"
                    "reject = fundamental technical problems that require a rewrite\n"
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
            action=f"Technical review: {result.get('verdict', 'unknown')} ({n_findings} findings)",
            reasoning=result.get("reasoning", ""),
            confidence=result.get("confidence", 0.8),
        )

        return result
