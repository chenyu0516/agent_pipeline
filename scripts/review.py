#!/usr/bin/env python3
"""review.py: the review object and the rejection log.

  review.py new <project> --step 2f [--kind gate|intake|external] [--sections §a §b] [--input seed.md]
                          [--source FILE --from "Name"] [--by AGENT]
  review.py validate <file>
  review.py commit <file> [--msg "..."]            draft -> pending (or applied on accept); commits REVIEW/INTAKE/IMPORT
  review.py disposition <file> I1 accept|counter|decline|defer [--required "..."] [--why "..."]
  review.py verify <file> [--set I1 addressed --quote "..."]   verify mode; prints current hashes of judged sections
  review.py apply <file>                            all items addressed or waived -> applied; commits APPLY
  review.py waive <file> --why "..."
  review.py reply <file>                            note for a coworker, names only
  review.py log add <project> --target 'A3 "name"'|§id --proposal "..." --why "..." [--review ID] [--from "Name"]
  review.py log promote <project> R19
  review.py log revive <project> R17 --why "..."
  review.py log show <project> [--section §id] [--global]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipelib as pl  # noqa: E402
from ref_checker import read_frontmatter, write_frontmatter  # noqa: E402
from commit import pipeline_commit  # noqa: E402

BLOCKING = {"accept", "counter"}


def project_of(path: Path) -> Path:
    return pl.find_project(path.resolve().parent if path.is_file() else path)


def new(project: Path, step: str, kind: str, sections: list[str], inp: str | None, source: Path | None, frm: str | None, by: str | None) -> Path:
    tree = pl.Tree(project)
    rid = pl.next_review_id(project, step, kind)
    root = pl.git_root(project)
    st = pl.load_state(project)
    if not sections:
        stage = tree.template.stage_of(step.replace("·in", ""))
        sections = sorted({sid for s2 in tree.template.step_order if tree.template.stage_of(s2) == stage for sid in tree.template.outputs_of(s2) if sid in tree.sections})
    fm = {
        "id": rid, "kind": kind, "step": step, "origin": "external" if kind == "external" else "internal",
        "external_source": str(source.resolve().relative_to(project)) if source and source.resolve().is_relative_to(project) else (str(source) if source else None),
        "doc_version": {"commit": pl.git_head_short(root), "files": tree.versions()},
        "sections_judged": {sid: tree.sections[sid].hash for sid in sections if sid in tree.sections},
        "authors": [by or ("review-converter" if kind == "external" else "intake-reviewer" if kind == "intake" else "reviewer")],
        "verdict": None, "route_to": None, "status": "draft", "applied_version": None, "items": [],
    }
    if kind == "intake":
        fm["input"] = inp
        fm["input_hash"] = pl.input_hash(project, inp) if inp else None
        fm["items"] = [{"id": "Q1", "severity": "framing", "choice": "", "why_it_matters": "", "options": [], "answer": None}]
    else:
        fm["items"] = [{"id": "I1", "object": None, "section": sections[0] if sections else None, "source": fm["authors"][0],
                        "finding": "", "proposal": "", "disposition": "accept", "required": "", "logged": None,
                        "status": "open", "addressed_at": None, "quote": None}]
    if frm:
        fm["authors"].append(frm)
    body = f"\n\n## Draft by {fm['authors'][0]}\n\n<!-- reviewer prose here; human edits are appended below, never deleted -->\n"
    if source:
        body += f"\n## Original from {frm or 'coworker'}\n\n```\n{source.read_text(encoding='utf-8').strip()}\n```\n"
    path = pl.review_path(project, rid)
    path.write_text("---\n" + pl.yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=120) + "---" + body, encoding="utf-8")
    return path


def validate(path: Path, final: bool = True) -> list[str]:
    fm = read_frontmatter(path)
    errs = []
    for k in ("id", "kind", "step", "doc_version", "sections_judged", "authors", "status", "items"):
        if k not in fm:
            errs.append(f"missing field {k}")
    if errs:
        return errs
    if not pl.REVIEW_ID_RE.match(fm["id"]):
        errs.append(f"bad review id {fm['id']}")
    if fm["kind"] == "intake":
        for it in fm["items"]:
            if it.get("severity") not in ("framing", "structural", "detail"):
                errs.append(f"{it.get('id')}: severity must be framing, structural, or detail")
            if final and it.get("severity") == "framing" and (it.get("answer") in (None, "", "delegate")):
                errs.append(f"{it.get('id')}: framing item must be answered by you")
            if final and it.get("answer") in (None, ""):
                errs.append(f"{it.get('id')}: no answer (write an option, free text, or 'delegate')")
        return errs
    if final:
        if fm.get("verdict") not in ("accept", "revise", "abandon"):
            errs.append("verdict must be accept, revise, or abandon")
        if fm.get("verdict") == "revise" and not fm.get("route_to"):
            errs.append("revise needs route_to")
        if fm.get("verdict") == "accept" and fm.get("route_to"):
            errs.append("accept must not carry route_to")
    prose = path.read_text(encoding="utf-8").split("\n---", 1)[-1].lower()
    for it in fm["items"]:
        d = it.get("disposition")
        if d not in ("accept", "counter", "decline", "defer"):
            errs.append(f"{it.get('id')}: disposition must be accept, counter, decline, or defer")
        if not it.get("finding"):
            errs.append(f"{it.get('id')}: empty finding")
        if d in BLOCKING and not it.get("required"):
            errs.append(f"{it.get('id')}: {d} needs a required change")
        if d in ("decline", "defer") and it.get("required"):
            errs.append(f"{it.get('id')}: {d} must leave required empty")
        if d == "decline" and "finding invalid because" not in prose:
            errs.append(f"{it.get('id')}: decline needs a reason in prose starting 'finding invalid because'")
        if it.get("status") == "addressed" and not it.get("quote"):
            errs.append(f"{it.get('id')}: addressed items need a quote of the satisfying text")
    return errs


def commit(path: Path, msg: str | None):
    project = project_of(path)
    root = pl.git_root(project)
    fm = read_frontmatter(path)
    user = pl.git_user(root)
    if user not in fm.get("authors", []):
        fm.setdefault("authors", []).append(user)
    errs = validate_with(path, fm)
    if errs:
        pl.die("review not valid:\n  " + "\n  ".join(errs))
    st = pl.load_state(project)
    kind = fm["kind"]
    verb = {"intake": "INTAKE", "external": "IMPORT"}.get(kind, "REVIEW")
    paths = [path]
    if kind == "intake":
        # write answers into the input file under ## Decisions
        inp = pl.input_path(project, fm["input"])
        text = inp.read_text(encoding="utf-8")
        lines = [f"- {it['id']}: {it['answer']} ({'delegate' if it['answer'] == 'delegate' else 'answered'}) — {it['choice']}" for it in fm["items"]]
        block = "\n".join(lines)
        if "## Decisions" in text:
            text = text.rstrip("\n") + "\n" + block + "\n"
        else:
            text += "\n## Decisions\n" + block + "\n"
        inp.write_text(text, encoding="utf-8")
        fm["status"] = "applied"
        fm["applied_version"] = {"commit": pl.git_head_short(root), "files": pl.Tree(project).versions()}
        st.setdefault("inputs", {}).setdefault(fm["input"], {})
        st["inputs"][fm["input"]].update({"hash": pl.input_hash(project, fm["input"]), "intake": fm["id"], "status": "applied"})
        paths.append(inp)
    else:
        blocking = [it for it in fm["items"] if it.get("disposition") in BLOCKING and it.get("status") == "open"]
        # log countered and declined proposals
        for it in fm["items"]:
            if it.get("disposition") in ("counter", "decline") and not it.get("logged"):
                target = it.get("object") or it.get("section") or "-"
                if it.get("object") and it["object"] in pl.Tree(project).objects:
                    target = f"{it['object']} \"{pl.Tree(project).objects[it['object']].name}\""
                reason = it.get("required") or "see review prose"
                it["logged"] = pl.append_log(project, fm["id"], target, it.get("proposal", ""), "countered" if it["disposition"] == "counter" else "declined", reason, user)
                st = pl.load_state(project)
        for it in fm["items"]:
            if it.get("disposition") == "defer":
                with open(pl.P(project).deferred, "a", encoding="utf-8") as fh:
                    fh.write(f"- {fm['id']} {it['id']} ({it.get('section')}): {it['finding']} — {it.get('proposal', '')}\n")
                paths.append(pl.P(project).deferred)
        if fm.get("verdict") == "accept" and not blocking:
            fm["status"] = "applied"
            fm["applied_version"] = dict(fm["doc_version"])
        elif fm.get("verdict") == "abandon":
            fm["status"] = "applied"
            fm["applied_version"] = dict(fm["doc_version"])
        else:
            fm["status"] = "pending" if not st.get("pending_review") else "draft"
            if fm["status"] == "pending":
                st["pending_review"] = pl.review_rel(fm['id'])
                key = f"{fm['step']}->{fm['route_to']}"
                st.setdefault("loops", {})[key] = st["loops"].get(key, 0) + 1
            else:
                st.setdefault("queued_reviews", []).append(pl.review_rel(fm['id']))
                print(f"note: {st['pending_review']} is pending; {fm['id']} queued")
        paths.append(pl.P(project).rejected)
    rec = {"id": fm["id"], "kind": kind, "verdict": fm.get("verdict"), "route_to": fm.get("route_to"), "status": fm["status"],
           "doc_version": fm["doc_version"], "applied_version": fm.get("applied_version")}
    st.setdefault("reviews", [])
    st["reviews"] = [r for r in st["reviews"] if r.get("id") != fm["id"]] + [rec]
    write_frontmatter(path, fm)
    if fm["status"] == "applied" and kind != "intake":
        status_line(project, fm)
        paths += [pl.P(project).docs, pl.P(project).index]
    pl.save_state(project, st)
    paths.append(pl.P(project).state)
    m = msg or f"{fm['kind']} review {fm['id']} {fm.get('verdict') or ''}".strip()
    step = fm["step"] if fm["step"] != "-" else "-"
    h = pipeline_commit(root, pl.format_commit(project.name, step, verb, m, review=fm["id"]), [Path(p) for p in paths])
    print(f"{fm['id']}: {fm['status']} at {h}")


def validate_with(path: Path, fm: dict) -> list[str]:
    write_frontmatter(path, fm)
    return validate(path, final=True)


def status_line(project: Path, fm: dict):
    tree = pl.Tree(project)
    dv = fm["doc_version"]; av = fm.get("applied_version") or dv
    def fmt(v):
        return f"{v['commit']} (" + ", ".join(f"{k} v{n}" for k, n in v["files"].items()) + ")"
    names = []
    for it in fm["items"]:
        if it.get("object") and it["object"] in tree.objects:
            o = tree.objects[it["object"]]
            names.append(f"[{o.name}]({o.file}#{o.anchor})")
    line = f"- {fm['id']} judged {fmt(dv)}, {fm.get('verdict')}" + (f" → {fm['route_to']}" if fm.get("route_to") else "") + f", applied {fmt(av)}" + (": " + ", ".join(names) if names else "") + "."
    tree.append("§status", line)
    tree.build_index()


def disposition(path: Path, item: str, d: str, required: str | None, why: str | None):
    fm = read_frontmatter(path)
    it = next((x for x in fm["items"] if x.get("id") == item), None)
    if not it:
        pl.die(f"no item {item}")
    it["disposition"] = d
    if d == "accept":
        it["required"] = required or it.get("proposal", "")
    elif d == "counter":
        if not required:
            pl.die("counter needs --required")
        it["required"] = required
    else:
        it["required"] = ""
    write_frontmatter(path, fm)
    if why:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(f"\n### {item} {d} by {pl.git_user(pl.git_root(project_of(path)))}\n\n{why}\n")
    print(f"{item}: {d}")


def verify(path: Path, sets: list[tuple[str, str, str | None]]):
    project = project_of(path)
    tree = pl.Tree(project)
    fm = read_frontmatter(path)
    for item, status, quote in sets:
        it = next((x for x in fm["items"] if x.get("id") == item), None)
        if not it:
            pl.die(f"no item {item}")
        it["status"] = status
        if status == "addressed":
            if not quote:
                pl.die("addressed needs --quote")
            it["quote"] = quote
            it["addressed_at"] = pl.git_head_short(pl.git_root(project))
    write_frontmatter(path, fm)
    print(f"review {fm['id']} judged {fm['doc_version']['commit']}; sections now:")
    for sid, h in (fm.get("sections_judged") or {}).items():
        cur = tree.sections[sid].hash if sid in tree.sections else None
        print(f"  {sid}: {'unchanged' if cur == h else f'changed {h} -> {cur}'}")
    for it in fm["items"]:
        print(f"  {it['id']} {it.get('disposition')}: {it.get('status')}" + (f" ({it.get('quote')[:60]}...)" if it.get("quote") else ""))


def apply(path: Path):
    project = project_of(path)
    root = pl.git_root(project)
    fm = read_frontmatter(path)
    if fm.get("status") not in ("pending", "stale"):
        pl.die(f"review is {fm.get('status')}, not pending")
    open_items = [it["id"] for it in fm["items"] if it.get("disposition") in BLOCKING and it.get("status") not in ("addressed", "waived")]
    if open_items:
        pl.die(f"items still open: {open_items}")
    errs = validate(path)
    if errs:
        pl.die("review not valid:\n  " + "\n  ".join(errs))
    tree = pl.Tree(project)
    fm["status"] = "applied"
    fm["applied_version"] = {"commit": pl.git_head_short(root), "files": tree.versions()}
    write_frontmatter(path, fm)
    status_line(project, fm)
    st = pl.load_state(project)
    for r in st.get("reviews", []):
        if r.get("id") == fm["id"]:
            r["status"], r["applied_version"] = "applied", fm["applied_version"]
    st["pending_review"] = None
    if st.get("queued_reviews"):
        nxt = st["queued_reviews"].pop(0)
        st["pending_review"] = nxt
        nfm = read_frontmatter(project / nxt)
        nfm["status"] = "pending"
        write_frontmatter(project / nxt, nfm)
        for r in st["reviews"]:
            if r.get("id") == nfm.get("id"):
                r["status"] = "pending"
        print(f"promoted {nxt} to pending")
    pl.save_state(project, st)
    paths = [path, pl.P(project).state, pl.P(project).index, pl.P(project).docs]
    if st.get("pending_review"):
        paths.append(project / st["pending_review"])
    h = pipeline_commit(root, pl.format_commit(project.name, fm["step"], "APPLY", f"review {fm['id']} applied", review=fm["id"]), [Path(p) for p in paths])
    print(f"{fm['id']}: applied at {h}")


def waive(path: Path, why: str):
    project = project_of(path)
    root = pl.git_root(project)
    fm = read_frontmatter(path)
    fm["status"] = "waived"
    write_frontmatter(path, fm)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(f"\n### Waived by {pl.git_user(root)}\n\n{why}\n")
    st = pl.load_state(project)
    if (st.get("pending_review") or "").endswith(f"{fm['id']}.md"):
        st["pending_review"] = None
    for r in st.get("reviews", []):
        if r.get("id") == fm["id"]:
            r["status"] = "waived"
    pl.save_state(project, st)
    h = pipeline_commit(root, pl.format_commit(project.name, fm["step"], "WAIVE", why, review=fm["id"]), [path, pl.P(project).state])
    print(f"{fm['id']}: waived at {h}")


def reply(path: Path):
    project = project_of(path)
    tree = pl.Tree(project)
    fm = read_frontmatter(path)
    who = next((a for a in fm.get("authors", []) if a not in ("review-converter", pl.git_user(pl.git_root(project)))), "you")
    out = [f"# Reply to {who} on {fm['id']}", "", f"Thanks for the comments on {tree.files['DESIGN.md'].title}. Here is what I did with each.", ""]
    for it in fm["items"]:
        name = tree.objects[it["object"]].name if it.get("object") in tree.objects else (it.get("section") or "the document")
        out.append(f"- **{name}**: you found that {it['finding']}. " + {
            "accept": f"Agreed, I will {it.get('required')}.",
            "counter": f"The finding stands, but I will instead {it.get('required')}.",
            "decline": "I do not think this holds; see my note in the review.",
            "defer": "Parked for now; it is on the deferred list.",
        }[it.get("disposition", "accept")])
    out += ["", f"Applied at: {fm.get('applied_version') or 'pending'}"]
    print("\n".join(out))


def log_cmd(a):
    project = Path(a.project).resolve()
    if a.logcmd == "add":
        rid = pl.append_log(project, a.review or "manual", a.target, a.proposal, "rejected", a.why, a.frm or pl.git_user(pl.git_root(project)))
        print(f"{rid} logged; commit with '{project.name}/- REJECT-LOG: {rid}'")
    elif a.logcmd == "promote":
        entry = next((e for e in pl.log_entries(project, include_global=False) if e["id"] == a.rid), None)
        if not entry:
            pl.die(f"no {a.rid} in project log")
        if not pl.GLOBAL_LOG.exists():
            pl.GLOBAL_LOG.write_text("# Rejected proposals, global\n\n<!-- curated with review.py log promote; append-only -->\n", encoding="utf-8")
        with open(pl.GLOBAL_LOG, "a", encoding="utf-8") as fh:
            fh.write(entry["raw"] + f" | promoted: from {project.name}\n")
        print(f"{a.rid} promoted to {pl.GLOBAL_LOG.name}")
    elif a.logcmd == "revive":
        p = pl.P(project).rejected
        lines = p.read_text(encoding="utf-8").splitlines()
        hit = [i for i, l in enumerate(lines) if l.startswith(a.rid + " |")]
        if not hit:
            pl.die(f"no {a.rid}")
        lines[hit[0]] += f" | revived: {a.why} ({pl.today()})"
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"{a.rid} revived")
    elif a.logcmd == "show":
        for e in pl.log_entries(project, include_global=a.glob):
            if a.section and not e["target"].startswith(a.section):
                continue
            print(e["raw"])


def main(argv=None):
    ap = argparse.ArgumentParser(prog="review.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("new"); p.add_argument("project"); p.add_argument("--step", required=True); p.add_argument("--kind", default="gate", choices=["gate", "intake", "external"])
    p.add_argument("--sections", nargs="*", default=[]); p.add_argument("--input"); p.add_argument("--source"); p.add_argument("--from", dest="frm"); p.add_argument("--by")
    sub.add_parser("validate").add_argument("file")
    p = sub.add_parser("commit"); p.add_argument("file"); p.add_argument("--msg")
    p = sub.add_parser("disposition"); p.add_argument("file"); p.add_argument("item"); p.add_argument("disposition", choices=["accept", "counter", "decline", "defer"]); p.add_argument("--required"); p.add_argument("--why")
    p = sub.add_parser("verify"); p.add_argument("file"); p.add_argument("--set", nargs="+", action="append", default=[], metavar=("ITEM STATUS", "QUOTE"))
    sub.add_parser("apply").add_argument("file")
    p = sub.add_parser("waive"); p.add_argument("file"); p.add_argument("--why", required=True)
    sub.add_parser("reply").add_argument("file")
    p = sub.add_parser("log"); ls = p.add_subparsers(dest="logcmd", required=True)
    q = ls.add_parser("add"); q.add_argument("project"); q.add_argument("--target", required=True); q.add_argument("--proposal", required=True); q.add_argument("--why", required=True); q.add_argument("--review"); q.add_argument("--from", dest="frm")
    q = ls.add_parser("promote"); q.add_argument("project"); q.add_argument("rid")
    q = ls.add_parser("revive"); q.add_argument("project"); q.add_argument("rid"); q.add_argument("--why", required=True)
    q = ls.add_parser("show"); q.add_argument("project"); q.add_argument("--section"); q.add_argument("--global", dest="glob", action="store_true")
    a = ap.parse_args(argv)

    if a.cmd == "new":
        path = new(Path(a.project).resolve(), a.step, a.kind, a.sections, a.input, Path(a.source).resolve() if a.source else None, a.frm, a.by)
        print(f"draft {path}")
    elif a.cmd == "validate":
        errs = validate(Path(a.file))
        print("\n".join(errs) if errs else "valid")
        sys.exit(1 if errs else 0)
    elif a.cmd == "commit":
        commit(Path(a.file), a.msg)
    elif a.cmd == "disposition":
        disposition(Path(a.file), a.item, a.disposition, a.required, a.why)
    elif a.cmd == "verify":
        sets = []
        for s in a.set:
            if len(s) < 2:
                pl.die("--set ITEM STATUS [QUOTE]")
            sets.append((s[0], s[1], " ".join(s[2:]) if len(s) > 2 else None))
        verify(Path(a.file), sets)
    elif a.cmd == "apply":
        apply(Path(a.file))
    elif a.cmd == "waive":
        waive(Path(a.file), a.why)
    elif a.cmd == "reply":
        reply(Path(a.file))
    elif a.cmd == "log":
        log_cmd(a)


if __name__ == "__main__":
    main()
