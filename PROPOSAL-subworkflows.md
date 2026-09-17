# Proposal: stages as checkpointed sub-workflows

Status: PROPOSAL v3 for decision. Nothing in the repo changes until the decision register at the end is filled in.

Changes from v2: the project document is the primary artifact and each pipeline step owns one section of it. Documents start as one file and split by big section as they grow, with stable section ids so references survive the split. Every file must be readable standalone by a collaborator. Staleness and reference checking work at section level, not file level.

## Hook

The current `PIPELINE.md` treats each stage as one agent call that produces one finished document. Your stages take days, and you discover problems only in that finished document, when everything in it already depends on the mistake. Rejecting a finished idea doc costs you the whole stage. The obvious fix, one file per step, produces a pile of fragments no collaborator can read.

## Core claim

**Each project is one document tree with stable section ids; each pipeline step owns exactly one section, faces its own gate, and is committed to git, so you intervene only at named checkpoints, every rejection or rewind lands on one section, and a collaborator can open any file in the tree cold and read it.**

## Elaboration

A project's knowledge lives in one document with a fixed section taxonomy: problem, position, model, data, experiment, implementation, results, status. At the start the whole document is one file. As sections grow, they move into their own files, and the parent keeps a stub with a summary and a link. Section ids never change when this happens, so every cross-reference and every agent input keeps resolving. The document is load-bearing twice over: a collaborator reads it, and every agent reads only the sections its step names, which keeps agent context small and agent output grounded in what the document actually says.

A pipeline step is then a section owner. Step 2c owns the assumptions and formal model sections; step 2d owns the derivation; step 3c owns procedure and metrics. A step's output is a new version of its sections, never a separate file. Rejected attempts, reviews, and diagnoses are process records, not document content, and live beside the document under `pipeline/`.

Six terms carry the design. A *section* is the unit of ownership, reference, hashing, and staleness. A *gate* is an automated check on a section: hygiene, references, a specialist reviewer, or tests. A *loop edge* sends work back to an earlier step, bounded inside a stage and human-only across stages. The *ledger* is git plus `state.yaml`, and the orchestrator refuses to run when they disagree. A *stale* section is one whose inputs changed since it was built; it stays in the document, marked, until regenerated. A *split* moves a section to its own file without changing its id.

The orchestrator is deliberately dumb. It checks the ledger, extracts the input sections a step names, runs the step's agent, writes the agent's output back into the owned section, runs the gates, commits, and stops at any checkpoint or pending review.

## Structure

### 1. Document taxonomy

Every project document has these top-level sections, in this order. Each has a stable id. Empty sections are allowed early and show as `[pending: step 3c]`.

| id | section | owned by | typical size when mature |
|---|---|---|---|
| `§context` | one paragraph: what this project is, current status, how to read the tree | `doc-keeper` | 10 lines |
| `§problem` | observed, unknown, why it matters, goal | 2a | 30 lines |
| `§position` | closest wiki notes, null model, what is new | 2b | 40 lines |
| `§model` | parent of the four below | 2c–2e | 200–600 lines, first split candidate |
| `§model.notation` | symbol table | 2c | 30 lines |
| `§model.assumptions` | A1.. with provenance tags | 2c | 40 lines |
| `§model.formal` | state, parameters, objective in LaTeX; scribble diff in an appendix | 2c | 60 lines |
| `§model.derivation` | numbered steps, results R1..Rk | 2d | 100–400 lines |
| `§model.predictions` | PA and PR with kill conditions | 2e | 60 lines |
| `§data` | inventory and plan | 3b | 60 lines |
| `§experiment` | parent of the three below | 3a, 3c, 3d | 150–400 lines, second split candidate |
| `§experiment.hypotheses` | H ↔ P mapping | 3a | 30 lines |
| `§experiment.procedure` | steps, features F, metrics M, baselines, split | 3c | 100 lines |
| `§experiment.leakage` | per-feature timestamp audit | 3d | 40 lines |
| `§implementation` | layout, run ids, deviations | 4a, 4d | 60 lines |
| `§results` | per-H outcome, tables, anomalies | 4e | 100 lines |
| `§status` | decision log: reviews resolved, rewinds, untested own assumptions | orchestrator | grows forever |

Your ML example maps directly: data is `§data`, model architecture is `§model`, train and test is `§experiment` plus `§implementation`. Decision D15 asks whether this taxonomy is right for your work or should be a per-project template.

Stage 1 uses the same mechanism on a smaller document: a wiki note with sections `§claim`, `§setup`, `§method`, `§results`, `§relevance`, `§hooks`.

### 2. Files, splitting, and standalone readability

A project starts as `work/<slug>/docs/DESIGN.md` containing every section. When a file exceeds its budget, `/split §model` moves that section and its children to `docs/model.md`, leaves a stub in `DESIGN.md`, and updates `docs/INDEX.yaml`. Nested splits work the same way: `docs/model/derivation.md`.

```yaml
# docs/INDEX.yaml, maintained by doc-keeper, read by everything
sections:
  §context:            {file: DESIGN.md}
  §problem:            {file: DESIGN.md}
  §model:              {file: model.md, stub_in: DESIGN.md}
  §model.derivation:   {file: model/derivation.md, stub_in: model.md}
  §experiment:         {file: DESIGN.md}
budget: {lines: 400}
```

A stub is a heading, a three-sentence summary, and the link. The summary is written by `doc-keeper` and regenerated when the child changes.

Every file must be readable on its own. The rule is enforced by three hard checks:

1. The file opens with a `Context` block: the project one-liner, what this file covers, what it depends on with links, and its current status. Four sentences at most.
2. Every symbol the file uses is defined in the file or the file links `§model.notation` in its Context block.
3. Every reference to another section is written as `§id` and resolves through `INDEX.yaml`. The hygiene reviewer gets a new soft dimension, *standalone*, scored as "could a collaborator with only this file and its linked notation follow it".

Split triggers, checked by `doc-keeper` at every orchestrator run: a file over budget, or a section with three or more children each over sixty lines. Merging back is allowed when a file falls under a quarter of budget, but is rare. Decision D14 sets the budget.

When someone wants the whole thing in one piece, `scripts/doc.py export` concatenates every file in `INDEX.yaml` order, replacing stubs with the full sections, into `export/<slug>-full.md`. That export is regenerated at every stage tag and is what you send to a collaborator who does not want to navigate the tree.

### 3. Step schema

Every step in every stage is one row with the same seven fields.

| field | meaning |
|---|---|
| id | stage number plus letter, `2c` |
| owner | agent name, `human`, or `agent → human` when an agent drafts and you accept |
| input | section ids and files, nothing implicit; the orchestrator extracts exactly these |
| output | the section ids this step owns and may write |
| pass rule | one sentence; what the gate checks |
| gate | `hygiene`, a reviewer agent name, `tests`, or `human`; `refs` runs on every step and is not repeated |
| on fail | `retry` (once, with gate findings appended), `→ 2c` (loop edge), or `stop` |

### 4. Ledger: git plus state.yaml

`work/<slug>/` is inside a git repository. Every section version, rejected attempt, review, human decision, split, and rewind is a commit. `state.yaml` is an index that must match the git log.

```yaml
slug: vol-regime-kalman
stage: ideate
head: 3f9c2a1
steps:
  2a: {status: done, sections: [§problem], gate: human, commit: a1b2c3d}
  2c: {status: done, sections: [§model.notation, §model.assumptions, §model.formal],
       attempts: 2, commit: c3d4e5f,
       built_from: {§problem: 9e1f..., scribble.md: 77ab..., §position: 12cd...}}
  2d: {status: stale, sections: [§model.derivation], commit: d4e5f6a,
       built_from: {§model.assumptions: 41cc..., §model.formal: 8a2b...},
       stale_reason: "§model.assumptions changed at c3d4e5f"}
  2e: {status: pending}
open_reviews: [pipeline/reviews/2f-r1.md]
loops: {2f->2c: 1}
rewinds: []
```

`built_from` hashes are per section, so a hand edit to `§data` never stales `§model.derivation`. This is the main reason staleness is tolerable in practice.

**Commit rules.** Enforced by `commit-msg` and `pre-commit` hooks. Decision D10 asks how strict.

1. One step per commit. The diff may touch only the sections that step owns, plus `state.yaml`. The hook checks changed section ids against the step's ownership. `HUMAN` and `SPLIT` commits are exempt from ownership but not from format.
2. The tree must be clean before any step runs.
3. Message format: `<slug>/<step> <VERB>[ a<n>]: <one line>`. Verbs: `PASS`, `REJECT`, `HUMAN`, `REVIEW`, `RESOLVE`, `LOOP`, `REWIND`, `STALE`, `SPLIT`, `EXPORT`.
4. Rejected attempts are committed as `REJECT` to `pipeline/attempts/<step>-a<n>.md` with the gate findings in the body.
5. Human edits to any section are committed as `HUMAN` with a reason. The orchestrator re-runs every gate on the touched sections before proceeding.
6. Reviews are append-only: `pipeline/reviews/<step>-r<n>.md`, status `pending`, committed as `REVIEW`. Your decision is appended and committed as `RESOLVE`.
7. Cross-stage rollbacks are committed as `REWIND` with from, to, reason. No amend, rebase, force push, or reset on `work/`.
8. Stage completion is tagged `<slug>/<stage>-done` and triggers an `EXPORT` commit.
9. `state.yaml` records `head`; on mismatch the orchestrator rebuilds the index from the log and asks you to confirm.

### 5. Orchestrator

One slash command per stage: `/read`, `/ideate`, `/design`, `/implement`, `/verdict`, plus `/split`. Behavior, in order:

0. **Consistency.** Tree clean; `state.yaml` head equals HEAD; last commit's step equals the last state entry.
1. **References and staleness.** Recompute section hashes; resolve every `§id`; mark stale where `built_from` differs; check file budgets and propose splits; commit `STALE` if anything changed.
2. **Blockers.** Pending review, or next step is a checkpoint: print the section or review path and the decision needed, then stop.
3. **Run.** Extract the input sections with `doc.py get`, run the step's agent as a subagent with those and nothing else, write its output into the owned sections with `doc.py put`.
4. **Gate.** On fail, commit `REJECT`, retry once with findings appended. Second fail: stop and show findings.
5. **Commit.** On pass, commit `PASS` with `state.yaml`, continue unless the next step is a checkpoint.
6. **Bounds.** When an in-stage loop edge has hit its maximum, force a checkpoint.

The orchestrator has no research tools. It may write only `state.yaml` and may call only `doc.py` and git.

### 6. Stage decompositions

Checkpoints are marked ⏸. Inputs and outputs are section ids. `refs` gate is implicit on every step.

**Stage 1, Read.** `/read <pdf-or-arxiv-id>`. The document is the wiki note.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 1a ⏸ | triage | `paper-reader` → human | pdf, `questions.md` | `§claim`, `pipeline/triage.md` | you say read | human | stop, archive |
| 1b | extract model | `paper-reader` | pdf | `§setup` (assumptions, LaTeX with eq cites, notation table) | every symbol in table; every equation cited | hygiene | retry |
| 1c | extract method + results | `paper-reader` | pdf, `§setup` | `§method`, `§results` | no number without a cite | hygiene | retry |
| 1d | relate | `wiki-searcher` | `§setup`, `§method`, `§results`, `questions.md`, wiki | `§relevance`, `§hooks` | "none" allowed; Inference labels present; cites only existing notes | hygiene | retry |
| 1e ⏸ | finalize | `doc-keeper` → human | all | `§context`; note passes full contract | full template; standalone | hygiene, human | retry |

**Stage 2, Ideate.** `/ideate <slug>`.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 2a ⏸ | frame | `idea-drafter` → human | `seed.md` | `§problem` | you accept | human | you edit `seed.md` |
| 2b | position | `wiki-searcher` | `§problem`, wiki | `§position` | null model named; cites only existing notes; "nothing close in wiki" valid | hygiene | retry |
| 2c ⏸ | formalize | `idea-drafter` → human | `§problem`, `§position`, `scribble.md` | `§model.notation`, `§model.assumptions` (each A tagged `[lit]`, `[standard]`, `[own]`), `§model.formal` (with scribble diff appendix) | every A tagged; diff present; math rules; you confirm nothing lost | hygiene, human | you edit |
| 2d | derive | `deriver` | `§model.notation`, `§model.assumptions`, `§model.formal` | `§model.derivation` (steps cite Ai; results R1..Rk) | every step cites an Ai; no unlisted assumption | `math-checker` | → 2c if an assumption is missing |
| 2e | predict | `idea-drafter` | `§model.assumptions`, `§model.derivation` | `§model.predictions` (PA per `[own]` A, PR per R, kill conditions) | every `[own]` A has a PA or is marked `untestable, accepted`; every R has a PR; no empirical numbers | hygiene | retry |
| 2f ⏸ | adversarial review | `idea-reviewer` → human | `§problem` through `§model.predictions` | `pipeline/reviews/2f-r<n>.md`, pending | you resolve: accept / → 2c / → 2d / abandon | human | loop, bound 3 |
| 2g | finalize | `doc-keeper` | all | `§context`, `§status` entry, stubs refreshed, export | file budgets respected; standalone | hygiene | retry |

What 2d does: it takes the formal model and produces the chain of consequences from the assumptions to results R1..Rk, each step naming the assumption it uses, so a reader sees which assumptions are load-bearing. If it needs an assumption not in `§model.assumptions`, it routes to 2c rather than adding it. What 2e does: it converts each result and each own assumption into a statement data can contradict, with a quantity, a direction, a comparison, and a kill condition. Own assumptions enter the pipeline here and earn their place by being tested in stage 3, not by citation.

**Stage 3, Design.** `/design <slug>`.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 3a | map hypotheses | `experiment-designer` | `§model.predictions` | `§experiment.hypotheses` (H per PA, max 3 PR-hypotheses) | every PA has an H; every H maps to a P | hygiene | retry |
| 3b ⏸ | data | `experiment-designer` → human | `§experiment.hypotheses`, `data.md` | `§data` (inventory, plan, gaps) | no field outside `data.md`; gaps explicit | human | you resolve gaps |
| 3c | procedure | `experiment-designer` | `§experiment.hypotheses`, `§data`, `§model.notation` | `§experiment.procedure` (steps, F, M in LaTeX, baselines, split) | every H has a metric and a baseline | hygiene | retry |
| 3d | leakage audit | `leakage-auditor` | `§experiment.procedure` | `§experiment.leakage` | every F listed; no violation | `leakage-auditor` | → 3c |
| 3e ⏸ | finalize | `doc-keeper` → human | all | `§context`, `§status`, stubs, export | budgets; standalone | hygiene, human | retry |

**Stage 4, Implement.** `/implement <slug>`.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 4a | scaffold | `implementer` | `§experiment.procedure` | code skeleton, synthetic tests; `§implementation` layout | tests exist and fail for the right reason | tests | retry |
| 4b ⏸ | loader + lookahead test | `implementer` → human | `§data`, `§experiment.leakage` | loader; lookahead test | tests pass on a real-data sample | tests, human | retry |
| 4c | implement, one step per iteration | `implementer` | `§experiment.procedure`, code | function + test per procedure step | all tests green | tests | retry per step |
| 4d | run | `implementer` | code | `runs/<id>/`; `§implementation` run entry | run completes; seeds logged | tests | stop |
| 4e | report | `results-reporter` | `runs/<id>/`, `§experiment.*` | `§results` (per H; deviations) | every number traces to a run file; every H present | hygiene | retry |

**Stage 5, Verdict.** `/verdict <slug>`. Yours alone.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 5a | diagnose | `results-reporter` | `§results`, `§experiment.*`, `§model.*` | `pipeline/diagnosis-<n>.md` (each refuted H traced to an A or R; candidate causes with evidence; no recommendation) | every refuted H traced; no verdict | hygiene | retry |
| 5b ⏸ | decide | human | diagnosis, everything | decision appended to the diagnosis | you decided | human | — |
| 5c | record | orchestrator + `doc-keeper` | 5b | `REWIND` or tag; `state.yaml` rewinds; stale marks; `§status` entry; wiki note on confirm or abandon; export | ledger consistent | refs | stop |

| decision at 5b | rewind to | marked stale |
|---|---|---|
| confirmed | tag `<slug>/confirmed` | nothing |
| implementation wrong | 4c | `§implementation` runs, `§results` |
| design wrong | 3c | `§experiment.leakage`, stage 4 sections |
| assumption falsified | 2c, Ai named | `§model.derivation` onward |
| framing wrong | 2a | everything after `§problem` |
| abandon | tag `<slug>/abandoned` | nothing; `§status` and wiki record why |

### 7. Gate types

- **hygiene**: `doc-hygiene-reviewer`, on every prose section, now with a *standalone* dimension.
- **refs**: `ref_checker.py`, deterministic. Resolves every `§id` and token (`A3`, `R1`, `PA2`, `H2`, `F4`, `M1`, wiki links, notation symbols) through `INDEX.yaml` and the notation table; compares per-section `built_from` hashes; checks Context blocks and file budgets. Runs at orchestrator start and as a `post-commit` hook after `HUMAN` and `SPLIT` commits.
- **specialist reviewer**: `math-checker`, `idea-reviewer`, `leakage-auditor`.
- **tests**: pytest, stage 4.
- **human**: ten checkpoints.

### 8. Agent roster

| agent | steps | model | notes |
|---|---|---|---|
| `doc-hygiene-reviewer` | all prose | Sonnet | built; add standalone dimension |
| `ref-checker` | all | script | no LLM |
| `doc-keeper` | 1e, 2g, 3e, 5c, `/split` | Sonnet | writes `§context`, stubs, `INDEX.yaml`, exports, wiki notes; never writes owned sections |
| `wiki-searcher` | 1d, 2b | Sonnet | only agent with wiki access |
| `paper-reader` | 1a–1c | Sonnet | only agent that reads PDFs |
| `idea-drafter` | 2a, 2c, 2e | Opus | `clean-proposal-writer` rules; tags provenance |
| `deriver` | 2d | Opus | math only; may not add assumptions |
| `math-checker` | gate for 2d | Opus | |
| `idea-reviewer` | 2f | Opus or Codex | append-only reviews; D8 |
| `experiment-designer` | 3a–3c | Opus | H for every PA |
| `leakage-auditor` | 3d | Sonnet | |
| `implementer` | 4a–4d | Sonnet, Opus for 4c | |
| `results-reporter` | 4e, 5a | Sonnet | diagnoses without recommending |

### 9. Repository layout

```
agent/                              # git repository
  CLAUDE.md  PIPELINE.md
  stages/REFS.md                    # §id grammar, token grammar, taxonomy template
  stages/0N-*/CONTRACT.md STEPS.md
  .claude/agents/<name>.md
  .claude/skills/{read,ideate,design,implement,verdict,split}/SKILL.md
  .githooks/commit-msg pre-commit post-commit
  scripts/doc.py                    # get/put sections, split, export, budgets
  scripts/ref_checker.py  scripts/state.py
  work/<slug>/
    docs/DESIGN.md                  # starts with everything
    docs/model.md  docs/model/derivation.md   # after splits
    docs/INDEX.yaml
    export/<slug>-full.md           # regenerated at stage tags
    pipeline/state.yaml attempts/ reviews/ diagnosis-1.md triage.md
    seed.md scribble.md data.md questions.md
    runs/<id>/
  benchmarks/0N-*/
```

## Process: one project from a single file to a split tree

**Week 1.** `DESIGN.md` is 120 lines: `§context`, `§problem`, `§position`, `§model.*` with notation, four assumptions, the formal model, and a 40-line derivation. Everything else reads `[pending]`. A collaborator can read the file top to bottom.

**Week 3.** The derivation is 300 lines after two loops through 2c. `DESIGN.md` is at 520 lines, over budget. The orchestrator proposes a split; you run `/split §model`. `doc-keeper` moves `§model` and children to `docs/model.md`, writes a three-sentence stub in `DESIGN.md`, updates `INDEX.yaml`, commits `SPLIT`. Nothing else changes; `§model.derivation` still resolves. `model.md` opens with a Context block saying what project it belongs to, that it covers notation through predictions, and that it depends on `§problem`.

**Week 4.** You hand-edit A3 in `model.md`. The post-commit hook runs the ref-checker, which stales only `§model.derivation` and `§model.predictions`, not `§data` or `§experiment`. `/ideate` regenerates the two stale sections through their gates.

**Week 6.** Stage 4 runs. `§results` says H3, the test of PA3, is refuted. `/verdict` produces a diagnosis; you decide "assumption falsified". `REWIND 4e->2c: A3 refuted by H3, runs/r7` is committed, `§status` gets a dated entry, `§model.derivation` onward is marked stale. A collaborator opening `DESIGN.md` sees the status in `§context`, the rewind in `§status`, and stale markers on affected stubs.

**Handing over.** You tag `ideate-done`; `export/<slug>-full.md` is regenerated with every stub replaced by its full section. That single file is what you send.

## Why it works, and why it could fail

The mechanism works because ownership, reference, hashing, and readability all share one unit, the section. A step can only write its section, so one bad step cannot corrupt the document. A reference is a stable id, so splitting a file never breaks anything. A hash is per section, so a hand edit stales only what depends on it. And a file is a set of sections with a Context block, so it reads standalone whether it is the whole project or one branch of it. The article's per-agent isolation testing falls out for free: a step's benchmark is its input sections and its accepted output section.

Failure modes, in order of likelihood:

- **Over-specification.** Guard: one-line pass rules; full rubrics at the stage level only.
- **Premature splitting.** The tree fragments before there is enough content to justify it, and readability drops. Guard: split only on budget; `doc-keeper` may propose, never execute; merging back is allowed.
- **Stubs rot.** Parent summaries drift from child content. Guard: stub regeneration is part of every `PASS` on a child section, and the ref-checker hashes stubs against children.
- **Git discipline erodes.** Guard: hooks reject bad messages and out-of-ownership diffs; the consistency check is the second line.
- **Orchestrator drift.** Guard: no tools beyond `doc.py`, git, and `state.yaml`.
- **Gate fatigue.** Guard: reject rate per step from the log; above 50%, loosen the rule.
- **Own assumptions never get tested.** Guard: `experiment-designer` must create an H per PA; `§status` lists untested own assumptions permanently.
- **Wrong split of steps.** Guard: merge a step after ten runs without a rejection.
- **Taxonomy mismatch.** A project does not fit the eight sections. Guard: D15 allows a per-project template, but ids used by steps must exist.

## Close

### Synthesis

The pipeline keeps its five stages and per-stage contracts. Inside each stage, steps own sections of one project document rather than producing separate files. The document starts as a single readable file and splits by big section under a size budget, with stable ids so nothing breaks and Context blocks so every file stands alone. Git holds every version, attempt, review, split, and decision under a fixed commit grammar. Ideas that are not in the literature enter through tagged own assumptions and earn their place by being tested. When an experiment refutes something, you alone decide how far back to rewind, and staleness is computed per section without deleting anything. You appear at ten checkpoints and nowhere else, and a collaborator can open any file cold.

### Decision register

| id | decision | options | recommend |
|---|---|---|---|
| D1 | step granularity | (a) as proposed; (b) coarser; (c) finer | (a) |
| D2 | state format | (a) `state.yaml` indexed to git; (b) derive from git log only; (c) SQLite | (a) |
| D3 | orchestrator | (a) skill per stage; (b) Python driver; (c) both, skill first | (c) |
| D4 | checkpoints | (a) all ten; (b) drop 1e, 3e, 4b; (c) only 2a, 2c, 2f, 5b | (a) for a month, then prune |
| D5 | where `work/` lives | (a) this repo; (b) wiki; (c) experiment repo | (a) |
| D6 | in-stage loop bound | 2 / 3 / unbounded | 3 |
| D7 | build order | (a) stage 2 first; (b) stage 1 first; (c) `doc.py`, ledger, ref-checker first, then stage 2 | (c) |
| D8 | Codex's role | (a) none; (b) reviewers on Codex; (c) Codex drafts | (b) |
| D9 | wiki tool and note format | your answer | needed for `wiki-searcher` |
| D10 | commit enforcement | (a) hooks reject; (b) hooks warn, orchestrator refuses; (c) convention | (a) |
| D11 | staleness | (a) any change to an input section stales dependents; (b) only changes to referenced tokens; (c) (a) plus "re-verify only" | (c) |
| D12 | rewind authority | (a) human at 5b only; (b) `idea-reviewer` may propose at 2f; (c) any gate may propose | (a) now |
| D13 | own assumptions | (a) PA or explicit "accepted untested" in `§status`; (b) PA mandatory | (a) |
| D14 | file budget | 300 / 400 / 600 lines; child-split trigger at 3 children over 60 lines | 400; keep the child trigger |
| D15 | taxonomy | (a) fixed eight sections for all projects; (b) per-project template chosen at `/ideate` init from 2–3 templates (quant model, ML model, empirical study); (c) free-form with required ids only | (b) |
| D16 | export format | (a) single markdown; (b) markdown plus PDF via pandoc; (c) markdown plus wiki page | (a) now, (c) after D9 |

### Build map

| component | how it gets built |
|---|---|
| `stages/REFS.md` | §id grammar, token grammar, taxonomy templates per D15 |
| `scripts/doc.py` | get/put by §id, split/merge, stub regeneration, budget check, export |
| commit grammar + hooks | `.githooks/`; pre-commit checks ownership via `doc.py diff` |
| `state.py`, `ref_checker.py` | per-section hashing via `doc.py`; INDEX resolution |
| `STEPS.md` × 5 | the tables above, adjusted per D1, D4 |
| orchestrators × 5 + `/split` | one skill each; `/ideate` first |
| `doc-keeper` | Context blocks, stubs, INDEX, export, wiki notes |
| `doc-hygiene-reviewer` update | add standalone dimension and Context-block check |
| stage 2 agents | each tested on 3 benchmark seeds |
| `paper-reader`, `wiki-searcher` | after D9 |
| stage 3, 4, 5 agents | after stage 2 runs end to end |
| `/review-logs` | weekly listing of `REJECT` commits per step |
| `PIPELINE.md` shrink | pointers to `STEPS.md` and `REFS.md` |

### Timeline

| phase | components | depends on | duration |
|---|---|---|---|
| 0 | decision register D1–D16 | you | 1 sitting |
| 1 | `REFS.md`, `doc.py`, hooks, `state.py`, `ref_checker.py`, `STEPS.md` × 5; a fake project split and exported by hand | 0 | 3 days |
| 2 | `/ideate`, `doc-keeper`, stage 2 agents, 3 seeds, one idea through with a loop, a hand edit, and a split | 1, D8, D9 | 1 week |
| 3 | `paper-reader`, `wiki-searcher`, `/read`, 5 papers | 2 | 3 days |
| 4 | stages 3–5 agents and skills, one idea to a recorded rewind and an export | 3 | 1 week |
| 5 | `/review-logs`, prune checkpoints, revisit D12 | 4 | ongoing |
