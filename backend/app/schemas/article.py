from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class ArticleRead(BaseModel):
    id: str
    source: str
    source_id: str | None = None
    title: str
    chinese_title: str | None = None
    abstract: str | None = None
    summary: str | None = None
    url: HttpUrl | str
    doi: str | None = None
    published_at: datetime | None = None
    topics: list[str] = Field(default_factory=list)
    relevance_score: float = 0.0
    quality_score: float = 0.0
    is_preprint: bool = False
