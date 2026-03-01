"""
Pydantic models for all CurriculumOS data structures.

Covers: CourseBrief, TaskGraphNode, ReviewOutput, ConflictReport,
DecisionLogEntry, Pipeline, catalog types, and API request/response models.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─── Enums ────────────────────────────────────────────────────────────────────


class TopicArea(str, Enum):
    ML = "ML"
    DATA_SCIENCE = "Data Science"
    ETHICS = "Ethics"
    PROGRAMMING = "Programming"
    APPLIED_AI = "Applied AI"
    OTHER = "Other"


class AudienceType(str, Enum):
    EXECUTIVES = "Executives"
    TECHNICAL_PMS = "Technical PMs"
    JUNIOR_DEVS = "Junior Devs"
    SENIOR_ENGINEERS = "Senior Engineers"
    NON_TECHNICAL = "Non-technical"


class ClassSize(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class Duration(str, Enum):
    ONE_HOUR = "1hr talk"
    HALF_DAY = "half-day"
    FULL_DAY = "full-day"
    MULTI_DAY = "multi-day"


class DeliveryFormat(str, Enum):
    IN_PERSON = "in-person"
    VIRTUAL = "virtual"
    SELF_PACED = "self-paced"


class NodeType(str, Enum):
    ORCHESTRATOR = "orchestrator"
    RESEARCH = "research"
    AUDIENCE = "audience"
    CATALOG = "catalog"
    OUTLINE = "outline"
    SCRIPT = "script"
    REVIEW_TECHNICAL = "review_technical"
    REVIEW_PEDAGOGY = "review_pedagogy"
    REVIEW_BUSINESS = "review_business"
    CONFLICT = "conflict"


class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    AWAITING_HUMAN = "awaiting_human"
    ERROR = "error"


class AutonomyLevel(str, Enum):
    FULL = "full"
    DRAFT = "draft"
    RECOMMEND = "recommend"
    ADVISORY = "advisory"
    ESCALATE = "escalate"
    REFUSE = "refuse"


class ReviewerType(str, Enum):
    TECHNICAL = "technical"
    PEDAGOGY = "pedagogy"
    BUSINESS = "business"


class Verdict(str, Enum):
    APPROVE = "approve"
    FLAG = "flag"
    REJECT = "reject"


class FindingSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class ConflictType(str, Enum):
    FACTUAL = "factual"
    SUBJECTIVE = "subjective"
    PRIORITY = "priority"


# ─── Course Brief ─────────────────────────────────────────────────────────────


class CourseBrief(BaseModel):
    title: str
    topic_area: TopicArea
    description: Annotated[str, Field(max_length=500)]
    audience: AudienceType
    prerequisites: List[str] = Field(default_factory=list)
    class_size: ClassSize
    duration: Duration
    format: DeliveryFormat
    # 0.0 = fully conceptual, 1.0 = fully hands-on
    balance: float = Field(..., ge=0.0, le=1.0)
    learning_objectives: List[str] = Field(default_factory=list)
    outcome_description: str


# ─── Task Graph Node ──────────────────────────────────────────────────────────


class TaskGraphNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: NodeType
    label: str
    status: NodeStatus = NodeStatus.PENDING
    autonomy: AutonomyLevel
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    blocked_by: Optional[str] = None
    reasoning: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ─── Review Structures ────────────────────────────────────────────────────────


class ReviewFinding(BaseModel):
    severity: FindingSeverity
    category: str
    description: str
    suggestion: str


class ReviewOutput(BaseModel):
    reviewer_type: ReviewerType
    module_id: str
    verdict: Verdict
    confidence: float = Field(..., ge=0.0, le=1.0)
    findings: List[ReviewFinding] = Field(default_factory=list)
    reasoning: str


# ─── Conflict Report ──────────────────────────────────────────────────────────


class Agreement(BaseModel):
    topic: str
    shared_recommendation: str


class Disagreement(BaseModel):
    topic: str
    # Maps reviewer_type string → position string
    positions: Dict[str, str]
    conflict_type: ConflictType
    ai_assessment: str
    human_options: List[str]


class ConflictReport(BaseModel):
    module_id: str
    agreements: List[Agreement] = Field(default_factory=list)
    disagreements: List[Disagreement] = Field(default_factory=list)


# ─── Decision Log ─────────────────────────────────────────────────────────────


class DecisionLogEntry(BaseModel):
    id: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    pipeline_id: Optional[str] = None
    node_id: str
    node_type: str
    action: str
    reasoning: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    autonomy_level: str
    human_override: bool = False
    human_decision: Optional[str] = None


# ─── Pipeline ─────────────────────────────────────────────────────────────────


class Pipeline(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    brief: CourseBrief
    nodes: List[TaskGraphNode] = Field(default_factory=list)
    status: str = "created"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ─── Catalog Models ───────────────────────────────────────────────────────────


class CatalogModule(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    duration_minutes: Optional[int] = None
    order_index: int


class CatalogCourse(BaseModel):
    id: int
    title: str
    duration: str
    audience: str
    topic_area: str
    description: Optional[str] = None
    modules: List[CatalogModule] = Field(default_factory=list)


# ─── API Request / Response Models ───────────────────────────────────────────


class BriefSubmitRequest(BaseModel):
    brief: CourseBrief


class BriefSubmitResponse(BaseModel):
    pipeline_id: str
    message: str


class HumanApproveRequest(BaseModel):
    pipeline_id: str


class HumanEditRequest(BaseModel):
    pipeline_id: str
    edited_output: Dict[str, Any]


class HumanDecideRequest(BaseModel):
    pipeline_id: str
    decision: Optional[str] = None          # single decision (legacy / no-disagreement case)
    decisions: Optional[Dict[str, str]] = None  # topic → chosen option (batch)
    context: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    pipeline_id: str
    message: str
