from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(80), index=True)
    source_id: Mapped[str | None] = mapped_column(String(200), index=True)
    title: Mapped[str] = mapped_column(Text)
    abstract: Mapped[str | None] = mapped_column(Text)
    chinese_title: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    doi: Mapped[str | None] = mapped_column(String(200), index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id"), index=True)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
