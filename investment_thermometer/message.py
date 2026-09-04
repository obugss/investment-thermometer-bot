"""Format market snapshots for Telegram."""

from html import escape
import unicodedata

from .source import MarketSnapshot


def format_snapshot(snapshot: MarketSnapshot) -> str:
    allocation = snapshot.allocation
    lines = [
        f"投资温度计 | {snapshot.updated_at:%Y-%m-%d %H:%M}",
        "",
        f"全市场温度：{snapshot.degree}°（{temperature_zone(snapshot.degree)}）",
        "",
        "资产配置：",
        f"股票 {allocation.stock}%",
        f"债券 {allocation.bond}%",
        f"现金 {allocation.cash}%",
    ]
    if snapshot.indices:
        lines.extend(["", "指数温度：", _format_index_table(snapshot)])
    if snapshot.bond_degree is not None:
        bond_date = (
            f"（{snapshot.bond_date:%Y-%m-%d}）" if snapshot.bond_date else ""
        )
        lines.extend(["", f"债市温度：{snapshot.bond_degree}°{bond_date}"])
    lines.extend(["", "数据来源：有知有行"])
    message = "\n".join(lines)
    if len(message) > 4096:
        raise ValueError("Telegram message exceeds 4096 characters")
    return message


def _format_index_table(snapshot: MarketSnapshot) -> str:
    name_width = max(_display_width("名称"), *(_display_width(item.name) for item in snapshot.indices))
    code_width = max(_display_width("代码"), *(_display_width(item.code) for item in snapshot.indices))
    degree_width = max(_display_width("温度"), *(_display_width(f"{item.degree}°") for item in snapshot.indices))
    rows = [
        f"{_pad_display('名称', name_width)}  {_pad_display('代码', code_width)}  {_pad_display('温度', degree_width, right=True)}"
    ]
    rows.extend(
        f"{_pad_display(item.name, name_width)}  {_pad_display(item.code, code_width)}  {_pad_display(f'{item.degree}°', degree_width, right=True)}"
        for item in snapshot.indices
    )
    return f"<pre>{escape(chr(10).join(rows))}</pre>"


def _pad_display(value: str, width: int, *, right: bool = False) -> str:
    padding = " " * (width - _display_width(value))
    return f"{padding}{value}" if right else f"{value}{padding}"


def _display_width(value: str) -> int:
    return sum(2 if unicodedata.east_asian_width(character) in {"W", "F"} else 1 for character in value)


def temperature_zone(degree: int) -> str:
    if degree < 30:
        return "低估"
    if degree < 70:
        return "中估"
    return "高估"