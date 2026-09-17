"""AIExpert portal: a local, live dashboard over the ai-expert-workspace markdown files.

Read-heavy, write-narrow: every page load re-parses the workspace files fresh (no
database, no cache, so the portal can never drift from what AIExpert itself wrote).
The only writes the portal makes are single-line status-field updates to backlog.md
and proposal files, via the same narrow line-rewrite functions used for reading.
"""
import os
from pathlib import Path

from flask import Flask, Response, abort, jsonify, render_template, request

import parser

PORTAL_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = Path(os.environ.get("AI_EXPERT_WORKSPACE", PORTAL_DIR.parent / "ai-expert-workspace")).resolve()

PLAYBOOK_PATH = WORKSPACE_DIR / "knowledge" / "playbook.md"
LEDGER_PATH = WORKSPACE_DIR / "knowledge" / "ledger.md"
BACKLOG_PATH = WORKSPACE_DIR / "exercises" / "backlog.md"
CHANGELOG_PATH = WORKSPACE_DIR / "knowledge" / "changelog.md"
REGRESSION_LOG_PATH = WORKSPACE_DIR / "references" / "regression-log.md"
PROPOSALS_DIR = WORKSPACE_DIR / "proposals"

app = Flask(__name__)
app.jinja_env.filters["mdinline"] = parser.render_md_inline

READ_ONLY = os.environ.get("PORTAL_READ_ONLY") == "1"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_proposals():
    if not PROPOSALS_DIR.exists():
        return []
    proposals = []
    for path in sorted(PROPOSALS_DIR.glob("*.md")):
        if path.name.upper() == "TEMPLATE.MD":
            continue
        proposals.append(parser.parse_proposal(path.read_text(encoding="utf-8"), path.name))
    proposals.sort(key=lambda p: p["id"], reverse=True)
    return proposals


def load_all():
    return {
        "playbook": parser.parse_playbook(_read(PLAYBOOK_PATH)),
        "ledger": parser.parse_ledger(_read(LEDGER_PATH)),
        "exercises": parser.parse_backlog(_read(BACKLOG_PATH)),
        "proposals": load_proposals(),
        "changelog": parser.parse_changelog(_read(CHANGELOG_PATH)),
        "regression": parser.parse_regression_log(_read(REGRESSION_LOG_PATH)),
    }


@app.route("/")
def index():
    data = load_all()
    counts = {
        "playbook": len(data["playbook"]),
        "ledger": len(data["ledger"]),
        "exercises": len(data["exercises"]),
        "proposals": len(data["proposals"]),
        "changelog": len(data["changelog"]),
        "regression": len(data["regression"]),
    }
    return render_template(
        "index.html",
        data=data,
        counts=counts,
        exercise_statuses=parser.EXERCISE_STATUSES,
        proposal_statuses=parser.PROPOSAL_STATUSES,
        workspace_dir=str(WORKSPACE_DIR),
        read_only=READ_ONLY,
    )


@app.route("/raw/<path:relpath>")
def raw_workspace_file(relpath):
    """Serves a workspace markdown file that isn't represented by its own portal
    tab (EX-001-results.md, evaluation.md, TEMPLATE.md, ...), so links to it from
    other files resolve to real content instead of a dead path. Read-only, and
    restricted to files inside WORKSPACE_DIR -- resolves the path and rejects
    anything that escapes it (blocks `../../` traversal), and only serves .md."""
    if not relpath.endswith(".md"):
        abort(404)
    target = (WORKSPACE_DIR / relpath).resolve()
    try:
        target.relative_to(WORKSPACE_DIR)
    except ValueError:
        abort(404)
    if not target.is_file():
        abort(404)
    return Response(parser.render_md(target.read_text(encoding="utf-8")), mimetype="text/html")


@app.route("/api/exercise/<exercise_id>/status", methods=["POST"])
def api_update_exercise_status(exercise_id):
    new_status = (request.get_json(silent=True) or {}).get("status", "").strip()
    if new_status not in parser.EXERCISE_STATUSES:
        return jsonify({"ok": False, "error": f"invalid status: {new_status!r}"}), 400
    if not BACKLOG_PATH.exists():
        return jsonify({"ok": False, "error": "backlog.md not found"}), 404
    changed = parser.update_exercise_status(str(BACKLOG_PATH), exercise_id, new_status)
    if not changed:
        return jsonify({"ok": False, "error": f"exercise {exercise_id!r} not found"}), 404
    return jsonify({"ok": True, "id": exercise_id, "status": new_status})


@app.route("/api/proposal/<filename>/status", methods=["POST"])
def api_update_proposal_status(filename):
    new_status = (request.get_json(silent=True) or {}).get("status", "").strip()
    if new_status not in parser.PROPOSAL_STATUSES:
        return jsonify({"ok": False, "error": f"invalid status: {new_status!r}"}), 400
    path = PROPOSALS_DIR / filename
    if not path.exists() or path.suffix != ".md":
        return jsonify({"ok": False, "error": "proposal file not found"}), 404
    changed = parser.update_proposal_status(str(path), new_status)
    if not changed:
        return jsonify({"ok": False, "error": "no Status field found in proposal"}), 404
    return jsonify({"ok": True, "id": filename, "status": new_status})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5057"))
    print(f"AIExpert portal serving workspace: {WORKSPACE_DIR}")
    app.run(host="127.0.0.1", port=port, debug=True)
