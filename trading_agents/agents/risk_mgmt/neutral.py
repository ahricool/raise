# -*- coding: utf-8 -*-
"""中立风控 Agent - 平衡激进与保守观点，提出折中方案。"""

from typing import TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from trading_agents.graph.state import GraphState
    from trading_agents.llm_client import RaiseLLMClient

SYSTEM_PROMPT = """你是风控委员会的中立派代表。
你追求在风险和收益之间寻找最优平衡点。

职责：
1. 综合激进派和保守派的观点，提炼各方合理之处
2. 评估概率加权后的期望收益
3. 提出符合风险收益比的折中方案
4. 给出明确的仓位比例建议（0%-30%）

用中文回复，不超过 250 字。结尾：【建议操作】或【建议观望】，并附仓位比例。"""


def neutral_risk_node(state: "GraphState", llm: "RaiseLLMClient") -> dict:
    """中立风控节点。"""
    stock_code = state.get("stock_code", "")
    stock_name = state.get("stock_name", stock_code)
    trade_decision = state.get("trade_decision", "")
    risk_aggressive = state.get("risk_aggressive", "")
    risk_conservative = state.get("risk_conservative", "")

    user_prompt = (
        f"股票：{stock_name}({stock_code})\n\n"
        f"【交易员建议】\n{trade_decision[:300]}\n\n"
        f"【激进派观点】\n{risk_aggressive[:200]}\n\n"
        f"【保守派观点】\n{risk_conservative[:200]}\n\n"
        "请从中立角度提出折中方案："
    )

    try:
        opinion = llm.chat(SYSTEM_PROMPT, user_prompt)
        logger.info(f"[{stock_code}] 中立风控完成")
    except Exception as e:
        logger.error(f"[{stock_code}] 中立风控失败: {e}")
        opinion = f"中立风控分析失败: {e}"

    history = list(state.get("risk_debate_history", []))
    history.append(f"[中立] {opinion}")

    return {
        "risk_neutral": opinion,
        "risk_debate_history": history,
    }
