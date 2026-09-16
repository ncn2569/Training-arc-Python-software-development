"""Load and validate benchmark task YAML files.

A task describes a clean seed directory, the agent instruction, execution
limits, and declared final artifacts. The judge may also inspect supporting files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .config import HARNESS_ROOT

DEFAULT_BENCH_TASK_PATH = HARNESS_ROOT / "tasks" / "telemetry_window_repair.yaml"
OVERNIGHT_TASK_NAMES = (
    "telemetry_window_repair",
    "expense_dashboard",
    "fullstack_todo",
)
CALIBRATION_TASK_NAMES = (
    "telemetry_window_repair",
    "expense_dashboard",
    "fullstack_todo",
    "fullstack_incident_command_center",
    "feature_flag_rollout_repair",
    "inventory_reservation_repair",
    "audit_log_normalizer",
)
DEFAULT_TEST_TASK_PATHS = tuple(sorted((HARNESS_ROOT / "tasks" / "heldout" / "test").glob("*.yaml")))
DEFAULT_VALIDATION_TASK_PATHS = tuple(sorted((HARNESS_ROOT / "tasks" / "heldout" / "val").glob("*.yaml")))


def task_paths(requested: list[str] | None = None) -> list[Path]:
    """Resolve requested YAMLs or enumerate only top-level source/train tasks."""
    if requested:
        paths = [Path(item).resolve() for item in requested]
    else:
        paths = sorted((HARNESS_ROOT / "tasks").glob("*.yaml"))
    if not paths:
        raise RuntimeError("No task YAML files found. Add one under self_harness/tasks/.")
    return paths


def load_task(path: Path) -> dict[str, Any]:
    """Validate one task contract and normalize all paths/limits for runners."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: task YAML must be an object")
    for key in ("id", "prompt", "judge"):
        if not raw.get(key):
            raise ValueError(f"{path}: missing required field {key!r}")
    if not isinstance(raw["judge"], dict) or not raw["judge"].get("rubric"):
        raise ValueError(f"{path}: judge.rubric is required")
    task_id = str(raw["id"])
    if any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for char in task_id):
        raise ValueError(f"{path}: id may contain only letters, numbers, '_' and '-'")
    seed_value = str(raw.get("seed_dir") or "")
    seed_dir = (HARNESS_ROOT / seed_value).resolve() if seed_value else path.parent / "fixtures" / task_id
    if not seed_dir.is_relative_to(HARNESS_ROOT):
        raise ValueError(f"{path}: seed_dir must stay inside self_harness/")
    artifacts = raw["judge"].get("artifacts", [])
    if not isinstance(artifacts, list):
        raise ValueError(f"{path}: judge.artifacts must be a list")
    for artifact in artifacts:
        if not isinstance(artifact, dict) or not artifact.get("path"):
            raise ValueError(f"{path}: every judge artifact needs path")
        if artifact.get("mode", "text") not in {"text", "image", "render"}:
            raise ValueError(f"{path}: artifact mode must be text, image, or render")
    return {
        "id": task_id,
        "prompt": str(raw["prompt"]),
        "seed_dir": seed_dir,
        "timeout_seconds": int(raw.get("timeout_seconds", 600)),
        "max_turns": int(raw.get("max_turns", 30)),
        "judge": {
            "rubric": str(raw["judge"]["rubric"]),
            "pass_score": float(raw["judge"].get("pass_score", 0.8)),
            "artifacts": artifacts,
        },
        "source_path": str(path),
    }


def load_tasks(requested: list[str] | None = None) -> list[dict[str, Any]]:
    """Load a unique-ID task list; duplicate IDs would corrupt suite accounting."""
    tasks = [load_task(path) for path in task_paths(requested)]
    ids = [task["id"] for task in tasks]
    if len(set(ids)) != len(ids):
        raise ValueError("Task ids must be unique")
    return tasks


def load_optimization_tasks(requested: list[str] | None = None) -> list[dict[str, Any]]:
    """One shared task supplies both tuner feedback and promotion reward."""
    paths = requested or [str(DEFAULT_BENCH_TASK_PATH)]
    if len(paths) != 1:
        raise ValueError("Optimize uses exactly one --task; use bench for multiple tasks.")
    return load_tasks(paths)


def load_overnight_tasks(requested: list[str] | None = None) -> list[dict[str, Any]]:
    """Load the three retained source tasks; never include render or held-out YAMLs."""
    paths = requested or [str(HARNESS_ROOT / "tasks" / f"{name}.yaml") for name in OVERNIGHT_TASK_NAMES]
    tasks = load_tasks(paths)
    expected = set(OVERNIGHT_TASK_NAMES)
    unexpected = [task["id"] for task in tasks if task["id"] not in expected]
    if unexpected:
        raise ValueError("Overnight only runs the retained source tasks: " + ", ".join(OVERNIGHT_TASK_NAMES))
    return tasks


def load_calibration_tasks(requested: list[str] | None = None) -> list[dict[str, Any]]:
    """Load seven source/train tasks for repeated reward-delta calibration.

    Held-out YAMLs are intentionally excluded: this suite is a train
    observation, not evidence of generalization.
    """
    paths = requested or [
        str(HARNESS_ROOT / "tasks" / f"{name}.yaml")
        for name in CALIBRATION_TASK_NAMES
    ]
    tasks = load_tasks(paths)
    expected = set(CALIBRATION_TASK_NAMES)
    unexpected = [task["id"] for task in tasks if task["id"] not in expected]
    if unexpected:
        raise ValueError(
            "Calibration only runs source/train tasks: "
            + ", ".join(CALIBRATION_TASK_NAMES)
        )
    return tasks


def load_validation_tasks(requested: list[str] | None = None) -> list[dict[str, Any]]:
    """Load held-out validation tasks unless the caller explicitly selects tasks."""
    paths = requested or [str(path) for path in DEFAULT_VALIDATION_TASK_PATHS]
    if not paths:
        raise RuntimeError("No held-out validation task YAML files found")
    return load_tasks(paths)
