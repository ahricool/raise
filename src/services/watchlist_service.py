# -*- coding: utf-8 -*-
"""
自选股服务层

职责：
1. 股票搜索（按代码或名称）
2. 自选股增删查
"""

import logging
import re
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import select

from src.storage import User, UserStock

logger = logging.getLogger(__name__)

# 无需用户认证时使用的默认 user_id
_DEFAULT_USER_ID = 1
_DEFAULT_USERNAME = "default"


class WatchlistService:
    """自选股服务"""

    # ── 股票搜索 ──────────────────────────────────────────────────────────

    def search_stock(self, query: str) -> List[Dict[str, Any]]:
        """
        按代码或名称搜索股票，返回候选列表。

        策略：
        1. 若输入为 6 位数字 / HK 格式 / 英文字母 → 直接取行情确认
        2. 否则 → 用 akshare 的 A 股代码名称列表做模糊匹配
        """
        query = query.strip()
        if not query:
            return []

        # 判断输入类型
        if self._looks_like_code(query):
            return self._lookup_by_code(query)
        else:
            return self._search_by_name(query)

    @staticmethod
    def _looks_like_code(q: str) -> bool:
        """判断输入是否像股票代码"""
        # 6 位纯数字 A 股
        if re.fullmatch(r'\d{5,6}', q):
            return True
        # HK 格式：hk + 5 位数字，或单独 5 位数字（0 开头）
        if re.fullmatch(r'[Hh][Kk]\d{4,5}', q):
            return True
        # 美股：1-6 位字母（可含 . 后缀如 BRK.A）
        if re.fullmatch(r'[A-Za-z]{1,6}(\.[A-Za-z]{1,2})?', q):
            return True
        return False

    def _lookup_by_code(self, code: str) -> List[Dict[str, Any]]:
        """通过代码直接查行情获取名称"""
        try:
            from data_provider.base import DataFetcherManager
            manager = DataFetcherManager()
            name = manager.get_stock_name(code)
            if name:
                return [{"stock_code": code.upper(), "stock_name": name, "market": self._guess_market(code)}]
            # 若 get_stock_name 返回 None，尝试通过行情
            quote = manager.get_realtime_quote(code)
            if quote:
                return [{
                    "stock_code": getattr(quote, "code", code.upper()),
                    "stock_name": getattr(quote, "name", code.upper()),
                    "market": self._guess_market(code),
                }]
        except Exception as e:
            logger.warning(f"[WatchlistService] 通过代码查询失败: {code} {e}")
        return []

    def _search_by_name(self, name_query: str) -> List[Dict[str, Any]]:
        """在 A 股代码名称列表中按名称模糊匹配"""
        try:
            import akshare as ak
            df = ak.stock_info_a_code_name()
            # 列名: code, name
            if df is None or df.empty:
                return []
            # 标准化列名
            if 'stock_code' in df.columns:
                df = df.rename(columns={'stock_code': 'code', 'stock_name': 'name'})
            mask = df['name'].str.contains(name_query, na=False, case=False)
            matched = df[mask].head(10)
            results = []
            for _, row in matched.iterrows():
                results.append({
                    "stock_code": str(row['code']),
                    "stock_name": str(row['name']),
                    "market": "A",
                })
            return results
        except Exception as e:
            logger.warning(f"[WatchlistService] 名称搜索失败: {name_query} {e}")
            return []

    @staticmethod
    def _guess_market(code: str) -> str:
        upper = code.upper()
        if upper.startswith('HK') or re.fullmatch(r'0\d{4}', code):
            return "HK"
        if re.fullmatch(r'[A-Za-z]{1,6}(\.[A-Za-z]{1,2})?', code):
            return "US"
        return "A"

    # ── 自选股 CRUD ───────────────────────────────────────────────────────

    def _ensure_default_user(self, db: Session) -> int:
        """确保默认用户存在，返回 user_id"""
        from sqlalchemy import select
        user = db.execute(
            select(User).where(User.id == _DEFAULT_USER_ID)
        ).scalar_one_or_none()

        if user is None:
            user = User(
                id=_DEFAULT_USER_ID,
                username=_DEFAULT_USERNAME,
                email=f"{_DEFAULT_USERNAME}@local",
                password_hash="",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        return user.id

    def list_stocks(self, db: Session) -> List[Dict[str, Any]]:
        """列出全部自选股"""
        user_id = self._ensure_default_user(db)
        rows = db.execute(
            select(UserStock)
            .where(UserStock.user_id == user_id)
            .order_by(UserStock.created_at.desc())
        ).scalars().all()

        return [
            {
                "id": r.id,
                "stock_code": r.stock_code,
                "stock_name": r.stock_name if hasattr(r, 'stock_name') else None,
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }
            for r in rows
        ]

    def add_stock(self, db: Session, stock_code: str, stock_name: Optional[str] = None) -> Dict[str, Any]:
        """添加自选股，已存在则直接返回"""
        from data_provider.base import normalize_stock_code
        stock_code = normalize_stock_code(stock_code.strip())

        user_id = self._ensure_default_user(db)

        # 查重
        existing = db.execute(
            select(UserStock).where(
                UserStock.user_id == user_id,
                UserStock.stock_code == stock_code,
            )
        ).scalar_one_or_none()

        if existing:
            return {
                "id": existing.id,
                "stock_code": existing.stock_code,
                "stock_name": existing.stock_name if hasattr(existing, 'stock_name') else stock_name,
                "created_at": existing.created_at.isoformat() if existing.created_at else "",
            }

        record = UserStock(
            user_id=user_id,
            stock_code=stock_code,
        )
        # 若 UserStock 有 stock_name 列则写入（兼容）
        if hasattr(record, 'stock_name') and stock_name:
            record.stock_name = stock_name

        db.add(record)
        db.commit()
        db.refresh(record)

        return {
            "id": record.id,
            "stock_code": record.stock_code,
            "stock_name": stock_name,
            "created_at": record.created_at.isoformat() if record.created_at else "",
        }

    def remove_stock(self, db: Session, stock_id: int) -> bool:
        """删除自选股，返回是否成功"""
        user_id = self._ensure_default_user(db)
        row = db.execute(
            select(UserStock).where(
                UserStock.id == stock_id,
                UserStock.user_id == user_id,
            )
        ).scalar_one_or_none()

        if row is None:
            return False

        db.delete(row)
        db.commit()
        return True
