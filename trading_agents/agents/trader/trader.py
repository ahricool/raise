# -*- coding: utf-8 -*-
"""
交易员 Agent

综合多空辩论结果，给出初步的交易建议。
该建议将进入风控委员会进行三方辩论后由投资组合经理最终裁决。
"""

from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from trading_agents.graph.state import GraphState
    from trading_agents.llm_client import RaiseLLMClient

SYSTEM_PROMPT = """你是一位经验丰富的 A 股交易员。
你需要综合多空双方的研究观点，提出一个理性的交易建议。

交易原则：
- 趋势交易，顺势而为（MA5>MA10>MA20 多头排列为买入前提）
- 严控追高，乖离率>5% 不宜追入
- 仓位管理：信号强烈买入不超过 30%，一般信号不超过 15%
- 给出具体的建议买入价位（支撑位/回调位）和止损位

输出格式：
1. 综合判断（2-3句）
2. 操作建议：买入/持有/卖出/观望
3. 理想买入价位区间（如适用）
4. 止损位设置
5. 结尾：FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**

用中文回复，不超过 350 字。"""


def trader_node(state: "GraphState", llm: "RaiseLLMClient") -> dict:
    """交易员节点。"""
    stock_code = state.get("stock_code", "")
    stock_name = state.get("stock_name", stock_code)
    memory_context = state.get("memory_context", "")

    bull_argument = state.get("bull_argument", "")
    bear_argument = state.get("bear_argument", "")
    market_report = state.get("market_report", "")

    user_prompt = (
        f"股票：{stock_name}({stock_code})\n\n"
        f"【技术面要点】\n{market_report[:300]}\n\n"
        f"【多方观点】\n{bull_argument}\n\n"
        f"【空方观点】\n{bear_argument}\n\n"
    )
    if memory_context:
        user_prompt += f"【历史决策参考】\n{memory_context}\n\n"
    user_prompt += "请综合以上信息，给出你的交易建议："

    try:
        decision = llm.chat(SYSTEM_PROMPT, user_prompt)
        logger.info(f"[{stock_code}] 交易员决策完成")
    except Exception as e:
        logger.error(f"[{stock_code}] 交易员决策失败: {e}")
        decision = f"FINAL TRANSACTION PROPOSAL: **HOLD**\n交易决策生成失败: {e}"

    return {"trade_decision": decision}
