"""Persist market snapshots as reviewable JSON files."""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from .source import MarketSnapshot, SOURCE_URL, THERMOMETER_URL


def save_snapshot(snapshot: MarketSnapshot, data_directory: Path = Path("data")) -> Path:
    snapshot_directory = data_directory / "snapshots"
    snapshot_directory.mkdir(parents=True, exist_ok=True)
    path = snapshot_directory / f"{snapshot.updated_at:%Y-%m-%d}.json"
    content = json.dumps(
        snapshot_to_dict(snapshot),
        ensure_ascii=False,
        indent=2,
    )
    path.write_text(f"{content}\n", encoding="utf-8")
    return path


def snapshot_to_dict(snapshot: MarketSnapshot) -> dict[str, Any]:
    allocation = snapshot.allocation
    return {
        "updated_at": snapshot.updated_at.isoformat(),
        "market_temperature": snapshot.degree,
        "allocation": {
            "stock": allocation.stock,
            "bond": allocation.bond,
            "cash": allocation.cash,
        },
        "index_temperatures": [
            {
                "name": index.name,
                "code": index.code,
                "degree": index.degree,
            }
            for index in snapshot.indices
        ],
        "bond_temperature": {
            "degree": snapshot.bond_degree,
            "date": snapshot.bond_date.isoformat() if snapshot.bond_date else None,
        },
        "sources": [SOURCE_URL, THERMOMETER_URL],
    }