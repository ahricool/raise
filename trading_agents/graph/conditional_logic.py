# -*- coding: utf-8 -*-
"""辩论轮次路由逻辑"""

from typing import TYPE_CHECKING
from src.config import get_config

if TYPE_CHECKING:
    from trading_agents.graph.state import GraphState


def should_continue_invest_debate(state: "GraphState") -> str:
    """判断是否继续多空辩论。"""
    config = get_config()
    max_rounds = config.multi_agent_invest_debate_rounds
    current = state.get("invest_iteration", 0)
    return "continue" if current < max_rounds else "end"


def should_continue_risk_debate(state: "GraphState") -> str:
    """判断是否继续风控辩论。"""
    config = get_config()
    max_rounds = config.multi_agent_risk_debate_rounds
    current = state.get("risk_iteration", 0)
    return "continue" if current < max_rounds else "end"
