# Self-Harness optimization

Active: v004 | Stage: complete

One task feeds tuner and selects by reward; costs use the fixed run-start baseline.

| Suite | Quality | Tokens | Turns | Time (s) | Reward | Valid |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| baseline | 1.000 | 68,769 | 9 | 81.9 | 0.7500 | True |

Each round has one raw-metric row and one delta row against the incumbent used for its decision. Positive cost percentages mean the candidate is more expensive.

| Round | Decision | Quality | Tokens | Turns | Time (s) | Reward | Reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | REJECTED | 0.000 | 64,875 | 8 | 71.5 | 0.2614 | incomplete/error evaluation; reward comparison unavailable |
| ↳ vs v004 |  | Δ -1.000 | -5.7% | -11.1% | -12.7% | Δ -0.4886 |  |
| 2 | ERROR | - | - | - | - | - | - |
| ↳ vs v004 |  | - | - | - | - | - |  |

Round 2 error: All routed models failed (2 attempted): openai/qwen/qwen3.8-flash: litellm.NotFoundError: OpenAIException - No account available for model 'qwen/qwen3.8-flash' / deepseek/deepseek-v4-flash: litellm.NotFoundError: DeepseekException - {"error":{"message":"No account available for model 'deepseek-v4-flash'","type":"invalid_request_error","code":"model_not_found"}}


Stopped: patience reached

Details and suite audit paths: [run.json](run.json).
Judge verdicts/evidence: [judge.json](judge.json). Tuner hypotheses/proposals: [tuner.json](tuner.json).
