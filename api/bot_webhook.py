# -*- coding: utf-8 -*-
"""Bot webhook endpoints."""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from api.deps import get_db
from src.config import get_config
from src.services.telegram_position_service import TelegramPositionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bot", tags=["BotWebhook"])


@router.post("/telegram", summary="Telegram webhook callback")
async def telegram_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict:
    config = get_config()
    expected_secret = (getattr(config, "telegram_webhook_secret", None) or "").strip()
    if expected_secret and x_telegram_bot_api_secret_token != expected_secret:
        raise HTTPException(status_code=403, detail={"error": "invalid_secret"})

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail={"error": "invalid_json"})

    service = TelegramPositionService()

    try:
        result = service.process_update(db, payload)
        return {"ok": True, "result": result}
    except Exception as e:
        logger.error("[BotWebhook] telegram webhook failed: %s", e, exc_info=True)
        return {"ok": False, "error": str(e)[:200]}
