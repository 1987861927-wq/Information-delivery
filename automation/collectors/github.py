from __future__ import annotations

import logging
import math
import os
import time
from datetime import date, datetime, time as dt_time, timezone
from typing import Any

import requests

from automation.models import Article, TopicConfig
from automation.utils import clean_text, keyword_count, parse_datetime, truncate_text

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://api.github.com"


def collect_github(
    topics: list[TopicConfig],
    start_date: date,
    end_date: date,
    source_config: dict[str, Any],
) -> list[Article]:
    if not source_config.get("enabled", True):
        return []

    token = os.getenv(str(source_config.get("token_env", "GITHUB_TOKEN")), "").strip()
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "research-intelligence-digest",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    max_results_per_topic = int(source_config.get("max_results_per_topic", 12))
    per_page = min(max(int(source_config.get("per_page", 20)), 1), 100)
    max_pages = max(int(source_config.get("max_pages", 1)), 1)
    min_score = float(source_config.get("min_score", 1.0))
    min_stars = int(source_config.get("min_stars", 5))
    stale_days = int(source_config.get("stale_days", 730))
    delay = float(source_config.get("request_delay_seconds", 1.0))
    language_boosts = {str(item).lower() for item in source_config.get("language_boosts", [])}
    extra_keywords = [str(item) for item in source_config.get("keywords", [])]
    query_overrides = source_config.get("queries") or {}

    articles: list[Article] = []
    seen: set[str] = set()
    since_dt = datetime.combine(start_date, dt_time.min, tzinfo=timezone.utc)
    until_dt = datetime.combine(end_date, dt_time.max, tzinfo=timezone.utc)

    for topic in topics:
        query = _build_query(topic=topic, source_config=source_config, query_overrides=query_overrides)
        topic_count = 0
        for page in range(1, max_pages + 1):
            params = {
                "q": query,
                "sort": str(source_config.get("sort", "updated")),
                "order": str(source_config.get("order", "desc")),
                "per_page": str(per_page),
                "page": str(page),
            }
            response = _github_get("/search/repositories", headers=headers, params=params, timeout=45)
            if response is None:
                break
            if response.status_code in {403, 429}:
                LOGGER.warning("GitHub API 可能触发限流 status=%s message=%s", response.status_code, response.text[:300])
                break
            response.raise_for_status()
            items = response.json().get("items") or []
            if not items:
                break
            for item in items:
                if topic_count >= max_results_per_topic:
                    break
                try:
                    article = _repo_to_article(
                        item=item,
                        topic=topic,
                        headers=headers,
                        since_dt=since_dt,
                        until_dt=until_dt,
                        extra_keywords=extra_keywords,
                        min_score=min_score,
                        min_stars=min_stars,
                        stale_days=stale_days,
                        language_boosts=language_boosts,
                        include_latest_release=bool(source_config.get("include_latest_release", True)),
                    )
                except Exception as exc:  # noqa: BLE001
                    LOGGER.warning("GitHub repo 解析失败 repo=%s error=%s", item.get("full_name"), exc)
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
        LOGGER.info("GitHub topic=%s items=%s", topic.slug, topic_count)
    return articles


def _build_query(topic: TopicConfig, source_config: dict[str, Any], query_overrides: Any) -> str:
    if isinstance(query_overrides, dict) and query_overrides.get(topic.slug):
        return str(query_overrides[topic.slug])
    base_terms = source_config.get("default_query_terms") or topic.keywords[:8]
    terms = [str(item).strip() for item in base_terms if str(item).strip()]
    query = " ".join(terms) or topic.name or topic.slug
    qualifiers = source_config.get("qualifiers") or ["archived:false"]
    qualifier_text = " ".join(str(item) for item in qualifiers if str(item).strip())
    return f"{query} {qualifier_text}".strip()


def _github_get(path: str, headers: dict[str, str], params: dict[str, str] | None = None, timeout: int = 30) -> requests.Response | None:
    try:
        return requests.get(f"{BASE_URL}{path}", headers=headers, params=params, timeout=timeout)
    except requests.RequestException as exc:
        LOGGER.warning("GitHub API 请求失败 path=%s error=%s", path, exc)
        return None


def _repo_to_article(
    item: dict[str, Any],
    topic: TopicConfig,
    headers: dict[str, str],
    since_dt: datetime,
    until_dt: datetime,
    extra_keywords: list[str],
    min_score: float,
    min_stars: int,
    stale_days: int,
    language_boosts: set[str],
    include_latest_release: bool,
) -> Article | None:
    full_name = clean_text(item.get("full_name"))
    description = clean_text(item.get("description"))
    if not full_name or not description:
        return None

    updated_at = parse_datetime(clean_text(item.get("updated_at")))
    created_at = parse_datetime(clean_text(item.get("created_at")))
    pushed_at = parse_datetime(clean_text(item.get("pushed_at"))) or updated_at
    if updated_at and (datetime.now(timezone.utc) - updated_at).days > stale_days:
        return None

    stars = _to_int(item.get("stargazers_count"))
    forks = _to_int(item.get("forks_count"))
    watchers = _to_int(item.get("watchers_count"))
    open_issues = _to_int(item.get("open_issues_count"))
    language = clean_text(item.get("language")) or "Unknown"
    repo_topics = [str(value) for value in item.get("topics") or [] if str(value).strip()]
    html_url = clean_text(item.get("html_url")) or f"https://github.com/{full_name}"

    latest_release = None
    if include_latest_release:
        latest_release = _fetch_latest_release(full_name=full_name, headers=headers)

    score = _hotness_score(
        topic=topic,
        title=full_name,
        description=description,
        repo_topics=repo_topics,
        language=language,
        stars=stars,
        forks=forks,
        updated_at=updated_at,
        latest_release=latest_release,
        extra_keywords=extra_keywords,
        language_boosts=language_boosts,
    )
    weak_keyword_match = keyword_count(f"{full_name} {description} {' '.join(repo_topics)}", topic.keywords + extra_keywords) <= 0
    if stars < min_stars and weak_keyword_match:
        return None
    if score < min_score:
        return None

    release_text = _format_release(latest_release)
    metadata = {
        "repo": full_name,
        "stars": stars,
        "forks": forks,
        "watchers": watchers,
        "open_issues": open_issues,
        "language": language,
        "repo_topics": repo_topics,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
        "pushed_at": pushed_at.isoformat() if pushed_at else None,
        "latest_release": latest_release or {},
        "hotness_score": round(score, 3),
        "note": "当前热度代理评分，未使用历史 star 增长趋势。",
    }
    abstract_parts = [
        description,
        f"GitHub 元数据：stars={stars}, forks={forks}, watchers={watchers}, open_issues={open_issues}, language={language}.",
    ]
    if repo_topics:
        abstract_parts.append(f"Topics: {', '.join(repo_topics[:12])}.")
    if release_text:
        abstract_parts.append(release_text)
    abstract_parts.append("说明：当前 hotness score 使用 stars、forks、更新时间、release 活跃度、关键词和 language/topics 代理估计，不代表真实增长趋势。")

    return Article(
        id=f"github-{full_name.lower()}",
        source="GitHub",
        source_id=full_name.lower(),
        title=f"GitHub: {full_name}",
        abstract=truncate_text(" ".join(part for part in abstract_parts if part), 1800),
        url=html_url,
        published_at=pushed_at or updated_at or created_at,
        authors=[clean_text((item.get("owner") or {}).get("login"))] if item.get("owner") else [],
        topics=[topic.slug],
        is_preprint=False,
        journal="GitHub Repository",
        relevance_score=score,
        quality_score=score,
        metadata=metadata,
    )


def _fetch_latest_release(full_name: str, headers: dict[str, str]) -> dict[str, Any] | None:
    response = _github_get(f"/repos/{full_name}/releases/latest", headers=headers, timeout=30)
    if response is None:
        return None
    if response.status_code == 404:
        return None
    if response.status_code in {403, 429}:
        LOGGER.warning("GitHub release API 可能触发限流 repo=%s status=%s", full_name, response.status_code)
        return None
    response.raise_for_status()
    data = response.json()
    return {
        "name": clean_text(data.get("name")) or clean_text(data.get("tag_name")),
        "tag_name": clean_text(data.get("tag_name")),
        "published_at": clean_text(data.get("published_at")),
        "url": clean_text(data.get("html_url")),
        "prerelease": bool(data.get("prerelease", False)),
    }


def _hotness_score(
    topic: TopicConfig,
    title: str,
    description: str,
    repo_topics: list[str],
    language: str,
    stars: int,
    forks: int,
    updated_at: datetime | None,
    latest_release: dict[str, Any] | None,
    extra_keywords: list[str],
    language_boosts: set[str],
) -> float:
    text = f"{title} {description} {' '.join(repo_topics)} {language}"
    score = float(keyword_count(text, topic.keywords + extra_keywords))
    score += min(math.log10(stars + 1), 4.0)
    score += min(math.log10(forks + 1), 3.0) * 0.55
    if updated_at:
        days_old = max((datetime.now(timezone.utc) - updated_at).days, 0)
        score += max(0.0, 2.0 - min(days_old, 365) / 180.0)
    if latest_release:
        release_date = parse_datetime(str(latest_release.get("published_at") or ""))
        if release_date:
            days_old = max((datetime.now(timezone.utc) - release_date).days, 0)
            score += max(0.0, 1.5 - min(days_old, 365) / 240.0)
        else:
            score += 0.5
    if repo_topics:
        score += min(len(repo_topics), 8) * 0.08
    if language.lower() in language_boosts:
        score += 0.4
    return round(score, 3)


def _format_release(latest_release: dict[str, Any] | None) -> str:
    if not latest_release:
        return ""
    name = latest_release.get("name") or latest_release.get("tag_name") or "latest release"
    published_at = latest_release.get("published_at") or "unknown date"
    url = latest_release.get("url") or ""
    return f"Latest release: {name} ({published_at}) {url}".strip()


def _to_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
