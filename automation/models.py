from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class TopicConfig:
    slug: str
    name: str
    description: str
    keywords: list[str]
    exclude_keywords: list[str] = field(default_factory=list)
    pubmed_query: str | None = None
    arxiv_query: str | None = None
    max_items: int | None = None


@dataclass(slots=True)
class DigestConfig:
    timezone: str = "Asia/Shanghai"
    push_time_local: str = "08:00"
    default_days_back: int = 2
    default_max_items_per_topic: int = 5
    max_items_total: int = 40
    language: str = "zh-CN"
    title: str = "科研情报日报"
    summary_style: str = "concise_mobile"


@dataclass(slots=True)
class SourceError:
    source: str
    message: str


@dataclass(slots=True)
class Article:
    id: str
    source: str
    title: str
    url: str
    abstract: str | None = None
    published_at: datetime | None = None
    source_id: str | None = None
    doi: str | None = None
    authors: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    is_preprint: bool = False
    journal: str | None = None
    journal_impact_factor: float | None = None
    journal_tier: str | None = None
    journal_is_whitelisted: bool = False
    journal_filter_reason: str | None = None
    relevance_score: float = 0.0
    quality_score: float = 0.0

    def identity_key(self) -> str:
        if self.doi:
            return f"doi:{self.doi.lower().strip()}"
        if self.source_id:
            return f"{self.source}:{self.source_id}".lower().strip()
        normalized_title = " ".join(self.title.lower().split())
        return f"title:{normalized_title}"


@dataclass(slots=True)
class ArticleSummary:
    brief: str
    key_conclusions: list[str]
    method_highlights: str
    value_judgement: str
    limitations: str = ""


@dataclass(slots=True)
class DigestItem:
    article: Article
    summary: ArticleSummary


@dataclass(slots=True)
class Digest:
    date: str
    title: str
    topics: list[TopicConfig]
    items_by_topic: dict[str, list[DigestItem]]
    source_errors: list[SourceError] = field(default_factory=list)
    generated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "title": self.title,
            "topics": [asdict(topic) for topic in self.topics],
            "items_by_topic": {
                slug: [
                    {
                        "article": asdict(item.article),
                        "summary": asdict(item.summary),
                    }
                    for item in items
                ]
                for slug, items in self.items_by_topic.items()
            },
            "source_errors": [asdict(error) for error in self.source_errors],
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
        }
