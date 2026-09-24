# Implementation notes

Reference and verification map for the tools. The runbook is `README.md`; the design is `PROPOSAL-subworkflows.md`; the exact rules the scripts enforce are `stages/REFS.md`. This file lists every function the build must perform, phase by phase, in Given-When-Then form, with the standard that proves it and the check that exists today. A function whose check says `none` is not done, whatever the code looks like.

## 1. Brief goal and how to read this file

Brief goal, from the proposal: one design document per research project, a git ledger that records how it evolved, and a human at every decision. The tools make it impossible to commit a document or ledger that breaks the rules.

Three standing decisions shape the plan below. Every project starts from the same universal core, not from a chosen template; the requirements of a project are not settled at the start, so sections are added as they settle. An agent helps the human draft each input until it is good enough, and that agent is the first thing phase 2 builds. An update agent revises requirements mid-project and is planned now but built last, so the build stays small.

Each function below is one row. **Given** is the state before, **When** is the action, **Then** is the observable outcome. The standard is what proves the row done. The check column says where that proof lives:

| check | meaning |
|---|---|
| `selftest N` | step N of `rp selftest` runs it; a nonzero exit fails the whole run, and where the row says so the output is also matched |
| `manual` | the README runbook drives it on a real project and a human judges the result |
| `none` | no check exists; the function is unverified |

To verify a phase, run `rp selftest`, then do every `manual` row in the runbook, then treat every `none` row as open work.

## 2. Layout of this repository

```
agent/                                  # tool repository, GitHub chenyu0516/agent_pipeline
  README.md                             # runbook
  IMPLEMENTATION.md                     # this file
  PROPOSAL-subworkflows.md              # accepted design and decision register
  CLAUDE.md                             # rules every agent inherits
  REJECTED-global.md                    # curated cross-project rejection log; created by `rp review log promote`
  pyproject.toml  uv.lock  .gitignore   # uv project; .venv and work/ are ignored
  bin/rp                                # the entry point shim
  .claude/
    agents/doc-hygiene-reviewer.md      # the one built agent; others land in phases 2 to 4
    skills/                             # orchestrators, phase 2
  stages/
    REFS.md                             # normative grammar
    templates/                          # quant-model, ml-model, empirical-study, tooling
    intake/                             # seed.md scribble.md data.md questions.md base templates
    01-read/ … 05-verdict/              # STEPS.md and CONTRACT.md per stage
  scripts/
    cli.py                              # `rp` dispatcher
    pipelib.py                          # library: parse the document tree, index, resolve, split, export, ledger, git
    doc.py                              # the document tree tool
    ref_checker.py                      # every hard rule and warning; staleness marking
    state.py                            # ledger: show, check, step, stage, rebuild, head
    review.py                           # review lifecycle and rejection log
    commit.py                           # the one way to commit design or ledger changes
    hooks.py                            # logic behind a project's three git hooks
    selftest.sh                         # fake projects through every mechanism; strict mode, stops at the first failure
  benchmarks/0N-*/                      # 3 to 5 real input/accepted-output pairs per stage; empty so far
```

## 3. Layout of a project

`rp doc init <slug> --template <name> --at <parent dir>` creates `<parent dir>/<slug>` as a new git repository with hooks enabled. The pipeline governs `docs/` and `.pipeline/`. Everything else commits with plain git and any message.

```
<slug>/                                 # its own git repository; slug: lowercase, digits, hyphens, underscores
  README.md                             # short entry point written at init; edit freely
  docs/
    DESIGN.md                           # root of the design tree, always present
    model.md  model/derivation.md       # split-out sections, created by `rp doc split`
    REGISTRY.md                         # generated object index; never edit
    REJECTED.md                         # project rejection log, append-only
    DEFERRED.md                         # deferred review items
    inputs/                             # seed.md scribble.md data.md questions.md, each ending with ## Decisions
    reviews/                            # 2a-in1.md 2f-r1.md ext-r1.md; append-only
    reviews/external/                   # coworker originals
    export/<slug>-full.md               # single-file export with stubs inlined and registry appended
  src/  scripts/  runs/<id>/            # code, experiment scripts, runs; plain git
  .githooks/                            # pre-commit, commit-msg, post-commit wrappers written at init
  .pipeline/
    state.yaml                          # ledger index
    INDEX.yaml                          # sections, objects, versions; rebuilt by every tool run
    template.yaml                       # copy of the taxonomy template, so the project is self-contained
    attempts/<step>-a<n>.md             # rejected attempts
    tool_root                           # absolute path of this tool repository; gitignored
```

Sections, objects, and stubs are markdown headings followed by an HTML comment. The grammar for each marker, the Context rule, anchors, and the prose rules are REFS sections 2 to 6. Ledger fields are REFS section 8, the review schema section 10, the log line section 11. Section ids may be written with or without `§`; intake step ids may be written `2a-in`.

## 4. Phase 1 functions: the tools

Built and self-tested. Every row here is what `rp selftest` proves, or does not.

### 4.1 Project creation, `rp doc init`

| function | given, when, then | standard | check |
|---|---|---|---|
| create a project | Given a slug in grammar. When init runs with `--at DIR` and no `--template`. Then `DIR/<slug>` is a git repository with hooks enabled, `DESIGN.md` holds every universal core section as pending, the input files exist, and `state.yaml` and the template copy are written. | `rp check` prints `0 hard` on the new project | selftest 17; selftest 1 with the quant-model preset |
| refuse a bad slug | Given a slug with uppercase or other characters outside the grammar. When init runs. Then nothing is created and the message names the nearest valid slug. | init exits nonzero; no directory | selftest 1 |

### 4.2 Document tree, `rp doc`

| function | given, when, then | standard | check |
|---|---|---|---|
| get | Given a section id, with or without `§`. When get runs. Then the section prints with its heading and comment. | output starts at the heading | selftest 11 |
| put | Given a file holding a section with its comment intact. When put runs. Then the section is replaced and the file version bumps by one. | `now vN` printed with N one higher | selftest 3, 5, 7 |
| append | Given a `§status` line. When append runs. Then the line is added without a version bump. | version unchanged | selftest 11, via apply |
| resolve | Given an object id, a name in quotes, a section id, or `file#anchor`. When resolve runs. Then the same card prints for each: id, name, kind, tag, file, section, hash, links to it, text. | card by id, by name, and by anchor agree | selftest 12 |
| split | Given a section with children. When split runs. Then a new file holds the section under an H1 `<title>: <section>`, a stub stays behind, every link path is rewritten, and the index rebuilds. | `rp check` prints `0 hard` after the split | selftest 12 |
| merge | Given a split-out file. When merge runs. Then the section returns to its host and the stub disappears. | `rp check` prints `0 hard` after the merge | none |
| export | Given a tree with stubs. When export runs. Then one file holds every section inlined and a generated registry. | export contains `## Registry` and no `stub:` marker | selftest 14 |
| index | Given any tree. When index runs. Then `INDEX.yaml` and `REGISTRY.md` match the files. | counts printed | selftest 6, 15 |
| version | Given any tree. When version runs. Then every file and its version print. | matches `state.yaml` versions | selftest 8 |
| budget | Given a file over the template's line budget. When budget runs. Then the file and the split trigger are named. | a report line per file over budget | none |
| relink | Given links whose paths went stale. When relink runs. Then paths are rewritten. | `rp check` reports no unresolved link | none, see fix-links below |
| bump | Given a file as a docs-relative key, a project-relative path, or an absolute path. When bump runs. Then its version rises by one; an unknown file is refused with the known files listed. | printed version; nonzero exit on an unknown file | selftest 17 |

### 4.3 Reference checker, `rp check`

| function | given, when, then | standard | check |
|---|---|---|---|
| clean tree passes | Given sections with symbols, assumptions, results, and links. When check runs. Then it prints `0 hard`. | exit 0 | selftest 1, 5, 12 |
| scope | The checker enforces only the deterministic rules in REFS section 6 and the line budget. Sentence length, paragraph length, hedging and filler words, bold count, and the skim rule stay with `doc-hygiene-reviewer` by decision. | no prose-style rule in the checker | by inspection |
| bare id is hard | Given prose containing `A1`. When check runs. Then a `HARD` line quotes it. | exit 1 with `--quiet` | selftest 6 |
| banned phrase is hard | Given prose containing `previously`. When check runs. Then a `HARD` line quotes it. | exit 1 | selftest 6 |
| rejected span is hard | Given a section reusing six words of a logged proposal. When check runs. Then a `HARD` line names the log entry. | exit 1 | selftest 15 |
| stub summary is a warning | Given a stub with `[summary pending]`. When check runs. Then a `WARN` line names it and the exit stays 0. | `0 hard, 1 warnings` | selftest 12 |
| fix links | Given a rename of an object heading. When a design commit runs. Then link anchors and link texts to it are rewritten and staged in the same commit. | grep finds the new name in both files | selftest 13 |
| mark stale | Given a done step and a hand edit to one of its inputs. When a design commit runs. Then the step is marked stale with the changed section as reason. | `rp state show` prints `status: stale` | selftest 8 |
| mark review stale | Given a pending review and a PASS by a step outside its route that changes a judged section. When the commit runs. Then the review status becomes stale. | `status: stale` in the review frontmatter | none |
| json output | Given `--json`. When check runs. Then the report is machine readable. | parses as JSON | none |

### 4.4 Ledger, `rp state`

| function | given, when, then | standard | check |
|---|---|---|---|
| show | Given a project. When show runs. Then `state.yaml` prints. | step records visible | selftest 8 |
| check, clean | Given a committed project. When check runs. Then it prints `consistent`. | exit 0 | selftest 2, 16, 17 |
| check, root commit | Given INIT as the first commit of the repository. When check runs. Then the `0000000` placeholder head is accepted. | `consistent` | selftest 17 |
| check, drift | Given a hand edit under `docs/` or a wrong head. When check runs. Then the problem is named and the exit is nonzero. | message names the file or hash | none |
| step done | Given the sections and input files a step read. When step done runs before the PASS commit. Then `built_from` holds their hashes plus the hashes of every linked object. | record present in the PASS commit | selftest 3, 5, 7 |
| stage | Given a stage name. When stage runs. Then `state.yaml` records it. | field updated | none |
| rebuild | Given a ledger commit history. When rebuild runs. Then steps, reviews, and head are reconstructed from the log. | counts match the log | selftest 16, 17 |
| head | Given a project. When head runs. Then the current HEAD is recorded. | field updated | none |

### 4.5 Reviews, `rp review`

| function | given, when, then | standard | check |
|---|---|---|---|
| new, gate | Given a step. When new runs. Then a draft is bound to the commit, file versions, and the hash of every section in the stage. | draft path printed; frontmatter complete | selftest 9 |
| new, intake | Given `--kind intake --input seed.md`. When new runs. Then the draft carries an id `<step>-in<n>` and item slots for questions. | draft exists | selftest 4 |
| new, external | Given `--kind external --source FILE --from "Name"`. When new runs. Then the draft records the source; items are still written by hand. | draft exists | none |
| validate | Given a draft with a missing field. When validate runs. Then the field is named. | nonzero exit | none |
| commit, intake | Given answered items. When commit runs. Then answers land under `## Decisions` in the input file and the commit uses the INTAKE verb. | `tail` of the input shows the answers | selftest 4 |
| commit, gate | Given a verdict, a route, and items with dispositions. When commit runs. Then the git user joins the authors, countered and declined proposals are appended to `REJECTED.md`, status becomes pending, and the commit uses REVIEW. | `R1` line in the log names the countered proposal | selftest 9 |
| disposition | Given an item id and a disposition. When disposition runs. Then the item is updated with `required` and `why`. | field updated | none, the self-test edits YAML directly |
| verify | Given the routed step has rerun. When verify runs with `--set I1 addressed "quote"`. Then each judged section prints changed or unchanged and the quote is recorded. | `changed` on the rerun section only | selftest 11 |
| apply | Given every blocking item addressed or waived. When apply runs. Then `applied_version` is set, a `§status` line names both commits and the objects, and the commit uses APPLY. | `§status` last line names the review | selftest 11 |
| waive | Given a pending review. When waive runs with `--why`. Then status becomes waived and the route is lifted. | later HUMAN edit off route succeeds | none |
| reply | Given a review from a coworker. When reply runs. Then a note prints using object names only. | no bare id in the output | none |
| progress cap | Given two agent-drafted reviews in a row with no human review between. When a third is drafted. Then it is refused. | nonzero exit | none, not implemented |
| no-progress flag | Given a review whose items repeat a prior review's items on unchanged objects. When commit runs. Then the review is flagged for confirmation. | flag in frontmatter | none, not implemented |

### 4.6 Rejection log, `rp review log`

| function | given, when, then | standard | check |
|---|---|---|---|
| add | Given a target, a proposal, and a reason. When add runs. Then one line is appended with the next `R<n>` id. | line printed by show | selftest 15 |
| show | Given `--section` or `--global`. When show runs. Then matching lines print, project and global together with `--global`. | both tiers listed | selftest 15 |
| promote | Given a project entry. When promote runs. Then it is copied to the global log with `promoted: from <slug>`. | line in the global log | selftest 15, against a temporary global log |
| revive | Given a logged entry. When revive runs. Then the line gains `revived:` with the reason, and the span check stops blocking it. | `rp check` passes on the revived proposal | selftest 15 revives; the pass after revival is not asserted |

### 4.7 Commit and hooks, `rp commit`

| function | given, when, then | standard | check |
|---|---|---|---|
| code commits are free | Given only `src/`, `scripts/`, `runs/`, or the README staged. When git commit runs with any message. Then it passes. | commit exists | selftest 2 |
| grammar required | Given `docs/` staged. When git commit runs with a free-form message. Then commit-msg refuses and prints the grammar. | nonzero exit | selftest 2 |
| grammar diagnosis | Given a message with a bad slug, a missing colon, or a lowercase verb. When commit runs. Then each fault is named on its own line and a corrected example prints. | output names the slug, the colon, and the verb | selftest 2 |
| ledger must match | Given `docs/` staged and a message in grammar. When raw git commit runs without the implied ledger. Then commit-msg refuses and prints the `rp commit` line. | nonzero exit | selftest 2 |
| rp commit writes the ledger | Given the same state. When `rp commit` runs. Then links are fixed, versions bumped, the index rebuilt, `state.yaml` updated, and one commit made. | `rp state check` prints `consistent` | selftest 2, 16, 17 |
| ownership | Given a PASS by a step that does not own the changed section. When commit runs. Then it is refused naming the section and the owner's sections. | nonzero exit | selftest 3 |
| route | Given a pending review routed to 2c and a HUMAN edit to `§problem`. When commit runs. Then it is refused naming the allowed sections. | nonzero exit | selftest 10 |
| pre-commit blocks hard failures | Given a hard failure in `docs/`. When any commit runs. Then pre-commit refuses. | nonzero exit | selftest 6 and 15 exercise the checker; the hook path itself is not asserted |
| post-commit report | Given any design commit. When it lands. Then the commit, the pending review, and stale steps print. | text present | none, runs unasserted |
| verbs without ledger effect | Given LOOP, REWIND, STALE, IMPORT, or EXPORT. When commit runs. Then the message is accepted and only stale marks and head are written. | commit exists | none; LOOP and REWIND effects are phase 4 |

### 4.8 Templates

| function | given, when, then | standard | check |
|---|---|---|---|
| universal | Given no `--template`. When init runs. Then the core sections in section 10 exist with their kinds, owners, and steps. | init, INIT commit, `rp state check` consistent | selftest 17 |
| quant-model preset | Given `--template quant-model`. When a project is driven through stage 2 mechanics. Then every section, kind, owner, and step resolves. | full self-test | selftest 1 to 16 |
| ml-model, empirical-study, tooling presets | Same, optional starts. | init, one PASS, one review | none |
| add a section after init | Given a project whose requirements have settled further. When the human edits `.pipeline/template.yaml` and inserts the pending heading in `DESIGN.md` in one commit. Then the checker accepts the new section and its owner. | `rp check` prints `0 hard`; a PASS by the owner succeeds | none; manual until `rp doc add-section` exists, see section 8 |

### 4.9 Agents

| function | given, when, then | standard | check |
|---|---|---|---|
| doc-hygiene-reviewer | Given an absolute project path, a section id, and a stage. When the agent runs from this repository. Then it prints the fixed report: verdict, hard failures with line and quote, seven soft scores, top three fixes, and never edits. | catches a planted violation; a human agrees with each finding | manual, README step 4; passed on the first real project on 2026-09-24 |

## 5. Phase 2 functions: ideate

Not built. The check column is the check that will prove each row; all are `none` today. The intake drafter comes first, because every later step consumes an input it helped write.

| function | given, when, then | standard | check |
|---|---|---|---|
| `intake-drafter` | Given an input file with empty or thin headings and a human in the conversation. When it runs. Then it asks one question at a time, writes the human's answers under the right heading in the human's words, never invents a fact, a number, or a preference, and stops when the input is good enough. | good enough: every heading outside `## Decisions` has content, no `[fill: ...]` marker remains, and `intake-reviewer` finds no open framing item | none; first check is `seed.md` of the first real project |
| `/ideate <slug>` | Given a project with `seed.md` filled. When the skill runs. Then it issues exactly the runbook commands step by step, stops at every ⏸ and ⌂ gate, and never edits a section it does not own. | git log of the run equals the runbook sequence | none; benchmark project through stage 2 |
| `intake-initializer` | Given a base input template and the project's current sections. When it runs once. Then the input file carries prompts specialized to them. Folded into `intake-drafter` if the two prove to be one job. | file ends with `## Decisions` | none |
| `intake-reviewer` | Given a filled input. When it runs. Then a draft intake review lists framing, structural, and detail items, each with options. | no open framing item after the human answers | none |
| `idea-drafter` at 2a | Given `seed.md` with decisions and the rejection log. When it runs. Then `§problem` is written with `Choices made` listing only delegated choices. | hygiene PASS; `plan-reviewer` draft; human accepts | none; 3 benchmark seeds |
| `idea-drafter` at 2c | Given `§problem`, `§position`, `scribble.md` with decisions. When it runs. Then notation, named and tagged assumptions, and the formal model are written with a scribble diff appendix. | hygiene PASS; every assumption tagged | none; 3 benchmark seeds |
| `idea-drafter` at 2e | Given assumptions and derivation. When it runs. Then every own assumption has a prediction or `untestable, accepted`, every result has a prediction, no empirical numbers. | `rp check` plus the 2e pass rule | none |
| `deriver` at 2d | Given notation, assumptions, formal model, resolver cards. When it runs. Then every derivation step links the assumptions it uses and adds none. | `math-checker` PASS | none |
| `math-checker` | Given `§model.derivation`. When it runs. Then an unlisted assumption produces a draft review routed to 2c. | routed review exists on a seeded violation | none |
| `plan-reviewer` | Given a section at a ⏸ gate. When it runs. Then a draft review with items anchored to object names, no verdict. | human sets verdict; draft validates | none |
| `idea-reviewer` at 2f | Given `§problem` through `§model.predictions` and the log. When it runs. Then an adversarial draft review, no verdict. | items cite objects by name | none |
| `doc-keeper` at 2g | Given all sections. When it runs. Then `§context`, `§status`, stubs, and the export are current and within budget. | `rp doc budget` clean; export regenerated | none |
| `/review`, `/reject` | Given a review file or a proposal. When the skill runs. Then it drives `rp review` and `rp review log` and nothing else. | commands match the runbook | none |
| 2b `§position` | Owner is `wiki-searcher`, a phase 3 agent. Until then 2b is written by hand. | hygiene PASS | manual |
| progress cap and no-progress flag | See 4.5. Required before two agent reviewers can run back to back. | refused third draft | none |

Exit criterion for phase 2: the first real project passes 2g with every gate review in `docs/reviews/`, and `rp state check` prints `consistent` at the end.

## 6. Phase 3 functions: read

| function | given, when, then | standard | check |
|---|---|---|---|
| wiki note template | Given a paper. When `rp doc init` runs with the note template. Then sections `§claim`, `§setup`, `§method`, `§results`, `§relevance`, `§hooks` exist. | `rp check` prints `0 hard` | none |
| `/read <pdf-or-arxiv-id>` | Given a pdf and `questions.md`. When the skill runs. Then steps 1a to 1e run with the gates in STEPS. | five papers read end to end | none |
| `paper-reader` at 1a to 1c | Given the pdf. When it runs. Then every symbol is in the notation table, every equation and number cites section, page, or equation. | hygiene PASS; no number without a cite | none; 5 papers |
| `wiki-searcher` at 1d and 2b | Given the vault on disk. When it runs. Then it cites only notes that exist and may answer "none". | every cited note exists | none |
| `review-converter` | Given a coworker's text. When it runs. Then items in the review schema anchored to object names. | `rp review validate` passes | none |

## 7. Phase 4 functions: design, implement, verdict

| function | given, when, then | standard | check |
|---|---|---|---|
| `experiment-designer` at 3a to 3c | Given predictions, data decisions, notation. When it runs. Then hypotheses link predictions, `§data` stays inside `data.md`, every hypothesis has a metric and a baseline. | pass rules in STEPS 3 | none |
| `leakage-auditor` at 3d | Given `§experiment.procedure`. When it runs. Then every feature is linked and audited; a violation drafts a review to 3c. | seeded leakage is caught | none |
| `implementer` at 4a to 4d | Given the procedure. When it runs. Then skeleton and failing tests, a lookahead test on real data, one passing function per step, and a run under `runs/<id>/` with seeds logged. | all tests green; run entry in `§implementation` | none |
| `results-reporter` at 4e | Given `runs/<id>/`. When it runs. Then every number in `§results` traces to a run file. | `rp check` plus trace rule | none |
| `results-reviewer` at 5a | Given `§results` and the model. When it runs. Then each refuted hypothesis is traced to an assumption or result, with candidate causes and a proposed route, no verdict. | human sets verdict and route | none |
| LOOP and REWIND effects | Given a 5a verdict of revise. When `rp commit` runs with REWIND. Then the sections in the STEPS 5 table are marked stale and nothing is deleted. | `rp state show` matches the table | none |
| tags | Given accept or abandon. When 5b runs. Then `<slug>/confirmed` or `<slug>/abandoned` is tagged and the core claim logged. | tag exists | none |

Exit criterion for phase 4: one idea driven from `seed.md` to a recorded rewind, with the rewind visible in `rp state show`.

## 8. Phase 5 functions: the update agent and maintenance

Built last. The update agent is planned here so that nothing earlier is built in a way that blocks it, and deferred so that phases 2 to 4 stay small.

| function | given, when, then | standard | check |
|---|---|---|---|
| `rp doc add-section` | Given a section id, title, owner, and parent. When it runs. Then the project's template copy gains the section, `DESIGN.md` gains the pending heading in template order, the step's outputs gain the id, and the index rebuilds. | `rp check` prints `0 hard`; the owner's PASS succeeds | none |
| `rp doc drop-section` | Given a section with no objects linked from elsewhere. When it runs. Then it leaves the tree and the template copy, and the ledger records the removal. | `rp check` prints `0 hard`; links to it would have been refused | none |
| `requirements-updater` | Given a human saying what changed about the requirements, mid-project. When it runs. Then it proposes the section additions, removals, and retitles as a draft review, and applies only what the human accepts, through the two commands above. | every step whose inputs changed is marked stale; nothing is deleted from git; the review is in `docs/reviews/` | none; first check is one real requirement change on the first real project |
| update the intake | Given a new or changed section. When the updater runs. Then the affected input file gains the prompts the section needs and the human is asked to fill them with `intake-drafter`. | intake review with no open framing item | none |
| `/review-logs` | Given a week of commits. When it runs. Then REJECT commits, reopened items, countered `Choices made`, and renamed objects are listed. | report matches `git log` | none |
| prune gates | Given gate statistics. When reviewed. Then gates that never changed a verdict are removed from STEPS. | decision recorded in the proposal | none |
| revisit D12 and D24 | Decisions on review depth and the global log. | recorded | none |

## 9. Git hooks

Written into every project at init. Commits that touch nothing under `docs/` or `.pipeline/` pass straight through. The hooks find the tools through `$AGENT_PIPELINE_ROOT`, then the gitignored `.pipeline/tool_root`, then `rp` on `PATH`.

| hook | what it does | refuses when |
|---|---|---|
| `pre-commit` | fix links, run the reference checker, bump versions of files whose sections changed, rebuild the index, stage `docs/` and the index | any hard failure from the reference checker |
| `commit-msg` | parse the message; on failure print each fault and a corrected example; check ownership for `PASS` and `REJECT`, route for `HUMAN` while a review is pending or stale, review id existence; compute the ledger the message implies and compare it to the staged `state.yaml` | message not in grammar; a step changed a section it does not own; a human edit off the review's route; staged ledger differs from the implied one, in which case it prints the `rp commit` line to run |
| `post-commit` | print the commit, the pending review if any, and stale steps | never |

Why a wrapper and not hooks alone: git snapshots the index after `pre-commit` and before `commit-msg`, so a hook that learns the message cannot add the ledger it implies to the same commit. `rp commit` writes the ledger before calling git; `commit-msg` verifies that what is staged matches. `head` in the ledger is the parent of the commit that carries it, or `0000000` when that commit is the root.

## 10. Taxonomy templates

A template is one YAML file in `stages/templates/`. `rp doc init` copies it into the project as `.pipeline/template.yaml`, and every tool reads the copy afterwards, so later template edits do not change existing projects.

| field | meaning |
|---|---|
| `budget` | `lines` per file, and `child_lines` with `child_count` for the child-split trigger |
| `kinds` | id prefix to `{kind, section, tag_required, tests}`; `section` is where objects of that kind must be defined; `tests` lists the prefixes an object may cite in `tests:` |
| `sections` | the tree in order, each `{id, title, owner, children}`; heading level follows depth |
| `inputs` | human input files, each with its intake step and consuming step |
| `steps` | each step's `stage` and `outputs`, the sections it may write |
| `step_order` | the order used for route checks and for the stage a step belongs to |

`universal.yaml` is the default and the core every project starts from: context, problem, position, model with notation, assumptions, statement, reasoning and predictions, data and environment, experiment with hypotheses, procedure and a leakage and risk audit, implementation, results, status. Its ids match the three research presets, so the step tables, the contracts, and `CLAUDE.md` apply unchanged; only its titles are generic. The presets are optional starts. To change a project's sections after init, edit its `.pipeline/template.yaml` and `DESIGN.md` together in one commit; a section in the template copy but absent from the tree is a hard failure; a section in the tree but absent from the template copy is a warning; a section in both passes. Keep `§context` first and `§status` last.

## 11. Where the build deviates from the proposal

| topic | proposal | as built | why |
|---|---|---|---|
| where projects live | `work/<slug>/` inside this repository | each project is its own git repository; this repository holds only tools | git boundary per project; code and docs share one standard repo |
| project layout | `docs/`, `pipeline/`, inputs at the root | `docs/` with `inputs/`, `reviews/`, `export/` inside; `src/`, `scripts/`, `runs/`; machine state in `.pipeline/` | the common research-repo shape; readable docs together, machine state hidden |
| commit enforcement | hooks write the ledger | `rp commit` writes it; hooks verify | git snapshots the index before `commit-msg` runs |
| hook scope | every commit under `work/` | only commits touching `docs/` or `.pipeline/` | code commits stay ordinary git |
| `head` in the ledger | equals HEAD | equals the parent of the commit that carries it | the hash is unknown until the commit exists |
| rejected-span check | ten words, against rejected attempts | six words, against logged proposals only | a retry legitimately keeps most of a rejected attempt's text |
| object name length | two to four words | two to five words | some symbol names needed room |
| split file title | the section heading | `<project title>: <section>` | the H1 and the first section heading would share one anchor |
| step status recording | by the orchestrator | by `rp state step` before the commit and by `rp commit` on `PASS` and `REJECT` | so the ledger is inside the commit it describes |
| intake review id | not specified | `<step>-in<n>` | distinguishes intake from gate reviews |
| template binding | read from this repository | copied into `.pipeline/template.yaml` at init | a project must not change when the tool repository does |
| id typing | `§problem`, `2a·in` | also `problem`, `2a-in` | `§` and `·` are hard to type |
| project start, D15 | per-project template chosen at init | one universal core for every project; presets optional; sections added as requirements settle | requirements are not known at the start; a template forces a guess |
| slug charset | not specified | lowercase letters, digits, hyphens, underscores | underscores are common directory names and are unambiguous in the grammar |

Everything else in the proposal's structure sections 1 to 10 is implemented as written. Sections 11 to 14 of the proposal, the orchestrator and the agents, are phases 2 and later.

## 12. Status

| phase | status | verified | unverified |
|---|---|---|---|
| 0 | done | decisions D1 to D27 | |
| 1 | built | every `selftest` row in section 4 | every `none` row in section 4: merge, budget, relink, bump, review external kind, validate, disposition, waive, reply, progress cap, three presets, hook output |
| 2 | next | | section 5, starting with `intake-drafter` |
| 3 | | | section 6 |
| 4 | | | section 7 |
| 5 | last | | section 8, the update agent and `rp doc add-section` |

Known gaps beyond the tables. The `CONTRACT.md` files still use bare ids in their examples and predate the object rules; each is rewritten with its stage's agents. No orchestrator exists, so the README runbook is the operating procedure. Export is markdown only. The benchmarks directory is empty. Stage 1 wiki notes have no template yet.
