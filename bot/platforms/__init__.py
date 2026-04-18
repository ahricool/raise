# -*- coding: utf-8 -*-
"""
===================================
平台适配器模块
===================================

包含各平台的 Webhook 处理和消息解析逻辑。
"""

from bot.platforms.base import BotPlatform
from bot.platforms.telegram import TelegramPlatform

ALL_PLATFORMS = {
    'telegram': TelegramPlatform,
}

__all__ = [
    'BotPlatform',
    'TelegramPlatform',
    'ALL_PLATFORMS',
]
