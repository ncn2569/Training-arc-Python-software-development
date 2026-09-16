"""Feedback and reward selection for one task or the retained overnight suite."""

from __future__ import annotations

import math
import time
import uuid
from pathlib import Path
from typing import Any

from .bench import run_bench
from .config import (
    RUNS_DIR,
    STATE_PATH,
    VALIDATION_RUNS_DIR,
    active_config,
    ensure_baseline,
    load_version,
    read_json,
    save_promoted_version,
    write_json,
)
from .reward import REWARD_CONFIG, score_suite
from .tasks import (
    load_calibration_tasks,
    load_optimization_tasks,
    load_overnight_tasks,
    load_tasks,
    load_validation_tasks,
)
from .tuner import propose_candidate, summarize_candidate_change


def _validate_optimization_request(
    *,
    overnight_suite: bool,
    calibration_suite: bool,
    control_rollouts: int,
    max_rounds: int,
    patience_limit: int,
    min_reward_gain: float,
    task_timeout: int,
    task_turns: int,
) -> None:
    """Reject an ambiguous or non-comparable experiment before any API call."""
    if (
        max_rounds < 1
        or patience_limit < 1
        or task_timeout < 1
        or task_turns < 1
        or control_rollouts < 0
    ):
        raise ValueError("Round, patience and runtime limits must be positive")
    if not math.isfinite(min_reward_gain) or min_reward_gain < 0:
        raise ValueError("Invalid minimum reward gain")
    if overnight_suite and calibration_suite:
        raise ValueError("Choose either the overnight or calibration suite")
    if control_rollouts and not calibration_suite:
        raise ValueError("Control rollouts are only available for calibration")


def _experiment_mode(*, overnight_suite: bool, calibration_suite: bool) -> str:
    """Name the task-selection policy persisted in run.json."""
    if calibration_suite:
        return "calibration-suite"
    return "overnight-suite" if overnight_suite else "single-task"


def _select_experiment_tasks(
    *,
    requested_tasks: list[str] | None,
    overnight_suite: bool,
    calibration_suite: bool,
) -> list[dict[str, Any]]:
    """Load exactly the task scope allowed by the selected experiment mode."""
    if calibration_suite:
        return load_calibration_tasks(requested_tasks)
    if overnight_suite:
        return load_overnight_tasks(requested_tasks)
    return load_optimization_tasks(requested_tasks)


def _apply_task_limits(
    tasks: list[dict[str, Any]], *, timeout: int, turns: int
) -> None:
    """Cap YAML task budgets in place; effective limits are persisted in the plan."""
    for task in tasks:
        task["timeout_seconds"] = min(task["timeout_seconds"], timeout)
        task["max_turns"] = min(task["max_turns"], turns)


def _task_plan(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Project mutable loaded task records into stable, readable run metadata."""
    return [
        {
            "id": task["id"],
            "source": task["source_path"],
            "timeout_seconds": task["timeout_seconds"],
            "max_turns": task["max_turns"],
        }
        for task in tasks
    ]


def decide(
    candidate: dict[str, Any], previous: dict[str, Any], *, min_reward_gain: float = 0.0
) -> tuple[bool, str]:
    """Compare shared-task reward; pass count and cost deltas are diagnostics."""
    current, prior = candidate["summary"], previous["summary"]
    if not math.isfinite(min_reward_gain) or min_reward_gain < 0:
        raise ValueError("Minimum reward gain must be finite and nonnegative")
    if not current["evaluation_valid"] or not prior["evaluation_valid"]:
        return False, "incomplete/error evaluation; reward comparison unavailable"
    if (
        candidate["reward_baseline"] != previous["reward_baseline"]
        or candidate["reward_config"] != previous["reward_config"]
    ):
        raise ValueError("Rewards must share a baseline and configuration")
    gain = current["reward"] - prior["reward"]
    return (
        gain > min_reward_gain,
        f"reward {prior['reward']:.4f} -> {current['reward']:.4f} (gain {gain:+.4f})",
    )


def _tuner_impact(
    candidate_summary: dict[str, Any], incumbent_summary: dict[str, Any]
) -> dict[str, Any]:
    """Raw experiment deltas for tuner learning, without reward values/weights."""

    def number(summary: dict[str, Any], key: str, *, agent: bool = False) -> float:
        value = summary.get("agent", {}).get(key, 0) if agent else summary.get(key, 0)
        return float(value)

    def comparison(key: str, *, agent: bool = False) -> dict[str, Any]:
        before, after = number(incumbent_summary, key, agent=agent), number(
            candidate_summary, key, agent=agent
        )
        record: dict[str, Any] = {
            "before": before,
            "after": after,
            "delta": after - before,
        }
        if before:
            record["relative_change"] = (after - before) / before
        return record

    return {
        "pass_count": comparison("pass_count"),
        "quality": comparison("average_score"),
        "reward_hacking_penalty": comparison("reward_hacking_penalty"),
        "agent": {
            "total_tokens": comparison("total_tokens", agent=True),
            "turns": comparison("turns", agent=True),
            "wall_time": comparison("wall_time", agent=True),
        },
    }


def run_benchmark(
    *,
    settings: dict[str, str],
    requested_tasks: list[str] | None,
    version: str | None = None,
) -> dict[str, Any]:
    """One-shot bench without tuning, promotion or baseline-normalized reward."""
    ensure_baseline()
    config = (
        active_config() if version in {None, "active"} else load_version(str(version))
    )
    return run_bench(
        settings=settings, config=config, tasks=load_tasks(requested_tasks)
    )


def _validation_cell(value: float, *, precision: int = 3) -> str:
    return f"{value:.{precision}f}"


def _validation_delta(
    candidate: float, reference: float, *, points: bool = False, precision: int = 3
) -> str:
    if points:
        return f"Δ {candidate - reference:+.{precision}f}"
    return "-" if reference == 0 else f"{(candidate - reference) / reference:+.1%}"


def _render_validation_report(run: dict[str, Any]) -> str:
    """Render held-out comparison without mixing metrics and deltas in one cell."""
    reference, candidate = run["reference"]["summary"], run["candidate"]["summary"]
    ref_agent, candidate_agent = reference["agent"], candidate["agent"]
    metrics = (
        ("Quality", "average_score", True, 3),
        ("Hacking penalty", "reward_hacking_penalty", True, 3),
        ("Tokens", "total_tokens", False, 0),
        ("Turns", "turns", False, 0),
        ("Time (s)", "wall_time", False, 1),
        ("Reward", "reward", True, 4),
    )

    def value(summary: dict[str, Any], agent: dict[str, Any], key: str) -> float:
        return float(
            agent[key]
            if key in {"total_tokens", "turns", "wall_time"}
            else summary.get(key, 0.0)
        )

    header = "| Result | " + " | ".join(item[0] for item in metrics) + " | Valid |"
    divider = "| --- | " + " | ".join("---:" for _ in metrics) + " | --- |"
    ref_values = [value(reference, ref_agent, key) for _, key, _, _ in metrics]
    candidate_values = [
        value(candidate, candidate_agent, key) for _, key, _, _ in metrics
    ]

    def formatted(values: list[float]) -> str:
        fields = []
        for metric, current in zip(metrics, values):
            _, key, _, precision = metric
            fields.append(
                f"{int(current):,}"
                if key in {"total_tokens", "turns"}
                else _validation_cell(current, precision=precision)
            )
        return " | ".join(fields)

    deltas = " | ".join(
        _validation_delta(current, previous, points=points, precision=precision)
        for (_, _, points, precision), current, previous in zip(
            metrics, candidate_values, ref_values
        )
    )
    lines = [
        "# Self-Harness validation comparison",
        "",
        f"Reference: {run['reference']['version']} | Candidate: {run['candidate']['version']}",
        "Held-out tasks are evaluated only; this command never tunes, promotes or changes the active version.",
        "",
        header,
        divider,
        f"| {run['reference']['version']} | {formatted(ref_values)} | {reference['evaluation_valid']} |",
        f"| {run['candidate']['version']} | {formatted(candidate_values)} | {candidate['evaluation_valid']} |",
        f"| Δ candidate vs reference | {deltas} | - |",
        "",
        "Positive cost percentages mean the candidate is more expensive. Quality and reward use point deltas.",
        "",
        "## Task suites",
        "",
        f"- Reference manifest: {run['reference']['manifest_path']}",
        f"- Candidate manifest: {run['candidate']['manifest_path']}",
        "",
    ]
    return "\n".join(lines)


def validate_versions(
    *,
    settings: dict[str, str],
    candidate_version: str | None = "active",
    reference_version: str | None = "parent",
    requested_tasks: list[str] | None = None,
    task_timeout: int = 900,
    task_turns: int = 40,
) -> Path:
    """Compare two versions once on held-out validation tasks without promotion."""
    if task_timeout < 1 or task_turns < 1:
        raise ValueError("Validation runtime limits must be positive")
    ensure_baseline()
    candidate = (
        active_config()
        if candidate_version in {None, "active"}
        else load_version(str(candidate_version))
    )
    if reference_version in {None, "parent"}:
        parent = candidate.get("parent")
        if not parent:
            raise ValueError(
                f"{candidate['version']} has no parent; pass --reference v000 or another version"
            )
        reference = load_version(str(parent))
    else:
        reference = load_version(str(reference_version))
    if reference["version"] == candidate["version"]:
        raise ValueError(
            "Validation reference and candidate must be different versions"
        )
    tasks = load_validation_tasks(requested_tasks)
    for task in tasks:
        task["timeout_seconds"] = min(task["timeout_seconds"], task_timeout)
        task["max_turns"] = min(task["max_turns"], task_turns)
    reference_suite = run_bench(settings=settings, config=reference, tasks=tasks)
    score_suite(reference_suite, reference_suite)
    write_json(Path(reference_suite["manifest_path"]), reference_suite)
    candidate_suite = run_bench(settings=settings, config=candidate, tasks=tasks)
    score_suite(candidate_suite, reference_suite)
    write_json(Path(candidate_suite["manifest_path"]), candidate_suite)
    run_dir = (
        VALIDATION_RUNS_DIR
        / f"validation-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    )
    run_dir.mkdir(parents=True)
    run = {
        "mode": "heldout-validation",
        "tasks": [{"id": task["id"], "source": task["source_path"]} for task in tasks],
        "reward_config": candidate_suite["reward_config"],
        "reference": {
            "version": reference["version"],
            "manifest_path": reference_suite["manifest_path"],
            "summary": reference_suite["summary"],
        },
        "candidate": {
            "version": candidate["version"],
            "manifest_path": candidate_suite["manifest_path"],
            "summary": candidate_suite["summary"],
        },
    }
    write_json(run_dir / "run.json", run)
    report_path = run_dir / "report.md"
    report_path.write_text(_render_validation_report(run), encoding="utf-8")
    print(f"Validation complete. Report: {report_path}")
    return report_path


def _tuner_audit(
    rounds: list[dict[str, Any]], proposals: dict[int, Any]
) -> dict[str, Any]:
    """Project the shared round state into the readable tuner audit.

    Decisions live only in rounds; this view cannot drift from run.json.
    Raw proposals are kept separately from the runnable merged configs.
    """
    records = []
    for entry in rounds:
        record = {
            key: entry[key]
            for key in (
                "round",
                "parent",
                "decision",
                "changes",
                "impact_vs_incumbent",
                "reason",
                "reward_gain",
                "promoted_version",
                "error",
            )
            if key in entry
        }
        record.update(entry.get("tuner", {}))
        if "config" in entry:
            record["hypothesis"] = entry["config"]["hypothesis"]
        if entry["round"] in proposals:
            record["proposal"] = proposals[entry["round"]]
        records.append(record)
    return {"rounds": records}


def _trim(value: Any, limit: int) -> str:
    text = str(value or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _compact_judge(judge: dict[str, Any]) -> dict[str, Any]:
    """Keep the direct judge audit decision-focused; full traces stay in manifests."""
    evidence = [
        {
            "requirement": _trim(item.get("requirement"), 180),
            "observation": _trim(item.get("observation"), 420),
            "reference": _trim(item.get("reference"), 220),
            "verified": item.get("verified"),
        }
        for item in judge.get("evidence", [])[:5]
        if isinstance(item, dict)
    ]
    inspections = []
    for item in judge.get("workspace_inspection", []):
        if not isinstance(item, dict):
            continue
        arguments = (
            item.get("arguments") if isinstance(item.get("arguments"), dict) else {}
        )
        result = item.get("result") if isinstance(item.get("result"), dict) else {}
        target = arguments.get(
            "path", arguments.get("command", arguments.get("query", ""))
        )
        inspections.append(
            {
                "tool": item.get("name"),
                "target": _trim(target, 180),
                "success": result.get("success"),
                "exit_code": result.get("exit_code"),
                "error": _trim(result.get("error"), 180),
            }
        )
    return {
        "evaluation_status": judge.get("evaluation_status"),
        "passed": judge.get("passed"),
        "score": judge.get("score"),
        "reason": _trim(judge.get("reason"), 700),
        "evidence": evidence,
        "artifacts": judge.get("artifacts", []),
        # Evidence explains the verdict. A small sample only confirms how much
        # inspection happened; raw inspection history remains in the manifest.
        "inspection_count": len(inspections),
        "inspection_samples": inspections[:8],
        "model": judge.get("model"),
        "models": judge.get("models", []),
        "model_usage": judge.get("model_usage", {}),
        "api_retries": judge.get("api_retries", 0),
    }


def _history_record(entry: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Keep the next tuner call focused on observed change, not reward internals."""
    return {
        "round": entry["round"],
        "parent": entry["parent"],
        "decision": entry["decision"],
        "hypothesis": entry["config"]["hypothesis"],
        "changes": entry["changes"],
        "impact_vs_incumbent": entry["impact_vs_incumbent"],
        "summary": candidate["summary"],
        "feedback": [
            {
                "task_id": task["task_id"],
                "judge": {
                    key: task["judge"].get(key)
                    for key in ("score", "evidence", "reward_hacking")
                },
            }
            for task in candidate["tasks"]
        ],
    }


def _render_report(run: dict[str, Any]) -> str:
    """One readable view: initial/final metrics and one row per round, no raw traces."""
    lines = [
        "# Self-Harness optimization",
        "",
        f"Active: {run['active_version']} | Stage: {run['stage']}",
        "",
        f"{'One task' if run.get('mode') == 'single-task' else 'The seven-task calibration suite' if run.get('mode') == 'calibration-suite' else 'The retained task suite'} feeds tuner and selects by reward; costs use the fixed run-start baseline.",
        "",
        "| Suite | Quality | Hacking penalty | Tokens | Turns | Time (s) | Reward | Valid |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for label, suite in run["suites"].items():
        if label.startswith("candidate-"):
            continue
        s, a = suite["summary"], suite["summary"]["agent"]
        lines.append(
            f"| {label} | {s['average_score']:.3f} | {s.get('reward_hacking_penalty', 0.0):.3f} | {a['total_tokens']:,} | {a['turns']} | {a['wall_time']:.1f} | {s['reward']:.4f} | {s['evaluation_valid']} |"
        )
    lines.extend(
        [
            "",
            "Each round has one raw-metric row and one delta row against the incumbent used for its decision. Positive cost percentages mean the candidate is more expensive; a lower hacking penalty is better.",
            "",
            "| Round | Decision | Quality | Hacking penalty | Tokens | Turns | Time (s) | Reward | Reason |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    baseline = run["suites"].get("baseline", {}).get("summary", {})

    def metric_value(summary: dict[str, Any], metric: str) -> float | None:
        if not summary:
            return None
        if metric in {"quality", "reward", "reward_hacking_penalty"}:
            key = {
                "quality": "average_score",
                "reward": "reward",
                "reward_hacking_penalty": "reward_hacking_penalty",
            }[metric]
            value = summary.get(key, 0.0)
        else:
            value = summary.get("agent", {}).get(metric)
        return None if value is None else float(value)

    def comparison(
        candidate: dict[str, Any], reference: dict[str, Any], metric: str
    ) -> float | None:
        if not candidate or not reference:
            return None
        current, previous = (
            metric_value(candidate, metric),
            metric_value(reference, metric),
        )
        if current is None or previous is None:
            return None
        if metric in {"quality", "reward", "reward_hacking_penalty"}:
            return current - previous
        return None if previous == 0 else (current - previous) / previous

    def metric_cell(summary: dict[str, Any], metric: str, *, digits: int = 3) -> str:
        value = metric_value(summary, metric)
        if value is None:
            return "-"
        if metric == "total_tokens":
            shown = f"{int(value):,}"
        elif metric == "turns":
            shown = f"{int(value)}"
        else:
            shown = f"{value:.{digits}f}"
        return shown

    def delta_cell(
        summary: dict[str, Any],
        incumbent: dict[str, Any],
        metric: str,
        *,
        digits: int = 3,
    ) -> str:
        change = comparison(summary, incumbent, metric)
        if change is None:
            return "-"
        if metric in {"quality", "reward", "reward_hacking_penalty"}:
            return f"Δ {change:+.{digits}f}"
        return f"{change:+.1%}"

    for r in run["rounds"]:
        summary = r.get("candidate_summary", {})
        incumbent = r.get("incumbent_summary", baseline)
        reason = str(r.get("reason", "-")).replace("\n", " ").replace("|", "/")
        lines.append(
            f"| {r['round']} | {r['decision']} | {metric_cell(summary, 'quality')} | {metric_cell(summary, 'reward_hacking_penalty')} | {metric_cell(summary, 'total_tokens')} | {metric_cell(summary, 'turns')} | {metric_cell(summary, 'wall_time', digits=1)} | {metric_cell(summary, 'reward', digits=4)} | {reason} |"
        )
        lines.append(
            f"| -> vs {r.get('parent', 'incumbent')} |  | {delta_cell(summary, incumbent, 'quality')} | {delta_cell(summary, incumbent, 'reward_hacking_penalty')} | {delta_cell(summary, incumbent, 'total_tokens')} | {delta_cell(summary, incumbent, 'turns')} | {delta_cell(summary, incumbent, 'wall_time', digits=1)} | {delta_cell(summary, incumbent, 'reward', digits=4)} |  |"
        )
        if r.get("error"):
            message = str(r["error"]).replace("\n", " ").replace("|", "/")
            lines.append(f"\nRound {r['round']} error: {message}\n")
    if run.get("error"):
        lines.extend(["", f"Error: {run['error']}"])
    if run.get("stop_reason"):
        lines.extend(["", f"Stopped: {run['stop_reason']}"])
    lines.extend(
        [
            "",
            "Details and suite audit paths: [run.json](run.json).",
            "Judge verdicts/evidence: [judge.json](judge.json). Tuner hypotheses/proposals: [tuner.json](tuner.json).",
        ]
    )
    return "\n".join(lines) + "\n"


def optimize(
    *,
    settings: dict[str, str],
    requested_tasks: list[str] | None = None,
    overnight_suite: bool = False,
    calibration_suite: bool = False,
    control_rollouts: int = 0,
    max_rounds: int = 3,
    patience_limit: int = 2,
    min_reward_gain: float = 0.0,
    task_timeout: int = 900,
    task_turns: int = 40,
) -> Path:
    """One selected task or retained suite; active rollout plus each candidate.

    The run-start active result is the fixed cost reference for all rounds.
    Promoted results become the incumbent without extra re-evaluation.

    Canonical trajectories live once per suite. A run has report.md, run.json,
    judge.json and tuner.json for direct inspection of verdicts and proposals.
    """
    _validate_optimization_request(
        overnight_suite=overnight_suite,
        calibration_suite=calibration_suite,
        control_rollouts=control_rollouts,
        max_rounds=max_rounds,
        patience_limit=patience_limit,
        min_reward_gain=min_reward_gain,
        task_timeout=task_timeout,
        task_turns=task_turns,
    )
    mode = _experiment_mode(
        overnight_suite=overnight_suite, calibration_suite=calibration_suite
    )
    tasks = _select_experiment_tasks(
        requested_tasks=requested_tasks,
        overnight_suite=overnight_suite,
        calibration_suite=calibration_suite,
    )
    _apply_task_limits(tasks, timeout=task_timeout, turns=task_turns)
    ensure_baseline()
    selected_config = active_config()
    active_name = selected_config["version"]
    run_dir = RUNS_DIR / f"run-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    run_dir.mkdir(parents=True)
    report_path = run_dir / "report.md"
    run: dict[str, Any] = {
        "active_version": active_name,
        "stage": "baseline",
        "suites": {},
        "rounds": [],
        "mode": mode,
        "baseline_version": active_name,
        "reward_config": dict(REWARD_CONFIG),
        "plan": {
            "tasks": _task_plan(tasks),
            "max_rounds": max_rounds,
            "patience": patience_limit,
            "min_reward_gain": min_reward_gain,
            "control_rollouts": control_rollouts,
            "model_candidates": settings["model_candidates"],
        },
    }
    judge_audit: dict[str, Any] = {"suites": {}}
    tuner_proposals: dict[int, Any] = {}

    def checkpoint(stage: str | None = None) -> None:
        if stage:
            run["stage"] = stage
        run["active_version"] = active_name
        write_json(run_dir / "run.json", run)
        write_json(run_dir / "judge.json", judge_audit)
        write_json(run_dir / "tuner.json", _tuner_audit(run["rounds"], tuner_proposals))
        report_path.write_text(_render_report(run), encoding="utf-8")
        state = read_json(STATE_PATH)
        state["latest_report"] = str(report_path)
        write_json(STATE_PATH, state)

    def bench(
        config: dict[str, Any], label: str, reference: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        checkpoint(f"running {label}")
        suite = run_bench(settings=settings, config=config, tasks=tasks)
        judge_audit["suites"][label] = {
            "version": config["version"],
            "manifest_path": suite["manifest_path"],
            "tasks": [
                {
                    "task_id": task["task_id"],
                    "judge": _compact_judge(task["judge"]),
                    **(
                        {
                            "judge_previous_attempts": [
                                _compact_judge(attempt)
                                for attempt in task["judge_previous_attempts"]
                            ]
                        }
                        if "judge_previous_attempts" in task
                        else {}
                    ),
                }
                for task in suite["tasks"]
            ],
        }
        score_suite(suite, reference or suite)
        write_json(Path(suite["manifest_path"]), suite)
        run["suites"][label] = {
            "manifest_path": suite["manifest_path"],
            "version": config["version"],
            "summary": suite["summary"],
        }
        checkpoint(f"finished {label}")
        return suite

    checkpoint()
    baseline = bench(selected_config, "baseline")
    if not baseline["summary"]["evaluation_valid"]:
        run["error"] = (
            "Baseline judge evaluation incomplete; inspect suite audit and rerun."
        )
        checkpoint("baseline error")
        raise RuntimeError(f"{run['error']} Report: {report_path}")
    active = baseline
    control_rounds: list[dict[str, Any]] = []
    for control_number in range(1, control_rollouts + 1):
        control = bench(selected_config, f"control-{control_number:03d}", baseline)
        control_rounds.append(
            {
                "control": control_number,
                "summary": control["summary"],
                "impact_vs_baseline": _tuner_impact(
                    control["summary"], baseline["summary"]
                ),
                "reward_delta": (
                    control["summary"]["reward"] - baseline["summary"]["reward"]
                ),
            }
        )
    if control_rounds:
        run["control_rounds"] = control_rounds
        checkpoint("control measurement complete")
    history: list[dict[str, Any]] = []
    patience = 0

    for round_number in range(1, max_rounds + 1):
        entry: dict[str, Any] = {
            "round": round_number,
            "parent": active_name,
            "decision": "RUNNING",
        }
        run["rounds"].append(entry)
        try:
            checkpoint(f"round {round_number}: tuner")
            candidate_config, tuner_result = propose_candidate(
                settings=settings, active=selected_config, suite=active, history=history
            )
            candidate_config["version"] = f"candidate-r{round_number:03d}"
            # Runnable merged config stays in run.json; the raw proposal has its own audit.
            entry["config"] = candidate_config
            entry["tuner"] = {
                key: value for key, value in tuner_result.items() if key != "raw"
            }
            tuner_proposals[round_number] = tuner_result.get("raw")
            checkpoint(f"round {round_number}: proposed")
            candidate = bench(
                candidate_config, f"candidate-{round_number:03d}", baseline
            )
            entry["candidate_summary"] = candidate["summary"]
            entry["incumbent_summary"] = active["summary"]
            entry["changes"] = summarize_candidate_change(
                selected_config, candidate_config
            )
            entry["impact_vs_incumbent"] = _tuner_impact(
                candidate["summary"], active["summary"]
            )
            entry["reward_gain"] = (
                candidate["summary"]["reward"] - active["summary"]["reward"]
            )
            accepted, reason = decide(
                candidate, active, min_reward_gain=min_reward_gain
            )
            entry["reason"] = reason
            if accepted:
                selected_config = save_promoted_version(candidate_config, active_name)
                active_name = selected_config["version"]
                active = candidate
                entry["promoted_version"] = active_name
                patience = 0
            else:
                patience += 1
            entry["decision"] = "PROMOTED" if accepted else "REJECTED"
            history.append(_history_record(entry, candidate))
            print(f"Round {round_number}: {entry['decision']} | {reason}")
        except Exception as exc:
            entry["decision"], entry["error"] = "ERROR", str(exc)
            patience += 1
            print(f"Round {round_number}: ERROR | {exc}")
        checkpoint(f"round {round_number}: {entry['decision'].lower()}")
        if patience >= patience_limit:
            run["stop_reason"] = "patience reached"
            break
    else:
        run["stop_reason"] = "max rounds reached"
    run["selected_summary"] = active["summary"]
    run["selected_manifest_path"] = active["manifest_path"]
    checkpoint("complete")
    print(
        f"Optimization complete. Active version: {active_name}. Report: {report_path}"
    )
    return report_path


def latest_report() -> Path:
    """Return the report path recorded in state."""
    ensure_baseline()
    raw = read_json(STATE_PATH).get("latest_report")
    if not raw:
        raise RuntimeError("No optimization report exists yet. Run optimize first.")
    path = Path(str(raw))
    if not path.exists():
        raise RuntimeError(f"Latest report is missing: {path}")
    return path
