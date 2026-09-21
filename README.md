# agent_pipeline

A checkpointed research pipeline for quantitative research with Claude Code agents: read papers, turn rough ideas into models, test them in Python, decide what to do with the result. One design document per project, a git ledger behind it, a human at every decision.

This repository holds the tools, the grammar, the templates, and the agent definitions. Each research project is a separate git repository created by these tools. This file is the implementation guide: setup, layout, what each tool and hook does, how to drive a project by hand today, how to share a project, and where the build deviates from the design. It does not restate the design. For that, read `PROPOSAL-subworkflows.md`; for the exact rules the scripts enforce, read `stages/REFS.md`.

Status: design accepted 2026-09-18. Phase 1 built and self-tested. Phase 2 next. First project: the Obsidian wiki-management skills, on the `tooling` template.

## 1. Document map

| file | what it holds | read it for |
|---|---|---|
| `PROPOSAL-subworkflows.md` | the accepted design: problem, mechanisms, taxonomy, objects, intake, reviews, rejection log, ledger, orchestrator, stage tables, gates, agent roster, walkthrough, failure modes, decisions D1–D27, build map, timeline | why anything is the way it is |
| `stages/REFS.md` | the normative grammar: project layout, file format, section and object markers, links, prose rules, versions, ledger fields, commit grammar, review schema, log line, commands | what the scripts check, exactly |
| `stages/0N-*/STEPS.md` | one step table per stage | who does what at each step |
| `stages/0N-*/CONTRACT.md` | per-stage output template, rubric, known failure modes | what an agent must produce; predates the object rules, rewritten per stage in phases 2–4 |
| `CLAUDE.md` | rules every agent inherits | what every agent is told |
| this file | setup, layout, tools, hooks, manual operation, templates, sharing, self-test, deviations, status | how to run it |

## 2. Setup

```
cd ~/Documents/agent                      # this repository
uv sync                                   # creates .venv with PyYAML; once
export PATH="$HOME/Documents/agent/bin:$PATH"   # gives you `rp`; put it in your shell profile
rp selftest                               # optional: proves every mechanism in a temporary project
```

Requirements: Python 3.11 or newer, `uv`, git. Nothing here calls a model; the agents run inside Claude Code and use these tools.

`rp` is a shell shim that runs the tools through this checkout's environment from any directory. Project hooks find the tools the same way, through `$AGENT_PIPELINE_ROOT`, then the gitignored `.pipeline/tool_root` written at project creation, then `rp` on `PATH`. A coworker who clones a project needs this repository too and sets one of those three.

## 3. Layout of this repository

```
agent/                                  # tool repository, GitHub chenyu0516/agent_pipeline
  README.md                             # this file
  PROPOSAL-subworkflows.md              # accepted design and decision register
  CLAUDE.md                             # rules every agent inherits
  REJECTED-global.md                    # curated cross-project rejection log; created by `rp review log promote`
  pyproject.toml  uv.lock  .gitignore   # uv project; .venv and work/ are ignored
  bin/rp                                # the entry point shim
  .claude/
    agents/doc-hygiene-reviewer.md      # the one built agent; others land in phases 2–4
    skills/                             # orchestrators, phase 2
  stages/
    REFS.md                             # normative grammar
    templates/
      quant-model.yaml                  # sections, owners, object kinds, step outputs, inputs
      ml-model.yaml  empirical-study.yaml  tooling.yaml
    intake/
      seed.md  scribble.md  data.md  questions.md   # base structural templates copied into each project
    01-read/      STEPS.md  CONTRACT.md
    02-ideate/    STEPS.md  CONTRACT.md
    03-design/    STEPS.md  CONTRACT.md
    04-implement/ STEPS.md  CONTRACT.md
    05-verdict/   STEPS.md
  scripts/
    cli.py                              # `rp` dispatcher
    pipelib.py                          # library: parse the document tree, index, resolve, split, export, ledger, git
    doc.py                              # the document tree tool
    ref_checker.py                      # every hard rule and warning; staleness marking
    state.py                            # ledger: show, check, step, stage, rebuild, head
    review.py                           # review lifecycle and rejection log
    commit.py                           # the one way to commit design or ledger changes
    hooks.py                            # logic behind a project's three git hooks
    selftest.sh                         # fake project through every mechanism
  benchmarks/0N-*/                      # 3–5 real input/accepted-output pairs per stage; empty so far
```

## 4. Layout of a project

`rp doc init <slug> --template <name> --at <parent dir>` creates `<parent dir>/<slug>` as a new git repository with hooks enabled. The pipeline governs `docs/` and `.pipeline/`. Everything else commits with plain git and any message.

```
<slug>/                                 # its own git repository
  README.md                             # short entry point written at init; edit freely
  docs/
    DESIGN.md                           # root of the design tree, always present
    model.md  model/derivation.md       # split-out sections, created by `rp doc split`
    REGISTRY.md                         # generated object index; never edit
    REJECTED.md                         # project rejection log, append-only
    DEFERRED.md                         # deferred review items
    inputs/
      seed.md  scribble.md  data.md  questions.md   # human inputs, each ending with ## Decisions
    reviews/
      2a-in1.md  2f-r1.md  ext-r1.md    # intake, gate, and external reviews; append-only
      external/                         # coworker originals
    export/<slug>-full.md               # single-file export with stubs inlined and registry appended
  src/                                  # code
  scripts/                              # experiment scripts
  runs/<id>/                            # experiment runs
  .githooks/                            # pre-commit, commit-msg, post-commit wrappers written at init
  .gitignore                            # ignores .pipeline/tool_root, caches
  .pipeline/
    state.yaml                          # ledger index
    INDEX.yaml                          # sections, objects, versions; rebuilt by every tool run
    template.yaml                       # copy of the taxonomy template, so the project is self-contained
    attempts/<step>-a<n>.md             # rejected attempts
    tool_root                           # absolute path of this tool repository; gitignored
```

The commit message slug is the project directory name and must match `state.yaml`.

## 5. What a project looks like on disk

`DESIGN.md` carries every section of the template as a pending placeholder at first. Sections, objects, and stubs are ordinary markdown headings followed by an HTML comment, so any viewer renders the document cleanly and the scripts parse it without a custom format:

```markdown
# Volatility regime filter
<!-- file: DESIGN.md | version: v3 -->

> **Context.** Volatility regime filter is a quant-model project. This file holds every section until one is split out. It depends on nothing yet. Status: ideate.

## Problem
<!-- section: §problem | owner: 2a -->
Daily equity returns show volatility clustering ...

### Assumptions
<!-- section: §model.assumptions | owner: 2c -->

#### Volatility persistence
<!-- object: A2 | kind: assumption | tag: own -->
The autocorrelation of [conditional volatility](#conditional-volatility) at lag one exceeds $0.9$.

### Derivation
<!-- stub: §model.derivation | file: model/derivation.md -->
[summary pending]
See [Derivation](model/derivation.md#derivation).
```

The exact grammar for each marker, the Context rule, anchors, and the prose rules are REFS sections 2 to 6. Ledger fields are REFS section 8, the review schema section 10, the log line section 11.

## 6. The tools

All run as `rp <tool> ...` from anywhere. `<project>` is a path; use `.` inside a project.

**rp doc** is the only thing that should write to `docs/`. `init <slug> --template <name> [--at DIR]` creates a project repository. `get <project> <§id>` prints a section; `put <project> <§id> --from FILE` replaces it and bumps the file version; `append` adds a line without a bump, used for `§status`. `resolve <project> <query>` accepts an object id, a name in quotes, or `file#anchor` and prints the same card for all three: id, name, kind, tag, file and version, section, hash, everything that links to it, current text. `split <project> <§id>` moves a section and its children to a new file whose H1 is `<project title>: <section>`, leaves a stub, rewrites link paths, and rebuilds the index; `merge` reverses it. `export` produces the single file. `index`, `budget`, `version`, `relink`, and `bump` are maintenance.

**rp check** runs every hard rule and warning in REFS section 6 and exits 1 on any hard failure. `--fix-links` rewrites link paths after a split and link anchors and texts after a rename, using the previous `INDEX.yaml` to know which object an old anchor belonged to. `--mark-stale` compares each done step's recorded input hashes to the tree, marks steps stale with a reason, records whether re-verify only is possible, and marks a pending review stale if a judged section changed off-route.

**rp state** manages `.pipeline/state.yaml`. `show` prints it. `check` confirms `docs/` and `.pipeline/` are clean, the recorded head is HEAD or the parent of a HEAD that touches the ledger, the last ledger commit is in grammar, and versions match the tree. `step <project> <step> done --inputs §a §b seed.md` records what a step was built from, as section and input hashes plus the hashes of every object its sections link, and must run before the `PASS` commit so the ledger rides in the same commit. `rebuild` reconstructs step and review status from the git log.

**rp review** is the review lifecycle. `new <project> --step 2f` drafts a review bound to the current commit, file versions, and the hashes of every section in the stage; `--kind intake --input seed.md` and `--kind external --source FILE --from "Name"` are the other kinds. `commit` adds your git user to the authors, validates, writes countered and declined proposals to the rejection log, writes intake answers under `## Decisions` in the input file, sets the status to pending, applied, or queued, and commits with the right verb. `disposition`, `verify`, `apply`, `waive`, `reply` follow the lifecycle in the proposal. `log add|show|promote|revive` is the rejection log; `promote` writes to `REJECTED-global.md` in this repository.

**rp commit "<message>"** is the one way to commit design or ledger changes. It checks the message grammar, section ownership, and review route first, so a refused commit leaves the tree untouched; then fixes links, bumps versions, rebuilds the index, writes the step status and stale marks the message implies into `state.yaml`, stages `docs/` and `.pipeline/`, and commits. `--all` stages everything first. When the staged files touch only `src/`, `scripts/`, `runs/`, or the README, it is a plain commit with any message.

## 7. Git hooks

Written into every project at init and enabled there. Commits that touch nothing under `docs/` or `.pipeline/` pass straight through.

| hook | what it does | refuses when |
|---|---|---|
| `pre-commit` | fix links, run the reference checker, bump versions of files whose sections changed, rebuild the index, stage `docs/` and the index | any hard failure from the reference checker |
| `commit-msg` | parse the message; check grammar, section ownership for `PASS` and `REJECT`, route for `HUMAN` while a review is pending or stale, review id existence; then compute the ledger the message implies and compare it to the staged `state.yaml` | message not in grammar; a step changed a section it does not own; a human edit off the review's route; staged ledger differs from the implied one, in which case it prints the `rp commit` line to run |
| `post-commit` | print the commit, the pending review if any, and stale steps | never |

Why a wrapper and not hooks alone: git snapshots the index after `pre-commit` and before `commit-msg`, so a hook that learns the message cannot add the ledger it implies to the same commit. `rp commit` writes the ledger before calling git; `commit-msg` verifies that what is staged matches. A raw `git commit` still works whenever the staged ledger already matches.

Refusals look like this:

```
commit-msg: docs/ or .pipeline/ is touched, message must be '<slug>/<step> <VERB>[ a<n>][ <review-id>]: <one line>'
commit-msg: PASS by 2b may not change ['§problem'] in DESIGN.md; it owns ['§position']
commit-msg: review 2f-r1 is pending and routes to 2c; HUMAN may change only [...], not ['§problem']. Waive the review first.
HARD  DESIGN.md: bare object id 'A1' in prose: 'By A1 the filter gain is constant.'
HARD  §model.formal: reuses a rejected proposal R2 ('process instead of a state space...')
```

## 8. Driving a project by hand

No orchestrator skill exists yet, so a step is run with the commands below from inside the project. The phase 2 orchestrator will issue exactly these.

```
# create
rp doc init vol-regime --template quant-model --title "Volatility regime filter" --at ~/research
cd ~/research/vol-regime
rp commit --all "vol-regime/- INIT: project created"

# fill an input, then record intake (the intake agents arrive in phase 2; the file format works now)
$EDITOR docs/inputs/seed.md
rp review new . --step 2a·in --kind intake --input seed.md
$EDITOR docs/reviews/2a-in1.md                              # answer every item
rp review commit docs/reviews/2a-in1.md

# run a generator step: write the section, record what it was built from, commit PASS
rp doc get . §problem > /tmp/problem.md
$EDITOR /tmp/problem.md                                     # or an agent writes it
rp doc put . §problem --from /tmp/problem.md
rp check .
rp state step . 2a done --inputs seed.md
rp commit --all "vol-regime/2a PASS a1: problem framed"

# a human gate: draft, edit, commit; on revise, rerun the routed step, then verify and apply
rp review new . --step 2f --by idea-reviewer
$EDITOR docs/reviews/2f-r1.md                               # items, verdict, route_to
rp review commit docs/reviews/2f-r1.md
...                                                         # rerun 2c and downstream with rp commit
rp review verify docs/reviews/2f-r1.md --set I1 addressed "the new text"
rp review apply docs/reviews/2f-r1.md

# a hand edit to a section
$EDITOR docs/DESIGN.md
rp commit --all "vol-regime/2c HUMAN: loosened persistence threshold"

# code is ordinary git
$EDITOR src/filter.py && git add src && git commit -m "kalman filter skeleton"

# split, export, reject
rp doc split . §model
rp commit --all "vol-regime/- SPLIT: model to model.md"
rp doc export .
rp review log add . --target "§model.formal" --proposal "..." --why "..."
rp commit --all "vol-regime/- REJECT-LOG: R2"
```

Rules of thumb. Record `rp state step ... done` before the `PASS` commit, not after. Never edit `INDEX.yaml` or `REGISTRY.md`; every tool rebuilds them. Never edit `state.yaml` by hand; if it is wrong, `rp state rebuild .`.

## 9. Sharing a project on GitHub

The ledger commits are the record of how the idea evolved, and they are what a collaborator's review binds to: every review stores the commit it judged and the commit that applied it, and `§status` prints both. That has one consequence for branching: never squash. A squash merge creates new hashes and orphans every version reference in `docs/reviews/` and `§status`.

The recommended shape:

- Work on a `pipeline` branch. Every `PASS`, `REVIEW`, `APPLY`, `HUMAN`, and `SPLIT` lands there.
- Merge into `main` with `git merge --no-ff pipeline` at stage tags, when the export has just been regenerated. `main` then reads as a sequence of stage completions, and the full ledger is one click away in each merge.
- `rp state check` and `rp state rebuild` read the log of the current branch, so both branches stay consistent.
- If you want a demonstration face with no ledger at all, publish the export file or a rendered site from `main`, and keep the repository itself as the audit trail. Deleting or rewriting the ledger to clean the history would remove exactly what a reviewer would ask for.

## 10. Taxonomy templates

A template is one YAML file in `stages/templates/`. `rp doc init` copies it into the project as `.pipeline/template.yaml`, and every tool reads the copy afterwards, so later template edits do not change existing projects. Fields:

| field | meaning |
|---|---|
| `budget` | `lines` per file, and `child_lines` with `child_count` for the child-split trigger |
| `kinds` | id prefix to `{kind, section, tag_required, tests}`; `section` is where objects of that kind must be defined; `tests` lists the prefixes an object may cite in `tests:` |
| `sections` | the tree in order, each `{id, title, owner, children}`; heading level follows depth |
| `inputs` | human input files, each with its intake step and consuming step |
| `steps` | each step's `stage` and `outputs`, the sections it may write |
| `step_order` | the order used for route checks and for the stage a step belongs to |

To add a template, copy `quant-model.yaml`, rename kinds and sections, keep the step ids so the step tables and hooks still apply, and keep `§context` first and `§status` last. The `tooling` template shows a full renaming: terms, requirements, components, interfaces, acceptance criteria, checks, fixtures, measures.

## 11. The self-test

`rp selftest` creates a fake quant-model project as its own repository in a temporary directory and drives it with the tools from this checkout. It prints `ALL STEPS RAN` on success and exits early on the first mechanism that misbehaves. It covers:

1. init as a git repository with hooks, and a clean reference check;
2. the project boundary: a commit touching only `src/` passes with a free-form message; with `docs/` staged, a free-form message is refused, a raw grammar commit is refused for a missing ledger, and `rp commit` succeeds;
3. a `PASS` by the wrong step is refused on ownership; the right step passes with `built_from` recorded;
4. an intake review writes answers under `## Decisions` and commits with the intake verb;
5. three sections with symbols, assumptions, and links pass every check;
6. a bare id and a banned phrase are hard failures;
7. a derivation with a named result passes;
8. a hand edit to an assumption marks the derivation stale;
9. a gate review is drafted, edited to counter one item, committed as pending, and the countered proposal lands in the rejection log;
10. a hand edit off the review's route is refused;
11. the routed step reruns; verify records quotes; apply writes the status line and commits;
12. a split moves the model to its own file, links are rewritten, the resolver answers by id, by name, and by anchor;
13. a rename by hand has its link anchors and texts rewritten in the same commit;
14. the export inlines the stub and appends the registry;
15. a manual log entry blocks a section that reuses its proposal; promote writes to a temporary global log; revive works;
16. `rp state check` is consistent and `rebuild` reproduces the ledger from the log.

## 12. Where the build deviates from the proposal

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

Everything else in the proposal's structure sections 1 to 10 is implemented as written. Sections 11 to 14 of the proposal, the orchestrator and the agents, are phase 2 and later.

## 13. Status and known gaps

| phase | status | contents |
|---|---|---|
| 0 | done | decisions D1–D27 |
| 1 | done, self-tested | REFS, templates, intake templates, five step tables, `rp` and six tools, per-project hooks, self-test, `CLAUDE.md`, hygiene reviewer |
| 2 | next | `/ideate`, `/review`, `/reject` skills; intake initializer and reviewer, doc keeper, plan reviewer, idea drafter, deriver, math checker, idea reviewer; the wiki-skills project through stage 2 |
| 3 | | review converter, paper reader, wiki searcher, `/read`; five papers |
| 4 | | stages 3 to 5 agents and skills; one idea to a recorded rewind |
| 5 | | `/review-logs`, prune gates, revisit D12 and D24 |

Known gaps. The `CONTRACT.md` files still use bare ids in their examples and predate the object rules; each is rewritten with its stage's agents. No orchestrator exists, so section 8 is the operating procedure. The hygiene reviewer is the only agent and has not yet run against a real project. Export is markdown only. `rp review new --kind external` scaffolds the file, but splitting a coworker's text into items is the phase 3 converter agent. The benchmarks directory is empty. Stage 1 wiki notes use the same machinery but have no template yet; that comes with the paper reader in phase 3.
