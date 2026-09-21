# Stage 2, Ideate: steps

Orchestrator: `/ideate <slug>`. Sections per the project's taxonomy template; ids below are for `quant-model`. `refs`, rejection-log dedupe, and object naming are implicit on every generator step. ⏸ human gate, ⌂ intake gate.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 2a·in ⌂ | intake | `intake-initializer` once, `intake-reviewer` → human | `seed.md` | intake review; `## Decisions` | no open framing item; structural and detail may be delegated | intake | you answer |
| 2a ⏸ | frame | `idea-drafter`; `plan-reviewer` → human | `seed.md` with decisions, log | `§problem` with `Choices made`; review 2a-r<n> | accept; every delegated choice seen | review | route 2a |
| 2b | position | `wiki-searcher` | `§problem`, wiki | `§position` | null model named; cites only existing notes; "nothing close in wiki" is valid | hygiene | retry |
| 2c·in ⌂ | intake | `intake-initializer` once, `intake-reviewer` → human | `scribble.md`, `§problem` | intake review; `## Decisions` | no open framing item | intake | you answer |
| 2c ⏸ | formalize | `idea-drafter`; `plan-reviewer` → human | `§problem`, `§position`, `scribble.md` with decisions, log, pending review if routed | `§model.notation`, `§model.assumptions` (named, tagged), `§model.formal` with scribble diff appendix; review 2c-r<n> | every assumption named and tagged; diff present; math rules; delegated choices seen | hygiene, review | route 2c |
| 2d | derive | `deriver` | `§model.notation`, `§model.assumptions`, `§model.formal`, resolver cards, log, pending review if routed | `§model.derivation` (named results) | every step links the assumptions it uses; no unlisted assumption | `math-checker` | drafts a review to 2c |
| 2e | predict | `idea-drafter` | `§model.assumptions`, `§model.derivation`, log | `§model.predictions` (named, each linking what it tests) | every own assumption has a prediction or `untestable, accepted`; every result has a prediction; no empirical numbers | hygiene | retry |
| 2f ⏸ | adversarial review | `idea-reviewer` → human | `§problem` through `§model.predictions`, log | review 2f-r<n> | you set verdict and route | review | route 2c or 2d |
| 2g | finalize | `doc-keeper` | all | `§context`, `§status`, stubs, export | budgets; standalone | hygiene | retry |

Progress check: routes you set are unbounded. Consecutive agent-drafted reviews with no human review between them cap at two. A review whose items repeat a prior review's items on unchanged objects is flagged "no progress" and needs your confirmation.
