#!/usr/bin/env python3
"""rp: one entry point for the pipeline tools.

  rp doc ...        scripts/doc.py
  rp check ...      scripts/ref_checker.py
  rp state ...      scripts/state.py
  rp review ...     scripts/review.py
  rp commit ...     scripts/commit.py
  rp hook <name>    scripts/hooks.py
  rp selftest       scripts/selftest.sh
  rp where          print the tool root

Most subcommands take a project path; use `.` inside a project.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "doc":
        import doc; return doc.main(rest)
    if cmd == "check":
        import ref_checker; return ref_checker.main(rest)
    if cmd == "state":
        import state; return state.main(rest)
    if cmd == "review":
        import review; return review.main(rest)
    if cmd == "commit":
        import commit; return commit.main(rest)
    if cmd == "hook":
        import hooks; return hooks.main(rest)
    if cmd == "selftest":
        return subprocess.call(["bash", str(HERE / "selftest.sh"), *rest])
    if cmd == "where":
        print(HERE.parent); return 0
    print(f"rp: unknown command {cmd}\n{__doc__}")
    return 2


if __name__ == "__main__":
    sys.exit(main() or 0)
