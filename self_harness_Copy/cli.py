"""Command-line entry points for bench, optimize, report, and activate.

Keep this file intentionally thin: command parsing belongs here while all
benchmarking and promotion behavior stays in the focused modules.
"""

from __future__ import annotations

import argparse
import sys

from .config import active_version, model_settings, restore_active
from .optimizer import latest_report, optimize, run_benchmark, validate_versions
from .tasks import (
    DEFAULT_BENCH_TASK_PATH,
    load_calibration_tasks,
    load_optimization_tasks,
    load_overnight_tasks,
    load_validation_tasks,
)


def _tasks(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--task", action="append", dest="tasks", help="Task YAML path. Repeat to select multiple tasks.")


def _optimization_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--max-rounds", type=int, default=3)
    parser.add_argument("--patience", type=int, default=2)
    parser.add_argument("--task", action="append", dest="tasks", help="Optimize: exactly one YAML. Overnight: subset of three retained tasks. Calibrate: subset of seven source/train tasks.")
    parser.add_argument("--min-reward-gain", type=float, default=0.0, help="Absolute reward improvement required.")
    parser.add_argument("--task-timeout", type=int, default=900, help="Cap agent task time budget; checked between turns.")
    parser.add_argument("--task-turns", type=int, default=80)
    parser.add_argument("--dry-run", action="store_true", help="Print the task plan without API calls or changing state.")


def _validation_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--candidate", default="active", help="Version to evaluate; defaults to active")
    parser.add_argument("--reference", default="parent", help="Comparison version; defaults to candidate's parent")
    parser.add_argument("--task", action="append", dest="tasks", help="Task YAML path. Defaults to all held-out validation tasks.")
    parser.add_argument("--task-timeout", type=int, default=900)
    parser.add_argument("--task-turns", type=int, default=70)
    parser.add_argument("--dry-run", action="store_true", help="Print the validation plan without API calls.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Small self-improvement harness for the local coding agent")
    commands = parser.add_subparsers(dest="command", required=True)
    bench = commands.add_parser("bench", help="Run one config against task YAML files")
    bench.add_argument("--version", default="active", help="v000, v001, ... or active")
    _tasks(bench)
    optimize_parser = commands.add_parser("optimize", help="Evaluate baseline, tune, and promote efficient candidates")
    _optimization_options(optimize_parser)
    overnight = commands.add_parser("overnight", help="Run bounded optimization across the retained three-task suite")
    _optimization_options(overnight)
    calibrate = commands.add_parser("calibrate", help="Run bounded optimization across the seven-task source/train calibration suite")
    _optimization_options(calibrate)
    calibrate.add_argument("--control-rollouts", type=int, default=0, help="Extra active-version suite rollouts before tuning; estimates sampling drift without promotion")
    validate = commands.add_parser("validate", help="Compare versions on held-out validation tasks without promotion")
    _validation_options(validate)
    commands.add_parser("report", help="Print the latest optimization report")
    activate = commands.add_parser("activate", help="Switch the active version, including back to v000")
    activate.add_argument("version")
    args = parser.parse_args(argv)
    try:
        if args.command == "activate":
            restore_active(args.version)
            print(f"Active version: {active_version()}")
            return 0
        if args.command == "report":
            print(latest_report().read_text(encoding="utf-8"))
            return 0
        if args.command == "validate" and args.dry_run:
            tasks = load_validation_tasks(args.tasks)
            print(f"candidate={args.candidate}, reference={args.reference}")
            print(f"validation tasks: {', '.join(task['id'] for task in tasks)}")
            print(f"agent task budget <= {args.task_timeout}s (between turns), <= {args.task_turns} turns")
            print("Two fresh rollouts per selected task; no tuner, promotion, or active-version change.")
            return 0
        if args.command in {"optimize", "overnight", "calibrate"}:
            tasks = (
                load_calibration_tasks(args.tasks)
                if args.command == "calibrate"
                else load_overnight_tasks(args.tasks)
                if args.command == "overnight"
                else load_optimization_tasks(args.tasks)
            )
            print(f"tasks: {', '.join(task['id'] for task in tasks)}")
            print(f"max_rounds={args.max_rounds}, patience={args.patience}")
            print(f"agent task budget <= {args.task_timeout}s (between turns), <= {args.task_turns} turns")
            scope = "suite" if args.command in {"overnight", "calibrate"} else "task"
            print(f"One active baseline {scope} + at most {args.max_rounds} candidate {scope}s; the same {scope} feeds tuner and selects.")
            if args.dry_run:
                return 0
        settings = model_settings()
        if args.command == "bench":
            requested = args.tasks or [str(DEFAULT_BENCH_TASK_PATH)]
            result = run_benchmark(settings=settings, requested_tasks=requested, version=args.version)
            summary = result["summary"]
            print(f"Bench {result['suite_id']} ({result['version']}): pass={summary['pass_count']}/{summary['task_count']}, tokens={summary['agent']['total_tokens']}, turns={summary['agent']['turns']}, wall_time={summary['agent']['wall_time']:.2f}s")
            print(f"Manifest: {result['manifest_path']}")
            return 0
        if args.command == "validate":
            validate_versions(settings=settings, candidate_version=args.candidate,
                              reference_version=args.reference, requested_tasks=args.tasks,
                              task_timeout=args.task_timeout, task_turns=args.task_turns)
            return 0
        optimize(settings=settings, requested_tasks=args.tasks, overnight_suite=args.command == "overnight",
                 calibration_suite=args.command == "calibrate",
                 control_rollouts=args.control_rollouts if args.command == "calibrate" else 0,
                 max_rounds=args.max_rounds, patience_limit=args.patience,
                 min_reward_gain=args.min_reward_gain,
                 task_timeout=args.task_timeout, task_turns=args.task_turns)
        return 0
    except Exception as exc:
        print(f"self_harness error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
