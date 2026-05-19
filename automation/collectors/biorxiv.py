from __future__ import annotations

from datetime import date
from typing import Any

from automation.collectors.preprint import collect_preprint_server
from automation.models import Article, TopicConfig


def collect_biorxiv(
    topics: list[TopicConfig],
    start_date: date,
    end_date: date,
    source_config: dict[str, Any],
) -> list[Article]:
    return collect_preprint_server("biorxiv", topics, start_date, end_date, source_config)
