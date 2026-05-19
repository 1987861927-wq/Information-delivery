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
    lines.append(f"今日筛选：{total} 条")
    if digest.source_errors:
        lines.append(f"⚠️ 数据源异常：{len(digest.source_errors)} 个，详见邮件或 Markdown 日报")
    lines.append("")
    count = 0
    for topic in digest.topics:
        items = digest.items_by_topic.get(topic.slug, [])
        if not items:
            continue
        lines.append(f"【{topic.name}】")
        for item in items[:2]:
            count += 1
            lines.append(f"{count}. {item.article.title}")
            lines.append(f"   {item.summary.brief[:180]}{'…' if len(item.summary.brief) > 180 else ''}")
            lines.append(f"   {item.article.url}")
            if count >= max_items:
                lines.append("")
                lines.append("完整日报请查看邮件或 GitHub Actions artifact。")
                return "\n".join(lines)
        lines.append("")
    lines.append("完整日报请查看邮件或 GitHub Actions artifact。")
    return "\n".join(lines)


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
