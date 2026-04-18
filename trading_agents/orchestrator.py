# -*- coding: utf-8 -*-
"""
多智能体分析编排器

作为 StockAnalysisPipeline 中多智能体模式的入口点：
1. 接收 pipeline 已构建的 enhanced_context 和 news_context
2. 构建 GraphState 并运行 LangGraph 工作流
3. 将最终状态转换为 AnalysisResult（与单次 AI 分析结果格式完全兼容）
4. 持久化辩论日志和记忆

WebSocket 进度推送：
  通过 progress_callback 参数支持实时进度通知。
  orchestrator 不直接操作 WebSocket，由调用方注入回调。
"""

from typing import Any, Callable, Dict, Optional

from loguru import logger

from src.config import Config, get_config
from trading_agents.graph.result_adapter import adapt
from trading_agents.graph.state import GraphState
from trading_agents.agents.memory.financial_memory import FinancialSituationMemory


# Node 名称 → 中文显示名（用于前端进度展示）
NODE_DISPLAY_NAMES: Dict[str, str] = {
    "market_analyst": "技术面分析师",
    "fundamentals_analyst": "基本面分析师",
    "news_analyst": "新闻分析师",
    "sentiment_analyst": "情绪分析师",
    "bull_researcher": "多方研究员",
    "bear_researcher": "空方研究员",
    "trader": "交易员",
    "aggressive_risk": "激进风控",
    "conservative_risk": "保守风控",
    "neutral_risk": "中立风控",
    "portfolio_manager": "投资组合经理",
}

# 工作流步骤总数（用于计算进度百分比）
TOTAL_STEPS = len(NODE_DISPLAY_NAMES)


class MultiAgentOrchestrator:
    """
    多智能体分析编排器。

    线程安全：每次 run() 调用都构建独立的 GraphState，
    图对象在实例级别缓存（LangGraph CompiledGraph 是线程安全的）。
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        progress_callback: Optional[Callable[[str, str, int, int], None]] = None,
    ):
        """
        Args:
            config: raise 配置对象
            progress_callback: 进度回调 (node_name, status, current_step, total_steps)
                               供 WebSocket 端点使用
        """
        self.config = config or get_config()
        self.progress_callback = progress_callback
        self._memory = FinancialSituationMemory()
        self._graph = None  # 惰性初始化

    def _get_graph(self):
        """惰性初始化并缓存编译后的图（节省重复编译开销）。"""
        if self._graph is None:
            from trading_agents.llm_client import RaiseLLMClient
            from trading_agents.graph.workflow import build_graph

            llm = RaiseLLMClient(temperature=self.config.multi_agent_llm_temperature)

            step_counter = {"current": 0}

            def _progress_wrapper(node_name: str, status: str) -> None:
                """内部辅助逻辑：_progress_wrapper（模块：orchestrator）。"""
                if status == "completed":
                    step_counter["current"] += 1
                if self.progress_callback:
                    try:
                        self.progress_callback(
                            node_name,
                            status,
                            step_counter["current"],
                            TOTAL_STEPS,
                        )
                    except Exception as e:
                        logger.debug(f"进度回调异常（非致命）: {e}")

            self._graph = build_graph(llm=llm, progress_callback=_progress_wrapper)
            logger.debug("多智能体图编译完成")
        return self._graph

    def run(
        self,
        stock_code: str,
        stock_name: str,
        enhanced_context: Dict[str, Any],
        news_context: Optional[str] = None,
    ):
        """
        运行多智能体分析流水线。

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            enhanced_context: pipeline 已构建的增强上下文（含 trend_analysis/realtime/chip）
            news_context: SearchService 已获取的新闻文本

        Returns:
            AnalysisResult（与 GeminiAnalyzer 输出格式完全兼容）
        """
        logger.info(f"[{stock_code}] 多智能体分析启动 (辩论轮次: invest={self.config.multi_agent_invest_debate_rounds}, risk={self.config.multi_agent_risk_debate_rounds})")

        # 获取历史记忆
        memory_context = self._memory.get_memory_context(stock_code)

        # 初始状态
        initial_state: GraphState = {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "enhanced_context": enhanced_context,
            "news_context": news_context or "",
            "memory_context": memory_context,
            "market_report": "",
            "fundamentals_report": "",
            "news_report": "",
            "sentiment_report": "",
            "bull_argument": "",
            "bear_argument": "",
            "bull_debate_history": [],
            "bear_debate_history": [],
            "invest_iteration": 0,
            "trade_decision": "",
            "risk_aggressive": "",
            "risk_conservative": "",
            "risk_neutral": "",
            "risk_debate_history": [],
            "risk_iteration": 0,
            "final_decision": "",
            "final_signal": "",
        }

        graph = self._get_graph()

        try:
            final_state = graph.invoke(
                initial_state,
                config={"recursion_limit": 50},
            )
        except Exception as e:
            logger.error(f"[{stock_code}] 多智能体图执行失败: {e}")
            raise

        logger.info(f"[{stock_code}] 多智能体分析完成，最终信号: {final_state.get('final_signal', 'HOLD')}")

        # 持久化辩论日志
        self._save_debate_log(stock_code, final_state)

        # 保存记忆
        final_signal = final_state.get("final_signal", "HOLD")
        self._memory.save_decision(stock_code, final_signal)

        # 转换为 AnalysisResult
        result = adapt(final_state, stock_code, stock_name)
        return result

    def _save_debate_log(self, stock_code: str, state: Dict[str, Any]) -> None:
        """持久化辩论过程（非致命，失败不影响主流程）。"""
        try:
            from src.storage import get_db
            db = get_db()
            db.save_multi_agent_debate_log(stock_code=stock_code, state_dict=state)
        except Exception as e:
            logger.warning(f"[{stock_code}] 辩论日志保存失败（非致命）: {e}")
