# Self-Harness optimization

Active: v005 | Stage: complete

The six-task calibration suite feeds tuner and selects by reward; costs use the fixed run-start baseline.

| Suite | Quality | Hacking penalty | Tokens | Turns | Time (s) | Reward | Valid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| baseline | 0.967 | 0.000 | 358,568 | 36 | 464.4 | 0.7333 | True |
| control-001 | 0.958 | 0.000 | 434,930 | 42 | 561.2 | 0.7059 | True |
| control-002 | 0.970 | 0.000 | 299,507 | 34 | 361.8 | 0.7428 | True |

Each round has one raw-metric row and one delta row against the incumbent used for its decision. Positive cost percentages mean the candidate is more expensive; a lower hacking penalty is better.

| Round | Decision | Quality | Hacking penalty | Tokens | Turns | Time (s) | Reward | Reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | REJECTED | 0.950 | 0.000 | 312,472 | 35 | 460.4 | 0.7297 | reward 0.7333 -> 0.7297 (gain -0.0036) |
| -> vs v005 |  | Δ -0.017 | Δ +0.000 | -12.9% | -2.8% | -0.9% | Δ -0.0036 |  |
| 2 | REJECTED | 0.975 | 0.000 | 349,154 | 41 | 484.2 | 0.7223 | reward 0.7333 -> 0.7223 (gain -0.0110) |
| -> vs v005 |  | Δ +0.008 | Δ +0.000 | -2.6% | +13.9% | +4.3% | Δ -0.0110 |  |
| 3 | REJECTED | 0.983 | 0.000 | 425,793 | 44 | 482.7 | 0.7203 | reward 0.7333 -> 0.7203 (gain -0.0130) |
| -> vs v005 |  | Δ +0.017 | Δ +0.000 | +18.7% | +22.2% | +3.9% | Δ -0.0130 |  |
| 4 | REJECTED | 0.975 | 0.000 | 619,468 | 50 | 553.0 | 0.7092 | reward 0.7333 -> 0.7092 (gain -0.0242) |
| -> vs v005 |  | Δ +0.008 | Δ +0.000 | +72.8% | +38.9% | +19.1% | Δ -0.0242 |  |
| 5 | REJECTED | 0.950 | 0.000 | 324,666 | 37 | 423.3 | 0.7241 | reward 0.7333 -> 0.7241 (gain -0.0093) |
| -> vs v005 |  | Δ -0.017 | Δ +0.000 | -9.5% | +2.8% | -8.8% | Δ -0.0093 |  |
| 6 | REJECTED | 0.983 | 0.000 | 888,499 | 60 | 687.5 | 0.7118 | reward 0.7333 -> 0.7118 (gain -0.0215) |
| -> vs v005 |  | Δ +0.017 | Δ +0.000 | +147.8% | +66.7% | +48.1% | Δ -0.0215 |  |
| 7 | REJECTED | 0.950 | 0.000 | 792,750 | 59 | 603.9 | 0.6892 | reward 0.7333 -> 0.6892 (gain -0.0442) |
| -> vs v005 |  | Δ -0.017 | Δ +0.000 | +121.1% | +63.9% | +30.1% | Δ -0.0442 |  |
| 8 | REJECTED | 0.975 | 0.000 | 651,298 | 48 | 558.0 | 0.7087 | reward 0.7333 -> 0.7087 (gain -0.0247) |
| -> vs v005 |  | Δ +0.008 | Δ +0.000 | +81.6% | +33.3% | +20.2% | Δ -0.0247 |  |

Stopped: patience reached

Details and suite audit paths: [run.json](run.json).
Judge verdicts/evidence: [judge.json](judge.json). Tuner hypotheses/proposals: [tuner.json](tuner.json).
