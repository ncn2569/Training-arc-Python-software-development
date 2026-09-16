# Reward-delta calibration

Source run: `run.json`
Mode: `calibration-suite` | Baseline: `v005`
Model route: `deepseek/deepseek-v4-flash, openai/qwen/qwen3.8-flash, openai/kCode`

The optimization reward uses the same fixed per-task run-start baseline for every candidate. Each task has a fresh seed workspace; suite reward is the mean task reward, so the six task domains have equal weight. Agent Time excludes provider failure/backoff/retry delay; `suite_wall_time` remains operational elapsed time only.

| Round | Decision | Reward Δ vs incumbent | Quality Δ | Tokens Δ | Turns Δ | Time Δ |
| --- | --- | ---: | ---: | ---: | ---: | ---: |

> Note: this run permits gateway fallback models for availability. Inspect the recorded model route and per-task model audit when interpreting small deltas.
| 1 | REJECTED | -0.0036 | -0.0167 | -12.9% | -2.8% | -0.9% |
| 2 | REJECTED | -0.0110 | +0.0083 | -2.6% | +13.9% | +4.3% |
| 3 | REJECTED | -0.0130 | +0.0167 | +18.7% | +22.2% | +3.9% |
| 4 | REJECTED | -0.0242 | +0.0083 | +72.8% | +38.9% | +19.1% |
| 5 | REJECTED | -0.0093 | -0.0167 | -9.5% | +2.8% | -8.8% |
| 6 | REJECTED | -0.0215 | +0.0167 | +147.8% | +66.7% | +48.1% |
| 7 | REJECTED | -0.0442 | -0.0167 | +121.1% | +63.9% | +30.1% |
| 8 | REJECTED | -0.0247 | +0.0083 | +81.6% | +33.3% | +20.2% |

## Interpreting a promotion floor

- Same-config control drift (n=2): deltas `-0.0275, +0.0094`; max absolute drift `0.0275`. A future `--min-reward-gain` should exceed this only after confirming with more control runs.
- Observed absolute reward delta: median `0.0173`, p75 `0.0243`, max `0.0442`.
- Flat-quality rejected candidates (n=3): median absolute delta `0.0242`, p75 `0.0244`. Use this as a conservative screening range for a future `--min-reward-gain`, not as a proof of noise.
- This run has one rollout per version/task. Reward deltas combine true prompt effects and sampling variation; the report intentionally does not auto-change the threshold.
