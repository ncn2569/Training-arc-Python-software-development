"""Health-check every shared fallback model through LiteLLM.

Run from the repository root:
    python -m self_harness.scripts.test_litellm_models

The script sends only ``Reply exactly: OK``. It does not load agent prompts,
tools, tasks, trajectories, or workspace artifacts.
"""

from __future__ import annotations

import os
import time
from typing import Any

from dotenv import load_dotenv
from litellm import completion

from self_harness.config import PROJECT_ROOT
from self_harness.scripts.model_routes import routed_models


def _usage_value(response: Any, key: str) -> int | None:
    """Read a usage field from LiteLLM's provider-specific object safely."""
    usage = getattr(response, "usage", None)
    value = getattr(usage, key, None)
    return value if isinstance(value, int) else None


def main() -> int:
    """Call each configured fallback once and return nonzero if any one fails."""
    load_dotenv(PROJECT_ROOT / ".env")
    missing = [name for name in ("API_KEY", "API_BASE", "MODEL") if not os.getenv(name)]
    if missing:
        print(f"Missing .env values: {', '.join(missing)}")
        return 2

    models = routed_models(os.environ["MODEL"])
    print(f"Testing {len(models)} configured model(s) against {os.environ['API_BASE']}")
    failures = 0
    for index, model in enumerate(models, start=1):
        started = time.perf_counter()
        try:
            response = completion(
                model=model,
                messages=[{"role": "user", "content": "Reply exactly: OK"}],
                api_key=os.environ["API_KEY"],
                api_base=os.environ["API_BASE"],
                timeout=30,
            )
            text = str(response.choices[0].message.content or "").strip().replace("\n", " ")
            prompt_tokens = _usage_value(response, "prompt_tokens")
            completion_tokens = _usage_value(response, "completion_tokens")
            token_text = "usage unavailable" if prompt_tokens is None else f"in={prompt_tokens}, out={completion_tokens}"
            print(f"[{index}/{len(models)}] OK   {model} · {time.perf_counter() - started:.2f}s · {token_text} · {text[:80]}")
        except Exception as exc:  # gateway/provider exceptions differ by model
            failures += 1
            print(f"[{index}/{len(models)}] FAIL {model} · {time.perf_counter() - started:.2f}s · {type(exc).__name__}: {exc}")
    if failures:
        print(f"Finished with {failures}/{len(models)} failed model(s).")
        return 1
    print("All configured fallback models responded successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
