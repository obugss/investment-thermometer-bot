"""List Telegram chats that have recently contacted the configured bot."""

import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Required environment variable TELEGRAM_BOT_TOKEN is not set")

    query = urlencode({"allowed_updates": json.dumps(["message"])})
    request = Request(f"https://api.telegram.org/bot{token}/getUpdates?{query}")
    with urlopen(request, timeout=20.0) as response:
        payload = json.load(response)

    chats: dict[int, str] = {}
    for update in payload.get("result", []):
        chat = update.get("message", {}).get("chat", {})
        chat_id = chat.get("id")
        if isinstance(chat_id, int):
            name = chat.get("title") or chat.get("username") or chat.get("first_name") or "unknown"
            chats[chat_id] = str(name)

    if not chats:
        print("No chats found. Send /start to the bot, then run this command again.")
        return

    for chat_id, name in chats.items():
        print(f"Chat ID: {chat_id} ({name})")


if __name__ == "__main__":
    main()