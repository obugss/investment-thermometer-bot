"""Fetch the current market snapshot and deliver it to Telegram."""

import os
from urllib.error import HTTPError, URLError

from .message import format_snapshot
from .source import SourceFormatError, fetch_market_snapshot
from .storage import save_snapshot
from .telegram import send_message


def main() -> None:
    token = _required_environment_variable("TELEGRAM_BOT_TOKEN")
    chat_id = _required_environment_variable("TELEGRAM_CHAT_ID")

    try:
        snapshot = fetch_market_snapshot()
    except (HTTPError, URLError, UnicodeError, SourceFormatError) as exc:
        send_message(token, chat_id, "投资温度计抓取失败，请检查 GitHub Actions 日志。")
        raise RuntimeError("market data could not be fetched or parsed") from exc

    snapshot_path = save_snapshot(snapshot)
    print(f"Saved market snapshot to {snapshot_path}.")
    send_message(token, chat_id, format_snapshot(snapshot))
    print(f"Sent market snapshot updated at {snapshot.updated_at:%Y-%m-%d %H:%M}.")


def _required_environment_variable(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not set")
    return value


if __name__ == "__main__":
    main()