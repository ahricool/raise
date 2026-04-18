# -*- coding: utf-8 -*-
"""
长桥 (LongBridge) 数据源
支持美股、港股实时行情和历史数据
修复了 yfinance 美股数据丢失问题的备用数据源
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any

import pandas as pd
from loguru import logger

from data_provider.base import BaseFetcher, DataFetchError, STANDARD_COLUMNS


class LongBridgeFetcher(BaseFetcher):
    """长桥数据获取器 — 美股/港股历史及实时行情"""

    name = "LongBridgeFetcher"
    priority = 3

    def __init__(
        self,
        app_key: Optional[str] = None,
        app_secret: Optional[str] = None,
        access_token: Optional[str] = None,
    ):
        """内部辅助逻辑：__init__（模块：longbridge-fetcher）。"""
        from src.config import get_config
        config = get_config()
        self._app_key = app_key or getattr(config, 'longbridge_app_key', None)
        self._app_secret = app_secret or getattr(config, 'longbridge_app_secret', None)
        self._access_token = access_token or getattr(config, 'longbridge_access_token', None)
        self._ctx = None
        self._available = bool(self._app_key and self._app_secret and self._access_token)
        if self._available:
            self._init_client()

    def _init_client(self):
        """内部辅助逻辑：_init_client（模块：longbridge-fetcher）。"""
        try:
            from longbridge.openapi import Config, QuoteContext
            lb_config = Config(
                app_key=self._app_key,
                app_secret=self._app_secret,
                access_token=self._access_token,
            )
            self._ctx = QuoteContext(lb_config)
            logger.info("LongBridge 数据源初始化成功")
        except ImportError:
            logger.warning("longbridge SDK 未安装，请运行: pip install longbridge")
            self._available = False
        except Exception as e:
            logger.warning(f"LongBridge 初始化失败: {e}")
            self._available = False

    @property
    def is_available(self) -> bool:
        """业务流程函数：is_available（模块：longbridge-fetcher）。"""
        return self._available and self._ctx is not None

    def get_daily_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """业务流程函数：get_daily_data（模块：longbridge-fetcher）。"""
        if not self.is_available:
            raise DataFetchError("LongBridge 未初始化")
        try:
            from longbridge.openapi import Period, AdjustType
            symbol = self._to_lb_symbol(stock_code)
            start_dt = datetime.strptime(start_date.replace('-', ''), "%Y%m%d")
            end_dt = datetime.strptime(end_date.replace('-', ''), "%Y%m%d")
            candlesticks = self._ctx.history_candlesticks_by_date(
                symbol, Period.Day, AdjustType.ForwardAdj, start_dt, end_dt
            )
            if not candlesticks:
                raise DataFetchError(f"LongBridge {stock_code} 无历史数据")
            rows = [{
                'date': pd.Timestamp(c.timestamp),
                'open': float(c.open),
                'high': float(c.high),
                'low': float(c.low),
                'close': float(c.close),
                'volume': float(c.volume),
                'amount': float(c.turnover),
            } for c in candlesticks]
            df = pd.DataFrame(rows).sort_values('date').reset_index(drop=True)
            df['code'] = stock_code
            keep_cols = ['code'] + [c for c in STANDARD_COLUMNS if c in df.columns]
            return df[keep_cols]
        except DataFetchError:
            raise
        except Exception as e:
            raise DataFetchError(f"LongBridge 获取 {stock_code} 历史数据失败: {e}") from e

    def get_realtime_quote(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """业务流程函数：get_realtime_quote（模块：longbridge-fetcher）。"""
        if not self.is_available:
            return None
        try:
            symbol = self._to_lb_symbol(stock_code)
            quotes = self._ctx.quote([symbol])
            if not quotes:
                return None
            q = quotes[0]
            return {
                'price': float(q.last_done),
                'change_pct': float(q.change_rate) * 100 if hasattr(q, 'change_rate') else None,
                'volume': float(q.volume) if hasattr(q, 'volume') else None,
                'source': 'longbridge',
            }
        except Exception as e:
            logger.debug(f"LongBridge 获取 {stock_code} 实时行情失败: {e}")
            return None

    def _to_lb_symbol(self, stock_code: str) -> str:
        """将股票代码转换为长桥 symbol 格式"""
        code = stock_code.strip().upper()
        if '.' in code and not code.endswith('.SH') and not code.endswith('.SZ'):
            return code
        # 美股：纯字母
        if re.match(r'^[A-Z]{1,5}$', code):
            return f"{code}.US"
        # 港股：5位数字
        bare = re.sub(r'\.(SH|SZ|BJ|SS|HK)$', '', code)
        if re.match(r'^\d{5}$', bare) or code.startswith('HK'):
            digits = re.sub(r'\D', '', bare)[-5:].zfill(5)
            return f"{digits}.HK"
        return code
