# -*- coding: utf-8 -*-
"""
===================================
Telegram 意图识别模块
===================================

用途：
- 对来自 Telegram 的自然语言消息调用 LLM 进行意图分析
- 识别：添加自选股 / 删除自选股 / 即时分析股票 / 即时分析所有自选股
- 提供主动向 Telegram 发送消息的工具函数
"""

import json
from loguru import logger
from dataclasses import dataclass
from enum import Enum
from typing import Optional

# ──────────────────────────────────────────────────────────────
# 意图类型
# ──────────────────────────────────────────────────────────────

class IntentType(str, Enum):
    ADD_WATCHLIST = "add_watchlist"       # 添加自选股
    REMOVE_WATCHLIST = "remove_watchlist" # 删除自选股
    ANALYZE_STOCK = "analyze_stock"       # 即时分析某只股票
    ANALYZE_ALL = "analyze_all"           # 即时分析所有自选股
    UNKNOWN = "unknown"                   # 无法识别


@dataclass
class IntentResult:
    intent: IntentType
    stock_code: Optional[str] = None       # 股票代码（可能为 None，需后续搜索）
    stock_name_hint: Optional[str] = None  # 用户提到的股票名称


# ──────────────────────────────────────────────────────────────
# 意图识别 System Prompt
# ──────────────────────────────────────────────────────────────

_INTENT_SYSTEM_PROMPT = """你是一个股票助手的意图识别引擎，只负责解析用户消息并返回 JSON。

意图类型说明：
- add_watchlist：用户想把某只股票加入自选股（含"加入"、"添加"、"关注"、"自选"、"收藏"、"买入关注"等词）
- remove_watchlist：用户想从自选股中删除（含"删除"、"移除"、"取消关注"、"不看了"、"去掉"等词）
- analyze_stock：用户想分析某只具体股票（含"分析"、"看看"、"怎么样"、"帮我研究"、"看一下"等词）
- analyze_all：用户想分析所有自选股（含"分析所有"、"全部分析"、"帮我跑一遍"、"全部看看"、"分析自选"等词）
- unknown：无法识别的意图

输出格式（仅输出 JSON，不要任何其他内容）：
{"intent": "意图类型", "stock_code": "股票代码或null", "stock_name": "股票名称或null"}

股票代码规则：
- A股：6位数字，如 600519
- 港股：HK开头+5位数字，如 HK00700
- 美股：1-5个英文大写字母，如 AAPL
- 如果用户只提到名称没有提到代码，stock_code 填 null，stock_name 填名称
- 如果用户提到了代码，stock_code 填代码（标准化格式），stock_name 也尽量填"""


# ──────────────────────────────────────────────────────────────
# LLM 调用
# ──────────────────────────────────────────────────────────────

def _call_gemini(prompt: str) -> Optional[str]:
    """调用 Gemini API 进行意图分析（同步）"""
    try:
        import google.generativeai as genai
        from src.config import get_config
        config = get_config()
        genai.configure(api_key=config.gemini_api_key)
        model = genai.GenerativeModel(
            model_name=config.gemini_model_fallback,
            system_instruction=_INTENT_SYSTEM_PROMPT,
        )
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.1, "max_output_tokens": 256},
        )
        return response.text
    except Exception as e:
        logger.warning(f"[IntentAnalyzer] Gemini 调用失败: {e}")
        return None


def _call_openai(prompt: str) -> Optional[str]:
    """调用 OpenAI 兼容 API 进行意图分析（同步）"""
    try:
        from openai import OpenAI
        from src.config import get_config
        config = get_config()
        client_kwargs: dict = {"api_key": config.openai_api_key}
        if config.openai_base_url and config.openai_base_url.startswith("http"):
            client_kwargs["base_url"] = config.openai_base_url
        client = OpenAI(**client_kwargs)
        resp = client.chat.completions.create(
            model=config.openai_model,
            messages=[
                {"role": "system", "content": _INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=256,
        )
        return resp.choices[0].message.content
    except Exception as e:
        logger.warning(f"[IntentAnalyzer] OpenAI 调用失败: {e}")
        return None


def analyze_intent(text: str) -> IntentResult:
    """
    调用 LLM 分析用户自然语言消息的意图。

    优先 Gemini，备选 OpenAI 兼容 API。

    Args:
        text: 用户消息原文

    Returns:
        IntentResult
    """
    from src.config import get_config
    config = get_config()

    prompt = f'用户消息："{text}"\n\n请分析意图并返回 JSON。'

    raw_text: Optional[str] = None

    # 1. 尝试 Gemini
    gemini_key = (config.gemini_api_key or "").strip()
    if gemini_key and not gemini_key.startswith("your_") and len(gemini_key) > 10:
        raw_text = _call_gemini(prompt)

    # 2. 备选 OpenAI
    if raw_text is None:
        openai_key = (config.openai_api_key or "").strip()
        if openai_key and not openai_key.startswith("your_") and len(openai_key) > 10:
            raw_text = _call_openai(prompt)

    if not raw_text:
        logger.warning("[IntentAnalyzer] 无可用 LLM，返回 unknown 意图")
        return IntentResult(intent=IntentType.UNKNOWN)

    # 解析 JSON（容错）
    try:
        from json_repair import repair_json
        data = json.loads(repair_json(raw_text.strip()))
    except Exception:
        try:
            data = json.loads(raw_text.strip())
        except Exception as e:
            logger.error(f"[IntentAnalyzer] JSON 解析失败: {e}, 原始: {raw_text[:200]}")
            return IntentResult(intent=IntentType.UNKNOWN)

    try:
        intent = IntentType(data.get("intent", "unknown"))
    except ValueError:
        intent = IntentType.UNKNOWN

    stock_code = data.get("stock_code") or None
    stock_name = data.get("stock_name") or None

    # 规范化代码
    if stock_code and isinstance(stock_code, str):
        stock_code = stock_code.strip().upper()
        if not stock_code or stock_code.lower() == "null":
            stock_code = None

    if stock_name and isinstance(stock_name, str):
        stock_name = stock_name.strip()
        if not stock_name or stock_name.lower() == "null":
            stock_name = None

    logger.info(
        f"[IntentAnalyzer] 意图: {intent}, code={stock_code}, name={stock_name}, 原文: {text[:50]}"
    )
    return IntentResult(intent=intent, stock_code=stock_code, stock_name_hint=stock_name)


# ──────────────────────────────────────────────────────────────
# Telegram 主动发送工具
# ──────────────────────────────────────────────────────────────

def send_telegram_message(chat_id: str, text: str) -> bool:
    """
    主动通过 Bot API 向指定会话发送消息。

    Args:
        chat_id: 目标会话 ID
        text: 消息文本

    Returns:
        是否发送成功
    """
    import requests as _requests
    from src.config import get_config

    config = get_config()
    bot_token = (config.telegram_bot_token or "").strip()
    if not bot_token:
        logger.warning("[TelegramSender] TELEGRAM_BOT_TOKEN 未配置，跳过发送")
        return False

    try:
        _requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
        return True
    except Exception as e:
        logger.error(f"[TelegramSender] 发送失败 chat_id={chat_id}: {e}")
        return False
