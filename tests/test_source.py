import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from investment_thermometer.source import (
    SourceFormatError,
    fetch_market_snapshot,
    parse_all_thermometers,
    parse_market_snapshot,
)


def build_html(*, degree: int = 51, stock: int = 56, bond: int = 24, cash: int = 20) -> str:
    data = {
        "temperature": {"degree": degree, "date": "2026-09-03", "time": "20:00"},
        "currentAllocation": {"stock": stock, "bond": bond, "cash": cash},
    }
    return f"<script>window.LONG_TERM_REMOTE_SOURCE={json.dumps(data)};</script>"


def build_thermometer_html() -> str:
    return """
        <p>温度更新时间：2026年9月3日 20:00</p>
        <h2>全市场温度</h2><div>51°</div>
        <table><tbody>
          <tr><td><a href="/data/indices/000932.SH">800消费 000932.SH</a></td>
              <td><a href="/data/indices/000932.SH">1°</a></td></tr>
          <tr><td><a href="/data/indices/000300.SH">沪深300 000300.SH</a></td>
              <td><a href="/data/indices/000300.SH">45°</a></td></tr>
        </tbody></table>
        <p>债市温度 <span>87°</span></p>
        <label>2026年9月3日</label>
    """


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

    def test_parses_every_index_and_bond_thermometer(self) -> None:
        indices, bond_degree, bond_date = parse_all_thermometers(
            build_thermometer_html()
        )

        self.assertEqual(
            [(item.name, item.code, item.degree) for item in indices],
            [("800消费", "000932.SH", 1), ("沪深300", "000300.SH", 45)],
        )
        self.assertEqual(bond_degree, 87)
        self.assertEqual(bond_date.isoformat(), "2026-09-03")

    @patch("investment_thermometer.source.time.sleep")
    @patch("investment_thermometer.source.urlopen")
    def test_retries_server_error(self, mock_urlopen: object, mock_sleep: object) -> None:
        error = HTTPError("https://example.test", 503, "unavailable", {}, None)
        source_response = FakeResponse(build_html().encode("utf-8"))
        thermometer_response = FakeResponse(build_thermometer_html().encode("utf-8"))
        mock_urlopen.side_effect = [error, source_response, thermometer_response]

        snapshot = fetch_market_snapshot(retry_delay=0)

        self.assertEqual(snapshot.degree, 51)
        self.assertEqual(len(snapshot.indices), 2)
        self.assertEqual(mock_urlopen.call_count, 3)
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