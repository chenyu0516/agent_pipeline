"""pipelib: document tree, index, ledger, git helpers.

Normative rules live in stages/REFS.md. This module implements them and nothing more.
All CLIs (doc.py, ref_checker.py, state.py, review.py, hooks.py) build on this.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

TOOL_ROOT = Path(__file__).resolve().parent.parent      # the agent_pipeline repo, where the tools and templates live
ROOT = TOOL_ROOT
TEMPLATES = TOOL_ROOT / "stages" / "templates"
INTAKE = TOOL_ROOT / "stages" / "intake"
GLOBAL_LOG = Path(os.environ.get("AGENT_PIPELINE_GLOBAL_LOG") or TOOL_ROOT / "REJECTED-global.md")

# A project is its own git repository with this layout (REFS section 1):
#   docs/            design tree (DESIGN.md, split files), REGISTRY.md, REJECTED.md, DEFERRED.md
#   docs/inputs/     seed.md scribble.md data.md questions.md
#   docs/reviews/    <step>-r<n>.md, <step>-in<n>.md, ext-r<n>.md
#   docs/export/     <slug>-full.md
#   src/ scripts/ runs/
#   .pipeline/       state.yaml INDEX.yaml template.yaml attempts/ tool_root (gitignored)
DESIGN_EXCLUDE_DIRS = {"inputs", "reviews", "export"}
DESIGN_EXCLUDE_FILES = {"REGISTRY.md", "REJECTED.md", "DEFERRED.md", "README.md"}


class P:
    """Paths inside one project."""

    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.docs = self.root / "docs"
        self.inputs = self.docs / "inputs"
        self.reviews = self.docs / "reviews"
        self.export = self.docs / "export"
        self.registry = self.docs / "REGISTRY.md"
        self.rejected = self.docs / "REJECTED.md"
        self.deferred = self.docs / "DEFERRED.md"
        self.pipeline = self.root / ".pipeline"
        self.state = self.pipeline / "state.yaml"
        self.index = self.pipeline / "INDEX.yaml"
        self.template = self.pipeline / "template.yaml"
        self.attempts = self.pipeline / "attempts"
        self.tool_root = self.pipeline / "tool_root"

    @property
    def slug(self) -> str:
        return self.root.name


def find_project(start: Path | None = None) -> Path:
    """Walk up from start (default cwd) to the directory holding .pipeline/state.yaml."""
    p = Path(start or Path.cwd()).resolve()
    while True:
        if (p / ".pipeline" / "state.yaml").exists():
            return p
        if p == p.parent:
            die(f"{start or Path.cwd()} is not inside a pipeline project (no .pipeline/state.yaml above it)")
        p = p.parent


def project_touched(staged: list[str]) -> bool:
    """True when staged paths touch the design tree, inputs, reviews, export, or the ledger."""
    return any(s == "docs" or s.startswith("docs/") or s.startswith(".pipeline/") for s in staged)

# ----------------------------------------------------------------------------- regexes
SECTION_RE = re.compile(r"^\s*<!--\s*section:\s*(§[\w.]+)\s*(?:\|\s*owner:\s*([\w·\-]+)\s*)?-->\s*$")
STUB_RE = re.compile(r"^\s*<!--\s*stub:\s*(§[\w.]+)\s*\|\s*file:\s*([\w./\-]+)\s*-->\s*$")
OBJECT_RE = re.compile(r"^\s*<!--\s*object:\s*([A-Z]{1,2}\d+)\s*\|\s*(.*?)\s*-->\s*$")
FILE_RE = re.compile(r"^\s*<!--\s*file:\s*([\w./\-]+)\s*\|\s*version:\s*v(\d+)\s*-->\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s#]*)#([^)\s]+)\)")
CONTEXT_RE = re.compile(r"^>\s*\*\*Context\.\*\*\s*(.*)$")
PENDING_RE = re.compile(r"^\[pending:\s*step\s+[\w·\-]+\]$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
INLINE_CODE_RE = re.compile(r"`[^`]*`")
MATH_RE = re.compile(r"\$\$.*?\$\$|\$[^$\n]*\$", re.S)
LINK_TARGET_RE = re.compile(r"\]\([^)]*\)")

BANNED = [
    "previously", "originally", "we changed", "was rejected", "instead of the earlier",
    "as before", "updated to", "formerly", "no longer", "used to",
]
KIND_WORDS = {
    "assumption", "result", "prediction", "hypothesis", "feature", "metric", "symbol",
    "requirement", "component", "interface", "test", "decision", "term", "fixture",
    "measure", "check", "acceptance",
}
ORDINALS = {
    "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth",
    "tenth", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
}

VERBS = [
    "PASS", "REJECT", "HUMAN", "INTAKE", "REVIEW", "IMPORT", "APPLY", "WAIVE", "LOOP",
    "REWIND", "STALE", "SPLIT", "EXPORT", "REJECT-LOG", "INIT",
]
COMMIT_RE = re.compile(
    r"^(?P<slug>[a-z0-9][a-z0-9_\-]*)/(?P<step>[0-9][a-z](?:[·.\-]in)?|-) "
    r"(?P<verb>" + "|".join(re.escape(v) for v in VERBS) + r")"
    r"(?: a(?P<attempt>\d+))?"
    r"(?: (?P<review>(?:[0-9][a-z]|ext)-(?:r|in)\d+))?"
    r": (?P<msg>.{1,72})$"
)
REVIEW_ID_RE = re.compile(r"^(?:[0-9][a-z]|ext)-(?:r|in)\d+$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_\-]*$")
STEP_RE = re.compile(r"^(?:[0-9][a-z](?:[·.\-]in)?|-)$")


def suggest_slug(text: str) -> str:
    """The nearest slug the commit grammar accepts: lowercase, digits, hyphens, underscores."""
    s = re.sub(r"[^a-z0-9_]+", "-", text.strip().lower()).strip("-_")
    return s or "project"


def explain_commit(msg: str) -> str:
    """Why a message fails COMMIT_RE, one actionable line per fault, then a corrected example."""
    first = msg.strip().splitlines()[0] if msg.strip() else ""
    out: list[str] = []
    head, sep, rest = first.partition(": ")
    if not sep:
        out.append("missing ': ' (colon and space) between the verb and the one-line summary")
        head, rest = first, ""
    parts = head.split(" ")
    slug, slash, step = parts[0].partition("/")
    i = 1
    if not slash:
        out.append("missing '/' after the slug; the form is <slug>/<step>")
        if len(parts) > 1 and STEP_RE.match(parts[1]):
            step, i = parts[1], 2
    if not SLUG_RE.match(slug):
        out.append(f"slug '{slug}' may use only lowercase letters, digits, hyphens and underscores; try '{suggest_slug(slug)}'")
    if slash and not STEP_RE.match(step):
        out.append(f"step '{step}' must be a step id such as 2a or 2a-in, or '-' for INIT, SPLIT, EXPORT, REJECT-LOG, STALE")
    verb = parts[i] if len(parts) > i else ""
    if verb not in VERBS:
        hint = f"; did you mean {verb.upper()}" if verb.upper() in VERBS else ""
        out.append(f"verb '{verb}' is not one of: {', '.join(VERBS)}{hint}")
    tail = parts[i + 1:]
    if not sep:
        # without a colon, the summary is whatever follows the tags; do not flag its words
        n = 0
        while n < len(tail) and (re.fullmatch(r"a\d+", tail[n]) or REVIEW_ID_RE.match(tail[n])):
            n += 1
        rest, tail = " ".join(tail[n:]), tail[:n]
    for x in tail:
        if not (re.fullmatch(r"a\d+", x) or REVIEW_ID_RE.match(x)):
            out.append(f"'{x}' is neither an attempt tag such as a2 nor a review id such as 2f-r1")
    if sep and not 1 <= len(rest) <= 72:
        out.append(f"summary is {len(rest)} characters; the limit is 72")
    if not out:
        out.append("the parts are out of order; the form is <slug>/<step> <VERB>[ a<n>][ <review-id>]: <summary>")
    ex_step = step if STEP_RE.match(step) else "-"
    ex_verb = verb if verb in VERBS else (verb.upper() if verb.upper() in VERBS else "INIT")
    ex_rest = rest[:72] if rest else "one line on what changed"
    out.append(f"example: {suggest_slug(slug)}/{ex_step} {ex_verb}: {ex_rest}")
    return "\n".join(out)


# ----------------------------------------------------------------------------- small helpers
def norm_sid(s: str) -> str:
    """Accept 'problem' or 'model.notation' as well as '§problem'."""
    s = s.strip()
    return s if s.startswith("§") or not s else "§" + s


def norm_step(s: str) -> str:
    """Accept '2a-in' or '2a.in' as well as '2a·in'."""
    return re.sub(r"[.\-]in$", "·in", s.strip())


def sha(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def slugify(text: str) -> str:
    t = text.strip().lower()
    t = re.sub(r"[^\w\s-]", "", t)
    return t.replace(" ", "-")


def today() -> str:
    return _dt.date.today().isoformat()


def die(msg: str, code: int = 2):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def strip_prose(text: str) -> str:
    """Remove everything that is not prose: comments, fenced code, inline code, math, link targets."""
    out = []
    in_fence = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        out.append(line)
    t = "\n".join(out)
    t = COMMENT_RE.sub(" ", t)
    t = MATH_RE.sub(" ", t)
    t = INLINE_CODE_RE.sub(" ", t)
    t = LINK_TARGET_RE.sub("]", t)
    return t


def sentences(text: str) -> int:
    return len([s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()])


def shingles(text: str, n: int) -> set[tuple[str, ...]]:
    words = re.findall(r"[a-z0-9]+", strip_prose(text).lower())
    return {tuple(words[i : i + n]) for i in range(0, max(0, len(words) - n + 1))}


def read_yaml(path: Path, default=None):
    if not path.exists():
        return default if default is not None else {}
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or (default if default is not None else {})


def write_yaml(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True, width=120)


# ----------------------------------------------------------------------------- templates
class Template:
    def __init__(self, name: str | None = None, path: Path | None = None):
        if path is None:
            path = TEMPLATES / f"{name}.yaml"
        if not path.exists():
            die(f"no template {name or path}")
        self.raw = read_yaml(path)
        self.name = self.raw.get("name", name or path.stem)
        self.budget = self.raw.get("budget", {"lines": 400, "child_lines": 60, "child_count": 3})
        self.kinds = self.raw.get("kinds", {})
        self.steps = self.raw.get("steps", {})
        self.step_order = self.raw.get("step_order", list(self.steps))
        self.inputs = self.raw.get("inputs", {})
        self.flat: list[dict] = []
        self._flatten(self.raw.get("sections", []), 2, None)

    def _flatten(self, secs, level, parent):
        for s in secs:
            entry = {"id": s["id"], "title": s["title"], "owner": s.get("owner", "-"), "level": level, "parent": parent}
            self.flat.append(entry)
            self._flatten(s.get("children", []), level + 1, s["id"])

    def section(self, sid: str) -> dict | None:
        return next((s for s in self.flat if s["id"] == sid), None)

    def owner_of(self, sid: str) -> str:
        s = self.section(sid)
        return s["owner"] if s else "-"

    def outputs_of(self, step: str) -> list[str]:
        return list(self.steps.get(step, {}).get("outputs", []))

    def stage_of(self, step: str) -> str:
        return self.steps.get(step, {}).get("stage", "-")

    def prefixes(self) -> list[str]:
        return sorted(self.kinds, key=len, reverse=True)

    def kind_of(self, oid: str) -> dict | None:
        m = re.match(r"^([A-Z]{1,2})\d+$", oid)
        if not m:
            return None
        return self.kinds.get(m.group(1))

    def steps_from(self, step: str) -> list[str]:
        """Steps at or after `step` in the order, within the same stage."""
        if step not in self.step_order:
            return []
        i = self.step_order.index(step)
        stage = self.stage_of(step)
        return [s for s in self.step_order[i:] if self.stage_of(s) == stage]


# ----------------------------------------------------------------------------- document model
@dataclass
class Heading:
    level: int
    text: str
    anchor: str
    line: int
    kind: str = "plain"  # plain | section | stub | object
    end: int = 0


@dataclass
class Section:
    id: str
    owner: str
    file: str
    level: int
    heading: str
    anchor: str
    start: int
    end: int
    hash: str
    parent: str | None = None
    children: list[str] = field(default_factory=list)
    objects: list[str] = field(default_factory=list)
    pending: bool = False


@dataclass
class Stub:
    id: str
    file: str
    target: str
    level: int
    heading: str
    anchor: str
    start: int
    end: int
    summary_pending: bool


@dataclass
class Obj:
    id: str
    name: str
    kind: str
    tag: str | None
    tests: str | None
    file: str
    anchor: str
    section: str | None
    level: int
    start: int
    end: int
    hash: str


@dataclass
class Link:
    file: str
    line: int
    text: str
    path: str
    anchor: str
    section: str | None


@dataclass
class DocFile:
    rel: str
    path: Path
    lines: list[str]
    title: str | None = None
    decl_name: str | None = None
    version: int | None = None
    decl_line: int | None = None
    context: str | None = None
    headings: list[Heading] = field(default_factory=list)
    sections: list[str] = field(default_factory=list)
    stubs: list[str] = field(default_factory=list)
    objects: list[str] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    anchors: dict[str, list[Heading]] = field(default_factory=dict)


def own_text_of(lines: list[str], start: int, end: int, children: list[tuple[int, int]]) -> str:
    keep = []
    for i in range(start, end):
        if any(cs <= i < ce for cs, ce in children):
            continue
        keep.append(lines[i])
    return "\n".join(keep)


def sections_in_text(lines: list[str]) -> dict[str, dict]:
    """Lightweight section map of raw markdown lines: sid -> {level, start, end, own}. Used to diff against HEAD."""
    heads = []
    in_fence = False
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING_RE.match(line)
        if m:
            nxt = next((lines[k] for k in range(i + 1, min(i + 4, len(lines))) if lines[k].strip()), "")
            sm = SECTION_RE.match(nxt)
            heads.append((i, len(m.group(1)), sm.group(1) if sm else None))
    out = {}
    for idx, (line, level, sid) in enumerate(heads):
        end = len(lines)
        for l2, lv2, _ in heads[idx + 1 :]:
            if lv2 <= level:
                end = l2
                break
        if sid:
            out[sid] = {"level": level, "start": line, "end": end}
    for sid, s in out.items():
        kids = [(c["start"], c["end"]) for cid, c in out.items() if cid != sid and s["start"] < c["start"] < s["end"]]
        s["own"] = own_text_of(lines, s["start"], s["end"], kids)
    return out


def _parse_kv(s: str) -> dict:
    out = {}
    for part in s.split("|"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip()] = v.strip()
    return out


class Tree:
    """The design document tree of one project: <project>/docs, excluding inputs, reviews, export, and logs."""

    def __init__(self, project: Path, template: str | None = None):
        self.project = Path(project).resolve()
        self.paths = P(self.project)
        self.slug = read_yaml(self.paths.state, {}).get("slug") or self.project.name
        self.docs = self.paths.docs
        self.index_path = self.paths.index
        self.index = read_yaml(self.index_path, {})
        if self.paths.template.exists():
            self.template = Template(path=self.paths.template)
        else:
            tname = template or self.index.get("template") or read_yaml(self.paths.state, {}).get("template")
            if not tname:
                die(f"{self.project}: no template in .pipeline/template.yaml, INDEX.yaml, or state.yaml")
            self.template = Template(tname)
        self.files: dict[str, DocFile] = {}
        self.sections: dict[str, Section] = {}
        self.stubs: dict[str, Stub] = {}
        self.objects: dict[str, Obj] = {}
        self.scan()

    # ---- scanning
    def doc_files(self) -> list[Path]:
        out = []
        for p in sorted(self.docs.rglob("*.md")):
            rel = p.relative_to(self.docs)
            if rel.parts[0] in DESIGN_EXCLUDE_DIRS or p.name in DESIGN_EXCLUDE_FILES:
                continue
            out.append(p)
        return out

    def scan(self):
        self.files, self.sections, self.stubs, self.objects = {}, {}, {}, {}
        for p in self.doc_files():
            self._parse(p)
        # parents by extent containment within a file, then by dotted id across files
        for sid, s in self.sections.items():
            if "." in sid:
                parent = sid.rsplit(".", 1)[0]
                if parent in self.sections:
                    s.parent = parent
                    self.sections[parent].children.append(sid)
        for oid, o in self.objects.items():
            if o.section and o.section in self.sections:
                self.sections[o.section].objects.append(oid)

    def _parse(self, path: Path):
        rel = str(path.relative_to(self.docs))
        lines = path.read_text(encoding="utf-8").split("\n")
        f = DocFile(rel=rel, path=path, lines=lines)
        in_fence = False
        heads: list[Heading] = []
        for i, line in enumerate(lines):
            if FENCE_RE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            m = FILE_RE.match(line)
            if m and f.decl_line is None:
                f.decl_name, f.version, f.decl_line = m.group(1), int(m.group(2)), i
                continue
            m = CONTEXT_RE.match(line)
            if m and f.context is None:
                ctx = [m.group(1)]
                j = i + 1
                while j < len(lines) and lines[j].startswith(">"):
                    ctx.append(lines[j].lstrip("> ").rstrip())
                    j += 1
                f.context = " ".join(ctx).strip()
                continue
            m = HEADING_RE.match(line)
            if m:
                level, text = len(m.group(1)), m.group(2).strip()
                if level == 1 and f.title is None:
                    f.title = text
                h = Heading(level=level, text=text, anchor=slugify(text), line=i)
                nxt = next((lines[k] for k in range(i + 1, min(i + 4, len(lines))) if lines[k].strip()), "")
                if SECTION_RE.match(nxt):
                    h.kind = "section"
                elif STUB_RE.match(nxt):
                    h.kind = "stub"
                elif OBJECT_RE.match(nxt):
                    h.kind = "object"
                heads.append(h)
        # extents
        for idx, h in enumerate(heads):
            h.end = len(lines)
            for h2 in heads[idx + 1 :]:
                if h2.level <= h.level:
                    h.end = h2.line
                    break
        f.headings = heads
        for h in heads:
            f.anchors.setdefault(h.anchor, []).append(h)
        # sections, stubs, objects
        sec_stack: list[Section] = []
        for h in heads:
            if h.level == 1:
                continue
            nxt_i = next((k for k in range(h.line + 1, min(h.line + 4, len(lines))) if lines[k].strip()), None)
            nxt = lines[nxt_i] if nxt_i is not None else ""
            if h.kind == "section":
                m = SECTION_RE.match(nxt)
                sid, owner = m.group(1), m.group(2) or self.template.owner_of(m.group(1))
                body = [l for l in lines[nxt_i + 1 : h.end] if l.strip()]
                # body excluding child section/object headings: pending if the only line is the pending marker
                own_body = []
                for k in range(nxt_i + 1, h.end):
                    hh = next((x for x in heads if x.line == k), None)
                    if hh:
                        break
                    if lines[k].strip():
                        own_body.append(lines[k].strip())
                pending = len(own_body) == 1 and bool(PENDING_RE.match(own_body[0]))
                s = Section(id=sid, owner=owner, file=rel, level=h.level, heading=h.text, anchor=h.anchor,
                            start=h.line, end=h.end, hash=sha("\n".join(lines[h.line : h.end])), pending=pending)
                if sid in self.sections:
                    # duplicate: keep first, record second as a fake id for the checker
                    self.sections[f"{sid}#dup@{rel}:{h.line}"] = s
                else:
                    self.sections[sid] = s
                f.sections.append(sid)
                sec_stack = [x for x in sec_stack if x.end > h.line and x.level < h.level] + [s]
            elif h.kind == "stub":
                m = STUB_RE.match(nxt)
                sid, target = m.group(1), m.group(2)
                body = [l.strip() for l in lines[nxt_i + 1 : h.end] if l.strip()]
                st = Stub(id=sid, file=rel, target=target, level=h.level, heading=h.text, anchor=h.anchor,
                          start=h.line, end=h.end, summary_pending=any(b == "[summary pending]" for b in body) or not body)
                self.stubs[sid] = st
                f.stubs.append(sid)
            elif h.kind == "object":
                m = OBJECT_RE.match(nxt)
                oid, kv = m.group(1), _parse_kv(m.group(2))
                enclosing = None
                for s in reversed(sec_stack):
                    if s.start < h.line < s.end:
                        enclosing = s.id
                        break
                o = Obj(id=oid, name=h.text, kind=kv.get("kind", "?"), tag=kv.get("tag"), tests=kv.get("tests"),
                        file=rel, anchor=h.anchor, section=enclosing, level=h.level, start=h.line, end=h.end,
                        hash=sha("\n".join(lines[h.line : h.end])))
                if oid in self.objects:
                    self.objects[f"{oid}#dup@{rel}:{h.line}"] = o
                else:
                    self.objects[oid] = o
                f.objects.append(oid)
            else:
                # plain heading: if it is at or below a section's level it may close it; handled by extents
                pass
        # links (outside fences)
        in_fence = False
        for i, line in enumerate(lines):
            if FENCE_RE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for m in LINK_RE.finditer(line):
                sec = self.section_at(rel, i, f)
                f.links.append(Link(file=rel, line=i, text=m.group(1), path=m.group(2), anchor=m.group(3), section=sec))
        self.files[rel] = f

    def own_text(self, sid: str) -> str:
        """A section's text excluding the extents of its child sections."""
        s = self.sections[sid]
        lines = self.files[s.file].lines
        return own_text_of(lines, s.start, s.end, [(self.sections[c].start, self.sections[c].end) for c in s.children if self.sections[c].file == s.file])

    def section_at(self, rel: str, line: int, f: DocFile | None = None) -> str | None:
        best = None
        for sid in (f or self.files[rel]).sections:
            s = self.sections.get(sid)
            if s and s.start <= line < s.end and (best is None or s.level > self.sections[best].level):
                best = sid
        return best

    # ---- lookup
    def anchor_targets(self, anchor: str) -> list[tuple[str, str, str]]:
        """All (file, kind, id_or_text) whose heading slug equals anchor."""
        out = []
        for rel, f in self.files.items():
            for h in f.anchors.get(anchor, []):
                if h.kind == "object":
                    oid = next((o for o in f.objects if self.objects[o].anchor == anchor and self.objects[o].file == rel), None)
                    out.append((rel, "object", oid or h.text))
                elif h.kind == "section":
                    sid = next((s for s in f.sections if self.sections[s].anchor == anchor and self.sections[s].file == rel), None)
                    out.append((rel, "section", sid or h.text))
                elif h.kind == "stub":
                    continue  # a stub is never a link target; the real section is elsewhere
                else:
                    out.append((rel, "heading", h.text))
        return out

    def resolve(self, query: str) -> dict | None:
        q = query.strip()
        if q in self.objects:
            return self._card_obj(self.objects[q])
        if q in self.sections:
            return self._card_sec(self.sections[q])
        if "§" + q in self.sections:
            return self._card_sec(self.sections["§" + q])
        if q.startswith("§"):
            return None
        anchor = q.split("#", 1)[1] if "#" in q else None
        if anchor:
            for o in self.objects.values():
                if o.anchor == anchor:
                    return self._card_obj(o)
            for s in self.sections.values():
                if s.anchor == anchor:
                    return self._card_sec(s)
            return None
        for o in self.objects.values():
            if o.name.lower() == q.lower():
                return self._card_obj(o)
        return None

    def _links_to(self, anchor: str) -> list[str]:
        out = set()
        for f in self.files.values():
            for l in f.links:
                if l.anchor == anchor:
                    out.add(l.section or f.rel)
        return sorted(out)

    def _card_obj(self, o: Obj) -> dict:
        f = self.files[o.file]
        return {
            "id": o.id, "name": o.name, "kind": o.kind, "tag": o.tag, "tests": o.tests,
            "file": o.file, "version": f.version, "section": o.section, "anchor": f"#{o.anchor}",
            "hash": o.hash, "linked_from": self._links_to(o.anchor),
            "text": "\n".join(f.lines[o.start : o.end]).rstrip(),
        }

    def _card_sec(self, s: Section) -> dict:
        f = self.files[s.file]
        return {
            "id": s.id, "name": s.heading, "kind": "section", "owner": s.owner, "file": s.file,
            "version": f.version, "anchor": f"#{s.anchor}", "hash": s.hash, "pending": s.pending,
            "children": s.children, "objects": s.objects, "linked_from": self._links_to(s.anchor),
            "text": "\n".join(f.lines[s.start : s.end]).rstrip(),
        }

    # ---- versions
    def versions(self) -> dict[str, int]:
        return {rel: (f.version or 0) for rel, f in sorted(self.files.items())}

    def version_block(self) -> str:
        head = git_head_short(self.project)
        return "\n".join([head] + [f"{rel}: v{v}" for rel, v in self.versions().items()])

    def file_key(self, arg: str) -> str:
        """Accept a docs-relative key (DESIGN.md), a project-relative path (docs/DESIGN.md), or an absolute path."""
        p = Path(arg)
        cands = [arg.strip()]
        try:
            cands.append(str((p if p.is_absolute() else Path.cwd() / p).resolve().relative_to(self.docs.resolve())))
        except ValueError:
            pass
        if not p.is_absolute():
            try:
                cands.append(str((self.project / p).resolve().relative_to(self.docs.resolve())))
            except ValueError:
                pass
        for c in cands:
            if c in self.files:
                return c
        die(f"no file '{arg}' under docs/; known files: {', '.join(sorted(self.files))}")

    def bump(self, rel: str) -> int:
        rel = self.file_key(rel)
        f = self.files[rel]
        if f.decl_line is None:
            die(f"{rel}: no file declaration to bump")
        new = (f.version or 0) + 1
        f.lines[f.decl_line] = f"<!-- file: {rel} | version: v{new} -->"
        f.path.write_text("\n".join(f.lines), encoding="utf-8")
        self.scan()
        return new

    # ---- section IO
    def get(self, sid: str) -> str:
        s = self.sections.get(sid)
        if not s:
            die(f"no section {sid}")
        return "\n".join(self.files[s.file].lines[s.start : s.end]).rstrip() + "\n"

    def put(self, sid: str, text: str, bump: bool = True) -> str:
        s = self.sections.get(sid)
        if not s:
            die(f"no section {sid}")
        f = self.files[s.file]
        new_lines = text.rstrip("\n").split("\n")
        marker = f"<!-- section: {sid} | owner: {s.owner} -->"
        if not (new_lines and HEADING_RE.match(new_lines[0])):
            new_lines = ["#" * s.level + " " + s.heading, marker] + new_lines
        elif not any(SECTION_RE.match(l) for l in new_lines[:3]):
            new_lines.insert(1, marker)
        # keep one blank line after the section
        f.lines[s.start : s.end] = new_lines + [""]
        f.path.write_text("\n".join(f.lines), encoding="utf-8")
        self.scan()
        if bump:
            self.bump(s.file)
        return s.file

    def append(self, sid: str, text: str, bump: bool = False):
        cur = self.get(sid).rstrip("\n").split("\n")
        # drop a pending marker if present
        cur = [l for l in cur if not PENDING_RE.match(l.strip())]
        cur.append(text.rstrip("\n"))
        self.put(sid, "\n".join(cur), bump=bump)

    # ---- index and registry
    def build_index(self) -> dict:
        objects = {}
        for oid, o in self.objects.items():
            if "#dup@" in oid:
                continue
            objects[oid] = {
                "name": o.name, "kind": o.kind, "tag": o.tag, "tests": o.tests, "section": o.section,
                "file": o.file, "anchor": f"#{o.anchor}", "hash": o.hash, "linked_from": self._links_to(o.anchor),
            }
        sections = {}
        for sid, s in self.sections.items():
            if "#dup@" in sid:
                continue
            sections[sid] = {"file": s.file, "owner": s.owner, "anchor": f"#{s.anchor}", "hash": s.hash,
                             "pending": s.pending, "stub_in": self.stubs[sid].file if sid in self.stubs else None}
        files = {rel: {"version": f.version, "title": f.title, "lines": len(f.lines)} for rel, f in sorted(self.files.items())}
        self.index = {
            "project": self.slug, "template": self.template.name, "budget": self.template.budget,
            "files": files, "sections": sections, "objects": objects,
        }
        write_yaml(self.index_path, self.index)
        self.write_registry()
        return self.index

    def write_registry(self):
        by_kind: dict[str, list[Obj]] = {}
        for oid, o in self.objects.items():
            if "#dup@" in oid:
                continue
            by_kind.setdefault(o.kind, []).append(o)
        out = ["# Registry", "", "<!-- generated by doc.py index; never edit. Names are what the document uses; ids are for pipeline files. -->", ""]
        for kind in sorted(by_kind):
            out += [f"## {kind}", "", "| name | id | tag | tests | defined in | linked from |", "|---|---|---|---|---|---|"]
            for o in sorted(by_kind[kind], key=lambda x: (int(re.sub(r"\D", "", x.id) or 0))):
                out.append(f"| [{o.name}]({o.file}#{o.anchor}) | {o.id} | {o.tag or ''} | {o.tests or ''} | {o.section or ''} | {', '.join(self._links_to(o.anchor))} |")
            out.append("")
        self.paths.registry.write_text("\n".join(out), encoding="utf-8")

    def registry_markdown(self) -> str:
        p = self.paths.registry
        return p.read_text(encoding="utf-8") if p.exists() else ""

    # ---- links
    def relink(self) -> list[str]:
        """Rewrite link paths to where anchors live now, link texts to current object names, and anchors of renamed
        objects (found through the previous INDEX.yaml). Returns notes."""
        notes = []
        prev_anchor_to_id = {str(v.get("anchor", "")).lstrip("#"): oid for oid, v in (self.index.get("objects") or {}).items()}
        for rel, f in self.files.items():
            changed = False
            for i, line in enumerate(f.lines):
                def fix(m):
                    nonlocal changed
                    text, path, anchor = m.group(1), m.group(2), m.group(3)
                    targets = [t for t in self.anchor_targets(anchor) if t[1] in ("object", "section")]
                    if not targets and anchor in prev_anchor_to_id and prev_anchor_to_id[anchor] in self.objects:
                        o = self.objects[prev_anchor_to_id[anchor]]
                        notes.append(f"{rel}:{i+1}: renamed object {o.id}: #{anchor} -> #{o.anchor}")
                        anchor = o.anchor
                        targets = [(o.file, "object", o.id)]
                    if len(targets) != 1:
                        return m.group(0)
                    tfile, tkind, tid = targets[0]
                    newpath = "" if tfile == rel else os.path.relpath(self.docs / tfile, (self.docs / rel).parent)
                    newtext = text
                    if tkind == "object" and tid in self.objects and text.lower() != self.objects[tid].name.lower():
                        newtext = self.objects[tid].name
                        notes.append(f"{rel}:{i+1}: link text '{text}' -> '{newtext}'")
                    if newpath != path:
                        notes.append(f"{rel}:{i+1}: link path '{path}' -> '{newpath}' for #{anchor}")
                    if newtext != text or newpath != path or anchor != m.group(3):
                        changed = True
                        return f"[{newtext}]({newpath}#{anchor})"
                    return m.group(0)
                f.lines[i] = LINK_RE.sub(fix, line)
            if changed:
                f.path.write_text("\n".join(f.lines), encoding="utf-8")
        if notes:
            self.scan()
        return notes

    # ---- split / merge / export
    def default_target(self, sid: str) -> str:
        s = self.sections[sid]
        last = sid.lstrip("§").split(".")[-1]
        host = Path(s.file)
        if host.name == "DESIGN.md":
            return f"{last}.md"
        return str(host.with_suffix("") / f"{last}.md")

    def split(self, sid: str, target: str | None = None) -> str:
        s = self.sections.get(sid)
        if not s:
            die(f"no section {sid}")
        if sid in self.stubs:
            die(f"{sid} is already split into {self.stubs[sid].target}")
        target = target or self.default_target(sid)
        tpath = self.docs / target
        if tpath.exists():
            die(f"{target} already exists")
        f = self.files[s.file]
        block = f.lines[s.start : s.end]
        delta = 2 - s.level
        moved = []
        in_fence = False
        for line in block:
            if FENCE_RE.match(line):
                in_fence = not in_fence
            m = HEADING_RE.match(line) if not in_fence else None
            if m:
                moved.append("#" * (len(m.group(1)) + delta) + " " + m.group(2))
            else:
                moved.append(line)
        children = [self.sections[c].heading for c in s.children]
        covers = s.heading + (" with " + ", ".join(children) if children else "")
        root_rel = os.path.relpath(self.docs / "DESIGN.md", tpath.parent)
        title = self.files["DESIGN.md"].title or self.slug
        context = (f"> **Context.** Part of {title}, see [{title}]({root_rel}#{slugify(title)}). "
                   f"Covers {covers}. Depends on the sections it links. Status: [summary pending].")
        header = [f"# {title}: {s.heading}", f"<!-- file: {target} | version: v1 -->", "", context, ""]
        tpath.parent.mkdir(parents=True, exist_ok=True)
        tpath.write_text("\n".join(header + moved).rstrip("\n") + "\n", encoding="utf-8")
        stub_rel = os.path.relpath(tpath, (self.docs / s.file).parent)
        stub = ["#" * s.level + " " + s.heading, f"<!-- stub: {sid} | file: {stub_rel} -->",
                "[summary pending]", f"See [{s.heading}]({stub_rel}#{s.anchor}).", ""]
        f.lines[s.start : s.end] = stub
        f.path.write_text("\n".join(f.lines), encoding="utf-8")
        self.scan()
        self.relink()
        self.build_index()
        return target

    def merge(self, sid: str) -> str:
        st = self.stubs.get(sid)
        if not st:
            die(f"{sid} is not split")
        host = self.files[st.file]
        tpath = (self.docs / st.file).parent / st.target
        child = self.files[str(tpath.resolve().relative_to(self.docs))]
        # body after context
        start = 0
        for i, line in enumerate(child.lines):
            if CONTEXT_RE.match(line):
                start = i + 1
                while start < len(child.lines) and child.lines[start].startswith(">"):
                    start += 1
                break
        body = child.lines[start:]
        delta = st.level - 2
        merged, in_fence = [], False
        for line in body:
            if FENCE_RE.match(line):
                in_fence = not in_fence
            m = HEADING_RE.match(line) if not in_fence else None
            merged.append("#" * (len(m.group(1)) + delta) + " " + m.group(2) if m else line)
        while merged and not merged[0].strip():
            merged.pop(0)
        host.lines[st.start : st.end] = merged + [""]
        host.path.write_text("\n".join(host.lines), encoding="utf-8")
        tpath.unlink()
        self.scan()
        self.relink()
        self.bump(host.rel)
        self.build_index()
        return host.rel

    def export(self) -> Path:
        def body_of(rel: str, level_shift: int) -> list[str]:
            f = self.files[rel]
            start = 0
            for i, line in enumerate(f.lines):
                if CONTEXT_RE.match(line):
                    start = i + 1
                    while start < len(f.lines) and f.lines[start].startswith(">"):
                        start += 1
                    break
            return assemble(rel, f.lines[start:], level_shift)

        def assemble(rel: str, lines: list[str], level_shift: int) -> list[str]:
            out, i, in_fence = [], 0, False
            stubs_here = {st.start: st for st in self.stubs.values() if st.file == rel}
            while i < len(lines):
                # map back to original line index for stub lookup
                orig = i + (len(self.files[rel].lines) - len(lines))
                if orig in stubs_here and not in_fence:
                    st = stubs_here[orig]
                    trel = str(((self.docs / rel).parent / st.target).resolve().relative_to(self.docs))
                    out += body_of(trel, st.level + level_shift - 2)
                    i += st.end - st.start
                    continue
                line = lines[i]
                if FENCE_RE.match(line):
                    in_fence = not in_fence
                m = HEADING_RE.match(line) if not in_fence else None
                if m and level_shift:
                    line = "#" * (len(m.group(1)) + level_shift) + " " + m.group(2)
                if not in_fence:
                    line = LINK_RE.sub(lambda mm: f"[{mm.group(1)}](#{mm.group(3)})", line)
                    line = STUB_RE.sub("", line)
                out.append(line)
                i += 1
            return out

        root = self.files["DESIGN.md"]
        head = [f"# {root.title}", f"<!-- export of {self.slug} at {git_head_short(self.project)}; versions: "
                + ", ".join(f"{r} v{v}" for r, v in self.versions().items()) + " -->", ""]
        ctx = [l for l in root.lines if CONTEXT_RE.match(l)]
        content = head + ctx + [""] + body_of("DESIGN.md", 0)
        reg = self.registry_markdown().replace("# Registry", "## Registry (generated)", 1)
        reg = re.sub(r"\]\(([^)#]+)#", "](#", reg)
        content += ["", "---", "", reg]
        out = self.paths.export / f"{self.slug}-full.md"
        out.parent.mkdir(exist_ok=True)
        out.write_text("\n".join(content).rstrip("\n") + "\n", encoding="utf-8")
        return out

    # ---- budgets
    def budget_report(self) -> list[str]:
        b = self.template.budget
        notes = []
        for rel, f in self.files.items():
            if len(f.lines) > b["lines"]:
                notes.append(f"{rel}: {len(f.lines)} lines over budget {b['lines']}; split candidate")
        for sid, s in self.sections.items():
            big = [c for c in s.children if (self.sections[c].end - self.sections[c].start) > b["child_lines"]]
            if len(big) >= b["child_count"] and sid not in self.stubs:
                notes.append(f"{sid}: {len(big)} children over {b['child_lines']} lines; split candidate")
        return notes


# ----------------------------------------------------------------------------- project creation
HOOK_SH = """#!/bin/sh
# Pipeline hook. Finds the agent_pipeline tools through $AGENT_PIPELINE_ROOT, then .pipeline/tool_root, then `rp` on PATH.
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT" || exit 1
TOOL="${AGENT_PIPELINE_ROOT:-}"
[ -z "$TOOL" ] && [ -f .pipeline/tool_root ] && TOOL="$(cat .pipeline/tool_root)"
if [ -n "$TOOL" ] && [ -f "$TOOL/scripts/hooks.py" ]; then
  exec uv run --quiet --project "$TOOL" python "$TOOL/scripts/hooks.py" %s "$@"
fi
if command -v rp >/dev/null 2>&1; then exec rp hook %s "$@"; fi
echo "pipeline hook: cannot find agent_pipeline tools; set AGENT_PIPELINE_ROOT or write .pipeline/tool_root" >&2; exit 1
"""


def init_project(slug: str, template_name: str, title: str | None = None, parent_dir: Path | None = None) -> Path:
    """Create a new project as its own git repository at <parent_dir>/<slug> (default: cwd/<slug>)."""
    if not SLUG_RE.match(slug):
        die(f"slug '{slug}' may use only lowercase letters, digits, hyphens and underscores, because every design commit "
            f"is named '<slug>/<step> <VERB>: ...'; try '{suggest_slug(slug)}'")
    t = Template(template_name)
    work = (Path(parent_dir).resolve() if parent_dir else Path.cwd()) / slug
    if work.exists():
        die(f"{work} already exists")
    pp = P(work)
    for d in (pp.docs, pp.inputs, pp.reviews, pp.attempts, work / "src", work / "scripts", work / "runs"):
        d.mkdir(parents=True)
    docs = pp.docs
    title = title or slug.replace("-", " ").title()
    lines = [f"# {title}", "<!-- file: DESIGN.md | version: v1 -->", "",
             f"> **Context.** {title} is a {t.name} project in the research pipeline. This file holds every section until one is split out. It depends on nothing yet. Status: initialized.", ""]
    for s in t.flat:
        lines += ["#" * s["level"] + " " + s["title"], f"<!-- section: {s['id']} | owner: {s['owner']} -->"]
        if s["id"] == "§context":
            lines += [f"{title}: one line on what this project is goes here. How to read: start at Problem; each section links the objects it uses. Status: initialized.", ""]
        elif s["id"] == "§status":
            lines += ["No reviews yet.", ""]
        elif any(x["parent"] == s["id"] for x in t.flat):
            lines += [""]
        else:
            lines += [f"[pending: step {s['owner']}]", ""]
    (docs / "DESIGN.md").write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")
    pp.rejected.write_text("# Rejected proposals\n\n<!-- append-only; one line per proposal; see REFS.md section 11 -->\n", encoding="utf-8")
    pp.deferred.write_text("# Deferred review items\n\n", encoding="utf-8")
    (pp.reviews / "external").mkdir()
    for name in t.inputs:
        src = INTAKE / name
        if src.exists():
            (pp.inputs / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    for d in ("src", "scripts", "runs"):
        (work / d / ".gitkeep").write_text("", encoding="utf-8")
    (work / "README.md").write_text(
        f"# {title}\n\nA pipeline project on the `{t.name}` template. Start at `docs/DESIGN.md`; the single-file export is `docs/export/{slug}-full.md`.\n"
        f"Reviews are in `docs/reviews/`, rejected proposals in `docs/REJECTED.md`. Code in `src/`, experiment scripts in `scripts/`, runs in `runs/`.\n"
        f"The ledger in `.pipeline/` is written by the agent_pipeline tools; commit with `rp commit \"{slug}/<step> <VERB>: ...\"`.\n",
        encoding="utf-8")
    (work / ".gitignore").write_text(".pipeline/tool_root\n__pycache__/\n*.pyc\n.venv/\n.DS_Store\n", encoding="utf-8")
    # template copy makes the project self-contained
    pp.template.write_text((TEMPLATES / f"{template_name}.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    pp.tool_root.write_text(str(TOOL_ROOT) + "\n", encoding="utf-8")
    state = {
        "slug": slug, "template": t.name, "stage": "ideate", "head": None, "versions": {"DESIGN.md": 1},
        "inputs": {name: {"hash": None, "intake": None, "status": "untouched"} for name in t.inputs},
        "steps": {}, "pending_review": None, "queued_reviews": [], "reviews": [], "loops": {}, "rejected_count": 0,
    }
    write_yaml(pp.state, state)
    # git repository with hooks
    hooks = work / ".githooks"
    hooks.mkdir()
    for name in ("pre-commit", "commit-msg", "post-commit"):
        h = hooks / name
        h.write_text(HOOK_SH % (name, name), encoding="utf-8")
        h.chmod(0o755)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(work), check=True)
    subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=str(work), check=True)
    tree = Tree(work, template=t.name)
    tree.build_index()
    return work


# ----------------------------------------------------------------------------- ledger
def state_path(project: Path) -> Path:
    return P(project).state


def load_state(project: Path) -> dict:
    st = read_yaml(state_path(project), {})
    if not st:
        die(f"{project}: no .pipeline/state.yaml")
    return st


def save_state(project: Path, st: dict):
    write_yaml(state_path(project), st)


def input_path(project: Path, name: str) -> Path:
    return P(project).inputs / name


def input_hash(project: Path, name: str) -> str | None:
    p = input_path(project, name)
    return sha(p.read_text(encoding="utf-8")) if p.exists() else None


def review_path(project: Path, rid: str) -> Path:
    return P(project).reviews / f"{rid}.md"


def review_rel(rid: str) -> str:
    return f"docs/reviews/{rid}.md"


def next_review_id(project: Path, step: str, kind: str) -> str:
    rdir = P(project).reviews
    prefix = "ext" if kind == "external" else step.replace("·in", "")
    tag = "in" if kind == "intake" else "r"
    n = 1
    while (rdir / f"{prefix}-{tag}{n}.md").exists():
        n += 1
    return f"{prefix}-{tag}{n}"


def next_log_id(project: Path) -> int:
    ids = [0]
    for p in [P(project).rejected, GLOBAL_LOG]:
        if p.exists():
            ids += [int(m) for m in re.findall(r"^R(\d+) \|", p.read_text(encoding="utf-8"), re.M)]
    return max(ids) + 1


def log_entries(project: Path, include_global: bool = True) -> list[dict]:
    out = []
    for p, scope in [(P(project).rejected, "project"), (GLOBAL_LOG, "global")]:
        if not (p.exists() and (include_global or scope == "project")):
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.startswith("R"):
                continue
            parts = [x.strip() for x in line.split("|")]
            if len(parts) < 6:
                continue
            e = {"id": parts[0], "date": parts[1], "review": parts[2], "target": parts[3], "scope": scope, "raw": line}
            for x in parts[4:]:
                if ":" in x:
                    k, v = x.split(":", 1)
                    e[k.strip()] = v.strip()
            e["revived"] = "revived" in e
            out.append(e)
    return out


def append_log(project: Path, review: str, target: str, proposal: str, verdict: str, reason: str, by: str) -> str:
    rid = f"R{next_log_id(project)}"
    line = f"{rid} | {today()} | {review} | {target} | proposal: {proposal} | {verdict}: {reason} | by: {by}"
    p = P(project).rejected
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    st = load_state(project)
    st["rejected_count"] = st.get("rejected_count", 0) + 1
    save_state(project, st)
    return rid


# ----------------------------------------------------------------------------- git
def git(args: list[str], cwd: Path | None = None, check: bool = True) -> str:
    r = subprocess.run(["git", *args], cwd=str(cwd or Path.cwd()), capture_output=True, text=True)
    if check and r.returncode != 0:
        die(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def git_root(path: Path) -> Path:
    return Path(git(["rev-parse", "--show-toplevel"], cwd=path))


def git_head_short(cwd: Path) -> str:
    r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(cwd), capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else "0000000"


def git_user(cwd: Path) -> str:
    return git(["config", "user.name"], cwd=cwd, check=False) or os.environ.get("USER", "human")


def git_dirty(cwd: Path, path: Path) -> list[str]:
    out = git(["status", "--porcelain", "--", str(path)], cwd=cwd)
    return [l for l in out.splitlines() if l.strip()]


def git_staged(cwd: Path) -> list[str]:
    return [l for l in git(["diff", "--cached", "--name-only"], cwd=cwd).splitlines() if l.strip()]


def git_show(cwd: Path, rev: str, rel: str) -> str | None:
    r = subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=str(cwd), capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def git_commit(cwd: Path, message: str, paths: list[Path]) -> str:
    git(["add", "--", *[str(p) for p in paths]], cwd=cwd)
    git(["commit", "-q", "-m", message], cwd=cwd)
    return git_head_short(cwd)


def git_log_for(cwd: Path, path: Path, n: int = 200) -> list[tuple[str, str]]:
    out = git(["log", f"-n{n}", "--format=%h%x09%s", "--", str(path)], cwd=cwd, check=False)
    return [tuple(l.split("\t", 1)) for l in out.splitlines() if "\t" in l]


def parse_commit(msg: str) -> dict | None:
    m = COMMIT_RE.match(msg.strip().splitlines()[0] if msg.strip() else "")
    if not m:
        return None
    d = m.groupdict()
    d["step"] = norm_step(d["step"]) if d["step"] != "-" else "-"
    return d


def format_commit(slug: str, step: str, verb: str, msg: str, attempt: int | None = None, review: str | None = None) -> str:
    s = f"{slug}/{step} {verb}"
    if attempt is not None:
        s += f" a{attempt}"
    if review:
        s += f" {review}"
    return f"{s}: {msg[:72]}"


def projects_touched(paths: list[str], root: Path) -> list[Path]:
    """The project is the repository. Returns [root] when staged paths touch the design tree or ledger."""
    return [root] if (root / ".pipeline" / "state.yaml").exists() and project_touched(paths) else []
