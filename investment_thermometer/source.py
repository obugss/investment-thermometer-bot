"""Read market thermometer data from Youzhiyouxing's public page."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
from html.parser import HTMLParser
import json
import re
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DATA_MARKER = "window.LONG_TERM_REMOTE_SOURCE="
SOURCE_URL = "https://youzhiyouxing.cn/advisor/longterm_strategy/?hosted=1#temperature"
THERMOMETER_URL = "https://youzhiyouxing.cn/thermometer"


class SourceFormatError(ValueError):
    """Raised when the source page does not contain valid market data."""


@dataclass(frozen=True)
class Allocation:
    stock: int
    bond: int
    cash: int


@dataclass(frozen=True)
class IndexTemperature:
    name: str
    code: str
    degree: int


@dataclass(frozen=True)
class MarketSnapshot:
    degree: int
    updated_at: datetime
    allocation: Allocation
    indices: tuple[IndexTemperature, ...] = ()
    bond_degree: int | None = None
    bond_date: date | None = None


def fetch_market_snapshot(
    *, timeout: float = 20.0, attempts: int = 3, retry_delay: float = 1.0
) -> MarketSnapshot:
    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    source_html = _fetch_html(
        SOURCE_URL, timeout=timeout, attempts=attempts, retry_delay=retry_delay
    )
    snapshot = parse_market_snapshot(source_html)
    thermometer_html = _fetch_html(
        THERMOMETER_URL, timeout=timeout, attempts=attempts, retry_delay=retry_delay
    )
    indices, bond_degree, bond_date = parse_all_thermometers(thermometer_html)
    return replace(
        snapshot,
        indices=indices,
        bond_degree=bond_degree,
        bond_date=bond_date,
    )


def _fetch_html(
    url: str, *, timeout: float, attempts: int, retry_delay: float
) -> str:
    request = Request(url, headers={"User-Agent": "investment-thermometer-bot/1.0"})
    for attempt in range(1, attempts + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.read().decode("utf-8")
        except HTTPError as exc:
            if exc.code < 500 or attempt == attempts:
                raise
        except URLError:
            if attempt == attempts:
                raise
        time.sleep(retry_delay)

    raise RuntimeError("unreachable")


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


def parse_all_thermometers(
    html: str,
) -> tuple[tuple[IndexTemperature, ...], int, date]:
    parser = _ThermometerPageParser()
    parser.feed(html)
    page_text = " ".join(parser.text_parts)

    market_match = re.search(r"全市场温度\s+.*?(\d{1,3})°", page_text)
    if market_match is None:
        raise SourceFormatError("full-market thermometer was not found")
    _validate_degree(int(market_match.group(1)), "full-market degree")

    indices: list[IndexTemperature] = []
    seen_codes: set[str] = set()
    for code, row_text in parser.index_rows:
        row_match = re.search(
            rf"^(?P<name>.+?)\s+{re.escape(code)}\s+(?P<degree>\d{{1,3}})°",
            row_text,
        )
        if row_match is None:
            raise SourceFormatError(f"temperature for index {code} was not found")
        if code in seen_codes:
            raise SourceFormatError(f"duplicate index code {code}")
        degree = int(row_match.group("degree"))
        _validate_degree(degree, f"degree for index {code}")
        indices.append(
            IndexTemperature(
                name=row_match.group("name").strip(),
                code=code,
                degree=degree,
            )
        )
        seen_codes.add(code)

    if not indices:
        raise SourceFormatError("index thermometers were not found")

    bond_match = re.search(
        r"债市温度\s+(\d{1,3})°.*?(\d{4})年(\d{1,2})月(\d{1,2})日",
        page_text,
    )
    if bond_match is None:
        raise SourceFormatError("bond thermometer was not found")
    bond_degree = int(bond_match.group(1))
    _validate_degree(bond_degree, "bond degree")
    try:
        bond_date = date(*(int(part) for part in bond_match.groups()[1:]))
    except ValueError as exc:
        raise SourceFormatError("bond thermometer date is invalid") from exc

    return tuple(indices), bond_degree, bond_date


class _ThermometerPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text_parts: list[str] = []
        self.index_rows: list[tuple[str, str]] = []
        self._row_depth = 0
        self._row_code: str | None = None
        self._row_text: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag == "tr":
            self._row_depth += 1
            if self._row_depth == 1:
                self._row_code = None
                self._row_text = []
        if self._row_depth and tag == "a":
            href = dict(attrs).get("href") or ""
            match = re.fullmatch(r"/data/indices/([^/?#]+)", href)
            if match is not None:
                self._row_code = match.group(1)

    def handle_endtag(self, tag: str) -> None:
        if tag != "tr" or not self._row_depth:
            return
        self._row_depth -= 1
        if self._row_depth == 0 and self._row_code is not None:
            row_text = " ".join(self._row_text)
            self.index_rows.append((self._row_code, row_text))

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text:
            return
        self.text_parts.append(text)
        if self._row_depth:
            self._row_text.append(text)


def _validate_degree(value: int, name: str) -> None:
    if not 0 <= value <= 100:
        raise SourceFormatError(f"{name} must be between 0 and 100")


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