# -*- coding: utf-8 -*-
"""空方研究员 Agent - 构建看空论据，与多方形成辩论。"""

from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from trading_agents.graph.state import GraphState
    from trading_agents.llm_client import RaiseLLMClient

SYSTEM_PROMPT = """你是一位具有丰富 A 股经验的空方研究员。
你的职责是基于分析师报告，构建有理有据的看空/谨慎论据。

要求：
1. 挖掘技术面、基本面、新闻面的风险信号
2. 正面反驳多方的乐观论点（如果有）
3. 提出投资者需要警惕的具体风险点
4. 结尾明确表态：【坚定看空】或【谨慎观望】

用中文回复，不超过 400 字。"""


def bear_researcher_node(state: "GraphState", llm: "RaiseLLMClient") -> dict:
    """空方研究员节点。"""
    stock_code = state.get("stock_code", "")
    stock_name = state.get("stock_name", stock_code)

    market_report = state.get("market_report", "")
    fundamentals_report = state.get("fundamentals_report", "")
    news_report = state.get("news_report", "")
    sentiment_report = state.get("sentiment_report", "")
    bull_argument = state.get("bull_argument", "")

    user_prompt = (
        f"股票：{stock_name}({stock_code})\n\n"
        f"【技术面报告】\n{market_report}\n\n"
        f"【基本面报告】\n{fundamentals_report}\n\n"
        f"【新闻报告】\n{news_report}\n\n"
        f"【情绪报告】\n{sentiment_report}\n\n"
    )
    if bull_argument:
        user_prompt += f"【多方观点（需反驳）】\n{bull_argument}\n\n"
    user_prompt += "请构建你的看空/谨慎论据："

    try:
        argument = llm.chat(SYSTEM_PROMPT, user_prompt)
        logger.info(f"[{stock_code}] 空方研究员完成")
    except Exception as e:
        logger.error(f"[{stock_code}] 空方研究员失败: {e}")
        argument = f"看空论据生成失败: {e}"

    history = list(state.get("bear_debate_history", []))
    history.append(argument)

    return {
        "bear_argument": argument,
        "bear_debate_history": history,
    }
