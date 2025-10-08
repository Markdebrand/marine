from __future__ import annotations

"""
Email utility for sending notification emails (e.g., contact form) via SMTP.

Configuration comes from app.config.settings:
 - SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
 - SMTP_SSL, SMTP_TLS
 - EMAIL_SENDER (From), EMAIL_TO (list of default recipients)

Exposes:
 - send_email(subject: str, body_text: str | dict, to: list[str] | None = None, reply_to: str | None = None, from_email: str | None = None) -> dict
 - async_send_email(...) -> awaitable wrapper that returns the same dict
"""

import smtplib
from email.message import EmailMessage
from typing import Iterable, List, Optional
import asyncio

from app.config import settings as cfg


class EmailConfigError(RuntimeError):
    pass


def _ensure_base_config():
    if not cfg.SMTP_HOST:
        raise EmailConfigError("SMTP_HOST is not configured")
    if not cfg.EMAIL_SENDER:
        raise EmailConfigError("EMAIL_SENDER (From) is not configured")


def _normalize_recipients(to: Optional[Iterable[str]]) -> List[str]:
    if to:
        recipients = [x.strip() for x in to if x and x.strip()]
    else:
        recipients = list(cfg.EMAIL_TO)
    if not recipients:
        raise EmailConfigError("No recipients provided and EMAIL_TO is empty")
    return recipients


def send_email(subject: str, body_text: str, to: Optional[Iterable[str]] = None, reply_to: Optional[str] = None, from_email: Optional[str] = None, cc: Optional[Iterable[str]] = None) -> dict:
    """Send an email (plain text or HTML) using configured SMTP settings. Returns log/result info.
    If body_html is provided, sends as multipart/alternative.
    If from_email is provided, uses it as the From address.
    """
    import sys
    import traceback
    _ensure_base_config()
    recipients = _normalize_recipients(to)
    cc_list = [x.strip() for x in cc] if cc else []

    # Support for HTML body (optional)
    body_html = None
    if isinstance(body_text, dict):
        # If called with dict, support {"text": ..., "html": ...}
        body_html = body_text.get("html")
        body_text = body_text.get("text", "")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email if from_email else cfg.EMAIL_SENDER
    msg["To"] = ", ".join(recipients)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    if reply_to:
        msg["Reply-To"] = reply_to

    if body_html:
        msg.set_content(body_text)
        msg.add_alternative(body_html, subtype="html")
    else:
        msg.set_content(body_text)

    log = {"recipients": recipients, "cc": cc_list, "result": None, "error": None}
    try:
        if cfg.SMTP_SSL:
            with smtplib.SMTP_SSL(cfg.SMTP_HOST, cfg.SMTP_PORT) as server: # type: ignore
                if cfg.SMTP_USER and cfg.SMTP_PASSWORD:
                    server.login(cfg.SMTP_USER, cfg.SMTP_PASSWORD)
                res = server.send_message(msg, to_addrs=recipients + cc_list)
                log["result"] = str(res)
                print(f"[EMAIL] Sent via SSL to: {recipients}. Result: {res}")
                return log
        # STARTTLS or plain
        with smtplib.SMTP(cfg.SMTP_HOST, cfg.SMTP_PORT) as server: # type: ignore
            server.ehlo()
            if cfg.SMTP_TLS:
                server.starttls()
                server.ehlo()
            if cfg.SMTP_USER and cfg.SMTP_PASSWORD:
                server.login(cfg.SMTP_USER, cfg.SMTP_PASSWORD)
            res = server.send_message(msg, to_addrs=recipients + cc_list)
            log["result"] = str(res)
            print(f"[EMAIL] Sent via TLS/plain to: {recipients}. Result: {res}")
            return log
    except Exception as e:
        log["error"] = f"{e}\n{traceback.format_exc()}"
        print(f"[EMAIL][ERROR] Failed to send to {recipients}: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        raise
    return log


async def async_send_email(subject: str, body_text: str, to: Optional[Iterable[str]] = None, reply_to: Optional[str] = None, from_email: Optional[str] = None, cc: Optional[Iterable[str]] = None) -> dict:
    """
    Async wrapper for send_email. Accepts body_text as str or dict {"text": ..., "html": ...}.
    Allows overriding the From address.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, send_email, subject, body_text, to, reply_to, from_email, cc)
