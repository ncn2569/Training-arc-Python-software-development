# Self-Harness validation comparison

Reference: v003 | Candidate: v005
Held-out tasks are evaluated only; this command never tunes, promotes or changes the active version.

| Result | Quality | Tokens | Turns | Time (s) | Reward | Valid |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| v003 | 0.950 | 81,004 | 4 | 120.2 | 0.7250 | True |
| v005 | 0.900 | 178,180 | 8 | 184.0 | 0.6176 | True |
| Δ candidate vs reference | Δ -0.050 | +120.0% | +100.0% | +53.1% | Δ -0.1074 | - |

Positive cost percentages mean the candidate is more expensive. Quality and reward use point deltas.

## Task suites

- Reference manifest: D:\Inter-K\self_harness\artifacts\suites\suite-77d158fb7e2c40ff\manifest.json
- Candidate manifest: D:\Inter-K\self_harness\artifacts\suites\suite-2cba50f986d746d6\manifest.json
