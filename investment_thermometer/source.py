"""Read market thermometer data from Youzhiyouxing's public page."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DATA_MARKER = "window.LONG_TERM_REMOTE_SOURCE="
SOURCE_URL = "https://youzhiyouxing.cn/advisor/longterm_strategy/?hosted=1#temperature"


class SourceFormatError(ValueError):
    """Raised when the source page does not contain valid market data."""


@dataclass(frozen=True)
class Allocation:
    stock: int
    bond: int
    cash: int


@dataclass(frozen=True)
class MarketSnapshot:
    degree: int
    updated_at: datetime
    allocation: Allocation


def fetch_market_snapshot(
    *, timeout: float = 20.0, attempts: int = 3, retry_delay: float = 1.0
) -> MarketSnapshot:
    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    request = Request(
        SOURCE_URL,
        headers={"User-Agent": "investment-thermometer-bot/1.0"},
    )
    for attempt in range(1, attempts + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                html = response.read().decode("utf-8")
            break
        except HTTPError as exc:
            if exc.code < 500 or attempt == attempts:
                raise
        except URLError:
            if attempt == attempts:
                raise
        time.sleep(retry_delay)

    return parse_market_snapshot(html)


def parse_market_snapshot(html: str) -> MarketSnapshot:
    marker_index = html.find(DATA_MARKER)
    if marker_index < 0:
        raise SourceFormatError("embedded market data was not found")

    json_start = marker_index + len(DATA_MARKER)
    try:
        data, _ = json.JSONDecoder().raw_decode(html[json_start:].lstrip())
    except json.JSONDecodeError as exc:
        raise SourceFormatError("embedded market data is not valid JSON") from exc

    if not isinstance(data, dict):
        raise SourceFormatError("embedded market data must be an object")

    temperature = _require_object(data, "temperature")
    allocation_data = _require_object(data, "currentAllocation")
    degree = _require_int(temperature, "degree", minimum=0, maximum=100)
    allocation = Allocation(
        stock=_require_int(allocation_data, "stock", minimum=0, maximum=100),
        bond=_require_int(allocation_data, "bond", minimum=0, maximum=100),
        cash=_require_int(allocation_data, "cash", minimum=0, maximum=100),
    )
    if allocation.stock + allocation.bond + allocation.cash != 100:
        raise SourceFormatError("asset allocation percentages must total 100")

    date = _require_string(temperature, "date")
    time = _require_string(temperature, "time")
    try:
        updated_at = datetime.fromisoformat(f"{date}T{time}")
    except ValueError as exc:
        raise SourceFormatError("temperature date or time is invalid") from exc

    return MarketSnapshot(
        degree=degree,
        updated_at=updated_at,
        allocation=allocation,
    )


def _require_object(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise SourceFormatError(f"{key} must be an object")
    return value


def _require_int(
    data: dict[str, Any], key: str, *, minimum: int, maximum: int
) -> int:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise SourceFormatError(f"{key} must be an integer")
    if not minimum <= value <= maximum:
        raise SourceFormatError(f"{key} must be between {minimum} and {maximum}")
    return value


def _require_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise SourceFormatError(f"{key} must be a non-empty string")
    return value