# agent_pipeline

A checkpointed research pipeline for reading papers, modeling ideas, and testing them in code, run by Claude Code agents with a human at every decision. Each project is one design document with named, linked objects. Every step owns one section, every human gate produces a review bound to a document version, and everything rejected goes to a log that generators must not contradict.

Status: design accepted 2026-09-18 (`PROPOSAL-subworkflows.md` v7). Phase 1 built and self-tested. Phase 2 next: `/ideate`, `/review`, `/reject` skills and the stage 2 agents, first project the Obsidian wiki-management skills.

## Quick start

```
uv sync                                   # once
git config core.hooksPath .githooks       # once per clone
uv run python scripts/doc.py init my-idea --template quant-model --title "My idea"
uv run python scripts/commit.py --all "my-idea/- INIT: project created"
scripts/selftest.sh                       # proves every mechanism in a temporary repo
```

Then fill `work/my-idea/seed.md` and run `/ideate my-idea` once phase 2 lands.

## Where things are

| what | where |
|---|---|
| why the pipeline is shaped this way, and every decision D1–D27 | `PROPOSAL-subworkflows.md` |
| the normative grammar: files, sections, objects, links, versions, ledger, commits, reviews, log, commands | `stages/REFS.md` |
| step tables per stage | `stages/01-read/STEPS.md` … `stages/05-verdict/STEPS.md` |
| end-to-end contracts per stage (input, output template, rubric, known failure modes) | `stages/0N-*/CONTRACT.md` |
| taxonomy templates: quant-model, ml-model, empirical-study, tooling | `stages/templates/` |
| intake templates for seed, scribble, data, questions | `stages/intake/` |
| rules every agent inherits | `CLAUDE.md` |
| agents | `.claude/agents/` (built: `doc-hygiene-reviewer`) |
| tools | `scripts/` (`doc.py`, `ref_checker.py`, `state.py`, `review.py`, `commit.py`, `hooks.py`, `selftest.sh`) |
| git hooks | `.githooks/` |
| projects | `work/<slug>/` |
| cross-project rejection log | `REJECTED-global.md` |
| benchmarks, 3–5 real examples per stage | `benchmarks/` |

## Stages

| # | stage | orchestrator | human gates | intake |
|---|---|---|---|---|
| 1 | read | `/read` | 1a, 1e | when `questions.md` changes |
| 2 | ideate | `/ideate` | 2a, 2c, 2f | `seed.md`, `scribble.md` |
| 3 | design | `/design` | 3b, 3e | `data.md` |
| 4 | implement | `/implement` | 4b | none |
| 5 | verdict | `/verdict` | 5a | none |

## Build phases

| phase | status | contents |
|---|---|---|
| 0 | done | decision register D1–D27 |
| 1 | done, self-tested | `REFS.md`, templates, `STEPS.md` × 5, `doc.py`, `ref_checker.py`, `state.py`, `review.py`, `commit.py`, hooks, `selftest.sh` |
| 2 | next | `/ideate`, `/review`, `/reject` skills; `intake-initializer`, `intake-reviewer`, `doc-keeper`, `plan-reviewer`, `idea-reviewer`, `idea-drafter`, `deriver`, `math-checker`; first project through stage 2 |
| 3 | | `review-converter`, `paper-reader`, `wiki-searcher`, `/read`; five papers |
| 4 | | stages 3–5 agents and skills; one idea to a recorded rewind |
| 5 | | `/review-logs`, prune gates, revisit D12 and D24 |
