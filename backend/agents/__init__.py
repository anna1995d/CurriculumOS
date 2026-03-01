"""
CurriculumOS agent package.

Each module exposes one agent class that extends BaseAgent.
Agents are instantiated and dispatched by the PipelineOrchestrator.
"""

from agents.audience import AudienceAgent
from agents.base import BaseAgent
from agents.catalog import CatalogAgent
from agents.conflict import ConflictAgent
from agents.outline import OutlineAgent
from agents.research import ResearchAgent
from agents.review_business import BusinessReviewAgent
from agents.review_pedagogy import PedagogyReviewAgent
from agents.review_technical import TechnicalReviewAgent
from agents.script import ScriptAgent

__all__ = [
    "BaseAgent",
    "ResearchAgent",
    "AudienceAgent",
    "CatalogAgent",
    "OutlineAgent",
    "ScriptAgent",
    "TechnicalReviewAgent",
    "PedagogyReviewAgent",
    "BusinessReviewAgent",
    "ConflictAgent",
]
