# -*- coding: utf-8 -*-
"""
结果适配器

将多智能体 GraphState 转换为 raise 现有的 AnalysisResult 格式，
确保下游通知、存储、API 响应完全兼容，无需改动。
"""

from typing import Any, Dict, TYPE_CHECKING

from trading_agents.graph.signal_processing import (
    extract_signal,
    signal_to_operation_advice,
    signal_to_trend_prediction,
    signal_to_score,
    signal_to_decision_type,
)

if TYPE_CHECKING:
    from trading_agents.graph.state import GraphState
    from src.analyzer import AnalysisResult


def adapt(state: "GraphState", stock_code: str, stock_name: str) -> "AnalysisResult":
    """将 GraphState 适配为 AnalysisResult。"""
    from src.analyzer import AnalysisResult

    final_decision = state.get("final_decision", "")
    final_signal = state.get("final_signal") or extract_signal(final_decision)

    operation_advice = signal_to_operation_advice(final_signal)
    trend_prediction = signal_to_trend_prediction(final_signal)
    sentiment_score = signal_to_score(final_signal)
    decision_type = signal_to_decision_type(final_signal)

    market_report = state.get("market_report", "")
    fundamentals_report = state.get("fundamentals_report", "")
    news_report = state.get("news_report", "")
    sentiment_report = state.get("sentiment_report", "")
    bull_argument = state.get("bull_argument", "")
    bear_argument = state.get("bear_argument", "")
    trade_decision = state.get("trade_decision", "")
    risk_aggressive = state.get("risk_aggressive", "")
    risk_conservative = state.get("risk_conservative", "")
    risk_neutral = state.get("risk_neutral", "")

    analysis_summary = _build_summary(
        final_decision, bull_argument, bear_argument, trade_decision
    )
    risk_warning = _extract_risk_warning(risk_conservative, final_decision)

    # 构建与 GeminiAnalyzer 兼容的 dashboard 结构
    dashboard = {
        "core_conclusion": {
            "one_liner": f"[多智能体] {final_signal}: {operation_advice}",
            "sentiment_score": sentiment_score,
            "operation_advice": operation_advice,
            "confidence_level": "中",
        },
        "data_perspective": {
            "trend": market_report[:500] if market_report else "",
            "fundamentals": fundamentals_report[:500] if fundamentals_report else "",
        },
        "intelligence": {
            "news_highlights": news_report[:500] if news_report else "",
            "sentiment": sentiment_report[:300] if sentiment_report else "",
            "risk_alerts": risk_warning,
        },
        "debate": {
            "bull_case": bull_argument[:600] if bull_argument else "",
            "bear_case": bear_argument[:600] if bear_argument else "",
            "trader_view": trade_decision[:400] if trade_decision else "",
            "risk_aggressive": risk_aggressive[:300] if risk_aggressive else "",
            "risk_conservative": risk_conservative[:300] if risk_conservative else "",
            "risk_neutral": risk_neutral[:300] if risk_neutral else "",
        },
        "final_decision": final_decision[:800] if final_decision else "",
    }

    return AnalysisResult(
        code=stock_code,
        name=stock_name,
        sentiment_score=sentiment_score,
        trend_prediction=trend_prediction,
        operation_advice=operation_advice,
        decision_type=decision_type,
        confidence_level="中",
        dashboard=dashboard,
        technical_analysis=market_report,
        fundamental_analysis=fundamentals_report,
        news_summary=news_report,
        market_sentiment=sentiment_report,
        analysis_summary=analysis_summary,
        risk_warning=risk_warning,
        data_sources="multi_agent_debate",
        success=True,
    )


def _build_summary(
    final_decision: str,
    bull_argument: str,
    bear_argument: str,
    trade_decision: str,
) -> str:
    parts = []
    if final_decision:
        parts.append(f"【最终裁决】{final_decision[:300]}")
    if trade_decision:
        parts.append(f"【交易员】{trade_decision[:200]}")
    if bull_argument:
        parts.append(f"【多方】{bull_argument[:200]}")
    if bear_argument:
        parts.append(f"【空方】{bear_argument[:200]}")
    return "\n\n".join(parts)


def _extract_risk_warning(risk_conservative: str, final_decision: str) -> str:
    text = risk_conservative or final_decision
    if not text:
        return ""
    # 取保守派风控的前300字作为风险提示
    return text[:300]
