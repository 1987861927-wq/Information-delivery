from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import requests

from automation.models import Article, ArticleSummary, TopicConfig
from automation.utils import truncate_text

LOGGER = logging.getLogger(__name__)


def summarize_article(article: Article, topics: list[TopicConfig]) -> ArticleSummary:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return rule_based_summary(article)
    try:
        return llm_summary(article=article, topics=topics, api_key=api_key)
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("LLM 摘要失败，回退到规则摘要 article=%s error=%s", article.id, exc)
        fallback = rule_based_summary(article)
        fallback.limitations = (fallback.limitations + f"；LLM 摘要失败，已回退规则摘要：{exc}").strip("；")
        return fallback


def rule_based_summary(article: Article) -> ArticleSummary:
    source_hint = "预印本" if article.is_preprint else "正式论文或资讯"
    focus_terms = _detect_focus_terms(article)
    focus = "、".join(focus_terms) if focus_terms else _topic_hint(article)
    method = _guess_method(article)
    value = _guess_value(article)
    brief = (
        f"来自 {article.source} 的{source_hint}，主要聚焦{focus}。"
        f"{method.rstrip('。')}；{value.rstrip('。')}。"
    )
    conclusions = _rule_based_chinese_conclusions(article=article, focus=focus, method=method, value=value)
    limitations = "规则模板摘要，仅基于标题和摘要进行中文归纳，未进行全文事实校验；建议打开原文确认研究设计、样本量和统计结果。"
    if article.is_preprint:
        limitations += " 该内容为预印本，通常尚未完成同行评议。"
    return ArticleSummary(
        brief=brief,
        key_conclusions=conclusions,
        method_highlights=method,
        value_judgement=value,
        limitations=limitations,
    )


def llm_summary(article: Article, topics: list[TopicConfig], api_key: str) -> ArticleSummary:
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    timeout = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "45"))
    matched_topics = [topic.name for topic in topics if topic.slug in article.topics]
    prompt = f"""
你是严谨的科研情报分析助手。请基于给定论文/资讯标题和摘要生成中文结构化摘要。
要求：
1. 不要夸大，不要编造摘要中没有的信息。
2. 如果是预印本，明确提示证据等级限制。
3. 输出严格 JSON，不要 Markdown。
4. JSON 字段必须包括：brief, key_conclusions, method_highlights, value_judgement, limitations。
5. key_conclusions 是 2-4 条中文字符串数组。

主题：{', '.join(matched_topics) or '未指定'}
来源：{article.source}
标题：{article.title}
摘要：{article.abstract or '无摘要'}
链接：{article.url}
""".strip()
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是专业、谨慎、擅长中文科研摘要的助手。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    response = requests.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    data = json.loads(content)
    conclusions = data.get("key_conclusions") or []
    if isinstance(conclusions, str):
        conclusions = [conclusions]
    return ArticleSummary(
        brief=str(data.get("brief") or "未生成摘要。"),
        key_conclusions=[str(item) for item in conclusions][:4],
        method_highlights=str(data.get("method_highlights") or "未识别方法亮点。"),
        value_judgement=str(data.get("value_judgement") or "需要结合原文进一步判断价值。"),
        limitations=str(data.get("limitations") or "未识别明确局限性。"),
    )


def _rule_based_chinese_conclusions(article: Article, focus: str, method: str, value: str) -> list[str]:
    conclusions = [f"该内容与{focus}相关，可作为今日主题线索优先浏览。"]
    if article.abstract:
        if method != "方法细节需阅读原文确认。":
            conclusions.append(f"摘要提示研究可能涉及{method.rstrip('。')}，但具体设计和证据强度需以原文为准。")
        else:
            conclusions.append("摘要提供了初步背景和结果线索，但方法细节、样本量和结论边界需阅读原文确认。")
    else:
        conclusions.append("原始摘要信息有限，建议打开原文进一步确认研究目的、方法和主要发现。")
    conclusions.append(f"初步价值：{value.rstrip('。')}。")
    if article.is_preprint:
        conclusions.append("该内容为预印本，应关注同行评议状态和后续独立验证。")
    return conclusions[:4]



def _detect_focus_terms(article: Article) -> list[str]:
    text = f"{article.title} {article.abstract or ''}".lower()
    candidates = [
        ("large language model", "大语言模型"),
        ("llm", "大语言模型"),
        ("foundation model", "基础模型"),
        ("artificial intelligence", "人工智能"),
        ("machine learning", "机器学习"),
        ("deep learning", "深度学习"),
        ("medical imaging", "医学影像"),
        ("bioinformatics", "生物信息学"),
        ("multimodal", "多模态模型"),
        ("neuroimaging", "神经影像"),
        ("neurodegeneration", "神经退行性疾病"),
        ("alzheimer", "阿尔茨海默病"),
        ("parkinson", "帕金森病"),
        ("stroke", "卒中"),
        ("brain-computer", "脑机接口"),
        ("hydrogel", "水凝胶"),
        ("scaffold", "组织工程支架"),
        ("tissue engineering", "组织工程"),
        ("regenerative medicine", "再生医学"),
        ("drug delivery", "药物递送"),
        ("implant", "植入物"),
        ("bone regeneration", "骨再生"),
        ("cartilage", "软骨"),
        ("osteoarthritis", "骨关节炎"),
        ("fracture", "骨折愈合"),
        ("arthroplasty", "关节置换"),
        ("spine", "脊柱外科"),
    ]
    terms: list[str] = []
    for needle, label in candidates:
        if needle in text and label not in terms:
            terms.append(label)
        if len(terms) >= 4:
            break
    if not terms:
        for label in _topic_labels(article):
            if label not in terms:
                terms.append(label)
    return terms[:4]



def _topic_hint(article: Article) -> str:
    labels = _topic_labels(article)
    return "、".join(labels) if labels else "当前关注主题"



def _topic_labels(article: Article) -> list[str]:
    mapping = {
        "neuroscience": "神经科学",
        "biomaterials": "生物材料",
        "ai": "人工智能",
        "orthopedics": "骨科",
    }
    return [mapping[topic] for topic in article.topics if topic in mapping]



def _extract_sentences(text: str | None, max_count: int = 3) -> list[str]:
    if not text:
        return []
    normalized = text.replace("\n", " ")
    parts = []
    for sentence in normalized.replace("?", ".").replace("!", ".").split("."):
        cleaned = sentence.strip()
        if len(cleaned) >= 30:
            parts.append(truncate_text(cleaned, 180))
        if len(parts) >= max_count:
            break
    return parts


def _guess_method(article: Article) -> str:
    text = f"{article.title} {article.abstract or ''}".lower()
    hints = []
    if _has_terms(text, ["randomized", "trial", "cohort", "patient", "patients", "clinical trial"]):
        hints.append("可能包含临床研究设计")
    if _has_terms(text, ["mouse", "mice", "rat", "rats", "in vivo", "animal", "preclinical"]):
        hints.append("可能包含临床前、动物或体内实验")
    if _has_terms(
        text,
        [
            "deep learning",
            "machine learning",
            "large language model",
            "foundation model",
            "neural network",
            "algorithm",
            "computer vision",
        ],
    ):
        hints.append("可能包含机器学习或模型方法")
    if _has_terms(text, ["hydrogel", "scaffold", "biomaterial", "material", "implant", "coating"]):
        hints.append("可能包含材料制备或性能评价")
    return "；".join(hints) if hints else "方法细节需阅读原文确认。"



def _has_terms(text: str, terms: list[str]) -> bool:
    for term in terms:
        pattern = r"(?<![a-z0-9])" + re.escape(term.lower()).replace(r"\ ", r"\s+") + r"(?![a-z0-9])"
        if re.search(pattern, text):
            return True
    return False


def _guess_value(article: Article) -> str:
    topics = set(article.topics)
    values = []
    if "orthopedics" in topics:
        values.append("可能对骨科诊疗、骨修复或植入物研究有参考价值")
    if "biomaterials" in topics:
        values.append("可能对生物材料设计、组织工程或再生医学有启发")
    if "neuroscience" in topics:
        values.append("可能对神经机制理解、疾病研究或神经技术有参考价值")
    if "ai" in topics:
        values.append("可能对 AI 方法、医学智能分析或科研自动化有借鉴意义")
    return "；".join(values) if values else "科研或应用价值需结合原文进一步判断。"
