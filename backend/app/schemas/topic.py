from pydantic import BaseModel, Field


class TopicRead(BaseModel):
    slug: str
    name: str
    description: str
    keywords: list[str] = Field(default_factory=list)
