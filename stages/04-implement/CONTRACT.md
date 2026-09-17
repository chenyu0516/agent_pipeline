# Stage 4 — Implement and run: experiment spec → code + results.md

Agent: `experiment-implementer` (stub). Gate: tests must pass, plus `doc-hygiene-reviewer` on `results.md` with stage `implement`.

## Input

- The experiment spec from stage 3 (passed gate).
- The target repo path and its conventions (existing `CLAUDE.md` in that repo, if any).

## Output

1. Code: one function per Procedure step in the spec, named after the step. Pure functions for computation, one driver script. Seeds fixed and logged.
2. Tests: at least one test per Procedure step on synthetic data with a known answer. One test that asserts no lookahead (feature timestamps < target timestamp).
3. `results.md` using the template below.

## `results.md` template (sections in this exact order)

```
# Results: <idea name>

## Run
<run id, commit hash, command, seed, wall time>

## Data actually used
<rows, date range, universe size; diff against spec if any>

## Per-hypothesis outcome
<Hi: supported / refuted / inconclusive; the metric value; the baseline value; table or figure path>

## Deviations from spec
<every place the implementation differs from the spec, and why>

## Anomalies
<anything odd in the data or outputs, unexplained>

## Verdict for stage 2
<one sentence per Hi: what the idea doc's status should become>
```

## Rubric

Hard (any → REJECT):
- Every number in `results.md` traces to a file or run id.
- Every Hi from the spec appears with an outcome.
- Deviations section exists even if it says "none".
- Tests pass; lookahead test present.

Soft (1–5, pass ≥ 3.5): clarity, skimmability, concreteness, math notation, uncertainty honesty.

## Known failure modes (append as they happen)

- Silently changes the metric to one that looks better. → Deviations section is mandatory; the reviewer diffs metric definitions against the spec.
- Reports only the best seed. → Run section must list all seeds run.
