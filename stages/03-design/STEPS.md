# Stage 3, Design: steps

Orchestrator: `/design <slug>`. `refs`, rejection-log dedupe, and object naming are implicit on every generator step. ⏸ human gate, ⌂ intake gate.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 3a | map hypotheses | `experiment-designer` | `§model.predictions`, log | `§experiment.hypotheses` (named, each linking its prediction) | every own-assumption prediction has a hypothesis; at most three result-hypotheses | hygiene | retry |
| 3b·in ⌂ | intake | `intake-initializer` once, `intake-reviewer` → human | `data.md`, `§experiment.hypotheses` | intake review; `## Decisions` | no open framing item | intake | you answer |
| 3b ⏸ | data | `experiment-designer`; `plan-reviewer` → human | `§experiment.hypotheses`, `data.md` with decisions, log | `§data` with `Choices made`; review 3b-r<n> | no field outside `data.md`; gaps explicit | review | route 3b |
| 3c | procedure | `experiment-designer` | `§experiment.hypotheses`, `§data`, `§model.notation`, log | `§experiment.procedure` (named features and metrics, baselines, split) | every hypothesis has a metric and a baseline | hygiene | retry |
| 3d | leakage audit | `leakage-auditor` | `§experiment.procedure` | `§experiment.leakage` | every feature linked and audited; no violation | `leakage-auditor` | drafts a review to 3c |
| 3e ⏸ | finalize | `doc-keeper`; `plan-reviewer` → human | all | `§context`, `§status`, export; review 3e-r<n> | budgets; standalone | review | route per review |
