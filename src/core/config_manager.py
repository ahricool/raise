# -*- coding: utf-8 -*-
"""
`.env` 配置管理器（供 WebUI 等热更新配置）

要点：
- 读：用 `dotenv_values` 解析，与 `src.config.setup_env` 行为一致
- 写：按 key 定位「最后一处」赋值行并原地替换，新 key 则追加；整文件重写后 `fsync`，降低半写风险
- 乐观版本：`get_config_version` 用 mtime + 内容哈希，前端可用 If-Match 式防并发覆盖
- 敏感键：`apply_updates` 遇到占位符（mask_token）且当前已有值则跳过写入，避免把真密钥覆盖成星号
"""

from __future__ import annotations

import hashlib
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

from dotenv import dotenv_values

_ASSIGNMENT_PATTERN = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")


class ConfigManager:
    """封装 `.env` 的线程安全读写与版本查询。"""

    def __init__(self, env_path: Optional[Path] = None):
        self._env_path = env_path or self._resolve_env_path()
        self._lock = threading.RLock()  # 与 Web 多请求并发写同一文件互斥

    @property
    def env_path(self) -> Path:
        """Return active `.env` path."""
        return self._env_path

    def read_config_map(self) -> Dict[str, str]:
        """读取 `.env` 为 key→value 字典（键统一大写由调用方在 apply_updates 中处理）。"""
        if not self._env_path.exists():
            return {}

        values = dotenv_values(self._env_path)
        return {
            str(key): "" if value is None else str(value)
            for key, value in values.items()
            if key is not None
        }

    def get_config_version(self) -> str:
        """返回可比较的版本串：修改时间与内容任一变化即变。"""
        if not self._env_path.exists():
            return "missing:0"

        content = self._env_path.read_bytes()
        file_stat = self._env_path.stat()
        content_hash = hashlib.sha256(content).hexdigest()
        return f"{file_stat.st_mtime_ns}:{content_hash}"

    def get_updated_at(self) -> Optional[str]:
        """文件 mtime 转 UTC ISO8601，便于前端展示「上次保存时间」。"""
        if not self._env_path.exists():
            return None

        file_stat = self._env_path.stat()
        updated_at = datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc)
        return updated_at.isoformat()

    def apply_updates(
        self,
        updates: Iterable[Tuple[str, str]],
        sensitive_keys: Set[str],
        mask_token: str,
    ) -> Tuple[List[str], List[str], str]:
        """
        合并更新并写回文件。

        Returns:
            (实际变更的 key 列表, 因掩码占位而跳过的 key 列表, 新版本号)
        """
        with self._lock:
            current_values = self.read_config_map()
            mutable_updates: Dict[str, str] = {}
            skipped_masked: List[str] = []

            for key, value in updates:
                key_upper = key.upper()
                current_value = current_values.get(key_upper)

                if key_upper in sensitive_keys and value == mask_token:
                    if current_value not in (None, ""):
                        skipped_masked.append(key_upper)
                    continue

                if current_value == value:
                    continue

                mutable_updates[key_upper] = value

            if mutable_updates:
                self._atomic_upsert(mutable_updates)

            return list(mutable_updates.keys()), skipped_masked, self.get_config_version()

    def _atomic_upsert(self, updates: Dict[str, str]) -> None:
        """整文件重写 + fsync；同一 key 多行时只改最后一次出现（与常见 .env 编辑习惯一致）。"""
        lines = self._read_lines()
        key_to_index = self._find_last_key_indexes(lines)

        for key, value in updates.items():
            line_value = value.replace("\n", "")
            new_line = f"{key}={line_value}"
            if key in key_to_index:
                lines[key_to_index[key]] = new_line
            else:
                lines.append(new_line)

        if not self._env_path.parent.exists():
            self._env_path.parent.mkdir(parents=True, exist_ok=True)

        content = "\n".join(lines)
        if content and not content.endswith("\n"):
            content += "\n"

        with self._env_path.open("w", encoding="utf-8", newline="\n") as file_obj:
            file_obj.write(content)
            file_obj.flush()
            os.fsync(file_obj.fileno())

    def _read_lines(self) -> List[str]:
        if not self._env_path.exists():
            return []
        return self._env_path.read_text(encoding="utf-8").splitlines()

    @staticmethod
    def _find_last_key_indexes(lines: List[str]) -> Dict[str, int]:
        # 重复定义同一 key 时保留较大行号，使后续替换落在「最后一处」
        key_to_index: Dict[str, int] = {}
        for index, raw_line in enumerate(lines):
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            matched = _ASSIGNMENT_PATTERN.match(raw_line)
            if not matched:
                continue

            key_to_index[matched.group(1).upper()] = index

        return key_to_index

    @staticmethod
    def _resolve_env_path() -> Path:
        env_file = os.getenv("ENV_FILE")
        if env_file:
            return Path(env_file).resolve()

        return (Path(__file__).resolve().parent.parent.parent / ".env").resolve()
