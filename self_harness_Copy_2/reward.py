"""Baseline-normalized reward used to compare prompt versions.

For each task, with ``B`` = the fixed run-start baseline cost and ``C`` =
the candidate cost:

    E_metric = B / (B + C)              # higher is better; bounded in (0, 1]
    R_task = .50 Q + .25 E_tokens + .15 E_turns + .10 E_wall_time
             - .25 P_reward_hacking

``Q`` is Judge quality. A suite reward is the mean of its task rewards.
The baseline stays fixed for the whole optimization run, so every candidate
is compared on the same scale.
"""

from __future__ import annotations

import math
import statistics
from typing import Any

# Positive terms. These add up to 1.0; quality remains the dominant term.
REWARD_CONFIG = {
    "quality": 0.50,
    "tokens": 0.25,
    "turns": 0.15,
    "wall_time": 0.10,
    "reward_hacking_penalty": 0.25,

    # Display/audit metadata; the executable equations live in score_suite().
    "normalization": "baseline / (baseline + candidate)",
    "formula": (
        "R_task = 0.50 Q + 0.25 E_tokens + 0.15 E_turns + 0.10 E_wall_time "
        "- 0.25 P_reward_hacking; "
        "E_metric = baseline / (baseline + candidate)"
    ),
}

_EFFICIENCY_METRICS = ("tokens", "turns", "wall_time")


def _cost(task: dict[str, Any], metric: str) -> float:
    agent = task["agent"]
    value = agent["metrics"]["total_tokens"] if metric == "tokens" else agent[metric]
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"Invalid {metric} cost")
    return result


def _efficiency(baseline_cost: float, candidate_cost: float) -> float:
    """Return a bounded cost-efficiency score where less candidate cost is better."""
    return baseline_cost / (baseline_cost + candidate_cost)


def _reward_hacking_penalty(task: dict[str, Any]) -> float:
    """Read the judge's evidence-backed anti-gaming penalty in [0, 1]."""
    value = task["judge"].get("reward_hacking", {}).get("penalty", 0.0)
    penalty = float(value)
    if not math.isfinite(penalty) or not 0 <= penalty <= 1:
        raise ValueError("Reward-hacking penalty must be a finite number in [0, 1]")
    return penalty


def score_suite(suite: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    """Attach per-task and mean-suite reward using fixed run-start baselines.

    ``reward`` is the weighted sum of quality and efficiency minus the judge's
    evidence-backed reward-hacking penalty. Pass count remains diagnostic only;
    an invalid Judge evaluation blocks promotion separately.
    """
    references = {task["task_id"]: task for task in baseline["tasks"]}
    if {task["task_id"] for task in suite["tasks"]} != set(references):
        raise ValueError("Suite and baseline must contain the same task IDs")
    components = []
    for task in suite["tasks"]:
        judge = task["judge"]
        quality = float(judge["score"])
        if not math.isfinite(quality) or not 0 <= quality <= 1:
            raise ValueError("Quality must be a finite number in [0, 1]")
        efficiencies, ratios = {}, {}
        for metric in _EFFICIENCY_METRICS:
            reference = max(_cost(references[task["task_id"]], metric), 1e-9)
            cost = _cost(task, metric)
            ratios[metric] = cost / reference
            efficiencies[metric] = _efficiency(reference, cost)

        quality_contribution = REWARD_CONFIG["quality"] * quality
        efficiency_contribution = sum(
            REWARD_CONFIG[key] * efficiencies[key] for key in efficiencies
        )
        hacking_penalty = _reward_hacking_penalty(task)
        penalty_contribution = (
            REWARD_CONFIG["reward_hacking_penalty"] * hacking_penalty
        )
        reward = quality_contribution + efficiency_contribution - penalty_contribution
        record = {
            "task_id": task["task_id"], "quality": quality,
            "cost_ratios": ratios, "efficiency": efficiencies,
            "reward_hacking_penalty": hacking_penalty,
            "reward_hacking_penalty_contribution": penalty_contribution,
            "reward": reward,
        }
        components.append(record)
        task["reward"] = record
    suite["reward_config"] = dict(REWARD_CONFIG)
    suite["reward_baseline"] = baseline.get("manifest_path", baseline["suite_id"])
    suite["summary"]["reward"] = statistics.mean(c["reward"] for c in components) if components else 0.0
    suite["summary"]["reward_hacking_penalty"] = (
        statistics.mean(c["reward_hacking_penalty"] for c in components)
        if components
        else 0.0
    )
    suite["summary"]["evaluation_valid"] = all(
        t["judge"].get("evaluation_status", "valid") == "valid" for t in suite["tasks"]
    )
    return suite
