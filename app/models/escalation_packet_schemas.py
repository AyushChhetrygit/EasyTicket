from pydantic import BaseModel, Field


class EscalationPacket(BaseModel):
    ticket_id: str
    customer_summary: str
    issue_summary: str
    category: str
    priority: str
    business_impact: str | None = None
    steps_already_attempted: list[str] = Field(default_factory=list)
    knowledge_articles_checked: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    possible_cause: str | None = None
    recommended_team: str
    recommended_next_actions: list[str] = Field(default_factory=list)
    internal_note: str
    customer_reply: str
