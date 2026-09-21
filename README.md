# agent_pipeline

A checkpointed research pipeline: read papers, turn rough ideas into models, test them in Python, decide what to do with the result. Each research project is one design document in its own git repository, with a ledger behind it and a human at every decision. This repository holds the tools. This file tells you how to run them.

Today the tools, the document format, the reviews, the ledger, and the git hooks work. The agents that will write sections for you do not exist yet, so in this runbook you write sections yourself, or paste what Claude Code drafts in an ordinary chat. The commands stay the same when the agents arrive.

Other files: `PROPOSAL-subworkflows.md` is why the pipeline is shaped this way. `stages/REFS.md` is the exact grammar the tools enforce. `IMPLEMENTATION.md` is the reference for layouts, tools, hooks, templates, and where the build deviates from the proposal.

## 1. Install, once

```
cd ~/Documents/agent
uv sync
echo 'export PATH="$HOME/Documents/agent/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
rp where
```

`rp where` prints `/Users/chen-yu/Documents/agent`. If it prints "command not found", the PATH line did not take; open a new terminal. Needs Python 3.11 or newer, `uv`, and git.

Prove everything works:

```
rp selftest
```

The last line must be `ALL STEPS RAN in /var/folders/.../vol-regime`. It builds a throwaway project in a temporary directory and runs every mechanism below. Two lines starting with `error:` are expected; they are refusals the test checks for.

## 2. Create a project

Pick a slug: lowercase, hyphens, no spaces. Pick a template: `quant-model` for a mathematical model tested on data, `tooling` for a software project such as the wiki skills, `ml-model`, or `empirical-study`.

```
rp doc init wiki-skills --template tooling --title "Obsidian wiki skills" --at ~/research
cd ~/research/wiki-skills
rp commit --all "wiki-skills/- INIT: project created"
```

You now have a git repository with hooks enabled, a `docs/DESIGN.md` holding every section as a pending placeholder, input files under `docs/inputs/`, and a ledger under `.pipeline/`. The `INIT` commit is the first ledger commit. Look around:

```
cat docs/DESIGN.md
rp state show .
git log --oneline
```

Rule for the whole project: anything under `docs/` or `.pipeline/` is committed with `rp commit` and a message in the form `<slug>/<step> <VERB>: <one line>`. Anything else, code in `src/`, experiment scripts in `scripts/`, outputs in `runs/`, the README, is ordinary git with any message.

## 3. Fill in your seed and pass intake

Open `docs/inputs/seed.md`. It is a template with `[fill: ...]` slots: observed, unknown, goal, target quantity, horizon, data, out of scope. Replace each slot with your own words. Rough is fine; that is what intake is for.

Then record the intake review. The intake reviewer agent will draft the questions in phase 2; today you draft them yourself, which is still useful because it forces the open choices into the open:

```
rp review new . --step 2a-in --kind intake --input seed.md
```

This writes `docs/reviews/2a-in1.md`. Open it. The frontmatter has one placeholder item. For each choice your seed leaves open, add an item with a `severity` of `framing`, `structural`, or `detail`, the `choice` as a question, `why_it_matters`, `options`, and your `answer`. A framing item must have a real answer. A structural or detail item may have the answer `delegate`, which means the writer of the next section decides and must say so. Then:

```
rp review commit docs/reviews/2a-in1.md
```

Your answers are appended under `## Decisions` in `docs/inputs/seed.md` and committed as `wiki-skills/2a·in INTAKE 2a-in1`. If the commit is refused with "framing item must be answered by you", answer it.

## 4. Write a section

Every section has an owner step. For the `tooling` template the first ones are `problem` (step 2a), `position` (2b), then `design.terms`, `design.requirements`, `design.components` (2c). For `quant-model` they are `problem`, `position`, then `model.notation`, `model.assumptions`, `model.formal`. The full list is in `.pipeline/template.yaml`.

Get the current section into a scratch file, write it, put it back:

```
rp doc get . problem > /tmp/problem.md
$EDITOR /tmp/problem.md
rp doc put . problem --from /tmp/problem.md
rp check .
```

Keep the first two lines of the scratch file as they are: the heading and the `<!-- section: §problem | owner: 2a -->` comment. Write the body below them. If you delegated any choice at intake, end the section with a `**Choices made.**` paragraph naming the choice, what you picked, and one line why.

`rp check .` prints `0 hard, 0 warnings` when the section is acceptable. Hard failures are things like a banned phrase ("previously", "updated to"), an object id such as `A1` in prose, or a link that does not resolve. Fix and rerun until it is clean.

Then record what the section was built from and commit it as a `PASS` by its owner step:

```
rp state step . 2a done --inputs seed.md
rp commit --all "wiki-skills/2a PASS a1: problem framed"
```

The order matters: `rp state step` before `rp commit`, so the ledger rides inside the commit. `a1` means first attempt. The commit is refused if the message names a step that does not own the changed section, for example `2b` for `problem`.

Sections that define objects work the same way, with one more rule. An assumption, symbol, requirement, component, or any other object is a heading with a comment on the next line:

```markdown
#### Vault is plain markdown
<!-- object: Q1 | kind: requirement | tag: own -->
Every note is a UTF-8 markdown file with YAML frontmatter; no database.
```

The heading is the object's name. Elsewhere in the document, refer to it by name as a link, `[vault is plain markdown](#vault-is-plain-markdown)`, never as `Q1`. To see what an id or name points to:

```
rp doc resolve . Q1
rp doc resolve . "vault is plain markdown"
```

Which kinds exist, their prefixes, and which section defines them is in `.pipeline/template.yaml` under `kinds`. Assumptions and requirements need a `tag`: `lit`, `standard`, or `own`.

## 5. Hold a review

Some steps are human gates: `2a`, `2c`, and `2f` in stage 2. At a gate you draft a review, finish it, commit it, and if it asks for changes, the pipeline routes back to one step until every item is applied. The reviewer agents will draft in phase 2; today you write the draft.

```
rp review new . --step 2f --by idea-reviewer
$EDITOR docs/reviews/2f-r1.md
```

In the frontmatter: set `verdict` to `accept`, `revise`, or `abandon`; on `revise` set `route_to` to the step that must rerun, for example `2c`. Each item has a `finding`, the reviewer's `proposal`, your `disposition` (`accept`, `counter`, `decline`, `defer`), and the `required` change. On `counter` you keep the finding and write your own `required`; the proposal goes to the rejection log automatically. On `decline` you must write "finding invalid because ..." in the prose below the frontmatter. Then:

```
rp review commit docs/reviews/2f-r1.md
```

An `accept` is applied at once. A `revise` becomes pending. While a review is pending, only the routed step and the steps after it may change, and a `HUMAN` commit elsewhere is refused with "Waive the review first". Rerun the routed step as in section 4, then everything downstream of it. When done, record that each item is addressed with a quote of the new text, and apply:

```
rp review verify docs/reviews/2f-r1.md --set I1 addressed "the text that now satisfies it"
rp review apply docs/reviews/2f-r1.md
```

`apply` writes one line to the `§status` section of the document, commits `APPLY 2f-r1`, and unblocks the pipeline. See the trail with `git log --oneline` and `rp doc get . status`.

## 6. Edit by hand

You may edit any section directly. Commit it as a `HUMAN` change by its owner step:

```
$EDITOR docs/DESIGN.md
rp commit --all "wiki-skills/2c HUMAN: tightened the plain-markdown requirement"
```

The commit bumps the file version and marks every step that was built from the changed section as stale. `rp state show .` lists stale steps and why. A stale step is regenerated by running it again as in section 4, which clears the mark. If you rename an object's heading, the commit rewrites every link to it.

## 7. Reject an idea so it stays rejected

When you decide against something, log it. Every later writer of that section is handed the log, and a section that reuses six or more consecutive words of a logged proposal is refused.

```
rp review log add . --target "design.components" --proposal "one skill per note type" --why "explodes with note types; one skill per verb instead"
rp commit --all "wiki-skills/- REJECT-LOG: one skill per note type"
rp review log show .
```

A lesson that outlives the project goes to the shared log with `rp review log promote . R1`. To bring a rejected idea back on the record: `rp review log revive . R1 --why "..."`.

## 8. Split a long file, export a single one

When `rp check .` warns that `DESIGN.md` is over budget, move a top-level section into its own file. Links keep working.

```
rp doc split . design
rp commit --all "wiki-skills/- SPLIT: design to design.md"
```

For a collaborator who wants one file, with every split section inlined and an index of all objects appended:

```
rp doc export .
open docs/export/wiki-skills-full.md
```

## 9. Code and experiments

Ordinary git, any message:

```
$EDITOR src/vault.py
git add src && git commit -m "vault reader"
```

Nothing under `docs/` or `.pipeline/` may be in a code commit. If you mix them, the hook refuses and prints the `rp commit` line to run instead.

## 10. Share on GitHub

Push the project repository as it is. The ledger commits are the record of how the idea evolved, and every review stores the commit it judged and the commit that applied it. Two rules follow. Never squash-merge; it rewrites the hashes the reviews point at. If you want a tidy main branch, do the work on a `pipeline` branch and `git merge --no-ff pipeline` into `main` at each stage completion, right after `rp doc export .`.

A coworker who clones the project needs this tool repository too, and one of: the `rp` shim on their PATH, `AGENT_PIPELINE_ROOT` pointing at their clone, or the path written into `.pipeline/tool_root`, which is gitignored and machine-local.

## 11. When something is refused

| you see | it means | do |
|---|---|---|
| `message must be '<slug>/<step> <VERB>...'` | a design or ledger file is staged with a plain commit message | use `rp commit "<slug>/<step> <VERB>: ..."` |
| `PASS by 2b may not change ['§problem']` | the step in the message does not own the section you changed | use the owner step from `.pipeline/template.yaml` |
| `staged .pipeline/state.yaml does not match` | you used raw `git commit` on ledger files | run the `rp commit` line it prints |
| `review 2f-r1 is pending and routes to 2c` | you edited a section outside the route while a review is open | rerun the routed step first, or `rp review waive` with a reason |
| `HARD ... bare object id 'A1' in prose` | an id appears in text instead of a name link | write `[name](#anchor)`; `rp doc resolve . A1` gives both |
| `HARD ... banned phrase 'previously'` | the section narrates its own history | state only the current design; history lives in git and the log |
| `HARD ... reuses a rejected proposal R2` | the text repeats something in `docs/REJECTED.md` | change the proposal, or `rp review log revive . R2 --why ...` |
| `framing item must be answered by you` | an intake question with severity framing has no answer or says delegate | answer it |
| `tree not clean under project` from `rp state check` | uncommitted changes under `docs/` or `.pipeline/` | commit them with `rp commit`, or `git checkout -- docs .pipeline` |

`rp state check .` says `consistent` when the ledger and git agree. If it does not and you cannot see why, `rp state rebuild .` reconstructs the ledger from the git log.

## 12. Command cheat sheet

```
rp doc init <slug> --template <t> --title "..." --at <dir>   new project repository
rp doc get . <section>            print a section          rp doc put . <section> --from FILE   replace it
rp doc resolve . <id|"name">      what an object is         rp doc split . <section>             move to its own file
rp doc export .                   single-file export        rp check .                           run every rule
rp state step . <step> done --inputs <sections and files>   record what a step was built from
rp state show . | check . | rebuild .
rp review new . --step <step> [--kind intake --input seed.md]   draft a review
rp review commit|verify|apply|waive|reply <review file>
rp review log add|show|promote|revive . ...
rp commit --all "<slug>/<step> <VERB>: <one line>"           the only way to commit docs/ and .pipeline/
```

Verbs: `PASS` a step's output, `HUMAN` a hand edit, `REVIEW` `INTAKE` `APPLY` `WAIVE` for reviews, `SPLIT` `EXPORT` `REJECT-LOG` `INIT` with step `-`. Section ids may be typed with or without `§`; intake steps as `2a-in`.
