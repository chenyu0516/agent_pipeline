#!/usr/bin/env python3
"""doc.py: the document tree tool.

  doc.py init <slug> --template <name> [--title "..."] [--at PARENT_DIR]   new project = new git repo at PARENT_DIR/<slug>
  doc.py index <project>                 rebuild INDEX.yaml and REGISTRY.md
  doc.py get <project> <§id>             print a section
  doc.py put <project> <§id> --from FILE|-   replace a section (bumps the file version)
  doc.py append <project> <§id> "text"   append a line to a section (no bump)
  doc.py resolve <project> <query>       id, name, or file#anchor -> card
  doc.py split <project> <§id> [--to FILE]
  doc.py merge <project> <§id>
  doc.py export <project>
  doc.py budget <project>
  doc.py version <project>
  doc.py relink <project>                fix link paths and texts
  doc.py bump <project> <file>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipelib as pl  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(prog="doc.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init"); p.add_argument("slug"); p.add_argument("--template", required=True); p.add_argument("--title"); p.add_argument("--at")
    for name in ["index", "export", "budget", "version", "relink"]:
        sub.add_parser(name).add_argument("project")
    p = sub.add_parser("get"); p.add_argument("project"); p.add_argument("section")
    p = sub.add_parser("put"); p.add_argument("project"); p.add_argument("section"); p.add_argument("--from", dest="src", required=True); p.add_argument("--no-bump", action="store_true")
    p = sub.add_parser("append"); p.add_argument("project"); p.add_argument("section"); p.add_argument("text")
    p = sub.add_parser("resolve"); p.add_argument("project"); p.add_argument("query"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("split"); p.add_argument("project"); p.add_argument("section"); p.add_argument("--to")
    p = sub.add_parser("merge"); p.add_argument("project"); p.add_argument("section")
    p = sub.add_parser("bump"); p.add_argument("project"); p.add_argument("file")
    a = ap.parse_args(argv)

    if a.cmd == "init":
        work = pl.init_project(a.slug, a.template, a.title, Path(a.at) if a.at else None)
        print(f"initialized {work} as a git repository with hooks enabled")
        print(f"next: cd {work} && rp commit --all \"{a.slug}/- INIT: project created\"; then fill docs/inputs/{', docs/inputs/'.join(pl.Template(a.template).inputs)}")
        return

    tree = pl.Tree(Path(a.project))
    if a.cmd == "index":
        idx = tree.build_index()
        print(f"indexed {len(idx['files'])} files, {len(idx['sections'])} sections, {len(idx['objects'])} objects")
    elif a.cmd == "get":
        sys.stdout.write(tree.get(a.section))
    elif a.cmd == "put":
        text = sys.stdin.read() if a.src == "-" else Path(a.src).read_text(encoding="utf-8")
        rel = tree.put(a.section, text, bump=not a.no_bump)
        tree.build_index()
        print(f"wrote {a.section} in {rel} (now v{tree.files[rel].version})")
    elif a.cmd == "append":
        tree.append(a.section, a.text)
        tree.build_index()
        print(f"appended to {a.section}")
    elif a.cmd == "resolve":
        card = tree.resolve(a.query)
        if not card:
            pl.die(f"nothing resolves '{a.query}'", 1)
        if a.json:
            import json
            print(json.dumps(card, ensure_ascii=False, indent=2))
        else:
            for k, v in card.items():
                if k == "text":
                    print("text:\n" + "\n".join("  " + l for l in v.splitlines()))
                else:
                    print(f"{k}: {v}")
    elif a.cmd == "split":
        target = tree.split(a.section, a.to)
        print(f"split {a.section} -> {target}; commit with '{tree.slug}/- SPLIT: {a.section} to {target}'")
    elif a.cmd == "merge":
        host = tree.merge(a.section)
        print(f"merged {a.section} back into {host}")
    elif a.cmd == "export":
        out = tree.export()
        print(f"exported {out}")
    elif a.cmd == "budget":
        notes = tree.budget_report()
        print("\n".join(notes) if notes else "within budget")
    elif a.cmd == "version":
        print(tree.version_block())
    elif a.cmd == "relink":
        notes = tree.relink()
        tree.build_index()
        print("\n".join(notes) if notes else "links already current")
    elif a.cmd == "bump":
        print(f"{a.file}: v{tree.bump(a.file)}")
        tree.build_index()


if __name__ == "__main__":
    main()
