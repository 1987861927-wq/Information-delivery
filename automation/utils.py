from __future__ import annotations

import logging
import re
from datetime import date, datetime, time, timedelta, timezone
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def resolve_digest_date(value: str | None, timezone_name: str) -> date:
    if value:
        return datetime.strptime(value, "%Y-%m-%d").date()
    return datetime.now(ZoneInfo(timezone_name)).date()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def make_since_date(digest_date: date, days_back: int) -> date:
    return digest_date - timedelta(days=max(days_back, 1) - 1)


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    cleaned = value.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            parsed = datetime.strptime(cleaned, fmt)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            pass
    try:
        parsed = parsedate_to_datetime(cleaned)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError, IndexError, OverflowError):
        return None


def parsed_struct_time_to_datetime(value: object) -> datetime | None:
    if not value:
        return None
    try:
        parts = tuple(value)[:6]  # type: ignore[arg-type]
        return datetime(*parts, tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def clean_text(value: str | None, max_spaces: bool = True) -> str:
    if not value:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", value)
    cleaned = cleaned.replace("\xa0", " ")
    if max_spaces:
        cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def truncate_text(value: str | None, limit: int = 600) -> str:
    text = clean_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def keyword_count(text: str, keywords: list[str]) -> int:
    lowered = text.lower()
    count = 0
    for keyword in keywords:
        key = keyword.lower().strip()
        if key and key in lowered:
            count += 1
    return count


def format_date_time(value: datetime | None) -> str:
    if not value:
        return "未知"
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d")


def iso_date_range(start: date, end: date) -> tuple[str, str]:
    return start.isoformat(), end.isoformat()


def pubmed_date_range(start: date, end: date) -> str:
    return f'("{start.strftime("%Y/%m/%d")}"[PDAT] : "{end.strftime("%Y/%m/%d")}"[PDAT])'


def safe_join(values: list[str], sep: str = ", ", limit: int = 5) -> str:
    non_empty = [value for value in values if value]
    if not non_empty:
        return ""
    rendered = sep.join(non_empty[:limit])
    if len(non_empty) > limit:
        rendered += " 等"
    return rendered
