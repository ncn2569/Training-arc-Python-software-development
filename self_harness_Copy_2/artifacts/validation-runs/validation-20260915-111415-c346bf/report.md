# Self-Harness validation comparison

Reference: v003 | Candidate: v004
Held-out tasks are evaluated only; this command never tunes, promotes or changes the active version.

| Result | Quality | Tokens | Turns | Time (s) | Reward | Valid |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| v003 | 0.950 | 185,415 | 8 | 313.0 | 0.7250 | True |
| v004 | 0.900 | 191,165 | 9 | 165.8 | 0.7090 | True |
| Δ candidate vs reference | Δ -0.050 | +3.1% | +12.5% | -47.0% | Δ -0.0160 | - |

Positive cost percentages mean the candidate is more expensive. Quality and reward use point deltas.

## Task suites

- Reference manifest: D:\Inter-K\self_harness\artifacts\suites\suite-3d7d32dd7c0548d2\manifest.json
- Candidate manifest: D:\Inter-K\self_harness\artifacts\suites\suite-72103f9637b048ec\manifest.json
