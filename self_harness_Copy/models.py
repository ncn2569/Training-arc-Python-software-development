"""Small LiteLLM adapter shared by the agent, judge, and tuner.

It normalizes provider-specific response objects, captures usage, and steps
through the shared fallback-model route when an individual call fails.
"""

from __future__ import annotations

import json
import time
from typing import Any


class ProviderCallError(RuntimeError):
    """All configured providers failed for one model request."""

    def __init__(self, errors: list[str], failure_wall_time: float) -> None:
        super().__init__(
            f"All routed models failed ({len(errors)} attempted): {' | '.join(errors)}"
        )
        self.failure_wall_time = failure_wall_time
        self.errors = errors


def _plain(value: Any) -> Any:
    """Convert LiteLLM/Pydantic response objects into JSON-safe Python values."""
    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_none=True)
    if hasattr(value, "dict"):
        return value.dict(exclude_none=True)
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    return value


def _usage(response: Any, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None, model: str) -> dict[str, Any]:
    """Use provider usage when available; otherwise estimate with LiteLLM's tokenizer."""
    raw = _plain(getattr(response, "usage", None)) or {}
    prompt = raw.get("prompt_tokens")
    completion_tokens = raw.get("completion_tokens")
    total = raw.get("total_tokens")
    if isinstance(prompt, int) and isinstance(completion_tokens, int):
        return {
            "input_tokens": prompt,
            "output_tokens": completion_tokens,
            "total_tokens": total if isinstance(total, int) else prompt + completion_tokens,
            "source": "provider",
        }
    try:
        from litellm import token_counter

        estimated_input = token_counter(model=model, messages=messages, tools=tools, default_token_count=256)
    except Exception:
        estimated_input = max(1, len(json.dumps(messages, ensure_ascii=False)) // 4)
    message = _plain(response.choices[0].message)
    text = json.dumps(message, ensure_ascii=False)
    try:
        estimated_output = token_counter(model=model, text=text, default_token_count=256)
    except Exception:
        estimated_output = max(1, len(text) // 4)
    return {
        "input_tokens": estimated_input,
        "output_tokens": estimated_output,
        "total_tokens": estimated_input + estimated_output,
        "source": "estimated",
    }


def call_model(
    *,
    settings: dict[str, Any],
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Try the shared route once and separate failed-provider latency.

    The caller decides whether to retry a fully failed request. If a fallback
    succeeds, ``wall_time`` contains only the successful request; failed
    requests and backoff are audit-only ``provider_failure_time``.
    """
    # Planning/dry-run commands never call this adapter, so LiteLLM is imported
    # lazily and a missing gateway cannot affect command parsing.
    from litellm import completion

    candidates = settings["model_candidates"]
    errors: list[str] = []
    provider_failure_time = 0.0
    for attempt, model in enumerate(candidates):
        attempt_started = time.perf_counter()
        try:
            request: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "api_key": settings["api_key"],
                "api_base": settings["api_base"],
                "timeout": 120,
            }
            if tools is not None:
                request["tools"] = tools
            response = completion(**request)
            return {
                "message": _plain(response.choices[0].message),
                "usage": _usage(response, messages, tools, model),
                "api_retries": attempt,
                "model": model,
                "wall_time": time.perf_counter() - attempt_started,
                "provider_failure_time": provider_failure_time,
            }
        except Exception as exc:  # provider-specific exceptions vary
            provider_failure_time += time.perf_counter() - attempt_started
            errors.append(f"{model}: {exc}")
            if attempt < len(candidates) - 1:
                backoff_started = time.perf_counter()
                time.sleep(1)
                provider_failure_time += time.perf_counter() - backoff_started
    raise ProviderCallError(errors, provider_failure_time)


def extract_json(text: str) -> dict[str, Any]:
    """Extract one JSON object, accepting a model's optional Markdown fence."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("Model response did not contain a JSON object")
    value = json.loads(text[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("Model JSON response must be an object")
    return value
