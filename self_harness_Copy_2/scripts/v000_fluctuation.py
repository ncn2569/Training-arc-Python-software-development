"""Measure natural benchmark variation for v000 without tuning or promotion.

Each measurement receives the same immutable v000 config and the same seven-task
calibration suite, but fresh task workspaces and fresh model calls. The first
successful measurement is used only as a fixed reward-cost reference; every
later measurement is still v000. This makes reward deltas a view of environment
and sampling variation, not prompt improvement.
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from ..bench import run_bench
from ..config import ARTIFACTS_DIR, ensure_baseline, load_version, model_settings, write_json
from ..reward import score_suite
from ..tasks import load_calibration_tasks


DEFAULT_MEASUREMENTS = 5
DEFAULT_TASK_TIMEOUT = 600
DEFAULT_TASK_TURNS = 36
DEFAULT_RETRY_ATTEMPTS = 2


class RetryableMeasurementError(RuntimeError):
    """A failed provider/judge measurement that must not enter fluctuation stats."""


def _cap_task_limits(
    tasks: list[dict[str, Any]], *, timeout: int, turns: int
) -> None:
    """Apply the same effective per-task caps to every repeated measurement."""
    for task in tasks:
        task["timeout_seconds"] = min(int(task["timeout_seconds"]), timeout)
        task["max_turns"] = min(int(task["max_turns"]), turns)


def _number(summary: dict[str, Any], key: str, *, agent: bool = False) -> float:
    """Read one numeric report field; all inputs are written by the harness."""
    value = summary["agent"][key] if agent else summary[key]
    return float(value)


def _delta(current: float, baseline: float) -> float | None:
    """Return relative cost movement, avoiding a meaningless divide by zero."""
    return None if baseline == 0 else (current - baseline) / baseline


def _quantile(values: list[float], percentile: float) -> float | None:
    """Linear percentile without a NumPy dependency."""
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    index = (len(ordered) - 1) * percentile
    lower, upper = int(index), min(int(index) + 1, len(ordered) - 1)
    fraction = index - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _summary_row(measurement: int, suite: dict[str, Any]) -> dict[str, Any]:
    """Keep the run report compact; complete evidence remains in its manifest."""
    summary = suite["summary"]
    return {
        "measurement": measurement,
        "suite_id": suite["suite_id"],
        "manifest_path": suite["manifest_path"],
        "pass_count": int(summary["pass_count"]),
        "task_count": int(summary["task_count"]),
        "quality": _number(summary, "average_score"),
        "hacking_penalty": float(summary.get("reward_hacking_penalty", 0.0)),
        "reward": _number(summary, "reward"),
        "tokens": _number(summary, "total_tokens", agent=True),
        "turns": _number(summary, "turns", agent=True),
        "wall_time": _number(summary, "wall_time", agent=True),
        "provider_failure_seconds": _number(
            summary, "provider_failure_seconds", agent=True
        ),
    }


def _render_report(run: dict[str, Any]) -> str:
    """Explain raw variation and reference-relative drift in one readable file."""
    rows = run["measurements"]
    baseline = rows[0]
    lines = [
        "# v000 natural-fluctuation measurement",
        "",
        f"Version: `{run['version']}` | Measurements: {len(rows)} | Tasks: {', '.join(run['task_ids'])}",
        f"Model route: `{', '.join(run['model_candidates'])}`",
        "",
        "Every row uses exactly v000 and a fresh seven-task workspace suite. No tuner, candidate, promotion, or active-version change occurs. The first row is only the fixed cost reference for reward normalization.",
        "",
        "| Run | Pass | Quality | Hacking penalty | Tokens | Turns | Agent time (s) | Reward | Provider-failure seconds |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['measurement']} | {row['pass_count']}/{row['task_count']} | "
            f"{row['quality']:.3f} | {row['hacking_penalty']:.3f} | "
            f"{int(row['tokens']):,} | {int(row['turns'])} | {row['wall_time']:.1f} | "
            f"{row['reward']:.4f} | {row['provider_failure_seconds']:.1f} |"
        )

    lines.extend(
        [
            "",
            "## Delta versus measurement 1",
            "",
            "| Run | Quality delta | Reward delta | Tokens | Turns | Agent time |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['measurement']} | {row['quality'] - baseline['quality']:+.4f} | "
            f"{row['reward'] - baseline['reward']:+.4f} | "
            f"{_format_percent(_delta(row['tokens'], baseline['tokens']))} | "
            f"{_format_percent(_delta(row['turns'], baseline['turns']))} | "
            f"{_format_percent(_delta(row['wall_time'], baseline['wall_time']))} |"
        )

    reward_deltas = [row["reward"] - baseline["reward"] for row in rows[1:]]
    all_rewards = [row["reward"] for row in rows]
    lines.extend(["", "## Observed fluctuation", ""])
    lines.append(
        f"- Reward: mean `{statistics.mean(all_rewards):.4f}`, population stddev `{statistics.pstdev(all_rewards):.4f}`, range `{min(all_rewards):.4f}` to `{max(all_rewards):.4f}`."
    )
    if reward_deltas:
        absolute = [abs(delta) for delta in reward_deltas]
        lines.append(
            f"- Absolute reward drift vs measurement 1: median `{statistics.median(absolute):.4f}`, p75 `{_quantile(absolute, 0.75):.4f}`, max `{max(absolute):.4f}`."
        )
    lines.extend(
        [
            "- Agent time excludes provider failures/backoff/retry delay. Provider-failure seconds are audit-only so outage latency does not inflate reward variation.",
            "- This is an observed five-rollout sample, not a statistically proven threshold. Compare it with later v005 control drift before choosing `min_reward_gain`.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_percent(value: float | None) -> str:
    return "-" if value is None else f"{value:+.1%}"


def _run_one_measurement(
    *, settings: dict[str, Any], config: dict[str, Any], tasks: list[dict[str, Any]], reference: dict[str, Any] | None
) -> dict[str, Any]:
    """Run/score one v000 suite, discarding invalid evaluator measurements."""
    try:
        suite = run_bench(settings=settings, config=config, tasks=tasks)
    except RuntimeError as exc:
        if "Provider retries exhausted" not in str(exc):
            raise
        raise RetryableMeasurementError(
            "Provider retries were exhausted; discarded this measurement."
        ) from exc
    score_suite(suite, reference or suite)
    if not suite["summary"]["evaluation_valid"]:
        raise RetryableMeasurementError(
            "Judge evaluation was incomplete; discarded this measurement rather than recording noise."
        )
    write_json(Path(suite["manifest_path"]), suite)
    return suite


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Repeat v000 on the calibration suite to measure natural fluctuation."
    )
    parser.add_argument("--runs", type=int, default=DEFAULT_MEASUREMENTS)
    parser.add_argument("--task-timeout", type=int, default=DEFAULT_TASK_TIMEOUT)
    parser.add_argument("--task-turns", type=int, default=DEFAULT_TASK_TURNS)
    parser.add_argument(
        "--measurement-retries",
        type=int,
        default=DEFAULT_RETRY_ATTEMPTS,
        help="Fresh retries for a discarded provider/judge measurement.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.runs < 2 or args.task_timeout < 1 or args.task_turns < 1 or args.measurement_retries < 0:
        parser.error("runs must be >=2; limits must be positive; retries must be nonnegative")

    ensure_baseline()
    config = load_version("v000")
    tasks = load_calibration_tasks()
    _cap_task_limits(tasks, timeout=args.task_timeout, turns=args.task_turns)
    print(
        f"v000 fluctuation plan: {args.runs} measurements x {len(tasks)} tasks "
        f"(turns <= {args.task_turns}, time <= {args.task_timeout}s)"
    )
    print("tasks: " + ", ".join(task["id"] for task in tasks))
    if args.dry_run:
        return 0

    settings = model_settings()
    run_dir = ARTIFACTS_DIR / "fluctuation-runs" / (
        f"v000-fluctuation-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    )
    run_dir.mkdir(parents=True)
    run: dict[str, Any] = {
        "mode": "v000-natural-fluctuation",
        "version": config["version"],
        "task_ids": [task["id"] for task in tasks],
        "task_limits": {"timeout_seconds": args.task_timeout, "max_turns": args.task_turns},
        "model_candidates": settings["model_candidates"],
        "measurements": [],
        "discarded_attempts": [],
    }
    reference: dict[str, Any] | None = None
    for measurement in range(1, args.runs + 1):
        for attempt in range(1, args.measurement_retries + 2):
            try:
                print(f"Measurement {measurement}/{args.runs}, attempt {attempt}")
                suite = _run_one_measurement(
                    settings=settings, config=config, tasks=tasks, reference=reference
                )
                if reference is None:
                    reference = suite
                run["measurements"].append(_summary_row(measurement, suite))
                write_json(run_dir / "run.json", run)
                break
            except RetryableMeasurementError as exc:
                run["discarded_attempts"].append(
                    {"measurement": measurement, "attempt": attempt, "reason": str(exc)}
                )
                write_json(run_dir / "run.json", run)
                if attempt > args.measurement_retries:
                    raise RuntimeError(
                        f"Measurement {measurement} remained invalid after {attempt} attempts"
                    ) from exc
                print(f"Discarded measurement {measurement}: {exc}; retrying fresh suite.")

    report_path = run_dir / "report.md"
    report_path.write_text(_render_report(run), encoding="utf-8")
    print(f"v000 fluctuation complete. Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
