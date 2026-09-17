# Proposal: stages as checkpointed sub-workflows

Status: PROPOSAL v5 for decision. Nothing in the repo changes until the decision register at the end is filled in.

Changes from v4: every human-authored input gets an intake gate that surfaces underdetermined choices before any agent fills them in. Versions are per-file counters plus the commit, not the commit alone. The document holds only the current design; history lives in git, `§status`, and an append-only rejection log that generators must consult so nothing rejected is re-proposed. Reviews from coworkers are imported into the review format, and each imported item is dispositioned as accept, counter, decline, or defer.

## Hook

The current `PIPELINE.md` treats each stage as one agent call that produces one finished document. Your stages take days, and you discover problems only in that finished document, when everything in it already depends on the mistake. Rejecting a finished idea doc costs you the whole stage. The obvious fix, one file per step, produces fragments no collaborator can read, decisions made in a chat window nobody can find, and documents that swell with the history of their own revisions.

## Core claim

**Each project is one design document with stable section ids and per-file versions; every human input passes an intake gate before an agent elaborates it; each pipeline step owns one section and writes only the current design; every human gate produces one review bound to one document version, co-authored by a reviewer agent and you, pending until a later version has applied it; and everything rejected goes to a log that generators must not contradict.**

## Elaboration

A project's knowledge lives in one design document with a fixed section taxonomy. At the start it is one file. As sections grow they move into their own files with stubs left behind, and section ids never change, so it remains one document. Each file carries its own version counter, and a document version is the commit plus the counter of every file. The document is load-bearing twice over: a collaborator reads it, and every agent reads only the sections its step names.

Agents deviate from your intent at two moments. The first is when your input is rough and the agent silently chooses the details. The **intake gate** handles this: before a generator touches `seed.md`, `scribble.md`, `data.md`, or `questions.md`, an intake reviewer lists every choice the input leaves open, ranked by how much it would change downstream, and you answer each or explicitly delegate it. Delegated choices are reported by the generator in a visible block and become default items in the next human review, so a delegated choice is never an invisible one.

The second moment is when an agent preserves history inside the document. Current models resist information loss, so an applied review tends to produce a section containing the old text, the new text, and the reason for the change. The **current-design rule** forbids this: a section states only what the design is now. History has three homes, each with one job. Git holds every version. The `§status` section holds one line per review. The **rejection log** holds every proposal that was turned down, with the reason, and every generator receives the log entries for its section and may not re-propose them.

A **review** is a change request against a specific document version. At a human gate a reviewer agent drafts it, you finish it, and it is committed as pending. It routes the pipeline to one step, that step receives it as input, and it is applied only when every item is addressed in a later version, verified by the reviewer and confirmed by you. Reviews from coworkers arrive in any form and are converted into the same object. For each imported item you keep their finding and decide what to do with their proposed fix: accept it, counter it with your own, decline it with a reason, or defer it. Countered and declined proposals go to the rejection log.

Eight terms carry the design: section, intake gate, automated gate, review, routing target, ledger, stale, split.

## Structure

### 1. Document taxonomy

Every design document has these top-level sections in this order, each with a stable id. Empty sections show as `[pending: step 3c]`.

| id | section | owned by |
|---|---|---|
| `§context` | project one-liner, status, file version, how to read the tree | `doc-keeper` |
| `§problem` | observed, unknown, why it matters, goal; a `Choices made` block listing delegated intake choices | 2a |
| `§position` | closest wiki notes, null model, what is new | 2b |
| `§model.notation` | symbol table | 2c |
| `§model.assumptions` | A1.. tagged `[lit]`, `[standard]`, `[own]`; `Choices made` block | 2c |
| `§model.formal` | state, parameters, objective in LaTeX; scribble diff appendix | 2c |
| `§model.derivation` | numbered steps citing Ai; results R1..Rk | 2d |
| `§model.predictions` | PA per own assumption, PR per result, kill conditions | 2e |
| `§data` | inventory, plan, gaps; `Choices made` block | 3b |
| `§experiment.hypotheses` | H ↔ P mapping | 3a |
| `§experiment.procedure` | steps, features F, metrics M, baselines, split | 3c |
| `§experiment.leakage` | per-feature timestamp audit | 3d |
| `§implementation` | layout, run ids, deviations | 4a, 4d |
| `§results` | per-H outcome, tables, anomalies | 4e |
| `§status` | one line per review: versions judged and applied, verdict, route; untested own assumptions | orchestrator |

Your ML example maps directly: data is `§data`, model architecture is `§model.*`, train and test is `§experiment.*` plus `§implementation`. Decision D15 asks whether the taxonomy is fixed or a per-project template. Stage 1 uses the same mechanism on a wiki note with `§claim`, `§setup`, `§method`, `§results`, `§relevance`, `§hooks`.

### 2. Versioning

Every file in `docs/` has a version counter, stored in `INDEX.yaml` and shown in the file's Context block. It bumps by one on every committed change to an owned section in that file. Stub refreshes do not bump the parent, since stubs are derived. A document version is written as the commit followed by the counters:

```
c3d4e5f
DESIGN.md: v4
model.md: v3
experiment.md: v2
```

Reviews bind to a document version in this form and record `applied_version` in the same form. Section hashes still exist underneath for staleness, since a file version says something changed but not what. A collaborator reads "model v3", the ref-checker reads hashes. Decision D20 asks whether counters should also exist per section.

### 3. Files, splitting, and standalone readability

A project starts as `work/<slug>/docs/DESIGN.md` containing every section. When a file exceeds its budget, `/split §model` moves that section and its children to `docs/model.md` at `v1`, leaves a stub, and updates `INDEX.yaml`. A stub is a heading, a three-sentence summary regenerated whenever the child changes, and a link.

Every file must be readable on its own: a Context block of at most four sentences naming the project, what the file covers, its version, what it depends on with links, and its status; every symbol defined in the file or `§model.notation` linked; every cross-reference written as `§id`. The hygiene reviewer scores a *standalone* dimension. Split triggers are a file over budget or a section with three or more children each over sixty lines; `doc-keeper` proposes, you run `/split`. `scripts/doc.py export` concatenates the tree into `export/<slug>-full.md` at every stage tag. Decision D14 sets the budget.

### 4. Intake gate for human inputs

Four files are written by you and elaborated by agents: `questions.md` (stage 1), `seed.md` (2a), `scribble.md` (2c), `data.md` (3b). Each passes an intake gate before the generator runs.

The `intake-reviewer` reads the input and the stage contract and produces a review of kind `intake`, whose items are questions rather than findings:

```yaml
kind: intake
input: seed.md
input_hash: 77ab...
items:
  - id: Q1
    severity: framing          # framing | structural | detail
    choice: "Is the target the conditional mean of returns or the full distribution?"
    why_it_matters: "Decides whether §model.formal is a filter or a density model; changes every downstream section"
    options: ["conditional mean", "full distribution", "both, mean first"]
    answer: null               # you fill: an option, free text, or `delegate`
  - id: Q2
    severity: detail
    choice: "Daily or intraday frequency?"
    why_it_matters: "Changes §data and the leakage audit, not the model"
    options: ["daily", "intraday", "delegate"]
    answer: null
```

Rules:

1. Every `framing` and `structural` item must have an answer before the generator runs. A `detail` item may be `delegate`.
2. Answers are written back into the input file under a `## Decisions` heading, so the input file remains the single source, and the intake review is applied at that point.
3. The generator receives the input, the decisions, and the rejection log. Every delegated choice it makes is listed in a `Choices made` block at the end of its section: the choice, what it picked, one line why.
4. Every entry in `Choices made` becomes a default item in the next human review of that section, pre-set to `accept`. You see each one and can counter it. This is what stops delegation from becoming deviation.
5. Intake reruns when the input file's hash changes.

Decision D21 asks whether `structural` items may also be delegated, and D22 whether `Choices made` items default to accept or to open.

### 5. Current-design rule and the rejection log

A section states only what the design is now. Hard rules enforced by the hygiene gate:

- No narration of change: banned phrases include "previously", "originally", "we changed", "was rejected", "instead of the earlier", "as before", "updated to".
- No superseded content. The ref-checker diffs a new section against the rejected attempts and the previous version; if a rejected span reappears verbatim or near-verbatim, the section is rejected.
- No rationale for a change inside the section. Rationale lives in the review that caused it.
- `Choices made` is the only block that explains a decision, and it explains only decisions delegated at intake.

History has three homes:

| home | holds | written by |
|---|---|---|
| git | every version of everything | hooks |
| `§status` | one line per review: id, versions judged and applied, verdict, route | orchestrator |
| `pipeline/REJECTED.md` | every proposal turned down, with reason | `review.py`, `/reject` |

The rejection log is append-only, one entry per rejected proposal:

```
R17 | 2026-10-02 | 2f-r1 | §model.assumptions | proposal: "A3 volatility persistence > 0.9 as [standard]" | rejected: no source; retagged [own] with PA3 | by: chen-yu
R18 | 2026-10-09 | ext-r3 | §experiment.procedure | proposal: "use Sharpe as primary metric" (from: J. Lin) | countered: Sharpe conflates PR1 and PR2; use IC per hypothesis | by: chen-yu
R19 | 2026-10-09 | manual | §model.formal | proposal: "model σ_t as GARCH(1,1)" | rejected: tried in idea vol-garch-2025, PA failed | by: chen-yu
```

Entries are written automatically when a review item's required change removes or replaces something, when an imported item is countered or declined, and manually through `/reject "<proposal>" --section §id --why "<reason>"`. A rejected *proposal* is content; a rejected *attempt* is a quality failure and goes to `pipeline/attempts/`. Only proposals block re-proposal.

Every generator receives the log entries for its sections. The pass rule on every generator step gains one clause: the output contains nothing matching an entry in the rejection log for its section. The reviewer checks this with the log in hand and cites the entry id on failure. If you want to revive a rejected proposal, `/reject revive R17 --why` marks it revived; nothing is deleted.

### 6. Review object

One file per review, append-only, at `pipeline/reviews/<step>-r<n>.md`, or `ext-r<n>.md` for imported ones.

```yaml
---
id: 2f-r1
kind: gate                        # gate | intake | external
step: 2f
origin: internal                  # internal | external
external_source: null             # path of the coworker's original, if external
doc_version:
  commit: c3d4e5f
  files: {DESIGN.md: v4, model.md: v3}
sections_judged: {§model.assumptions: 41cc..., §model.derivation: 8a2b...}
authors: [idea-reviewer, chen-yu]
verdict: revise                   # accept | revise | abandon
route_to: 2c
status: pending                   # draft | pending | applied | waived | superseded | stale
applied_version: null
items:
  - id: I1
    section: §model.assumptions
    source: idea-reviewer         # agent name, chen-yu, or coworker name
    finding: "A3 assumes volatility persistence above 0.9 with no source"
    proposal: "Tag A3 [own]; add PA3 with a measurable threshold"
    disposition: accept           # accept | counter | decline | defer
    required: "Tag A3 [own]; add PA3 with a measurable threshold"   # what the pipeline must do; equals proposal on accept
    logged: null                  # rejection-log id when countered or declined
    status: open                  # open | addressed | waived
    addressed_at: null
---
<prose: reviewer draft, then your edits, appended in order>
```

Rules:

1. Binds to one document version and one hash per judged section. If a judged section changes by a route other than the prescribed one, the ref-checker marks the review `stale`.
2. Every item has a `finding` and a `required`. `proposal` is what the source suggested; `required` is what you decided. On `counter`, you write `required` yourself and the proposal is logged. On `decline`, `required` is empty, the item does not block, and the proposal is logged with your reason. On `defer`, the item is copied to `pipeline/DEFERRED.md` and does not block.
3. Only you set `verdict`, `route_to`, and `disposition`. The hook refuses a review without you in `authors`.
4. At most one review is pending per project. Others wait as `draft`. Decision D18.
5. Applied when every item is `addressed` or `waived` and you confirm per item. The drafting reviewer runs in verify mode and must quote the new text satisfying each `required`. Decision D17.
6. An accept is a review with no blocking items, applied at its own version.
7. A route across a stage boundary is a rewind; same object, different commit verb.

### 7. External reviews

Coworkers send reviews as email, comments, or marked-up copies of the export. `/review import <file> --from "J. Lin"` runs `review-converter`, which:

1. Identifies which document version they read, from the export header if present, otherwise asks you.
2. Splits their text into items, each anchored to a section. Their finding becomes `finding`, their suggested fix becomes `proposal`, `source` is their name.
3. Checks each anchored section against the current version; if the text they judged has changed, the item is flagged `judged_outdated` with both hashes.
4. Proposes a `disposition` for each item with one line of reasoning, and proposes a `route_to`.
5. Writes `ext-r<n>.md` as `draft`.

You then disposition each item. `counter` keeps their finding, replaces the fix with yours, and logs theirs with your reason. `decline` logs theirs. After commit, `/review reply ext-r3` produces a short markdown note for the coworker: each item, your disposition, your reason, and the version where it will be applied. Decision D23 asks whether that reply is generated automatically at apply time.

### 8. Step schema

| field | meaning |
|---|---|
| id | stage number plus letter |
| owner | agent name, or `reviewer → human` at a human gate |
| input | section ids and files; a routed step always also receives the pending review and the rejection-log entries for its sections |
| output | owned section ids, or a review |
| pass rule | one sentence; every generator step implicitly adds "and nothing in the rejection log for its sections" |
| gate | `hygiene`, a reviewer agent, `tests`, `intake`, or `review`; `refs` implicit |
| on fail | `retry`, or whatever `route_to` says |

### 9. Ledger: git plus state.yaml

`work/<slug>/` is inside a git repository. Every section version, attempt, review, application, split, and export is a commit. `state.yaml` indexes the log and must match it.

```yaml
slug: vol-regime-kalman
stage: ideate
head: 3f9c2a1
versions: {DESIGN.md: v4, model.md: v3}
inputs:
  seed.md:     {hash: 77ab..., intake: 2a-in1, status: applied}
  scribble.md: {hash: 19cd..., intake: 2c-in1, status: applied}
steps:
  2c: {status: done, sections: [§model.notation, §model.assumptions, §model.formal],
       attempts: 2, commit: c3d4e5f, built_from: {§problem: 9e1f..., scribble.md: 19cd..., §position: 12cd...}}
  2d: {status: stale, sections: [§model.derivation], commit: d4e5f6a,
       built_from: {§model.assumptions: 41cc..., §model.formal: 8a2b...}, stale_reason: "review 2f-r1 routed to 2c"}
pending_review: pipeline/reviews/2f-r1.md
queued_reviews: [pipeline/reviews/ext-r3.md]
reviews:
  - {id: 2a-in1, kind: intake, status: applied}
  - {id: 2a-r1, verdict: accept, doc_version: {commit: a1b2c3d, files: {DESIGN.md: v1}}, applied_version: same}
  - {id: 2f-r1, verdict: revise, route_to: 2c, status: pending}
rejected_count: 19
loops: {2f->2c: 1}
```

**Commit rules.** Enforced by hooks. Decision D10.

1. One step per commit; the diff touches only that step's sections, `state.yaml`, and `INDEX.yaml` version bumps. `HUMAN`, `SPLIT`, `REJECT-LOG` are exempt from ownership, not from format.
2. Tree clean before any step runs.
3. Message: `<slug>/<step> <VERB>[ a<n>][ <review-id>]: <one line>`. Verbs: `PASS`, `REJECT`, `HUMAN`, `INTAKE`, `REVIEW`, `IMPORT`, `APPLY`, `WAIVE`, `LOOP`, `REWIND`, `STALE`, `SPLIT`, `EXPORT`, `REJECT-LOG`.
4. Rejected attempts commit as `REJECT` to `pipeline/attempts/`. Rejected proposals commit as `REJECT-LOG` to `pipeline/REJECTED.md`.
5. Hand edits commit as `HUMAN` with a reason; gates rerun on touched sections; a pending review whose judged sections were touched goes `stale`. During a pending review, `HUMAN` commits may touch only the routed step's sections.
6. Reviews: `INTAKE` at creation of an intake review, `REVIEW` at creation of a gate review, `IMPORT` for an external one, `APPLY` at application, `WAIVE` if abandoned. `APPLY` records `applied_version`.
7. `LOOP <id>` for in-stage routes, `REWIND <id>` across stages. No amend, rebase, force push, or reset on `work/`.
8. Stage completion tags `<slug>/<stage>-done`, triggers `EXPORT`.
9. `state.yaml` records `head`; on mismatch the orchestrator rebuilds from the log and asks you to confirm.

### 10. Orchestrator

One slash command per stage, `/read`, `/ideate`, `/design`, `/implement`, `/verdict`, plus `/split`, `/review`, `/reject`. Behavior, in order:

0. **Consistency.** Tree clean; head matches; last commit matches last state entry.
1. **References and staleness.** Rehash sections; resolve `§id`s; mark stale sections and stale reviews; check budgets; commit `STALE` if anything changed.
2. **Intake.** For every input file whose hash differs from `inputs.<file>.hash`, run `intake-reviewer`, write the intake review as `draft`, print the path, and stop. On your answers, `/review commit` writes them into the input file's `## Decisions` and commits `INTAKE`.
3. **Pending review.** If one exists, the only runnable step is `route_to` and its downstream. When the last downstream step passes, run the drafting reviewer in verify mode, write per-item proposals, stop for your confirmation. On confirmation, commit `APPLY`, then promote the first queued review to `pending` if any.
4. **Human gate.** If the next step is a human gate, run its reviewer in draft mode, pre-load `Choices made` entries from the judged sections as items, write the review as `draft`, and stop. `/review commit` validates and commits `REVIEW`.
5. **Run.** Extract input sections, the pending review if routed, and the rejection-log entries for the owned sections; run the agent; write output with `doc.py put`; bump file versions.
6. **Automated gate.** Hygiene, refs, rejection-log dedupe, specialist. On fail, `REJECT`, retry once with findings; second fail stops.
7. **Commit.** `PASS`; continue unless the next step is a human gate.
8. **Bounds.** When the same route has fired its maximum, the next review must carry `abandon` or an explicit override.

The orchestrator has no research tools. It may write only `state.yaml`, call `doc.py`, `review.py`, git, and invoke agents.

### 11. Stage decompositions

Human gates ⏸ always produce a review. Intake gates are marked ⌂. `refs` and rejection-log dedupe are implicit on every generator step.

**Stage 1, Read.** `/read <pdf-or-arxiv-id>`.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 1·in ⌂ | intake | `intake-reviewer` → human | `questions.md` | intake review; `## Decisions` in `questions.md` | no open framing item | intake | you answer |
| 1a ⏸ | triage | `paper-reader`; `plan-reviewer` → human | pdf, `questions.md` | `§claim`; review 1a-r<n> | accept means read | review | abandon archives |
| 1b | extract model | `paper-reader` | pdf | `§setup` | every symbol in table; every equation cited | hygiene | retry |
| 1c | extract method + results | `paper-reader` | pdf, `§setup` | `§method`, `§results` | no number without a cite | hygiene | retry |
| 1d | relate | `wiki-searcher` | `§setup`, `§method`, `§results`, `questions.md`, wiki | `§relevance`, `§hooks` | "none" allowed; Inference labels; cites only existing notes | hygiene | retry |
| 1e ⏸ | finalize | `doc-keeper`; `plan-reviewer` → human | all | `§context`; review 1e-r<n> | full contract; standalone | review | route per review |

**Stage 2, Ideate.** `/ideate <slug>`.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 2a·in ⌂ | intake | `intake-reviewer` → human | `seed.md` | intake review; `## Decisions` in `seed.md` | no open framing or structural item | intake | you answer |
| 2a ⏸ | frame | `idea-drafter`; `plan-reviewer` → human | `seed.md` with decisions, log | `§problem` with `Choices made`; review 2a-r<n> | accept; every delegated choice seen | review | route 2a |
| 2b | position | `wiki-searcher` | `§problem`, wiki | `§position` | null model named; cites only existing notes | hygiene | retry |
| 2c·in ⌂ | intake | `intake-reviewer` → human | `scribble.md`, `§problem` | intake review; `## Decisions` in `scribble.md` | no open framing or structural item | intake | you answer |
| 2c ⏸ | formalize | `idea-drafter`; `plan-reviewer` → human | `§problem`, `§position`, `scribble.md` with decisions, log, pending review if routed | `§model.notation`, `§model.assumptions`, `§model.formal`; review 2c-r<n> | every A tagged; scribble diff present; math rules; delegated choices seen | hygiene, review | route 2c |
| 2d | derive | `deriver` | `§model.*` inputs, log, pending review if routed | `§model.derivation` | every step cites an Ai; no unlisted assumption | `math-checker` | drafts a review to 2c |
| 2e | predict | `idea-drafter` | `§model.assumptions`, `§model.derivation`, log | `§model.predictions` | every `[own]` A has a PA or `untestable, accepted`; every R has a PR; no empirical numbers | hygiene | retry |
| 2f ⏸ | adversarial review | `idea-reviewer` → human | `§problem` through `§model.predictions`, log | review 2f-r<n> | you set verdict and route | review | route 2c or 2d, bound 3 |
| 2g | finalize | `doc-keeper` | all | `§context`, `§status`, stubs, export | budgets; standalone | hygiene | retry |

Step 2d derives the chain of consequences from the assumptions to results R1..Rk, each step naming the assumption it uses; a missing assumption becomes a drafted review to 2c, never a silent addition. Step 2e converts each result and each own assumption into a statement data can contradict, with quantity, direction, comparison, and kill condition.

**Stage 3, Design.** `/design <slug>`.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 3a | map hypotheses | `experiment-designer` | `§model.predictions`, log | `§experiment.hypotheses` | every PA has an H; every H maps to a P; max 3 PR-hypotheses | hygiene | retry |
| 3b·in ⌂ | intake | `intake-reviewer` → human | `data.md`, `§experiment.hypotheses` | intake review; `## Decisions` in `data.md` | no open structural item | intake | you answer |
| 3b ⏸ | data | `experiment-designer`; `plan-reviewer` → human | `§experiment.hypotheses`, `data.md` with decisions, log | `§data` with `Choices made`; review 3b-r<n> | no field outside `data.md`; gaps explicit | review | route 3b |
| 3c | procedure | `experiment-designer` | `§experiment.hypotheses`, `§data`, `§model.notation`, log | `§experiment.procedure` | every H has a metric and a baseline | hygiene | retry |
| 3d | leakage audit | `leakage-auditor` | `§experiment.procedure` | `§experiment.leakage` | every F listed; no violation | `leakage-auditor` | drafts a review to 3c |
| 3e ⏸ | finalize | `doc-keeper`; `plan-reviewer` → human | all | `§context`, `§status`, export; review 3e-r<n> | budgets; standalone | review | route per review |

**Stage 4, Implement.** `/implement <slug>`.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 4a | scaffold | `implementer` | `§experiment.procedure` | code skeleton, synthetic tests; `§implementation` | tests exist and fail for the right reason | tests | retry |
| 4b ⏸ | loader + lookahead test | `implementer`; `plan-reviewer` → human | `§data`, `§experiment.leakage` | loader; lookahead test; review 4b-r<n> | tests pass on a real-data sample | tests, review | route 4b or 3c |
| 4c | implement | `implementer` | `§experiment.procedure`, code | function + test per step | all tests green | tests | retry per step |
| 4d | run | `implementer` | code | `runs/<id>/`; `§implementation` run entry | run completes; seeds logged | tests | stop |
| 4e | report | `results-reporter` | `runs/<id>/`, `§experiment.*` | `§results` | every number traces to a run file; every H present | hygiene | retry |

**Stage 5, Verdict.** `/verdict <slug>`.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 5a ⏸ | verdict | `results-reviewer` → human | `§results`, `§experiment.*`, `§model.*`, log | review 5a-r<n> (each refuted H traced to an A or R; candidate causes with evidence; proposed route) | you set verdict and route | review | — |
| 5b | record | orchestrator, `doc-keeper` | review | `REWIND` or tag; stale marks; `§status`; rejection-log entries for abandoned assumptions; wiki note; export | ledger consistent | refs | stop |

| verdict and route at 5a | commit | marked stale |
|---|---|---|
| accept | tag `<slug>/confirmed` | nothing |
| revise → 4c | `REWIND` | `§implementation` runs, `§results` |
| revise → 3c | `REWIND` | `§experiment.leakage`, stage 4 |
| revise → 2c, Ai named | `REWIND`; Ai logged as rejected with the H that refuted it | `§model.derivation` onward |
| revise → 2a | `REWIND` | everything after `§problem` |
| abandon | tag `<slug>/abandoned`; core claim logged | nothing |

### 12. Gate types

- **intake**: `intake-reviewer` on human inputs; blocks until framing and structural choices are answered.
- **hygiene**: `doc-hygiene-reviewer` on every prose section, with standalone and current-design-rule checks.
- **refs**: `ref_checker.py`, deterministic; ids, hashes, Context blocks, budgets, stale sections and reviews, rejected-span reappearance.
- **rejection-log dedupe**: the section's reviewer checks output against log entries for that section and cites the entry on failure.
- **specialist automated**: `math-checker`, `leakage-auditor`; draft a review backward on failure.
- **tests**: pytest, stage 4.
- **review**: the human gate; ten of them plus specialist-drafted reviews you confirm.

### 13. Agent roster

| agent | steps | model | notes |
|---|---|---|---|
| `doc-hygiene-reviewer` | all prose | Sonnet | built; add standalone, current-design rule |
| `ref-checker` | all | script | no LLM |
| `intake-reviewer` | 1·in, 2a·in, 2c·in, 3b·in | Opus | lists open choices with severity and downstream effect; never answers them |
| `review-converter` | `/review import` | Opus | maps a coworker's text to items; proposes dispositions; never sets them |
| `doc-keeper` | 1e, 2g, 3e, 5b, `/split` | Sonnet | Context, stubs, index, versions, export, wiki notes, `§status` |
| `plan-reviewer` | drafts 1a, 1e, 2a, 2c, 3b, 3e, 4b | Opus | checks against contract, previous review, `Choices made`, log |
| `idea-reviewer` | 2f draft and verify | Opus or Codex | adversarial; D8 |
| `results-reviewer` | 5a draft and verify | Opus | traces refuted H to A or R; proposes route |
| `math-checker` | gate 2d | Opus | |
| `leakage-auditor` | gate 3d | Sonnet | |
| `wiki-searcher` | 1d, 2b | Sonnet | only wiki access |
| `paper-reader` | 1a–1c | Sonnet | only PDF access |
| `idea-drafter` | 2a, 2c, 2e | Opus | tags provenance; writes `Choices made`; consumes reviews and log |
| `deriver` | 2d | Opus | may not add assumptions |
| `experiment-designer` | 3a–3c | Opus | H for every PA; writes `Choices made` at 3b |
| `implementer` | 4a–4d | Sonnet, Opus for 4c | |
| `results-reporter` | 4e | Sonnet | never judges |

Seventeen agents. Reviewer agents share one template with draft and verify modes; intake and converter share the item schema. The count is high but each is one page, and the article's threshold for hierarchical orchestration is what the per-stage skills provide.

### 14. Repository layout

```
agent/                              # git repository
  CLAUDE.md  PIPELINE.md
  stages/REFS.md                    # §id grammar, tokens, taxonomy templates, review and intake schemas
  stages/0N-*/CONTRACT.md STEPS.md
  .claude/agents/<name>.md
  .claude/skills/{read,ideate,design,implement,verdict,split,review,reject}/SKILL.md
  .githooks/commit-msg pre-commit post-commit
  scripts/doc.py ref_checker.py state.py review.py
  work/<slug>/
    docs/DESIGN.md  docs/model.md  docs/INDEX.yaml
    export/<slug>-full.md
    pipeline/state.yaml  REJECTED.md  DEFERRED.md  attempts/  reviews/
    seed.md scribble.md data.md questions.md     # each with ## Decisions
    external/<from>-<date>.md                    # coworker originals
    runs/<id>/
  benchmarks/0N-*/
```

## Process: intake, review, import, rewind

**Intake.** You write a four-line `seed.md` and run `/ideate vol-regime-kalman`. `intake-reviewer` returns five questions: two framing, one structural, two detail. You answer the framing and structural ones and delegate the two details. `/review commit` writes `## Decisions` into `seed.md`, commits `INTAKE 2a-in1`. `idea-drafter` writes `§problem` with a `Choices made` block listing its two delegated picks. `plan-reviewer` drafts `2a-r1` with those two picks as items pre-set to accept. You counter one; its proposal goes to the log as R1. Commit `REVIEW 2a-r1`, route 2a, applied on the next pass.

**Gate and apply.** 2b through 2e pass. `idea-reviewer` drafts `2f-r1` against `e5f6a7b` (DESIGN v4, model v3) with two items. You add a third, set revise, route 2c. The routed 2c receives the review and the log entries R1 through R3 for its sections. 2c through 2e regenerate. `idea-reviewer` in verify mode quotes the satisfying text for each item; you confirm per item. Commit `APPLY 2f-r1`, `applied_version` `9a8b7c6` (DESIGN v5, model v5). `§status` gets one line. `§model.assumptions` contains the new A3 and nothing about the old one.

**Import.** J. Lin reads the export and sends six comments by email. `/review import external/jlin-2026-10-09.md --from "J. Lin"` produces `ext-r3` as draft, anchored to the version in the export header, with one item flagged `judged_outdated`. You accept two, counter two, decline one, defer one. Two log entries are written. `ext-r3` queues behind the pending `2f-r2`, becomes pending when that applies, routes to 3c. `/review reply ext-r3` gives you a note to send back.

**Rewind.** `§results` refutes H3. `results-reviewer` drafts `5a-r1`: H3 tests PA3, PA3 tests A3, proposed route 2c. You agree. `REWIND 5a-r1`, A3 logged as rejected with the run id, `§model.derivation` onward stale. 2c reruns with the review and the log, and cannot re-propose A3 as it was.

## Why it works, and why it could fail

The mechanism works because each of the four ways an agent drifts now has one named check. Silent gap-filling meets the intake gate and `Choices made`. Historical bloat meets the current-design rule and the three homes for history. Re-proposal of rejected ideas meets the rejection log as a generator input and a gate. Outside opinion meets the converter and the disposition field, which separates a valid finding from a fix you do not want. Underneath, section ownership, section hashes, per-file versions, and the single pending review keep the ledger uniform.

Failure modes, in order of likelihood:

- **Intake fatigue.** The intake reviewer asks twenty questions for a four-line seed. Guard: it must rank by downstream effect and cap at eight; `detail` items are delegatable; the reject rate on `Choices made` items tells you whether delegation is safe.
- **Rejection log becomes a wall.** After a year, the log forbids so much that generators cannot move. Guard: entries carry the idea slug and the reason; `/reject revive` exists; generators see only entries for their sections of the current project unless you pass `--global`.
- **History leaks back.** A generator narrates a change in polite words the banned list misses. Guard: the ref-checker's rejected-span diff is mechanical and catches content, not phrasing; the hygiene reviewer's soft score covers phrasing.
- **Counter without a fix.** You decline a coworker's proposal but their finding was valid and nobody addresses it. Guard: a `decline` on an item whose finding is not also covered by another item requires a reason of the form "finding invalid because"; otherwise the disposition must be `counter`.
- **Review friction.** Ten gates plus intakes. Guard: accepts are one command; D4 prunes gates after a month.
- **Verify mode rubber-stamps.** Guard: quote the satisfying text; confirm per item.
- **Version confusion.** File versions and section hashes disagree in someone's head. Guard: humans read versions, tools read hashes, and `§status` prints both.
- **Premature splitting, git erosion, orchestrator drift, untested own assumptions, loop without progress.** Guards as in v4: budget-only splits, hooks, no research tools, H per PA, bound forces abandon or override.

## Close

### Synthesis

The pipeline keeps its five stages and per-stage contracts. Inside each stage, steps own sections of one design document that starts as a single file and splits under a budget, with stable ids, per-file versions, and Context blocks so every file reads standalone. Your inputs pass an intake gate so an agent never silently chooses what you left open, and every delegated choice surfaces in the next review. Each section states only the current design; git, `§status`, and the rejection log hold the past, and generators are bound by the log. Every human gate produces one review, drafted by an agent and finished by you, bound to the version it judged, routed to one step, and pending until a later version has applied it. Coworkers' reviews enter the same format and each of their proposals is accepted, countered, declined, or deferred on the record.

### Decision register

| id | decision | options | recommend |
|---|---|---|---|
| D1 | step granularity | (a) as proposed; (b) coarser; (c) finer | (a) |
| D2 | state format | (a) `state.yaml` indexed to git; (b) git log only; (c) SQLite | (a) |
| D3 | orchestrator | (a) skill per stage; (b) Python driver; (c) both, skill first | (c) |
| D4 | human gates | (a) all ten; (b) drop 1e, 3e, 4b; (c) only 2a, 2c, 2f, 5a | (a) for a month, then prune |
| D5 | where `work/` lives | (a) this repo; (b) wiki; (c) experiment repo | (a) |
| D6 | loop bound per route | 2 / 3 / unbounded | 3 |
| D7 | build order | (a) stage 2 first; (b) stage 1 first; (c) `doc.py`, `review.py`, ledger, ref-checker first, then stage 2 | (c) |
| D8 | Codex's role | (a) none; (b) `idea-reviewer` and `leakage-auditor` on Codex; (c) Codex drafts | (b) |
| D9 | wiki tool and note format | your answer | needed for `wiki-searcher` |
| D10 | commit enforcement | (a) hooks reject; (b) hooks warn; (c) convention | (a) |
| D11 | staleness | (a) any input change; (b) referenced tokens only; (c) (a) plus "re-verify only" | (c) |
| D12 | who may draft a review | (a) human gates plus `math-checker` and `leakage-auditor`; (b) any gate; (c) human gates only | (a) |
| D13 | own assumptions | (a) PA or explicit "accepted untested"; (b) PA mandatory | (a) |
| D14 | file budget | 300 / 400 / 600 lines | 400 |
| D15 | taxonomy | (a) fixed; (b) per-project template; (c) free-form with required ids | (b) |
| D16 | export format | (a) markdown; (b) plus PDF; (c) plus wiki page | (a) now, (c) after D9 |
| D17 | who verifies application | (a) reviewer proposes per item, you confirm per item; (b) you alone; (c) reviewer alone | (a) |
| D18 | concurrent reviews | (a) one pending, others queued; (b) one per stage; (c) unlimited | (a) |
| D19 | review editing surface | (a) edit the file; (b) `/review` prompts; (c) both | (c) |
| D20 | version counters | (a) per file; (b) per file and per section; (c) per document only | (a) |
| D21 | delegatable intake severity | (a) `detail` only; (b) `detail` and `structural`; (c) anything | (a) |
| D22 | `Choices made` default in the next review | (a) pre-set accept, you may counter; (b) open, you must disposition each | (a) |
| D23 | reply to coworkers | (a) generated on `/review reply` only; (b) generated automatically at apply; (c) never generated | (a) |
| D24 | rejection-log scope for generators | (a) current project's sections; (b) all projects, same section id; (c) all projects, all sections | (a) with `--global` on demand |

### Build map

| component | how it gets built |
|---|---|
| `stages/REFS.md` | id grammar, tokens, taxonomy templates, review and intake schemas, banned-phrase list |
| `scripts/doc.py` | get/put by id, split/merge, stubs, budgets, version bumps, export |
| `scripts/review.py` | draft, validate, commit, import, disposition, verify merge, apply, reply, log writes |
| `scripts/ref_checker.py`, `state.py` | hashing, index, stale sections and reviews, rejected-span diff |
| commit grammar + hooks | ownership, author check, version bump check |
| `STEPS.md` × 5 | tables above per D1, D4 |
| skills: 5 stages, `/split`, `/review`, `/reject` | `/ideate`, `/review`, `/reject` first |
| `intake-reviewer`, `review-converter` | shared item schema |
| `plan-reviewer`, `idea-reviewer`, `results-reviewer` | shared review template, draft and verify |
| `doc-keeper`, `doc-hygiene-reviewer` update | versions, standalone, current-design rule |
| stage 2 generators | 3 benchmark seeds each |
| `paper-reader`, `wiki-searcher` | after D9 |
| stage 3, 4 agents | after stage 2 end to end |
| `/review-logs` | weekly: `REJECT` commits, reopened items, countered `Choices made` |
| `PIPELINE.md` shrink | pointers |

### Timeline

| phase | components | depends on | duration |
|---|---|---|---|
| 0 | decision register D1–D24 | you | 1 sitting |
| 1 | `REFS.md`, `doc.py`, `review.py`, hooks, `state.py`, `ref_checker.py`, `STEPS.md` × 5; a fake project through one intake, one review, one import by hand | 0 | 4 days |
| 2 | `/ideate`, `/review`, `/reject`, `intake-reviewer`, `doc-keeper`, `plan-reviewer`, `idea-reviewer`, stage 2 generators; one idea through with an intake, a revise review, a hand edit, a split, and one logged rejection | 1, D8, D9 | 1 week |
| 3 | `review-converter`, `paper-reader`, `wiki-searcher`, `/read`; 5 papers; one imported coworker review | 2 | 4 days |
| 4 | stages 3–5; one idea to a recorded rewind and an export | 3 | 1 week |
| 5 | `/review-logs`, prune gates, revisit D12 and D24 | 4 | ongoing |
