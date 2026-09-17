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
    that has its own portal tab jumps straight to the specific entry
    (`#<entry-slug>`) if the link already carries a `#fragment` (e.g.
    `ledger.md#openai-agents-api`), or to the tab in general (`#tab-<name>`)
    if it doesn't. Anything else (EX-001-results.md, evaluation.md,
    TEMPLATE.md, ...) is routed through /raw/<path>.html (note: .html, not
    .md -- see raw_url_for_md()).
    """
    if not text:
        return text

    def repl(m):
        prefix, target, suffix = m.group(1), m.group(2), m.group(3)
        if target.startswith(("http://", "https://", "#", "mailto:")):
            return m.group(0)
        target_path, _sep, fragment = target.partition("#")
        basename = target_path.split("/")[-1]
        if basename in _TAB_FOR_FILE:
            anchor = fragment if fragment else f"tab-{_TAB_FOR_FILE[basename]}"
            return f"{prefix}#{anchor}{suffix}"
        resolved = os.path.normpath(os.path.join(base_dir, target_path)).replace(os.sep, "/")
        frag_suffix = f"#{fragment}" if fragment else ""
        return f"{prefix}{raw_url_for_md(resolved)}{frag_suffix}{suffix}"

    return _MD_LINK_TARGET_RE.sub(repl, text)


def raw_url_for_md(relpath_md: str) -> str:
    """/raw/<relpath, .md replaced with .html>. Azure Static Web Apps' production
    edge (unlike its own CLI emulator) won't let a route's custom headers override
    Content-Type -- only the extension-keyed mimeTypes map does that, and it can't
    distinguish two different .md files that need two different content types
    (this HTML content vs. the genuinely-markdown agent-best-practices.md
    download). Serving these as .html sidesteps the conflict entirely: a real
    .html extension gets text/html by default, no override needed."""
    if relpath_md.endswith(".md"):
        relpath_md = relpath_md[: -len(".md")] + ".html"
    return f"/raw/{relpath_md}"


def raw_source_for_url(relpath_html: str) -> str:
    """Inverse of raw_url_for_md's extension swap, for the /raw/ route handler to
    find the actual .md source file on disk from the .html URL it was served at."""
    if relpath_html.endswith(".html"):
        return relpath_html[: -len(".html")] + ".md"
    return relpath_html


def rewrite_fields(fields, base_dir: str):
    return [(k, rewrite_internal_links(v, base_dir)) for k, v in fields]


_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


_FENCE_RE = re.compile(r"^\s*(```+|~~~+)")


def split_sections(text: str, marker: str = "## "):
    """Split a markdown file into (header_line, body_text) pairs on a heading marker.

    Returns (preamble, sections) where preamble is any text before the first
    matching heading and sections is a list of (header, body). HTML comments
    are stripped first, since schema-documentation comments in these files
    contain an example heading line that would otherwise be parsed as a
    spurious first section.

    Fence-aware: a marker-looking line inside a ``` or ~~~ fenced code block
    (e.g. an example agent instruction file's own "## Section" heading) is
    never treated as a real section boundary.
    """
    text = _HTML_COMMENT_RE.sub("", text)
    lines = text.split("\n")
    sections = []
    preamble_lines = []
    current_header = None
    current_body = []
    in_fence = False
    for line in lines:
        if _FENCE_RE.match(line):
            in_fence = not in_fence
        if not in_fence and line.startswith(marker):
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


def split_subsections(body: str, marker: str = "### "):
    """Split an entry body into (bullet_field_portion, {subsection_name: content}).

    Playbook entries can carry ### -level subsections (Bad example / Good
    example) after the bullet fields. "### " is a safe marker to nest inside
    a "## "-delimited entry -- split_sections' marker check is a literal
    prefix match, and "### " does not start with "## " (the third character
    differs), so it never gets mistaken for a new top-level entry boundary.

    Fence-aware for the same reason split_sections is: an example snippet's
    own "### "-or-deeper heading (or a stray "```" line) inside a fenced
    code block must not be treated as a real subsection boundary.
    """
    lines = body.split("\n")
    main_lines = []
    subsections = {}
    current_name = None
    current_lines = []
    in_fence = False
    for line in lines:
        if _FENCE_RE.match(line):
            in_fence = not in_fence
        if not in_fence and line.startswith(marker):
            if current_name is not None:
                subsections[current_name] = "\n".join(current_lines).strip("\n")
            current_name = line[len(marker):].strip()
            current_lines = []
        elif current_name is not None:
            current_lines.append(line)
        else:
            main_lines.append(line)
    if current_name is not None:
        subsections[current_name] = "\n".join(current_lines).strip("\n")
    return "\n".join(main_lines), subsections


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
        main_body, subsections = split_subsections(body)
        fields = rewrite_fields(parse_bullet_fields(main_body), "knowledge")
        raw_status = get_field(fields, "Status")
        summary = subsections.get("Summary", "")
        entries.append({
            "id": ledger_entry_slug(header),
            "title": header,
            "fields": fields,
            "eli10": get_field_startswith(fields, "Explain it like"),
            "status_raw": raw_status,
            "status": status_keyword(raw_status) or "unknown",
            "linked": get_field_startswith(fields, "Linked exercises"),
            "summary_html": render_md(rewrite_internal_links(summary, "knowledge")) if summary else "",
        })
    return list(reversed(entries))  # most recently added first


# ---------------------------------------------------------------------------
# Playbook
# ---------------------------------------------------------------------------

def parse_playbook(text: str):
    _preamble, sections = split_sections(text)
    entries = []
    for header, body in sections:
        main_body, subsections = split_subsections(body)
        fields = rewrite_fields(parse_bullet_fields(main_body), "knowledge")
        summary = subsections.get("Summary", "")
        bad_example = subsections.get("Bad example", "")
        good_example = subsections.get("Good example", "")
        entries.append({
            "id": playbook_entry_slug(header),
            "title": header,
            "fields": fields,
            "eli10": get_field_startswith(fields, "Explain it like"),
            "confidence": status_keyword(get_field(fields, "Confidence")) or "unknown",
            "status": status_keyword(get_field(fields, "Status")) or "active",
            "summary_html": render_md(rewrite_internal_links(summary, "knowledge")) if summary else "",
            "bad_example_html": render_md(rewrite_internal_links(bad_example, "knowledge")) if bad_example else "",
            "good_example_html": render_md(rewrite_internal_links(good_example, "knowledge")) if good_example else "",
        })
    return entries


def generate_agent_best_practices(text: str, portal_url: str = "") -> str:
    """Renders the active playbook entries into a standalone markdown file --
    an importable instruction set for designing agents elsewhere (in a
    project's CLAUDE.md, or any other agent-building context), independent
    of this portal.

    Deliberately NOT the same parse as parse_playbook(): this uses raw field
    text with no portal-specific link rewriting (a #tab-findings anchor
    means nothing outside this site), keeps only the fields useful for
    *applying* a recommendation (Recommendation, Why, Bad/Good example) and
    drops the ones that are about *researching* it (Evidence, References,
    Summary, Explain it like I'm 10) -- those stay one click away via the
    link back to the full entry. Superseded/non-active entries are excluded;
    stale advice has no place in an instruction set someone will load as-is.
    """
    _preamble, sections = split_sections(text)
    by_category = {}
    order = []
    for header, body in sections:
        main_body, subsections = split_subsections(body)
        fields = parse_bullet_fields(main_body)
        if status_keyword(get_field(fields, "Status")) != "active":
            continue
        category = get_field(fields, "Category", "Uncategorized")
        if category not in by_category:
            by_category[category] = []
            order.append(category)
        by_category[category].append({
            "id": playbook_entry_slug(header),
            "title": header,
            "confidence": get_field(fields, "Confidence"),
            "recommendation": get_field(fields, "Recommendation"),
            "why": get_field(fields, "Why"),
            "bad_example": subsections.get("Bad example", ""),
            "good_example": subsections.get("Good example", ""),
        })

    lines = [
        "# Agent Building Best Practices",
        "",
        "Evidence-backed recommendations for designing, instructing, and running AI "
        "agents, auto-generated from the AIExpert playbook. Read this before writing "
        "a new agent's instructions.",
        "",
    ]
    if portal_url:
        lines += [f"Full evidence, sources, and context: {portal_url}", ""]
    lines += ["---", ""]

    for category in order:
        lines += [f"## {category}", ""]
        for e in by_category[category]:
            title = e["title"].split("—", 1)[-1].strip() or e["title"]
            lines += [f"### {title}", ""]
            if e["confidence"]:
                lines += [f"*Confidence: {e['confidence']}*", ""]
            if e["recommendation"]:
                lines += [e["recommendation"], ""]
            if e["why"]:
                lines += [f"**Why:** {e['why']}", ""]
            if e["bad_example"]:
                lines += ["**Bad example:**", "", e["bad_example"], ""]
            if e["good_example"]:
                lines += ["**Good example:**", "", e["good_example"], ""]
            if portal_url:
                lines += [f"[Full entry, evidence, and sources]({portal_url}#{e['id']})", ""]
            lines += ["---", ""]

    return "\n".join(lines).rstrip() + "\n"


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
