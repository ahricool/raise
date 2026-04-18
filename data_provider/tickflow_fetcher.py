# -*- coding: utf-8 -*-
"""
TickFlow A股行情增强数据源
提供更精细的A股实时行情辅助数据
"""

from typing import Optional, Dict, Any

from loguru import logger

from data_provider.base import DataFetchError


class TickFlowFetcher:
    """TickFlow 数据获取器（A股行情增强，辅助数据源）"""

    BASE_URL = "https://api.tickflow.cn/v1"

    def __init__(self, api_key: Optional[str] = None):
        from src.config import get_config
        config = get_config()
        self._api_key = api_key or getattr(config, 'tickflow_api_key', None)
        self._available = bool(self._api_key)
        if self._available:
            logger.info("TickFlow 数据源已初始化")

    @property
    def is_available(self) -> bool:
        return self._available

    @property
    def name(self) -> str:
        return "TickFlowFetcher"

    def get_realtime_quote(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """获取 TickFlow 实时行情辅助数据"""
        if not self._available:
            return None
        try:
            import requests
            headers = {"Authorization": f"Bearer {self._api_key}"}
            resp = requests.get(
                f"{self.BASE_URL}/quote/{stock_code}",
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("data")
        except Exception as e:
            logger.debug(f"TickFlow 获取 {stock_code} 行情失败: {e}")
            return None

    def get_market_sentiment(self) -> Optional[Dict[str, Any]]:
        """获取市场情绪指标"""
        if not self._available:
            return None
        try:
            import requests
            headers = {"Authorization": f"Bearer {self._api_key}"}
            resp = requests.get(
                f"{self.BASE_URL}/market/sentiment",
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("data")
        except Exception as e:
            logger.debug(f"TickFlow 获取市场情绪失败: {e}")
            return None
