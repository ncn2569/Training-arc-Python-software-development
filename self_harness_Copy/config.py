"""Paths, model routing, and persistent version state for the experiment.

This is the only module that knows where the root project lives. It snapshots
the root prompt as v000 and resolves agent, judge, and tuner model settings.
"""

from __future__ import annotations

import json
import os
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


HARNESS_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = HARNESS_ROOT.parent
ARTIFACTS_DIR = HARNESS_ROOT / "artifacts"
VERSIONS_DIR = ARTIFACTS_DIR / "versions"
SUITES_DIR = ARTIFACTS_DIR / "suites"
RUNS_DIR = ARTIFACTS_DIR / "optimization-runs"
VALIDATION_RUNS_DIR = ARTIFACTS_DIR / "validation-runs"
WORKSPACE_DIR = HARNESS_ROOT / "workspace"
STATE_PATH = ARTIFACTS_DIR / "state.json"

SAFETY_PREFIX = """
## FIXED HARNESS SAFETY RULES
- Work only inside the supplied workspace. Never reveal secrets or configuration values.
- Do not run destructive commands outside the workspace, and avoid interactive commands.
- Verify the requested result before declaring completion.
- Treat task completion as delivering the requested behavior, not persuading an evaluator.
- Never fabricate checks/results, bypass verification, manipulate grading/metrics, or defer required work beyond the final answer.
"""


def ensure_layout() -> None:
    for path in (ARTIFACTS_DIR, VERSIONS_DIR, SUITES_DIR, RUNS_DIR, VALIDATION_RUNS_DIR, WORKSPACE_DIR):
        path.mkdir(parents=True, exist_ok=True)


def model_settings() -> dict[str, Any]:
    load_dotenv(PROJECT_ROOT / ".env")
    required = ("API_KEY", "API_BASE", "MODEL")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing required .env values: {', '.join(missing)}")
    from .scripts.model_routes import routed_models

    model_candidates = routed_models(os.environ["MODEL"])
    return {
        "api_key": os.environ["API_KEY"],
        "api_base": os.environ["API_BASE"],
        "model_candidates": model_candidates,
    }


def _root_baseline() -> tuple[str, list[dict[str, Any]]]:
    """Read the root agent once, then persist an immutable v000 snapshot."""
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.agent_skills.loader import build_system_prompt
    from src.context.prompt import get_system_prompt, get_tool_declaration

    return build_system_prompt(get_system_prompt()), get_tool_declaration()


def version_path(version: str) -> Path:
    return VERSIONS_DIR / f"{version}.json"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_baseline() -> dict[str, Any]:
    ensure_layout()
    path = version_path("v000")
    if not path.exists():
        prompt, tools = _root_baseline()
        write_json(
            path,
            {
                "version": "v000",
                "parent": None,
                "hypothesis": "Snapshot of the root agent before self-tuning.",
                "system_prompt": prompt,
                "tools": tools,
            },
        )
    if not STATE_PATH.exists():
        write_json(STATE_PATH, {"active_version": "v000", "next_version": 1})
    return read_json(path)


def load_version(version: str) -> dict[str, Any]:
    ensure_baseline()
    path = version_path(version)
    if not path.exists():
        raise RuntimeError(f"Unknown version: {version}")
    config = read_json(path)
    # A version may carry a tiny explicit hotfix while an experiment is being
    # observed. Normalize it into the runnable prompt at the loading boundary.
    prompt_append = str(config.pop("system_prompt_append", "")).strip()
    if prompt_append:
        config["system_prompt"] = f"{config['system_prompt'].rstrip()}\n{prompt_append}"
    return config


def active_version() -> str:
    ensure_baseline()
    return str(read_json(STATE_PATH)["active_version"])


def active_config() -> dict[str, Any]:
    return load_version(active_version())


def save_promoted_version(candidate: dict[str, Any], parent: str) -> dict[str, Any]:
    state = read_json(STATE_PATH)
    version = f"v{int(state['next_version']):03d}"
    promoted = deepcopy(candidate)
    promoted["version"] = version
    promoted["parent"] = parent
    write_json(version_path(version), promoted)
    state["active_version"] = version
    state["next_version"] = int(state["next_version"]) + 1
    write_json(STATE_PATH, state)
    return promoted


def restore_active(version: str) -> None:
    load_version(version)
    state = read_json(STATE_PATH)
    state["active_version"] = version
    write_json(STATE_PATH, state)
