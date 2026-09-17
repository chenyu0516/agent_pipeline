# Research Pipeline (top-level map)

Status: DRAFT v0 — confirm stage boundaries and contracts before building agents.

## Why this exists

The failure mode so far: each stage's AI output is not what I want, and I spend the time
policing it (writing hygiene, notation, hallucinated claims). The fix is not a better
prompt. It is a **contract per stage** (what goes in, what must come out, what "good" means)
plus a **gate** that checks the output against the contract before I ever read it.

Method (adapted from thinking.inc "Build an AI agent pipeline"):
1. Map the workflow into granular steps with a cognitive type each.
2. Write the inter-stage contract (input schema → output template + rubric).
3. Design each agent: role, task, quality criteria with examples, constraints, output format.
4. Test each agent alone on 5–10 real inputs before wiring anything together.
5. Only then chain them, with a gate between every pair.

## Workflow map

| # | Step | Cognitive type | Input | Output (contract) | Gate | Runs where |
|---|------|----------------|-------|-------------------|------|------------|
| 1 | Read a paper / frontier result | extraction | PDF / arXiv id + my current questions | Wiki note (`stages/01-read/CONTRACT.md`) | hygiene + citation check | Claude Code → LLM wiki |
| 2 | Brainstorm an idea, math model | generation | 1–N wiki notes + a seed question | Idea doc (`stages/02-ideate/CONTRACT.md`) | hygiene + math check + adversarial review | Claude Code / Codex |
| 3 | Design the experiment | analysis | Idea doc | Experiment spec (`stages/03-experiment/CONTRACT.md`) | leakage/baseline/metric check | Claude Code |
| 4 | Implement and run | generation + verification | Experiment spec | Code + `results.md` (`stages/04-implement/CONTRACT.md`) | tests + reproducibility check | Claude Code |
| 5 | Feed results back | synthesis | `results.md` | Update idea doc status, new wiki note | hygiene check | Claude Code → LLM wiki |

Cross-cutting gate used by every stage: `doc-hygiene-reviewer` (built first, see below).

## Agent roster (target: 5–6, article recommends 3–7)

| Agent | Stage | Model tier | Status |
|-------|-------|-----------|--------|
| `doc-hygiene-reviewer` | all | Sonnet (cheap, runs often) | built (v0) |
| `paper-reader` | 1 | Sonnet | stub |
| `idea-drafter` | 2 | Opus | stub — reuse `clean-proposal-writer` skill for structure |
| `idea-reviewer` (adversarial) | 2 | Opus | stub |
| `experiment-designer` | 3 | Opus | stub |
| `experiment-implementer` | 4 | Sonnet/Opus | stub |

Rule: a **generator never grades its own output**. Every stage has a separate reviewer or the shared hygiene reviewer.

## Contracts

Each `stages/NN-*/CONTRACT.md` has four parts:
1. **Input** — exactly what the agent receives, nothing implicit.
2. **Output template** — the required sections, in order. Missing section = reject.
3. **Rubric** — hard rules (pass/fail) and soft dimensions (1–5). Pass threshold stated.
4. **Known failure modes** — grows every time an output annoys me. This list is the real spec.

## Benchmarks (my homework, not the agent's)

For each stage, collect in `benchmarks/NN-*/`:
- 3–5 real inputs I actually had.
- For each, one output I would have accepted (or an AI output plus my corrections).

Without these, "not what I want" stays unmeasurable. Ten annotated examples beat any prompt.

## Build map

| Phase | Work | Depends on | Done when |
|-------|------|-----------|-----------|
| 0 | Confirm this map; edit stage boundaries | — | I agree the 5 stages are how I actually work |
| 1 | `CLAUDE.md` global rules + `doc-hygiene-reviewer` | 0 | Reviewer rejects 3 of my old bad docs and passes 1 good one |
| 2 | Stage 1 contract + `paper-reader` | 1 | 5 papers → 5 wiki notes I accept with ≤2 edits each |
| 3 | Stage 2 contracts + `idea-drafter` + `idea-reviewer` | 1 | 3 ideas drafted, reviewer catches a planted flaw |
| 4 | Stage 3 + 4 contracts and agents | 3 | one idea goes end-to-end without me rewriting anything |
| 5 | Stage 5 feedback loop, hooks to auto-run the gate | 4 | gate runs on every doc write without me asking |

## Open decisions (fill in)

- LLM wiki tool and note format: ______ (Obsidian? markdown folder? what frontmatter?)
- Where idea docs live: ______
- Code repo layout for experiments: ______
- Which of Claude Code / Codex owns stage 2 drafting: ______
