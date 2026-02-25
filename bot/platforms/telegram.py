# -*- coding: utf-8 -*-
"""Telegram platform adapter."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from bot.models import BotMessage, BotResponse, ChatType, WebhookResponse
from bot.platforms.base import BotPlatform
from src.config import get_config

logger = logging.getLogger(__name__)


class TelegramPlatform(BotPlatform):
    """Telegram webhook adapter."""

    def __init__(self):
        config = get_config()
        self._secret = (getattr(config, "telegram_webhook_secret", None) or "").strip()

    @property
    def platform_name(self) -> str:
        return "telegram"

    def verify_request(self, headers: Dict[str, str], body: bytes) -> bool:
        if not self._secret:
            return True

        provided = headers.get("x-telegram-bot-api-secret-token", "")
        return provided == self._secret

    def parse_message(self, data: Dict[str, Any]) -> Optional[BotMessage]:
        message = data.get("message") or data.get("edited_message") or {}
        if not message:
            return None

        from_user = message.get("from") or {}
        chat = message.get("chat") or {}

        text = (message.get("text") or "").strip()
        caption = (message.get("caption") or "").strip()
        content = text or caption
        if not content:
            return None

        chat_type = ChatType.GROUP if chat.get("type") in {"group", "supergroup"} else ChatType.PRIVATE

        unix_ts = message.get("date")
        try:
            ts = datetime.fromtimestamp(int(unix_ts)) if unix_ts else datetime.now()
        except Exception:
            ts = datetime.now()

        return BotMessage(
            platform=self.platform_name,
            message_id=str(message.get("message_id") or ""),
            user_id=str(from_user.get("id") or ""),
            user_name=(from_user.get("username") or from_user.get("first_name") or "telegram_user"),
            chat_id=str(chat.get("id") or ""),
            chat_type=chat_type,
            content=content,
            raw_content=content,
            mentioned=chat_type == ChatType.PRIVATE,
            mentions=[],
            timestamp=ts,
            raw_data=data,
        )

    def format_response(self, response: BotResponse, message: BotMessage) -> WebhookResponse:
        if not response.text:
            return WebhookResponse.success()

        body = {
            "method": "sendMessage",
            "chat_id": message.chat_id,
            "text": response.text,
        }
        if message.message_id.isdigit():
            body["reply_to_message_id"] = int(message.message_id)

        return WebhookResponse.success(body)
