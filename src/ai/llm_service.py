"""
Centralized NVIDIA Nemotron LLM Service
Integrates NVIDIA Nemotron 3.5 Lightning 30B A3B using the OpenAI Python SDK.
Enforces client centralization, reasoning/content separation, structured error handling,
retry management, and secret sanitization.
"""

import time
import json
import logging
from typing import List, Dict, Any, Optional, Iterator, Generator, Tuple
from openai import OpenAI, AuthenticationError, RateLimitError, APITimeoutError, APIConnectionError, APIStatusError

from src.core.config import NVIDIAConfig, config
from src.core.exceptions import (
    LLMConfigurationError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMResponseError,
    LLMError,
)
from src.core.security import mask_secret, sanitize_log_message
from src.ai.models import LLMMessage, LLMResponse

logger = logging.getLogger("ai.llm_service")


class NVIDIANemotronService:
    """
    Centralized service for NVIDIA Nemotron LLM inference.
    All application modules must invoke LLM capabilities through this service.
    """

    def __init__(self, cfg: Optional[NVIDIAConfig] = None):
        self.config = cfg or config.nvidia
        self._client: Optional[OpenAI] = None

    def _get_client(self) -> OpenAI:
        """
        Lazily initializes the OpenAI client.
        Raises LLMConfigurationError if API key is unconfigured.
        """
        if not self.config.is_configured:
            raise LLMConfigurationError(
                "NVIDIA Nemotron API key is not configured. "
                "Please set the 'NVIDIA_API_KEY' environment variable."
            )
        if self._client is None:
            self._client = OpenAI(
                base_url=self.config.base_url,
                api_key=self.config.api_key,
                timeout=self.config.timeout_seconds,
                max_retries=0  # Handled explicitly with fine-grained error control
            )
        return self._client

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        enable_thinking: Optional[bool] = None,
        reasoning_budget: Optional[int] = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        """
        Executes a non-streaming chat completion request.
        Strictly isolates reasoning content from user-facing response content.
        """
        client = self._get_client()

        temp = temperature if temperature is not None else self.config.temperature
        top_prob = top_p if top_p is not None else self.config.top_p
        tokens = max_tokens if max_tokens is not None else self.config.max_output_tokens
        thinking = enable_thinking if enable_thinking is not None else self.config.enable_thinking
        budget = reasoning_budget if reasoning_budget is not None else self.config.reasoning_budget

        extra_body: Dict[str, Any] = {}
        if thinking:
            extra_body["chat_template_kwargs"] = {"enable_thinking": True}
            extra_body["reasoning_budget"] = budget

        kwargs: Dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temp,
            "top_p": top_prob,
            "max_tokens": tokens,
            "stream": False,
        }
        if extra_body:
            kwargs["extra_body"] = extra_body
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        start_time = time.perf_counter()
        attempt = 0
        last_error = None

        while attempt <= self.config.max_retries:
            attempt += 1
            try:
                logger.info(sanitize_log_message(
                    f"Dispatching LLM request to {self.config.model} (attempt {attempt}/{self.config.max_retries + 1})"
                ))
                completion = client.chat.completions.create(**kwargs)
                latency_ms = (time.perf_counter() - start_time) * 1000

                if not completion.choices:
                    raise LLMResponseError("LLM response contained no choices.")

                choice = completion.choices[0]
                message = choice.message
                raw_content = message.content or ""

                # Extract reasoning tokens (if provided by Nemotron)
                reasoning = getattr(message, "reasoning_content", None)
                if not reasoning and hasattr(message, "model_extra") and isinstance(message.model_extra, dict):
                    reasoning = message.model_extra.get("reasoning_content")

                reasoning_str = str(reasoning) if reasoning and isinstance(reasoning, str) else None

                usage_dict = {}
                if hasattr(completion, "usage") and completion.usage:
                    usage_dict = {
                        "prompt_tokens": getattr(completion.usage, "prompt_tokens", 0),
                        "completion_tokens": getattr(completion.usage, "completion_tokens", 0),
                        "total_tokens": getattr(completion.usage, "total_tokens", 0),
                    }

                # Optional JSON mode validation
                if json_mode:
                    try:
                        json.loads(raw_content)
                    except json.JSONDecodeError as jde:
                        raise LLMResponseError(f"Requested json_mode but response was not valid JSON: {jde}")

                finish_reason_str = str(choice.finish_reason) if choice.finish_reason and isinstance(choice.finish_reason, str) else None

                return LLMResponse(
                    content=raw_content,
                    reasoning_content=reasoning_str,
                    model=str(completion.model or self.config.model),
                    usage=usage_dict,
                    latency_ms=round(latency_ms, 2),
                    finish_reason=finish_reason_str
                )

            except AuthenticationError as e:
                # Do NOT retry authentication failures
                logger.error(sanitize_log_message(f"LLM Authentication error: {e}"))
                raise LLMAuthenticationError(f"Authentication failed with NVIDIA API: {e}") from e

            except RateLimitError as e:
                logger.warning(sanitize_log_message(f"LLM Rate limit reached (attempt {attempt}): {e}"))
                last_error = LLMRateLimitError(f"Rate limited by NVIDIA API: {e}")
                if attempt <= self.config.max_retries:
                    time.sleep(2 ** attempt)
                else:
                    raise last_error from e

            except APITimeoutError as e:
                logger.warning(sanitize_log_message(f"LLM Request timed out (attempt {attempt}): {e}"))
                last_error = LLMTimeoutError(f"NVIDIA API request timed out after {self.config.timeout_seconds}s: {e}")
                if attempt <= self.config.max_retries:
                    time.sleep(1)
                else:
                    raise last_error from e

            except (APIConnectionError, APIStatusError) as e:
                logger.warning(sanitize_log_message(f"LLM Network/API error (attempt {attempt}): {e}"))
                last_error = LLMError(f"NVIDIA API connection error: {e}")
                if attempt <= self.config.max_retries:
                    time.sleep(1)
                else:
                    raise last_error from e

            except Exception as e:
                if isinstance(e, LLMError):
                    raise
                logger.error(sanitize_log_message(f"Unexpected LLM error: {e}"))
                raise LLMError(f"Unexpected LLM error occurred: {e}") from e

        if last_error:
            raise last_error
        raise LLMError("Failed to complete LLM request after retries.")

    def stream_generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        enable_thinking: Optional[bool] = None,
        reasoning_budget: Optional[int] = None,
    ) -> Generator[Tuple[str, str], None, None]:
        """
        Streams completions from NVIDIA Nemotron.
        Yields tuples of (chunk_type, text):
          - ("reasoning", text): internal thinking tokens
          - ("content", text): final answer text intended for user
        """
        client = self._get_client()

        temp = temperature if temperature is not None else self.config.temperature
        top_prob = top_p if top_p is not None else self.config.top_p
        tokens = max_tokens if max_tokens is not None else self.config.max_output_tokens
        thinking = enable_thinking if enable_thinking is not None else self.config.enable_thinking
        budget = reasoning_budget if reasoning_budget is not None else self.config.reasoning_budget

        extra_body: Dict[str, Any] = {}
        if thinking:
            extra_body["chat_template_kwargs"] = {"enable_thinking": True}
            extra_body["reasoning_budget"] = budget

        kwargs: Dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temp,
            "top_p": top_prob,
            "max_tokens": tokens,
            "stream": True,
        }
        if extra_body:
            kwargs["extra_body"] = extra_body

        try:
            stream = client.chat.completions.create(**kwargs)
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta

                # 1. Reasoning chunk
                reasoning = getattr(delta, "reasoning_content", None)
                if reasoning:
                    yield ("reasoning", reasoning)

                # 2. Content chunk
                if delta.content:
                    yield ("content", delta.content)

        except AuthenticationError as e:
            raise LLMAuthenticationError(f"Authentication failed during stream: {e}") from e
        except RateLimitError as e:
            raise LLMRateLimitError(f"Rate limited during stream: {e}") from e
        except APITimeoutError as e:
            raise LLMTimeoutError(f"Timeout during stream: {e}") from e
        except Exception as e:
            raise LLMError(f"Error during stream generation: {e}") from e
