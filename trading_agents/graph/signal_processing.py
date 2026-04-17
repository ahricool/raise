# -*- coding: utf-8 -*-
"""
信号处理模块

从投资组合经理的自由文本输出中提取标准化交易信号，
并将其映射到 raise 的 AnalysisResult 词汇。
"""

import re


# 信号关键词映射（中英文）
_BUY_PATTERNS = [
    r"\bBUY\b", r"\bOVERWEIGHT\b",
    r"买入", r"强烈看多", r"建议买入", r"积极买入",
]
_SELL_PATTERNS = [
    r"\bSELL\b", r"\bUNDERWEIGHT\b",
    r"卖出", r"强烈看空", r"建议卖出", r"减仓",
]
_HOLD_PATTERNS = [
    r"\bHOLD\b", r"\bNEUTRAL\b",
    r"持有", r"观望", r"震荡", r"等待",
]

# raise AnalysisResult operation_advice 词汇
_SIGNAL_TO_ADVICE = {
    "BUY": "买入",
    "HOLD": "持有",
    "SELL": "卖出",
}

_SIGNAL_TO_TREND = {
    "BUY": "看多",
    "HOLD": "震荡",
    "SELL": "看空",
}

_SIGNAL_TO_SCORE = {
    "BUY": 75,
    "HOLD": 50,
    "SELL": 30,
}

_SIGNAL_TO_DECISION_TYPE = {
    "BUY": "buy",
    "HOLD": "hold",
    "SELL": "sell",
}


def extract_signal(text: str) -> str:
    """
    从文本中提取 BUY / HOLD / SELL 信号。

    优先匹配最后一次出现的明确信号（投资组合经理通常在结尾给出最终决策）。
    """
    text_upper = text.upper()

    # 反向扫描——取最后一次出现的信号
    last_pos = -1
    last_signal = "HOLD"

    for pattern in _BUY_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            if m.start() > last_pos:
                last_pos = m.start()
                last_signal = "BUY"

    for pattern in _SELL_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            if m.start() > last_pos:
                last_pos = m.start()
                last_signal = "SELL"

    for pattern in _HOLD_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            if m.start() > last_pos:
                last_pos = m.start()
                last_signal = "HOLD"

    return last_signal


def signal_to_operation_advice(signal: str) -> str:
    return _SIGNAL_TO_ADVICE.get(signal, "持有")


def signal_to_trend_prediction(signal: str) -> str:
    return _SIGNAL_TO_TREND.get(signal, "震荡")


def signal_to_score(signal: str) -> int:
    return _SIGNAL_TO_SCORE.get(signal, 50)


def signal_to_decision_type(signal: str) -> str:
    return _SIGNAL_TO_DECISION_TYPE.get(signal, "hold")
