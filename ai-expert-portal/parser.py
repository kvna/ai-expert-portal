"""Parses the AIExpert workspace's markdown files into structured data for the portal.

The workspace markdown files are the single source of truth (git-tracked, already
the audit trail AIExpert itself maintains). This module only reads them; writes
happen through the narrow, line-level functions at the bottom, which touch only
the one field being changed and leave everything else in the file byte-for-byte
identical.
"""
import os
import re
import markdown as _markdown

_MD = _markdown.Markdown(extensions=["extra", "sane_lists"])


def render_md(text: str) -> str:
    """Render a markdown fragment to HTML. Resets the parser's internal state first."""
    _MD.reset()
    return _MD.convert(text or "")


def render_md_inline(text: str) -> str:
    """Render a single line of markdown (links, bold, code) without wrapping <p> tags,
    for use inside a <dd> or other inline context."""
    html = render_md(text)
    if html.startswith("<p>") and html.endswith("</p>"):
        html = html[3:-4]
    return html


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def ledger_entry_slug(header: str) -> str:
    """Extract the canonical slug from a ledger header, e.g.
    '2026-09-10 openai-agents-api — OpenAI ships...' -> 'openai-agents-api'.
    This is the same slug used everywhere else in the workspace to refer to
    the entry (Evidence/Linked fields), so IDs built this way are addressable.
    Falls back to a full slugify if a header doesn't match the usual shape."""
    m = re.match(r"^\S+\s+([a-zA-Z][a-zA-Z0-9.-]*)\s+—", header)
    return m.group(1) if m else slugify(header)[:80]


def playbook_entry_slug(header: str) -> str:
    """Extract the canonical slug from a playbook header, e.g.
    'instructions-are-not-controls — Treat every...' -> 'instructions-are-not-controls'."""
    m = re.match(r"^([a-zA-Z][a-zA-Z0-9.-]*)\s+—", header)
    return m.group(1) if m else slugify(header)[:80]


_TAB_FOR_FILE = {
    "ledger.md": "findings",
    "playbook.md": "playbook",
    "changelog.md": "implementations",
    "backlog.md": "recommendations",
    "regression-log.md": "regression",
}

_MD_LINK_TARGET_RE = re.compile(r"(\]\()([^)]+)(\))")


def rewrite_internal_links(text: str, base_dir: str) -> str:
    """Rewrite relative markdown links to other workspace files so they resolve
    inside the portal's single-page layout instead of 404ing against a Flask
    route that doesn't exist (e.g. a raw `ledger.md` link goes nowhere here).

    base_dir is the directory the source file lives in relative to the
    workspace root (e.g. "knowledge", "exercises"), needed to resolve a
    relative target like "../knowledge/ledger.md" correctly. A link to a file
    that has its own portal tab jumps to that tab (`#tab-<name>`); anything
    else (EX-001-results.md, evaluation.md, TEMPLATE.md, ...) is routed
    through /raw/ so it at least resolves to real content instead of nothing.
    """
    if not text:
        return text

    def repl(m):
        prefix, target, suffix = m.group(1), m.group(2), m.group(3)
        if target.startswith(("http://", "https://", "#", "mailto:")):
            return m.group(0)
        basename = target.split("/")[-1]
        if basename in _TAB_FOR_FILE:
            return f"{prefix}#tab-{_TAB_FOR_FILE[basename]}{suffix}"
        resolved = os.path.normpath(os.path.join(base_dir, target)).replace(os.sep, "/")
        return f"{prefix}/raw/{resolved}{suffix}"

    return _MD_LINK_TARGET_RE.sub(repl, text)


def rewrite_fields(fields, base_dir: str):
    return [(k, rewrite_internal_links(v, base_dir)) for k, v in fields]


_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def split_sections(text: str, marker: str = "## "):
    """Split a markdown file into (header_line, body_text) pairs on a heading marker.

    Returns (preamble, sections) where preamble is any text before the first
    matching heading and sections is a list of (header, body). HTML comments
    are stripped first, since schema-documentation comments in these files
    contain an example heading line that would otherwise be parsed as a
    spurious first section.
    """
    text = _HTML_COMMENT_RE.sub("", text)
    lines = text.split("\n")
    sections = []
    preamble_lines = []
    current_header = None
    current_body = []
    for line in lines:
        if line.startswith(marker):
            if current_header is not None:
                sections.append((current_header, "\n".join(current_body).strip("\n")))
            elif preamble_lines is not None:
                preamble = "\n".join(preamble_lines)
            current_header = line[len(marker):].strip()
            current_body = []
            preamble_lines = None
        else:
            if current_header is None:
                preamble_lines.append(line)
            else:
                current_body.append(line)
    if current_header is not None:
        sections.append((current_header, "\n".join(current_body).strip("\n")))
    preamble = "\n".join(preamble_lines) if preamble_lines is not None else ""
    return preamble, sections


_FIELD_RE = re.compile(r"^- ([^:]+):\s?(.*)$")


def parse_bullet_fields(body: str):
    """Parse a body of `- Key: value` bullet lines into an ordered list of (key, value).

    A non-bullet, non-blank line following a field is treated as a continuation
    of that field's value (handles the rare wrapped line without corrupting
    later fields).
    """
    fields = []
    for raw_line in body.split("\n"):
        line = raw_line.rstrip()
        if not line.strip():
            continue
        # Skip markdown comments (schema headers) entirely.
        if line.strip().startswith("<!--") or line.strip().startswith("-->"):
            continue
        m = _FIELD_RE.match(line)
        if m:
            fields.append([m.group(1).strip(), m.group(2).strip()])
        elif fields and not line.startswith("#"):
            fields[-1][1] = (fields[-1][1] + " " + line.strip()).strip()
    return [(k, v) for k, v in fields]


def get_field(fields, key, default=""):
    for k, v in fields:
        if k.strip().lower() == key.strip().lower():
            return v
    return default


def get_field_startswith(fields, prefix, default=""):
    for k, v in fields:
        if k.strip().lower().startswith(prefix.strip().lower()):
            return v
    return default


def status_keyword(raw_status: str) -> str:
    """Pull the leading status keyword out of a status field like
    'in-progress (Claude leg complete...)' -> 'in-progress'."""
    if not raw_status:
        return ""
    m = re.match(r"^([a-zA-Z-]+)", raw_status.strip())
    return m.group(1).lower() if m else raw_status.strip().lower()


# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------

def parse_ledger(text: str):
    _preamble, sections = split_sections(text)
    entries = []
    for header, body in sections:
        fields = rewrite_fields(parse_bullet_fields(body), "knowledge")
        raw_status = get_field(fields, "Status")
        entries.append({
            "id": ledger_entry_slug(header),
            "title": header,
            "fields": fields,
            "eli10": get_field_startswith(fields, "Explain it like"),
            "status_raw": raw_status,
            "status": status_keyword(raw_status) or "unknown",
            "linked": get_field_startswith(fields, "Linked exercises"),
        })
    return list(reversed(entries))  # most recently added first


# ---------------------------------------------------------------------------
# Playbook
# ---------------------------------------------------------------------------

def parse_playbook(text: str):
    _preamble, sections = split_sections(text)
    entries = []
    for header, body in sections:
        fields = rewrite_fields(parse_bullet_fields(body), "knowledge")
        entries.append({
            "id": playbook_entry_slug(header),
            "title": header,
            "fields": fields,
            "eli10": get_field_startswith(fields, "Explain it like"),
            "confidence": status_keyword(get_field(fields, "Confidence")) or "unknown",
            "status": status_keyword(get_field(fields, "Status")) or "active",
        })
    return entries


# ---------------------------------------------------------------------------
# Backlog / exercises
# ---------------------------------------------------------------------------

EXERCISE_STATUSES = ["proposed", "accepted", "in-progress", "completed", "retired"]


def parse_backlog(text: str):
    _preamble, sections = split_sections(text)
    exercises = []
    for header, body in sections:
        m = re.match(r"^([A-Za-z0-9-]+)\s*—\s*(.*)$", header)
        ex_id = m.group(1) if m else header
        title = m.group(2) if m else ""
        fields = rewrite_fields(parse_bullet_fields(body), "exercises")
        raw_status = get_field(fields, "Status")
        exercises.append({
            "id": ex_id,
            "title": title,
            "header": header,
            "fields": fields,
            "eli10": get_field_startswith(fields, "Explain it like"),
            "status_raw": raw_status,
            "status": status_keyword(raw_status) or "proposed",
        })
    return exercises


def update_exercise_status(path: str, exercise_id: str, new_status: str) -> bool:
    """Rewrite only the `- Status:` line of the named exercise's section, leaving
    every other line in the file untouched. Returns True if a change was made."""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    in_target_section = False
    changed = False
    header_re = re.compile(r"^## " + re.escape(exercise_id) + r"\b")
    any_header_re = re.compile(r"^## ")
    status_re = re.compile(r"^(- Status:\s*)(.*)$")

    for i, line in enumerate(lines):
        if header_re.match(line):
            in_target_section = True
            continue
        if in_target_section and any_header_re.match(line):
            break
        if in_target_section:
            m = status_re.match(line)
            if m:
                lines[i] = f"{m.group(1)}{new_status}\n"
                changed = True
                break

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    return changed


# ---------------------------------------------------------------------------
# Proposals
# ---------------------------------------------------------------------------

PROPOSAL_STATUSES = ["proposed", "approved", "rejected", "implemented", "rolled-back"]


def parse_proposal(text: str, filename: str):
    title_m = re.match(r"^# AIExpert improvement proposal:\s*(.*)$", text.split("\n", 1)[0])
    title = title_m.group(1) if title_m else filename

    _preamble, sections = split_sections(text)
    body_before_sections = text.split("\n", 1)[1] if "\n" in text else ""
    # Everything up to the first "## " heading is the field list.
    field_block = body_before_sections.split("\n## ", 1)[0]
    fields = rewrite_fields(parse_bullet_fields(field_block), "proposals")
    raw_status = get_field(fields, "Status")

    decision = ""
    patch = ""
    for header, body in sections:
        if header.strip().lower() == "decision":
            decision = rewrite_internal_links(body.strip(), "proposals")
        elif "patch" in header.strip().lower():
            patch = body.strip()

    return {
        "id": filename,
        "title": title,
        "fields": fields,
        "eli10": get_field_startswith(fields, "Explain it like"),
        "status_raw": raw_status,
        "status": status_keyword(raw_status) or "proposed",
        "decision": decision,
        "patch": patch,
    }


def update_proposal_status(path: str, new_status: str) -> bool:
    """Rewrite only the `- Status:` line at the top of the proposal file."""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    status_re = re.compile(r"^(- Status:\s*)(.*)$")
    changed = False
    for i, line in enumerate(lines):
        m = status_re.match(line)
        if m:
            lines[i] = f"{m.group(1)}{new_status}\n"
            changed = True
            break

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    return changed


# ---------------------------------------------------------------------------
# Changelog (the implementation log)
# ---------------------------------------------------------------------------

def parse_changelog(text: str):
    _preamble, sections = split_sections(text)
    entries = []
    for header, body in sections:
        entries.append({
            "id": slugify(header)[:80],
            "title": header,
            "body_html": render_md(rewrite_internal_links(body, "knowledge")),
        })
    return list(reversed(entries))


# ---------------------------------------------------------------------------
# Regression log
# ---------------------------------------------------------------------------

def parse_regression_log(text: str):
    _preamble, sections = split_sections(text)
    entries = []
    for header, body in sections:
        entries.append({
            "id": slugify(header)[:80],
            "title": header,
            "body_html": render_md(rewrite_internal_links(body, "references")),
        })
    return list(reversed(entries))
