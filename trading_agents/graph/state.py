# -*- coding: utf-8 -*-
"""
多智能体图状态定义

GraphState 是整个 LangGraph 工作流的共享状态，
每个 Agent 节点读取所需字段并返回自己的更新字典。
"""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class GraphState(TypedDict, total=False):
    # === 输入 ===
    """业务实体类：GraphState。"""
    stock_code: str
    stock_name: str
    enhanced_context: Dict[str, Any]   # StockAnalysisPipeline 已构建的增强上下文
    news_context: Optional[str]        # SearchService 已获取的新闻文本

    # === 四位分析师报告 ===
    market_report: str          # 技术面分析师
    fundamentals_report: str    # 基本面分析师
    news_report: str            # 新闻分析师
    sentiment_report: str       # 情绪分析师

    # === 多空辩论 ===
    bull_argument: str
    bear_argument: str
    bull_debate_history: List[str]
    bear_debate_history: List[str]
    invest_iteration: int       # 当前辩论轮次

    # === 交易员决策 ===
    trade_decision: str

    # === 风控辩论 ===
    risk_aggressive: str
    risk_conservative: str
    risk_neutral: str
    risk_debate_history: List[str]
    risk_iteration: int

    # === 最终裁决 ===
    final_decision: str
    final_signal: str           # BUY / HOLD / SELL

    # === 记忆系统 ===
    memory_context: str         # 历史决策记忆摘要（注入到相关 Agent 提示）
