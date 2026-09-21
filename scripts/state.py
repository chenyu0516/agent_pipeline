#!/usr/bin/env python3
"""state.py: the ledger index.

  state.py show <project>
  state.py check <project>                 tree clean, head matches, last commit matches last step
  state.py step <project> <step> <status> [--inputs §a §b file.md ...]   record a step; computes built_from and built_objects
  state.py stage <project> <stage>
  state.py rebuild <project>               rebuild steps and reviews from git log
  state.py head <project>                  record current HEAD
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipelib as pl  # noqa: E402


def check(project: Path) -> list[str]:
    problems = []
    root = pl.git_root(project)
    dirty = pl.git_dirty(root, project / "docs") + pl.git_dirty(root, project / ".pipeline")
    if dirty:
        problems.append("tree not clean under project:\n  " + "\n  ".join(dirty))
    st = pl.load_state(project)
    head = pl.git_head_short(root)
    parent = pl.git(["rev-parse", "--short", "HEAD^"], cwd=root, check=False) or None
    log = pl.git_log_for(root, project, n=1)
    head_touches = bool(log) and log[0][0] == head
    if st.get("head") and not (st["head"] == head or (head_touches and st["head"] == parent)):
        problems.append(f"state.yaml head {st['head']} but HEAD is {head} (parent {parent}); run 'state.py rebuild'")
    if log:
        parsed = pl.parse_commit(log[0][1])
        if not parsed:
            problems.append(f"last commit on project is not in grammar: {log[0][1]}")
        elif parsed["step"] != "-" and parsed["verb"] in ("PASS", "REJECT"):
            rec = st.get("steps", {}).get(parsed["step"])
            if not rec:
                problems.append(f"last commit is for step {parsed['step']} but state has no record of it")
    tree = pl.Tree(project)
    if st.get("versions") and st["versions"] != tree.versions():
        problems.append(f"state versions {st['versions']} differ from tree {tree.versions()}")
    return problems


def record_step(project: Path, step: str, status: str, inputs: list[str]):
    st = pl.load_state(project)
    tree = pl.Tree(project)
    rec = st.setdefault("steps", {}).setdefault(step, {})
    rec["status"] = status
    rec["sections"] = tree.template.outputs_of(step)
    if status == "done":
        bf, bo = {}, {}
        for key in inputs:
            if not pl.input_path(project, key).exists():
                key = pl.norm_sid(key)
            if key.startswith("§"):
                if key not in tree.sections:
                    pl.die(f"unknown section {key}")
                bf[key] = tree.sections[key].hash
            else:
                h = pl.input_hash(project, key)
                if h is None:
                    pl.die(f"no input file {key}")
                bf[key] = h
        for sid in rec["sections"]:
            s = tree.sections.get(sid)
            if not s:
                continue
            for l in tree.files[s.file].links:
                if l.section == sid:
                    for tfile, tkind, tid in tree.anchor_targets(l.anchor):
                        if tkind == "object" and tid in tree.objects:
                            bo[tid] = tree.objects[tid].hash
        rec["built_from"] = bf
        rec["built_objects"] = bo
        rec["attempts"] = rec.get("attempts", 0)
        rec.pop("stale_reason", None)
        rec.pop("reverify_ok", None)
    st["versions"] = tree.versions()
    pl.save_state(project, st)
    print(f"{step}: {status}" + (f", built from {list(rec['built_from'])}, objects {list(rec['built_objects'])}" if status == "done" else ""))


def rebuild(project: Path):
    st = pl.load_state(project)
    root = pl.git_root(project)
    steps, reviews = {}, {}
    for h, msg in reversed(pl.git_log_for(root, project, n=2000)):
        p = pl.parse_commit(msg)
        if not p:
            continue
        if p["step"] != "-" and p["verb"] in ("PASS", "REJECT", "HUMAN"):
            rec = steps.setdefault(p["step"], {"attempts": 0})
            if p["verb"] == "PASS":
                rec["status"], rec["commit"] = "done", h
            elif p["verb"] == "REJECT":
                rec["attempts"] = rec.get("attempts", 0) + 1
                rec.setdefault("status", "in_progress")
        if p["review"]:
            rv = reviews.setdefault(p["review"], {"id": p["review"]})
            rv["status"] = {"REVIEW": "pending", "INTAKE": "pending", "IMPORT": "pending", "APPLY": "applied", "WAIVE": "waived"}.get(p["verb"], rv.get("status"))
    old = st.get("steps", {})
    for k, rec in steps.items():
        if k in old:
            for key in ("built_from", "built_objects", "sections", "stale_reason", "reverify_ok"):
                if key in old[k]:
                    rec[key] = old[k][key]
    st["steps"] = steps
    st["reviews"] = [{**next((r for r in st.get("reviews", []) if r.get("id") == k), {}), **v} for k, v in reviews.items()]
    st["pending_review"] = next((pl.review_rel(r['id']) for r in st["reviews"] if r.get("status") == "pending"), None)
    st["head"] = pl.git_head_short(root)
    st["versions"] = pl.Tree(project).versions()
    pl.save_state(project, st)
    print(f"rebuilt: {len(steps)} steps, {len(reviews)} reviews, head {st['head']}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="state.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ["show", "check", "rebuild", "head"]:
        sub.add_parser(name).add_argument("project")
    p = sub.add_parser("step"); p.add_argument("project"); p.add_argument("step"); p.add_argument("status", choices=["pending", "in_progress", "done", "stale"]); p.add_argument("--inputs", nargs="*", default=[])
    p = sub.add_parser("stage"); p.add_argument("project"); p.add_argument("stage")
    a = ap.parse_args(argv)
    project = Path(a.project).resolve()
    if a.cmd == "show":
        sys.stdout.write(pl.yaml.safe_dump(pl.load_state(project), sort_keys=False, allow_unicode=True))
    elif a.cmd == "check":
        problems = check(project)
        print("\n".join(problems) if problems else "consistent")
        sys.exit(1 if problems else 0)
    elif a.cmd == "step":
        record_step(project, pl.norm_step(a.step), a.status, a.inputs)
    elif a.cmd == "stage":
        st = pl.load_state(project); st["stage"] = a.stage; pl.save_state(project, st); print(f"stage: {a.stage}")
    elif a.cmd == "rebuild":
        rebuild(project)
    elif a.cmd == "head":
        st = pl.load_state(project); st["head"] = pl.git_head_short(pl.git_root(project)); pl.save_state(project, st); print(st["head"])


if __name__ == "__main__":
    main()
