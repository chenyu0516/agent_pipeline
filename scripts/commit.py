#!/usr/bin/env python3
"""commit.py: the one way to commit design or ledger changes in a project.

  commit.py "<slug>/<step> <VERB>[ a<n>][ <review-id>]: <one line>" [--all] [--paths P ...]

Run inside the project repository. Checks grammar, ownership, and route first, so a refused commit leaves the tree
untouched; then fixes links, bumps versions, rebuilds the index, writes the ledger the message implies, stages docs/
and .pipeline/, and commits. Commits that touch only src/, scripts/, runs/, or README use plain git.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipelib as pl  # noqa: E402
import hooks  # noqa: E402


def pipeline_commit(root: Path, message: str, paths: list[Path] | None = None) -> str:
    if paths:
        pl.git(["add", "--", *[str(p) for p in paths if Path(p).exists()]], cwd=root)
    if not hooks.touched(root):
        pl.git(["commit", "-q", "-m", message], cwd=root)
        return pl.git_head_short(root)
    p = pl.parse_commit(message)
    if not p:
        pl.die(f"message not in grammar: {message}")
    err = hooks.check_message(root, p)
    if err:
        pl.die(err)
    if hooks.pre_commit(root) != 0:
        pl.die("hard failures; nothing committed")
    _, notes = hooks.effects(root, p, write=True)
    for n in notes:
        print(f"NOTE  {n}")
    pl.git(["add", "--", "docs", ".pipeline"], cwd=root)
    pl.git(["commit", "-q", "-m", message], cwd=root)
    return pl.git_head_short(root)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="commit.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("message")
    ap.add_argument("--paths", nargs="*", default=[])
    ap.add_argument("--all", action="store_true", help="stage docs/, .pipeline/, src/, scripts/, runs/ first")
    a = ap.parse_args(argv)
    root = pl.find_project()
    if pl.git_root(root) != root:
        pl.die(f"{root} is a project but not the root of its git repository")
    if a.all:
        pl.git(["add", "-A"], cwd=root)
    h = pipeline_commit(root, a.message, [Path(p).resolve() for p in a.paths])
    print(f"committed {h}")


if __name__ == "__main__":
    main()
