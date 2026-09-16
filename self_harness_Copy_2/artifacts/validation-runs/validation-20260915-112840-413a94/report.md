# Self-Harness validation comparison

Reference: v003 | Candidate: v004
Held-out tasks are evaluated only; this command never tunes, promotes or changes the active version.

| Result | Quality | Tokens | Turns | Time (s) | Reward | Valid |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| v003 | 0.900 | 260,388 | 13 | 282.7 | 0.7000 | True |
| v004 | 0.900 | 179,764 | 12 | 178.7 | 0.7152 | True |
| Δ candidate vs reference | Δ +0.000 | -31.0% | -7.7% | -36.8% | Δ +0.0152 | - |

Positive cost percentages mean the candidate is more expensive. Quality and reward use point deltas.

## Task suites

- Reference manifest: D:\Inter-K\self_harness\artifacts\suites\suite-386e338eb23f4b02\manifest.json
- Candidate manifest: D:\Inter-K\self_harness\artifacts\suites\suite-74bd4f1ec69f4c00\manifest.json
