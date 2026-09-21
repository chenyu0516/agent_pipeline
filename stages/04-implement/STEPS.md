# Stage 4, Implement: steps

Orchestrator: `/implement <slug>`. Code lives in the project's `runs/` and the target repo named in `§implementation`. ⏸ human gate.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 4a | scaffold | `implementer` | `§experiment.procedure` | code skeleton, one stub per procedure step, synthetic-data tests; `§implementation` layout | tests exist and fail for the right reason | tests | retry |
| 4b ⏸ | loader and lookahead test | `implementer`; `plan-reviewer` → human | `§data`, `§experiment.leakage` | loader; test asserting feature timestamp precedes target timestamp; review 4b-r<n> | tests pass on a real-data sample | tests, review | route 4b or 3c |
| 4c | implement, one procedure step per iteration | `implementer` | `§experiment.procedure`, code | function and passing test per step | all tests green | tests | retry per step |
| 4d | run | `implementer` | code | `runs/<id>/` with seed, log, outputs; `§implementation` run entry | run completes; all seeds logged | tests | stop |
| 4e | report | `results-reporter` | `runs/<id>/`, `§experiment.*` | `§results` (per hypothesis, linked; deviations from spec) | every number traces to a run file; every hypothesis present | hygiene | retry |
