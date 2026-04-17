# -*- coding: utf-8 -*-
"""新闻分析师 Agent - 解析 SearchService 已获取的新闻情报。"""

from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from trading_agents.graph.state import GraphState
    from trading_agents.llm_client import RaiseLLMClient

SYSTEM_PROMPT = """你是一位专注于 A 股新闻事件分析的资深分析师。
基于提供的新闻情报，提炼对股价有实质影响的信息。

分析要点：
1. 正面催化剂（政策利好、业绩超预期、合同签订等）
2. 负面风险（监管处罚、业绩下滑、行业政策收紧等）
3. 中性信息（人事变动、常规公告等）
4. 市场热点关联性

报告结尾给出新闻面评级：【利多】【中性】【利空】。
用中文回复，不超过 350 字。如无新闻数据，说明"暂无最新情报"。"""


def news_analyst_node(state: "GraphState", llm: "RaiseLLMClient") -> dict:
    """新闻分析师节点。"""
    stock_code = state.get("stock_code", "")
    stock_name = state.get("stock_name", stock_code)
    news_context = state.get("news_context") or "（本次分析未获取到最新新闻情报）"

    # 截断过长的新闻文本，避免超出上下文限制
    if len(news_context) > 3000:
        news_context = news_context[:3000] + "\n...[新闻内容已截断]"

    user_prompt = (
        f"请分析以下关于 {stock_name}({stock_code}) 的新闻情报，"
        f"并撰写新闻面分析报告：\n\n{news_context}"
    )

    try:
        report = llm.chat(SYSTEM_PROMPT, user_prompt)
        logger.info(f"[{stock_code}] 新闻分析师完成")
    except Exception as e:
        logger.error(f"[{stock_code}] 新闻分析师失败: {e}")
        report = f"新闻分析失败: {e}"

    return {"news_report": report}
