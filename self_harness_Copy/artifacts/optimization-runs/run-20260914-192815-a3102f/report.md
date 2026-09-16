# Self-Harness optimization

Active: v004 | Stage: complete

The retained task suite feeds tuner and selects by reward; costs use the fixed run-start baseline.

| Suite | Quality | Tokens | Turns | Time (s) | Reward | Valid |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| baseline | 0.933 | 567,412 | 29 | 457.2 | 0.7167 | True |

Each round has one raw-metric row and one delta row against the incumbent used for its decision. Positive cost percentages mean the candidate is more expensive.

| Round | Decision | Quality | Tokens | Turns | Time (s) | Reward | Reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | PROMOTED | 0.923 | 245,322 | 18 | 336.5 | 0.7348 | reward 0.7167 -> 0.7348 (gain +0.0181) |
| ↳ vs v003 |  | Δ -0.010 | -56.8% | -37.9% | -26.4% | Δ +0.0181 |  |
| 2 | REJECTED | 0.907 | 652,043 | 32 | 463.3 | 0.6732 | reward 0.7348 -> 0.6732 (gain -0.0616) |
| ↳ vs v004 |  | Δ -0.017 | +165.8% | +77.8% | +37.7% | Δ -0.0616 |  |
| 3 | REJECTED | 0.917 | 375,209 | 21 | 386.6 | 0.6950 | reward 0.7348 -> 0.6950 (gain -0.0397) |
| ↳ vs v004 |  | Δ -0.007 | +52.9% | +16.7% | +14.9% | Δ -0.0397 |  |

Stopped: patience reached

Details and suite audit paths: [run.json](run.json).
Judge verdicts/evidence: [judge.json](judge.json). Tuner hypotheses/proposals: [tuner.json](tuner.json).
