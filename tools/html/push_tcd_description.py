#!/usr/bin/env python3
"""
Push TCD descriptions from KB/pm_tcd_kb markdown files to HSD test_case_definition.description.

Calls build_desc_from_kb() from generate_tcd_preview.py to render the 8 structured
sections with inline styles (HSDES-safe, no CSS classes).  Backs up the existing
description as a comment before overwriting.

Usage
-----
  # Dry-run (default) - show preview, no writes:
  python tools/html/push_tcd_description.py --tcd 22022421183

  # Push one TCD after confirmation prompt:
  python tools/html/push_tcd_description.py --tcd 22022421183 --push

  # Push without prompt:
  python tools/html/push_tcd_description.py --tcd 22022421183 --push --yes
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from tools.html.generate_tcd_preview import build_desc_from_kb, find_kb_file

TODAY        = time.strftime("%Y-%m-%d")
BACKUP_LIMIT = 4000
RATE_SLEEP   = 0.4
HSD_LINK     = "https://hsdes.intel.com/appstore/article-one/#/{}"

CONTAINER = (
    '<div style="font-family:\'Segoe UI\',Arial,sans-serif;'
    'font-size:13px;color:#1f2937;line-height:1.6;">'
    "{body}"
    "</div>"
)


def _render_tcd_description(kb_text: str) -> str:
    """Render KB markdown to inline-styled HTML for HSD (no page chrome)."""
    desc_htm, _ = build_desc_from_kb(kb_text)
    return CONTAINER.format(body=desc_htm)


def push_one(
    tcd_id: str,
    *,
    dry_run: bool,
    yes: bool,
    session,
) -> str:
    from hsd_utils.queries import get_article
    from hsd_utils.operations import set_field, create_article

    kb_file = find_kb_file(tcd_id)
    if not kb_file:
        print(f"  SKIP {tcd_id}: no KB file in KB/pm_tcd_kb/")
        return "skip"

    kb_text  = kb_file.read_text(encoding="utf-8", errors="replace")
    new_desc = _render_tcd_description(kb_text)

    art      = get_article(tcd_id, fields="id,title,description", session=session)
    title    = art.get("title", tcd_id)
    old_desc = art.get("description") or ""

    # Extract section count from rendered HTML
    nsec = len(re.findall(r'font-size:1\.3em;font-weight:bold', new_desc))

    print(f"\n  [{tcd_id}] {title[:72]}")
    print(f"    KB file : {kb_file.name}")
    print(f"    Sections: {nsec} of 8")
    print(f"    Desc    : {len(old_desc):,} chars -> {len(new_desc):,} chars")

    if dry_run:
        print("    [DRY-RUN] no writes")
        return "dry"

    if not yes:
        ans = input("    Push to HSD? [y/N] ").strip().lower()
        if ans not in ("y", "yes"):
            print("    Skipped.")
            return "confirm_no"

    # Backup original description
    if old_desc.strip():
        backup_body = old_desc[:BACKUP_LIMIT] + ("..." if len(old_desc) > BACKUP_LIMIT else "")
        comment_fv = [
            {"parent_id": int(tcd_id)},
            {"title": f"[val_agent {TODAY}] pre-push TCD description backup"},
            {"description": backup_body},
            {"send_mail": "false"},
        ]
        try:
            create_article("comments", comment_fv, session=session)
        except Exception as e:
            print(f"    WARN: backup comment failed: {e}")

    code = set_field(tcd_id, "test_case_definition", "description", new_desc, session=session)
    if code not in (200, 201):
        print(f"    ERR: PUT returned HTTP {code}")
        return "error"

    print(f"    OK (HTTP {code})")
    return "ok"


def main() -> int:
    p = argparse.ArgumentParser(
        description="Push KB TCD description to HSD test_case_definition.description",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--tcd", nargs="+", metavar="ID", required=True, help="TCD HSD ID(s)")
    p.add_argument("--push",  action="store_true", help="Actually write to HSD (default: dry-run)")
    p.add_argument("--yes",   action="store_true", help="Skip per-TCD confirmation")
    args = p.parse_args()

    dry_run = not args.push
    ids     = args.tcd

    if dry_run:
        print(f"[DRY-RUN] {len(ids)} TCD(s) - pass --push to write to HSD")
    else:
        print(f"[PUSH] {len(ids)} TCD(s)")

    from hsd_utils.session import get_session
    session = get_session()

    counts: dict[str, int] = {"ok": 0, "skip": 0, "dry": 0, "error": 0, "confirm_no": 0}
    results = []

    for tcd_id in ids:
        try:
            status = push_one(tcd_id, dry_run=dry_run, yes=args.yes, session=session)
        except Exception as e:
            print(f"  ERR {tcd_id}: {e}")
            status = "error"

        counts[status] = counts.get(status, 0) + 1
        results.append({"id": tcd_id, "status": status})
        if not dry_run and status == "ok":
            time.sleep(RATE_SLEEP)

    print(f"\n{'-'*60}")
    print(f"  OK: {counts['ok']}  |  Dry: {counts['dry']}  |  "
          f"Skip: {counts['skip']}  |  No: {counts['confirm_no']}  |  Err: {counts['error']}")
    return 0 if counts["error"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
