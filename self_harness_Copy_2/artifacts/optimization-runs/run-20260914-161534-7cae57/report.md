# Self-Harness optimization

Active: v003 | Stage: complete

One task feeds tuner and selects by reward; costs use the fixed run-start baseline.

| Suite | Quality | Tokens | Turns | Time (s) | Reward | Valid |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| baseline | 0.900 | 67,933 | 6 | 82.2 | 0.7000 | True |

Each round has one raw-metric row and one delta row against the incumbent used for its decision. Positive cost percentages mean the candidate is more expensive.

| Round | Decision | Quality | Tokens | Turns | Time (s) | Reward | Reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | PROMOTED | 0.950 | 63,490 | 3 | 119.3 | 0.7450 | reward 0.7000 -> 0.7450 (gain +0.0450) |
| ↳ vs v001 |  | Δ +0.050 | -6.5% | -50.0% | +45.1% | Δ +0.0450 |  |
| 2 | REJECTED | 0.950 | 175,565 | 11 | 143.3 | 0.6341 | reward 0.7450 -> 0.6341 (gain -0.1109) |
| ↳ vs v002 |  | Δ +0.000 | +176.5% | +266.7% | +20.2% | Δ -0.1109 |  |
| 3 | PROMOTED | 0.900 | 48,540 | 3 | 77.9 | 0.7472 | reward 0.7450 -> 0.7472 (gain +0.0021) |
| ↳ vs v002 |  | Δ -0.050 | -23.5% | +0.0% | -34.7% | Δ +0.0021 |  |

Stopped: max rounds reached

Details and suite audit paths: [run.json](run.json).
Judge verdicts/evidence: [judge.json](judge.json). Tuner hypotheses/proposals: [tuner.json](tuner.json).
