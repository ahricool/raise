# -*- coding: utf-8 -*-
"""
===================================
Bot Webhook API 端点
===================================

提供各平台机器人 Webhook 接收端点。

Telegram 接收逻辑：
1. 命令消息（以 / 开头或已知中文命令）→ 同步处理，通过 webhook 响应体回复
2. 自然语言消息 → 后台任务处理：
   a. 调用 LLM 分析意图
   b. 执行对应操作（添加/删除自选股、即时分析）
   c. 通过 Telegram Bot API 主动发送回复
"""

import json
import logging

from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter()


# ──────────────────────────────────────────────────────────────
# Telegram Webhook
# ──────────────────────────────────────────────────────────────

@router.post("/telegram", summary="Telegram Webhook", tags=["Bot"])
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    接收 Telegram Bot Webhook 推送。

    - 命令消息：同步处理并通过 HTTP 响应体返回 sendMessage
    - 自然语言：后台异步处理意图识别，完成后主动推送回复
    """
    body = await request.body()
    headers = dict(request.headers)

    # 解析 JSON
    try:
        data = json.loads(body.decode("utf-8")) if body else {}
    except Exception:
        return JSONResponse({}, status_code=200)

    # 解析消息
    from bot.platforms.telegram import TelegramPlatform
    platform = TelegramPlatform()

    # 验证请求合法性
    if not platform.verify_request(headers, body):
        logger.warning("[BotEndpoint] Telegram webhook 验证失败")
        return JSONResponse({"error": "Unauthorized"}, status_code=403)

    message = platform.parse_message(data)
    if not message:
        return JSONResponse({}, status_code=200)

    # 判断是否为命令消息
    from src.config import get_config
    config = get_config()
    prefix = getattr(config, "bot_command_prefix", "/")

    if message.is_command(prefix):
        # 命令消息：同步调用 dispatcher，通过 webhook 响应体回复
        from bot.dispatcher import get_dispatcher
        dispatcher = get_dispatcher()
        response = dispatcher.dispatch(message)

        if response.text:
            webhook_body = platform.format_response(response, message).body
            return JSONResponse(webhook_body, status_code=200)
        return JSONResponse({}, status_code=200)

    # 自然语言消息：后台处理
    background_tasks.add_task(_handle_intent_message, message.chat_id, message.content)
    return JSONResponse({}, status_code=200)


# ──────────────────────────────────────────────────────────────
# 后台意图处理（同步函数，FastAPI 在线程池中执行）
# ──────────────────────────────────────────────────────────────

def _handle_intent_message(chat_id: str, text: str) -> None:
    """
    在后台线程中处理自然语言消息：
    1. 调用 LLM 分析意图
    2. 执行对应操作
    3. 向用户发送反馈
    """
    from bot.intent_analyzer import (
        IntentType,
        analyze_intent,
        send_telegram_message,
    )

    logger.info(f"[BotEndpoint] 后台处理自然语言: chat_id={chat_id}, text={text[:60]}")

    try:
        intent_result = analyze_intent(text)
    except Exception as e:
        logger.error(f"[BotEndpoint] 意图分析异常: {e}", exc_info=True)
        send_telegram_message(chat_id, "⚠️ 意图分析失败，请稍后重试或使用命令行模式")
        return

    intent = intent_result.intent

    # ── 添加自选股 ──────────────────────────────────────────
    if intent == IntentType.ADD_WATCHLIST:
        _do_add_watchlist(chat_id, intent_result.stock_code, intent_result.stock_name_hint)

    # ── 删除自选股 ──────────────────────────────────────────
    elif intent == IntentType.REMOVE_WATCHLIST:
        _do_remove_watchlist(chat_id, intent_result.stock_code, intent_result.stock_name_hint)

    # ── 即时分析某只股票 ────────────────────────────────────
    elif intent == IntentType.ANALYZE_STOCK:
        _do_analyze_stock(chat_id, intent_result.stock_code, intent_result.stock_name_hint)

    # ── 即时分析所有自选股 ──────────────────────────────────
    elif intent == IntentType.ANALYZE_ALL:
        _do_analyze_all(chat_id)

    # ── 无法识别 ────────────────────────────────────────────
    else:
        send_telegram_message(
            chat_id,
            "抱歉，我没有理解你的意思 😅\n\n"
            "你可以这样说：\n"
            "• 「添加 贵州茅台」或 /add 600519 — 添加自选股\n"
            "• 「删除 茅台」或 /remove 600519 — 移除自选股\n"
            "• 「分析 600519」或 /analyze 600519 — 即时分析股票\n"
            "• 「分析所有自选股」或 /all — 立即跑一遍自选股分析\n"
            "• /help — 查看全部命令",
        )


# ──────────────────────────────────────────────────────────────
# 各意图处理逻辑
# ──────────────────────────────────────────────────────────────

def _do_add_watchlist(chat_id: str, stock_code: str | None, name_hint: str | None) -> None:
    from bot.intent_analyzer import send_telegram_message
    from src.services.watchlist_service import WatchlistService
    from src.storage import DatabaseManager

    service = WatchlistService()
    query = stock_code or name_hint

    if not query:
        send_telegram_message(chat_id, "❌ 未识别到股票代码或名称，请重新描述")
        return

    try:
        results = service.search_stock(query)
        if not results:
            send_telegram_message(chat_id, f"❌ 未找到股票「{query}」，请检查代码或名称")
            return

        stock = results[0]
        code = stock["stock_code"]
        name = stock.get("stock_name") or code

        db = DatabaseManager.get_instance().get_session()
        try:
            item = service.add_stock(db, code, name)
        finally:
            db.close()

        send_telegram_message(
            chat_id,
            f"✅ 已添加自选股\n\n"
            f"• 代码：{item['stock_code']}\n"
            f"• 名称：{item.get('stock_name') or name}",
        )
    except Exception as e:
        logger.error(f"[BotEndpoint] 添加自选股失败: {e}", exc_info=True)
        send_telegram_message(chat_id, f"❌ 添加失败：{str(e)[:100]}")


def _do_remove_watchlist(chat_id: str, stock_code: str | None, name_hint: str | None) -> None:
    from bot.intent_analyzer import send_telegram_message
    from src.services.watchlist_service import WatchlistService
    from src.storage import DatabaseManager

    service = WatchlistService()
    query = (stock_code or name_hint or "").strip()

    if not query:
        send_telegram_message(chat_id, "❌ 未识别到股票代码或名称，请重新描述")
        return

    try:
        db = DatabaseManager.get_instance().get_session()
        try:
            stocks = service.list_stocks(db)
        finally:
            db.close()

        if not stocks:
            send_telegram_message(chat_id, "自选股列表为空，无需删除")
            return

        # 精确代码匹配 → 名称模糊匹配
        query_upper = query.upper()
        target = None
        for s in stocks:
            if s["stock_code"].upper() == query_upper:
                target = s
                break
        if target is None:
            for s in stocks:
                name_lower = (s.get("stock_name") or "").lower()
                if query.lower() in name_lower:
                    target = s
                    break

        if target is None:
            send_telegram_message(
                chat_id,
                f"❌ 自选股中未找到「{query}」\n"
                f"当前共 {len(stocks)} 只自选股，请确认代码或名称",
            )
            return

        db = DatabaseManager.get_instance().get_session()
        try:
            ok = service.remove_stock(db, target["id"])
        finally:
            db.close()

        if ok:
            send_telegram_message(
                chat_id,
                f"✅ 已从自选股中移除\n\n"
                f"• 代码：{target['stock_code']}\n"
                f"• 名称：{target.get('stock_name') or target['stock_code']}",
            )
        else:
            send_telegram_message(chat_id, "❌ 删除失败，请稍后重试")

    except Exception as e:
        logger.error(f"[BotEndpoint] 删除自选股失败: {e}", exc_info=True)
        send_telegram_message(chat_id, f"❌ 删除失败：{str(e)[:100]}")


def _do_analyze_stock(chat_id: str, stock_code: str | None, name_hint: str | None) -> None:
    from bot.intent_analyzer import send_telegram_message
    from src.services.watchlist_service import WatchlistService

    query = stock_code or name_hint
    if not query:
        send_telegram_message(chat_id, "❌ 未识别到股票代码或名称，请重新描述")
        return

    try:
        # 若只有名称，先搜索代码
        if not stock_code:
            service = WatchlistService()
            results = service.search_stock(query)
            if not results:
                send_telegram_message(chat_id, f"❌ 未找到股票「{query}」")
                return
            stock_code = results[0]["stock_code"]
            name_hint = results[0].get("stock_name") or stock_code

        from src.services.task_service import get_task_service
        from src.enums import ReportType
        from bot.models import BotMessage, ChatType
        from datetime import datetime

        # 构造最小化 BotMessage（供 task_service 记录来源）
        fake_msg = BotMessage(
            platform="telegram",
            message_id="intent",
            user_id="intent",
            user_name="intent",
            chat_id=chat_id,
            chat_type=ChatType.PRIVATE,
            content=f"/analyze {stock_code}",
            timestamp=datetime.now(),
        )

        task_service = get_task_service()
        result = task_service.submit_analysis(
            code=stock_code.lower(),
            report_type=ReportType.SIMPLE,
            source_message=fake_msg,
        )

        if result.get("success"):
            send_telegram_message(
                chat_id,
                f"✅ 已提交分析任务\n\n"
                f"• 股票：{name_hint or stock_code}\n"
                f"• 代码：{stock_code}\n\n"
                f"分析完成后将自动推送结果，请稍候...",
            )
        else:
            error = result.get("error", "未知错误")
            send_telegram_message(chat_id, f"❌ 提交分析任务失败：{error}")

    except Exception as e:
        logger.error(f"[BotEndpoint] 即时分析失败: {e}", exc_info=True)
        send_telegram_message(chat_id, f"❌ 分析失败：{str(e)[:100]}")


def _do_analyze_all(chat_id: str) -> None:
    from bot.intent_analyzer import send_telegram_message

    try:
        import asyncio
        from src.services.schedule_service import get_scheduler_service

        scheduler = get_scheduler_service()

        # trigger_now 是 async，在同步后台线程中用 asyncio.run
        result = asyncio.run(scheduler.trigger_now())
        submitted = result.get("submitted", 0)

        if submitted == 0:
            send_telegram_message(
                chat_id,
                "⚠️ 自选股列表为空，无法触发分析\n"
                "请先添加自选股，例如：「添加 贵州茅台」",
            )
        else:
            send_telegram_message(
                chat_id,
                f"✅ 已提交 {submitted} 只自选股分析任务\n\n"
                f"分析完成后将自动推送结果，请稍候...",
            )
    except Exception as e:
        logger.error(f"[BotEndpoint] 分析所有自选股失败: {e}", exc_info=True)
        send_telegram_message(chat_id, f"❌ 触发分析失败：{str(e)[:100]}")
