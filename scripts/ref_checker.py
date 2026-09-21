#!/usr/bin/env python3
"""ref_checker.py: deterministic checks over a project's document tree.

  ref_checker.py <project> [--fix-links] [--mark-stale] [--json] [--quiet]

Exit 1 on any hard failure. Hard failures and warnings follow stages/REFS.md section 6.
With --mark-stale, compares state.yaml built_from hashes to the tree and updates step and review status.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipelib as pl  # noqa: E402


class Report:
    def __init__(self):
        self.hard: list[str] = []
        self.warn: list[str] = []
        self.notes: list[str] = []

    def h(self, msg):
        self.hard.append(msg)

    def w(self, msg):
        self.warn.append(msg)


def check_files(tree: pl.Tree, r: Report):
    for rel, f in tree.files.items():
        if not f.title:
            r.h(f"{rel}: no H1 title")
        if f.decl_line is None:
            r.h(f"{rel}: no file declaration '<!-- file: {rel} | version: vN -->'")
        elif f.decl_name != rel:
            r.h(f"{rel}: file declaration names '{f.decl_name}'")
        if f.context is None:
            r.h(f"{rel}: no Context blockquote '> **Context.** ...' before the first section")
        elif pl.sentences(f.context) > 4:
            r.h(f"{rel}: Context has {pl.sentences(f.context)} sentences, limit 4")
        for anchor, hs in f.anchors.items():
            if len(hs) > 1:
                r.h(f"{rel}: duplicate anchor #{anchor} at lines {[h.line + 1 for h in hs]}")


def check_sections(tree: pl.Tree, r: Report):
    t = tree.template
    expected = [s["id"] for s in t.flat]
    present = [sid for sid in tree.sections if "#dup@" not in sid]
    for sid in expected:
        if sid not in present:
            r.h(f"missing section {sid} (template {t.name})")
    for sid in present:
        if sid not in expected:
            r.w(f"section {sid} is not in template {t.name}")
    for sid in tree.sections:
        if "#dup@" in sid:
            r.h(f"duplicate section {sid.split('#dup@')[0]} at {sid.split('#dup@')[1]}")
    # order within DESIGN.md follows the template
    root = tree.files.get("DESIGN.md")
    if root:
        order = [sid for sid in root.sections if sid in expected]
        stubs = [st.id for st in tree.stubs.values() if st.file == "DESIGN.md"]
        seq = sorted(order + stubs, key=lambda s: (tree.sections[s].start if s in tree.sections and tree.sections[s].file == "DESIGN.md" else tree.stubs[s].start))
        exp_seq = [s for s in expected if s in seq]
        if seq != exp_seq:
            r.h(f"DESIGN.md section order {seq} differs from template order {exp_seq}")
    for sid, s in tree.sections.items():
        if "#dup@" in sid:
            continue
        exp_owner = t.owner_of(sid)
        if exp_owner != "-" and s.owner != exp_owner:
            r.h(f"{sid}: owner '{s.owner}' but template says '{exp_owner}'")
    for sid, st in tree.stubs.items():
        tpath = (tree.docs / st.file).parent / st.target
        if not tpath.exists():
            r.h(f"stub {sid} in {st.file} points to missing {st.target}")
        elif sid not in tree.sections:
            r.h(f"stub {sid} in {st.file}: {st.target} does not define {sid}")
        if st.summary_pending:
            r.w(f"stub {sid} in {st.file}: summary pending")


def check_objects(tree: pl.Tree, r: Report):
    t = tree.template
    names: dict[str, str] = {}
    for oid, o in tree.objects.items():
        if "#dup@" in oid:
            r.h(f"duplicate object id {oid.split('#dup@')[0]} at {oid.split('#dup@')[1]}")
            continue
        k = t.kind_of(oid)
        if not k:
            r.h(f"{oid} '{o.name}': prefix not in template kinds {list(t.kinds)}")
        else:
            if k["kind"] != o.kind:
                r.h(f"{oid} '{o.name}': kind '{o.kind}' but prefix means '{k['kind']}'")
            if k.get("section") and o.section != k["section"]:
                r.h(f"{oid} '{o.name}': defined in {o.section}, template says {k['section']}")
            if k.get("tag_required") and o.tag not in ("lit", "standard", "own"):
                r.h(f"{oid} '{o.name}': tag must be lit, standard, or own")
            if k.get("tests") and o.tests:
                allowed = k["tests"] if isinstance(k["tests"], list) else [k["tests"]]
                pref = re.sub(r"\d+$", "", o.tests)
                if pref not in allowed:
                    r.h(f"{oid} '{o.name}': tests {o.tests}, allowed prefixes {allowed}")
                if o.tests not in tree.objects:
                    r.h(f"{oid} '{o.name}': tests {o.tests} which does not exist")
        words = o.name.lower().split()
        if not 2 <= len(words) <= 5:
            r.h(f"{oid} '{o.name}': name must be two to five words")
        if any(w in pl.KIND_WORDS for w in words):
            r.h(f"{oid} '{o.name}': name contains a kind word")
        if any(w in pl.ORDINALS or re.search(r"\d", w) for w in words):
            r.h(f"{oid} '{o.name}': name contains an ordinal or digit")
        low = o.name.lower()
        if low in names:
            r.h(f"{oid} '{o.name}': duplicate name of {names[low]}")
        names[low] = oid


def check_links(tree: pl.Tree, r: Report):
    for rel, f in tree.files.items():
        for l in f.links:
            targets = [t for t in tree.anchor_targets(l.anchor) if t[1] in ("object", "section", "heading")]
            if l.path:
                tfile = str(((tree.docs / rel).parent / l.path).resolve().relative_to(tree.docs)) if (tree.docs / rel).parent.joinpath(l.path).resolve().is_relative_to(tree.docs) else None
                targets = [t for t in targets if t[0] == tfile]
            else:
                targets = [t for t in targets if t[0] == rel]
            if not targets:
                r.h(f"{rel}:{l.line + 1}: link [{l.text}]({l.path}#{l.anchor}) does not resolve")
                continue
            tfile, tkind, tid = targets[0]
            if tkind == "object" and tid in tree.objects and l.text.lower() != tree.objects[tid].name.lower():
                r.h(f"{rel}:{l.line + 1}: link text '{l.text}' differs from object name '{tree.objects[tid].name}'")


def check_prose(tree: pl.Tree, r: Report):
    prefixes = tree.template.prefixes()
    bare = re.compile(r"(?<![\w\-#/])(" + "|".join(prefixes) + r")\d+(?![\w\-])")
    for rel, f in tree.files.items():
        prose = pl.strip_prose("\n".join(f.lines))
        for i, line in enumerate(prose.splitlines()):
            for m in bare.finditer(line):
                r.h(f"{rel}: bare object id '{m.group(0)}' in prose: '{line.strip()[:80]}'")
            low = line.lower()
            for b in pl.BANNED:
                if re.search(r"\b" + re.escape(b) + r"\b", low):
                    r.h(f"{rel}: banned phrase '{b}': '{line.strip()[:80]}'")


def check_rejected_spans(tree: pl.Tree, r: Report):
    entries = [e for e in pl.log_entries(tree.project) if not e["revived"] and e.get("proposal")]
    if not entries:
        return
    for sid, s in tree.sections.items():
        if "#dup@" in sid:
            continue
        text = tree.get(sid)
        sh = pl.shingles(text, 6)
        for e in entries:
            target = e["target"].split(" ")[0]
            if target not in (sid,) and not (target in tree.objects and tree.objects[target].section == sid):
                continue
            hit = sh & pl.shingles(e["proposal"], 6)
            if hit:
                r.h(f"{sid}: reuses a rejected proposal {e['id']} ('{' '.join(next(iter(hit)))}...')")


def mark_stale(tree: pl.Tree, r: Report) -> bool:
    st = pl.load_state(tree.project)
    changed = False
    for step, rec in st.get("steps", {}).items():
        if rec.get("status") not in ("done", "stale"):
            continue
        reasons = []
        for key, h in (rec.get("built_from") or {}).items():
            cur = tree.sections[key].hash if key.startswith("§") and key in tree.sections else (None if key.startswith("§") else pl.input_hash(tree.project, key))
            if cur != h:
                reasons.append(f"{key} changed")
        if reasons and rec.get("status") == "done":
            rec["status"] = "stale"
            rec["stale_reason"] = "; ".join(reasons)
            bo = rec.get("built_objects") or {}
            rec["reverify_ok"] = bool(bo) and all(oid in tree.objects and tree.objects[oid].hash == h for oid, h in bo.items())
            r.notes.append(f"step {step} marked stale: {rec['stale_reason']}" + (" (re-verify only possible)" if rec["reverify_ok"] else ""))
            changed = True
        elif not reasons and rec.get("status") == "stale":
            rec["status"] = "done"
            rec.pop("stale_reason", None)
            rec.pop("reverify_ok", None)
            r.notes.append(f"step {step} no longer stale")
            changed = True
    pr = st.get("pending_review")
    if pr:
        rp = tree.project / pr
        if rp.exists():
            fm = read_frontmatter(rp)
            allowed = set()
            for s2 in tree.template.steps_from(fm.get("route_to") or ""):
                allowed.update(tree.template.outputs_of(s2))
            for sid, h in (fm.get("sections_judged") or {}).items():
                if sid in tree.sections and tree.sections[sid].hash != h and sid not in allowed and fm.get("status") == "pending":
                    fm["status"] = "stale"
                    write_frontmatter(rp, fm)
                    for rv in st.get("reviews", []):
                        if rv.get("id") == fm.get("id"):
                            rv["status"] = "stale"
                    r.notes.append(f"review {fm.get('id')} marked stale: {sid} changed off-route")
                    changed = True
                    break
    st["versions"] = tree.versions()
    pl.save_state(tree.project, st)
    return changed


def read_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    return pl.yaml.safe_load(text[3:end]) or {}


def write_frontmatter(path: Path, fm: dict):
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---", 3)
    body = text[end + 4 :]
    path.write_text("---\n" + pl.yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=120) + "---" + body, encoding="utf-8")


def run(project: Path, fix_links=False, mark=False) -> Report:
    tree = pl.Tree(project)
    r = Report()
    if fix_links:
        r.notes += tree.relink()
    check_files(tree, r)
    check_sections(tree, r)
    check_objects(tree, r)
    check_links(tree, r)
    check_prose(tree, r)
    check_rejected_spans(tree, r)
    r.warn += tree.budget_report()
    if mark and pl.P(project).state.exists():
        mark_stale(tree, r)
    tree.build_index()
    return r


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ref_checker.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--fix-links", action="store_true")
    ap.add_argument("--mark-stale", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    r = run(Path(a.project), a.fix_links, a.mark_stale)
    if a.json:
        print(json.dumps({"hard": r.hard, "warnings": r.warn, "notes": r.notes}, ensure_ascii=False, indent=2))
    elif not a.quiet or r.hard:
        for m in r.hard:
            print(f"HARD  {m}")
        for m in r.warn:
            print(f"WARN  {m}")
        for m in r.notes:
            print(f"NOTE  {m}")
        print(f"{len(r.hard)} hard, {len(r.warn)} warnings")
    sys.exit(1 if r.hard else 0)


if __name__ == "__main__":
    main()
