# -*- coding: utf-8 -*-
"""
===================================
自选股管理命令
===================================

提供以下命令：
- /add <code_or_name>   : 添加股票到自选股
- /remove <code_or_name>: 从自选股删除（按代码或名称）
- /all                  : 立即分析所有自选股（触发定时任务逻辑）
"""

from loguru import logger
from typing import List, Optional

from bot.commands.base import BotCommand
from bot.models import BotMessage, BotResponse

# ──────────────────────────────────────────────────────────────
# /add 命令
# ──────────────────────────────────────────────────────────────

class AddWatchlistCommand(BotCommand):
    """
    添加自选股命令

    用法：
        /add 600519       - 按代码添加（贵州茅台）
        /add 贵州茅台     - 按名称搜索后添加
    """

    @property
    def name(self) -> str:
        """业务流程函数：name（模块：watchlist-cmd）。"""
        return "add"

    @property
    def aliases(self) -> List[str]:
        """业务流程函数：aliases（模块：watchlist-cmd）。"""
        return ["添加", "加入", "关注"]

    @property
    def description(self) -> str:
        """业务流程函数：description（模块：watchlist-cmd）。"""
        return "添加股票到自选股"

    @property
    def usage(self) -> str:
        """业务流程函数：usage（模块：watchlist-cmd）。"""
        return "/add <股票代码或名称>"

    def validate_args(self, args: List[str]) -> Optional[str]:
        """业务流程函数：validate_args（模块：watchlist-cmd）。"""
        if not args:
            return "请输入股票代码或名称"
        return None

    def execute(self, message: BotMessage, args: List[str]) -> BotResponse:
        """业务流程函数：execute（模块：watchlist-cmd）。"""
        query = " ".join(args).strip()
        logger.info(f"[AddWatchlistCommand] 添加自选股: {query}")

        try:
            from src.services.watchlist_service import WatchlistService
            from src.storage import DatabaseManager

            service = WatchlistService()

            # 搜索股票
            results = service.search_stock(query)
            if not results:
                return BotResponse.error_response(
                    f"未找到股票「{query}」，请检查代码或名称是否正确"
                )

            stock = results[0]
            code = stock["stock_code"]
            name = stock.get("stock_name") or code

            # 写入数据库
            db = DatabaseManager.get_instance().get_session()
            try:
                item = service.add_stock(db, code, name)
            finally:
                db.close()

            return BotResponse.text_response(
                f"✅ 已添加自选股\n\n"
                f"• 代码：{item['stock_code']}\n"
                f"• 名称：{item.get('stock_name') or name}"
            )

        except Exception as e:
            logger.error(f"[AddWatchlistCommand] 失败: {e}", exc_info=True)
            return BotResponse.error_response(f"添加失败: {str(e)[:100]}")


# ──────────────────────────────────────────────────────────────
# /remove 命令
# ──────────────────────────────────────────────────────────────

class RemoveWatchlistCommand(BotCommand):
    """
    从自选股删除命令

    用法：
        /remove 600519   - 按代码删除
        /remove 茅台     - 按名称模糊匹配后删除（取第一个匹配项）
    """

    @property
    def name(self) -> str:
        """业务流程函数：name（模块：watchlist-cmd）。"""
        return "remove"

    @property
    def aliases(self) -> List[str]:
        """业务流程函数：aliases（模块：watchlist-cmd）。"""
        return ["删除", "移除", "取消关注"]

    @property
    def description(self) -> str:
        """业务流程函数：description（模块：watchlist-cmd）。"""
        return "从自选股删除"

    @property
    def usage(self) -> str:
        """业务流程函数：usage（模块：watchlist-cmd）。"""
        return "/remove <股票代码或名称>"

    def validate_args(self, args: List[str]) -> Optional[str]:
        """业务流程函数：validate_args（模块：watchlist-cmd）。"""
        if not args:
            return "请输入股票代码或名称"
        return None

    def execute(self, message: BotMessage, args: List[str]) -> BotResponse:
        """业务流程函数：execute（模块：watchlist-cmd）。"""
        query = " ".join(args).strip().upper()
        logger.info(f"[RemoveWatchlistCommand] 删除自选股: {query}")

        try:
            from src.services.watchlist_service import WatchlistService
            from src.storage import DatabaseManager

            service = WatchlistService()
            db = DatabaseManager.get_instance().get_session()
            try:
                stocks = service.list_stocks(db)
            finally:
                db.close()

            if not stocks:
                return BotResponse.text_response("自选股列表为空，无需删除")

            # 先精确匹配代码，再模糊匹配名称
            target = None
            query_upper = query.upper()
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
                return BotResponse.error_response(
                    f"自选股中未找到「{query}」\n"
                    f"当前自选股共 {len(stocks)} 只，请确认代码或名称"
                )

            db = DatabaseManager.get_instance().get_session()
            try:
                ok = service.remove_stock(db, target["id"])
            finally:
                db.close()

            if ok:
                return BotResponse.text_response(
                    f"✅ 已从自选股中移除\n\n"
                    f"• 代码：{target['stock_code']}\n"
                    f"• 名称：{target.get('stock_name') or target['stock_code']}"
                )
            else:
                return BotResponse.error_response("删除失败，请稍后重试")

        except Exception as e:
            logger.error(f"[RemoveWatchlistCommand] 失败: {e}", exc_info=True)
            return BotResponse.error_response(f"删除失败: {str(e)[:100]}")


# ──────────────────────────────────────────────────────────────
# /all 命令
# ──────────────────────────────────────────────────────────────

class AnalyzeAllCommand(BotCommand):
    """
    立即分析所有自选股命令

    触发定时任务的同等逻辑——将所有自选股提交到分析队列。
    分析完成后会自动推送结果（与定时任务行为一致）。

    用法：
        /all
    """

    @property
    def name(self) -> str:
        """业务流程函数：name（模块：watchlist-cmd）。"""
        return "all"

    @property
    def aliases(self) -> List[str]:
        """业务流程函数：aliases（模块：watchlist-cmd）。"""
        return ["分析全部", "全部分析", "跑一遍"]

    @property
    def description(self) -> str:
        """业务流程函数：description（模块：watchlist-cmd）。"""
        return "立即分析所有自选股"

    @property
    def usage(self) -> str:
        """业务流程函数：usage（模块：watchlist-cmd）。"""
        return "/all"

    def validate_args(self, args: List[str]) -> Optional[str]:
        """业务流程函数：validate_args（模块：watchlist-cmd）。"""
        return None  # 不需要参数

    def execute(self, message: BotMessage, args: List[str]) -> BotResponse:
        """业务流程函数：execute（模块：watchlist-cmd）。"""
        logger.info("[AnalyzeAllCommand] 触发全量自选股分析")

        try:
            import asyncio
            from src.services.schedule_service import get_scheduler_service

            scheduler = get_scheduler_service()

            # trigger_now 是 async，在同步上下文中用 asyncio.run 调用
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 在已有事件循环中（FastAPI），创建 task
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, scheduler.trigger_now())
                        result = future.result(timeout=10)
                else:
                    result = loop.run_until_complete(scheduler.trigger_now())
            except RuntimeError:
                result = asyncio.run(scheduler.trigger_now())

            submitted = result.get("submitted", 0)
            if submitted == 0:
                return BotResponse.text_response(
                    "⚠️ 自选股列表为空，无法触发分析\n"
                    "请先用 /add <代码> 添加自选股"
                )

            return BotResponse.text_response(
                f"✅ 已提交 {submitted} 只自选股分析任务\n\n"
                f"分析完成后将自动推送结果，请稍候..."
            )

        except Exception as e:
            logger.error(f"[AnalyzeAllCommand] 失败: {e}", exc_info=True)
            return BotResponse.error_response(f"触发分析失败: {str(e)[:100]}")
