# REFS: the normative grammar

Everything machine-checked in this pipeline is defined here. `PROPOSAL-subworkflows.md` explains why; this file says what. Scripts in `scripts/` implement exactly these rules and nothing more.

## 1. Project layout

A project is its own git repository. The pipeline governs `docs/` and `.pipeline/`; everything else in the repository commits freely.

```
<project>/                    git repository; the slug is its directory name
  README.md                   short human entry point, written at init, free to edit
  docs/
    DESIGN.md                 root of the design tree, always present
    <name>.md                 split-out sections
    <name>/<child>.md         nested splits
    REGISTRY.md               generated object index, never edited
    REJECTED.md               project rejection log, append-only
    DEFERRED.md               deferred review items
    inputs/                   seed.md scribble.md data.md questions.md, each ending with ## Decisions
    reviews/                  <step>-r<n>.md, <step>-in<n>.md, ext-r<n>.md, append-only
    reviews/external/         coworker originals
    export/<slug>-full.md     generated single-file export with registry appendix
  src/                        code
  scripts/                    experiment scripts
  runs/<id>/                  experiment runs
  .githooks/                  pre-commit, commit-msg, post-commit wrappers written at init
  .pipeline/
    state.yaml                ledger index
    INDEX.yaml                sections, objects, versions (rebuilt by every tool run; versions persisted)
    template.yaml             copy of the taxonomy template, so the project is self-contained
    attempts/                 rejected attempts, <step>-a<n>.md
    tool_root                 absolute path of the agent_pipeline checkout; gitignored, machine-local

<agent_pipeline>/REJECTED-global.md   curated cross-project rejection log, in the tool repository
```

Hooks find the tools through `$AGENT_PIPELINE_ROOT`, then `.pipeline/tool_root`, then `rp` on `PATH`.

## 2. File format

Every file under `docs/` is:

```markdown
# <Title>
<!-- file: model.md | version: v3 -->

> **Context.** <at most four sentences: project, what this file covers, what it depends on with links, status>

## <Section heading>
<!-- section: §model | owner: 2c -->
...
```

Rules: exactly one H1; the file comment on the line after it; the Context blockquote before the first section; the version in the comment equals `INDEX.yaml`. The version bumps by one on every committed change to an owned section in that file. Stub refreshes do not bump.

## 3. Sections

A section is a heading whose next non-blank line is a section comment:

```markdown
### Assumptions
<!-- section: §model.assumptions | owner: 2c -->
```

- Id grammar: `§` then lowercase words joined by dots, `§model.assumptions`. Nesting follows the dots and the heading levels.
- Extent: from the heading to the next heading of equal or higher level, or end of file.
- Owner: a step id from `STEPS.md`, `doc-keeper`, or `orchestrator`. Only the owner's step may change the section in a `PASS` or `REJECT` commit.
- Empty section body: exactly `[pending: step <id>]`.
- The set and order of sections come from the project's taxonomy template in `stages/templates/`.

A stub marks a section that has moved to another file:

```markdown
### Model
<!-- stub: §model | file: model.md -->
<three-sentence summary, or [summary pending]>
See [Model](model.md#model).
```

## 4. Objects

An object is a heading whose next non-blank line is an object comment. It lives inside the section that the template says defines its kind.

```markdown
#### Volatility persistence
<!-- object: A3 | kind: assumption | tag: own -->
Conditional volatility $\sigma_t$ satisfies $\rho(\sigma_t, \sigma_{t-1}) > 0.9$ at the daily horizon.
```

- **Name** is the heading text: two to five words, unique across the project ignoring case, no kind word (assumption, result, prediction, hypothesis, feature, metric, symbol, requirement, component, interface, test, decision), no ordinal or digit, changed only by a `HUMAN` commit.
- **Id** is permanent: prefix from the template's kind table plus an integer, `A3`. A deleted id is never reused. Ids never appear in prose under `docs/`. They appear in object comments, `INDEX.yaml`, `REGISTRY.md`, reviews, logs, `state.yaml`, and agent inputs, always paired with the name as `A3 "volatility persistence"`.
- **Tag** is required for assumptions: `lit`, `standard`, or `own`. Optional `tests: <id>` on predictions and hypotheses names what they test.
- **Anchor** is the GitHub slug of the heading: lowercase, drop characters other than letters, digits, spaces, hyphens, then spaces to hyphens. All headings in a file must have distinct anchors.
- **Extent**: heading to the next heading of equal or higher level, or the section end.

Default kind table (templates may override):

| prefix | kind | defined in (quant-model) |
|---|---|---|
| S | symbol | `§model.notation` |
| A | assumption | `§model.assumptions` |
| R | result | `§model.derivation` |
| PA | prediction, tests an assumption | `§model.predictions` |
| PR | prediction, tests a result | `§model.predictions` |
| H | hypothesis | `§experiment.hypotheses` |
| F | feature | `§experiment.procedure` |
| M | metric | `§experiment.procedure` |

## 5. Links

A reference to an object or section in prose is always a markdown link whose text is the object's current name and whose target is the anchor, with a path when the target is in another file:

```markdown
By [Gaussian noise](#gaussian-noise) and [volatility persistence](model.md#volatility-persistence), ...
```

Paths are relative to the linking file. The ref-checker rewrites paths after a split and rewrites link text after a rename; a rename commit that would leave a mismatched link text is refused.

## 6. Prose rules checked mechanically

Hard failures under `docs/`:

- a bare object id in prose (outside comments, code, math, link targets);
- a link that does not resolve, or whose text differs from the object's current name;
- a duplicate object name or duplicate anchor;
- a file without H1, file comment, or Context blockquote, or a Context over four sentences;
- a section missing, duplicated, or out of template order;
- a banned phrase: previously, originally, we changed, was rejected, instead of the earlier, as before, updated to, formerly, no longer, used to;
- a span of six or more consecutive words reused from a rejected proposal in the rejection log for the same section or an object in it (rejected attempts are quality failures and are not matched, since a retry legitimately keeps most of its text).

Warnings: file over budget; section with three or more children each over sixty lines; stub summary pending.

## 7. Versions

A document version is the commit plus every file counter:

```
c3d4e5f
DESIGN.md: v4
model.md: v3
```

Section and object hashes (sha1 of extent text) sit underneath for staleness and review binding.

## 8. Ledger

`pipeline/state.yaml`:

```yaml
slug: vol-regime-kalman
template: quant-model
stage: ideate
head: 3f9c2a1
versions: {DESIGN.md: 4, model.md: 3}
inputs:
  seed.md: {hash: 77ab, intake: 2a-in1, status: applied}
steps:
  2c: {status: done, sections: [§model.notation, §model.assumptions, §model.formal], attempts: 2, commit: c3d4e5f,
       built_from: {§problem: 9e1f, scribble.md: 19cd}}
  2d: {status: stale, sections: [§model.derivation], commit: d4e5f6a,
       built_from: {§model.assumptions: 41cc}, stale_reason: "...", reverify_ok: true}
pending_review: pipeline/reviews/2f-r1.md
queued_reviews: []
reviews: [{id: 2f-r1, kind: gate, verdict: revise, route_to: 2c, status: pending}]
loops: {"2f->2c": 1}
rejected_count: 19
```

Step status: `pending`, `in_progress`, `done`, `stale`. `reverify_ok` is true when the step's inputs changed but no object its sections link changed, so the orchestrator may offer re-verify only.

`head` is the HEAD seen when the ledger was last written, so it is the parent of the commit that carries it. `state.py check` accepts `head == HEAD`, or `head == HEAD^` when HEAD touches the project.

## 9. Commit grammar

A commit that touches any path under `docs/` or `.pipeline/` must have the message:

```
<slug>/<step> <VERB>[ a<n>][ <review-id>]: <one line, at most 72 characters>
```

Verbs: `PASS`, `REJECT`, `HUMAN`, `INTAKE`, `REVIEW`, `IMPORT`, `APPLY`, `WAIVE`, `LOOP`, `REWIND`, `STALE`, `SPLIT`, `EXPORT`, `REJECT-LOG`, `INIT`.

Slug is the project directory name: lowercase letters, digits, hyphens, and underscores, starting with a letter or digit. `rp doc init` refuses any other slug, and a refused message prints which part failed and a corrected example.

Step is a step id from `STEPS.md`, or `-` for commits not tied to a step (`SPLIT`, `EXPORT`, `INIT`, `REJECT-LOG`, `STALE`).

Design and ledger commits go through `rp commit "<message>"`, which runs every check below, writes the ledger the message implies, stages `docs/` and `.pipeline/`, and commits. The hooks are the guard: `pre-commit` fixes links, bumps versions, rebuilds the index, and blocks on hard failures; `commit-msg` checks grammar, ownership, and route, then refuses a raw `git commit` whose staged `state.yaml` differs from what the message implies and prints the `rp commit` line to run. Git snapshots the index after `pre-commit`, so a hook cannot write a message-dependent ledger into the same commit; that is why the wrapper exists.

Rules enforced:

1. Message matches the grammar when `docs/` or `.pipeline/` is touched. Commits that touch only `src/`, `scripts/`, `runs/`, or `README.md` are free-form and never blocked.
2. `PASS` and `REJECT` may change only the sections owned by `<step>` in the template. A parent section does not count as changed when only its children changed.
3. Every commit runs the ref-checker on affected projects; hard failures block the commit. Link paths, link texts, and anchors of renamed objects are fixed and staged automatically.
4. Changed `docs/` files get their version bumped and staged automatically, unless only stub blocks changed.
5. `HUMAN` commits while a review is pending or stale may change only sections owned by the review's `route_to` step or steps after it in the stage.
6. One project per commit.
7. Never amend, rebase, force-push, or reset history under `work/`.

## 10. Review object

`pipeline/reviews/<step>-r<n>.md` or `ext-r<n>.md`. YAML frontmatter then prose, append-only.

```yaml
id: 2f-r1
kind: gate                  # gate | intake | external
step: 2f
origin: internal            # internal | external
external_source: null
doc_version: {commit: c3d4e5f, files: {DESIGN.md: 4, model.md: 3}}
sections_judged: {§model.assumptions: 41cc, §model.derivation: 8a2b}
authors: [idea-reviewer, chenyu0516]
verdict: revise             # accept | revise | abandon ; null while draft
route_to: 2c                # null on accept
status: draft               # draft | pending | applied | waived | superseded | stale
applied_version: null
items:
  - id: I1
    object: A3              # object id, or a section id, or null
    section: §model.assumptions
    source: idea-reviewer   # agent, git user, or coworker name
    finding: "..."
    proposal: "..."
    disposition: accept     # accept | counter | decline | defer
    required: "..."         # empty on decline and defer
    logged: null            # R<n> when countered or declined
    status: open            # open | addressed | waived
    addressed_at: null
    quote: null             # verify mode: the new text that satisfies `required`
```

Intake reviews use `kind: intake`, `input: seed.md`, `input_hash`, and items with `severity` (framing, structural, detail), `choice`, `why_it_matters`, `options`, `answer`.

Rules: a git user must be in `authors` before commit; `verdict` and `route_to` are required unless status is draft; `decline` requires `required` empty and a reason in prose starting "finding invalid because"; `counter` requires `required` non-empty and writes the proposal to the rejection log; one review pending per project, others queue in creation order; `applied` requires every item `addressed` or `waived` with `quote` on addressed items.

## 11. Rejection log line

```
R17 | 2026-10-02 | 2f-r1 | A3 "volatility persistence" | proposal: <one line> | <rejected|countered|declined>: <reason> | by: chenyu0516 [| promoted]
```

Fourth field is an object id with name, or a section id. `revived` entries get ` | revived: <reason>` appended; nothing is deleted.

## 12. Taxonomy templates

`stages/templates/<name>.yaml` defines the sections in order with owners and object kinds, the kind table, and which sections each step outputs. `doc.py init --template <name>` instantiates it. Available: `quant-model`, `tooling`, `ml-model`, `empirical-study`.

## 13. Commands

All run as `rp <tool> ...` from anywhere once `<agent_pipeline>/bin` is on `PATH`, or as `uv run --project <agent_pipeline> python <agent_pipeline>/scripts/<tool>.py ...`. `<project>` is a path; use `.` inside a project.

| tool | what it does |
|---|---|
| `doc.py init <slug> --template <name> [--at DIR]` | create `DIR/<slug>/` as a new git repository with hooks enabled, from a taxonomy template, with input files from `stages/intake/` |
| `doc.py get/put/append <project> <§id>` | read or replace one section; `put` bumps the file version |
| `doc.py resolve <project> <id\|name\|file#anchor>` | the object card: id, name, kind, tag, file, version, section, hash, linked from, text |
| `doc.py split/merge <project> <§id>` | move a section to its own file and back; links are rewritten |
| `doc.py export <project>` | single file with stubs inlined and the registry appended |
| `doc.py index/budget/version/relink <project>` | rebuild INDEX and REGISTRY; budget report; version block; fix links |
| `ref_checker.py <project> [--fix-links] [--mark-stale]` | every hard rule and warning in section 6; staleness with `--mark-stale` |
| `state.py show/check/step/rebuild <project>` | ledger index; `step <id> done --inputs ...` records built_from and built_objects |
| `review.py new/commit/disposition/verify/apply/waive/reply` | the review lifecycle |
| `review.py log add/show/promote/revive` | the rejection log |
| `commit.py "<message>" [--all]` | the one way to commit design or ledger changes; `rp commit` |
| `scripts/selftest.sh` | runs a fake project through every mechanism in a temporary repo |

## 14. Intake templates

`stages/intake/<input>.md` is the base structural template the `intake-initializer` specializes for a project. Slots are `[fill: <what goes here and why the generator needs it>]`. The filled file is the input itself; answers to intake review items go under `## Decisions` as `- Q1: <answer> (answered|delegate)`.
