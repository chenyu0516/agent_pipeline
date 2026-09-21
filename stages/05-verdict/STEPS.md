# Stage 5, Verdict: steps

Orchestrator: `/verdict <slug>`. One human gate whose review is the rewind. ⏸ human gate.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 5a ⏸ | verdict | `results-reviewer` drafts → human | `§results`, `§experiment.*`, `§model.*`, log | review 5a-r<n>: each refuted hypothesis traced by link to an assumption or result; candidate causes with evidence; proposed route; no verdict from the agent | you set verdict and route | review | — |
| 5b | record | orchestrator, `doc-keeper` | review | `REWIND` or tag; stale marks; `§status` line; rejection-log entries for falsified assumptions by name; wiki note on confirm or abandon; export | ledger consistent | refs | stop |

| verdict and route at 5a | commit | marked stale |
|---|---|---|
| accept | tag `<slug>/confirmed` | nothing |
| revise → 4c | `REWIND` | `§implementation` runs, `§results` |
| revise → 3c | `REWIND` | `§experiment.leakage`, stage 4 sections |
| revise → 2c, assumption named | `REWIND`; assumption logged with the refuting hypothesis | `§model.derivation` onward |
| revise → 2a | `REWIND` | everything after `§problem` |
| abandon | tag `<slug>/abandoned`; core claim logged | nothing |

A rewind never deletes. Stale sections stay in the tree and in git, and clear one step at a time as each downstream step regenerates and passes its gate.
