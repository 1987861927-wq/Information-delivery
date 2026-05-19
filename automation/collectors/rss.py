from __future__ import annotations

import logging
from datetime import date, datetime, time, timezone
from typing import Any

import feedparser

from automation.models import Article, TopicConfig
from automation.utils import clean_text, keyword_count, parsed_struct_time_to_datetime

LOGGER = logging.getLogger(__name__)


def collect_rss(
    topics: list[TopicConfig],
    start_date: date,
    end_date: date,
    source_config: dict[str, Any],
) -> list[Article]:
    if not source_config.get("enabled", True):
        return []
    feeds = source_config.get("feeds") or []
    max_entries = int(source_config.get("max_entries_per_feed", 20))
    topic_by_slug = {topic.slug: topic for topic in topics}
    since_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    until_dt = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
    articles: list[Article] = []

    for feed in feeds:
        feed_topics = [slug for slug in feed.get("topics", []) if slug in topic_by_slug]
        if not feed_topics:
            continue
        parsed = feedparser.parse(feed["url"])
        if parsed.bozo and parsed.bozo_exception:
            LOGGER.warning("RSS 解析警告 feed=%s error=%s", feed.get("name"), parsed.bozo_exception)
        for entry in parsed.entries[:max_entries]:
            published_at = parsed_struct_time_to_datetime(getattr(entry, "published_parsed", None))
            if published_at and not (since_dt <= published_at <= until_dt):
                continue
            title = clean_text(getattr(entry, "title", ""))
            summary = clean_text(getattr(entry, "summary", "")) or clean_text(getattr(entry, "description", ""))
            link = clean_text(getattr(entry, "link", ""))
            matched_topics = _match_feed_topics(title=title, summary=summary, feed_topics=feed_topics, topic_by_slug=topic_by_slug)
            if not matched_topics:
                continue
            articles.append(
                Article(
                    id=f"rss-{abs(hash((feed.get('name'), link or title)))}",
                    source="RSS",
                    source_id=link or title,
                    title=title or "RSS item",
                    abstract=summary or None,
                    url=link or feed["url"],
                    published_at=published_at,
                    topics=matched_topics,
                    is_preprint=False,
                    journal=str(feed.get("name", "RSS")),
                )
            )
    LOGGER.info("RSS items=%s", len(articles))
    return articles


def _match_feed_topics(
    title: str,
    summary: str,
    feed_topics: list[str],
    topic_by_slug: dict[str, TopicConfig],
) -> list[str]:
    text = f"{title} {summary}"
    matched: list[str] = []
    for slug in feed_topics:
        topic = topic_by_slug[slug]
        if keyword_count(text, topic.keywords) > 0:
            matched.append(slug)
    return matched or feed_topics
