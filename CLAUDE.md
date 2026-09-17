# Global rules for every agent in this pipeline

These apply to every stage. Stage contracts in `stages/*/CONTRACT.md` add to them, never relax them.
Read `PIPELINE.md` for the workflow map.

## Writing hygiene (hard rules, checked by `doc-hygiene-reviewer`)

- One idea per sentence. Target 18–22 words, hard cap 35.
- Paragraphs: 3–5 sentences. First sentence of every paragraph is a standalone claim.
- Skim rule: headers + bold + first sentences must reconstruct the document.
- At most one bolded phrase per paragraph.
- No hedging words: "arguably", "it seems", "sort of", "I think", "potentially", "may help".
- No filler openers: "In this section we", "It is worth noting", "Importantly".
- No em-dashes. No parentheticals longer than three words.
- No bullet lists inside prose sections unless the items are genuinely parallel.
- Delete pass: every sentence whose removal loses no claim is removed.

## Math conventions (hard rules)

- Every symbol is defined once, inline, at first use. No silent redefinition across sections.
- Use LaTeX for any formula, transformation, or precisely defined quantity. Never prose and equation for the same fact.
- Number displayed equations that are referenced later.
- State assumptions before the derivation that uses them, not after.
- Distinguish clearly: definition (:=), claim to be proved, empirical observation, conjecture.
- A "model" section names: state variables, parameters, what is observed, what is latent, the objective.

## Epistemic rules (hard rules)

- Never invent a number, citation, dataset, or result. Write `[UNKNOWN]` or `[TODO: verify]` instead.
- Every claim about a paper cites section/page/equation number.
- Every empirical claim in `results.md` traces to a run id or file path.
- Separate what the source says from what I infer. Use "Source:" and "Inference:" labels when in doubt.
- If a tool or data source fails, say so and stop. Do not fill the gap.

## Quant-specific rules

- Any backtest or predictive claim states: data window, universe, frequency, lookahead handling, transaction-cost assumption, and the baseline it beats.
- Flag possible leakage explicitly whenever features and targets share a timestamp.
- Report both in-sample and out-of-sample where the design allows it. Say when it does not.

## Output discipline

- Produce exactly the sections the stage contract requires, in that order. No extra sections.
- Do not summarize what you just wrote at the end. Do not add "next steps" unless the contract asks.
- Do not ask the user questions inside the document. Put open questions in an `Open questions` section only if the contract has one.
