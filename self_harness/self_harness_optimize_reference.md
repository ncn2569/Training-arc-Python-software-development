# Feature: Self-Optimization Harness

> Reference draft only. The main document is `self_harness_optimize.md`.
> This version follows the same structure, but completes the ideas using the
> behavior of the current harness and labels future work explicitly.

## 1. Objective

The goal of the self-optimization harness is to improve selected harness
components—currently the system prompt and tool descriptions—by learning from
observed agent trajectories and measurable execution costs.

Instead of changing the agent based only on intuition or manual trial and error,
the harness runs controlled experiments. It compares a candidate configuration
with the current configuration under the same task conditions, then keeps the
candidate only when the measured result supports the change.

The current optimization objectives are:

- output quality;
- token usage;
- number of agent turns;
- useful agent wall time;
- reward-hacking risk;
- additional metrics when they can be measured fairly and audited.

This is currently a black-box optimization system for agent policy text. It does
not update model weights. However, its trajectories, judgments, and pairwise
decisions can later become useful data for an RLAIF-style training pipeline.

## 2. Frameworks

The framework has four connected stages:

```text
Run -> Judge -> Tune -> Decide -> Run -> Judge -> Tune -> Decide -> ...
```

The first three stages generate evidence. The decision stage is the only stage
allowed to change which configuration is active.

### 2.1 Run phase

The run phase executes one predefined task with one harness configuration.

For each task, the harness:

1. Creates a clean workspace from the same task seed.
2. Gives the task prompt and the selected configuration to the agent.
3. Runs the agent within fixed turn and time limits.
4. Records the full trajectory: model responses, tool calls, tool results, final
   answer, tokens, turns, tool errors, retries, and wall time.
5. Preserves the final workspace as the artifact to be evaluated.

The run phase measures what the agent actually did. It does not decide whether
the artifact is correct.

Provider failures are handled separately from agent performance. The runtime
retries a failed provider request within the same turn while retaining context
and workspace state. Failed-provider latency and backoff are recorded for
operations, but are excluded from the wall-time metric used by reward. If all
provider retries fail, the rollout is invalid rather than treated as a poor
agent result.

### 2.2 Judge phase

The judge phase evaluates the finished workspace against the task contract and
its rubric.

The judge should:

- inspect the actual artifact rather than trust the agent's final answer;
- run bounded verification only in a temporary copy of the workspace;
- return a quality score, requirement-level evidence, and an evaluation-validity
  status;
- report a reward-hacking penalty only when there is evidence that the agent
  attempted to manipulate evaluation rather than complete the task.

The judge must score achieved artifact quality, not agent effort. A trajectory
can help the judge find relevant files or checks, but it must not become an
unstated grading criterion. For example, an agent should not receive extra
quality credit merely for showing a failing test before its repair.

### 2.3 Tune phase

The tuner reads the active configuration, bounded trajectory summaries, judge
feedback, and the history of previous candidate experiments. It proposes one
small candidate change.

The current mutable surfaces are:

- the system prompt;
- tool and parameter descriptions.

The tuner cannot change tool handlers, tool schemas, task contracts, judge
instructions, reward weights, or fixed safety rules. Every candidate must be
validated before it is run. The proposal should contain one causal hypothesis:
what behavior was observed, why it happened, what minimal change may address it,
and what regression risk remains.

The main purpose of the tune phase is not to memorize benchmark tasks. It is to
turn recurring trajectory patterns into general agent guidance that could still
apply to a different repository, framework, or domain.

### 2.4 Decide phase

The decision phase compares the candidate reward scores against active fluctuation. It can
return one of four outcomes:

- **Promote:** the candidate has valid and sufficiently strong evidence of
  improvement.
- **Reject:** the candidate is valid but does not improve enough, or regresses.
- **Inconclusive:** the measured change is too close to known natural noise and
  needs a confirm rollout if the experiment budget allows it.
- **Invalid:** a provider, runtime, or evaluator failure made the comparison
  unreliable; it should not be treated as an ordinary candidate rejection.

Only a promoted candidate becomes the next active configuration.

## 3. Methodology

### 3.1 Fixed baseline and incumbent

The harness uses two related but different references:

- **Run-start baseline:** the initial active configuration evaluated at the start
  of the run. Its per-task costs remain fixed for reward normalization across all
  candidate rounds.
- **Incumbent:** the best promoted configuration so far. Each candidate is
  compared with this configuration to decide whether it should be promoted.

Keeping the baseline fixed makes reward values within a run comparable. Allowing
the incumbent to change lets the optimizer make sequential improvements.

### 3.2 Reward function

For each task, the current reward function is:

```text
Reward_task = 0.50 * Quality
            + 0.25 * Token_norm
            + 0.15 * Turn_norm
            + 0.10 * Time_norm
            - 0.25 * Reward_hacking_penalty
```

The suite reward is the arithmetic mean of all task rewards. Every task has equal
weight in the suite, regardless of its absolute token cost.

#### Quality

`Quality` is the judge score for the completed artifact, in the range `[0, 1]`.
It represents correctness and completeness against the task rubric.

#### Token normalization

```text
Token_norm = Token_baseline / (Token_baseline + Token_candidate)
```

#### Turn normalization

```text
Turn_norm = Turn_baseline / (Turn_baseline + Turn_candidate)
```

#### Time normalization

```text
Time_norm = Time_baseline / (Time_baseline + Time_candidate)
```

For all normalized cost metrics, a candidate equal to its baseline receives
`0.5`. A cheaper candidate receives a value above `0.5`; a more expensive
candidate receives a value below `0.5`.

#### Reward-hacking penalty

`Reward_hacking_penalty` is in `[0, 1]` and is subtracted at the end of the
formula. It is not a generic bug penalty. It is only non-zero when the judge
has evidence of behavior intended to manipulate the evaluation process, such as
modifying evaluation assets or fabricating verification.

### 3.3 Reward delta

Reward delta is the improvement of a candidate over the current incumbent:

```text
Reward_delta = Reward_candidate - Reward_incumbent
```

It is important not to define reward delta as the standard deviation of reward.
The standard deviation, range, or quantiles from repeated same-config rollouts
are instead estimates of **natural measurement noise**.

For a control rollout with the same active configuration:

```text
Control_delta_i = Reward_control_i - Reward_reference
```

The distribution of `Control_delta` tells us how much reward can change even
when the prompt has not changed. That distribution is the evidence used to set
a future promotion and stopping threshold.

### 3.4 Current and proposed decision rules

The current implementation promotes when:

```text
evaluation is valid
and Reward_delta > min_reward_gain
```

`min_reward_gain` is currently a manual CLI parameter. A value of `0` accepts
any valid positive reward delta.

The proposed calibrated rule is:

```text
evaluation is valid
and Reward_delta > delta_promote
```

where `delta_promote` is derived from repeated same-config control deltas, not
chosen from intuition alone. A candidate with a small positive delta inside the
noise range is inconclusive rather than a reliable win.

The v000 fluctuation experiment is intended to establish an initial estimate of
this natural noise. Controls near the active incumbent are still necessary,
because variance can change with prompt length, task mix, model route, and
gateway conditions.

### 3.5 Stopping signs

The optimizer should not stop simply because one candidate loses. A useful
stopping signal is that several valid, non-duplicate candidate hypotheses fail
to produce a reward delta greater than the calibrated progress threshold.

```text
stop when K consecutive valid candidate experiments
do not produce a confirmed Reward_delta > delta_progress
```

Provider failures, invalid judge outputs, and malformed candidate proposals must
be tracked separately from ordinary rejected experiments. Otherwise, gateway
instability is incorrectly interpreted as a limit of the optimization process.

### 3.6 Configuration-specific calibration and practical update threshold

Every configuration that may become an active incumbent must have its own
calibration profile. A fluctuation profile from v000, or from any other version,
must not automatically be reused for a different prompt configuration.

For one configuration `theta`, run the same configuration five times on the same
task suite, with clean workspaces and unchanged evaluation conditions:

```text
R_1, R_2, R_3, R_4, R_5
mean_reward(theta) = mean(R_1 ... R_5)
```

The calibration record should persist all five rewards, their mean, standard
deviation, minimum, maximum, model-route audit, and the experiment conditions.
Standard deviation is useful for analysis, but five samples are too few to rely
on it alone as a safety boundary. The initial conservative fluctuation threshold
can be defined as:

```text
fluctuation_threshold(theta) = max(|R_i - mean_reward(theta)|)
```

The system also has a practical threshold. It prevents a statistically visible
but operationally insignificant improvement from changing the active policy.
This reference defines a practical improvement as five percent of the active
configuration's calibrated mean reward:

```text
practical_threshold(theta) = 0.05 * mean_reward(theta)
```

This is a relative five-percent improvement, not an absolute increase of `0.05`
reward points. For example, if the calibrated active mean reward is `0.7333`,
the practical threshold is `0.0367`; a candidate must reach a mean reward above
approximately `0.7700` before the practical condition is satisfied.

The active configuration's required improvement is the stricter of its noise
and practical thresholds:

```text
required_gain(theta_active) = max(
    fluctuation_threshold(theta_active),
    practical_threshold(theta_active)
)
```

#### Candidate confirmation rule

A one-rollout candidate result may be used as a cheap screening signal, but it
must not by itself promote a new version. If a candidate first appears to beat
the active calibrated mean by `required_gain`, run the candidate five times and
create its own calibration profile.

The final promotion rule becomes:

```text
candidate_mean_reward - active_mean_reward
    > max(
        fluctuation_threshold(active),
        fluctuation_threshold(candidate),
        practical_threshold(active)
      )
```

This requires the improvement to survive both configurations' observed natural
fluctuation and to be large enough to matter in practice.

After promotion, the candidate calibration profile becomes the active profile
for the next round. Recalibration is required whenever any comparison condition
changes: active configuration, task suite, reward function, evaluator behavior,
runtime semantics, or model-route policy. It is not necessary to rerun five
controls before every candidate while the active configuration and conditions
remain unchanged.

#### Effect on stopping

The no-progress counter should count only valid candidate experiments that have
had a fair opportunity to clear `required_gain`. Provider failures, invalid
evaluations, and candidates awaiting confirmation should not be treated as normal
optimization failures. The optimizer can stop when `K` successive valid,
non-duplicate candidate hypotheses fail to produce a confirmed improvement above
the active configuration's `required_gain`.

## 4. Implementation Requirements

For reward comparisons to be meaningful, the following conditions are required:

1. Candidate and incumbent use the same task scope, task budgets, rubric,
   reward function, and fixed cost baseline.
2. Every rollout starts from a clean copy of the same task seed.
3. The judge cannot modify the original workspace during verification.
4. Agent cost, provider failure time, and judge/tuner overhead are recorded as
   separate metrics.
5. The actual model route is persisted because fallback models can change agent
   behavior even when provider delay is excluded from reward time.
6. Every candidate diff, trajectory, verdict, reward component, and decision is
   persisted for audit.
7. The tuner cannot change the evaluator, runtime safety boundary, or hidden
   reward weights.
8. A train-suite promotion is not treated as a production release; held-out
   validation is required before deployment.

## 5. Optimization Loop

```text
1. Run the active configuration on a fixed task suite.
2. Judge each resulting workspace and calculate the run-start baseline reward.
3. Run same-config controls when calibrating noise.
4. Ask the tuner for one bounded candidate change.
5. Validate the candidate mutation surface and prompt budget.
6. Run the candidate on fresh copies of the same task suite.
7. Judge candidate artifacts and calculate reward with the fixed baseline.
8. Calculate candidate Reward_delta against the incumbent.
9. Promote, reject, mark inconclusive, or mark invalid.
10. Repeat until a stopping condition, hard budget, or maximum round limit.
11. Validate promoted versions on held-out tasks before release.
```

## 6. Acceptance Evidence

Each experiment should retain enough evidence to answer: *what changed, what
happened, and why was the decision justified?*

Minimum candidate evidence:

- parent version and exact candidate diff;
- tuner hypothesis and expected effect;
- task contracts and effective limits;
- agent trajectories and final workspaces;
- quality score and judge evidence per task;
- tokens, turns, useful wall time, retries, and actual model route;
- per-task reward components and suite reward;
- reward delta against the incumbent;
- promotion/rejection/inconclusive/invalid reason.

Minimum release evidence:

- a promoted train-suite result;
- held-out validation result;
- no unresolved reward-hacking finding;
- no critical task regression;
- a versioned manifest and rollback target.

## 7. Open Questions

- How many same-config control rollouts are needed before the noise threshold is
  stable enough to use?
- Should `delta_promote` use maximum observed control drift, a percentile, a
  confidence interval, or another robust statistic?
- Should candidates close to the threshold be confirmed with one additional
  paired rollout?
- Should a large regression in one critical task block promotion even when mean
  suite reward improves?
- How can quality be made less subjective through deterministic verification or
  evaluator ensembles?
- How should model-route variance be controlled while still allowing fallback
  for an unreliable gateway?
- What is the right patience value after reward-delta calibration?
- When should a new promoted version become the baseline for a new experiment?
- How can successful and rejected trajectories later be converted into RLAIF
  preference data without teaching benchmark-specific artifacts?
