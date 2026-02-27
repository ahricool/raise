# -*- coding: utf-8 -*-
"""System configuration endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from api.deps import get_system_config_service
from api.v1.schemas.common import ErrorResponse
from api.v1.schemas.system_config import (
    SystemConfigConflictResponse,
    SystemConfigResponse,
    SystemConfigSchemaResponse,
    SystemConfigValidationErrorResponse,
    UpdateSystemConfigRequest,
    UpdateSystemConfigResponse,
    ValidateSystemConfigRequest,
    ValidateSystemConfigResponse,
)
from src.services.system_config_service import ConfigConflictError, ConfigValidationError, SystemConfigService
from src.services.schedule_service import SchedulerService

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_scheduler(request: Request) -> SchedulerService:
    svc = getattr(request.app.state, "scheduler_service", None)
    if svc is None:
        raise HTTPException(status_code=503, detail={"error": "scheduler_unavailable", "message": "调度器未就绪"})
    return svc


@router.get(
    "/config",
    response_model=SystemConfigResponse,
    responses={
        200: {"description": "Configuration loaded"},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Get system configuration",
    description="Read current configuration from .env and return raw values.",
)
def get_system_config(
    include_schema: bool = Query(True, description="Whether to include schema metadata"),
    service: SystemConfigService = Depends(get_system_config_service),
) -> SystemConfigResponse:
    """Load and return current system configuration."""
    try:
        payload = service.get_config(include_schema=include_schema)
        return SystemConfigResponse.model_validate(payload)
    except Exception as exc:
        logger.error("Failed to load system configuration: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "Failed to load system configuration",
            },
        )


@router.put(
    "/config",
    response_model=UpdateSystemConfigResponse,
    responses={
        200: {"description": "Configuration updated"},
        400: {"description": "Validation failed", "model": SystemConfigValidationErrorResponse},
        409: {"description": "Version conflict", "model": SystemConfigConflictResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Update system configuration",
    description="Update key-value pairs in .env. Mask token preserves existing secret values.",
)
def update_system_config(
    request: UpdateSystemConfigRequest,
    service: SystemConfigService = Depends(get_system_config_service),
) -> UpdateSystemConfigResponse:
    """Validate and persist system configuration updates."""
    try:
        payload = service.update(
            config_version=request.config_version,
            items=[item.model_dump() for item in request.items],
            mask_token=request.mask_token,
            reload_now=request.reload_now,
        )
        return UpdateSystemConfigResponse.model_validate(payload)
    except ConfigValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "validation_failed",
                "message": "System configuration validation failed",
                "issues": exc.issues,
            },
        )
    except ConfigConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "config_version_conflict",
                "message": "Configuration has changed, please reload and retry",
                "current_config_version": exc.current_version,
            },
        )
    except Exception as exc:
        logger.error("Failed to update system configuration: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "Failed to update system configuration",
            },
        )


@router.post(
    "/config/validate",
    response_model=ValidateSystemConfigResponse,
    responses={
        200: {"description": "Validation completed"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Validate system configuration",
    description="Validate submitted configuration values without writing to .env.",
)
def validate_system_config(
    request: ValidateSystemConfigRequest,
    service: SystemConfigService = Depends(get_system_config_service),
) -> ValidateSystemConfigResponse:
    """Run pre-save validation only."""
    try:
        payload = service.validate(items=[item.model_dump() for item in request.items])
        return ValidateSystemConfigResponse.model_validate(payload)
    except Exception as exc:
        logger.error("Failed to validate system configuration: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "Failed to validate system configuration",
            },
        )


@router.get(
    "/config/schema",
    response_model=SystemConfigSchemaResponse,
    responses={
        200: {"description": "Schema loaded"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Get system configuration schema",
    description="Return categorized field metadata used for dynamic settings form rendering.",
)
def get_system_config_schema(
    service: SystemConfigService = Depends(get_system_config_service),
) -> SystemConfigSchemaResponse:
    """Return schema metadata for system configuration fields."""
    try:
        payload = service.get_schema()
        return SystemConfigSchemaResponse.model_validate(payload)
    except Exception as exc:
        logger.error("Failed to load system configuration schema: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "Failed to load system configuration schema",
            },
        )


# ── 定时任务调度器 ─────────────────────────────────────────────────────────


@router.get(
    "/scheduler/status",
    summary="查询定时任务状态",
    description="返回调度器运行状态、下次执行时间、上次执行时间等信息。",
    tags=["Scheduler"],
)
def get_scheduler_status(request: Request) -> dict:
    """返回调度器当前状态"""
    return _get_scheduler(request).get_status()


@router.get(
    "/scheduler/trigger",
    summary="手动立即触发一次自选股分析",
    description="不影响正常定时计划，立即对自选股列表中的所有股票提交分析任务。",
    tags=["Scheduler"],
)
async def trigger_scheduler(request: Request) -> dict:
    """手动触发自选股分析"""
    scheduler = _get_scheduler(request)
    try:
        result = await scheduler.trigger_now()
        return result
    except Exception as exc:
        logger.error("手动触发调度任务失败: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "trigger_failed", "message": str(exc)},
        )


@router.get(
    "/scheduler/trigger/push",
    summary="手动触发 Telegram 推送",
    description="立即触发一次自选股 Telegram 推送。mode: morning（晨间）/ noon（午间）/ evening（收盘）。",
    tags=["Scheduler"],
)
async def trigger_push(request: Request, mode: str = Query(..., description="推送模式: morning / noon / evening")) -> dict:
    """手动触发 Telegram 推送"""
    scheduler = _get_scheduler(request)
    try:
        result = await scheduler.trigger_push(mode)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"error": "invalid_mode", "message": str(exc)})
    except Exception as exc:
        logger.error("手动触发推送任务失败: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "trigger_failed", "message": str(exc)})


@router.put(
    "/scheduler/reschedule",
    summary="动态更新定时时间",
    description="在不重启应用的情况下更新每日分析执行时间（格式 HH:MM）。",
    tags=["Scheduler"],
)
def reschedule(request: Request, schedule_time: str = Query(..., description="新的执行时间，格式 HH:MM，如 18:30")) -> dict:
    """更新定时执行时间"""
    import re
    if not re.fullmatch(r"\d{1,2}:\d{2}", schedule_time):
        raise HTTPException(status_code=422, detail={"error": "invalid_time", "message": "格式应为 HH:MM，如 18:30"})
    scheduler = _get_scheduler(request)
    scheduler.reschedule(schedule_time)
    return {"success": True, "schedule_time": schedule_time}
