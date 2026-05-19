from __future__ import annotations

import html

from automation.models import Digest
from automation.renderers.markdown import _pick_highlights
from automation.utils import format_date_time, safe_join


def render_html(digest: Digest) -> str:
    total = sum(len(items) for items in digest.items_by_topic.values())
    body: list[str] = []
    body.append("<!doctype html><html><head><meta charset='utf-8'>")
    body.append("<meta name='viewport' content='width=device-width, initial-scale=1'>")
    body.append(f"<title>{html.escape(digest.title)}｜{html.escape(digest.date)}</title>")
    body.append("""
<style>
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,'PingFang SC','Microsoft YaHei',sans-serif;line-height:1.65;color:#17202a;background:#f6f8fa;margin:0;padding:0}
.container{max-width:860px;margin:0 auto;padding:18px}
.card{background:#fff;border:1px solid #e6e8eb;border-radius:14px;padding:16px;margin:14px 0;box-shadow:0 2px 10px rgba(0,0,0,.03)}
h1{font-size:24px;margin:12px 0}h2{font-size:20px;margin-top:28px}h3{font-size:17px;margin:0 0 8px}
a{color:#0b65c2;text-decoration:none}.meta{color:#606b76;font-size:13px}.tag{display:inline-block;background:#eef6ff;color:#0b65c2;border-radius:999px;padding:2px 8px;margin-right:6px;font-size:12px}
ul{padding-left:20px}.warning{background:#fff8e1;border-color:#ffe3a3}.footer{color:#606b76;font-size:13px;margin:28px 0}
</style></head><body><div class='container'>
""")
    body.append(f"<h1>📚 {html.escape(digest.title)}｜{html.escape(digest.date)}</h1>")
    body.append(f"<p class='meta'>今日共筛选出 {total} 条内容。生成时间：{html.escape(digest.generated_at.isoformat() if digest.generated_at else '未知')}</p>")
    if digest.source_errors:
        body.append("<div class='card warning'><h2>⚠️ 数据源异常提示</h2><ul>")
        for error in digest.source_errors:
            body.append(f"<li><strong>{html.escape(error.source)}</strong>：{html.escape(error.message)}</li>")
        body.append("</ul></div>")
    body.append("<div class='card'><h2>今日重点</h2><ol>")
    for item in _pick_highlights(digest):
        body.append(f"<li><a href='{html.escape(item.article.url)}'>{html.escape(item.article.title)}</a><br>{html.escape(item.summary.brief)}</li>")
    body.append("</ol></div>")

    for topic in digest.topics:
        body.append(f"<h2>{html.escape(topic.name)}</h2>")
        items = digest.items_by_topic.get(topic.slug, [])
        if not items:
            body.append("<div class='card'><p>今日未筛选到足够相关的新内容。</p></div>")
            continue
        for index, item in enumerate(items, start=1):
            article = item.article
            summary = item.summary
            body.append("<div class='card'>")
            body.append(f"<h3>{index}. <a href='{html.escape(article.url)}'>{html.escape(article.title)}</a></h3>")
            body.append("<p class='meta'>")
            body.append(f"<span class='tag'>{html.escape(article.source)}</span>")
            if article.is_preprint:
                body.append("<span class='tag'>预印本</span>")
            body.append(f" 发布时间：{html.escape(format_date_time(article.published_at))}")
            if article.journal:
                body.append(f"｜{html.escape(article.journal)}")
            authors = safe_join(article.authors, limit=4)
            if authors:
                body.append(f"｜作者：{html.escape(authors)}")
            body.append("</p>")
            body.append(f"<p><strong>简短中文摘要：</strong>{html.escape(summary.brief)}</p>")
            body.append("<p><strong>关键结论：</strong></p><ul>")
            for conclusion in summary.key_conclusions:
                body.append(f"<li>{html.escape(conclusion)}</li>")
            body.append("</ul>")
            body.append(f"<p><strong>方法或技术亮点：</strong>{html.escape(summary.method_highlights)}</p>")
            body.append(f"<p><strong>科研或临床价值判断：</strong>{html.escape(summary.value_judgement)}</p>")
            body.append(f"<p><strong>局限性/注意事项：</strong>{html.escape(summary.limitations)}</p>")
            body.append(f"<p><a href='{html.escape(article.url)}'>打开原文</a></p>")
            body.append("</div>")
    body.append("<p class='footer'>提示：预印本通常尚未完成同行评议；中文摘要由自动化脚本生成，重要结论请以原文为准。</p>")
    body.append("</div></body></html>")
    return "\n".join(body)
