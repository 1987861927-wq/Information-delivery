from __future__ import annotations

import logging
import os
from pathlib import Path

import requests

LOGGER = logging.getLogger(__name__)
TELEGRAM_LIMIT = 3900


def send_telegram_message(text: str, markdown_file: Path | None = None, skip: bool = False) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if skip:
        LOGGER.info("已按参数跳过 Telegram 推送")
        return False
    if not token or not chat_id:
        LOGGER.warning("缺少 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID，跳过 Telegram 推送")
        return False
    chunks = _split_message(text)
    for chunk in chunks:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": chunk, "disable_web_page_preview": True},
            timeout=30,
        )
        response.raise_for_status()
    if markdown_file and markdown_file.exists():
        with markdown_file.open("rb") as file:
            response = requests.post(
                f"https://api.telegram.org/bot{token}/sendDocument",
                data={"chat_id": chat_id, "caption": "完整 Markdown 日报"},
                files={"document": (markdown_file.name, file, "text/markdown")},
                timeout=60,
            )
            response.raise_for_status()
    LOGGER.info("Telegram 推送完成 messages=%s document=%s", len(chunks), bool(markdown_file))
    return True


def _split_message(text: str) -> list[str]:
    if len(text) <= TELEGRAM_LIMIT:
        return [text]
    chunks: list[str] = []
    current: list[str] = []
    size = 0
    for line in text.splitlines():
        line_size = len(line) + 1
        if size + line_size > TELEGRAM_LIMIT and current:
            chunks.append("\n".join(current))
            current = []
            size = 0
        current.append(line)
        size += line_size
    if current:
        chunks.append("\n".join(current))
    return chunks
