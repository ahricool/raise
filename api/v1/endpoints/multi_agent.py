# -*- coding: utf-8 -*-
"""
多智能体分析 WebSocket 端点

通过 WebSocket 实时推送每个 Agent 节点的执行进度和最终结果。

协议：
  客户端发送 JSON: {"stock_code": "600519", "analysis_mode": "multi_agent"}
  服务器推送 JSON 事件流：
    {"event": "started",   "node": "market_analyst",     "display_name": "技术面分析师", "step": 1,  "total": 11}
    {"event": "completed", "node": "market_analyst",     "display_name": "技术面分析师", "step": 1,  "total": 11}
    ...
    {"event": "done",      "result": { ...AnalysisResult... }}
    {"event": "error",     "message": "..."}
"""

import asyncio
import json
import threading
from typing import Any, Dict, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from trading_agents.orchestrator import MultiAgentOrchestrator, NODE_DISPLAY_NAMES, TOTAL_STEPS

router = APIRouter()


@router.websocket("/ws/multi-agent")
async def multi_agent_websocket(websocket: WebSocket):
    """
    WebSocket 端点：运行多智能体分析并实时推送进度。

    连接建立后等待客户端发送请求参数，然后在后台线程运行分析，
    通过队列将进度事件推送到 WebSocket。
    """
    await websocket.accept()
    logger.info("WebSocket 连接已建立")

    try:
        # 等待客户端发送请求参数
        raw = await websocket.receive_text()
        try:
            params = json.loads(raw)
        except json.JSONDecodeError:
            await websocket.send_json({"event": "error", "message": "无效的 JSON 请求"})
            await websocket.close()
            return

        stock_code = params.get("stock_code", "").strip()
        if not stock_code:
            await websocket.send_json({"event": "error", "message": "缺少 stock_code 参数"})
            await websocket.close()
            return

        analysis_mode = params.get("analysis_mode", "multi_agent")

        await websocket.send_json({
            "event": "init",
            "message": f"开始多智能体分析: {stock_code}",
            "total_steps": TOTAL_STEPS,
        })

        # 事件队列：后台线程 → 主协程
        event_queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def progress_callback(node_name: str, status: str, current_step: int, total: int):
            """业务流程函数：progress_callback（模块：multi-agent）。"""
            display_name = NODE_DISPLAY_NAMES.get(node_name, node_name)
            event = {
                "event": status,          # "started" | "completed" | "error"
                "node": node_name,
                "display_name": display_name,
                "step": current_step,
                "total": total,
            }
            loop.call_soon_threadsafe(event_queue.put_nowait, event)

        # 在后台线程运行分析（避免阻塞事件循环）
        result_holder: Dict[str, Any] = {}
        error_holder: Dict[str, str] = {}

        def run_analysis():
            """业务流程函数：run_analysis（模块：multi-agent）。"""
            try:
                from src.config import get_config
                import copy
                from src.core.pipeline import StockAnalysisPipeline
                from src.enums import ReportType

                config = get_config()
                if analysis_mode in ("multi_agent",):
                    config = copy.copy(config)
                    config.enable_multi_agent = True

                # 构建 pipeline 以获取 enhanced_context 和 news_context
                pipeline = StockAnalysisPipeline(config=config, max_workers=1, query_source="websocket")

                # 获取数据
                pipeline.fetch_and_save_stock_data(stock_code)

                from src.analyzer import STOCK_NAME_MAP
                stock_name = STOCK_NAME_MAP.get(stock_code, f"股票{stock_code}")

                # 实时行情
                realtime_quote = None
                try:
                    realtime_quote = pipeline.fetcher_manager.get_realtime_quote(stock_code)
                    if realtime_quote and realtime_quote.name:
                        stock_name = realtime_quote.name
                except Exception:
                    pass

                # 筹码
                chip_data = None
                try:
                    chip_data = pipeline.fetcher_manager.get_chip_distribution(stock_code)
                except Exception:
                    pass

                # 趋势分析
                import pandas as pd
                trend_result = None
                try:
                    ctx = pipeline.db.get_analysis_context(stock_code)
                    if ctx and "raw_data" in ctx:
                        df = pd.DataFrame(ctx["raw_data"])
                        trend_result = pipeline.trend_analyzer.analyze(df, stock_code)
                except Exception:
                    pass

                # 新闻搜索
                news_context = None
                if pipeline.search_service.is_available:
                    try:
                        intel = pipeline.search_service.search_comprehensive_intel(
                            stock_code=stock_code, stock_name=stock_name, max_searches=3
                        )
                        if intel:
                            news_context = pipeline.search_service.format_intel_report(intel, stock_name)
                    except Exception:
                        pass

                # 构建 enhanced_context
                db_context = pipeline.db.get_analysis_context(stock_code) or {
                    "code": stock_code, "stock_name": stock_name
                }
                enhanced_context = pipeline._enhance_context(
                    db_context, realtime_quote, chip_data, trend_result, stock_name
                )

                # 运行多智能体编排器
                orchestrator = MultiAgentOrchestrator(
                    config=config,
                    progress_callback=progress_callback,
                )
                result = orchestrator.run(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    enhanced_context=enhanced_context,
                    news_context=news_context,
                )
                result_holder["result"] = result
            except Exception as e:
                logger.error(f"WebSocket 多智能体分析失败: {e}")
                error_holder["error"] = str(e)
            finally:
                # 发送终止信号
                loop.call_soon_threadsafe(event_queue.put_nowait, {"event": "__done__"})

        thread = threading.Thread(target=run_analysis, daemon=True)
        thread.start()

        # 转发事件到 WebSocket
        while True:
            try:
                event = await asyncio.wait_for(event_queue.get(), timeout=300)
            except asyncio.TimeoutError:
                await websocket.send_json({"event": "error", "message": "分析超时"})
                break

            if event.get("event") == "__done__":
                break

            await websocket.send_json(event)

        # 发送最终结果
        if "result" in result_holder:
            result = result_holder["result"]
            await websocket.send_json({
                "event": "done",
                "result": {
                    "code": result.code,
                    "name": result.name,
                    "sentiment_score": result.sentiment_score,
                    "trend_prediction": result.trend_prediction,
                    "operation_advice": result.operation_advice,
                    "decision_type": result.decision_type,
                    "confidence_level": result.confidence_level,
                    "dashboard": result.dashboard,
                    "technical_analysis": result.technical_analysis,
                    "fundamental_analysis": result.fundamental_analysis,
                    "news_summary": result.news_summary,
                    "market_sentiment": result.market_sentiment,
                    "analysis_summary": result.analysis_summary,
                    "risk_warning": result.risk_warning,
                    "data_sources": result.data_sources,
                },
            })
        elif "error" in error_holder:
            await websocket.send_json({"event": "error", "message": error_holder["error"]})

    except WebSocketDisconnect:
        logger.info("WebSocket 客户端主动断开")
    except Exception as e:
        logger.error(f"WebSocket 异常: {e}")
        try:
            await websocket.send_json({"event": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
