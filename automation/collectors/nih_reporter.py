from __future__ import annotations

import logging
import math
import time
from datetime import date, datetime, timezone
from typing import Any

import requests

from automation.models import Article, TopicConfig
from automation.utils import clean_text, keyword_count, parse_datetime, truncate_text

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://api.reporter.nih.gov/v2/projects/search"
PROJECT_URL = "https://reporter.nih.gov/project-details"


def collect_nih_reporter(
    topics: list[TopicConfig],
    start_date: date,
    end_date: date,
    source_config: dict[str, Any],
) -> list[Article]:
    if not source_config.get("enabled", True):
        return []

    max_results_per_topic = int(source_config.get("max_results_per_topic", 12))
    limit = min(max(int(source_config.get("limit", 25)), 1), 500)
    max_pages = max(int(source_config.get("max_pages", 1)), 1)
    min_score = float(source_config.get("min_score", 1.0))
    delay = float(source_config.get("request_delay_seconds", 1.0))
    extra_keywords = [str(item) for item in source_config.get("keywords", [])]
    fiscal_years = [int(item) for item in source_config.get("fiscal_years", []) if str(item).strip().isdigit()]
    agencies = [str(item) for item in source_config.get("agencies", []) if str(item).strip()]
    organizations = [str(item) for item in source_config.get("organizations", []) if str(item).strip()]
    pis = [str(item) for item in source_config.get("pis", []) if str(item).strip()]
    query_overrides = source_config.get("queries") or {}

    articles: list[Article] = []
    seen: set[str] = set()
    for topic in topics:
        topic_count = 0
        terms = _topic_terms(topic=topic, extra_keywords=extra_keywords, query_overrides=query_overrides)
        for page in range(max_pages):
            payload = _build_payload(
                terms=terms,
                fiscal_years=fiscal_years,
                agencies=agencies,
                organizations=organizations,
                pis=pis,
                offset=page * limit,
                limit=limit,
            )
            response = _post_reporter(payload)
            if response is None:
                break
            response.raise_for_status()
            items = response.json().get("results") or []
            if not items:
                break
            for item in items:
                if topic_count >= max_results_per_topic:
                    break
                try:
                    article = _project_to_article(
                        item=item,
                        topic=topic,
                        extra_keywords=extra_keywords,
                        start_date=start_date,
                        end_date=end_date,
                        min_score=min_score,
                    )
                except Exception as exc:  # noqa: BLE001
                    LOGGER.warning("NIH RePORTER project 解析失败 project=%s error=%s", item.get("project_num"), exc)
                    continue
                if article is None:
                    continue
                if article.source_id in seen:
                    continue
                seen.add(str(article.source_id))
                articles.append(article)
                topic_count += 1
            if topic_count >= max_results_per_topic:
                break
            time.sleep(delay)
        LOGGER.info("NIH RePORTER topic=%s items=%s", topic.slug, topic_count)
    return articles


def _topic_terms(topic: TopicConfig, extra_keywords: list[str], query_overrides: Any) -> list[str]:
    if isinstance(query_overrides, dict) and query_overrides.get(topic.slug):
        raw = query_overrides[topic.slug]
        if isinstance(raw, list):
            return [str(item) for item in raw if str(item).strip()]
        return [str(raw)]
    terms = [keyword for keyword in topic.keywords[:8] if keyword]
    terms.extend(extra_keywords)
    return sorted(set(str(term).strip() for term in terms if str(term).strip()))


def _build_payload(
    terms: list[str],
    fiscal_years: list[int],
    agencies: list[str],
    organizations: list[str],
    pis: list[str],
    offset: int,
    limit: int,
) -> dict[str, Any]:
    criteria: dict[str, Any] = {
        "advanced_text_search": {
            "operator": "or",
            "search_field": "all",
            "search_text": " ".join(terms),
        }
    }
    if fiscal_years:
        criteria["fiscal_years"] = fiscal_years
    if agencies:
        criteria["agency_ic_admin"] = agencies
    if organizations:
        criteria["org_names"] = organizations
    if pis:
        criteria["pi_names"] = pis
    return {
        "criteria": criteria,
        "include_fields": [
            "ApplId",
            "ProjectNum",
            "ProjectTitle",
            "AbstractText",
            "AgencyIcAdmin",
            "AgencyIcFundings",
            "PrincipalInvestigators",
            "Organization",
            "FiscalYear",
            "ProjectStartDate",
            "ProjectEndDate",
            "AwardAmount",
            "ProjectDetailUrl",
            "Terms",
        ],
        "offset": offset,
        "limit": limit,
        "sort_field": "fiscal_year",
        "sort_order": "desc",
    }


def _post_reporter(payload: dict[str, Any]) -> requests.Response | None:
    try:
        return requests.post(BASE_URL, json=payload, timeout=45)
    except requests.RequestException as exc:
        LOGGER.warning("NIH RePORTER API 请求失败 error=%s", exc)
        return None


def _project_to_article(
    item: dict[str, Any],
    topic: TopicConfig,
    extra_keywords: list[str],
    start_date: date,
    end_date: date,
    min_score: float,
) -> Article | None:
    appl_id = clean_text(str(item.get("appl_id") or item.get("applId") or ""))
    project_num = clean_text(item.get("project_num") or item.get("projectNumber"))
    title = clean_text(item.get("project_title") or item.get("projectTitle"))
    abstract = clean_text(item.get("abstract_text") or item.get("abstractText"))
    if not project_num or not title:
        return None

    fiscal_year = _to_int(item.get("fiscal_year"))
    award_amount = _to_float(item.get("award_amount"))
    start_dt = parse_datetime(clean_text(item.get("project_start_date")))
    end_dt = parse_datetime(clean_text(item.get("project_end_date")))
    published_at = _fiscal_year_datetime(fiscal_year) or start_dt
    if published_at:
        project_day = published_at.date()
        if project_day < start_date.replace(year=max(start_date.year - 5, 1900)) or project_day > end_date.replace(year=end_date.year + 1):
            # RePORTER projects often span years; keep a wider window than papers, but skip very old records.
            return None

    agency = _agency_name(item.get("agency_ic_admin"))
    fundings = item.get("agency_ic_fundings") or []
    organization = item.get("organization") or {}
    org_name = clean_text(organization.get("org_name") or organization.get("name")) if isinstance(organization, dict) else clean_text(str(organization))
    pi_names = _pi_names(item.get("principal_investigators") or [])
    terms = _terms(item.get("terms") or [])
    detail_url = clean_text(item.get("project_detail_url")) or (f"{PROJECT_URL}/{appl_id}" if appl_id else f"{PROJECT_URL}/{project_num}")

    score = _importance_score(
        topic=topic,
        title=title,
        abstract=abstract,
        terms=terms,
        fiscal_year=fiscal_year,
        award_amount=award_amount,
        agency=agency,
        extra_keywords=extra_keywords,
    )
    if score < min_score:
        return None

    metadata = {
        "appl_id": appl_id,
        "project_num": project_num,
        "agency": agency,
        "agency_fundings": fundings,
        "principal_investigators": pi_names,
        "organization": org_name,
        "fiscal_year": fiscal_year,
        "project_start_date": start_dt.isoformat() if start_dt else None,
        "project_end_date": end_dt.isoformat() if end_dt else None,
        "award_amount": award_amount,
        "terms": terms[:20],
        "importance_score": round(score, 3),
    }
    abstract_parts = [abstract]
    abstract_parts.append(
        "NIH RePORTER 元数据："
        f"project={project_num}, agency={agency or 'unknown'}, fiscal_year={fiscal_year or 'unknown'}, "
        f"award_amount={award_amount or 0:g}, organization={org_name or 'unknown'}, PI={', '.join(pi_names[:4]) or 'unknown'}."
    )
    if terms:
        abstract_parts.append(f"Terms: {', '.join(terms[:12])}.")

    return Article(
        id=f"nih-reporter-{project_num.lower()}",
        source="NIH RePORTER",
        source_id=project_num.lower(),
        title=f"NIH Grant: {title}",
        abstract=truncate_text(" ".join(part for part in abstract_parts if part), 2200),
        url=detail_url,
        published_at=published_at,
        authors=pi_names[:8],
        topics=[topic.slug],
        is_preprint=False,
        journal="NIH RePORTER Project",
        relevance_score=score,
        quality_score=score,
        metadata=metadata,
    )


def _importance_score(
    topic: TopicConfig,
    title: str,
    abstract: str,
    terms: list[str],
    fiscal_year: int,
    award_amount: float,
    agency: str,
    extra_keywords: list[str],
) -> float:
    text = f"{title} {abstract} {' '.join(terms)}"
    score = float(keyword_count(text, topic.keywords + extra_keywords))
    current_year = datetime.now(timezone.utc).year
    if fiscal_year:
        age = max(current_year - fiscal_year, 0)
        score += max(0.0, 2.0 - min(age, 8) * 0.25)
    if award_amount:
        score += min(math.log10(award_amount + 1) - 4.0, 2.5) if award_amount > 10_000 else 0.0
    if agency:
        score += 0.4
    if terms:
        score += min(len(terms), 10) * 0.05
    return round(max(score, 0.0), 3)


def _agency_name(raw: Any) -> str:
    if isinstance(raw, dict):
        return clean_text(raw.get("abbreviation") or raw.get("name") or raw.get("code"))
    if isinstance(raw, list):
        names = [_agency_name(item) for item in raw]
        return ", ".join(name for name in names if name)
    return clean_text(str(raw or ""))


def _terms(raw: list[Any]) -> list[str]:
    terms: list[str] = []
    for item in raw:
        if isinstance(item, dict):
            value = clean_text(item.get("term") or item.get("text") or item.get("name"))
        else:
            value = clean_text(str(item))
        if value:
            terms.append(value)
    return terms


def _pi_names(raw: list[Any]) -> list[str]:
    names: list[str] = []
    for item in raw:
        if isinstance(item, dict):
            name = clean_text(item.get("full_name") or item.get("name"))
        else:
            name = clean_text(str(item))
        if name:
            names.append(name)
    return names


def _fiscal_year_datetime(fiscal_year: int) -> datetime | None:
    if not fiscal_year:
        return None
    try:
        return datetime(int(fiscal_year), 1, 1, tzinfo=timezone.utc)
    except ValueError:
        return None


def _to_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _to_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0
