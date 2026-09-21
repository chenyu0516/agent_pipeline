# Proposal: stages as checkpointed sub-workflows

Status: ACCEPTED v7 on 2026-09-18. Every decision in the register is taken: D6, D9, D16, D21, D24 as decided in the rows, D11 as (c), and every other row at its recommendation. Phase 1 build follows this document; `stages/REFS.md` is the normative grammar from here on.

Changes from v6: loop bounds apply only to consecutive agent-drafted reviews, never to human-set routes; a progress check replaces the bound elsewhere. Intake is split into an initializer that gives you a structural template and a reviewer that only reviews what you filled; structural choices become delegatable. The rejection log gains a curated global tier. D9 is answered: Obsidian vault, and the first project through the pipeline is the wiki-management skill set. Export formats beyond markdown are deferred until the pipeline runs.

Changes from v5: every defined object (assumption, result, prediction, hypothesis, feature, metric, symbol) has a human name and an anchor in the document, and a short id that appears only in definition comments and pipeline files. Prose in the document refers to objects by name with a link, never by id. A resolver maps id, name, or anchor to the current text for both humans and agents. Stage 1 intake runs only when the questions file changes, not per paper.

## Hook

The first workflow map (v0 of what is now `README.md`) treated each stage as one agent call that produces one finished document. Your stages take days, and you discover problems only in that finished document, when everything in it already depends on the mistake. Rejecting a finished idea doc costs you the whole stage. The obvious fix, one file per step, produces fragments no collaborator can read, decisions made in a chat window nobody can find, documents that swell with their own history, and prose full of tokens like "A3" that mean nothing to a coworker.

## Core claim

**Each project is one design document with stable section ids, named and linked objects, and per-file versions; every human input passes an intake gate before an agent elaborates it; each pipeline step owns one section and writes only the current design; every human gate produces one review bound to one document version, co-authored by a reviewer agent and you, pending until a later version has applied it; and everything rejected goes to a log that generators must not contradict.**

## Elaboration

A project's knowledge lives in one design document with a fixed section taxonomy. At the start it is one file. As sections grow they move into their own files with stubs left behind, and section ids never change, so it remains one document. Each file carries a version counter, and a document version is the commit plus every counter. The document is load-bearing twice over: a collaborator reads it, and every agent reads only the sections its step names.

Inside the document, the things the pipeline reasons about are **objects**: an assumption, a derived result, a prediction, a hypothesis, a feature, a metric, a symbol. Each object is defined exactly once, under a heading that gives it a human name, and that heading is its anchor. Prose anywhere in the document refers to the object by name with a link to the anchor. Each object also has a short id such as `A3`, but the id is for machines and pipeline files: it sits in a comment beside the definition, in the index, in reviews, and in the rejection log, always next to the name. A coworker reads "the volatility-persistence assumption" and clicks; an agent reads `A3` and resolves it. The same resolver serves both, and the ref-checker guarantees every link lands on a definition and every link text still matches the object's current name.

Agents deviate from your intent at two moments. The first is when your input is rough and the agent silently chooses the details. The **intake gate** handles this: before a generator touches `seed.md`, `scribble.md`, `data.md`, or `questions.md`, an intake reviewer lists every choice the input leaves open, ranked by downstream effect, and you answer each or explicitly delegate it. Delegated choices are reported by the generator in a visible block and become default items in the next human review.

The second moment is when an agent preserves history inside the document. The **current-design rule** forbids this: a section states only what the design is now. Git holds every version, the `§status` section holds one line per review, and the **rejection log** holds every proposal turned down with its reason. Every generator receives the log entries for its sections and may not re-propose them.

A **review** is a change request against a specific document version. At a human gate a reviewer agent drafts it, you finish it, and it is committed as pending. It routes the pipeline to one step, that step receives it as input, and it is applied only when every item is addressed in a later version, verified by the reviewer and confirmed by you. Coworkers' reviews arrive in any form and are converted into the same object, and for each item you keep their finding and accept, counter, decline, or defer their fix.

## Structure

### 1. Document taxonomy

Every design document has these top-level sections in this order, each with a stable id. Empty sections show as `[pending: step 3c]`.

| id | section | owned by | objects defined here |
|---|---|---|---|
| `§context` | project one-liner, status, file version, how to read the tree | `doc-keeper` | none |
| `§problem` | observed, unknown, why it matters, goal; `Choices made` block | 2a | none |
| `§position` | closest wiki notes, null model, what is new | 2b | none |
| `§model.notation` | symbol table | 2c | symbols |
| `§model.assumptions` | one named assumption per heading, provenance tag; `Choices made` block | 2c | assumptions |
| `§model.formal` | state, parameters, objective in LaTeX; scribble diff appendix | 2c | none |
| `§model.derivation` | numbered steps linking the assumptions they use; one named result per heading | 2d | results |
| `§model.predictions` | one named prediction per heading, each linking the assumption or result it tests, with a kill condition | 2e | predictions |
| `§data` | inventory, plan, gaps; `Choices made` block | 3b | none |
| `§experiment.hypotheses` | one named hypothesis per heading, linking the prediction it tests | 3a | hypotheses |
| `§experiment.procedure` | steps; one named feature and metric per heading; baselines; split | 3c | features, metrics |
| `§experiment.leakage` | per-feature timestamp audit, linking each feature | 3d | none |
| `§implementation` | layout, run ids, deviations | 4a, 4d | none |
| `§results` | per-hypothesis outcome with links, tables, anomalies | 4e | none |
| `§status` | one line per review, with names and links; untested own assumptions by name | orchestrator | none |

Your ML example maps directly: data is `§data`, model architecture is `§model.*`, train and test is `§experiment.*` plus `§implementation`. Decision D15 asks whether the taxonomy is fixed or a per-project template. Stage 1 uses the same mechanism on a wiki note with `§claim`, `§setup`, `§method`, `§results`, `§relevance`, `§hooks`.

### 2. Objects, names, and links

An object is defined once, as a heading inside its owning section. The heading is the object's name, the heading's anchor is its link target, and a comment on the next line carries the id.

```markdown
### Volatility persistence
<!-- object: A3 | kind: assumption | tag: own -->
Conditional volatility $\sigma_t$ satisfies $\rho(\sigma_t, \sigma_{t-1}) > 0.9$ at the daily horizon.
```

Rules:

1. **Names.** Two to four words, unique within the project across all kinds, chosen by the generator and changeable only by a `HUMAN` commit. A name says what the thing is, not what number it has.
2. **Ids.** Permanent. `A3` stays `A3` if the assumption is renamed, moved to another file, or deleted; a deleted id is never reused. Ids never appear in document prose. They appear in the definition comment, `INDEX.yaml`, reviews, the rejection log, `state.yaml`, and agent inputs, always as `A3 "volatility persistence"`.
3. **References in prose.** Always the name with a link: `the [volatility persistence](model.md#volatility-persistence) assumption`. The link is relative to the current file, so it survives splits because the ref-checker rewrites paths when a section moves. In a derivation step: "By [Gaussian noise](#gaussian-noise) and [volatility persistence](#volatility-persistence), the filter gain is ...".
4. **Resolver.** `doc.py resolve A3`, `doc.py resolve "volatility persistence"`, and `doc.py resolve model.md#volatility-persistence` all print the same card: id, name, kind, tag, file and version, section, current text, hash, and every place that links to it. Agents call it before using an object; you call it from the terminal, or click the link in any markdown viewer.
5. **Index.** `INDEX.yaml` gains an `objects` map, maintained by the ref-checker, so lookup is a file read, not a search:

```yaml
objects:
  A3: {name: volatility persistence, kind: assumption, tag: own, section: §model.assumptions,
       file: model.md, anchor: "#volatility-persistence", hash: 41cc..., linked_from: [§model.derivation, §model.predictions, §status]}
  PA3: {name: persistence threshold test, kind: prediction, tests: A3, section: §model.predictions, file: model.md, anchor: "#persistence-threshold-test", hash: ...}
```

6. **Checks.** The ref-checker fails a section when: a bare id appears in prose; a link does not resolve to an object heading; a link's text differs from the object's current name; an object is defined twice; an object is deleted while something still links to it. The hygiene reviewer additionally scores whether names are meaningful to a reader who has not seen the ids.
7. **Registry for readers.** `doc.py export` appends a generated registry: one table per kind, columns name, id, tag, where defined, linked from. Coworkers who read with an LLM get the ids; coworkers who read with their eyes get the names. Decision D25 asks whether the registry also lives in `docs/` as a generated file.

Pipeline files follow the mirror rule: an id never appears without its name. A rejection-log line reads `A3 "volatility persistence"`; a review item reads `object: A3 "volatility persistence" (model.md#volatility-persistence)`; a `§status` line reads "review 2f-r1 revised [volatility persistence](model.md#volatility-persistence)".

### 3. Versioning

Every file in `docs/` has a version counter in `INDEX.yaml` and in its Context block, bumped on every committed change to an owned section. Stub refreshes do not bump. A document version is the commit plus the counters:

```
c3d4e5f
DESIGN.md: v4
model.md: v3
experiment.md: v2
```

Reviews bind to and apply at versions in this form. Section and object hashes exist underneath for the ref-checker. Decision D20.

### 4. Files, splitting, and standalone readability

A project starts as `docs/DESIGN.md` containing every section. When a file exceeds its budget, `/split §model` moves that section and its children to `docs/model.md` at `v1`, leaves a stub, updates `INDEX.yaml`, and rewrites every link path that crossed the split. A stub is a heading, a three-sentence summary regenerated when the child changes, and a link.

Every file must read standalone: a Context block of at most four sentences naming the project, the file's scope and version, what it depends on with links, and its status; every symbol defined in the file or `§model.notation` linked; every cross-reference a named link. Split triggers: a file over budget, or a section with three or more children each over sixty lines. `doc-keeper` proposes; you run `/split`. `doc.py export` concatenates the tree with the registry appended. Decision D14.

### 5. Intake gate for human inputs

Four files are written by you and elaborated by agents: `questions.md`, `seed.md`, `scribble.md`, `data.md`. Each passes an intake gate before the generator that consumes it runs, and the gate reruns only when the file's hash changes.

`questions.md` is different in cadence. It is a long-lived list of your research questions, not a per-paper input, so its intake runs when you edit the questions, not when you read a paper. Per paper, there is no rough human input to elaborate: the paper is the input and the triage gate at 1a is where you correct focus. An optional `--focus "..."` on `/read` passes a one-line hint straight to the reader without intake.

The `intake-reviewer` produces a review of kind `intake` whose items are questions:

```yaml
kind: intake
input: seed.md
input_hash: 77ab...
items:
  - id: Q1
    severity: framing          # framing | structural | detail
    choice: "Is the target the conditional mean of returns or the full distribution?"
    why_it_matters: "Decides whether the formal model is a filter or a density model; changes every downstream section"
    options: ["conditional mean", "full distribution", "both, mean first"]
    answer: null               # an option, free text, or `delegate`
```

Two agents share the gate and never overlap. The **intake-initializer** runs first, once per input file, and turns your rough text into a structural template for that stage: the headings the generator will need, your existing text slotted under the right heading, and each empty slot marked `[fill: <what goes here and why the generator needs it>]`. It proposes nothing. You fill the template. The **intake-reviewer** then reviews what you filled and produces the intake review above: what is still missing, what is ambiguous, what conflicts with an earlier decision, each with severity and downstream effect. It reviews; it does not write content into the template.

Rules: framing items must be answered by you; structural and detail items may be marked `delegate`; the filled template is the input file itself, so there is no second copy; the generator lists every delegated choice in a `Choices made` block at the end of its section; every such entry becomes a pre-filled item in the next human review of that section. The initializer reruns only if you ask, since your filled text is the source; the reviewer reruns whenever the file's hash changes. Decisions D21, D22.

### 6. Current-design rule and the rejection log

A section states only what the design is now. Hard rules: no narration of change (banned: "previously", "originally", "we changed", "was rejected", "instead of the earlier", "updated to"); no superseded content, checked mechanically by diffing against rejected attempts and the prior version; no rationale for a change inside a section; `Choices made` is the only explanatory block and covers only delegated intake choices.

History has three homes:

| home | holds | written by |
|---|---|---|
| git | every version of everything | hooks |
| `§status` | one line per review, names linked | orchestrator |
| `pipeline/REJECTED.md` | every proposal turned down, with reason | `review.py`, `/reject` |

The rejection log is append-only:

```
R17 | 2026-10-02 | 2f-r1 | A3 "volatility persistence" | proposal: tag as [standard] | rejected: no source; retagged [own] with PA3 "persistence threshold test" | by: chen-yu
R18 | 2026-10-09 | ext-r3 | §experiment.procedure | proposal: "use Sharpe as primary metric" (from: J. Lin) | countered: conflates PR1 "forecast correlation" and PR2 "forecast variance"; use IC per hypothesis | by: chen-yu
R19 | 2026-10-09 | manual | §model.formal | proposal: "model σ_t as GARCH(1,1)" | rejected: tried in vol-garch-2025, prediction failed | by: chen-yu
```

Entries are written automatically when a review item removes or replaces something, when an imported item is countered or declined, when a stage 5 rewind names a falsified assumption, and manually through `/reject`. Every generator receives the entries for its sections, and every generator pass rule includes "nothing in the log for these sections". `/reject revive R17 --why` marks an entry revived; nothing is deleted.

The log has two tiers. The project log at `work/<slug>/pipeline/REJECTED.md` is automatic and complete. The global log at `agent/REJECTED-global.md` is curated: `/reject promote R19` copies an entry there when the lesson outlives the project, such as "GARCH(1,1) for this volatility target failed its prediction in vol-garch-2025". Every generator receives its project entries plus the whole global log. Decision D24.

### 7. Review object

One file per review, append-only, at `pipeline/reviews/<step>-r<n>.md` or `ext-r<n>.md`.

```yaml
---
id: 2f-r1
kind: gate                        # gate | intake | external
step: 2f
origin: internal
external_source: null
doc_version: {commit: c3d4e5f, files: {DESIGN.md: v4, model.md: v3}}
sections_judged: {§model.assumptions: 41cc..., §model.derivation: 8a2b...}
authors: [idea-reviewer, chen-yu]
verdict: revise                   # accept | revise | abandon
route_to: 2c
status: pending                   # draft | pending | applied | waived | superseded | stale
applied_version: null
items:
  - id: I1
    object: A3 "volatility persistence" (model.md#volatility-persistence)
    source: idea-reviewer
    finding: "assumes persistence above 0.9 with no source"
    proposal: "tag [own]; add a prediction with a measurable threshold"
    disposition: accept           # accept | counter | decline | defer
    required: "tag [own]; add a prediction with a measurable threshold"
    logged: null
    status: open                  # open | addressed | waived
    addressed_at: null
---
<prose: reviewer draft, then your edits, appended in order>
```

Rules: binds to one version and one hash per judged section, goes `stale` if a judged section changes off-route; every item has a `finding` and a `required`, with `proposal` preserved as what the source suggested; only you set `verdict`, `route_to`, `disposition`; one pending review per project, others queued; applied when every item is addressed or waived and you confirm per item, with the reviewer in verify mode quoting the satisfying text; an accept is a review with no blocking items; a cross-stage route is a rewind. Decisions D17, D18.

### 8. External reviews

`/review import <file> --from "J. Lin"` runs `review-converter`, which identifies the version they read from the export header, splits their text into items anchored to sections and objects by name, flags items whose judged text has changed, proposes a disposition and a route, and writes `ext-r<n>.md` as draft. You disposition each item. `counter` keeps their finding, replaces the fix with yours, and logs theirs. `decline` requires a reason of the form "finding invalid because"; if the finding stands, the disposition must be `counter`. `/review reply ext-r3` produces a note for the coworker in names, not ids. Decision D23.

### 9. Step schema

| field | meaning |
|---|---|
| id | stage number plus letter |
| owner | agent name, or `reviewer → human` at a human gate |
| input | section ids and files; a routed step also receives the pending review and the log entries for its sections |
| output | owned section ids, or a review |
| pass rule | one sentence; generators implicitly add "nothing in the log for these sections" and "objects named and linked, no bare ids" |
| gate | `hygiene`, a reviewer agent, `tests`, `intake`, or `review`; `refs` implicit |
| on fail | `retry`, or whatever `route_to` says |

### 10. Ledger: git plus state.yaml

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
  2c: {status: done, sections: [§model.notation, §model.assumptions, §model.formal], attempts: 2, commit: c3d4e5f,
       built_from: {§problem: 9e1f..., scribble.md: 19cd..., §position: 12cd...}}
  2d: {status: stale, sections: [§model.derivation], commit: d4e5f6a,
       built_from: {§model.assumptions: 41cc..., §model.formal: 8a2b...}, stale_reason: "review 2f-r1 routed to 2c"}
pending_review: pipeline/reviews/2f-r1.md
queued_reviews: [pipeline/reviews/ext-r3.md]
reviews:
  - {id: 2a-in1, kind: intake, status: applied}
  - {id: 2f-r1, verdict: revise, route_to: 2c, status: pending}
rejected_count: 19
loops: {2f->2c: 1}
```

**Commit rules**, enforced by hooks (D10): one step per commit touching only its sections, `state.yaml`, and `INDEX.yaml`; tree clean before any step; message `<slug>/<step> <VERB>[ a<n>][ <review-id>]: <one line>` with verbs `PASS`, `REJECT`, `HUMAN`, `INTAKE`, `REVIEW`, `IMPORT`, `APPLY`, `WAIVE`, `LOOP`, `REWIND`, `STALE`, `SPLIT`, `EXPORT`, `REJECT-LOG`; rejected attempts to `pipeline/attempts/`, rejected proposals to `REJECTED.md`; `HUMAN` commits during a pending review only on the routed step's sections; `APPLY` records `applied_version`; `LOOP` in-stage, `REWIND` across stages; no history rewriting on `work/`; stage tags trigger `EXPORT`; `head` mismatch triggers a rebuild you confirm.

### 11. Orchestrator

One skill per stage, `/read`, `/ideate`, `/design`, `/implement`, `/verdict`, plus `/split`, `/review`, `/reject`. Behavior, in order:

0. **Consistency.** Tree clean; head matches; last commit matches last state entry.
1. **References.** Rehash sections and objects; rebuild the `objects` map; resolve every link; check link texts against names; mark stale sections and reviews; check budgets; commit `STALE` if anything changed.
2. **Intake.** For an input file seen for the first time, run `intake-initializer`, write the template back into the file, and stop for you to fill it. For an input file whose hash changed since its last intake review, run `intake-reviewer`, write the intake review as draft, and stop.
3. **Pending review.** Only `route_to` and downstream are runnable; on completion, verify mode, then your per-item confirmation, then `APPLY` and promote the next queued review.
4. **Human gate.** Draft the review with `Choices made` entries pre-loaded, stop; `/review commit` validates and commits.
5. **Run.** Extract input sections, the pending review if routed, the log entries for the owned sections, and resolver cards for every object the inputs link; run the agent; write output; bump versions.
6. **Automated gate.** Hygiene, refs, log dedupe, specialist. Fail: `REJECT`, retry once; second fail stops.
7. **Commit.** `PASS`; continue unless the next step is a human gate.
8. **Progress check.** Routes you set are unbounded, since new information from coworkers or experiments can arrive at any time. Two guards replace the bound. Consecutive agent-drafted reviews (`math-checker`, `leakage-auditor`) with no human review between them are capped at two, after which the orchestrator stops and asks you. And when a new review's items match a prior review's items on the same objects with no intervening change to those objects, the orchestrator flags "no progress since <review id>" and asks you to confirm before routing.

No research tools. Writes only `state.yaml`; calls `doc.py`, `review.py`, git; invokes agents.

### 12. Stage decompositions

⏸ human gate, ⌂ intake gate. `refs`, log dedupe, and object naming are implicit on every generator step.

**Stage 1, Read.** `/read <pdf-or-arxiv-id> [--focus "..."]`.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 1·in ⌂ | intake, only when `questions.md` changes | `intake-reviewer` → human | `questions.md` | intake review; `## Decisions` | no open framing item | intake | you answer |
| 1a ⏸ | triage | `paper-reader`; `plan-reviewer` → human | pdf, `questions.md`, focus | `§claim`; review 1a-r<n> | accept means read | review | abandon archives |
| 1b | extract model | `paper-reader` | pdf | `§setup` | every symbol in table; every equation cited | hygiene | retry |
| 1c | extract method + results | `paper-reader` | pdf, `§setup` | `§method`, `§results` | no number without a cite | hygiene | retry |
| 1d | relate | `wiki-searcher` | `§setup`, `§method`, `§results`, `questions.md`, wiki | `§relevance`, `§hooks` | "none" allowed; Inference labels; cites only existing notes | hygiene | retry |
| 1e ⏸ | finalize | `doc-keeper`; `plan-reviewer` → human | all | `§context`; review 1e-r<n> | full contract; standalone | review | route per review |

**Stage 2, Ideate.** `/ideate <slug>`.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 2a·in ⌂ | intake | `intake-reviewer` → human | `seed.md` | intake review; `## Decisions` | no open framing or structural item | intake | you answer |
| 2a ⏸ | frame | `idea-drafter`; `plan-reviewer` → human | `seed.md` with decisions, log | `§problem` with `Choices made`; review 2a-r<n> | accept; every delegated choice seen | review | route 2a |
| 2b | position | `wiki-searcher` | `§problem`, wiki | `§position` | null model named; cites only existing notes | hygiene | retry |
| 2c·in ⌂ | intake | `intake-reviewer` → human | `scribble.md`, `§problem` | intake review; `## Decisions` | no open framing or structural item | intake | you answer |
| 2c ⏸ | formalize | `idea-drafter`; `plan-reviewer` → human | `§problem`, `§position`, `scribble.md` with decisions, log, pending review if routed | `§model.notation`, `§model.assumptions` (named, tagged), `§model.formal`; review 2c-r<n> | every assumption named and tagged; scribble diff present; math rules; delegated choices seen | hygiene, review | route 2c |
| 2d | derive | `deriver` | `§model.*` inputs, resolver cards, log, pending review if routed | `§model.derivation` (named results) | every step links the assumptions it uses; no unlisted assumption | `math-checker` | drafts a review to 2c |
| 2e | predict | `idea-drafter` | `§model.assumptions`, `§model.derivation`, log | `§model.predictions` (named, each linking what it tests) | every `[own]` assumption has a prediction or `untestable, accepted`; every result has a prediction; no empirical numbers | hygiene | retry |
| 2f ⏸ | adversarial review | `idea-reviewer` → human | `§problem` through `§model.predictions`, log | review 2f-r<n> | you set verdict and route | review | route 2c or 2d |
| 2g | finalize | `doc-keeper` | all | `§context`, `§status`, stubs, export | budgets; standalone | hygiene | retry |

Step 2d derives the chain of consequences from the assumptions to named results, each step linking the assumptions it uses; a missing assumption becomes a drafted review to 2c, never a silent addition. Step 2e converts each result and each own assumption into a named prediction that data can contradict, with quantity, direction, comparison, and kill condition.

**Stage 3, Design.** `/design <slug>`.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 3a | map hypotheses | `experiment-designer` | `§model.predictions`, log | `§experiment.hypotheses` (named, each linking its prediction) | every own-assumption prediction has a hypothesis; max 3 result-hypotheses | hygiene | retry |
| 3b·in ⌂ | intake | `intake-reviewer` → human | `data.md`, `§experiment.hypotheses` | intake review; `## Decisions` | no open structural item | intake | you answer |
| 3b ⏸ | data | `experiment-designer`; `plan-reviewer` → human | `§experiment.hypotheses`, `data.md` with decisions, log | `§data` with `Choices made`; review 3b-r<n> | no field outside `data.md`; gaps explicit | review | route 3b |
| 3c | procedure | `experiment-designer` | `§experiment.hypotheses`, `§data`, `§model.notation`, log | `§experiment.procedure` (named features and metrics) | every hypothesis has a metric and a baseline | hygiene | retry |
| 3d | leakage audit | `leakage-auditor` | `§experiment.procedure` | `§experiment.leakage` | every feature linked and audited; no violation | `leakage-auditor` | drafts a review to 3c |
| 3e ⏸ | finalize | `doc-keeper`; `plan-reviewer` → human | all | `§context`, `§status`, export; review 3e-r<n> | budgets; standalone | review | route per review |

**Stage 4, Implement.** `/implement <slug>`.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 4a | scaffold | `implementer` | `§experiment.procedure` | code skeleton, synthetic tests; `§implementation` | tests exist and fail for the right reason | tests | retry |
| 4b ⏸ | loader + lookahead test | `implementer`; `plan-reviewer` → human | `§data`, `§experiment.leakage` | loader; lookahead test; review 4b-r<n> | tests pass on a real-data sample | tests, review | route 4b or 3c |
| 4c | implement | `implementer` | `§experiment.procedure`, code | function + test per step | all tests green | tests | retry per step |
| 4d | run | `implementer` | code | `runs/<id>/`; `§implementation` run entry | run completes; seeds logged | tests | stop |
| 4e | report | `results-reporter` | `runs/<id>/`, `§experiment.*` | `§results` (per hypothesis, linked) | every number traces to a run file; every hypothesis present | hygiene | retry |

**Stage 5, Verdict.** `/verdict <slug>`.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 5a ⏸ | verdict | `results-reviewer` → human | `§results`, `§experiment.*`, `§model.*`, log | review 5a-r<n> (each refuted hypothesis traced by link to an assumption or result; candidate causes with evidence; proposed route) | you set verdict and route | review | — |
| 5b | record | orchestrator, `doc-keeper` | review | `REWIND` or tag; stale marks; `§status`; log entries for falsified assumptions by name; wiki note; export | ledger consistent | refs | stop |

| verdict and route at 5a | commit | marked stale |
|---|---|---|
| accept | tag `<slug>/confirmed` | nothing |
| revise → 4c | `REWIND` | `§implementation` runs, `§results` |
| revise → 3c | `REWIND` | `§experiment.leakage`, stage 4 |
| revise → 2c, assumption named | `REWIND`; assumption logged with the refuting hypothesis | `§model.derivation` onward |
| revise → 2a | `REWIND` | everything after `§problem` |
| abandon | tag `<slug>/abandoned`; core claim logged | nothing |

### 13. Gate types

- **intake**: `intake-reviewer` on human inputs; blocks until framing and structural choices are answered.
- **hygiene**: `doc-hygiene-reviewer` on every prose section; standalone, current-design rule, meaningful names.
- **refs**: `ref_checker.py`, deterministic; section ids, object links and names, hashes, Context blocks, budgets, stale sections and reviews, rejected-span reappearance, bare ids in prose.
- **log dedupe**: the section's reviewer checks output against rejection-log entries and cites the entry on failure.
- **specialist automated**: `math-checker`, `leakage-auditor`; draft a review backward on failure.
- **tests**: pytest, stage 4.
- **review**: the human gate; ten of them plus specialist-drafted reviews you confirm.

### 14. Agent roster

| agent | steps | model | notes |
|---|---|---|---|
| `doc-hygiene-reviewer` | all prose | Sonnet | built; add standalone, current-design rule, name quality |
| `ref-checker` | all | script | no LLM; owns the `objects` map and the resolver |
| `intake-initializer` | 1·in, 2a·in, 2c·in, 3b·in, first pass | Sonnet | turns rough input into a stage-specific template with your text slotted in and empty slots marked; proposes no content |
| `intake-reviewer` | 1·in, 2a·in, 2c·in, 3b·in, every change | Opus | reviews the filled template; lists what is missing, ambiguous, or conflicting with severity; never fills anything |
| `review-converter` | `/review import` | Opus | maps coworker text to items by object name; proposes dispositions |
| `doc-keeper` | 1e, 2g, 3e, 5b, `/split` | Sonnet | Context, stubs, index, versions, export with registry, wiki notes, `§status` |
| `plan-reviewer` | drafts 1a, 1e, 2a, 2c, 3b, 3e, 4b | Opus | checks against contract, previous review, `Choices made`, log |
| `idea-reviewer` | 2f draft and verify | Opus or Codex | adversarial; D8 |
| `results-reviewer` | 5a draft and verify | Opus | traces refuted hypotheses by link; proposes route |
| `math-checker` | gate 2d | Opus | |
| `leakage-auditor` | gate 3d | Sonnet | |
| `wiki-searcher` | 1d, 2b | Sonnet | only wiki access |
| `paper-reader` | 1a–1c | Sonnet | only PDF access |
| `idea-drafter` | 2a, 2c, 2e | Opus | names objects; tags provenance; writes `Choices made` |
| `deriver` | 2d | Opus | names results; may not add assumptions |
| `experiment-designer` | 3a–3c | Opus | names hypotheses, features, metrics |
| `implementer` | 4a–4d | Sonnet, Opus for 4c | |
| `results-reporter` | 4e | Sonnet | never judges |

### 15. Repository layout

The layout as built, with every file annotated, is `README.md` section 3. The README also holds setup, tool descriptions, hook behavior, the manual operating procedure, template authoring, the self-test, and the table of where the build deviates from this document.

## Process: intake, review, import, rewind

**Intake.** You write a four-line `seed.md` and run `/ideate vol-regime-kalman`. The initializer rewrites the file as a template: your four lines slotted under Observed and Goal, and empty slots for Unknown, Target quantity, Horizon, Data you have in mind, each marked with why the drafter needs it. You fill four slots and leave two blank. The reviewer returns five items: two framing you must answer, three structural or detail you delegate. `idea-drafter` writes `§problem` with a `Choices made` block. `plan-reviewer` drafts `2a-r1` with those two choices as items pre-set to accept. You counter one; its proposal is logged. Applied on the next pass.

**Naming.** At 2c the drafter defines four assumptions as headings: Gaussian noise, latent mean reversion, volatility persistence, known volatility scale. The ids `A1` to `A4` sit in comments. `§model.formal` says "under [Gaussian noise](#gaussian-noise) and [latent mean reversion](#latent-mean-reversion), the state equation is ...". The ref-checker confirms four links, four definitions, no bare ids.

**Gate and apply.** `idea-reviewer` drafts `2f-r1` against `e5f6a7b` (DESIGN v4, model v3). Item I1 reads `object: A3 "volatility persistence"`, finding "no source", proposal "tag own; add a threshold prediction". You accept, route 2c. 2c reruns with the review, the log, and the resolver card for `A3`. The new `§model.assumptions` tags the heading own; `§model.predictions` gains a heading "Persistence threshold test" linking to it. Verify mode quotes both. `APPLY 2f-r1` at `9a8b7c6` (DESIGN v5, model v5). `§status` reads: "2f-r1 judged c3d4e5f (DESIGN v4, model v3), revise → 2c, applied 9a8b7c6 (DESIGN v5, model v5): [volatility persistence](model.md#volatility-persistence) retagged own; [persistence threshold test](model.md#persistence-threshold-test) added."

**Import.** J. Lin reads the export, sees "volatility persistence" in the prose and `A3` only in the registry appendix, and emails six comments naming things by name. `/review import` anchors each to the object, flags one as judged on an older version, proposes dispositions. You accept two, counter two, decline one with "finding invalid because", defer one. `/review reply` gives you a note in names.

**Rewind.** `§results` refutes the hypothesis "Persistence threshold holds". `results-reviewer` drafts `5a-r1` tracing it by link to the persistence threshold test and then to volatility persistence, proposed route 2c. You agree. `REWIND`, the assumption logged with the run id, downstream stale, 2c reruns and cannot re-propose it unchanged.

## Why it works, and why it could fail

The mechanism works because each way an agent or a document drifts now has one named check. Silent gap-filling meets intake and `Choices made`. Historical bloat meets the current-design rule. Re-proposal meets the log. Outside opinion meets the converter and dispositions. Unreadable tokens meet names, anchors, and the mirror rule, with one resolver serving the person who clicks and the agent that queries. Underneath, section ownership, hashes, per-file versions, and the single pending review keep the ledger uniform.

Failure modes, in order of likelihood:

- **Name drift.** Someone renames an assumption by hand and forty links go stale in meaning while still resolving. Guard: rename is a `HUMAN` commit; the ref-checker rewrites link texts to the new name in the same commit or refuses it.
- **Names that are numbers in disguise.** The drafter names things "assumption three". Guard: the hygiene reviewer's name-quality score; names must not contain kind words or ordinals.
- **Intake fatigue.** Guard: rank by downstream effect, cap at eight, detail delegatable.
- **Log becomes a wall.** Guard: scoped to the current project's sections by default; revive exists.
- **History leaks back.** Guard: mechanical rejected-span diff plus phrase list.
- **Counter without a fix.** Guard: decline needs "finding invalid because"; otherwise counter.
- **Loop without progress.** The same items reopen on the same objects. Guard: the progress check flags a repeat and asks you; agent-drafted loops cap at two without you.
- **Review friction, verify rubber-stamping, version confusion, premature splitting, git erosion, orchestrator drift, untested own assumptions.** Guards as before: one-command accepts and pruning; quote per item; humans read versions and tools read hashes; budget-only splits; hooks; no research tools; a hypothesis per own-assumption prediction.

## Close

### Synthesis

The pipeline keeps its five stages and per-stage contracts. Inside each stage, steps own sections of one design document that starts as a single file and splits under a budget, with stable section ids, named and linked objects, per-file versions, and Context blocks so every file reads standalone for a coworker and resolves cleanly for an agent. Your inputs pass an intake gate so nothing you left open is chosen silently. Each section states only the current design; git, `§status`, and the rejection log hold the past, and generators are bound by the log. Every human gate produces one review, drafted by an agent and finished by you, bound to the version it judged, routed to one step, and pending until a later version has applied it. Coworkers' reviews enter the same format and each of their proposals is dispositioned on the record, in names they recognize.

### Decision register

| id | decision | options | recommend |
|---|---|---|---|
| D1 | step granularity | (a) as proposed; (b) coarser; (c) finer | (a) |
| D2 | state format | (a) `state.yaml` indexed to git; (b) git log only; (c) SQLite | (a) |
| D3 | orchestrator | (a) skill per stage; (b) Python driver; (c) both, skill first | (c) |
| D4 | human gates | (a) all ten; (b) drop 1e, 3e, 4b; (c) only 2a, 2c, 2f, 5a | (a) for a month, then prune |
| D5 | where `work/` lives | (a) this repo; (b) wiki; (c) experiment repo | (a) |
| D6 | loop bound | decided: human-set routes unbounded; agent-drafted reviews capped at two consecutive; progress check on repeated items | — |
| D7 | build order | (a) stage 2 first; (b) stage 1 first; (c) `doc.py`, `review.py`, ledger, ref-checker first, then stage 2 | (c) |
| D8 | Codex's role | (a) none; (b) `idea-reviewer` and `leakage-auditor` on Codex; (c) Codex drafts | (b) |
| D9 | wiki | decided: Obsidian vault, LLM-wiki framework, markdown with frontmatter and wikilinks; `wiki-searcher` reads the vault on disk; the first project through the pipeline is the wiki-management skill set | — |
| D10 | commit enforcement | (a) hooks reject; (b) hooks warn; (c) convention | (a) |
| D11 | staleness: when an input section changes, which dependents are marked stale | (a) every dependent of that section, even for a typo; (b) only dependents that link an object whose own hash changed, which misses a newly added assumption a derivation should now use; (c) as (a), but when no linked object changed the orchestrator offers "re-verify only", which reruns the dependent's gate against the new inputs instead of regenerating it | (c) |
| D12 | which automated gates may draft a review that routes backward, outside the ten human gates where `plan-reviewer`, `idea-reviewer`, and `results-reviewer` always draft | (a) `math-checker` and `leakage-auditor` only; (b) any automated gate including hygiene; (c) none, automated gates only reject and retry | (a) |
| D13 | own assumptions | (a) prediction or explicit "accepted untested"; (b) prediction mandatory | (a) |
| D14 | file budget | 300 / 400 / 600 lines | 400 |
| D15 | taxonomy | (a) fixed; (b) per-project template, with a tooling template needed for the first project; (c) free-form with required ids | (b) |
| D16 | export format | decided: markdown only until the pipeline runs end to end; backlog in this order: HTML slides for group meeting, Quarto for static Python, Marimo for interactive; all are renderers over the same document tree | — |
| D17 | who verifies application | (a) reviewer proposes per item, you confirm per item; (b) you alone; (c) reviewer alone | (a) |
| D18 | concurrent reviews | (a) one pending, others queued; (b) one per stage; (c) unlimited | (a) |
| D19 | review editing surface | (a) edit the file; (b) `/review` prompts; (c) both | (c) |
| D20 | version counters | (a) per file; (b) per file and per section; (c) per document only | (a) |
| D21 | delegatable intake severity | decided: (b) `detail` and `structural`; `intake-initializer` supplies the structural template, `intake-reviewer` only reviews; framing must be answered by you | — |
| D22 | `Choices made` default in the next review | (a) pre-set accept, you may counter; (b) open, you must disposition each | (a) |
| D23 | reply to coworkers | (a) on `/review reply` only; (b) automatically at apply; (c) never | (a) |
| D24 | rejection-log scope for generators | decided: project log plus a curated global log filled by `/reject promote`; no flag | — |
| D25 | registry: a generated index of every object, all kinds, with name, id, tag, location, and links; symbols from the notation table are one kind among seven | (a) export appendix only; (b) also a generated `docs/REGISTRY.md`; (c) also inline at the end of each file | (b), one generated file, never edited |
| D26 | object id visibility for coworkers | (a) ids only in the registry appendix; (b) ids also as hover text on links; (c) ids also in a footnote per definition | (a) |
| D27 | anchor scheme | (a) heading text slug, GitHub style; (b) explicit `{#id}` attributes, pandoc style; (c) both, slug canonical | (a); works in GitHub, Obsidian, VS Code without plugins |

### Build map

| component | how it gets built |
|---|---|
| `stages/REFS.md` | section ids, object kinds, naming rules, anchor scheme, taxonomy templates, review and intake schemas, banned phrases |
| `scripts/doc.py` | get/put by section, `resolve` by id, name, or anchor, split/merge with link rewriting, stubs, budgets, versions, export with registry |
| `scripts/review.py` | draft, validate, commit, import, disposition, verify merge, apply, reply, log writes |
| `scripts/ref_checker.py`, `state.py` | section and object hashing, `objects` map, link resolution and name match, stale marks, rejected-span diff, bare-id scan |
| commit grammar + hooks | ownership, author check, version bump, rename link rewrite |
| `STEPS.md` × 5 | tables above per D1, D4 |
| skills: 5 stages, `/split`, `/review`, `/reject` | `/ideate`, `/review`, `/reject` first |
| `intake-initializer` | one template per input kind in `REFS.md`, specialized per project taxonomy |
| `intake-reviewer`, `review-converter` | shared item schema, object-name anchoring |
| `plan-reviewer`, `idea-reviewer`, `results-reviewer` | shared review template, draft and verify |
| `doc-keeper`, `doc-hygiene-reviewer` update | versions, registry, standalone, current-design rule, name quality |
| stage 2 generators | 3 benchmark seeds each; naming rules in every prompt |
| `paper-reader`, `wiki-searcher` | after D9 |
| stage 3, 4 agents | after stage 2 end to end |
| `/review-logs` | weekly: `REJECT` commits, reopened items, countered `Choices made`, renamed objects |
| `README.md` | pointer table and build phases (formerly `PIPELINE.md`) |

### Timeline

| phase | components | depends on | duration |
|---|---|---|---|
| 0 | decision register D1–D27 | you | 1 sitting |
| 1 | `REFS.md`, `doc.py` with resolver, `review.py`, hooks, `state.py`, `ref_checker.py`, `STEPS.md` × 5; a fake project with six named objects through one intake, one review, one import, one split, one rename | 0 | 4 days |
| 2 | `/ideate`, `/review`, `/reject`, `intake-initializer`, `intake-reviewer`, `doc-keeper`, `plan-reviewer`, `idea-reviewer`, stage 2 generators, tooling taxonomy template; first project: the Obsidian wiki-management skill set, taken through intake, a revise review, a hand edit, a split, and one logged rejection; export read cold by one coworker | 1, D8 | 1 week |
| 3 | `review-converter`, `paper-reader`, `wiki-searcher`, `/read`; 5 papers; one imported coworker review | 2 | 4 days |
| 4 | stages 3–5; one idea to a recorded rewind and an export | 3 | 1 week |
| 5 | `/review-logs`, prune gates, revisit D12 and D24 | 4 | ongoing |
