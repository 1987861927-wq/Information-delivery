from datetime import UTC, date, datetime

from app.schemas.article import ArticleRead
from app.schemas.briefing import BriefingRead

SAMPLE_ARTICLES: list[ArticleRead] = [
    ArticleRead(
        id="sample-ai-001",
        source="arXiv",
        source_id="2401.00001",
        title="Foundation models for biomedical discovery",
        chinese_title="用于生物医学发现的基础模型",
        abstract="A survey-like placeholder for biomedical foundation models.",
        summary="一句话结论：基础模型正在成为生物医学文献理解、影像分析和分子设计的通用底座。\n核心发现：多模态数据整合是提升医学 AI 泛化能力的关键。",
        url="https://arxiv.org/",
        published_at=datetime.now(UTC),
        topics=["ai"],
        relevance_score=0.86,
        quality_score=0.72,
        is_preprint=True,
    ),
    ArticleRead(
        id="sample-ortho-001",
        source="PubMed",
        source_id="PMID_PLACEHOLDER",
        title="Biomaterial scaffolds for bone regeneration",
        chinese_title="用于骨再生的生物材料支架",
        abstract="A placeholder article about scaffold design for bone regeneration.",
        summary="一句话结论：可降解支架结合成骨信号有望提升骨缺损修复效果。\n局限性：仍需更多大样本临床证据。",
        url="https://pubmed.ncbi.nlm.nih.gov/",
        published_at=datetime.now(UTC),
        topics=["biomaterials", "orthopedics"],
        relevance_score=0.91,
        quality_score=0.80,
        is_preprint=False,
    ),
]


class BriefingService:
    def list_articles(self, topic_slug: str | None = None, query: str | None = None) -> list[ArticleRead]:
        articles = SAMPLE_ARTICLES
        if topic_slug:
            articles = [article for article in articles if topic_slug in article.topics]
        if query:
            lowered = query.lower()
            articles = [
                article
                for article in articles
                if lowered in article.title.lower()
                or (article.chinese_title and lowered in article.chinese_title.lower())
                or (article.summary and lowered in article.summary.lower())
            ]
        return articles

    def today(self, topic_slug: str | None = None) -> BriefingRead:
        articles = self.list_articles(topic_slug=topic_slug)
        highlights = sorted(articles, key=lambda article: article.relevance_score, reverse=True)[:3]
        topics = sorted({topic for article in articles for topic in article.topics})
        return BriefingRead(
            date=date.today(),
            title="今日科研情报简报",
            topics=topics,
            highlights=highlights,
            articles=articles,
        )


briefing_service = BriefingService()
