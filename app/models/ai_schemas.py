from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TicketCategory = Literal["account", "billing", "technical", "refund", "feature_request"]
TicketPriority = Literal["P0", "P1", "P2", "P3", "P4"]
SupportTeam = Literal[
    "Billing Support",
    "Technical Support",
    "Account Management",
    "Product Team",
]


class StrictSchema(BaseModel):
    """Base schema that rejects unexpected AI response fields."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class ClassificationResult(StrictSchema):
    """Structured result returned by the classification component."""

    category: TicketCategory
    subcategory: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)


class PriorityResult(StrictSchema):
    """Structured result returned by the priority component."""

    priority: TicketPriority
    reason: str = Field(min_length=1)


class RoutingResult(StrictSchema):
    """Structured result returned by the routing component."""

    assigned_team: SupportTeam
    reason: str = Field(min_length=1)


class TicketAnalysisResult(StrictSchema):
    """Combined result containing all AI ticket-analysis outputs."""

    category: TicketCategory
    subcategory: str = Field(min_length=1)
    classification_confidence: float = Field(ge=0.0, le=1.0)
    priority: TicketPriority
    assigned_team: SupportTeam
    reason: str = Field(min_length=1)
