# Stage 1, Read: steps

Orchestrator: `/read <pdf-or-arxiv-id> [--focus "..."]`. Document: a wiki note with sections `§claim`, `§setup`, `§method`, `§results`, `§relevance`, `§hooks`. `refs`, rejection-log dedupe, and object naming are implicit on every generator step. ⏸ human gate, ⌂ intake gate.

| id | step | owner | input | output | pass rule | gate | on fail |
|---|---|---|---|---|---|---|---|
| 1·in ⌂ | intake, only when `questions.md` changes | `intake-initializer` once, `intake-reviewer` → human | `questions.md` | intake review; `## Decisions` | no open framing item | intake | you answer |
| 1a ⏸ | triage | `paper-reader`; `plan-reviewer` → human | pdf, `questions.md`, focus | `§claim`; review 1a-r<n> | accept means read | review | abandon archives |
| 1b | extract model | `paper-reader` | pdf | `§setup` | every symbol in table; every equation cited | hygiene | retry |
| 1c | extract method and results | `paper-reader` | pdf, `§setup` | `§method`, `§results` | no number without a cite | hygiene | retry |
| 1d | relate | `wiki-searcher` | `§setup`, `§method`, `§results`, `questions.md`, wiki | `§relevance`, `§hooks` | "none" allowed; Inference labels; cites only existing notes | hygiene | retry |
| 1e ⏸ | finalize | `doc-keeper`; `plan-reviewer` → human | all | `§context`; review 1e-r<n> | full contract; standalone | review | route per review |

Wiki: Obsidian vault, LLM-wiki framework. `wiki-searcher` reads the vault on disk; `doc-keeper` writes notes as markdown with frontmatter and wikilinks.
