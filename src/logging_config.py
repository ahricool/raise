# -*- coding: utf-8 -*-
"""
===================================
日志配置模块 - 统一的日志系统初始化
===================================

职责：
1. 提供统一的日志格式和配置常量
2. 支持控制台 + 文件（常规/调试）三层日志输出
3. 自动降低第三方库日志级别
4. 将标准库 logging 输出桥接到 loguru（InterceptHandler）
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from loguru import logger

# ============================================================
# 日志格式常量
# ============================================================

DEFAULT_QUIET_LOGGERS = [
    "urllib3",
    "sqlalchemy",
    "google",
    "httpx",
]

CONSOLE_FMT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level:<8}</level> | "
    "<cyan>{name}</cyan> | "
    "<level>{message}</level>"
)
FILE_FMT = "{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name} | {message}"


class InterceptHandler(logging.Handler):
    """Forward stdlib logging records into loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def is_loguru_debug_enabled() -> bool:
    """True if loguru's minimum level allows DEBUG messages (for error detail exposure)."""
    try:
        return logger._core.min_level <= logger.level("DEBUG").no
    except (ValueError, AttributeError):
        return False


def configure_stderr_logging(level: str = "INFO", fmt: Optional[str] = None) -> None:
    """
    Minimal loguru setup for CLI / test entrypoints (stderr only).

    Args:
        level: Loguru level name (e.g. INFO, DEBUG).
        fmt: Optional format string; default matches former script-style output.
    """
    logger.remove()
    fmt = fmt or "{time:HH:mm:ss} | {level:<8} | {message}"
    logger.add(sys.stderr, level=level, format=fmt, colorize=True)


def setup_logging(
    log_prefix: str = "app",
    log_dir: str = "./logs",
    console_level: Optional[int] = None,
    debug: bool = False,
    extra_quiet_loggers: Optional[List[str]] = None,
) -> None:
    """
    统一的日志系统初始化

    配置三层日志输出：
    1. 控制台：根据 debug 参数或 console_level 设置级别
    2. 常规日志文件：INFO 级别，10MB 轮转，保留 5 个备份
    3. 调试日志文件：DEBUG 级别，50MB 轮转，保留 3 个备份

    Args:
        log_prefix: 日志文件名前缀（如 "api_server" -> api_server_20240101.log）
        log_dir: 日志文件目录，默认 ./logs
        console_level: 控制台日志级别（可选，优先于 debug 参数），使用与 logging 相同的数值
        debug: 是否启用调试模式（控制台输出 DEBUG 级别）
        extra_quiet_loggers: 额外需要降低日志级别的第三方库列表
    """
    if console_level is not None:
        console_lvl = console_level
    else:
        console_lvl = 10 if debug else 20

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    today_str = datetime.now().strftime("%Y%m%d")
    log_file = log_path / f"{log_prefix}_{today_str}.log"
    debug_log_file = log_path / f"{log_prefix}_debug_{today_str}.log"

    logger.remove()

    logger.add(
        sys.stdout,
        level=console_lvl,
        format=CONSOLE_FMT,
        colorize=True,
    )

    logger.add(
        str(log_file),
        rotation=10 * 1024 * 1024,
        retention=5,
        level="INFO",
        encoding="utf-8",
        format=FILE_FMT,
    )

    logger.add(
        str(debug_log_file),
        rotation=50 * 1024 * 1024,
        retention=3,
        level="DEBUG",
        encoding="utf-8",
        format=FILE_FMT,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    quiet_loggers = DEFAULT_QUIET_LOGGERS.copy()
    if extra_quiet_loggers:
        quiet_loggers.extend(extra_quiet_loggers)

    for logger_name in quiet_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    logger.info(f"日志系统初始化完成，日志目录: {log_path.absolute()}")
    logger.info(f"常规日志: {log_file}")
    logger.info(f"调试日志: {debug_log_file}")
