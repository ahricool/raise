# -*- coding: utf-8 -*-
"""情绪分析师 Agent - 综合新闻与市场数据分析市场情绪。"""

import json
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from trading_agents.graph.state import GraphState
    from trading_agents.llm_client import RaiseLLMClient

SYSTEM_PROMPT = """你是一位专注于 A 股市场情绪分析的资深分析师。
综合技术面与新闻面数据，分析当前市场对该股票的情绪倾向。

分析要点：
1. 量价背离或共振信号
2. 资金流向（量比、换手率暗示的主力行为）
3. 新闻情绪（正面/负面报道比例）
4. 投资者情绪（是否恐慌/贪婪）

报告结尾给出情绪评级：【乐观】【中性】【悲观】。
用中文回复，不超过 250 字。"""


def sentiment_analyst_node(state: "GraphState", llm: "RaiseLLMClient") -> dict:
    """情绪分析师节点。"""
    stock_code = state.get("stock_code", "")
    stock_name = state.get("stock_name", stock_code)
    enhanced_context = state.get("enhanced_context", {})
    news_context = state.get("news_context", "")

    realtime = enhanced_context.get("realtime", {})
    trend = enhanced_context.get("trend_analysis", {})

    data_summary = json.dumps(
        {
            "股票": f"{stock_name}({stock_code})",
            "量比": realtime.get("volume_ratio", "未知"),
            "换手率": realtime.get("turnover_rate", "未知"),
            "涨跌幅": realtime.get("change_pct", "未知"),
            "量能状态": trend.get("volume_status", "未知"),
            "信号评分": trend.get("signal_score", 0),
        },
        ensure_ascii=False,
        indent=2,
    )

    news_snippet = (news_context or "")[:500]
    user_prompt = (
        f"请分析 {stock_name}({stock_code}) 的市场情绪：\n\n"
        f"市场数据：\n{data_summary}\n\n"
        f"新闻摘要：\n{news_snippet}"
    )

    try:
        report = llm.chat(SYSTEM_PROMPT, user_prompt)
        logger.info(f"[{stock_code}] 情绪分析师完成")
    except Exception as e:
        logger.error(f"[{stock_code}] 情绪分析师失败: {e}")
        report = f"情绪分析失败: {e}"

    return {"sentiment_report": report}
