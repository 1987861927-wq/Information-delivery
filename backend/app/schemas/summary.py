from pydantic import BaseModel, Field


class StructuredSummary(BaseModel):
    one_sentence: str
    research_question: str
    methods: str
    key_findings: list[str] = Field(default_factory=list)
    value: str
    limitations: str
    audience: list[str] = Field(default_factory=list)
