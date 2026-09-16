# Self-Harness validation comparison

Reference: v002 | Candidate: v003
Held-out tasks are evaluated only; this command never tunes, promotes or changes the active version.

| Result | Quality | Tokens | Turns | Time (s) | Reward | Valid |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| v002 | 0.920 | 226,812 | 14 | 177.7 | 0.7100 | True |
| v003 | 0.930 | 261,056 | 13 | 215.5 | 0.7042 | True |
| Δ candidate vs reference | Δ +0.010 | +15.1% | -7.1% | +21.3% | Δ -0.0058 | - |

Positive cost percentages mean the candidate is more expensive. Quality and reward use point deltas.

## Task suites

- Reference manifest: D:\Inter-K\self_harness\artifacts\suites\suite-aaf95d52676945c8\manifest.json
- Candidate manifest: D:\Inter-K\self_harness\artifacts\suites\suite-365a095c8bc54741\manifest.json
