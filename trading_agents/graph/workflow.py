# -*- coding: utf-8 -*-
"""
LangGraph 工作流构建

并行架构：
- 4 位分析师同时运行（market / fundamentals / news / sentiment）
- 3 位风控 Agent 同时运行（aggressive / conservative / neutral）
- 辩论轮次由 conditional_logic 控制

WebSocket 进度推送：
- 每个节点执行完毕后通过 progress_callback 发送进度事件
"""

from functools import partial
from typing import Any, Callable, Dict, Optional

from langgraph.graph import StateGraph, START, END

from trading_agents.graph.state import GraphState
from trading_agents.graph.conditional_logic import (
    should_continue_invest_debate,
    should_continue_risk_debate,
)
from trading_agents.llm_client import RaiseLLMClient

# Agent 节点导入
from trading_agents.agents.analysts.market_analyst import market_analyst_node
from trading_agents.agents.analysts.fundamentals_analyst import fundamentals_analyst_node
from trading_agents.agents.analysts.news_analyst import news_analyst_node
from trading_agents.agents.analysts.sentiment_analyst import sentiment_analyst_node
from trading_agents.agents.researchers.bull_researcher import bull_researcher_node
from trading_agents.agents.researchers.bear_researcher import bear_researcher_node
from trading_agents.agents.trader.trader import trader_node
from trading_agents.agents.risk_mgmt.aggressive import aggressive_risk_node
from trading_agents.agents.risk_mgmt.conservative import conservative_risk_node
from trading_agents.agents.risk_mgmt.neutral import neutral_risk_node
from trading_agents.agents.managers.portfolio_manager import portfolio_manager_node


def _wrap_with_progress(
    node_fn: Callable,
    node_name: str,
    llm: RaiseLLMClient,
    progress_callback: Optional[Callable[[str, str], None]] = None,
) -> Callable:
    """
    包装 Agent 节点函数：执行后通过回调发送进度通知。

    progress_callback(node_name, status)  status: "started" | "completed" | "error"
    """
    def wrapped(state: GraphState) -> Dict[str, Any]:
        """业务流程函数：wrapped（模块：workflow）。"""
        if progress_callback:
            try:
                progress_callback(node_name, "started")
            except Exception:
                pass
        try:
            result = node_fn(state, llm)
            if progress_callback:
                try:
                    progress_callback(node_name, "completed")
                except Exception:
                    pass
            return result
        except Exception as e:
            if progress_callback:
                try:
                    progress_callback(node_name, "error")
                except Exception:
                    pass
            raise

    wrapped.__name__ = node_name
    return wrapped


def build_graph(
    llm: Optional[RaiseLLMClient] = None,
    progress_callback: Optional[Callable[[str, str], None]] = None,
):
    """
    构建多智能体 LangGraph 工作流。

    并行节点：
    - analysts_parallel: market / fundamentals / news / sentiment 同时执行
    - risk_parallel: aggressive / conservative / neutral 同时执行

    Args:
        llm: LLM 客户端（为 None 时自动初始化）
        progress_callback: 进度回调函数 (node_name, status) -> None
                           用于 WebSocket 实时推送

    Returns:
        编译后的 LangGraph CompiledStateGraph
    """
    if llm is None:
        llm = RaiseLLMClient()

    def wrap(fn, name):
        """业务流程函数：wrap（模块：workflow）。"""
        return _wrap_with_progress(fn, name, llm, progress_callback)

    graph = StateGraph(GraphState)

    # === 节点注册 ===

    # 并行分析师节点（LangGraph 会自动并行执行 fan-out）
    graph.add_node("market_analyst", wrap(market_analyst_node, "market_analyst"))
    graph.add_node("fundamentals_analyst", wrap(fundamentals_analyst_node, "fundamentals_analyst"))
    graph.add_node("news_analyst", wrap(news_analyst_node, "news_analyst"))
    graph.add_node("sentiment_analyst", wrap(sentiment_analyst_node, "sentiment_analyst"))

    # 辩论节点
    graph.add_node("bull_researcher", wrap(bull_researcher_node, "bull_researcher"))
    graph.add_node("bear_researcher", wrap(bear_researcher_node, "bear_researcher"))

    # 交易员
    graph.add_node("trader", wrap(trader_node, "trader"))

    # 并行风控节点
    graph.add_node("aggressive_risk", wrap(aggressive_risk_node, "aggressive_risk"))
    graph.add_node("conservative_risk", wrap(conservative_risk_node, "conservative_risk"))
    graph.add_node("neutral_risk", wrap(neutral_risk_node, "neutral_risk"))

    # 投资组合经理
    graph.add_node("portfolio_manager", wrap(portfolio_manager_node, "portfolio_manager"))

    # === 边（执行顺序）===

    # 起点 → 4 位分析师（并行 fan-out）
    graph.add_edge(START, "market_analyst")
    graph.add_edge(START, "fundamentals_analyst")
    graph.add_edge(START, "news_analyst")
    graph.add_edge(START, "sentiment_analyst")

    # 4 位分析师都完成后 → 多空研究员（fan-in，LangGraph 自动等待所有前置节点）
    graph.add_edge("market_analyst", "bull_researcher")
    graph.add_edge("fundamentals_analyst", "bull_researcher")
    graph.add_edge("news_analyst", "bull_researcher")
    graph.add_edge("sentiment_analyst", "bull_researcher")

    # bull → bear（保证 bull 先完成）
    graph.add_edge("bull_researcher", "bear_researcher")

    # bear 完成后：条件路由（继续辩论 or 进入 trader）
    graph.add_conditional_edges(
        "bear_researcher",
        should_continue_invest_debate,
        {
            "continue": "bull_researcher",  # 继续辩论轮次
            "end": "trader",
        },
    )

    # 交易员 → 3 位风控（并行 fan-out）
    graph.add_edge("trader", "aggressive_risk")
    graph.add_edge("trader", "conservative_risk")
    graph.add_edge("trader", "neutral_risk")

    # 3 位风控完成后 → 条件路由（继续 or 进入 portfolio_manager）
    graph.add_conditional_edges(
        "aggressive_risk",
        should_continue_risk_debate,
        {
            "continue": "conservative_risk",  # 再辩一轮
            "end": "portfolio_manager",
        },
    )
    graph.add_edge("conservative_risk", "neutral_risk")
    graph.add_conditional_edges(
        "neutral_risk",
        should_continue_risk_debate,
        {
            "continue": "aggressive_risk",
            "end": "portfolio_manager",
        },
    )

    # 投资组合经理 → END
    graph.add_edge("portfolio_manager", END)

    return graph.compile()
