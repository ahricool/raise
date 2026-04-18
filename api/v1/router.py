# -*- coding: utf-8 -*-
"""
===================================
API v1 路由聚合
===================================

职责：
1. 聚合 v1 版本的所有 endpoint 路由
2. 统一添加 /api/v1 前缀
"""

from fastapi import APIRouter

from api.v1.endpoints import analysis, history, stocks, backtest, watchlist, bot, multi_agent

# 创建 v1 版本主路由
router = APIRouter(prefix="/api/v1")

# 股票 AI 分析：触发分析、任务状态、任务列表、SSE 推送等
router.include_router(
    analysis.router,
    prefix="/analysis",
    tags=["Analysis"]
)

# 历史分析记录：列表、单条详情等
router.include_router(
    history.router,
    prefix="/history",
    tags=["History"]
)

# 行情数据：单只股票实时行情、历史 K 线等
router.include_router(
    stocks.router,
    prefix="/stocks",
    tags=["Stocks"]
)

# 回测：对历史分析做回测、查询回测结果
router.include_router(
    backtest.router,
    prefix="/backtest",
    tags=["Backtest"]
)

# 自选股：列表、搜索、增删
router.include_router(
    watchlist.router,
    prefix="/watchlist",
    tags=["Watchlist"]
)

# 各平台机器人 Webhook（如 Telegram），接收平台推送并处理命令/自然语言
router.include_router(
    bot.router,
    prefix="/bot",
    tags=["Bot"]
)

# 多智能体分析 WebSocket：/api/v1/ws/multi-agent，实时推送各 Agent 节点进度与结果
router.include_router(
    multi_agent.router,
    tags=["MultiAgent"]
)
