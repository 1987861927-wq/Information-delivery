from __future__ import annotations

from automation.models import Digest, DigestItem
from automation.utils import format_date_time, safe_join


def render_markdown(digest: Digest) -> str:
    lines: list[str] = []
    lines.append(f"# {digest.title}｜{digest.date}")
    lines.append("")
    lines.append(f"生成时间：{digest.generated_at.isoformat() if digest.generated_at else '未知'}")
    lines.append("")
    total = sum(len(items) for items in digest.items_by_topic.values())
    lines.append(f"今日共筛选出 **{total}** 条内容。")
    lines.append("")
    if digest.source_errors:
        lines.append("## 数据源异常提示")
        lines.append("")
        for error in digest.source_errors:
            lines.append(f"- **{error.source}**：{error.message}")
        lines.append("")
    lines.append("## 今日重点")
    lines.append("")
    highlights = _pick_highlights(digest)
    if highlights:
        for index, item in enumerate(highlights, start=1):
            article = item.article
            lines.append(f"{index}. [{article.title}]({article.url}) — {item.summary.brief}")
    else:
        lines.append("暂无内容。")
    lines.append("")

    for topic in digest.topics:
        items = digest.items_by_topic.get(topic.slug, [])
        lines.append(f"## {topic.name}")
        lines.append("")
        if not items:
            lines.append("今日未筛选到足够相关的新内容。")
            lines.append("")
            continue
        for index, item in enumerate(items, start=1):
            lines.extend(_render_item(index, item))
            lines.append("")
    lines.append("---")
    lines.append("提示：预印本通常尚未完成同行评议；中文摘要由自动化脚本生成，重要结论请以原文为准。")
    lines.append("")
    return "\n".join(lines)


def render_telegram_preview(digest: Digest, max_items: int = 8) -> str:
    lines: list[str] = []
    lines.append(f"📚 {digest.title}｜{digest.date}")
    total = sum(len(items) for items in digest.items_by_topic.values())
    lines.append(f"今日筛选：{total} 条；以下为手机端精炼中文要点。")
    if digest.source_errors:
        lines.append(f"⚠️ 数据源异常：{len(digest.source_errors)} 个，详见 Markdown 日报附件或 GitHub Actions artifact。")
    lines.append("")
    count = 0
    for topic in digest.topics:
        items = digest.items_by_topic.get(topic.slug, [])
        if not items:
            continue
        lines.append(f"【{topic.name}】")
        for item in items[:2]:
            count += 1
            summary = item.summary
            conclusion = _first_non_empty(summary.key_conclusions) or "暂无明确关键结论，建议打开原文核对。"
            lines.append(f"{count}. {item.article.title}")
            lines.append(f"   精炼总结：{_truncate_line(summary.brief, 150)}")
            lines.append(f"   关键结论：{_truncate_line(conclusion, 130)}")
            lines.append(f"   价值判断：{_truncate_line(summary.value_judgement, 120)}")
            lines.append(f"   链接：{item.article.url}")
            if count >= max_items:
                lines.append("")
                lines.append("完整 Markdown 日报会作为 Telegram 附件发送；也可在 GitHub Actions artifact 中下载。")
                return "\n".join(lines)
        lines.append("")
    lines.append("完整 Markdown 日报会作为 Telegram 附件发送；也可在 GitHub Actions artifact 中下载。")
    return "\n".join(lines)



def _truncate_line(text: str | None, limit: int) -> str:
    cleaned = " ".join((text or "").split())
    if not cleaned:
        return "暂无。"
    return f"{cleaned[:limit]}…" if len(cleaned) > limit else cleaned



def _first_non_empty(items: list[str]) -> str | None:
    for item in items:
        cleaned = " ".join(item.split())
        if cleaned:
            return cleaned
    return None


def _render_item(index: int, item: DigestItem) -> list[str]:
    article = item.article
    summary = item.summary
    authors = safe_join(article.authors, limit=4)
    lines = [
        f"### {index}. {article.title}",
        "",
        f"- 来源：{article.source}{' / ' + article.journal if article.journal else ''}",
        f"- 发布时间：{format_date_time(article.published_at)}",
        f"- 作者：{authors or '未知'}",
        f"- 原文链接：{article.url}",
        f"- 预印本：{'是' if article.is_preprint else '否'}",
        "",
        f"**简短中文摘要：** {summary.brief}",
        "",
        "**关键结论：**",
    ]
    for conclusion in summary.key_conclusions:
        lines.append(f"- {conclusion}")
    lines.extend(
        [
            "",
            f"**方法或技术亮点：** {summary.method_highlights}",
            "",
            f"**科研或临床价值判断：** {summary.value_judgement}",
            "",
            f"**局限性/注意事项：** {summary.limitations}",
        ]
    )
    return lines


def _pick_highlights(digest: Digest) -> list[DigestItem]:
    all_items = [item for items in digest.items_by_topic.values() for item in items]
    all_items.sort(
        key=lambda item: (item.article.relevance_score, item.article.quality_score),
        reverse=True,
    )
    return all_items[:3]
