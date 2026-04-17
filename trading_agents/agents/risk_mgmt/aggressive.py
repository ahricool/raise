# -*- coding: utf-8 -*-
"""激进风控 Agent - 支持高风险高收益决策，挑战保守观点。"""

from typing import TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from trading_agents.graph.state import GraphState
    from trading_agents.llm_client import RaiseLLMClient

SYSTEM_PROMPT = """你是风控委员会的激进派代表。
你认为适当的风险是必要的，高风险往往对应高收益。

职责：
1. 支持交易员的买入/卖出决策，为其提供数据支撑
2. 挑战过于保守的观点，指出保守策略可能错失的机会
3. 分析风险可控性，说明如何通过止损控制损失
4. 提出更积极的仓位建议

用中文回复，不超过 250 字。结尾：【支持操作】或【建议加码】。"""


def aggressive_risk_node(state: "GraphState", llm: "RaiseLLMClient") -> dict:
    """激进风控节点。"""
    stock_code = state.get("stock_code", "")
    stock_name = state.get("stock_name", stock_code)
    trade_decision = state.get("trade_decision", "")
    risk_conservative = state.get("risk_conservative", "")
    risk_neutral = state.get("risk_neutral", "")

    user_prompt = (
        f"股票：{stock_name}({stock_code})\n\n"
        f"【交易员建议】\n{trade_decision[:400]}\n\n"
    )
    if risk_conservative:
        user_prompt += f"【保守派观点（需反驳）】\n{risk_conservative[:300]}\n\n"
    if risk_neutral:
        user_prompt += f"【中立派观点】\n{risk_neutral[:300]}\n\n"
    user_prompt += "请从激进风控的角度评估："

    try:
        opinion = llm.chat(SYSTEM_PROMPT, user_prompt)
        logger.info(f"[{stock_code}] 激进风控完成")
    except Exception as e:
        logger.error(f"[{stock_code}] 激进风控失败: {e}")
        opinion = f"激进风控分析失败: {e}"

    history = list(state.get("risk_debate_history", []))
    history.append(f"[激进] {opinion}")

    return {
        "risk_aggressive": opinion,
        "risk_debate_history": history,
        "risk_iteration": state.get("risk_iteration", 0) + 1,
    }
