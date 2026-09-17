# Benchmarks

One folder per stage. Each example is a pair:

```
benchmarks/01-read/
  ex01/
    input/        # the paper + questions.md exactly as given
    accepted.md   # the note I would accept (or AI output + my edits)
    rejected.md   # optional: an AI output I rejected, with a one-line reason at the top
```

Minimum before building a stage's agent: 3 examples. Target: 5–10.

Use: run the agent on `input/`, run `doc-hygiene-reviewer`, compare to `accepted.md`.
Every `rejected.md` reason becomes a line in that stage's "Known failure modes".
