# -*- coding: utf-8 -*-
"""
自选股接口

GET  /api/v1/watchlist               → 列出自选股
GET  /api/v1/watchlist/search?q=...  → 按代码/名称搜索股票
POST /api/v1/watchlist               → 添加自选股
DELETE /api/v1/watchlist/{id}        → 删除自选股
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.deps import get_db
from api.v1.schemas.watchlist import (
    WatchlistResponse,
    WatchlistItem,
    StockSearchResponse,
    StockSearchResult,
    AddWatchlistRequest,
)
from src.services.watchlist_service import WatchlistService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "",
    response_model=WatchlistResponse,
    summary="获取自选股列表",
)
def list_watchlist(db: Session = Depends(get_db)) -> WatchlistResponse:
    svc = WatchlistService()
    items = svc.list_stocks(db)
    return WatchlistResponse(
        items=[WatchlistItem(**i) for i in items],
        total=len(items),
    )


@router.get(
    "/search",
    response_model=StockSearchResponse,
    summary="搜索股票（按代码或名称）",
)
def search_stock(
    q: str = Query(..., min_length=1, description="股票代码或名称关键词"),
) -> StockSearchResponse:
    svc = WatchlistService()
    results = svc.search_stock(q)
    return StockSearchResponse(
        query=q,
        results=[StockSearchResult(**r) for r in results],
    )


@router.post(
    "",
    response_model=WatchlistItem,
    summary="添加自选股",
)
def add_watchlist(
    body: AddWatchlistRequest,
    db: Session = Depends(get_db),
) -> WatchlistItem:
    if not body.stock_code or not body.stock_code.strip():
        raise HTTPException(status_code=422, detail={"error": "invalid_code", "message": "股票代码不能为空"})

    svc = WatchlistService()
    try:
        item = svc.add_stock(db, body.stock_code, body.stock_name)
        return WatchlistItem(**item)
    except Exception as e:
        logger.error(f"添加自选股失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "internal_error", "message": str(e)})


@router.delete(
    "/{stock_id}",
    summary="删除自选股",
)
def remove_watchlist(
    stock_id: int,
    db: Session = Depends(get_db),
) -> dict:
    svc = WatchlistService()
    ok = svc.remove_stock(db, stock_id)
    if not ok:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "自选股记录不存在"})
    return {"success": True}
