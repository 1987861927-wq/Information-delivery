from __future__ import annotations

from datetime import datetime, timezone

from automation.models import Article, TopicConfig
from automation.utils import keyword_count

SOURCE_WEIGHTS = {
    "PubMed": 1.0,
    "arXiv": 0.82,
    "bioRxiv": 0.78,
    "medRxiv": 0.80,
    "RSS": 0.55,
}


def assign_topics_and_scores(articles: list[Article], topics: list[TopicConfig]) -> list[Article]:
    result: list[Article] = []
    for article in articles:
        text = f"{article.title} {article.abstract or ''}".lower()
        matched: list[str] = list(article.topics)
        relevance = article.relevance_score
        for topic in topics:
            if any(exclude.lower() in text for exclude in topic.exclude_keywords):
                continue
            score = keyword_count(text, topic.keywords)
            if score > 0 or topic.slug in matched:
                if topic.slug not in matched:
                    matched.append(topic.slug)
                relevance = max(relevance, float(score))
        if matched:
            article.topics = sorted(set(matched))
            article.relevance_score = relevance
            article.quality_score = compute_quality_score(article)
            result.append(article)
    return result


def compute_quality_score(article: Article) -> float:
    score = SOURCE_WEIGHTS.get(article.source, 0.5)
    if article.abstract and len(article.abstract) > 400:
        score += 0.2
    if article.doi:
        score += 0.1
    if article.published_at:
        days_old = max((datetime.now(timezone.utc) - article.published_at).days, 0)
        score += max(0.0, 0.25 - min(days_old, 30) * 0.01)
    return round(score, 3)


def dedupe_articles(articles: list[Article]) -> list[Article]:
    seen: set[str] = set()
    result: list[Article] = []
    for article in articles:
        key = article.identity_key()
        if key in seen:
            continue
        seen.add(key)
        result.append(article)
    return result


def select_items_by_topic(
    articles: list[Article],
    topics: list[TopicConfig],
    default_limit: int,
    override_limit: int | None = None,
) -> dict[str, list[Article]]:
    selected: dict[str, list[Article]] = {}
    for topic in topics:
        limit = override_limit or topic.max_items or default_limit
        topic_articles = [article for article in articles if topic.slug in article.topics]
        topic_articles.sort(
            key=lambda article: (
                article.relevance_score,
                article.quality_score,
                article.published_at.timestamp() if article.published_at else 0,
            ),
            reverse=True,
        )
        selected[topic.slug] = topic_articles[:limit]
    return selected
