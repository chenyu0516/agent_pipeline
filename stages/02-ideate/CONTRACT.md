# Stage 2 — Ideate: notes + seed question → idea doc

Agents: `idea-drafter` (stub; uses `clean-proposal-writer` skill for structure) and `idea-reviewer` (stub, adversarial).
Gate: `doc-hygiene-reviewer` with stage `ideate`, then `idea-reviewer`.

## Input

- A seed question, one paragraph, written by me.
- 1–N wiki notes from stage 1 (paths).
- Optional: my scribbled math, any format. The drafter formalizes it, does not replace it.

## Output template (sections in this exact order)

```
# <Idea name>

## Core claim
**<one bolded sentence, quotable out of context>**

## Problem statement
<what is being modeled, what is observed, what is unknown>

## Model
<state variables, parameters, assumptions (numbered A1, A2, ...), objective. LaTeX. Every symbol defined at first use.>

## Derivation sketch
<the key steps; each step names the assumption it uses>

## Testable predictions
<numbered P1, P2, ...; each a statement that data could contradict>

## What would kill it
<for each Pi, the observation that falsifies it>

## Relation to prior work
<per wiki note: what is reused, what is different. Cite the note.>

## Open questions
<things I must decide before stage 3>
```

## Rubric

Hard (any → REJECT):
- Every assumption used in the derivation appears in the numbered list.
- Every prediction has a matching kill condition.
- No empirical number appears anywhere (this is a model doc, not a results doc).
- "Relation to prior work" cites only notes provided in the input.

Soft (1–5, pass ≥ 3.5): clarity, skimmability, concreteness, math notation, uncertainty honesty.

## `idea-reviewer` adds (separate pass, separate output)

- Does the derivation actually follow from the assumptions? Point to the step that does not.
- Which assumption is least plausible for the target market/data, and why.
- What is the null model this must beat, and is it stated.
- Is this already known? Name the closest thing you know of, with `[verify]` tag.

## Known failure modes (append as they happen)

- Drafter "improves" my math into something more standard and loses the idea. → Drafter must quote my original scribble in an appendix and diff against it.
- Predictions are vague ("returns will be more predictable"). → Each Pi must name the quantity, the direction, and the comparison.
