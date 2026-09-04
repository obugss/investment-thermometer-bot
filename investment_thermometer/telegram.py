"""Minimal Telegram Bot API client."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class TelegramError(RuntimeError):
    """Raised when Telegram does not accept a message."""


def send_message(token: str, chat_id: str, text: str, *, timeout: float = 20.0) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urlencode(
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")
    request = Request(url, data=body, method="POST")

    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.load(response)
    except HTTPError as exc:
        raise TelegramError(f"Telegram returned HTTP {exc.code}") from None
    except URLError as exc:
        raise TelegramError("Telegram could not be reached") from exc

    if not isinstance(result, dict) or result.get("ok") is not True:
        raise TelegramError("Telegram rejected the message")