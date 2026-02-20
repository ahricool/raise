# -*- coding: utf-8 -*-
"""
自选股相关请求/响应模型
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class StockSearchResult(BaseModel):
    """股票搜索候选项"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    market: Optional[str] = Field(None, description="市场 (A/HK/US)")


class StockSearchResponse(BaseModel):
    """股票搜索结果"""
    results: List[StockSearchResult] = Field(default_factory=list)
    query: str = Field(..., description="原始搜索词")


class WatchlistItem(BaseModel):
    """自选股条目"""
    id: int = Field(..., description="记录 ID")
    stock_code: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    created_at: str = Field(..., description="添加时间")


class WatchlistResponse(BaseModel):
    """自选股列表响应"""
    items: List[WatchlistItem] = Field(default_factory=list)
    total: int = Field(0)


class AddWatchlistRequest(BaseModel):
    """添加自选股请求"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称（前端确认后传入）")
