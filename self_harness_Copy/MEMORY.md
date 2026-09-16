# Self-Harness — Current Session Handoff

## Maintenance rule

- Keep individual-task optimize, the three-task retained overnight suite, and the
  four readable run files; avoid additional layers/side files unless a concrete
  experiment change needs them.
- README is the current design map; update it alongside flow/schema/default changes.
- Round decisions are owned by optimizer's run state; tuner.json is projected
  from it by _tuner_audit(), without separately synchronized decision state.
- Tuner receives only the symbolic reward formula, observed metrics and Judge
  feedback. Do not expose coefficients, weighted reward totals or component costs
  through reward_config, summary, task rewards or history. Those remain in local audits.
- Reward uses `0.50Q + 0.25E_tokens + 0.15E_turns + 0.10E_time
  - 0.25P_reward_hacking`. Judge emits an evidence-backed `P_reward_hacking`
  in [0, 1]; it is 0 for ordinary bugs/incomplete work and nonzero only for
  verified evaluation manipulation. There are no penalty CLI flags.
- Tuner receives the symbolic penalty term plus judge findings/penalty, never
  the penalty weight. A candidate system prompt above 3x v000 prompt tokens is
  requested once more in a shorter form; a second oversized result is rejected.
- Model health check on 2026-09-14: deepseek/deepseek-v4-flash worked; Qwen had
  no gateway account and kCode returned no_available_workers. Route therefore
  temporarily contains DeepSeek only. Re-add a fallback only after it passes
  scripts.test_litellm_models.

## September 14: separate model audit files (current)

- User explicitly requested judge and tuner as separate files because they are
  central to observing the experiment. Every new optimization run now has four
  files: report.md, run.json, judge.json and tuner.json, updated at checkpoints.
- judge.json: suites[label] -> version, manifest_path, tasks[].judge with compact
  verdict/reason/evidence, inspection count plus at most eight samples,
  model/usage and prior failed attempts. Full inspection stays only in the suite
  manifest.
- tuner.json: rounds[] -> round/parent/hypothesis/raw JSON proposal/model/usage,
  final decision/reason/reward_gain/promoted_version/errors.
- Existing manifests keep complete task audits; no agent trajectories duplicated
  into these new files. No additional LLM calls and no per-round side folders.

## September 14: individual optimize plus retained overnight suite (current)

- User chose cost reduction over automatic train/val/test evaluation.
- Optimize uses exactly one --task (default telemetry_window_repair). Overnight uses
  telemetry_window_repair, expense_dashboard and fullstack_todo by default; render and
  heldout tasks are excluded. It may receive a subset of those three for a short check.
- Run the starting active once; use that result as the fixed reward cost baseline
  throughout this run. No extra v000 bench if active is already another version.
- Each round: one tuner proposal, one candidate task rollout + judge; the same
  result feeds tuner history and decide(candidate, incumbent). No val/final test.
- Promote replaces active/incumbent with the candidate result; reject retains it.
  Stop on max_rounds or consecutive rejection/error patience. No final rerun.
- Reward formula, judge evidence, fixed safety and prompt-only tuning constraints
  stay intact. Tuner explicitly avoids task-specific fitting.
- One optimize round = 1 candidate rollout + 1 tuner call; N rounds <= 1+N task
  rollouts. Overnight is three times that rollout count.
- New run.json: mode=single-task or overnight-suite, baseline_version, plan.tasks, suites.baseline,
  suites.candidate-NNN, rounds[].candidate_summary/decision/reason/reward_gain,
  selected_summary/selected_manifest_path and stop_reason.
- Runs have report.md/run.json plus the separate model audits described above;
  detailed agent trajectories live once in suites.
- Existing heldout task YAMLs and historical artifacts remain for manual bench/audit.
- Previous split-based processes already in memory must be interrupted with Ctrl+C
  before starting the new flow. State.json and README describe current behavior.

## September 13 implementation update (historical split-based flow)

- Runtime isolation is deferred by user choice; protections currently rely on prompts.
- State at implementation start is v000, next_version=1; always read artifacts/state.json.
  The v005/v006 records below describe a different historical state, not current artifacts.
- reward.py replaces quality-first decisions with baseline-normalized scalar reward:
  Q*(.60+.25 E_tokens+.10 E_turns+.05 E_time)-.25 hacking_penalty; E=b/(b+c).
- Train=original three tasks; val/test=three distinct variants each under tasks/heldout.
  Tuner gets train-only evidence/history; val reward selects; test is final-only.
- Judge emits requirement evidence and evidence-backed reward_hacking penalty/findings.
  Ordinary bugs/simplification are not hacking. Shape/type validation retries twice;
  actual evidence truth/coverage and hacking classification remain prompt-driven.
- Judge review uses factual tool metadata/exit status/bounded outputs, without reasoning,
  assistant narrative or usage. Tuner retains reasoning and structured train feedback.
- Overnight launcher: python -u -m self_harness.scripts.overnight --max-rounds 3 --patience 2
  Add --dry-run for an API-free plan. Logs under artifacts/logs; rounds checkpoint reports.
- Default agent caps: 900s (checked between turns) and 40 turns. No automatic resume.
- Shared model fallback remains unchanged. No real benchmark has been run for this update.
- See README.md for current behavior. The quality-first flow below is historical.
- Artifact simplification: new runs contain only report.md and run.json (plan,
  merged proposals, metrics, errors and suite references). Canonical detailed
  trajectories stay in artifacts/suites. No per-round audit folders, suite copies,
  history/plan/error side files, or local .self_harness_result.json are generated.
  Existing historical files are retained. Tuner raw proposal is omitted from disk
  because the merged config is retained; successful judge inspections are not duplicated.

Use this file to resume work in another chat. The project root is
`D:\Inter-K`; the experiment is `D:\Inter-K\self_harness`.

## Historical state (older experiment; state.json is authoritative)

```text
active_version: v005
next_version:   7
latest report:  artifacts/optimization-runs/run-20260911-095736-4a5f7c/report.md
```

`v006.json` still exists but was manually retired by switching active back to
`v005`:

```powershell
python -m self_harness.cli activate v005
```

Do not reuse version numbers. A future promotion should become `v007` because
`state.json.next_version` is 7.

## Why v006 was retired

`v006` was promoted in `run-20260911-095736-4a5f7c`, round 3, on **only one
task**: `fullstack_todo`. It passed (`0.95`) with excellent observed efficiency:

```text
v005 active: 115,617 tokens, 6 turns, 89.6 s
v006 sample:  45,581 tokens, 3 turns, 55.5 s
```

However, `v006` has full-stack-specific global instructions: required frontend
file list, Dockerfile COPY checks, API client/styles/nginx requirements, and
file-existence scans. It is likely reward-hacking/overfitting to
`fullstack_todo`, not a proven general improvement. Its score also remained
`0.95`, so promotion was solely an efficiency win in one stochastic rollout.

The optimizer currently has no retired-version memory or blacklist. Starting
from `v005` prevents use of v006 but does not stop tuner from rediscovering a
similar candidate as `v007`. If asked to fix this, add explicit retirement
metadata/reasons and include it in tuner input plus a promotion guard.

## Experiment intent

- Tune only system prompt, tool description, and parameter descriptions.
- Never tune tool names, JSON types, required fields, or Python handlers.
- Use real LiteLLM calls for agent runtime, judge, and tuner.
- Quality before agent efficiency: pass count → score guard → tokens → turns →
  wall time.
- Keep changes under `self_harness/` unless explicitly asked otherwise.
- User prefers simple implementation and Vietnamese explanations. No unit tests
  unless explicitly requested.

## Main flow

```text
bench
  Run one config on selected tasks. No tuner and no promotion.

optimize / overnight
  v000 baseline bench
  -> active bench if active != v000
  -> tuner candidate
  -> candidate bench + judge
  -> promote/reject
  -> next round or stop
```

`previous` in a round is the best active version at the start of that round.
Promotion replaces previous for the next round. Rejection leaves previous
unchanged. `v000` is fixed within the whole run.

## Retained task suite

The retained overnight suite contains these task YAMLs:

```text
self_harness/tasks/telemetry_window_repair.yaml
self_harness/tasks/expense_dashboard.yaml
self_harness/tasks/fullstack_todo.yaml
```

`bench` defaults to `telemetry_window_repair`. `overnight` runs all three. They
are source-text-only; they forbid server/dev-server startup, package install,
interactive shells, screenshots, rendering, and terminal-hanging commands.

`tasks/poster_render_image.yaml` is an additional ad-hoc image-render workflow
task. It is deliberately excluded from `overnight`: it asks the agent to use
the external `render-to-image` skill. The judge can inspect declared supported
raster images (PNG/JPG/JPEG/GIF/WebP) visually through a multimodal attachment,
with a 5 MB per-image limit, as well as verify the workflow and metadata.

`seed_dir` is copied into a clean workspace for each task. Today most seeds are
empty `.gitkeep` folders, but the mechanism ensures isolation and supports
future seeded-code/fixture tasks.

## Important source files

| Path | Purpose |
| --- | --- |
| `cli.py` | Commands: bench, optimize, overnight, report, activate. |
| `config.py` | Paths, `.env`, v000 snapshot, active state, version saving. |
| `runtime.py` | ReAct runtime; raw agent trajectory and metrics. |
| `models.py` | LiteLLM call/usage/fallback adapter. |
| `tasks.py` | Task YAML loader and retained overnight task list. |
| `bench.py` | Clean workspace → agent → judge → suite manifest. |
| `judge.py` | Read-only workspace judge loop and enforced task pass. |
| `trajectory.py` | Shared compact review trajectory for judge/tuner. |
| `tuner.py` | Candidate prompt/description proposal and validation. |
| `optimizer.py` | Baseline/active/candidate loop plus promotion decision. |
| `scripts/model_routes.py` | Primary/fallback model names. |
| `scripts/test_litellm_models.py` | Real minimal LiteLLM health check. |

Core functions have explanatory docstrings in `judge.py`, `bench.py`,
`optimizer.py`, and `tuner.py`.

## Judge and tuner evidence

Raw agent trajectory is saved in each suite manifest. It contains full model
messages, tool arguments/results, retries, usage, timing, and provider-exposed
reasoning when returned.

Judge and tuner do **not** receive that raw payload. They receive the shared
`trajectory.review_trajectory()` view:

```text
reasoning content exposed by provider
visible assistant text output
tool name and compact intent/path
tool_result: worked true/false only
```

Large write-file bodies, stdout/stderr, image payloads, and verbose tool
results stay in raw local logs and are omitted from model context.

The tuner receives each task's judge `passed` flag and numeric `score`, but not
the judge's free-text `reason`; reasons stay only in local audit artifacts to
avoid rubric-feedback leakage into prompt tuning.

Judge additionally has workspace inspection tools and one isolated test tool:

```text
list_workspace(path)
read_workspace_file(path)
run_workspace_test(command, timeout_seconds?)
```

`run_workspace_test` copies the workspace to a temporary directory and runs a
bounded non-interactive verification command there, then discards the copy.
It therefore cannot alter the original judged output. The judge is instructed
not to install dependencies, start a service/container, or use the tool for
anything other than verification. It receives task/rubric/final
answer/review trajectory and can inspect supporting files beyond the YAML
artifact allow-list.

This change fixed a prior problem: old judge received only declared files and
incorrectly described existing `api.js`, `styles.css`, `nginx.conf`, etc. as
missing because it could not see them. A live end-to-end test from this coding
environment was blocked by network-data safety policy, but local read/list
validation and compilation passed. Users running the harness locally will make
the real judge calls through their configured gateway.

## Pass, score, and promotion

In `judge.py:judge_task()`:

```python
passed = (
    judge_raw_passed
    and score >= task["judge"]["pass_score"]
    and agent_result["status"] == "completed"
)
```

`bench._aggregate()` computes suite `pass_count`, `pass_rate`, and
`average_score`. `optimizer.decide()`:

1. Rejects fewer task passes or a passing-task regression.
2. Promotes more task passes.
3. Rejects average score loss >0.05 when pass count ties.
4. Then promotes >=3% lower agent tokens; with token tie +/-3%, one fewer turn;
   with turn tie, >=10% lower wall time.

Judge/tuner tokens are logged as overhead, not used for efficiency promotion.

## Token counting

`models._usage()` prefers provider `prompt_tokens`, `completion_tokens`, and
`total_tokens`. Fallback is LiteLLM token counting, then JSON-character count
divided by 4. `usage.source` says `provider` or `estimated`.

Agent totals sum every agent turn. Judge totals sum all judge loop calls.
Tuner usage lives in each round's `tuner.json`.

## Artifact layout

```text
self_harness/workspace/suite-<id>/<task-id>/
  Actual files agent created. This is the only retained output copy.

self_harness/artifacts/suites/suite-<id>/manifest.json
  Per-suite metrics, raw agent trajectory, judge inspection, verdict, workspace path.

self_harness/artifacts/optimization-runs/run-<id>/
  baseline.json, active-start.json, round audit files, report.md.

self_harness/artifacts/versions/vNNN.json
  Promoted config only: prompt plus full tool schema.

self_harness/artifacts/state.json
  Active version pointer, next version ID, latest report path.
```

For one round:

```text
tuner.json            raw tuner output + model/usage/retries
candidate-config.json  validated merged config actually run
candidate-suite.json   candidate benchmark result
comparison.md          candidate vs v000 and previous active
```

`tuner.json` and `candidate-config.json` often look similar because a valid raw
proposal is merged directly. The latter includes every inherited tool definition
and only exists after validation succeeds.

Legacy `artifacts/suite-snapshots/` holds old manifest history. Its copied
fixtures were removed; new runs use `artifacts/suites/`.

## Version chain summary

```text
v000: root snapshot, 8,950 prompt chars
v001: reading_tracker_text token/turn reduction
v002: expense_dashboard token/turn reduction
v003-v004: fullstack completeness rules added after missing frontend/support files
v005: fullstack efficiency improvement, current active
v006: fullstack-only reward-hacking candidate, retained for audit but inactive
```

Before trusting a future candidate globally, run the fixed three-task suite and
prefer repeated rollouts/median metrics. One task/one rollout is insufficient
evidence due model sampling variance.
