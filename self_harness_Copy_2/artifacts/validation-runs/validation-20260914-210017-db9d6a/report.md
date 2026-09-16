# Self-Harness validation comparison

Reference: v003 | Candidate: v004
Held-out tasks are evaluated only; this command never tunes, promotes or changes the active version.

| Result | Quality | Tokens | Turns | Time (s) | Reward | Valid |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| v003 | 0.910 | 1,137,768 | 47 | 1087.0 | 0.7050 | True |
| v004 | 0.893 | 733,391 | 36 | 509.9 | 0.7271 | True |
| Δ candidate vs reference | Δ -0.017 | -35.5% | -23.4% | -53.1% | Δ +0.0221 | - |

Positive cost percentages mean the candidate is more expensive. Quality and reward use point deltas.

## Task suites

- Reference manifest: D:\Inter-K\self_harness\artifacts\suites\suite-021a37afaa3c4a5a\manifest.json
- Candidate manifest: D:\Inter-K\self_harness\artifacts\suites\suite-c2c57d0616b346a8\manifest.json
