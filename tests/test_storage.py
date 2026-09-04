import json
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from investment_thermometer.source import parse_all_thermometers, parse_market_snapshot
from investment_thermometer.storage import save_snapshot
from tests.test_source import build_html, build_thermometer_html


class SaveSnapshotTests(unittest.TestCase):
    def test_saves_all_temperatures_by_source_date(self) -> None:
        snapshot = parse_market_snapshot(build_html())
        indices, bond_degree, bond_date = parse_all_thermometers(
            build_thermometer_html()
        )
        snapshot = replace(
            snapshot,
            indices=indices,
            bond_degree=bond_degree,
            bond_date=bond_date,
        )

        with TemporaryDirectory() as temporary_directory:
            path = save_snapshot(snapshot, Path(temporary_directory))
            data = json.loads(path.read_text(encoding="utf-8"))

            self.assertEqual(path.name, "2026-09-03.json")
            self.assertEqual(data["market_temperature"], 51)
            self.assertEqual(data["allocation"], {"stock": 56, "bond": 24, "cash": 20})
            self.assertEqual(len(data["index_temperatures"]), 2)
            self.assertEqual(data["index_temperatures"][0]["degree"], 1)
            self.assertEqual(data["bond_temperature"], {"degree": 87, "date": "2026-09-03"})
            self.assertEqual(len(data["sources"]), 2)

    def test_repeated_save_is_identical(self) -> None:
        snapshot = parse_market_snapshot(build_html())

        with TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            first_path = save_snapshot(snapshot, directory)
            first_content = first_path.read_bytes()
            second_path = save_snapshot(snapshot, directory)

            self.assertEqual(first_path, second_path)
            self.assertEqual(second_path.read_bytes(), first_content)


if __name__ == "__main__":
    unittest.main()