from __future__ import annotations

import logging
import time
from datetime import date
from typing import Any

import requests

from automation.models import Article, TopicConfig
from automation.utils import clean_text, keyword_count, parse_datetime

LOGGER = logging.getLogger(__name__)


def collect_preprint_server(
    server: str,
    topics: list[TopicConfig],
    start_date: date,
    end_date: date,
    source_config: dict[str, Any],
) -> list[Article]:
    if not source_config.get("enabled", True):
        return []
    max_results = int(source_config.get("max_results", 100))
    delay = float(source_config.get("request_delay_seconds", 1.0))
    base_url = f"https://api.biorxiv.org/details/{server}/{start_date.isoformat()}/{end_date.isoformat()}/0"
    response = requests.get(base_url, timeout=45)
    response.raise_for_status()
    items = response.json().get("collection", [])[:max_results]
    articles: list[Article] = []
    for item in items:
        title = clean_text(item.get("title"))
        abstract = clean_text(item.get("abstract"))
        text = f"{title} {abstract}"
        matched = [topic.slug for topic in topics if keyword_count(text, topic.keywords) > 0]
        if not matched:
            continue
        doi = clean_text(item.get("doi")) or None
        published_at = parse_datetime(clean_text(item.get("date")))
        articles.append(
            Article(
                id=f"{server}-{doi or abs(hash(title))}",
                source="bioRxiv" if server == "biorxiv" else "medRxiv",
                source_id=doi,
                title=title or f"{server} preprint",
                abstract=abstract or None,
                url=f"https://www.{server}.org/content/{doi}" if doi else f"https://www.{server}.org/",
                doi=doi,
                published_at=published_at,
                authors=[clean_text(item.get("authors"))] if item.get("authors") else [],
                topics=matched,
                is_preprint=True,
                journal=clean_text(item.get("server")) or None,
            )
        )
    time.sleep(delay)
    LOGGER.info("%s items=%s", server, len(articles))
    return articles
