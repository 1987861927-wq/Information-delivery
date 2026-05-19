from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from automation.models import Article, TopicConfig
from automation.utils import keyword_count

SOURCE_WEIGHTS = {
    "PubMed": 1.0,
    "GitHub": 0.88,
    "NIH RePORTER": 0.92,
    "arXiv": 0.82,
    "bioRxiv": 0.78,
    "medRxiv": 0.80,
    "RSS": 0.55,
}

FILTER_MODES = {"off", "rank", "push", "fetch-and-push", "fetch_and_push"}


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


def annotate_journal_metadata(articles: list[Article], journal_catalog: list[dict[str, Any]]) -> list[Article]:
    lookup = _build_journal_lookup(journal_catalog)
    for article in articles:
        match = _match_journal(article.journal, lookup)
        if not match:
            article.journal_filter_reason = "未匹配到本地 top 期刊目录"
            continue
        article.journal_impact_factor = float(match.get("impact_factor") or 0.0)
        article.journal_tier = match.get("tier")
        article.journal_is_whitelisted = bool(match.get("whitelist", True))
        article.journal_filter_reason = f"匹配本地期刊目录：{match.get('name')}"
    return articles


def apply_top_journal_filter(articles: list[Article], filter_config: dict[str, Any]) -> list[Article]:
    mode = normalize_top_journal_filter_mode(str(filter_config.get("mode", "off") or "off"))
    min_impact_factor = float(filter_config.get("min_impact_factor", 10.0) or 10.0)
    keep_unknown_if = bool(filter_config.get("keep_unknown_if", False))
    keep_unknown_sources = {str(item) for item in filter_config.get("keep_unknown_if_sources", [])}

    if mode in {"off", "rank"}:
        for article in articles:
            if article.journal_impact_factor is None:
                article.journal_filter_reason = article.journal_filter_reason or "未启用 IF 过滤，未知 IF 仅参与常规排序"
            elif article.journal_impact_factor >= min_impact_factor and article.journal_is_whitelisted:
                article.journal_filter_reason = f"top 期刊优先排序：白名单且 IF≈{article.journal_impact_factor:g} ≥ {min_impact_factor:g}"
            elif article.journal_impact_factor >= min_impact_factor:
                article.journal_filter_reason = f"IF≈{article.journal_impact_factor:g} ≥ {min_impact_factor:g}，但未在白名单启用"
            else:
                article.journal_filter_reason = f"未启用 IF 过滤：IF≈{article.journal_impact_factor:g} < {min_impact_factor:g}"
        return articles

    filtered: list[Article] = []
    for article in articles:
        if article.journal_impact_factor is not None:
            if article.journal_impact_factor >= min_impact_factor and article.journal_is_whitelisted:
                article.journal_filter_reason = f"保留：白名单期刊且 IF≈{article.journal_impact_factor:g} ≥ {min_impact_factor:g}"
                filtered.append(article)
            elif article.journal_impact_factor >= min_impact_factor:
                article.journal_filter_reason = f"排除：IF≈{article.journal_impact_factor:g} 达标但未在白名单启用"
            else:
                article.journal_filter_reason = f"排除：IF≈{article.journal_impact_factor:g} < {min_impact_factor:g}"
            continue

        if keep_unknown_if or article.source in keep_unknown_sources:
            article.journal_filter_reason = "保留：未知 IF，但配置允许保留该来源"
            filtered.append(article)
        else:
            article.journal_filter_reason = "排除：未知 IF，未进入 top 期刊目录"
    return filtered


def build_pubmed_journal_query(journal_catalog: list[dict[str, Any]], min_impact_factor: float = 10.0) -> str:
    terms: list[str] = []
    seen: set[str] = set()
    for journal in journal_catalog:
        impact_factor = float(journal.get("impact_factor") or 0.0)
        if impact_factor < min_impact_factor or not bool(journal.get("whitelist", True)):
            continue
        candidates = [str(journal.get("name", "")), *[str(item) for item in journal.get("aliases", [])]]
        for candidate in candidates:
            cleaned = candidate.strip()
            normalized = normalize_journal_name(cleaned)
            if not cleaned or normalized in seen:
                continue
            seen.add(normalized)
            terms.append(f'"{cleaned}"[Journal]')
    if not terms:
        return ""
    return "(" + " OR ".join(terms) + ")"


def compute_quality_score(article: Article) -> float:
    score = SOURCE_WEIGHTS.get(article.source, 0.5)
    if article.abstract and len(article.abstract) > 400:
        score += 0.2
    if article.doi:
        score += 0.1
    if article.journal_impact_factor is not None:
        score += min(article.journal_impact_factor / 100.0, 0.45)
    if article.journal_is_whitelisted:
        score += 0.05
    source_signal = article.metadata.get("hotness_score") or article.metadata.get("importance_score")
    if source_signal is not None:
        try:
            score += min(float(source_signal) / 10.0, 0.6)
        except (TypeError, ValueError):
            pass
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
                article.journal_impact_factor or 0,
                article.published_at.timestamp() if article.published_at else 0,
            ),
            reverse=True,
        )
        selected[topic.slug] = topic_articles[:limit]
    return selected


def normalize_journal_name(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _build_journal_lookup(journal_catalog: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for journal in journal_catalog:
        candidates = [str(journal.get("name", "")), *[str(item) for item in journal.get("aliases", [])]]
        for candidate in candidates:
            normalized = normalize_journal_name(candidate)
            if normalized:
                lookup[normalized] = journal
    return lookup


def _match_journal(journal_name: str | None, lookup: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    normalized = normalize_journal_name(journal_name)
    if not normalized:
        return None
    return lookup.get(normalized)


def normalize_top_journal_filter_mode(mode: str) -> str:
    normalized = mode.strip().lower().replace("_", "-")
    if normalized not in FILTER_MODES:
        return "off"
    return normalized
