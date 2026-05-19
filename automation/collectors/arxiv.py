from __future__ import annotations

import logging
import time
from datetime import date, datetime, time as dt_time, timezone
from typing import Any
from xml.etree import ElementTree

import requests

from automation.models import Article, TopicConfig
from automation.utils import clean_text, parse_datetime

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def collect_arxiv(
    topics: list[TopicConfig],
    start_date: date,
    end_date: date,
    source_config: dict[str, Any],
) -> list[Article]:
    if not source_config.get("enabled", True):
        return []
    max_results = int(source_config.get("max_results_per_topic", 20))
    delay = float(source_config.get("request_delay_seconds", 3.0))
    since_dt = datetime.combine(start_date, dt_time.min, tzinfo=timezone.utc)
    until_dt = datetime.combine(end_date, dt_time.max, tzinfo=timezone.utc)

    articles: list[Article] = []
    for topic in topics:
        query = topic.arxiv_query or " OR ".join(f'all:"{keyword}"' for keyword in topic.keywords[:8])
        params = {
            "search_query": query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": str(max_results),
        }
        response = requests.get(BASE_URL, params=params, timeout=45)
        response.raise_for_status()
        parsed = _parse_arxiv_response(response.text, topic.slug)
        filtered = [
            article
            for article in parsed
            if not article.published_at or since_dt <= article.published_at <= until_dt
        ]
        LOGGER.info("arXiv topic=%s items=%s", topic.slug, len(filtered))
        articles.extend(filtered)
        time.sleep(delay)
    return articles


def _parse_arxiv_response(xml_text: str, topic_slug: str) -> list[Article]:
    root = ElementTree.fromstring(xml_text)
    articles: list[Article] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        entry_url = clean_text(entry.findtext("atom:id", default="", namespaces=ATOM_NS))
        arxiv_id = entry_url.rstrip("/").split("/")[-1]
        title = clean_text(entry.findtext("atom:title", default="", namespaces=ATOM_NS))
        abstract = clean_text(entry.findtext("atom:summary", default="", namespaces=ATOM_NS)) or None
        published_at = parse_datetime(entry.findtext("atom:published", default="", namespaces=ATOM_NS))
        authors = [
            clean_text(author.findtext("atom:name", default="", namespaces=ATOM_NS))
            for author in entry.findall("atom:author", ATOM_NS)
        ]
        articles.append(
            Article(
                id=f"arxiv-{arxiv_id}",
                source="arXiv",
                source_id=arxiv_id,
                title=title or f"arXiv paper {arxiv_id}",
                abstract=abstract,
                url=entry_url or "https://arxiv.org/",
                published_at=published_at,
                authors=[author for author in authors if author][:8],
                topics=[topic_slug],
                is_preprint=True,
            )
        )
    return articles
