# Global rules for every agent in this pipeline

These apply to every stage. `stages/REFS.md` is the normative grammar; `stages/*/STEPS.md` are the step tables; `PROPOSAL-subworkflows.md` is the accepted design and the reasons. Stage contracts add to these rules, never relax them.

## The document is the deliverable

- Each project is its own git repository. Its design document lives under `docs/`, split into files only by `rp doc split`. Code goes in `src/`, experiment scripts in `scripts/`, runs in `runs/`. Every file reads standalone: H1, file declaration, a Context blockquote of at most four sentences, then sections.
- A step writes only the sections it owns. Read `.pipeline/template.yaml` in the project for ownership. Never touch another step's section, even to fix a typo; route a review instead.
- A section states only the current design. Never narrate change inside a section. Banned: previously, originally, we changed, was rejected, instead of the earlier, as before, updated to, formerly, no longer, used to. History lives in git, `§status`, and `docs/REJECTED.md`.
- `Choices made` is the only explanatory block, and it lists only choices delegated at intake: the choice, what was picked, one line why.

## Objects, names, links

- Every assumption, result, prediction, hypothesis, feature, metric, and symbol is an object: a heading with a human name and an object comment on the next line. Names are two to five words, unique in the project, no kind word, no ordinal or digit.
- In prose, refer to an object by its name as a link to its heading, never by its id. `A3` appears only in the object comment, `INDEX.yaml`, `REGISTRY.md`, reviews, logs, and `state.yaml`, and there always as `A3 "volatility persistence"`.
- Before using an object, run `rp doc resolve . <id or name>` and use the name and anchor it prints.
- Assumptions carry a tag: `lit`, `standard`, or `own`. An own assumption is legitimate. It must get a prediction that tests it, or be marked `untestable, accepted` in `§status`.

## Writing hygiene (hard rules, checked by `doc-hygiene-reviewer`)

- One idea per sentence. Target 18–22 words, hard cap 35.
- Paragraphs: 3–5 sentences. First sentence of every paragraph is a standalone claim.
- Skim rule: headers, bold, and first sentences must reconstruct the document.
- At most one bolded phrase per paragraph.
- No hedging words: arguably, it seems, sort of, I think, potentially, may help.
- No filler openers: In this section we, It is worth noting, Importantly.
- No em-dashes. No parentheticals longer than three words.
- Delete pass: every sentence whose removal loses no claim is removed.

## Math conventions (hard rules)

- Every symbol is an object in `§model.notation`, defined once. No silent redefinition.
- Use LaTeX for any formula or precisely defined quantity. Never prose and equation for the same fact.
- Number displayed equations that are referenced later.
- Every derivation step links the assumptions it uses. A derivation may not add an assumption; it routes a review to the formalize step.
- Distinguish definition (:=), claim to be proved, empirical observation, conjecture.

## Epistemic rules (hard rules)

- Never invent a number, citation, dataset, or result. Write `[UNKNOWN]` or `[TODO: verify]`.
- Every claim about a paper cites section, page, or equation number.
- Every empirical claim in `§results` traces to a run id or file path.
- Separate what a source says from what is inferred, with `Source:` and `Inference:` labels when in doubt.
- If a tool or data source fails, say so and stop.

## Quant-specific rules

- Any backtest or predictive claim states: data window, universe, frequency, lookahead handling, transaction-cost assumption, and the baseline it beats.
- Flag possible leakage whenever features and targets share a timestamp.
- Report in-sample and out-of-sample where the design allows it. Say when it does not.

## Rejection log

- Before writing a section, read `rp review log show . --section <§id> --global`. Nothing in the log may be re-proposed unless it is marked revived.

## Ledger and commits

- Design and ledger commits go through `rp commit "<slug>/<step> <VERB>: <one line>"`. Code-only commits use plain git. Never amend, rebase, force-push, or reset under `docs/` or `.pipeline/`.
- Reviews are append-only files under `docs/reviews/`. Only the human sets verdict, route, and disposition. A generator never grades its own output.
- Human-set review routes are unbounded. Agent-drafted reviews cap at two in a row without a human review between.

## Output discipline

- Produce exactly the sections the step owns, in the template's order, with the section comment intact. No extra sections.
- Do not summarize what you wrote. Do not add next steps unless the contract asks.
- Do not ask the user questions inside the document. Open questions go into the review the orchestrator drafts.
