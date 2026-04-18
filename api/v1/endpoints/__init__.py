# -*- coding: utf-8 -*-
"""
===================================
API v1 Endpoints 模块初始化
===================================

说明：此处仅导出部分子模块，便于 `from api.v1.endpoints import X` 的兼容用法。
实际路由聚合见 `api.v1.router`（另含 watchlist、bot、multi_agent 等）。
"""

from api.v1.endpoints import health, analysis, history, stocks, backtest

__all__ = ["health", "analysis", "history", "stocks", "backtest"]
