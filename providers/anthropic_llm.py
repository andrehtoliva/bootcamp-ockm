"""Claude API provider with structured outputs, retry, and observability."""

from __future__ import annotations

import json
import time
from typing import Type, TypeVar

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from observability.logger import get_logger

log = get_logger(__name__)
T = TypeVar("T")


class AnthropicLLM:
    """Claude LLM provider via Anthropic SDK. Implements LLMProvider protocol."""

    provider_name: str = "anthropic"

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
    ) -> None:
        self.model_id = model
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        reraise=True,
    )
    async def generate(
        self,
        prompt: str,
        response_model: Type[T],
        *,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> T:
        start = time.perf_counter()

        message = await self._client.messages.create(
            model=self.model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        latency_ms = (time.perf_counter() - start) * 1000
        raw_text = message.content[0].text

        # Extract JSON from response (handle markdown code blocks)
        json_text = raw_text.strip()
        if json_text.startswith("```"):
            lines = json_text.split("\n")
            # Remove first and last lines (```json and ```)
            json_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        parsed = response_model.model_validate_json(json_text)

        log.info(
            "anthropic.generate.success",
            model=self.model_id,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
            latency_ms=round(latency_ms, 2),
        )

        # Attach usage metadata for metrics collection
        parsed._anthropic_usage = {  # type: ignore[attr-defined]
            "input_tokens": message.usage.input_tokens,
            "output_tokens": message.usage.output_tokens,
            "latency_ms": round(latency_ms, 2),
        }

        return parsed
