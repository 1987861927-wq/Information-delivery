from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

LOGGER = logging.getLogger(__name__)


def send_email(
    subject: str,
    text_body: str,
    html_body: str | None = None,
    attachment: Path | None = None,
    skip: bool = False,
) -> bool:
    if skip:
        LOGGER.info("已按参数跳过邮件发送")
        return False
    host = os.getenv("SMTP_HOST", "").strip()
    port = int(os.getenv("SMTP_PORT", "587") or "587")
    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    sender = os.getenv("SMTP_FROM", "").strip() or username
    recipients = [item.strip() for item in os.getenv("SMTP_TO", "").split(",") if item.strip()]
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}
    use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() in {"1", "true", "yes"}
    if not host or not sender or not recipients:
        LOGGER.warning("缺少 SMTP_HOST、SMTP_FROM/SMTP_USERNAME 或 SMTP_TO，跳过邮件发送")
        return False
    if username and not password:
        LOGGER.warning("已设置 SMTP_USERNAME 但缺少 SMTP_PASSWORD，跳过邮件发送")
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")
    if attachment and attachment.exists():
        message.add_attachment(
            attachment.read_bytes(),
            maintype="text",
            subtype="markdown",
            filename=attachment.name,
        )

    if use_ssl:
        server_cls = smtplib.SMTP_SSL
    else:
        server_cls = smtplib.SMTP
    with server_cls(host, port, timeout=45) as server:
        if use_tls and not use_ssl:
            server.starttls()
        if username:
            server.login(username, password)
        server.send_message(message)
    LOGGER.info("邮件发送完成 recipients=%s", len(recipients))
    return True
