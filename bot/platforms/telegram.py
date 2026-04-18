# -*- coding: utf-8 -*-
"""
Telegram 平台适配器

负责：
- Webhook 校验：若配置了 `telegram_webhook_secret`，则比对 Header 中的 Secret Token
- 将 Telegram Update JSON 转为统一的 `BotMessage`
- 将 `BotResponse` 转为 Telegram 期望的 `sendMessage` 响应体（供 Webhook 同步回复）

说明：群组里若需 @ 机器人才响应，由上层 dispatcher 处理；此处只解析 text/caption。
"""

from loguru import logger
from datetime import datetime
from typing import Any, Dict, Optional

from bot.models import BotMessage, BotResponse, ChatType, WebhookResponse
from bot.platforms.base import BotPlatform
from src.config import get_config

class TelegramPlatform(BotPlatform):
    """Telegram Bot API Webhook 与统一消息模型的桥接。"""

    def __init__(self):
        """内部辅助逻辑：__init__（模块：telegram）。"""
        config = get_config()
        # 未配置 secret 时不校验（开发环境常见）；生产环境建议在 BotFather 设置并与此处一致
        self._secret = (getattr(config, "telegram_webhook_secret", None) or "").strip()

    @property
    def platform_name(self) -> str:
        """业务流程函数：platform_name（模块：telegram）。"""
        return "telegram"

    def verify_request(self, headers: Dict[str, str], body: bytes) -> bool:
        # 与 setWebhook(secret_token=...) 对应；Header 名固定为 Telegram 文档约定
        """业务流程函数：verify_request（模块：telegram）。"""
        if not self._secret:
            return True

        provided = headers.get("x-telegram-bot-api-secret-token", "")
        return provided == self._secret

    def parse_message(self, data: Dict[str, Any]) -> Optional[BotMessage]:
        # 普通消息在 message；编辑过的消息在 edited_message
        """业务流程函数：parse_message（模块：telegram）。"""
        message = data.get("message") or data.get("edited_message") or {}
        if not message:
            return None

        from_user = message.get("from") or {}
        chat = message.get("chat") or {}

        # 文本或媒体说明（图片/文件带 caption）
        text = (message.get("text") or "").strip()
        caption = (message.get("caption") or "").strip()
        content = text or caption
        if not content:
            return None

        # Telegram 的 chat.type：private / group / supergroup / channel
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
            # 私聊视为「已点名」；群聊是否 @ 机器人由 dispatcher 结合 entities 判断
            mentioned=chat_type == ChatType.PRIVATE,
            mentions=[],
            timestamp=ts,
            raw_data=data,
        )

    def format_response(self, response: BotResponse, message: BotMessage) -> WebhookResponse:
        # Webhook 同步回复体里直接带 method，Telegram 会当作一次 Bot API 调用执行
        """业务流程函数：format_response（模块：telegram）。"""
        if not response.text:
            return WebhookResponse.success()

        body = {
            "method": "sendMessage",
            "chat_id": message.chat_id,
            "text": response.text,
        }
        # 尽量串回原消息，便于群内上下文阅读
        if message.message_id.isdigit():
            body["reply_to_message_id"] = int(message.message_id)

        return WebhookResponse.success(body)
