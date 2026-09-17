"""Pre-renders the AIExpert portal to static HTML for Azure Static Web Apps.

Runs the real Flask app through its own test client -- the exact same code
path the live dev server uses for the same request -- so the static build
can never drift from what the dynamic portal would show for the same
workspace content. Sets PORTAL_READ_ONLY=1 first so the interactive status
controls (which need a live backend this static host doesn't have) don't
render.
"""
import os
import shutil
from pathlib import Path

os.environ["PORTAL_READ_ONLY"] = "1"
os.environ.setdefault("PORTAL_PUBLIC_URL", "https://ashy-pebble-0b4d0eb03.2.azurestaticapps.net")

import app as portal_app  # noqa: E402  (must follow the env vars above)
import parser  # noqa: E402

PORTAL_DIR = Path(__file__).resolve().parent
OUT_DIR = PORTAL_DIR / "dist"

# Workspace files already rendered as their own tab don't need a /raw/ copy.
_TAB_FILES = {"ledger.md", "playbook.md", "changelog.md", "backlog.md", "regression-log.md"}


def _write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def main() -> None:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    client = portal_app.app.test_client()

    res = client.get("/")
    if res.status_code != 200:
        raise SystemExit(f"index build failed: HTTP {res.status_code}")
    _write(OUT_DIR / "index.html", res.data)
    print(f"wrote index.html ({len(res.data)} bytes)")

    shutil.copytree(PORTAL_DIR / "static", OUT_DIR / "static")
    print("copied static/ assets")

    res = client.get("/agent-best-practices.md")
    if res.status_code != 200:
        raise SystemExit(f"agent-best-practices.md build failed: HTTP {res.status_code}")
    _write(OUT_DIR / "agent-best-practices.md", res.data)
    print(f"wrote agent-best-practices.md ({len(res.data)} bytes)")

    shutil.copy(PORTAL_DIR / "staticwebapp.config.json", OUT_DIR / "staticwebapp.config.json")
    print("copied staticwebapp.config.json")

    # Requested at their .html URL (parser.raw_url_for_md) even though the
    # source file on disk is .md -- see that function's docstring for why.
    workspace_dir = portal_app.WORKSPACE_DIR
    raw_count = 0
    for md_path in sorted(workspace_dir.rglob("*.md")):
        if md_path.name in _TAB_FILES:
            continue
        rel = md_path.relative_to(workspace_dir).as_posix()
        raw_url = parser.raw_url_for_md(rel)
        res = client.get(raw_url)
        if res.status_code == 200:
            out_rel = raw_url[len("/raw/"):]
            _write(OUT_DIR / "raw" / out_rel, res.data)
            raw_count += 1
        else:
            print(f"warning: {raw_url} returned HTTP {res.status_code}, skipped")
    print(f"wrote {raw_count} /raw/ page(s)")

    print(f"Static build complete: {OUT_DIR}")


if __name__ == "__main__":
    main()
