from datetime import date

from pydantic import BaseModel, Field

from app.schemas.article import ArticleRead


class BriefingRead(BaseModel):
    date: date
    title: str
    topics: list[str] = Field(default_factory=list)
    highlights: list[ArticleRead] = Field(default_factory=list)
    articles: list[ArticleRead] = Field(default_factory=list)
