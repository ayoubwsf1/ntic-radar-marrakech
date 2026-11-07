from __future__ import annotations

import email
import email.policy
from dataclasses import dataclass
from datetime import datetime, timezone
from email.header import decode_header, make_header
from email.utils import getaddresses, parsedate_to_datetime

from .text_utils import html_to_text


@dataclass
class Parsed:
    subject: str
    from_name: str
    from_addrs: list
    to_addrs: list
    date: datetime
    body: str
    multipart_mixed: bool


def _decode(s) -> str:
    s = str(s or "")
    try:
        return str(make_header(decode_header(s)))
    except Exception:
        return s


def parse_message(header: bytes, text: bytes = b"") -> Parsed:
    raw = header.rstrip(b"\r\n") + b"\r\n\r\n" + (text or b"")
    msg = email.message_from_bytes(raw, policy=email.policy.default)

    plain, html = "", ""
    for part in msg.walk():
        ctype = part.get_content_type()
        if part.is_multipart() or ctype not in ("text/plain", "text/html"):
            continue
        try:
            payload = part.get_payload(decode=True) or b""
            charset = part.get_content_charset() or "utf-8"
            content = payload.decode(charset, errors="replace")
        except Exception:
            continue
        if ctype == "text/plain":
            plain += content
        else:
            html += content
    body = plain or html_to_text(html)

    from_pairs = getaddresses([_decode(msg.get("From", ""))])
    to_pairs = getaddresses([_decode(msg.get("To", "")), _decode(msg.get("Cc", ""))])

    try:
        d = parsedate_to_datetime(str(msg.get("Date")))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
    except Exception:
        d = datetime.now(timezone.utc)

    return Parsed(
        subject=_decode(msg.get("Subject", "")),
        from_name=from_pairs[0][0] if from_pairs else "",
        from_addrs=[a.lower() for _, a in from_pairs if a],
        to_addrs=[a.lower() for _, a in to_pairs if a],
        date=d,
        body=body,
        multipart_mixed=msg.get_content_type() == "multipart/mixed",
    )
