# Self-Harness validation comparison

Reference: v005 | Candidate: v004
Held-out tasks are evaluated only; this command never tunes, promotes or changes the active version.

| Result | Quality | Tokens | Turns | Time (s) | Reward | Valid |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| v005 | 0.925 | 278,473 | 16 | 265.3 | 0.7125 | True |
| v004 | 0.900 | 447,051 | 23 | 407.9 | 0.6491 | True |
| Δ candidate vs reference | Δ -0.025 | +60.5% | +43.8% | +53.8% | Δ -0.0634 | - |

Positive cost percentages mean the candidate is more expensive. Quality and reward use point deltas.

## Task suites

- Reference manifest: D:\Inter-K\self_harness\artifacts\suites\suite-1f9003a8f6ee4eb9\manifest.json
- Candidate manifest: D:\Inter-K\self_harness\artifacts\suites\suite-0b0c61bc8081468b\manifest.json
