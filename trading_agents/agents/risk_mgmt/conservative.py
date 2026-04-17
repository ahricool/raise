# -*- coding: utf-8 -*-
"""保守风控 Agent - 强调下行风险保护，挑战激进观点。"""

from typing import TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from trading_agents.graph.state import GraphState
    from trading_agents.llm_client import RaiseLLMClient

SYSTEM_PROMPT = """你是风控委员会的保守派代表。
你的首要职责是保护本金，宁可错过收益，不可承担不必要的损失。

职责：
1. 识别交易决策中的潜在风险和下行空间
2. 质疑过于乐观的假设，指出被忽视的风险点
3. 评估最坏情景下的最大回撤
4. 提出更保守的仓位建议或止损要求

用中文回复，不超过 250 字。结尾：【建议谨慎】或【反对操作】。"""


def conservative_risk_node(state: "GraphState", llm: "RaiseLLMClient") -> dict:
    """保守风控节点。"""
    stock_code = state.get("stock_code", "")
    stock_name = state.get("stock_name", stock_code)
    trade_decision = state.get("trade_decision", "")
    risk_aggressive = state.get("risk_aggressive", "")

    user_prompt = (
        f"股票：{stock_name}({stock_code})\n\n"
        f"【交易员建议】\n{trade_decision[:400]}\n\n"
    )
    if risk_aggressive:
        user_prompt += f"【激进派观点（需质疑）】\n{risk_aggressive[:300]}\n\n"
    user_prompt += "请从保守风控的角度评估风险："

    try:
        opinion = llm.chat(SYSTEM_PROMPT, user_prompt)
        logger.info(f"[{stock_code}] 保守风控完成")
    except Exception as e:
        logger.error(f"[{stock_code}] 保守风控失败: {e}")
        opinion = f"保守风控分析失败: {e}"

    history = list(state.get("risk_debate_history", []))
    history.append(f"[保守] {opinion}")

    return {
        "risk_conservative": opinion,
        "risk_debate_history": history,
    }
