"""Format market snapshots for Telegram."""

from .source import MarketSnapshot


def format_snapshot(snapshot: MarketSnapshot) -> str:
    allocation = snapshot.allocation
    return "\n".join(
        [
            f"投资温度计 | {snapshot.updated_at:%Y-%m-%d %H:%M}",
            "",
            f"全市场温度：{snapshot.degree}°（{temperature_zone(snapshot.degree)}）",
            "",
            "资产配置：",
            f"股票 {allocation.stock}%",
            f"债券 {allocation.bond}%",
            f"现金 {allocation.cash}%",
            "",
            "数据来源：有知有行",
        ]
    )


def temperature_zone(degree: int) -> str:
    if degree < 30:
        return "低估"
    if degree < 70:
        return "中估"
    return "高估"