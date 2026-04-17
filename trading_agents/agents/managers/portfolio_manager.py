# -*- coding: utf-8 -*-
"""
投资组合经理 Agent - 最终裁决者

综合所有分析师报告、多空辩论、交易员意见和三方风控观点，
给出最终的投资决策和具体的操作计划。
"""

from typing import TYPE_CHECKING

from loguru import logger
from trading_agents.graph.signal_processing import extract_signal

if TYPE_CHECKING:
    from trading_agents.graph.state import GraphState
    from trading_agents.llm_client import RaiseLLMClient

SYSTEM_PROMPT = """你是投资组合经理，拥有最终决策权。
你需要综合所有团队成员的分析，做出最终的投资裁决。

裁决要求：
1. 简短总结各方核心观点（不超过3句）
2. 给出最终操作建议：买入/持有/卖出/观望
3. 如果建议买入或加仓，提供：
   - 理想买入价位（支撑位/回调点）
   - 备选买入价位
   - 止损位（跌破则离场）
   - 止盈目标位
   - 建议仓位比例（0%-30%）
4. 核心风险提示（1-2条）

输出格式（严格遵循）：
## 最终裁决
**决策**：[买入/持有/卖出/观望]
**置信度**：[高/中/低]

## 操作计划
（如适用）
- 理想买入：X.XX 元
- 备选买入：X.XX 元
- 止损位：X.XX 元
- 止盈目标：X.XX 元
- 建议仓位：X%

## 核心风险
- [风险1]
- [风险2]

## 最终信号
FINAL SIGNAL: **BUY/HOLD/SELL**

用中文回复，不超过 500 字。"""


def portfolio_manager_node(state: "GraphState", llm: "RaiseLLMClient") -> dict:
    """投资组合经理节点（最终裁决）。"""
    stock_code = state.get("stock_code", "")
    stock_name = state.get("stock_name", stock_code)
    memory_context = state.get("memory_context", "")

    user_prompt = (
        f"股票：{stock_name}({stock_code})\n\n"
        f"【技术面分析】\n{state.get('market_report', '')[:300]}\n\n"
        f"【基本面分析】\n{state.get('fundamentals_report', '')[:200]}\n\n"
        f"【新闻面分析】\n{state.get('news_report', '')[:200]}\n\n"
        f"【多方观点】\n{state.get('bull_argument', '')[:300]}\n\n"
        f"【空方观点】\n{state.get('bear_argument', '')[:300]}\n\n"
        f"【交易员建议】\n{state.get('trade_decision', '')[:300]}\n\n"
        f"【激进风控】\n{state.get('risk_aggressive', '')[:200]}\n\n"
        f"【保守风控】\n{state.get('risk_conservative', '')[:200]}\n\n"
        f"【中立风控】\n{state.get('risk_neutral', '')[:200]}\n\n"
    )
    if memory_context:
        user_prompt += f"【历史决策参考】\n{memory_context}\n\n"
    user_prompt += "请做出最终裁决："

    try:
        decision = llm.chat(SYSTEM_PROMPT, user_prompt)
        logger.info(f"[{stock_code}] 投资组合经理裁决完成")
    except Exception as e:
        logger.error(f"[{stock_code}] 投资组合经理失败: {e}")
        decision = "FINAL SIGNAL: **HOLD**\n最终裁决生成失败，默认持有观望。"

    final_signal = extract_signal(decision)

    return {
        "final_decision": decision,
        "final_signal": final_signal,
    }
