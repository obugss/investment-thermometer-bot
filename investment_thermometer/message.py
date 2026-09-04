"""Format market snapshots for Telegram."""

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
        lines.extend(
            f"{index.name}（{index.code}）：{index.degree}°"
            for index in snapshot.indices
        )
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


def temperature_zone(degree: int) -> str:
    if degree < 30:
        return "低估"
    if degree < 70:
        return "中估"
    return "高估"