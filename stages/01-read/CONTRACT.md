# Stage 1 — Read: paper → wiki note

Agent: `paper-reader` (stub). Gate: `doc-hygiene-reviewer` with stage `read`.

## Input

- The paper: PDF path or arXiv id.
- `questions.md`: my current research questions, 3–10 lines. The note must be written *for these*.
- Optional: 1–3 existing wiki notes the paper should be linked against.

## Output template (sections in this exact order)

```
# <Paper title> (<first author>, <year>)

## One-line claim
<what the paper claims, in my words, one sentence>

## Setup and model
<the formal setup: state variables, assumptions, objective. LaTeX for every defined quantity. Cite eq. numbers.>

## Notation table
| symbol | meaning | defined at |

## Method
<what they actually do, step by step, with section cites>

## Results that matter to me
<only results relevant to questions.md; each with table/figure number>

## Limitations stated by the authors
<cite>

## Limitations I see
<labelled "Inference:">

## Relevance to my questions
<one paragraph per question in questions.md it touches; say "none" for the rest>

## Hooks
<1–5 concrete follow-up questions or extensions, each one sentence>

## Links
<wiki links to related notes>
```

## Rubric

Hard (any → REJECT):
- Every section present, in order.
- Every equation cite resolves to an equation number in the paper.
- Notation table covers every symbol used in the note.
- "Limitations I see" and "Hooks" carry the "Inference:" label or are clearly separated from source claims.
- No result reported that is not in the paper.

Soft (1–5, pass ≥ 3.5): clarity, skimmability, concreteness, math notation, uncertainty honesty.

## Known failure modes (append as they happen)

- Summarizes the abstract instead of the model. → Setup section must contain at least one LaTeX equation with cite.
- Praises the paper ("elegant", "seminal"). → Ban evaluative adjectives in sections 1–6.
- Invents relevance to my questions to seem useful. → "none" is a valid and expected answer.
