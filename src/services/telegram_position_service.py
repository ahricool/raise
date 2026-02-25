# -*- coding: utf-8 -*-
"""Telegram position webhook processing service."""

import json
import logging
import re
from typing import Any, Dict, List, Optional

import requests
from json_repair import repair_json
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config import get_config
from src.storage import TelegramPosition

logger = logging.getLogger(__name__)


class TelegramPositionService:
    """Handle Telegram callbacks and persist parsed positions."""

    def __init__(self) -> None:
        self._config = get_config()
        self._bot_token = (self._config.telegram_bot_token or "").strip()

    def process_update(self, db: Session, update: Dict[str, Any]) -> Dict[str, Any]:
        message = update.get("message") or update.get("edited_message") or {}
        if not message:
            return {"ok": True, "message": "no_message"}

        chat = message.get("chat") or {}
        from_user = message.get("from") or {}
        chat_id = str(chat.get("id") or "")
        user_id = str(from_user.get("id") or "")
        message_id = message.get("message_id")

        if not chat_id or not user_id:
            return {"ok": True, "message": "missing_chat_or_user"}

        text = (message.get("text") or "").strip()
        caption = (message.get("caption") or "").strip()
        photos = message.get("photo") or []
        image_file_id = photos[-1].get("file_id") if photos else None
        content = text or caption

        if self._is_position_list_command(content):
            reply_text = self._render_positions(db, user_id, chat_id)
            self._send_message(chat_id, reply_text, reply_to_message_id=message_id)
            return {"ok": True, "message": "listed"}

        delete_codes = self._parse_delete_command(content)
        if delete_codes:
            deleted_count = self._delete_positions(db, user_id, chat_id, delete_codes)
            reply_text = f"✅ 已删除 {deleted_count} 条持仓记录"
            self._send_message(chat_id, reply_text, reply_to_message_id=message_id)
            return {"ok": True, "message": "deleted", "deleted": deleted_count}

        if not content and not image_file_id:
            return {"ok": True, "message": "empty_content"}

        parsed = self._parse_positions_with_llm(content=content, image_file_id=image_file_id)
        if not parsed:
            reply_text = (
                "❌ 无法识别持仓信息，请发送文字或在图片消息中带上说明。\n"
                "示例：600519 200股 成本价 1820"
            )
            self._send_message(chat_id, reply_text, reply_to_message_id=message_id)
            return {"ok": False, "message": "parse_failed"}

        intent = (parsed.get("intent") or "upsert").lower().strip()
        if intent == "delete":
            codes = [c for c in (parsed.get("delete_codes") or []) if c]
            deleted_count = self._delete_positions(db, user_id, chat_id, codes)
            reply_text = f"✅ 已删除 {deleted_count} 条持仓记录"
            self._send_message(chat_id, reply_text, reply_to_message_id=message_id)
            return {"ok": True, "message": "deleted", "deleted": deleted_count}

        rows = parsed.get("positions") or []
        if not rows:
            self._send_message(chat_id, "❌ 未识别到有效持仓条目", reply_to_message_id=message_id)
            return {"ok": False, "message": "no_positions"}

        upserted = self._upsert_positions(db, user_id, chat_id, rows, content, image_file_id)
        positions_preview = self._render_positions(db, user_id, chat_id)
        self._send_message(
            chat_id,
            f"✅ 已更新 {upserted} 条持仓\n\n{positions_preview}",
            reply_to_message_id=message_id,
        )
        return {"ok": True, "message": "upserted", "count": upserted}

    @staticmethod
    def _is_position_list_command(content: str) -> bool:
        text = (content or "").strip().lower()
        if not text:
            return False
        return text in {"/positions", "/position", "持仓", "查看持仓", "我的持仓"}

    @staticmethod
    def _parse_delete_command(content: str) -> List[str]:
        text = (content or "").strip()
        if not text:
            return []

        lowered = text.lower()
        if lowered.startswith("/position_delete") or lowered.startswith("/delete_position"):
            args = text.split()[1:]
            return [TelegramPositionService._normalize_code(arg) for arg in args if TelegramPositionService._normalize_code(arg)]

        if text.startswith("删除持仓") or text.startswith("删除"):
            candidates = re.findall(r"[A-Za-z]{1,6}(?:\.[A-Za-z]{1,2})?|\d{5,6}", text)
            return [TelegramPositionService._normalize_code(item) for item in candidates if TelegramPositionService._normalize_code(item)]

        return []

    @staticmethod
    def _normalize_code(value: str) -> str:
        text = (value or "").strip().upper()
        if re.fullmatch(r"\d{5,6}", text):
            return text
        if re.fullmatch(r"[A-Z]{1,6}(?:\.[A-Z]{1,2})?", text):
            return text
        return ""

    def _upsert_positions(
        self,
        db: Session,
        user_id: str,
        chat_id: str,
        rows: List[Dict[str, Any]],
        raw_text: str,
        image_file_id: Optional[str],
    ) -> int:
        upserted = 0
        for item in rows:
            stock_code = self._normalize_code(str(item.get("stock_code") or ""))
            if not stock_code:
                continue

            existing = db.execute(
                select(TelegramPosition).where(
                    TelegramPosition.platform_user_id == user_id,
                    TelegramPosition.platform_chat_id == chat_id,
                    TelegramPosition.stock_code == stock_code,
                )
            ).scalar_one_or_none()

            if existing:
                existing.stock_name = item.get("stock_name") or existing.stock_name
                existing.quantity = self._to_float(item.get("quantity"), existing.quantity)
                existing.cost_price = self._to_float(item.get("cost_price"), existing.cost_price)
                existing.note = item.get("note") or existing.note
                existing.source_type = "image" if image_file_id else "text"
                existing.raw_text = raw_text or existing.raw_text
                existing.image_file_id = image_file_id or existing.image_file_id
            else:
                record = TelegramPosition(
                    platform_user_id=user_id,
                    platform_chat_id=chat_id,
                    stock_code=stock_code,
                    stock_name=item.get("stock_name"),
                    quantity=self._to_float(item.get("quantity")),
                    cost_price=self._to_float(item.get("cost_price")),
                    note=item.get("note"),
                    source_type="image" if image_file_id else "text",
                    raw_text=raw_text,
                    image_file_id=image_file_id,
                )
                db.add(record)

            upserted += 1

        if upserted > 0:
            db.commit()
        return upserted

    def _delete_positions(self, db: Session, user_id: str, chat_id: str, stock_codes: List[str]) -> int:
        if not stock_codes:
            return 0

        deleted = 0
        code_set = set(stock_codes)
        rows = db.execute(
            select(TelegramPosition).where(
                TelegramPosition.platform_user_id == user_id,
                TelegramPosition.platform_chat_id == chat_id,
            )
        ).scalars().all()

        for row in rows:
            if row.stock_code in code_set:
                db.delete(row)
                deleted += 1

        if deleted > 0:
            db.commit()
        return deleted

    def _render_positions(self, db: Session, user_id: str, chat_id: str) -> str:
        rows = db.execute(
            select(TelegramPosition)
            .where(
                TelegramPosition.platform_user_id == user_id,
                TelegramPosition.platform_chat_id == chat_id,
            )
            .order_by(TelegramPosition.updated_at.desc())
        ).scalars().all()

        if not rows:
            return "📭 当前没有持仓记录"

        lines = ["📊 当前持仓："]
        for row in rows:
            qty = "-" if row.quantity is None else f"{row.quantity:g}"
            cost = "-" if row.cost_price is None else f"{row.cost_price:g}"
            name = f" {row.stock_name}" if row.stock_name else ""
            lines.append(f"• {row.stock_code}{name} | 数量: {qty} | 成本: {cost}")

        lines.append("\n删除示例：/position_delete 600519")
        return "\n".join(lines)

    def _parse_positions_with_llm(self, content: str, image_file_id: Optional[str]) -> Optional[Dict[str, Any]]:
        prompt = (
            "You are a parser for stock positions. "
            "Read user content and return strict JSON only. "
            "JSON schema: {\"intent\":\"upsert|delete|unknown\","
            "\"positions\":[{\"stock_code\":\"\",\"stock_name\":\"\",\"quantity\":0,\"cost_price\":0,\"note\":\"\"}],"
            "\"delete_codes\":[\"\"],\"summary\":\"\"}. "
            "If data is missing, keep null/empty instead of guessing."
        )

        llm_text = None
        image_bytes = self._download_telegram_photo(image_file_id) if image_file_id else None

        if self._config.gemini_api_key:
            llm_text = self._call_gemini(prompt=prompt, content=content, image_bytes=image_bytes)

        if not llm_text and self._config.openai_api_key:
            llm_text = self._call_openai(prompt=prompt, content=content)

        if not llm_text:
            return self._fallback_parse(content)

        data = self._safe_load_json(llm_text)
        if not isinstance(data, dict):
            return self._fallback_parse(content)

        return data

    def _call_gemini(self, prompt: str, content: str, image_bytes: Optional[bytes] = None) -> Optional[str]:
        try:
            import google.generativeai as genai

            model_name = self._config.gemini_model or "gemini-2.5-flash"
            genai.configure(api_key=self._config.gemini_api_key)
            model = genai.GenerativeModel(model_name)

            payload: List[Any] = [f"{prompt}\n\nUser content:\n{content or ''}"]
            if image_bytes:
                payload.append({"mime_type": "image/jpeg", "data": image_bytes})

            response = model.generate_content(payload)
            text = getattr(response, "text", None)
            return text.strip() if text else None
        except Exception as e:
            logger.warning("[TelegramPosition] Gemini parse failed: %s", e)
            return None

    def _call_openai(self, prompt: str, content: str) -> Optional[str]:
        try:
            from openai import OpenAI

            client_kwargs: Dict[str, Any] = {"api_key": self._config.openai_api_key}
            if self._config.openai_base_url:
                client_kwargs["base_url"] = self._config.openai_base_url

            client = OpenAI(**client_kwargs)
            completion = client.chat.completions.create(
                model=self._config.openai_model or "gpt-4o-mini",
                temperature=0,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content or ""},
                ],
            )
            text = completion.choices[0].message.content if completion.choices else None
            return text.strip() if text else None
        except Exception as e:
            logger.warning("[TelegramPosition] OpenAI parse failed: %s", e)
            return None

    def _download_telegram_photo(self, file_id: Optional[str]) -> Optional[bytes]:
        if not file_id or not self._bot_token:
            return None

        try:
            file_resp = requests.get(
                f"https://api.telegram.org/bot{self._bot_token}/getFile",
                params={"file_id": file_id},
                timeout=10,
            )
            payload = file_resp.json() if file_resp.ok else {}
            file_path = (((payload.get("result") or {}).get("file_path")) or "").strip()
            if not file_path:
                return None

            bin_resp = requests.get(
                f"https://api.telegram.org/file/bot{self._bot_token}/{file_path}",
                timeout=15,
            )
            if not bin_resp.ok:
                return None

            return bin_resp.content
        except Exception as e:
            logger.warning("[TelegramPosition] Download photo failed: %s", e)
            return None

    def _send_message(self, chat_id: str, text: str, reply_to_message_id: Optional[int] = None) -> None:
        if not self._bot_token or not chat_id or not text:
            return

        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
        }
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id

        try:
            requests.post(
                f"https://api.telegram.org/bot{self._bot_token}/sendMessage",
                json=payload,
                timeout=10,
            )
        except Exception as e:
            logger.warning("[TelegramPosition] sendMessage failed: %s", e)

    @staticmethod
    def _safe_load_json(text: str) -> Optional[Dict[str, Any]]:
        body = (text or "").strip()
        if not body:
            return None

        body = re.sub(r"^```(?:json)?", "", body, flags=re.IGNORECASE).strip()
        body = re.sub(r"```$", "", body).strip()

        try:
            return json.loads(body)
        except Exception:
            pass

        try:
            repaired = repair_json(body)
            return json.loads(repaired)
        except Exception:
            return None

    @staticmethod
    def _fallback_parse(content: str) -> Optional[Dict[str, Any]]:
        text = (content or "").strip()
        if not text:
            return None

        codes = re.findall(r"[A-Za-z]{1,6}(?:\.[A-Za-z]{1,2})?|\d{5,6}", text)
        if not codes:
            return None

        qty_match = re.search(r"(\d+(?:\.\d+)?)\s*(股|手|shares?)", text, flags=re.IGNORECASE)
        cost_match = re.search(r"(?:成本|成本价|cost|买入价)\s*[:：]?\s*(\d+(?:\.\d+)?)", text, flags=re.IGNORECASE)

        positions = []
        for code in codes[:5]:
            normalized = TelegramPositionService._normalize_code(code)
            if not normalized:
                continue
            positions.append(
                {
                    "stock_code": normalized,
                    "stock_name": "",
                    "quantity": float(qty_match.group(1)) if qty_match else None,
                    "cost_price": float(cost_match.group(1)) if cost_match else None,
                    "note": "",
                }
            )

        if not positions:
            return None

        return {
            "intent": "upsert",
            "positions": positions,
            "delete_codes": [],
            "summary": "fallback_parser",
        }

    @staticmethod
    def _to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
        if value is None:
            return default
        try:
            return float(value)
        except Exception:
            return default
