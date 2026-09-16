"""Run an immutable agent configuration against one or more clean task workspaces.

The benchmark owns workspace lifecycle and persistence. The agent owns task work;
the judge owns quality; reward scoring is deliberately left to ``optimizer`` so
the same raw suite can be used as a baseline, candidate, or control rollout.
"""

from __future__ import annotations

import statistics
import time
import uuid
from pathlib import Path
from typing import Any

from .config import SUITES_DIR, WORKSPACE_DIR, write_json
from .judge import JUDGE_INSTRUCTIONS, judge_task
from .runtime import prepare_workspace, run_agent


# These are agent-side costs. Judge usage stays separate so tuning cannot win
# merely by making evaluation cheaper or less thorough.
_AGENT_METRIC_KEYS = (
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "api_retries",
    "provider_retry_cycles",
    "tool_calls",
    "tool_errors",
    "tool_retries",
)


def _suite_id() -> str:
    """Return a unique ID shared by all task workspaces in one suite."""
    return f"suite-{uuid.uuid4().hex[:16]}"


def _aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Reduce task results into the cost/quality view consumed by reward scoring."""
    totals = {
        key: sum(int(item["agent"]["metrics"][key]) for item in results)
        for key in _AGENT_METRIC_KEYS
    }
    # Provider failures are operational audit data, not an agent reward cost.
    totals["provider_failure_seconds"] = sum(
        float(item["agent"]["metrics"]["provider_failure_seconds"])
        for item in results
    )
    totals["turns"] = sum(int(item["agent"]["turns"]) for item in results)
    totals["wall_time"] = sum(float(item["agent"]["wall_time"]) for item in results)
    passed = sum(1 for item in results if item["judge"]["passed"])
    scores = [float(item["judge"]["score"]) for item in results]
    return {
        "task_count": len(results),
        "pass_count": passed,
        "pass_rate": passed / len(results) if results else 0.0,
        "average_score": statistics.mean(scores) if scores else 0.0,
        "agent": totals,
        "judge_total_tokens": sum(
            int(item["judge"]["model_usage"]["total_tokens"]) for item in results
        ),
    }


def _judge_with_one_recheck(
    *,
    settings: dict[str, str],
    task: dict[str, Any],
    workspace: Path,
    agent: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Judge once and rejudge an invalid evaluator result without rerunning the agent."""
    attempts: list[dict[str, Any]] = []
    for attempt_number in range(2):
        judge = judge_task(
            settings=settings,
            task=task,
            workspace=workspace,
            agent_result=agent,
        )
        attempts.append(judge)
        if judge.get("evaluation_status", "valid") == "valid":
            break
        if attempt_number == 0:
            print(
                f"Judge evaluation error for {task['id']}; retained workspace, "
                f"bounded rejudge: {judge['reason']}"
            )

    final_judge = attempts[-1]
    if len(attempts) == 1:
        return final_judge, attempts

    # Retain all evaluator cost for audit, while reward continues to consider
    # only agent costs. ``mixed`` makes the retry visible to report consumers.
    total_usage = {
        key: sum(int(item["model_usage"][key]) for item in attempts)
        for key in ("input_tokens", "output_tokens", "total_tokens")
    }
    return (
        {
            **final_judge,
            "model_usage": {
                **final_judge["model_usage"],
                **total_usage,
                "source": "mixed",
            },
            "api_retries": sum(int(item["api_retries"]) for item in attempts),
        },
        attempts,
    )


def _run_task(
    *,
    settings: dict[str, str],
    config: dict[str, Any],
    task: dict[str, Any],
    workspace: Path,
) -> dict[str, Any]:
    """Copy one seed, run the agent, and return its result plus a judge verdict."""
    prepare_workspace(task["seed_dir"], workspace)
    agent = run_agent(
        settings=settings,
        config=config,
        task_prompt=task["prompt"],
        workspace=workspace,
        max_turns=task["max_turns"],
        timeout_seconds=task["timeout_seconds"],
        label=f"{task['id']} / {config['version']}",
    )
    if agent["status"] == "model_error":
        # No partial score: the provider retry policy could not obtain an agent
        # turn, so this suite is not a comparable measurement.
        raise RuntimeError(
            f"Provider retries exhausted for {task['id']}; no judge or reward metrics were recorded."
        )
    judge, attempts = _judge_with_one_recheck(
        settings=settings, task=task, workspace=workspace, agent=agent
    )
    result = {
        "task_id": task["id"],
        "task_source": task["source_path"],
        "workspace_path": str(workspace),
        "agent": agent,
        "judge": judge,
    }
    if len(attempts) > 1:
        result["judge_previous_attempts"] = attempts[:-1]
    return result


def run_bench(
    *, settings: dict[str, str], config: dict[str, Any], tasks: list[dict[str, Any]]
) -> dict[str, Any]:
    """Evaluate one config on fresh workspaces and persist one canonical manifest.

    Output files are retained under ``workspace/<suite>/<task>``. The suite
    manifest records only enough metadata, trajectories, and judge evidence to
    audit that output without duplicating the files themselves.
    """
    suite_dir = SUITES_DIR / _suite_id()
    live_suite = WORKSPACE_DIR / suite_dir.name
    started = time.perf_counter()
    results = [
        _run_task(
            settings=settings,
            config=config,
            task=task,
            workspace=live_suite / task["id"],
        )
        for task in tasks
    ]
    manifest = {
        "config": config,
        "judge_instructions": JUDGE_INSTRUCTIONS,
        "task_contracts": [
            {**task, "seed_dir": str(task["seed_dir"])} for task in tasks
        ],
        "suite_id": suite_dir.name,
        "version": config["version"],
        "created_at": time.time(),
        # Operational elapsed time includes outages; task agent wall_time does
        # not, and is the value used for reward scoring.
        "suite_wall_time": time.perf_counter() - started,
        "tasks": results,
        "summary": _aggregate(results),
    }
    manifest_path = suite_dir / "manifest.json"
    write_json(manifest_path, manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
