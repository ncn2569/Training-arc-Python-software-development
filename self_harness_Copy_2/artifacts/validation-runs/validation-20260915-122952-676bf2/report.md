# Self-Harness validation comparison

Reference: v003 | Candidate: v005
Held-out tasks are evaluated only; this command never tunes, promotes or changes the active version.

| Result | Quality | Tokens | Turns | Time (s) | Reward | Valid |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| v003 | 0.950 | 120,761 | 5 | 155.8 | 0.7250 | True |
| v005 | 0.950 | 133,755 | 9 | 118.7 | 0.7040 | True |
| Δ candidate vs reference | Δ +0.000 | +10.8% | +80.0% | -23.9% | Δ -0.0210 | - |

Positive cost percentages mean the candidate is more expensive. Quality and reward use point deltas.

## Task suites

- Reference manifest: D:\Inter-K\self_harness\artifacts\suites\suite-d051703b4c3b41e3\manifest.json
- Candidate manifest: D:\Inter-K\self_harness\artifacts\suites\suite-e6b9b5211e3a4d74\manifest.json
