"""Phase 2 stub — відправка повідомлень Telegram буде реалізована пізніше."""
from io import BytesIO


class TelegramSender:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token

    def send_message(self, chat_id: str, text: str) -> dict:
        """Stub: відправити текстове повідомлення."""
        return {"ok": False, "description": "Not implemented (Phase 2)"}

    def send_document(self, chat_id: str, document: BytesIO, filename: str, caption: str = "") -> dict:
        """Stub: відправити документ."""
        return {"ok": False, "description": "Not implemented (Phase 2)"}
