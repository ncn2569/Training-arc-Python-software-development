"""Run the seven-task train calibration suite and summarize observed deltas.

The normal runtime retries a failed provider request without resetting an
agent. This launcher is only a second guard for a process-level calibration
failure (for example, an unavailable provider during the baseline suite).
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO

from ..cli import main
from ..config import ARTIFACTS_DIR


class Tee:
    def __init__(self, terminal: TextIO, log: TextIO) -> None:
        self.terminal, self.log = terminal, log

    def write(self, text: str) -> int:
        self.terminal.write(text)
        self.log.write(text)
        self.flush()
        return len(text)

    def flush(self) -> None:
        self.terminal.flush()
        self.log.flush()


def _has_option(arguments: list[str], option: str) -> bool:
    return any(value == option or value.startswith(f"{option}=") for value in arguments)


def _with_defaults(arguments: list[str]) -> list[str]:
    result = list(arguments)
    if not _has_option(result, "--max-rounds"):
        result.extend(["--max-rounds", "8"])
    if not _has_option(result, "--patience"):
        # Calibration needs observed deltas, so do not stop after two ordinary rejects.
        result.extend(["--patience", "8"])
    if not _has_option(result, "--min-reward-gain"):
        # Measure before selecting a non-zero promotion threshold.
        result.extend(["--min-reward-gain", "0"])
    if not _has_option(result, "--control-rollouts"):
        # Two same-config suites make sampling drift observable before tuning.
        result.extend(["--control-rollouts", "2"])
    return result


def _quantile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    index = (len(ordered) - 1) * percentile
    lower, upper = int(index), min(int(index) + 1, len(ordered) - 1)
    fraction = index - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def write_delta_report(report_path: Path) -> Path:
    """Create a transparent reward-delta calibration report beside run.json.

    Rejected deltas with effectively flat quality are a useful *screening*
    proxy for a promotion floor, but are not a statistical estimate of sampling
    noise. The report deliberately presents the distribution rather than
    silently changing ``min_reward_gain``.
    """
    run_path = report_path.with_name("run.json")
    run = json.loads(run_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    control_deltas = [
        float(control["reward_delta"])
        for control in run.get("control_rounds", [])
        if _number(control.get("reward_delta")) is not None
    ]
    flat_quality_rejected: list[float] = []
    for round_data in run.get("rounds", []):
        gain = _number(round_data.get("reward_gain"))
        candidate = round_data.get("candidate_summary", {})
        incumbent = round_data.get("incumbent_summary", {})
        quality_delta = _number(candidate.get("average_score"))
        prior_quality = _number(incumbent.get("average_score"))
        quality_delta = (
            None
            if quality_delta is None or prior_quality is None
            else quality_delta - prior_quality
        )
        if gain is not None:
            rows.append(
                {
                    "round": round_data.get("round"),
                    "decision": round_data.get("decision"),
                    "reward_gain": gain,
                    "quality_delta": quality_delta,
                    "tokens_delta": round_data.get("impact_vs_incumbent", {})
                    .get("agent", {})
                    .get("total_tokens", {})
                    .get("relative_change"),
                    "turns_delta": round_data.get("impact_vs_incumbent", {})
                    .get("agent", {})
                    .get("turns", {})
                    .get("relative_change"),
                    "time_delta": round_data.get("impact_vs_incumbent", {})
                    .get("agent", {})
                    .get("wall_time", {})
                    .get("relative_change"),
                }
            )
            if (
                round_data.get("decision") == "REJECTED"
                and quality_delta is not None
                and abs(quality_delta) <= 0.01
            ):
                flat_quality_rejected.append(abs(gain))

    lines = [
        "# Reward-delta calibration",
        "",
        f"Source run: `{run_path.name}`",
        f"Mode: `{run.get('mode')}` | Baseline: `{run.get('baseline_version')}`",
        f"Model route: `{', '.join(run.get('plan', {}).get('model_candidates', [])) or 'unknown'}`",
        "",
        "The optimization reward uses the same fixed per-task run-start baseline for every candidate. Each task has a fresh seed workspace; suite reward is the mean task reward, so the seven task domains have equal weight. Agent Time excludes provider failure/backoff/retry delay; `suite_wall_time` remains operational elapsed time only.",
        "",
        "| Round | Decision | Reward Δ vs incumbent | Quality Δ | Tokens Δ | Turns Δ | Time Δ |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    if len(run.get("plan", {}).get("model_candidates", [])) > 1:
        lines.extend(
            [
                "",
                "> Note: this run permits gateway fallback models for availability. Inspect the recorded model route and per-task model audit when interpreting small deltas.",
            ]
        )
    for row in rows:
        def value(name: str, percent: bool = False) -> str:
            current = row[name]
            if current is None:
                return "-"
            return f"{current:+.1%}" if percent else f"{current:+.4f}"

        lines.append(
            f"| {row['round']} | {row['decision']} | {value('reward_gain')} | "
            f"{value('quality_delta')} | {value('tokens_delta', True)} | "
            f"{value('turns_delta', True)} | {value('time_delta', True)} |"
        )

    all_abs = [abs(row["reward_gain"]) for row in rows]
    lines.extend(["", "## Interpreting a promotion floor", ""])
    if control_deltas:
        control_abs = [abs(delta) for delta in control_deltas]
        lines.append(
            f"- Same-config control drift (n={len(control_deltas)}): deltas `{', '.join(f'{delta:+.4f}' for delta in control_deltas)}`; max absolute drift `{max(control_abs):.4f}`. A future `--min-reward-gain` should exceed this only after confirming with more control runs."
        )
    else:
        lines.append("- No same-config control rollouts were recorded. Candidate deltas alone cannot distinguish prompt effect from sampling drift.")
    if all_abs:
        lines.append(f"- Observed absolute reward delta: median `{statistics.median(all_abs):.4f}`, p75 `{_quantile(all_abs, 0.75):.4f}`, max `{max(all_abs):.4f}`.")
    else:
        lines.append("- No completed candidate reward deltas were recorded.")
    if len(flat_quality_rejected) >= 2:
        lines.append(
            f"- Flat-quality rejected candidates (n={len(flat_quality_rejected)}): median absolute delta `{statistics.median(flat_quality_rejected):.4f}`, p75 `{_quantile(flat_quality_rejected, 0.75):.4f}`. Use this as a conservative screening range for a future `--min-reward-gain`, not as a proof of noise."
        )
    else:
        lines.append(
            "- Fewer than two flat-quality rejected candidates were observed; do not infer a noise floor yet. Repeat the same suite/config or inspect another overnight run before raising `--min-reward-gain`."
        )
    lines.extend(
        [
            "- This run has one rollout per version/task. Reward deltas combine true prompt effects and sampling variation; the report intentionally does not auto-change the threshold.",
            "",
        ]
    )
    output = report_path.with_name("reward-delta-calibration.md")
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def run() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--restart-attempts", type=int, default=2)
    launcher, forwarded = parser.parse_known_args(sys.argv[1:])
    if launcher.restart_attempts < 0:
        raise SystemExit("--restart-attempts must be nonnegative")
    command = _with_defaults(forwarded)
    if "--dry-run" in command:
        return main(["calibrate", *command])

    log_dir = ARTIFACTS_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"overnight-calibration-{datetime.now():%Y%m%d-%H%M%S-%f}.log"
    print(f"Overnight calibration log: {log_path}")
    with log_path.open("w", encoding="utf-8") as log:
        with redirect_stdout(Tee(sys.stdout, log)), redirect_stderr(Tee(sys.stderr, log)):
            for attempt in range(1, launcher.restart_attempts + 2):
                print(f"Calibration launcher attempt {attempt}/{launcher.restart_attempts + 1}")
                result = main(["calibrate", *command])
                if result == 0:
                    from ..optimizer import latest_report

                    delta_report = write_delta_report(latest_report())
                    print(f"Reward-delta calibration report: {delta_report}")
                    return 0
                if attempt <= launcher.restart_attempts:
                    print("Calibration process failed; retrying a fresh run in 30 seconds.")
                    time.sleep(30)
            print(f"Calibration failed after {launcher.restart_attempts + 1} launcher attempts.")
            return result


if __name__ == "__main__":
    raise SystemExit(run())
