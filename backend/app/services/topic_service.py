from app.core.topics import DEFAULT_TOPICS
from app.schemas.topic import TopicRead


class TopicService:
    def list_topics(self) -> list[TopicRead]:
        return DEFAULT_TOPICS

    def get_keywords(self, topic_slug: str | None) -> list[str]:
        if topic_slug is None:
            return [keyword for topic in DEFAULT_TOPICS for keyword in topic.keywords]
        for topic in DEFAULT_TOPICS:
            if topic.slug == topic_slug:
                return topic.keywords
        return []


topic_service = TopicService()
