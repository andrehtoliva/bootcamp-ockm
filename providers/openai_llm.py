"""OpenAI fallback LLM provider."""

from __future__ import annotations

import json
import time
from typing import Type, TypeVar

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from observability.logger import get_logger

log = get_logger(__name__)
T = TypeVar("T")


class OpenAILLM:
    """OpenAI GPT as fallback provider. Implements LLMProvider protocol."""

    provider_name: str = "openai"

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
    ) -> None:
        self.model_id = model
        self._client = AsyncOpenAI(api_key=api_key)

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=8),
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

        response = await self._client.chat.completions.create(
            model=self.model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "Responda APENAS com JSON válido. Sem texto adicional.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        latency_ms = (time.perf_counter() - start) * 1000
        raw_text = response.choices[0].message.content or "{}"

        # Extract JSON from response (handle markdown code blocks)
        json_text = raw_text.strip()
        if json_text.startswith("```"):
            lines = json_text.split("\n")
            json_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        parsed = response_model.model_validate_json(json_text)

        input_tokens = response.usage.prompt_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0

        log.info(
            "openai.generate.success",
            model=self.model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=round(latency_ms, 2),
        )

        parsed._openai_usage = {  # type: ignore[attr-defined]
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": round(latency_ms, 2),
        }

        return parsed
