# -*- coding: utf-8 -*-
"""
多智能体 LLM 客户端

封装 raise 现有的 Gemini/OpenAI 调用逻辑，供各 Agent 节点直接使用。
不引入 LangChain LLM 包装，直接复用已有的重试/降级策略。
"""

import time
from typing import Optional
from loguru import logger

from src.config import get_config


class RaiseLLMClient:
    """
    封装 raise 已有 LLM 调用逻辑的轻量客户端。

    优先使用 Gemini，若不可用则降级到 OpenAI 兼容 API。
    """

    def __init__(self, temperature: Optional[float] = None):
        self.config = get_config()
        self.temperature = temperature if temperature is not None else self.config.multi_agent_llm_temperature
        self._gemini_client = None
        self._openai_client = None
        self._init_clients()

    def _init_clients(self) -> None:
        if self.config.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.config.gemini_api_key)
                self._gemini_client = genai
                logger.debug("多智能体 LLM: Gemini 客户端初始化成功")
            except Exception as e:
                logger.warning(f"多智能体 LLM: Gemini 初始化失败: {e}")

        if self.config.openai_api_key:
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(
                    api_key=self.config.openai_api_key,
                    base_url=self.config.openai_base_url,
                )
                logger.debug("多智能体 LLM: OpenAI 客户端初始化成功")
            except Exception as e:
                logger.warning(f"多智能体 LLM: OpenAI 初始化失败: {e}")

    def chat(self, system_prompt: str, user_prompt: str, temperature: Optional[float] = None) -> str:
        """
        调用 LLM 生成回复。

        Args:
            system_prompt: 系统角色提示
            user_prompt: 用户输入（包含分析上下文）
            temperature: 覆盖实例默认温度

        Returns:
            LLM 生成的文本内容
        """
        temp = temperature if temperature is not None else self.temperature

        # 先走 Gemini（与主分析器一致），失败再 OpenAI 兼容接口
        if self._gemini_client:
            result = self._call_gemini(system_prompt, user_prompt, temp)
            if result:
                return result

        if self._openai_client:
            result = self._call_openai(system_prompt, user_prompt, temp)
            if result:
                return result

        raise RuntimeError("所有 LLM 客户端均不可用，请检查 API Key 配置")

    def _call_gemini(self, system_prompt: str, user_prompt: str, temperature: float) -> Optional[str]:
        max_retries = self.config.gemini_max_retries
        retry_delay = self.config.gemini_retry_delay

        for attempt in range(max_retries):
            try:
                import google.generativeai as genai
                model = genai.GenerativeModel(
                    model_name=self.config.gemini_model,
                    system_instruction=system_prompt,
                )
                response = model.generate_content(
                    user_prompt,
                    generation_config=genai.types.GenerationConfig(temperature=temperature),
                )
                if response and response.text:
                    # 成功后仍 sleep：多 Agent 连续节点调用时降低瞬时 QPS，减轻 429
                    time.sleep(self.config.gemini_request_delay)
                    return response.text.strip()
            except Exception as e:
                err = str(e)
                if "429" in err or "quota" in err.lower():
                    # 指数退避：限流时拉长等待，避免雪崩式重试
                    wait = retry_delay * (2 ** attempt)
                    logger.warning(f"Gemini 限流，等待 {wait:.0f}s 后重试 (attempt {attempt + 1})")
                    time.sleep(wait)
                elif attempt < max_retries - 1:
                    logger.warning(f"Gemini 调用失败 (attempt {attempt + 1}): {e}")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Gemini 多次重试失败，降级到 OpenAI: {e}")
                    return None
        return None

    def _call_openai(self, system_prompt: str, user_prompt: str, temperature: float) -> Optional[str]:
        try:
            response = self._openai_client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI 调用失败: {e}")
            return None
