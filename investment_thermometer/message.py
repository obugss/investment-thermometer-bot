"""Format market snapshots for Telegram."""

from html import escape

from .source import MarketSnapshot, THERMOMETER_URL


def format_snapshot(snapshot: MarketSnapshot) -> str:
    allocation = snapshot.allocation
    lines = [
        "<b>投资温度计</b>",
        f"<b>🔴 更新时间：{snapshot.updated_at:%Y-%m-%d %H:%M}</b>",
        "",
        f"全市场温度：{snapshot.degree}°（{temperature_zone(snapshot.degree)}）",
    ]
    if snapshot.bond_degree is not None:
        bond_date = (
            f"（{snapshot.bond_date:%Y-%m-%d}）" if snapshot.bond_date else ""
        )
        lines.append(f"债市温度：{snapshot.bond_degree}°{bond_date}")
    lines.extend(
        [
            "",
            "资产配置：",
            f"股票 {allocation.stock}%",
            f"债券 {allocation.bond}%",
            f"现金 {allocation.cash}%",
        ]
    )
    if snapshot.indices:
        lines.extend(["", "指数温度："])
        lines.extend(_format_index_rows(snapshot))
    lines.extend(
        [
            "",
            f'数据来源：<a href="{escape(THERMOMETER_URL, quote=True)}">有知有行 · 知行温度计</a>',
        ]
    )
    message = "\n".join(lines)
    if len(message) > 4096:
        raise ValueError("Telegram message exceeds 4096 characters")
    return message


def _format_index_rows(snapshot: MarketSnapshot) -> list[str]:
    code_width = max(len(item.code) for item in snapshot.indices)
    degree_width = max(len(f"{item.degree}°") for item in snapshot.indices)
    return [
        f"<code>{escape(item.code.ljust(code_width))}  "
        f"{escape(f'{item.degree}°'.rjust(degree_width))}</code>　"
        f"{escape(item.name)}"
        for item in snapshot.indices
    ]


def temperature_zone(degree: int) -> str:
    if degree < 30:
        return "低估"
    if degree < 70:
        return "中估"
    return "高估"