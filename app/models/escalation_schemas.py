from typing import Literal

from pydantic import BaseModel, Field

EscalationAction = Literal[
    "suggest_resolution",
    "request_information",
    "escalate_to_human",
]


class EscalationDecision(BaseModel):
    action: EscalationAction
    escalation_required: bool
    escalation_score: float = Field(ge=0.0, le=1.0)
    human_approval_required: bool
    sensitive_action: bool
    destination_team: str
    reason: str
    missing_information: list[str] = Field(default_factory=list)
