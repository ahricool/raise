# -*- coding: utf-8 -*-
"""
LangGraph 工作流定义：状态 `GraphState` 与 `build_graph()` 构建的多智能体 DAG。

条件边与节点实现在 `conditional_logic`、`workflow` 等模块中。
"""

from trading_agents.graph.state import GraphState
from trading_agents.graph.workflow import build_graph

__all__ = ["GraphState", "build_graph"]
