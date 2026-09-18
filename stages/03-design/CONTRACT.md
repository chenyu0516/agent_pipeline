# Stage 3 — Experiment design: idea doc → experiment spec

Agent: `experiment-designer` (stub). Gate: `doc-hygiene-reviewer` with stage `experiment`.

## Input

- The idea doc from stage 2 (must have passed both gates).
- `data.md`: what data I actually have access to (source, window, frequency, fields). The spec may not assume data outside this file.

## Output template (sections in this exact order)

```
# Experiment: <idea name>

## Hypotheses
<H1..Hn, each mapped to a prediction Pi from the idea doc>

## Data
<source, universe, window, frequency, fields; cite data.md>

## Procedure
<numbered steps; each step is one function to be written in stage 4>

## Metrics
<each metric defined in LaTeX; what value supports/refutes each Hi>

## Baselines
<at least one null model per hypothesis>

## Leakage and lookahead audit
<for every feature: the timestamp it is known at vs the target timestamp>

## Train / validation / test split
<explicit dates or rule>

## Compute budget
<expected runtime, memory; say if unknown>

## Stop condition
<the result that ends the experiment early, either way>
```

## Rubric

Hard (any → REJECT):
- Every Hi maps to a Pi in the idea doc.
- Every metric has a LaTeX definition.
- Every hypothesis has a baseline.
- Leakage audit lists every feature named in Procedure.
- No data assumed that is not in `data.md`.

Soft (1–5, pass ≥ 3.5): clarity, skimmability, concreteness, math notation, uncertainty honesty.

## Known failure modes (append as they happen)

- Proposes 12 experiments when one would answer the question. → Max 3 hypotheses per spec; split otherwise.
