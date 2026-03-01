"""
BaseAgent — shared logic for all CurriculumOS agents.

Provides:
  • An AsyncOpenAI client pre-configured for GPT-4o-mini.
  • call_llm()       — raw chat completion, returns string.
  • call_llm_json()  — chat completion with json_mode, returns parsed dict.
                       Retries once on JSON parse failure.
  • log()            — writes a structured entry to the decision_log table.
  • run()            — abstract; subclasses implement and return output_data dict.

Returning {"awaiting_human": True, ...} from run() tells the orchestrator to
set the node to AWAITING_HUMAN and wait for the human before continuing.
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL
from database import log_decision
from models import AutonomyLevel, TaskGraphNode


class BaseAgent(ABC):
    autonomy: AutonomyLevel = AutonomyLevel.FULL

    def __init__(self) -> None:
        if not OPENAI_API_KEY:
            raise EnvironmentError(
                "OPENAI_API_KEY is not set. Add it to backend/.env before running agents."
            )
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL

    # ─── LLM helpers ──────────────────────────────────────────────────────────

    async def call_llm(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> str:
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    async def call_llm_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """Call LLM in JSON mode and return a parsed dict. Retries once."""
        raw = await self.call_llm(
            messages, temperature=temperature, max_tokens=max_tokens, json_mode=True
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            retry = messages + [
                {"role": "assistant", "content": raw},
                {
                    "role": "user",
                    "content": "Your response was not valid JSON. Please return ONLY a valid JSON object with no other text.",
                },
            ]
            raw2 = await self.call_llm(
                retry, temperature=0.1, max_tokens=max_tokens, json_mode=True
            )
            return json.loads(raw2)

    # ─── Audit log ────────────────────────────────────────────────────────────

    async def log(
        self,
        node_id: str,
        node_type: str,
        action: str,
        reasoning: str,
        confidence: float,
        pipeline_id: Optional[str] = None,
        human_override: bool = False,
        human_decision: Optional[str] = None,
    ) -> None:
        await log_decision(
            node_id=node_id,
            node_type=node_type,
            action=action,
            reasoning=reasoning,
            confidence=confidence,
            autonomy_level=self.autonomy.value,
            pipeline_id=pipeline_id,
            human_override=human_override,
            human_decision=human_decision,
        )

    # ─── Abstract interface ───────────────────────────────────────────────────

    @abstractmethod
    async def run(
        self,
        node: TaskGraphNode,
        pipeline_id: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Execute this agent's task and return output_data.

        Include {"awaiting_human": True} in the returned dict to pause the
        pipeline at this node until the human approves.
        """
        ...
