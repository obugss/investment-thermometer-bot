import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from investment_thermometer.source import (
    SourceFormatError,
    fetch_market_snapshot,
    parse_market_snapshot,
)


def build_html(*, degree: int = 51, stock: int = 56, bond: int = 24, cash: int = 20) -> str:
    data = {
        "temperature": {"degree": degree, "date": "2026-09-03", "time": "20:00"},
        "currentAllocation": {"stock": stock, "bond": bond, "cash": cash},
    }
    return f"<script>window.LONG_TERM_REMOTE_SOURCE={json.dumps(data)};</script>"


class ParseMarketSnapshotTests(unittest.TestCase):
    def test_parses_temperature_and_current_allocation(self) -> None:
        snapshot = parse_market_snapshot(build_html())

        self.assertEqual(snapshot.degree, 51)
        self.assertEqual(snapshot.updated_at.isoformat(), "2026-09-03T20:00:00")
        self.assertEqual(snapshot.allocation.stock, 56)
        self.assertEqual(snapshot.allocation.bond, 24)
        self.assertEqual(snapshot.allocation.cash, 20)

    def test_rejects_missing_embedded_data(self) -> None:
        with self.assertRaisesRegex(SourceFormatError, "was not found"):
            parse_market_snapshot("<html></html>")

    def test_rejects_allocation_that_does_not_total_100(self) -> None:
        with self.assertRaisesRegex(SourceFormatError, "must total 100"):
            parse_market_snapshot(build_html(stock=50))

    @patch("investment_thermometer.source.time.sleep")
    @patch("investment_thermometer.source.urlopen")
    def test_retries_server_error(self, mock_urlopen: object, mock_sleep: object) -> None:
        error = HTTPError("https://example.test", 503, "unavailable", {}, None)
        response = FakeResponse(build_html().encode("utf-8"))
        mock_urlopen.side_effect = [error, response]

        snapshot = fetch_market_snapshot(retry_delay=0)

        self.assertEqual(snapshot.degree, 51)
        self.assertEqual(mock_urlopen.call_count, 2)
        mock_sleep.assert_called_once_with(0)


class FakeResponse:
    def __init__(self, content: bytes) -> None:
        self.content = content

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.content


if __name__ == "__main__":
    unittest.main()