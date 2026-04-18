# -*- coding: utf-8 -*-
"""
===================================
定时任务服务
===================================

职责：
1. 管理 APScheduler 定时任务（AsyncIOScheduler，运行在 FastAPI 事件循环中）
2. 每日固定时间自动分析自选股列表
3. 开盘前 09:00（工作日）对 Telegram 持仓股票分析并推送今日交易建议
4. 收盘后 15:30（工作日）对 Telegram 持仓推送当日走势总结
5. 支持动态修改调度时间和手动立即触发
6. 对外暴露状态查询接口
"""

from __future__ import annotations

import asyncio
from loguru import logger
from datetime import datetime
from typing import Optional, Dict, Any, List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

_JOB_ID = "daily_watchlist_analysis"
_POSITION_MORNING_JOB_ID = "daily_position_morning_review"
_POSITION_NOON_JOB_ID = "daily_position_noon_playback"
_POSITION_EVENING_JOB_ID = "daily_position_evening_summary"


class SchedulerService:
    """
    APScheduler 定时任务服务（单例）

    生命周期由 FastAPI lifespan 管理：
        start()  → 应用启动时调用
        stop()   → 应用关闭时调用
    """

    _instance: Optional["SchedulerService"] = None

    def __new__(cls) -> "SchedulerService":
        """内部辅助逻辑：__new__（模块：schedule-service）。"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """内部辅助逻辑：__init__（模块：schedule-service）。"""
        if self._initialized:
            return
        self._scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
        self._last_run_at: Optional[datetime] = None
        self._last_run_stocks: int = 0
        self._initialized = True

    # ── 生命周期 ──────────────────────────────────────────────────────────

    def start(self, schedule_enabled: bool, schedule_time: str) -> None:
        """启动调度器，按配置决定是否注册每日任务"""
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("[Scheduler] APScheduler 已启动")

        if schedule_enabled:
            self._add_or_replace_job(schedule_time)
        else:
            logger.info("[Scheduler] 定时任务未启用（SCHEDULE_ENABLED=false）")

    def stop(self) -> None:
        """关闭调度器（应用退出时调用）"""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("[Scheduler] APScheduler 已关闭")

    # ── 调度管理 ──────────────────────────────────────────────────────────

    def _add_or_replace_job(self, schedule_time: str) -> None:
        """注册/替换每日定时任务"""
        try:
            hour, minute = map(int, schedule_time.split(":"))
        except ValueError:
            logger.error(f"[Scheduler] 无效的 schedule_time 格式: {schedule_time}，应为 HH:MM")
            return

        trigger = CronTrigger(hour=hour, minute=minute, timezone="Asia/Shanghai")
        self._scheduler.add_job(
            self._run_daily_analysis,
            trigger=trigger,
            id=_JOB_ID,
            replace_existing=True,
            name="自选股每日分析",
        )
        logger.info(f"[Scheduler] 每日分析任务已注册，执行时间: {schedule_time}")

        morning_trigger = CronTrigger(
            hour=9, minute=0, day_of_week="mon-fri", timezone="Asia/Shanghai"
        )
        self._scheduler.add_job(
            self._run_position_morning_review,
            trigger=morning_trigger,
            id=_POSITION_MORNING_JOB_ID,
            replace_existing=True,
            name="自选股晨间交易建议",
        )
        logger.info("[Scheduler] 自选股晨间交易建议已注册，执行时间: 09:00 (工作日)")

        noon_trigger = CronTrigger(
            hour=12, minute=0, day_of_week="mon-fri", timezone="Asia/Shanghai"
        )
        self._scheduler.add_job(
            self._run_position_noon_playback,
            trigger=noon_trigger,
            id=_POSITION_NOON_JOB_ID,
            replace_existing=True,
            name="自选股午间行情播报",
        )
        logger.info("[Scheduler] 自选股午间行情播报已注册，执行时间: 12:00 (工作日)")

        evening_trigger = CronTrigger(
            hour=15, minute=30, day_of_week="mon-fri", timezone="Asia/Shanghai"
        )
        self._scheduler.add_job(
            self._run_position_evening_summary,
            trigger=evening_trigger,
            id=_POSITION_EVENING_JOB_ID,
            replace_existing=True,
            name="自选股收盘走势总结",
        )
        logger.info("[Scheduler] 自选股收盘走势总结已注册，执行时间: 15:30 (工作日)")

    def reschedule(self, schedule_time: str) -> None:
        """
        动态更改执行时间（配置更新后调用）

        Args:
            schedule_time: 新的执行时间，格式 HH:MM
        """
        self._add_or_replace_job(schedule_time)

    def enable(self, schedule_time: str) -> None:
        """启用定时任务"""
        self._add_or_replace_job(schedule_time)

    def disable(self) -> None:
        """禁用定时任务（移除 job，调度器保持运行）"""
        if self._scheduler.get_job(_JOB_ID):
            self._scheduler.remove_job(_JOB_ID)
            logger.info("[Scheduler] 每日分析任务已移除")
        if self._scheduler.get_job(_POSITION_MORNING_JOB_ID):
            self._scheduler.remove_job(_POSITION_MORNING_JOB_ID)
            logger.info("[Scheduler] 自选股晨间交易建议已移除")
        if self._scheduler.get_job(_POSITION_NOON_JOB_ID):
            self._scheduler.remove_job(_POSITION_NOON_JOB_ID)
            logger.info("[Scheduler] 自选股午间行情播报已移除")
        if self._scheduler.get_job(_POSITION_EVENING_JOB_ID):
            self._scheduler.remove_job(_POSITION_EVENING_JOB_ID)
            logger.info("[Scheduler] 自选股收盘走势总结已移除")

    # ── 手动触发 ──────────────────────────────────────────────────────────

    async def trigger_now(self) -> Dict[str, Any]:
        """立即触发一次自选股队列分析（不影响正常定时计划）"""
        logger.info("[Scheduler] 手动触发自选股分析")
        count = await self._run_daily_analysis()
        return {"submitted": count, "triggered_at": datetime.now().isoformat()}

    async def trigger_push(self, mode: str) -> Dict[str, Any]:
        """
        立即触发一次 Telegram 推送任务。

        Args:
            mode: morning | noon | evening
        """
        if mode not in ("morning", "noon", "evening"):
            raise ValueError(f"无效的 mode: {mode}，应为 morning / noon / evening")
        logger.info(f"[Scheduler] 手动触发 Telegram 推送: {mode}")
        pushed = await asyncio.to_thread(self._run_position_job, mode)
        return {"mode": mode, "pushed": pushed, "triggered_at": datetime.now().isoformat()}

    # ── 状态查询 ──────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """
        返回调度器当前状态

        Returns:
            状态字典，包含 enabled, schedule_time, next_run_at, last_run_at 等
        """
        job = self._scheduler.get_job(_JOB_ID)
        next_run_at: Optional[str] = None
        schedule_time: Optional[str] = None

        if job:
            next_fire = getattr(job, "next_run_time", None)
            if next_fire:
                next_run_at = next_fire.isoformat()
            # 从 CronTrigger 反解 HH:MM 字符串
            trigger = getattr(job, "trigger", None)
            if trigger:
                try:
                    h = trigger.fields[5].expressions[0]   # hour field
                    m = trigger.fields[6].expressions[0]   # minute field
                    schedule_time = f"{h}:{int(str(m)):02d}"
                except Exception:
                    pass

        return {
            "enabled": job is not None,
            "schedule_time": schedule_time,
            "next_run_at": next_run_at,
            "last_run_at": self._last_run_at.isoformat() if self._last_run_at else None,
            "last_run_stocks": self._last_run_stocks,
            "scheduler_running": self._scheduler.running,
        }

    # ── 核心任务逻辑 ──────────────────────────────────────────────────────

    async def _run_daily_analysis(self) -> int:
        """
        读取自选股列表并逐个提交到 AnalysisTaskQueue。

        DB 操作在线程池中运行（同步 SQLAlchemy），submit_task 是同步的立即返回。

        Returns:
            成功提交的任务数
        """
        from src.storage import DatabaseManager
        from src.services.watchlist_service import WatchlistService
        from src.services.task_queue import get_task_queue, DuplicateTaskError
        from src.config import get_config

        config = get_config()
        report_type = config.report_type or "simple"

        def _fetch_stocks() -> list:
            """内部辅助逻辑：_fetch_stocks（模块：schedule-service）。"""
            db = DatabaseManager.get_instance().get_session()
            try:
                return WatchlistService().list_stocks(db)
            finally:
                db.close()

        try:
            stocks = await asyncio.to_thread(_fetch_stocks)
        except Exception as e:
            logger.error(f"[Scheduler] 获取自选股列表失败: {e}", exc_info=True)
            return 0

        if not stocks:
            logger.info("[Scheduler] 自选股列表为空，跳过本次分析")
            return 0

        queue = get_task_queue()
        submitted = 0
        skipped = 0

        for stock in stocks:
            code = stock.get("stock_code", "")
            name = stock.get("stock_name")
            if not code:
                continue
            try:
                queue.submit_task(code, stock_name=name, report_type=report_type)
                submitted += 1
                logger.info(f"[Scheduler] 已提交分析任务: {code} ({name})")
            except DuplicateTaskError:
                skipped += 1
                logger.debug(f"[Scheduler] 跳过（已在分析中）: {code}")
            except Exception as e:
                logger.warning(f"[Scheduler] 提交任务失败: {code} {e}")

        self._last_run_at = datetime.now()
        self._last_run_stocks = submitted
        logger.info(f"[Scheduler] 本次触发完成：提交 {submitted} 支，跳过 {skipped} 支")
        return submitted

    async def _run_position_morning_review(self) -> int:
        """开盘前 09:00：对自选股进行分析并给出今日交易建议。"""
        logger.info("[Scheduler] 开始执行自选股晨间交易建议")
        return await asyncio.to_thread(self._run_position_job, "morning")

    async def _run_position_noon_playback(self) -> int:
        """午间 12:00：对自选股进行分析并播报午间行情。"""
        logger.info("[Scheduler] 开始执行自选股午间行情播报")
        return await asyncio.to_thread(self._run_position_job, "noon")

    async def _run_position_evening_summary(self) -> int:
        """收盘后 15:30：对今日自选股走势进行总结。"""
        logger.info("[Scheduler] 开始执行自选股收盘走势总结")
        return await asyncio.to_thread(self._run_position_job, "evening")

    def _run_position_job(self, mode: str) -> int:
        """同步执行自选股分析并推送到 Telegram。mode: morning | noon | evening。"""
        import requests as _requests

        from src.config import get_config
        from src.core.pipeline import StockAnalysisPipeline
        from src.enums import ReportType
        from src.services.watchlist_service import WatchlistService
        from src.storage import DatabaseManager

        config = get_config()
        chat_id = (config.telegram_chat_id or "").strip()
        if not chat_id:
            logger.warning("[Scheduler] TELEGRAM_CHAT_ID 未配置，跳过推送")
            return 0

        # 读取自选股
        session = DatabaseManager.get_instance().get_session()
        try:
            stocks = WatchlistService().list_stocks(session)
        except Exception as e:
            logger.error(f"[Scheduler] 读取自选股失败: {e}", exc_info=True)
            return 0
        finally:
            session.close()

        if not stocks:
            logger.info("[Scheduler] 自选股列表为空，跳过")
            return 0

        # 逐支分析
        pipeline = StockAnalysisPipeline(config=config, max_workers=config.max_workers)
        results_by_code: Dict[str, Any] = {}
        for stock in stocks:
            code = stock.get("stock_code", "")
            if not code:
                continue
            try:
                res = pipeline.process_single_stock(
                    code, skip_analysis=False, single_stock_notify=False, report_type=ReportType.SIMPLE
                )
                if res:
                    results_by_code[code] = res
            except Exception as e:
                logger.error(f"[Scheduler] 自选股分析 {code} 失败: {e}", exc_info=True)

        if not results_by_code:
            logger.info("[Scheduler] 无有效分析结果，跳过推送")
            return 0

        from src.analyzer import AnalysisResult

        today = datetime.now().strftime("%Y-%m-%d")
        lines = []
        for stock in stocks:
            code = stock.get("stock_code", "")
            res = results_by_code.get(code)
            if not res or not isinstance(res, AnalysisResult):
                continue
            emoji = res.get_emoji()
            core = res.get_core_conclusion()
            if mode in ("morning", "noon"):
                lines.append(
                    f"{emoji} {res.name}({res.code}) | 建议: {res.operation_advice} | "
                    f"评分: {res.sentiment_score} | 结论: {core}"
                )
            else:  # evening
                pct = getattr(res, "change_pct", None)
                pct_str = f"{pct:+.2f}%" if pct is not None else "N/A"
                lines.append(f"{emoji} {res.name}({res.code}) | 今日涨跌: {pct_str} | 结论: {core}")

        if not lines:
            return 0

        if mode == "morning":
            title = f"📌 {today} 自选股晨间交易建议"
            footer = "以上内容仅供参考，不构成投资建议。"
        elif mode == "noon":
            title = f"🕛 {today} 自选股午间行情播报"
            footer = "以上内容仅供参考，不构成投资建议。"
        else:
            title = f"📈 {today} 自选股收盘走势总结"
            footer = "以上为今日走势回顾，仅供复盘参考。"

        text = f"{title}\n\n" + "\n".join(lines) + f"\n\n{footer}"
        bot_token = (config.telegram_bot_token or "").strip()
        if not bot_token:
            logger.warning("[Scheduler] TELEGRAM_BOT_TOKEN 未配置，跳过推送")
            return 0
        try:
            _requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": text},
                timeout=10,
            )
            logger.info(f"[Scheduler] 已推送 {mode} 报告至 {chat_id}，共 {len(lines)} 支")
            return 1
        except Exception as e:
            logger.error(f"[Scheduler] 推送至 {chat_id} 失败: {e}", exc_info=True)
            return 0


def get_scheduler_service() -> SchedulerService:
    """获取 SchedulerService 单例"""
    return SchedulerService()
