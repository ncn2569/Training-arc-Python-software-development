# Self-Harness validation comparison

Reference: v005 | Candidate: v003
Held-out tasks are evaluated only; this command never tunes, promotes or changes the active version.

| Result | Quality | Tokens | Turns | Time (s) | Reward | Valid |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| v005 | 0.950 | 377,146 | 23 | 475.3 | 0.7250 | True |
| v003 | 0.933 | 440,956 | 24 | 491.4 | 0.6956 | True |
| Δ candidate vs reference | Δ -0.017 | +16.9% | +4.3% | +3.4% | Δ -0.0294 | - |

Positive cost percentages mean the candidate is more expensive. Quality and reward use point deltas.

## Task suites

- Reference manifest: D:\Inter-K\self_harness\artifacts\suites\suite-5aa92b3517d04179\manifest.json
- Candidate manifest: D:\Inter-K\self_harness\artifacts\suites\suite-b60b854726d14b0a\manifest.json
