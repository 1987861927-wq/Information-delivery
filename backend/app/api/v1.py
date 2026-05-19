from fastapi import APIRouter, Query

from app.schemas.article import ArticleRead
from app.schemas.briefing import BriefingRead
from app.schemas.topic import TopicRead
from app.services.briefing_service import briefing_service
from app.services.topic_service import topic_service

router = APIRouter()


@router.get("/topics", response_model=list[TopicRead], tags=["topics"])
def list_topics() -> list[TopicRead]:
    return topic_service.list_topics()


@router.get("/articles", response_model=list[ArticleRead], tags=["articles"])
def list_articles(
    topic: str | None = Query(default=None, description="主题 slug，例如 ai、neuroscience"),
    q: str | None = Query(default=None, description="关键词搜索"),
) -> list[ArticleRead]:
    return briefing_service.list_articles(topic_slug=topic, query=q)


@router.get("/briefings/today", response_model=BriefingRead, tags=["briefings"])
def today_briefing(topic: str | None = Query(default=None)) -> BriefingRead:
    return briefing_service.today(topic_slug=topic)
