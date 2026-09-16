# Self-Harness validation comparison

Reference: v000 | Candidate: v005
Held-out tasks are evaluated only; this command never tunes, promotes or changes the active version.

| Result | Quality | Tokens | Turns | Time (s) | Reward | Valid |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| v000 | 0.950 | 134,993 | 10 | 121.8 | 0.7250 | True |
| v005 | 0.950 | 108,444 | 7 | 144.5 | 0.7476 | True |
| Δ candidate vs reference | Δ +0.000 | -19.7% | -30.0% | +18.6% | Δ +0.0226 | - |

Positive cost percentages mean the candidate is more expensive. Quality and reward use point deltas.

## Task suites

- Reference manifest: D:\Inter-K\self_harness\artifacts\suites\suite-b746fc7e817c4f96\manifest.json
- Candidate manifest: D:\Inter-K\self_harness\artifacts\suites\suite-6c294e8e59fe4bf3\manifest.json
