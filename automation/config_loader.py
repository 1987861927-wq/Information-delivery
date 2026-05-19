from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from automation.models import DigestConfig, TopicConfig


class ConfigError(RuntimeError):
    pass


def load_environment(env_file: str | Path | None = None) -> None:
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"配置文件不存在: {path}")
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"配置文件格式错误，顶层必须是对象: {path}")
    return data


def load_topics_config(path: str | Path = "config/topics.yml") -> tuple[DigestConfig, list[TopicConfig]]:
    data = _read_yaml(Path(path))
    digest_data = data.get("digest") or {}
    topics_data = data.get("topics") or []
    if not isinstance(topics_data, list) or not topics_data:
        raise ConfigError("topics.yml 必须包含非空 topics 列表")

    digest_config = DigestConfig(**digest_data)
    topics: list[TopicConfig] = []
    for raw in topics_data:
        if not isinstance(raw, dict):
            raise ConfigError("每个 topic 必须是对象")
        topics.append(
            TopicConfig(
                slug=str(raw["slug"]),
                name=str(raw["name"]),
                description=str(raw.get("description", "")),
                keywords=[str(item) for item in raw.get("keywords", [])],
                exclude_keywords=[str(item) for item in raw.get("exclude_keywords", [])],
                pubmed_query=raw.get("pubmed_query"),
                arxiv_query=raw.get("arxiv_query"),
                max_items=raw.get("max_items"),
            )
        )
    return digest_config, topics


def load_sources_config(path: str | Path = "config/sources.yml") -> dict[str, Any]:
    data = _read_yaml(Path(path))
    sources = data.get("sources") or {}
    if not isinstance(sources, dict):
        raise ConfigError("sources.yml 必须包含 sources 对象")
    return sources


def filter_topics(topics: list[TopicConfig], selected_slugs: list[str] | None) -> list[TopicConfig]:
    if not selected_slugs:
        return topics
    selected = set(selected_slugs)
    filtered = [topic for topic in topics if topic.slug in selected]
    missing = selected - {topic.slug for topic in filtered}
    if missing:
        raise ConfigError(f"未知主题: {', '.join(sorted(missing))}")
    return filtered
