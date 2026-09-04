import io
import unittest
from unittest.mock import patch

from investment_thermometer.telegram import TelegramError, send_message


class FakeResponse(io.BytesIO):
    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class SendMessageTests(unittest.TestCase):
    @patch("investment_thermometer.telegram.urlopen")
    def test_posts_message_to_telegram(self, mock_urlopen: object) -> None:
        mock_urlopen.return_value = FakeResponse(b'{"ok": true}')

        send_message("secret-token", "12345", "hello")

        request = mock_urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.full_url, "https://api.telegram.org/botsecret-token/sendMessage")
        self.assertEqual(
            request.data,
            b"chat_id=12345&text=hello&parse_mode=HTML&disable_web_page_preview=true",
        )

    @patch("investment_thermometer.telegram.urlopen")
    def test_rejects_unsuccessful_api_response(self, mock_urlopen: object) -> None:
        mock_urlopen.return_value = FakeResponse(b'{"ok": false}')

        with self.assertRaisesRegex(TelegramError, "rejected"):
            send_message("secret-token", "12345", "hello")


if __name__ == "__main__":
    unittest.main()