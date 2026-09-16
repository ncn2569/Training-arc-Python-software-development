# Self-Harness optimization

Active: v005 | Stage: running control-001

The six-task calibration suite feeds tuner and selects by reward; costs use the fixed run-start baseline.

| Suite | Quality | Hacking penalty | Tokens | Turns | Time (s) | Reward | Valid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| baseline | 0.800 | 0.000 | 1,179,578 | 92 | 1192.2 | 0.6500 | True |

Each round has one raw-metric row and one delta row against the incumbent used for its decision. Positive cost percentages mean the candidate is more expensive; a lower hacking penalty is better.

| Round | Decision | Quality | Hacking penalty | Tokens | Turns | Time (s) | Reward | Reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |

Details and suite audit paths: [run.json](run.json).
Judge verdicts/evidence: [judge.json](judge.json). Tuner hypotheses/proposals: [tuner.json](tuner.json).
