"""Format market snapshots for Telegram."""

from html import escape

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
        lines.extend(["", "指数温度："])
        lines.extend(_format_index_rows(snapshot))
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


def _format_index_rows(snapshot: MarketSnapshot) -> list[str]:
    code_width = max(len(item.code) for item in snapshot.indices)
    degree_width = max(len(f"{item.degree}°") for item in snapshot.indices)
    lines: list[str] = []
    for item in snapshot.indices:
        data_row = f"{item.code:<{code_width}}  {f'{item.degree}°':>{degree_width}}"
        lines.extend(
            [
                f"<b>{escape(item.name)}</b>",
                f"<code>{escape(data_row)}</code>",
            ]
        )
    return lines


def temperature_zone(degree: int) -> str:
    if degree < 30:
        return "低估"
    if degree < 70:
        return "中估"
    return "高估"