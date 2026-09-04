import unittest
import re

from investment_thermometer.message import format_snapshot, temperature_zone
from dataclasses import replace

from investment_thermometer.source import parse_all_thermometers, parse_market_snapshot
from tests.test_source import build_html, build_thermometer_html


class FormatSnapshotTests(unittest.TestCase):
    def test_formats_daily_telegram_message(self) -> None:
        snapshot = parse_market_snapshot(build_html())
        indices, bond_degree, bond_date = parse_all_thermometers(
            build_thermometer_html()
        )
        message = format_snapshot(
            replace(
                snapshot,
                indices=indices,
                bond_degree=bond_degree,
                bond_date=bond_date,
            )
        )

        self.assertIn("<b>投资温度计</b>", message)
        self.assertIn("<b>🔴 更新时间：2026-09-03 20:00</b>", message)
        self.assertIn("全市场温度：51°（中估）", message)
        self.assertLess(
            message.index("全市场温度："), message.index("债市温度：")
        )
        self.assertLess(message.index("债市温度："), message.index("资产配置："))
        self.assertIn("股票 56%", message)
        self.assertIn("债券 24%", message)
        self.assertIn("现金 20%", message)
        self.assertNotIn("<pre>", message)
        rows = re.findall(r"<code>(.*?)</code>　([^\n]+)", message)
        self.assertEqual([name for _, name in rows], ["800消费", "沪深300"])
        self.assertEqual(len({len(columns) for columns, _ in rows}), 1)
        self.assertTrue(rows[0][0].startswith("000932.SH"))
        self.assertTrue(rows[0][0].endswith(" 1°"))
        self.assertTrue(rows[1][0].startswith("000300.SH"))
        self.assertTrue(rows[1][0].endswith("45°"))
        self.assertIn("债市温度：87°（2026-09-03）", message)
        self.assertIn(
            '<a href="https://youzhiyouxing.cn/advisor/longterm_strategy/?hosted=1#temperature">有知有行 · 长钱账户</a>',
            message,
        )
        self.assertIn(
            '<a href="https://youzhiyouxing.cn/thermometer">有知有行 · 知行温度计</a>',
            message,
        )
        self.assertLessEqual(len(message), 4096)

    def test_temperature_zone_boundaries(self) -> None:
        self.assertEqual(temperature_zone(29), "低估")
        self.assertEqual(temperature_zone(30), "中估")
        self.assertEqual(temperature_zone(69), "中估")
        self.assertEqual(temperature_zone(70), "高估")


if __name__ == "__main__":
    unittest.main()