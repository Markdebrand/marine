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
    import time
    from datetime import datetime
    
    start_time = time.time()
    print(f"\n[EMAIL][{datetime.now().isoformat()}] Starting email send process")
    
    _ensure_base_config()
    recipients = _normalize_recipients(to)
    cc_list = [x.strip() for x in cc] if cc else []
    
    print(f"[EMAIL] Recipients: {recipients}, CC: {cc_list}")

    # Support for HTML body (optional)
    body_html = None
    if isinstance(body_text, dict):
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
            print(f"[EMAIL] Using SSL connection to {cfg.SMTP_HOST}:{cfg.SMTP_PORT}")
            conn_start = time.time()
            with smtplib.SMTP_SSL(cfg.SMTP_HOST, cfg.SMTP_PORT, timeout=30) as server: # type: ignore
                conn_time = time.time() - conn_start
                print(f"[EMAIL] ✓ SSL connection established in {conn_time:.2f}s")
                
                if cfg.SMTP_USER and cfg.SMTP_PASSWORD:
                    login_start = time.time()
                    print(f"[EMAIL] Logging in as {cfg.SMTP_USER}...")
                    server.login(cfg.SMTP_USER, cfg.SMTP_PASSWORD)
                    login_time = time.time() - login_start
                    print(f"[EMAIL] ✓ Login successful in {login_time:.2f}s")
                
                send_start = time.time()
                print(f"[EMAIL] Sending message...")
                res = server.send_message(msg, to_addrs=recipients + cc_list)
                send_time = time.time() - send_start
                print(f"[EMAIL] ✓ Message sent in {send_time:.2f}s")
                
                log["result"] = str(res)
                total_time = time.time() - start_time
                print(f"[EMAIL] ✓ TOTAL TIME: {total_time:.2f}s")
                return log
                
        # STARTTLS or plain
        print(f"[EMAIL] Using STARTTLS connection to {cfg.SMTP_HOST}:{cfg.SMTP_PORT}")
        conn_start = time.time()
        with smtplib.SMTP(cfg.SMTP_HOST, cfg.SMTP_PORT, timeout=30) as server: # type: ignore
            conn_time = time.time() - conn_start
            print(f"[EMAIL] ✓ Connection established in {conn_time:.2f}s")
            
            ehlo_start = time.time()
            server.ehlo()
            ehlo_time = time.time() - ehlo_start
            print(f"[EMAIL] ✓ EHLO completed in {ehlo_time:.2f}s")
            
            if cfg.SMTP_TLS:
                tls_start = time.time()
                print(f"[EMAIL] Starting TLS...")
                server.starttls()
                tls_time = time.time() - tls_start
                print(f"[EMAIL] ✓ TLS started in {tls_time:.2f}s")
                
                ehlo2_start = time.time()
                server.ehlo()
                ehlo2_time = time.time() - ehlo2_start
                print(f"[EMAIL] ✓ EHLO after TLS in {ehlo2_time:.2f}s")
            
            if cfg.SMTP_USER and cfg.SMTP_PASSWORD:
                login_start = time.time()
                print(f"[EMAIL] Logging in as {cfg.SMTP_USER}...")
                server.login(cfg.SMTP_USER, cfg.SMTP_PASSWORD)
                login_time = time.time() - login_start
                print(f"[EMAIL] ✓ Login successful in {login_time:.2f}s")
            
            send_start = time.time()
            print(f"[EMAIL] Sending message...")
            res = server.send_message(msg, to_addrs=recipients + cc_list)
            send_time = time.time() - send_start
            print(f"[EMAIL] ✓ Message sent in {send_time:.2f}s")
            
            log["result"] = str(res)
            total_time = time.time() - start_time
            print(f"[EMAIL] ✓ TOTAL TIME: {total_time:.2f}s\n")
            return log
    except Exception as e:
        total_time = time.time() - start_time
        log["error"] = f"{e}\n{traceback.format_exc()}"
        print(f"[EMAIL][ERROR] Failed after {total_time:.2f}s: {e}", file=sys.stderr)
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
