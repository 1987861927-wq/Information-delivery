from __future__ import annotations

import logging
import os
import time
from datetime import date
from typing import Any
from urllib.parse import quote_plus
from xml.etree import ElementTree

import requests

from automation.models import Article, TopicConfig
from automation.utils import clean_text, parse_datetime, pubmed_date_range

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def collect_pubmed(
    topics: list[TopicConfig],
    start_date: date,
    end_date: date,
    source_config: dict[str, Any],
) -> list[Article]:
    if not source_config.get("enabled", True):
        return []
    retmax = int(source_config.get("retmax_per_topic", 20))
    delay = float(source_config.get("request_delay_seconds", 0.34))
    email = os.getenv(str(source_config.get("email_env", "NCBI_EMAIL")), "")
    api_key = os.getenv(str(source_config.get("api_key_env", "NCBI_API_KEY")), "")

    articles: list[Article] = []
    for topic in topics:
        term = topic.pubmed_query or " OR ".join(topic.keywords)
        journal_query = str(source_config.get("journal_query", "") or "").strip()
        if journal_query:
            term = f"({term}) AND {journal_query} AND {pubmed_date_range(start_date, end_date)}"
        else:
            term = f"({term}) AND {pubmed_date_range(start_date, end_date)}"
        ids = _search_pubmed(term=term, retmax=retmax, email=email, api_key=api_key)
        LOGGER.info("PubMed topic=%s ids=%s", topic.slug, len(ids))
        if ids:
            fetched = _fetch_pubmed(ids=ids, topic_slug=topic.slug, email=email, api_key=api_key)
            articles.extend(fetched)
        time.sleep(delay)
    return articles


def _search_pubmed(term: str, retmax: int, email: str, api_key: str) -> list[str]:
    params = {
        "db": "pubmed",
        "term": term,
        "retmode": "json",
        "retmax": str(retmax),
        "sort": "pub date",
    }
    if email:
        params["email"] = email
    if api_key:
        params["api_key"] = api_key
    response = requests.get(f"{BASE_URL}/esearch.fcgi", params=params, timeout=30)
    response.raise_for_status()
    return [str(item) for item in response.json().get("esearchresult", {}).get("idlist", [])]


def _fetch_pubmed(ids: list[str], topic_slug: str, email: str, api_key: str) -> list[Article]:
    params = {
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "xml",
    }
    if email:
        params["email"] = email
    if api_key:
        params["api_key"] = api_key
    response = requests.get(f"{BASE_URL}/efetch.fcgi", params=params, timeout=45)
    response.raise_for_status()
    root = ElementTree.fromstring(response.content)
    return [_parse_pubmed_article(node, topic_slug) for node in root.findall(".//PubmedArticle")]


def _parse_pubmed_article(node: ElementTree.Element, topic_slug: str) -> Article:
    pmid = clean_text(node.findtext(".//PMID"))
    title = _inner_text(node.find(".//ArticleTitle")) or f"PubMed article {pmid}"
    abstract_parts = [_inner_text(item) for item in node.findall(".//Abstract/AbstractText")]
    abstract = clean_text("\n".join(part for part in abstract_parts if part)) or None
    journal = clean_text(node.findtext(".//Journal/Title")) or None
    doi = _find_article_id(node, "doi")
    authors = _parse_authors(node)
    published_at = _parse_pubmed_date(node)
    return Article(
        id=f"pubmed-{pmid}",
        source="PubMed",
        source_id=pmid,
        title=title,
        abstract=abstract,
        url=f"https://pubmed.ncbi.nlm.nih.gov/{quote_plus(pmid)}/" if pmid else "https://pubmed.ncbi.nlm.nih.gov/",
        doi=doi,
        published_at=published_at,
        authors=authors,
        topics=[topic_slug],
        is_preprint=False,
        journal=journal,
    )


def _inner_text(node: ElementTree.Element | None) -> str:
    if node is None:
        return ""
    return clean_text("".join(node.itertext()))


def _find_article_id(node: ElementTree.Element, id_type: str) -> str | None:
    for article_id in node.findall(".//ArticleId"):
        if article_id.attrib.get("IdType") == id_type:
            return clean_text(article_id.text)
    return None


def _parse_authors(node: ElementTree.Element) -> list[str]:
    authors: list[str] = []
    for author in node.findall(".//AuthorList/Author"):
        last = clean_text(author.findtext("LastName"))
        initials = clean_text(author.findtext("Initials"))
        collective = clean_text(author.findtext("CollectiveName"))
        if collective:
            authors.append(collective)
        elif last:
            authors.append(f"{last} {initials}".strip())
    return authors[:8]


def _parse_pubmed_date(node: ElementTree.Element):
    article_date = node.find(".//ArticleDate")
    if article_date is not None:
        year = clean_text(article_date.findtext("Year"))
        month = clean_text(article_date.findtext("Month")) or "01"
        day = clean_text(article_date.findtext("Day")) or "01"
        parsed = parse_datetime(f"{year}-{month.zfill(2)}-{day.zfill(2)}")
        if parsed:
            return parsed
    pub_date = node.find(".//JournalIssue/PubDate")
    if pub_date is not None:
        year = clean_text(pub_date.findtext("Year"))
        month = _month_to_number(clean_text(pub_date.findtext("Month"))) or "01"
        day = clean_text(pub_date.findtext("Day")) or "01"
        if year:
            return parse_datetime(f"{year}-{month.zfill(2)}-{day.zfill(2)}")
    return None


def _month_to_number(value: str) -> str:
    if value.isdigit():
        return value
    mapping = {
        "jan": "01",
        "feb": "02",
        "mar": "03",
        "apr": "04",
        "may": "05",
        "jun": "06",
        "jul": "07",
        "aug": "08",
        "sep": "09",
        "oct": "10",
        "nov": "11",
        "dec": "12",
    }
    return mapping.get(value[:3].lower(), "")
