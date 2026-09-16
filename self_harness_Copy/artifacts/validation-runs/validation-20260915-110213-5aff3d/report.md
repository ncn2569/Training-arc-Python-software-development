# Self-Harness validation comparison

Reference: v003 | Candidate: v005
Held-out tasks are evaluated only; this command never tunes, promotes or changes the active version.

| Result | Quality | Tokens | Turns | Time (s) | Reward | Valid |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| v003 | 0.950 | 142,586 | 9 | 152.8 | 0.7250 | True |
| v005 | 0.950 | 167,703 | 13 | 129.4 | 0.7054 | True |
| Δ candidate vs reference | Δ +0.000 | +17.6% | +44.4% | -15.3% | Δ -0.0196 | - |

Positive cost percentages mean the candidate is more expensive. Quality and reward use point deltas.

## Task suites

- Reference manifest: D:\Inter-K\self_harness\artifacts\suites\suite-76bd2454adff4404\manifest.json
- Candidate manifest: D:\Inter-K\self_harness\artifacts\suites\suite-fbf8c01d2acb4acc\manifest.json
