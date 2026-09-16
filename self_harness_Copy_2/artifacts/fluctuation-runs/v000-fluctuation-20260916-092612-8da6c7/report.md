# v000 natural-fluctuation measurement

Version: `v000` | Measurements: 5 | Tasks: telemetry_window_repair, expense_dashboard, fullstack_todo, feature_flag_rollout_repair, inventory_reservation_repair, audit_log_normalizer
Model route: `deepseek/deepseek-v4-flash, openai/qwen/qwen3.8-flash, openai/kCode`

Every row uses exactly v000 and a fresh six-task workspace suite. No tuner, candidate, promotion, or active-version change occurs. The first row is only the fixed cost reference for reward normalization.

| Run | Pass | Quality | Hacking penalty | Tokens | Turns | Agent time (s) | Reward | Provider-failure seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 5/6 | 0.983 | 0.000 | 1,935,491 | 105 | 991.9 | 0.7417 | 0.0 |
| 2 | 4/6 | 0.920 | 0.000 | 1,272,266 | 79 | 1764.3 | 0.7169 | 414.9 |
| 3 | 5/6 | 0.975 | 0.000 | 1,209,801 | 88 | 736.6 | 0.7721 | 0.0 |
| 4 | 6/6 | 0.975 | 0.000 | 857,640 | 62 | 644.1 | 0.7843 | 0.0 |
| 5 | 5/6 | 0.975 | 0.000 | 1,656,845 | 98 | 867.6 | 0.7571 | 0.0 |

## Delta versus measurement 1

| Run | Quality delta | Reward delta | Tokens | Turns | Agent time |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | +0.0000 | +0.0000 | +0.0% | +0.0% | +0.0% |
| 2 | -0.0633 | -0.0248 | -34.3% | -24.8% | +77.9% |
| 3 | -0.0083 | +0.0305 | -37.5% | -16.2% | -25.7% |
| 4 | -0.0083 | +0.0426 | -55.7% | -41.0% | -35.1% |
| 5 | -0.0083 | +0.0155 | -14.4% | -6.7% | -12.5% |

## Observed fluctuation

- Reward: mean `0.7544`, population stddev `0.0236`, range `0.7169` to `0.7843`.
- Absolute reward drift vs measurement 1: median `0.0276`, p75 `0.0335`, max `0.0426`.
- Agent time excludes provider failures/backoff/retry delay. Provider-failure seconds are audit-only so outage latency does not inflate reward variation.
- This is an observed five-rollout sample, not a statistically proven threshold. Compare it with later v005 control drift before choosing `min_reward_gain`.
