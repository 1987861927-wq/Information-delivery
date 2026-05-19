#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from automation.collectors import collect_arxiv, collect_biorxiv, collect_medrxiv, collect_pubmed, collect_rss
from automation.config_loader import filter_topics, load_environment, load_sources_config, load_topics_config
from automation.models import Article, Digest, DigestItem, SourceError
from automation.notifiers import send_email, send_telegram_message
from automation.processing import assign_topics_and_scores, dedupe_articles, select_items_by_topic
from automation.renderers import render_html, render_markdown, render_telegram_preview
from automation.summarizer import summarize_article
from automation.utils import make_since_date, resolve_digest_date, setup_logging, utc_now

LOGGER = logging.getLogger("daily_digest")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成科研情报日报并推送到 Telegram 和邮箱")
    parser.add_argument("--date", dest="digest_date", help="日报日期，格式 YYYY-MM-DD，默认使用配置时区当天")
    parser.add_argument("--topics", nargs="+", help="只运行指定主题 slug，例如 ai neuroscience")
    parser.add_argument("--max-items", type=int, help="覆盖每个主题最多条目数")
    parser.add_argument("--days-back", type=int, help="向前抓取天数，默认读取 config/topics.yml")
    parser.add_argument("--topics-config", default="config/topics.yml", help="主题配置文件路径")
    parser.add_argument("--sources-config", default="config/sources.yml", help="数据源配置文件路径")
    parser.add_argument("--output-dir", default=None, help="日报输出目录，默认 data/digests")
    parser.add_argument("--skip-telegram", action="store_true", help="跳过 Telegram 推送")
    parser.add_argument("--skip-email", action="store_true", help="跳过邮件推送")
    parser.add_argument("--preview", action="store_true", help="只打印 Telegram 预览，不发送推送")
    parser.add_argument("--no-fetch", action="store_true", help="不访问外部数据源，使用本地样例数据生成日报，便于自检")
    parser.add_argument("--verbose", action="store_true", help="输出 DEBUG 日志")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(verbose=args.verbose)
    load_environment()

    try:
        digest_config, topics = load_topics_config(args.topics_config)
        sources_config = load_sources_config(args.sources_config)
        topics = filter_topics(topics, args.topics)
        target_date = resolve_digest_date(args.digest_date, digest_config.timezone)
        days_back = args.days_back or digest_config.default_days_back
        start_date = make_since_date(target_date, days_back)
        output_dir = Path(args.output_dir or "data/digests") / target_date.isoformat()
        output_dir.mkdir(parents=True, exist_ok=True)

        if args.no_fetch:
            articles: list[Article] = _sample_articles(target_date)
            source_errors: list[SourceError] = []
        else:
            articles, source_errors = collect_all_sources(
                topics=topics,
                start_date=start_date,
                end_date=target_date,
                sources_config=sources_config,
            )

        LOGGER.info("采集完成 raw_articles=%s source_errors=%s", len(articles), len(source_errors))
        articles = assign_topics_and_scores(articles, topics)
        articles = dedupe_articles(articles)
        LOGGER.info("去重和主题匹配完成 articles=%s", len(articles))
        selected = select_items_by_topic(
            articles=articles,
            topics=topics,
            default_limit=digest_config.default_max_items_per_topic,
            override_limit=args.max_items,
        )

        items_by_topic: dict[str, list[DigestItem]] = {}
        for topic in topics:
            items_by_topic[topic.slug] = []
            for article in selected.get(topic.slug, []):
                summary = summarize_article(article, topics)
                items_by_topic[topic.slug].append(DigestItem(article=article, summary=summary))

        digest = Digest(
            date=target_date.isoformat(),
            title=digest_config.title,
            topics=topics,
            items_by_topic=items_by_topic,
            source_errors=source_errors,
            generated_at=utc_now(),
        )
        markdown = render_markdown(digest)
        html = render_html(digest)
        telegram_preview = render_telegram_preview(digest)

        markdown_path = output_dir / "digest.md"
        html_path = output_dir / "digest.html"
        json_path = output_dir / "digest.json"
        markdown_path.write_text(markdown, encoding="utf-8")
        html_path.write_text(html, encoding="utf-8")
        json_path.write_text(json.dumps(_json_safe_digest(digest), ensure_ascii=False, indent=2), encoding="utf-8")
        LOGGER.info("日报已保存 markdown=%s html=%s json=%s", markdown_path, html_path, json_path)

        if args.preview:
            print(telegram_preview)
            LOGGER.info("预览模式：跳过 Telegram 和邮件发送")
            return 0

        send_telegram_message(
            text=telegram_preview,
            markdown_file=markdown_path,
            skip=args.skip_telegram,
        )
        send_email(
            subject=f"{digest.title}｜{digest.date}",
            text_body=markdown,
            html_body=html,
            attachment=markdown_path,
            skip=args.skip_email,
        )
        return 0
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("日报生成失败: %s", exc)
        return 1


def collect_all_sources(
    topics,
    start_date: date,
    end_date: date,
    sources_config: dict,
) -> tuple[list[Article], list[SourceError]]:
    collectors = [
        ("PubMed", collect_pubmed, sources_config.get("pubmed", {})),
        ("arXiv", collect_arxiv, sources_config.get("arxiv", {})),
        ("RSS", collect_rss, sources_config.get("rss", {})),
        ("bioRxiv", collect_biorxiv, sources_config.get("biorxiv", {})),
        ("medRxiv", collect_medrxiv, sources_config.get("medrxiv", {})),
    ]
    articles: list[Article] = []
    errors: list[SourceError] = []
    for source_name, collector, config in collectors:
        try:
            LOGGER.info("开始采集 %s", source_name)
            collected = collector(topics, start_date, end_date, config)
            articles.extend(collected)
            LOGGER.info("%s 采集完成 count=%s", source_name, len(collected))
        except Exception as exc:  # noqa: BLE001
            message = str(exc)
            LOGGER.exception("%s 采集失败，但继续其他数据源: %s", source_name, message)
            errors.append(SourceError(source=source_name, message=message[:500]))
    return articles, errors


def _sample_articles(target_date: date) -> list[Article]:
    from datetime import datetime, timezone

    return [
        Article(
            id="sample-ai-001",
            source="arXiv",
            title="Large language models for biomedical literature triage",
            abstract="This paper evaluates large language models for biomedical literature triage and summarizes their strengths and limitations in screening scientific abstracts.",
            url="https://arxiv.org/",
            published_at=datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc),
            topics=["ai"],
            is_preprint=True,
            relevance_score=3,
            quality_score=0.8,
        ),
        Article(
            id="sample-neuro-001",
            source="PubMed",
            title="Neuroimaging biomarkers in early neurodegeneration",
            abstract="The study reviews neuroimaging biomarkers associated with early neurodegeneration and discusses their potential clinical utility in risk stratification.",
            url="https://pubmed.ncbi.nlm.nih.gov/",
            published_at=datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc),
            topics=["neuroscience"],
            relevance_score=3,
            quality_score=1.0,
        ),
        Article(
            id="sample-biomaterials-001",
            source="bioRxiv",
            title="Hydrogel scaffold design for bone regeneration",
            abstract="A bioactive hydrogel scaffold was designed to support osteogenic differentiation and improve bone regeneration in a preclinical model.",
            url="https://www.biorxiv.org/",
            published_at=datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc),
            topics=["biomaterials", "orthopedics"],
            is_preprint=True,
            relevance_score=4,
            quality_score=0.9,
        ),
    ]


def _json_safe_digest(digest: Digest) -> dict:
    data = digest.to_dict()
    for items in data["items_by_topic"].values():
        for item in items:
            article = item["article"]
            if article.get("published_at") is not None:
                article["published_at"] = article["published_at"].isoformat()
    return data


if __name__ == "__main__":
    raise SystemExit(main())
