# Feature: Self Optimize Harness

## 1. Objective

The goal of the self-optimization harness is to tune harness components—currently the system prompt and tool descriptions—using observed agent trajectories and cost metrics such as tokens, turns, and wall time. It selects the best-performing harness configuration based on measured outcomes.

This makes improvements to agent trajectories and the harness system evidence-driven, rather than dependent on intuition, guesswork, and manual trial and error.

Current optimization objectives include:

- output quality;
- token usage;
- number of turns;
- agent wall time;
- additional metrics as the system evolves.

## 2. Frameworks

The framework loops included:

```text
Run -> Judge -> Tune -> Decide -> Run -> Judge -> Tune -> Decide -> ...
```

### 2.1 Run phase:

The run phase executes one predefined task with one harness configuration.

For each task, the harness:

1. Creates a clean workspace from the same task seed.
2. Gives the task prompt and the selected configuration to the agent.
3. Runs the agent with a preferable configs.
4. Records the full trajectory: model responses, tool calls, tool results, final, reasoning,
   tokens, turns, tool errors, retries, and wall time.
5. Preserves the final workspace as the artifact to be evaluated.

The run phase measures what the agent actually did. It does not decide whether
the artifact is correct.

### 2.2 Judge phase:

The judge phase evaluates the finished workspace against the task contract and
its rubric.

The judge should:

- inspect the actual artifact rather than trust the agent's final answer;
- run bounded verification only in a temporary copy of the workspace;
- return a quality score, requirement-level evidence, and an evaluation-validity
  status;
- report a reward-hacking penalty only when there is evidence that the agent
  attempted to manipulate evaluation rather than complete the task.

The judge must score achieved purely from artifact quality. A trajectory
can help the judge find relevant files or checks, but it must not become an
unstated grading criterion.


### 2.3 Tune phase:

The tuner reads the active configuration, trajectory summaries, judge
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

### 2.4 Decision phase:

The decision phase requires the reward delta of the candidate config with the incumbent config to be greater than the flucation_metrics (standard deviation during 5 run) and the practical_threshold ( >= 5% of the active config). It can return one of three outcomes:

- **Promote:** the candidate has valid and sufficiently strong evidence of
  improvement.
- **Reject:** the candidate is valid but does not improve enough, or regresses.
- **Invalid:** a provider, runtime, or evaluator failure made the comparison
  unreliable; it should not be treated as an ordinary candidate rejection.

Only a promoted candidate becomes the next active configuration.

## 3. Methodology

### 3.1 Fixed baseline and incumbent

The harness uses two related but different references:

- **Run-start baseline:** the initial active configuration evaluated at the start
  of the run. Its per-task costs remain fixed for reward normalization across all
  candidate rounds.
- **Incumbent:** the highest-scored configuration so far. Each candidate is
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

## 4. Implementation Requirements

For reward comparisons to be meaningful, the following conditions are required:

1. Candidate and incumbent use the same task scope, task budgets, rubric,
   reward function, and fixed cost baseline.
2. Every rollout starts from a clean copy of the same task seed.
3. The judge cannot modify the original workspace during verification.
4. Agent cost, provider failure time, and judge/tuner overhead are recorded as
   separate metrics.
5. Every candidate diff, trajectory, verdict, reward component, and decision should be
   persisted for observation.
6. A train-suite promotion is recommended to get tested through a held-out
   validation.

## 5. Optimization Loop

```text
1. Run the active configuration on a fixed task suite.
2. Judge each resulting workspace and calculate the run-start baseline reward.
3. Run same-config controls when calibrating noise to get the noise fluctuation measurements.
4. Ask the tuner for a candidate change.
5. Validate the candidate mutation surface and prompt budget.
6. Run the candidate on fresh copies of the same task suite.
7. Judge candidate artifacts and calculate reward with the fixed baseline.
8. Calculate candidate Reward_delta against the incumbent.
9. Promote, reject, or mark invalid.
10. Repeat until a stopping condition (fluctuation and practical ensurements) or maximum round limit.
11. Validate promoted versions on held-out tasks before release.
```
## 6. Acceptance Evidence

Each experiment should retain enough evidence to answer: *what changed, what
happened, and why was the decision justified?*

Minimum candidate evidence:

- parent version and candidate diff;
- tuner hypothesis and expected effect;
- task contracts and effective limits;
- agent trajectories and final workspaces;
- quality score and judge evidence per task;
- tokens, turns, useful wall time, retries, and actual model-used;
- per-task reward components and suite reward;
- reward delta against the incumbent;
- promotion/rejection/invalid result.

Minimum release evidence:

- a promoted train-suite result;
- held-out validation result;
- no unresolved reward-hacking finding;
- no critical task regression;
- a versioned manifest and rollback target.
