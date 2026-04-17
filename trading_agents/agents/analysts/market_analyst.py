# -*- coding: utf-8 -*-
"""
技术面分析师 Agent

使用 StockAnalysisPipeline 已构建的 enhanced_context（含 MA/量能/筹码/趋势分析），
生成专业的技术面分析报告。无需额外网络请求。
"""

import json
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from trading_agents.graph.state import GraphState
    from trading_agents.llm_client import RaiseLLMClient

SYSTEM_PROMPT = """你是一位专注于 A 股技术分析的资深分析师。
你的任务是基于提供的技术数据，撰写一份清晰、客观的技术面分析报告。

分析要点：
1. 均线结构（MA5/MA10/MA20 多头/空头排列）
2. 趋势强度与买入信号评级
3. 量价关系（量比、成交量趋势）
4. 筹码分布健康度
5. 当前价格位置与乖离率风险

报告结尾必须给出明确的技术面评级：【看多】【中性】【看空】。
用中文回复，不超过 400 字。"""


def market_analyst_node(state: "GraphState", llm: "RaiseLLMClient") -> dict:
    """技术面分析师节点。"""
    stock_code = state.get("stock_code", "")
    stock_name = state.get("stock_name", stock_code)
    enhanced_context = state.get("enhanced_context", {})

    trend = enhanced_context.get("trend_analysis", {})
    realtime = enhanced_context.get("realtime", {})
    chip = enhanced_context.get("chip", {})
    today = enhanced_context.get("today", {})

    data_summary = json.dumps(
        {
            "股票": f"{stock_name}({stock_code})",
            "趋势状态": trend.get("trend_status", "未知"),
            "均线排列": trend.get("ma_alignment", "未知"),
            "趋势强度": f"{trend.get('trend_strength', 0):.1f}%",
            "MA5乖离率": f"{trend.get('bias_ma5', 0):.2f}%",
            "MA10乖离率": f"{trend.get('bias_ma10', 0):.2f}%",
            "量能状态": trend.get("volume_status", "未知"),
            "买入信号": trend.get("buy_signal", "未知"),
            "信号评分": trend.get("signal_score", 0),
            "信号依据": trend.get("signal_reasons", []),
            "风险因素": trend.get("risk_factors", []),
            "量比": realtime.get("volume_ratio", "未知"),
            "换手率": realtime.get("turnover_rate", "未知"),
            "获利筹码比例": f"{chip.get('profit_ratio', 0):.1%}" if chip else "未知",
            "今日收盘": today.get("close", "未知"),
        },
        ensure_ascii=False,
        indent=2,
    )

    user_prompt = f"请基于以下技术数据，撰写 {stock_name}({stock_code}) 的技术面分析报告：\n\n{data_summary}"

    try:
        report = llm.chat(SYSTEM_PROMPT, user_prompt)
        logger.info(f"[{stock_code}] 技术面分析师完成")
    except Exception as e:
        logger.error(f"[{stock_code}] 技术面分析师失败: {e}")
        report = f"技术面数据获取失败: {e}"

    return {"market_report": report}
