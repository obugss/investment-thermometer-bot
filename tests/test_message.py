import unittest

from investment_thermometer.message import format_snapshot, temperature_zone
from investment_thermometer.source import parse_market_snapshot
from test_source import build_html


class FormatSnapshotTests(unittest.TestCase):
    def test_formats_daily_telegram_message(self) -> None:
        message = format_snapshot(parse_market_snapshot(build_html()))

        self.assertIn("投资温度计 | 2026-09-03 20:00", message)
        self.assertIn("全市场温度：51°（中估）", message)
        self.assertIn("股票 56%", message)
        self.assertIn("债券 24%", message)
        self.assertIn("现金 20%", message)

    def test_temperature_zone_boundaries(self) -> None:
        self.assertEqual(temperature_zone(29), "低估")
        self.assertEqual(temperature_zone(30), "中估")
        self.assertEqual(temperature_zone(69), "中估")
        self.assertEqual(temperature_zone(70), "高估")


if __name__ == "__main__":
    unittest.main()