#!/usr/bin/env python3
"""hooks.py: git hook logic for a project repository. Called by the project's .githooks/* wrappers.

  hooks.py pre-commit          fix links, ref-check (hard failures block), bump versions, index, stage docs/
  hooks.py commit-msg FILE     grammar, ownership, route; then compare the staged ledger to what the message implies
  hooks.py post-commit         print a one-line summary and any pending review (no writes)

The project is the repository: hooks act when staged paths touch docs/ or .pipeline/. Everything else
(src/, scripts/, runs/, README) commits freely with any message.

`head` in state.yaml is the HEAD seen by the last tool that wrote the state, so it is the parent of the
commit that carries it. state.py check accepts head == HEAD or head == HEAD^ when HEAD touches the ledger.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipelib as pl  # noqa: E402
import ref_checker as rc  # noqa: E402


def touched(root: Path) -> bool:
    return (root / ".pipeline" / "state.yaml").exists() and pl.project_touched(pl.git_staged(root))


def changed_sections(root: Path) -> dict[str, set[str]]:
    """Sections whose own text (excluding child sections) differs between HEAD and the working tree."""
    tree = pl.Tree(root)
    out: dict[str, set[str]] = {}
    for rel, f in tree.files.items():
        old = pl.git_show(root, "HEAD", f"docs/{rel}")
        if old is None:
            out.setdefault(rel, set()).update(f.sections)
            continue
        old_secs = pl.sections_in_text(old.split("\n"))
        for sid in f.sections:
            if sid not in old_secs or old_secs[sid]["own"] != tree.own_text(sid):
                out.setdefault(rel, set()).add(sid)
    return out


def pre_commit(root: Path) -> int:
    if not touched(root):
        return 0
    rep = rc.run(root, fix_links=True, mark=False)
    tree = pl.Tree(root)
    for rel, secs in changed_sections(root).items():
        old = pl.git_show(root, "HEAD", f"docs/{rel}")
        if secs and old is not None:
            m = re.search(r"version: v(\d+)", old)
            old_v = int(m.group(1)) if m else 0
            if (tree.files[rel].version or 0) <= old_v:
                tree.bump(rel)
                rep.notes.append(f"{rel}: version bumped to v{tree.files[rel].version}")
    tree.build_index()
    for m in rep.hard:
        print(f"HARD  {m}")
    for m in rep.warn:
        print(f"WARN  {m}")
    for m in rep.notes:
        print(f"NOTE  {m}")
    if rep.hard:
        print(f"pre-commit: {len(rep.hard)} hard failures; commit refused")
        return 1
    pl.git(["add", "--", "docs", ".pipeline/INDEX.yaml"], cwd=root)
    return 0


def check_message(root: Path, p: dict) -> str | None:
    """Grammar-level and ownership checks. Returns an error string or None."""
    tree = pl.Tree(root)
    t = tree.template
    st = pl.load_state(root)
    step = p["step"]
    if p["slug"] != st.get("slug"):
        return f"message names {p['slug']} but this project is {st.get('slug')}"
    if step != "-" and step not in t.steps and not step.endswith("·in"):
        return f"unknown step {step} for template {t.name}"
    ch = changed_sections(root)
    if p["verb"] in ("PASS", "REJECT"):
        allowed = set(t.outputs_of(step))
        for rel, secs in ch.items():
            bad = secs - allowed
            if bad:
                return f"{p['verb']} by {step} may not change {sorted(bad)} in {rel}; it owns {sorted(allowed)}"
    pr = st.get("pending_review")
    if p["verb"] == "HUMAN" and pr and (root / pr).exists():
        fm = rc.read_frontmatter(root / pr)
        if fm.get("status") in ("pending", "stale"):
            allowed = set()
            for s2 in t.steps_from(fm.get("route_to") or ""):
                allowed.update(t.outputs_of(s2))
            for rel, secs in ch.items():
                bad = secs - allowed
                if bad:
                    return (f"review {fm.get('id')} is pending and routes to {fm.get('route_to')}; "
                            f"HUMAN may change only {sorted(allowed)}, not {sorted(bad)}. Waive the review first.")
    if p["review"] and not pl.review_path(root, p["review"]).exists():
        return f"review {p['review']} does not exist"
    return None


def effects(root: Path, p: dict, write: bool) -> tuple[dict, list[str]]:
    """The ledger as it must look inside a commit with message p. With write=False nothing is left changed."""
    tree = pl.Tree(root)
    t = tree.template
    st = pl.load_state(root)
    step = p["step"]
    if step != "-" and p["verb"] in ("PASS", "REJECT"):
        rec = st.setdefault("steps", {}).setdefault(step, {"attempts": 0})
        rec["sections"] = t.outputs_of(step)
        if p["verb"] == "PASS":
            rec["status"] = "done"
            rec["attempts"] = int(p["attempt"] or rec.get("attempts", 0) or 1)
            rec.pop("stale_reason", None)
            rec.pop("reverify_ok", None)
        else:
            rec["status"] = "in_progress"
            rec["attempts"] = rec.get("attempts", 0) + 1
    st["head"] = pl.git_head_short(root)
    st["versions"] = tree.versions()
    notes: list[str] = []
    snapshot = None if write else pl.read_yaml(pl.state_path(root), {})
    pl.save_state(root, st)
    try:
        rep = rc.Report()
        rc.mark_stale(tree, rep)
        notes = rep.notes
        st = pl.load_state(root)
    finally:
        if snapshot is not None:
            pl.save_state(root, snapshot)
    return st, notes


def commit_msg(root: Path, msg_file: Path) -> int:
    if not touched(root):
        return 0
    msg = msg_file.read_text(encoding="utf-8")
    first = next((l for l in msg.splitlines() if l.strip() and not l.startswith("#")), "")
    p = pl.parse_commit(first)
    if not p:
        print("commit-msg: docs/ or .pipeline/ is touched, message must be '<slug>/<step> <VERB>[ a<n>][ <review-id>]: <one line>'")
        print(f"  verbs: {', '.join(pl.VERBS)}")
        print(f"  got: {first}")
        return 1
    err = check_message(root, p)
    if err:
        print(f"commit-msg: {err}")
        return 1
    expected, _ = effects(root, p, write=False)
    staged_txt = pl.git(["show", ":.pipeline/state.yaml"], cwd=root, check=False)
    staged = pl.yaml.safe_load(staged_txt) if staged_txt else None
    if staged != expected:
        print("commit-msg: staged .pipeline/state.yaml does not match the ledger this message implies.")
        print(f"  commit with: rp commit \"{first}\"")
        return 1
    return 0


def post_commit(root: Path) -> int:
    h = pl.git_head_short(root)
    last = pl.git(["log", "-1", "--format=%s"], cwd=root)
    print(f"committed {h}: {last}")
    if not (root / ".pipeline" / "state.yaml").exists():
        return 0
    st = pl.load_state(root)
    if st.get("pending_review"):
        print(f"pending review: {st['pending_review']}")
    stale = [s for s, r in st.get("steps", {}).items() if r.get("status") == "stale"]
    if stale:
        print(f"stale steps: {', '.join(stale)}")
    return 0


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(__doc__)
        return 2
    root = pl.git_root(Path.cwd())
    cmd = argv[0]
    if cmd == "pre-commit":
        return pre_commit(root)
    if cmd == "commit-msg":
        return commit_msg(root, Path(argv[1]))
    if cmd == "post-commit":
        return post_commit(root)
    print(f"unknown hook {cmd}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
