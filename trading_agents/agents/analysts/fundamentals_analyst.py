# -*- coding: utf-8 -*-
"""基本面分析师 Agent - 使用 enhanced_context 中的实时行情基本面数据。"""

import json
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from trading_agents.graph.state import GraphState
    from trading_agents.llm_client import RaiseLLMClient

SYSTEM_PROMPT = """你是一位专注于 A 股基本面分析的资深分析师。
基于提供的基本面数据，撰写一份简洁客观的基本面分析报告。

分析要点：
1. 估值水平（PE/PB 是否合理）
2. 市值规模与流通盘
3. 筹码成本结构（平均成本、获利比例）
4. 近期价格变化趋势（60日涨跌幅）

报告结尾给出明确基本面评级：【低估】【合理】【高估】。
用中文回复，不超过 300 字。"""


def fundamentals_analyst_node(state: "GraphState", llm: "RaiseLLMClient") -> dict:
    """基本面分析师节点。"""
    stock_code = state.get("stock_code", "")
    stock_name = state.get("stock_name", stock_code)
    enhanced_context = state.get("enhanced_context", {})

    realtime = enhanced_context.get("realtime", {})
    chip = enhanced_context.get("chip", {})

    data_summary = json.dumps(
        {
            "股票": f"{stock_name}({stock_code})",
            "当前价格": realtime.get("price", "未知"),
            "PE市盈率": realtime.get("pe_ratio", "未知"),
            "PB市净率": realtime.get("pb_ratio", "未知"),
            "总市值(亿)": realtime.get("total_mv", "未知"),
            "流通市值(亿)": realtime.get("circ_mv", "未知"),
            "60日涨跌幅": realtime.get("change_60d", "未知"),
            "筹码平均成本": chip.get("avg_cost", "未知") if chip else "未知",
            "获利筹码比例": f"{chip.get('profit_ratio', 0):.1%}" if chip else "未知",
            "筹码健康状态": chip.get("chip_status", "未知") if chip else "未知",
        },
        ensure_ascii=False,
        indent=2,
    )

    user_prompt = f"请基于以下基本面数据，撰写 {stock_name}({stock_code}) 的基本面分析报告：\n\n{data_summary}"

    try:
        report = llm.chat(SYSTEM_PROMPT, user_prompt)
        logger.info(f"[{stock_code}] 基本面分析师完成")
    except Exception as e:
        logger.error(f"[{stock_code}] 基本面分析师失败: {e}")
        report = f"基本面数据分析失败: {e}"

    return {"fundamentals_report": report}
