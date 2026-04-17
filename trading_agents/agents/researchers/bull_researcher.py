# -*- coding: utf-8 -*-
"""多方研究员 Agent - 基于四位分析师报告构建看多论据。"""

from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from trading_agents.graph.state import GraphState
    from trading_agents.llm_client import RaiseLLMClient

SYSTEM_PROMPT = """你是一位具有丰富 A 股经验的多方研究员。
你的职责是基于分析师报告，构建强有力的看多论据。

要求：
1. 充分挖掘技术面、基本面、新闻面的看多信号
2. 正面回应空方的质疑（如果有空方观点）
3. 论据具体，引用数据支撑
4. 结尾明确表态：【坚定看多】或【谨慎看多】

用中文回复，不超过 400 字。"""


def bull_researcher_node(state: "GraphState", llm: "RaiseLLMClient") -> dict:
    """多方研究员节点。"""
    stock_code = state.get("stock_code", "")
    stock_name = state.get("stock_name", stock_code)

    market_report = state.get("market_report", "")
    fundamentals_report = state.get("fundamentals_report", "")
    news_report = state.get("news_report", "")
    sentiment_report = state.get("sentiment_report", "")
    bear_argument = state.get("bear_argument", "")

    user_prompt = (
        f"股票：{stock_name}({stock_code})\n\n"
        f"【技术面报告】\n{market_report}\n\n"
        f"【基本面报告】\n{fundamentals_report}\n\n"
        f"【新闻报告】\n{news_report}\n\n"
        f"【情绪报告】\n{sentiment_report}\n\n"
    )
    if bear_argument:
        user_prompt += f"【空方观点（需反驳）】\n{bear_argument}\n\n"
    user_prompt += "请构建你的看多论据："

    try:
        argument = llm.chat(SYSTEM_PROMPT, user_prompt)
        logger.info(f"[{stock_code}] 多方研究员完成（轮次 {state.get('invest_iteration', 0) + 1}）")
    except Exception as e:
        logger.error(f"[{stock_code}] 多方研究员失败: {e}")
        argument = f"看多论据生成失败: {e}"

    history = list(state.get("bull_debate_history", []))
    history.append(argument)

    return {
        "bull_argument": argument,
        "bull_debate_history": history,
        "invest_iteration": state.get("invest_iteration", 0) + 1,
    }
