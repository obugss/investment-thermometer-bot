"""Daily investment thermometer notifications."""

from .source import (
    Allocation,
    IndexTemperature,
    MarketSnapshot,
    SourceFormatError,
    fetch_market_snapshot,
    parse_all_thermometers,
    parse_market_snapshot,
)

__all__ = [
    "Allocation",
    "IndexTemperature",
    "MarketSnapshot",
    "SourceFormatError",
    "fetch_market_snapshot",
    "parse_all_thermometers",
    "parse_market_snapshot",
]