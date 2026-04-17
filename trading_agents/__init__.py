# -*- coding: utf-8 -*-
"""
多智能体交易分析框架

将 TradingAgents 的多智能体辩论架构迁移到 raise，
复用 raise 现有的数据源、LLM 配置和通知系统。

核心流程：
  4 分析师 → 多空辩论 → 交易员 → 三方风控辩论 → 投资组合经理 → AnalysisResult
"""

from trading_agents.orchestrator import MultiAgentOrchestrator

__all__ = ["MultiAgentOrchestrator"]
