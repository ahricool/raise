# -*- coding: utf-8 -*-
"""
金融记忆系统

从数据库读取该股票的历史 AI 决策，将其格式化为上下文字符串，
供交易员和投资组合经理参考，避免重复相同错误。
"""

from typing import Optional
from loguru import logger


class FinancialSituationMemory:
    """使用 raise 现有数据库存储和查询股票决策记忆。"""

    def get_memory_context(self, stock_code: str, limit: int = 3) -> str:
        """
        查询某只股票最近的历史决策，格式化为提示上下文。

        Returns:
            格式化的记忆字符串，供注入 Agent 提示；若无记录返回空字符串。
        """
        try:
            from src.storage import get_db
            db = get_db()
            memories = db.get_agent_memories(stock_code, limit=limit)
            if not memories:
                return ""
            lines = [f"过去 {len(memories)} 次对 {stock_code} 的决策记录："]
            for m in memories:
                lines.append(
                    f"- 决策：{m['signal']}，时间：{m['created_at']}"
                    + (f"，备注：{m['outcome_context']}" if m.get("outcome_context") else "")
                )
            return "\n".join(lines)
        except Exception as e:
            logger.debug(f"记忆系统查询失败（非致命）: {e}")
            return ""

    def save_decision(self, stock_code: str, signal: str, outcome_context: str = "") -> None:
        """保存本次决策到记忆系统。"""
        try:
            from src.storage import get_db
            db = get_db()
            db.save_agent_memory(stock_code, signal, outcome_context)
        except Exception as e:
            logger.debug(f"记忆系统写入失败（非致命）: {e}")
