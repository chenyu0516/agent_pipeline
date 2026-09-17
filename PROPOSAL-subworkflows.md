# Proposal: stages as checkpointed sub-workflows

Status: PROPOSAL v4 for decision. Nothing in the repo changes until the decision register at the end is filled in.

Changes from v3: a review is a change request bound to one version of the single design document. Every human gate produces exactly one review, drafted by a reviewer agent and finished by you. A review stays pending until a later version of the document has applied every item in it, verified by the reviewer and confirmed by you. Stage 5's diagnosis becomes the draft of the stage 5 review. Rewinds and in-stage loops are both just reviews with a routing target.

## Hook

The current `PIPELINE.md` treats each stage as one agent call that produces one finished document. Your stages take days, and you discover problems only in that finished document, when everything in it already depends on the mistake. Rejecting a finished idea doc costs you the whole stage. The obvious fix, one file per step, produces a pile of fragments no collaborator can read, and a decision made in a chat window that nobody can find later.

## Core claim

**Each project is one design document with stable section ids; each pipeline step owns one section; every human gate produces one review bound to one document version, co-authored by a reviewer agent and you, that stays pending until a later version has applied it; so every decision is recorded against the exact text it judged, and the pipeline always knows what it is waiting for.**

## Elaboration

A project's knowledge lives in one design document with a fixed section taxonomy. At the start it is one file. As sections grow, they move into their own files with stubs left behind, and section ids never change, so it remains one document with one version history. The document is load-bearing twice over: a collaborator reads it, and every agent reads only the sections its step names.

A pipeline step is a section owner. Its output is a new version of its sections, committed to git. Automated gates check the section immediately. Human gates work differently: they produce a **review**.

A review is a change request against a specific version of the document. A reviewer agent drafts it: findings, each anchored to a section and a document hash, with a proposed required change and a proposed routing target. You finish it: delete findings you disagree with, add your own, set the verdict, and set where the pipeline restarts. The review is committed and becomes pending. The orchestrator then runs only the routed step, with the review as an input. When that step and everything downstream have passed their gates again, the reviewer agent checks each item against the new version and marks it addressed or not. You confirm, and the review becomes applied, recorded with the version that applied it. An accept is a review with zero items that is applied immediately.

This makes one object carry every decision: in-stage loops, cross-stage rewinds, hand-edit requests, and accepts. The `§status` section of the document lists them all with versions, so a collaborator can see what was judged, when, against which text, and what changed as a result.

Seven terms carry the design. A *section* is the unit of ownership, reference, hashing, and staleness. An *automated gate* checks a section without you. A *review* is the output of a human gate, bound to a version. A *routing target* is the step a review restarts. The *ledger* is git plus `state.yaml`. A *stale* section is one whose inputs changed since it was built. A *split* moves a section to its own file without changing its id.

## Structure

### 1. Document taxonomy

Every design document has these top-level sections in this order, each with a stable id. Empty sections show as `[pending: step 3c]`.

| id | section | owned by |
|---|---|---|
| `§context` | project one-liner, status, how to read the tree | `doc-keeper` |
| `§problem` | observed, unknown, why it matters, goal | 2a |
| `§position` | closest wiki notes, null model, what is new | 2b |
| `§model.notation` | symbol table | 2c |
| `§model.assumptions` | A1.. with provenance tags `[lit]`, `[standard]`, `[own]` | 2c |
| `§model.formal` | state, parameters, objective in LaTeX; scribble diff appendix | 2c |
| `§model.derivation` | numbered steps citing Ai; results R1..Rk | 2d |
| `§model.predictions` | PA per own assumption, PR per result, kill conditions | 2e |
| `§data` | inventory, plan, gaps | 3b |
| `§experiment.hypotheses` | H ↔ P mapping | 3a |
| `§experiment.procedure` | steps, features F, metrics M, baselines, split | 3c |
| `§experiment.leakage` | per-feature timestamp audit | 3d |
| `§implementation` | layout, run ids, deviations | 4a, 4d |
| `§results` | per-H outcome, tables, anomalies | 4e |
| `§status` | every review: version judged, verdict, route, version applied; untested own assumptions | orchestrator |

Your ML example maps directly: data is `§data`, model architecture is `§model.*`, train and test is `§experiment.*` plus `§implementation`. Decision D15 asks whether the taxonomy is fixed or chosen per project from a few templates. Stage 1 uses the same mechanism on a wiki note with sections `§claim`, `§setup`, `§method`, `§results`, `§relevance`, `§hooks`.

### 2. Files, splitting, and standalone readability

A project starts as `work/<slug>/docs/DESIGN.md` containing every section. When a file exceeds its budget, `/split §model` moves that section and its children to `docs/model.md`, leaves a stub, and updates `docs/INDEX.yaml`, which maps every id to its file. A stub is a heading, a three-sentence summary regenerated whenever the child changes, and a link.

Every file must be readable on its own. Three hard checks: the file opens with a Context block of at most four sentences naming the project, what the file covers, what it depends on with links, and its status; every symbol used is defined in the file or `§model.notation` is linked in the Context block; every cross-reference is written as `§id` and resolves through the index. The hygiene reviewer scores a *standalone* dimension.

Split triggers, checked at every orchestrator run: a file over budget, or a section with three or more children each over sixty lines. `doc-keeper` proposes; you run `/split`. Merging back is allowed. `scripts/doc.py export` concatenates the tree in index order into `export/<slug>-full.md`, regenerated at every stage tag, for a collaborator who wants one file. Decision D14 sets the budget.

### 3. Review object

One file per review, append-only, at `pipeline/reviews/<step>-r<n>.md`.

```yaml
---
id: 2f-r1
step: 2f                          # the human gate that produced it
doc_version: c3d4e5f              # commit of docs/ that was judged
sections_judged:
  §model.assumptions: 41cc...     # hash at doc_version
  §model.derivation: 8a2b...
authors: [idea-reviewer, chen-yu]
verdict: revise                   # accept | revise | abandon
route_to: 2c                      # first step to rerun; omitted on accept
status: pending                   # pending | applied | waived | superseded
applied_version: null             # commit that closed it
items:
  - id: I1
    section: §model.assumptions
    finding: "A3 assumes volatility persistence above 0.9 with no source"
    required: "Tag A3 [own]; add PA3 in §model.predictions with a measurable threshold"
    status: open                  # open | addressed | waived
    addressed_at: null
  - id: I2
    section: §model.derivation
    finding: "Step 4 uses a bound that is not A1–A4"
    required: "Add the bound as A5 with provenance, or rewrite step 4"
    status: open
---
<prose: the reviewer's draft, then your edits, in order; nothing is deleted, edits are appended>
```

Rules for the object:

1. It binds to exactly one document version and one hash per judged section. If any judged section changes by a route other than the one the review prescribes, the ref-checker marks the review `stale` and you decide: re-review or continue.
2. Every item names one section and one required change. A finding without a required change is a comment, not an item, and does not block.
3. Only you set `verdict` and `route_to`. The reviewer agent proposes both; the orchestrator refuses a review whose author list lacks you.
4. At most one review is pending per project. The next human gate cannot open a new review until the current one is applied or waived. Decision D18.
5. A review is applied when every item is `addressed` or `waived` and you confirm. The reviewer agent that drafted it runs in verify mode against the new version and proposes per-item status; you confirm or override. Decision D17.
6. An accept is a review with no items, `verdict: accept`, applied at its own `doc_version`.
7. A review whose route crosses a stage boundary is a rewind. It is the same object; the commit verb differs.

### 4. Step schema

| field | meaning |
|---|---|
| id | stage number plus letter |
| owner | agent name, or `reviewer → human` at a human gate |
| input | section ids and files; at a routed step, the pending review is always added |
| output | the section ids this step owns, or a review at a human gate |
| pass rule | one sentence |
| gate | `hygiene`, a reviewer agent, `tests`, or `review` (human gate); `refs` is implicit everywhere |
| on fail | `retry`, or, at a human gate, whatever `route_to` says |

### 5. Ledger: git plus state.yaml

`work/<slug>/` is inside a git repository. Every section version, rejected attempt, review, review application, split, and export is a commit. `state.yaml` indexes the log and must match it.

```yaml
slug: vol-regime-kalman
stage: ideate
head: 3f9c2a1
steps:
  2c: {status: done, sections: [§model.notation, §model.assumptions, §model.formal],
       attempts: 2, commit: c3d4e5f,
       built_from: {§problem: 9e1f..., scribble.md: 77ab..., §position: 12cd...}}
  2d: {status: stale, sections: [§model.derivation], commit: d4e5f6a,
       built_from: {§model.assumptions: 41cc..., §model.formal: 8a2b...},
       stale_reason: "review 2f-r1 routed to 2c"}
pending_review: pipeline/reviews/2f-r1.md
reviews:
  - {id: 2a-r1, verdict: accept, doc_version: a1b2c3d, applied_version: a1b2c3d}
  - {id: 2c-r1, verdict: accept, doc_version: c3d4e5f, applied_version: c3d4e5f}
  - {id: 2f-r1, verdict: revise, route_to: 2c, doc_version: e5f6a7b, status: pending}
loops: {2f->2c: 1}
```

**Commit rules.** Enforced by hooks. Decision D10.

1. One step per commit; the diff may touch only that step's sections plus `state.yaml`. `HUMAN` and `SPLIT` are exempt from ownership, not from format.
2. Tree clean before any step runs.
3. Message: `<slug>/<step> <VERB>[ a<n>][ <review-id>]: <one line>`. Verbs: `PASS`, `REJECT`, `HUMAN`, `REVIEW`, `APPLY`, `WAIVE`, `LOOP`, `REWIND`, `STALE`, `SPLIT`, `EXPORT`.
4. Rejected attempts commit as `REJECT` to `pipeline/attempts/`, findings in the body.
5. Hand edits commit as `HUMAN` with a reason; all gates rerun on the touched sections; any pending review whose judged sections were touched is marked stale.
6. A review commits as `REVIEW <id>` at creation, `APPLY <id>` at application, `WAIVE <id>` if abandoned unapplied. The `APPLY` commit records `applied_version`.
7. `LOOP <id>` when a review routes within a stage; `REWIND <id>` when it crosses stages. Both reference the review that caused them. No amend, rebase, force push, or reset on `work/`.
8. Stage completion tags `<slug>/<stage>-done` and triggers `EXPORT`.
9. `state.yaml` records `head`; on mismatch the orchestrator rebuilds from the log and asks you to confirm.

### 6. Orchestrator

One slash command per stage, `/read`, `/ideate`, `/design`, `/implement`, `/verdict`, plus `/split` and `/review`. Behavior, in order:

0. **Consistency.** Tree clean; `state.yaml` head equals HEAD; last commit matches last state entry.
1. **References and staleness.** Rehash sections; resolve every `§id`; mark stale; check budgets; mark stale reviews; commit `STALE` if anything changed.
2. **Pending review.** If one exists, the only runnable step is its `route_to`, followed by every step downstream of it. When the last downstream step passes, run the drafting reviewer in verify mode, write per-item proposals into the review, and stop for your confirmation. On confirmation, commit `APPLY`.
3. **Human gate.** If the next step is a human gate, run its reviewer agent in draft mode against the current version, write the review with `status: draft`, print the path, and stop. You edit and run `/review commit`, which validates the object and commits `REVIEW`. If `verdict: accept`, it is applied at once and the orchestrator continues; if `revise`, step 2 applies from now on; if `abandon`, tag and stop.
4. **Run.** Extract input sections with `doc.py get`, add the pending review if the step is routed, run the agent, write output with `doc.py put`.
5. **Automated gate.** On fail, `REJECT`, retry once with findings appended; second fail stops.
6. **Commit.** `PASS` with `state.yaml`; continue unless the next step is a human gate.
7. **Bounds.** When the same route has fired its maximum, the next review must carry `verdict: abandon` or an explicit bound override from you.

The orchestrator has no research tools. It may write only `state.yaml`, call `doc.py` and git, and invoke agents.

### 7. Stage decompositions

Human gates are marked ⏸ and always produce a review. `refs` is implicit.

**Stage 1, Read.** `/read <pdf-or-arxiv-id>`. The document is the wiki note.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 1a ⏸ | triage | `paper-reader` drafts `§claim`; `plan-reviewer` → human | pdf, `questions.md` | `§claim`; review 1a-r<n> | verdict accept means read | review | abandon archives |
| 1b | extract model | `paper-reader` | pdf | `§setup` | every symbol in table; every equation cited | hygiene | retry |
| 1c | extract method + results | `paper-reader` | pdf, `§setup` | `§method`, `§results` | no number without a cite | hygiene | retry |
| 1d | relate | `wiki-searcher` | `§setup`, `§method`, `§results`, `questions.md`, wiki | `§relevance`, `§hooks` | "none" allowed; Inference labels; cites only existing notes | hygiene | retry |
| 1e ⏸ | finalize | `doc-keeper`; `plan-reviewer` → human | all | `§context`; review 1e-r<n> | full contract; standalone | review | route per review |

**Stage 2, Ideate.** `/ideate <slug>`.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 2a ⏸ | frame | `idea-drafter`; `plan-reviewer` → human | `seed.md` | `§problem`; review 2a-r<n> | verdict accept | review | route 2a |
| 2b | position | `wiki-searcher` | `§problem`, wiki | `§position` | null model named; cites only existing notes; "nothing close" valid | hygiene | retry |
| 2c ⏸ | formalize | `idea-drafter`; `plan-reviewer` → human | `§problem`, `§position`, `scribble.md`, pending review if routed | `§model.notation`, `§model.assumptions`, `§model.formal`; review 2c-r<n> | every A tagged; scribble diff present; math rules; review confirms nothing lost | hygiene, review | route 2c |
| 2d | derive | `deriver` | `§model.notation`, `§model.assumptions`, `§model.formal`, pending review if routed | `§model.derivation` | every step cites an Ai; no unlisted assumption | `math-checker` | `math-checker` opens a draft review routed to 2c; you confirm |
| 2e | predict | `idea-drafter` | `§model.assumptions`, `§model.derivation` | `§model.predictions` | every `[own]` A has a PA or `untestable, accepted`; every R has a PR; no empirical numbers | hygiene | retry |
| 2f ⏸ | adversarial review | `idea-reviewer` → human | `§problem` through `§model.predictions` | review 2f-r<n> | you set verdict and route | review | route 2c or 2d, bound 3 |
| 2g | finalize | `doc-keeper` | all | `§context`, `§status`, stubs, export | budgets; standalone | hygiene | retry |

Step 2d derives the chain of consequences from the assumptions to results R1..Rk, each step naming the assumption it uses. When it needs an assumption that is not listed, the math-checker drafts a review routed to 2c rather than letting the deriver add one silently. Step 2e converts each result and each own assumption into a statement data can contradict, with quantity, direction, comparison, and kill condition. Own assumptions enter here and earn their place by being tested in stage 3.

**Stage 3, Design.** `/design <slug>`.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 3a | map hypotheses | `experiment-designer` | `§model.predictions` | `§experiment.hypotheses` | every PA has an H; every H maps to a P; max 3 PR-hypotheses | hygiene | retry |
| 3b ⏸ | data | `experiment-designer`; `plan-reviewer` → human | `§experiment.hypotheses`, `data.md` | `§data`; review 3b-r<n> | no field outside `data.md`; gaps explicit; review resolves gaps | review | route 3b |
| 3c | procedure | `experiment-designer` | `§experiment.hypotheses`, `§data`, `§model.notation` | `§experiment.procedure` | every H has a metric and a baseline | hygiene | retry |
| 3d | leakage audit | `leakage-auditor` | `§experiment.procedure` | `§experiment.leakage` | every F listed; no violation | `leakage-auditor` | drafts a review routed to 3c; you confirm |
| 3e ⏸ | finalize | `doc-keeper`; `plan-reviewer` → human | all | `§context`, `§status`, export; review 3e-r<n> | budgets; standalone | review | route per review |

**Stage 4, Implement.** `/implement <slug>`.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 4a | scaffold | `implementer` | `§experiment.procedure` | code skeleton, synthetic tests; `§implementation` | tests exist and fail for the right reason | tests | retry |
| 4b ⏸ | loader + lookahead test | `implementer`; `plan-reviewer` → human | `§data`, `§experiment.leakage` | loader; lookahead test; review 4b-r<n> | tests pass on a real-data sample | tests, review | route 4b or 3c |
| 4c | implement | `implementer` | `§experiment.procedure`, code | function + test per procedure step | all tests green | tests | retry per step |
| 4d | run | `implementer` | code | `runs/<id>/`; `§implementation` run entry | run completes; seeds logged | tests | stop |
| 4e | report | `results-reporter` | `runs/<id>/`, `§experiment.*` | `§results` | every number traces to a run file; every H present | hygiene | retry |

**Stage 5, Verdict.** `/verdict <slug>`. One human gate whose review is the rewind.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 5a ⏸ | verdict | `results-reviewer` drafts → human | `§results`, `§experiment.*`, `§model.*` | review 5a-r<n> (each refuted H traced to an A or R; candidate causes with evidence; proposed route) | you set verdict and route | review | — |
| 5b | record | orchestrator, `doc-keeper` | review | `REWIND` or tag; stale marks; `§status`; wiki note on confirm or abandon; export | ledger consistent | refs | stop |

| verdict and route at 5a | commit | marked stale |
|---|---|---|
| accept | tag `<slug>/confirmed` | nothing |
| revise → 4c | `REWIND` | `§implementation` runs, `§results` |
| revise → 3c | `REWIND` | `§experiment.leakage`, stage 4 sections |
| revise → 2c, Ai named | `REWIND` | `§model.derivation` onward |
| revise → 2a | `REWIND` | everything after `§problem` |
| abandon | tag `<slug>/abandoned` | nothing; `§status` and wiki record why |

### 8. Gate types

- **hygiene**: `doc-hygiene-reviewer`, every prose section, with a standalone dimension.
- **refs**: `ref_checker.py`, deterministic. Resolves every `§id` and token, compares per-section hashes to `built_from`, checks Context blocks and budgets, marks stale sections and stale reviews.
- **specialist automated**: `math-checker`, `leakage-auditor`. On failure they draft a review rather than rejecting silently, because their failures route backward, and you confirm before the route fires.
- **tests**: pytest, stage 4.
- **review**: the human gate. Ten in total: 1a, 1e, 2a, 2c, 2f, 3b, 3e, 4b, 5a, plus any specialist-drafted review you confirm.

### 9. Agent roster

Reviewer agents share one review template and two modes, draft and verify, so adding one costs a page.

| agent | steps | model | notes |
|---|---|---|---|
| `doc-hygiene-reviewer` | all prose | Sonnet | built; add standalone dimension |
| `ref-checker` | all | script | no LLM |
| `doc-keeper` | 1e, 2g, 3e, 5b, `/split` | Sonnet | Context blocks, stubs, index, export, wiki notes, `§status` |
| `plan-reviewer` | drafts reviews at 1a, 1e, 2a, 2c, 3b, 3e, 4b | Opus | checks the section against the stage contract and the previous review; generic |
| `idea-reviewer` | drafts and verifies 2f | Opus or Codex | adversarial; D8 |
| `results-reviewer` | drafts and verifies 5a | Opus | traces refuted H to A or R; proposes route; never decides |
| `math-checker` | gate for 2d | Opus | drafts a review to 2c on missing assumptions |
| `leakage-auditor` | gate for 3d | Sonnet | drafts a review to 3c on violations |
| `wiki-searcher` | 1d, 2b | Sonnet | only wiki access |
| `paper-reader` | 1a–1c | Sonnet | only PDF access |
| `idea-drafter` | 2a, 2c, 2e | Opus | tags provenance; consumes routed reviews |
| `deriver` | 2d | Opus | may not add assumptions |
| `experiment-designer` | 3a–3c | Opus | H for every PA |
| `implementer` | 4a–4d | Sonnet, Opus for 4c | |
| `results-reporter` | 4e | Sonnet | reports; never judges |

### 10. Repository layout

```
agent/                              # git repository
  CLAUDE.md  PIPELINE.md
  stages/REFS.md                    # §id grammar, token grammar, taxonomy templates, review template
  stages/0N-*/CONTRACT.md STEPS.md
  .claude/agents/<name>.md
  .claude/skills/{read,ideate,design,implement,verdict,split,review}/SKILL.md
  .githooks/commit-msg pre-commit post-commit
  scripts/doc.py ref_checker.py state.py review.py
  work/<slug>/
    docs/DESIGN.md  docs/model.md  docs/INDEX.yaml
    export/<slug>-full.md
    pipeline/state.yaml  attempts/  reviews/2a-r1.md 2c-r1.md 2f-r1.md ...
    seed.md scribble.md data.md questions.md
    runs/<id>/
  benchmarks/0N-*/
```

## Process: one review from draft to applied

**Gate.** Steps 2a through 2e have passed. `/ideate` reaches 2f, runs `idea-reviewer` in draft mode against version `e5f6a7b`, writes `reviews/2f-r1.md` with two items and a proposed route to 2c, and stops.

**Co-author.** You open the review. You delete a third finding the reviewer proposed, add an item of your own about the objective in `§model.formal`, set `verdict: revise` and `route_to: 2c`. You run `/review commit`. The hook checks the object, checks that your name is in the authors, and commits `REVIEW 2f-r1`. `state.yaml` now has `pending_review: 2f-r1`, and `§model.derivation` and `§model.predictions` are marked stale because they are downstream of 2c.

**Apply.** Next `/ideate`: the only runnable step is 2c. `idea-drafter` receives its normal inputs plus the review, and produces new assumptions and formal model. 2c is itself a human gate, so `plan-reviewer` drafts `2c-r2` against the new version; you accept, and it is applied at once. 2d and 2e rerun through their gates. When 2e passes, `idea-reviewer` runs in verify mode against version `9a8b7c6`, proposes I1 addressed, I2 addressed, I3 addressed, and stops. You confirm. Commit `APPLY 2f-r1`, `applied_version: 9a8b7c6`, `§status` gets a line: "2f-r1 judged e5f6a7b, revise → 2c, applied at 9a8b7c6". The loop counter reads 1.

**Second pass.** 2f runs again on `9a8b7c6`, drafts `2f-r2` with no items. You set accept. Applied immediately. 2g finalizes, tag `ideate-done`, export regenerated.

**Rewind, weeks later.** `§results` refutes H3. `/verdict` runs `results-reviewer`, which drafts `5a-r1`: H3 tests PA3, PA3 tests A3, candidate causes listed with evidence, proposed route 2c. You agree, set revise → 2c. Commit `REVIEW 5a-r1` then `REWIND 5a-r1`. `§model.derivation` onward is stale. 2c reruns with the review as input, and everything downstream regenerates through its gates. `5a-r1` is applied when a new `§results` exists and `results-reviewer` in verify mode confirms H3 now has a different outcome or A3 is gone. A collaborator opening `DESIGN.md` sees the rewind in `§status` with both versions.

## Why it works, and why it could fail

The mechanism works because one object, the review, carries every human decision, and it is bound to the exact text it judged. Nothing is decided in a chat window. A pending review tells the orchestrator precisely which step to run and tells a collaborator precisely what is unresolved. Section-level ownership means a routed step cannot damage anything but its own sections. Section-level hashes mean a review can detect when the text it judged has moved under it. And the same object handles an in-stage loop, a cross-stage rewind, and an accept, so the log is uniform.

Failure modes, in order of likelihood:

- **Review friction.** Ten human gates each producing a review feels heavy for a one-line accept. Guard: an accept is `/review accept` with no editing; the reviewer's draft is pre-filled; D4 prunes gates after a month.
- **Verify mode rubber-stamps.** The reviewer marks every item addressed because the section changed. Guard: verify mode must quote the new text that satisfies each required change; you confirm per item, not per review.
- **Stale reviews accumulate.** Hand edits during a pending review invalidate it. Guard: `HUMAN` commits during a pending review are allowed only on the routed step's sections; anything else needs the review waived first.
- **Over-specification.** Guard: one-line pass rules; full rubrics at the stage level only.
- **Premature splitting.** Guard: split on budget only; `doc-keeper` proposes, never executes.
- **Git discipline erodes.** Guard: hooks reject bad messages and out-of-ownership diffs.
- **Orchestrator drift.** Guard: no tools beyond `doc.py`, `review.py`, git, `state.yaml`.
- **Own assumptions never get tested.** Guard: `experiment-designer` must create an H per PA; `§status` lists untested own assumptions permanently.
- **Loop without progress.** The same item reopens three times. Guard: the bound forces `abandon` or an explicit override in the next review, with the reason recorded.

## Close

### Synthesis

The pipeline keeps its five stages and per-stage contracts. Inside each stage, steps own sections of one design document that starts as a single file and splits by big section under a budget, with stable ids and Context blocks so every file reads standalone. Every human gate produces one review, drafted by a reviewer agent and finished by you, bound to the version it judged, routed to the step that must act on it, and pending until a later version has applied every item and you have confirmed. In-stage loops and cross-stage rewinds are the same object with different commit verbs. Git holds every version, attempt, review, and application under a fixed grammar. Ideas that are not in the literature enter through tagged own assumptions and earn their place by being tested. A collaborator opening any file sees what was judged, against which text, and what changed.

### Decision register

| id | decision | options | recommend |
|---|---|---|---|
| D1 | step granularity | (a) as proposed; (b) coarser; (c) finer | (a) |
| D2 | state format | (a) `state.yaml` indexed to git; (b) derive from git log only; (c) SQLite | (a) |
| D3 | orchestrator | (a) skill per stage; (b) Python driver; (c) both, skill first | (c) |
| D4 | human gates | (a) all ten; (b) drop 1e, 3e, 4b; (c) only 2a, 2c, 2f, 5a | (a) for a month, then prune |
| D5 | where `work/` lives | (a) this repo; (b) wiki; (c) experiment repo | (a) |
| D6 | loop bound per route | 2 / 3 / unbounded | 3 |
| D7 | build order | (a) stage 2 first; (b) stage 1 first; (c) `doc.py`, `review.py`, ledger, ref-checker first, then stage 2 | (c) |
| D8 | Codex's role | (a) none; (b) `idea-reviewer` and `leakage-auditor` on Codex; (c) Codex drafts | (b) |
| D9 | wiki tool and note format | your answer | needed for `wiki-searcher` |
| D10 | commit enforcement | (a) hooks reject; (b) hooks warn, orchestrator refuses; (c) convention | (a) |
| D11 | staleness | (a) any input change stales dependents; (b) only referenced tokens; (c) (a) plus "re-verify only" | (c) |
| D12 | who may draft a review | (a) only at human gates plus `math-checker` and `leakage-auditor`; (b) any automated gate may draft; (c) only human gates | (a) |
| D13 | own assumptions | (a) PA or explicit "accepted untested" in `§status`; (b) PA mandatory | (a) |
| D14 | file budget | 300 / 400 / 600 lines; child trigger at 3 over 60 | 400 |
| D15 | taxonomy | (a) fixed; (b) per-project template; (c) free-form with required ids | (b) |
| D16 | export format | (a) markdown; (b) plus PDF; (c) plus wiki page | (a) now, (c) after D9 |
| D17 | who verifies application | (a) drafting reviewer proposes per item, you confirm per item; (b) you tick items alone; (c) reviewer alone | (a) |
| D18 | concurrent reviews | (a) one pending per project; (b) one per stage; (c) unlimited | (a) |
| D19 | review co-authoring surface | (a) edit the markdown file directly; (b) `/review` interactive prompts that write the file; (c) both | (c) |

### Build map

| component | how it gets built |
|---|---|
| `stages/REFS.md` | §id grammar, token grammar, taxonomy templates, review template |
| `scripts/doc.py` | get/put by §id, split/merge, stubs, budget, export |
| `scripts/review.py` | create draft, validate object, commit, verify-mode merge, apply |
| commit grammar + hooks | `.githooks/`; ownership check via `doc.py diff`; review-author check |
| `state.py`, `ref_checker.py` | per-section hashing; index resolution; stale sections and stale reviews |
| `STEPS.md` × 5 | the tables above, adjusted per D1, D4 |
| orchestrators × 5 + `/split` + `/review` | one skill each; `/ideate` and `/review` first |
| `doc-keeper` | Context, stubs, index, export, wiki notes, `§status` |
| `plan-reviewer`, `idea-reviewer`, `results-reviewer` | one shared template, draft and verify modes |
| `doc-hygiene-reviewer` update | standalone dimension; Context-block check |
| stage 2 generators | each tested on 3 benchmark seeds |
| `paper-reader`, `wiki-searcher` | after D9 |
| stage 3, 4 agents | after stage 2 runs end to end |
| `/review-logs` | weekly listing of `REJECT` commits and reopened items per step |
| `PIPELINE.md` shrink | pointers to `STEPS.md` and `REFS.md` |

### Timeline

| phase | components | depends on | duration |
|---|---|---|---|
| 0 | decision register D1–D19 | you | 1 sitting |
| 1 | `REFS.md`, `doc.py`, `review.py`, hooks, `state.py`, `ref_checker.py`, `STEPS.md` × 5; a fake project taken through one review by hand | 0 | 3 days |
| 2 | `/ideate`, `/review`, `doc-keeper`, `plan-reviewer`, `idea-reviewer`, stage 2 generators, 3 seeds; one idea through with a revise review applied, a hand edit, and a split | 1, D8, D9 | 1 week |
| 3 | `paper-reader`, `wiki-searcher`, `/read`, 5 papers | 2 | 3 days |
| 4 | stages 3–5, one idea to a recorded rewind via a 5a review, and an export | 3 | 1 week |
| 5 | `/review-logs`, prune gates, revisit D12 | 4 | ongoing |
