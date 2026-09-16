# Self-Harness optimization

Active: v005 | Stage: complete

One task feeds tuner and selects by reward; costs use the fixed run-start baseline.

| Suite | Quality | Tokens | Turns | Time (s) | Reward | Valid |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| baseline | 1.000 | 56,502 | 8 | 69.4 | 0.7500 | True |

Each round has one raw-metric row and one delta row against the incumbent used for its decision. Positive cost percentages mean the candidate is more expensive.

| Round | Decision | Quality | Tokens | Turns | Time (s) | Reward | Reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | PROMOTED | 1.000 | 37,888 | 7 | 57.1 | 0.7845 | reward 0.7500 -> 0.7845 (gain +0.0345) |
| ↳ vs v004 |  | Δ +0.000 | -32.9% | -12.5% | -17.8% | Δ +0.0345 |  |
| 2 | REJECTED | 1.000 | 46,040 | 8 | 64.5 | 0.7646 | reward 0.7845 -> 0.7646 (gain -0.0200) |
| ↳ vs v005 |  | Δ +0.000 | +21.5% | +14.3% | +13.1% | Δ -0.0200 |  |

Stopped: patience reached

Details and suite audit paths: [run.json](run.json).
Judge verdicts/evidence: [judge.json](judge.json). Tuner hypotheses/proposals: [tuner.json](tuner.json).
