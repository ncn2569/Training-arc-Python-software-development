"""Configure a shared ordered failover route for overnight runs.

All three harness roles (agent, judge, and tuner) use the same ordered route.
When one gateway call fails, the next model is tried for that same call.
"""

from __future__ import annotations


MODEL_FALLBACKS = [
    "openai/kCode",
    "deepseek/deepseek-v4-flash",
    "openai/qwen/qwen3.8-flash",
]


def routed_models(default_model: str) -> list[str]:
    """Return valid configured models, falling back to MODEL when unconfigured."""
    configured = [
        value.strip()
        for value in MODEL_FALLBACKS
        if isinstance(value, str) and value.strip() and not value.startswith("REPLACE_")
    ]
    return configured or [default_model]
