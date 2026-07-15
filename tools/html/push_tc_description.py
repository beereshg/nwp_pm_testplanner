#!/usr/bin/env python3
"""
Push TC descriptions from KB inference.md to HSD test_case.description field.

Renders KB/pm_tc_kb/{fv|pss}/HSD_{id}_*.inference.md via the Jinja2 template
(KB/templates/tc_hsd_description.html.j2) — the same inline-styled HTML that
HSDES renders correctly — then PUTs to HSD.  The existing HSD description is
backed up as a comment before any overwrite.

Usage
-----
  # Dry-run (default): show preview, make no writes
  python tools/html/push_tc_description.py --hsd 22022423032

  # Push one or more TCs after confirmation
  python tools/html/push_tc_description.py --hsd 22022423032 22022423036 --push

  # Push without per-TC prompts
  python tools/html/push_tc_description.py --hsd 22022423032 --push --yes

  # Push all TCs that have a KB inference.md
  python tools/html/push_tc_description.py --all --push --yes

  # Limit to a segment
  python tools/html/push_tc_description.py --all --segment fv --push --yes
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

# Ensure stdout handles unicode scope snippets on Windows cp1252 terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure stdout can handle unicode (scope snippets may contain em-dashes etc.)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tools.html.generate_tc_description import (
    find_inference_file,
    extract_scope,
    extract_preconditions,
    extract_steps,
    extract_passfail,
    extract_health_checks,
    extract_notes,
    extract_opens,
    extract_refs,
    extract_post_process,
    render_fallback,
    _JINJA,
    TEMPLATE_DIR,
    CACHE_ROOT,
)

try:
    from jinja2 import Environment, FileSystemLoader
    _JINJA2 = True
except ImportError:
    _JINJA2 = False

TODAY = time.strftime("%Y-%m-%d")
BACKUP_LIMIT = 4000   # chars to include in the backup comment
RATE_SLEEP   = 0.4    # seconds between HSD PUTs


def _render_description(text: str) -> str:
    """Render the inference.md text to an inline-styled HTML string for HSD."""
    tc = {
        "scope":         extract_scope(text),
        "preconditions": extract_preconditions(text),
        "steps":         extract_steps(text),
        "passfail":      extract_passfail(text),
        "health_checks": extract_health_checks(text),
        "notes":         extract_notes(text),
        "opens":         extract_opens(text),
        "post_process":  extract_post_process(text),
    }
    fr_hsd, specs = extract_refs(text)
    config = {"fr_hsd": fr_hsd, "specs": specs}

    if _JINJA2:
        env  = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False)
        tmpl = env.get_template("tc_hsd_description.html.j2")
        return tmpl.render(tc=tc, config=config)
    return render_fallback(tc, config, "")


def _extract_command(text: str) -> str:
    """Extract test command from the metadata table (Automation row)."""
    m = re.search(r"\|\s*\*\*Automation\*\*\s*\|\s*(.+?)\s*\|", text)
    if m:
        cmd = m.group(1).strip()
        return cmd if cmd and cmd != "—" and cmd.lower() != "n/a" else ""
    return ""


def _list_all_kb_ids(segment: str = "all") -> list[str]:
    """Return sorted list of HSD IDs present in the KB."""
    segs = [segment] if segment in ("fv", "pss") else ["fv", "pss"]
    ids: list[str] = []
    seen: set[str] = set()
    for seg in segs:
        for f in sorted((CACHE_ROOT / seg).glob("HSD_*_*.inference.md")):
            m = re.match(r"HSD_(\d+)_", f.name)
            if m and m.group(1) not in seen:
                ids.append(m.group(1))
                seen.add(m.group(1))
    return ids


def push_one(
    hsd_id: str,
    *,
    dry_run: bool,
    yes: bool,
    session,
    from_hsd_utils,
) -> str:
    """Process a single TC.  Returns 'ok', 'skip', 'dry', 'error', or 'confirm_no'."""
    from hsd_utils.queries import get_article
    from hsd_utils.operations import set_field, create_article

    inf = find_inference_file(hsd_id)
    if not inf:
        print(f"  SKIP {hsd_id}: no KB inference.md found")
        return "skip"

    text      = inf.read_text(encoding="utf-8", errors="replace")
    new_desc  = _render_description(text)
    new_cmd   = _extract_command(text)

    # Pull current HSD state for preview and backup
    art = get_article(hsd_id, fields="id,title,description,test_case.test_commands", session=session)
    title     = art.get("title", hsd_id)
    old_desc  = art.get("description") or ""
    old_cmd   = art.get("test_case.test_commands") or ""

    scope_snip = (extract_scope(text) or "")[:100]
    print(f"\n  [{hsd_id}] {title[:72]}")
    print(f"    KB file : {inf.name}")
    print(f"    Scope   : {scope_snip}{'…' if len(scope_snip)==100 else ''}")
    print(f"    Steps   : {len(extract_steps(text))}")
    print(f"    Desc    : {len(old_desc):,} chars → {len(new_desc):,} chars")
    if new_cmd and new_cmd != old_cmd:
        print(f"    Command : {old_cmd!r} → {new_cmd!r}")

    if dry_run:
        print("    [DRY-RUN] no writes")
        return "dry"

    if not yes:
        ans = input("    Push to HSD? [y/N] ").strip().lower()
        if ans not in ("y", "yes"):
            print("    Skipped.")
            return "confirm_no"

    # Backup original description as a comment
    if old_desc.strip():
        backup_body = old_desc[:BACKUP_LIMIT] + ("…" if len(old_desc) > BACKUP_LIMIT else "")
        comment_fv = [
            {"parent_id": int(hsd_id)},
            {"title": f"[val_agent {TODAY}] pre-push description backup"},
            {"description": backup_body},
            {"send_mail": "false"},
        ]
        try:
            create_article("comments", comment_fv, session=session)
        except Exception as e:
            print(f"    WARN: backup comment failed: {e}")

    # Push description
    code = set_field(hsd_id, "test_case", "description", new_desc, session=session)
    if code not in (200, 201):
        print(f"    ERR: description PUT returned HTTP {code}")
        return "error"

    # Push command if changed
    if new_cmd and new_cmd != old_cmd:
        c2 = set_field(hsd_id, "test_case", "test_case.test_commands", new_cmd, session=session)
        if c2 not in (200, 201):
            print(f"    WARN: command PUT returned HTTP {c2}")

    print(f"    OK (HTTP {code})")
    return "ok"


def main() -> int:
    p = argparse.ArgumentParser(
        description="Push KB inference.md → HSD test_case.description",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    grp = p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--hsd", nargs="+", metavar="ID", help="One or more TC HSD IDs")
    grp.add_argument("--all",  action="store_true",    help="Process all TCs with a KB file")
    p.add_argument("--segment", choices=["fv", "pss", "all"], default="all",
                   help="KB segment to search (default: all)")
    p.add_argument("--push",    action="store_true",   help="Actually write to HSD (default: dry-run)")
    p.add_argument("--yes",     action="store_true",   help="Skip per-TC confirmation")
    args = p.parse_args()

    dry_run = not args.push
    ids = args.hsd if args.hsd else _list_all_kb_ids(args.segment)

    if dry_run:
        print(f"[DRY-RUN] {len(ids)} TC(s) — pass --push to write to HSD")
    else:
        print(f"[PUSH] {len(ids)} TC(s)")

    from hsd_utils.session import get_session
    session = get_session()

    counts: dict[str, int] = {"ok": 0, "skip": 0, "dry": 0, "error": 0, "confirm_no": 0}
    results = []

    for hsd_id in ids:
        try:
            status = push_one(
                hsd_id,
                dry_run=dry_run,
                yes=args.yes,
                session=session,
                from_hsd_utils=True,
            )
        except Exception as e:
            print(f"  ERR {hsd_id}: {e}")
            status = "error"

        counts[status] = counts.get(status, 0) + 1
        results.append({"id": hsd_id, "status": status})
        if not dry_run and status == "ok":
            time.sleep(RATE_SLEEP)

    print(f"\n{'-'*60}")
    print(f"  OK: {counts['ok']}  |  Dry: {counts['dry']}  |  "
          f"Skip: {counts['skip']}  |  No: {counts['confirm_no']}  |  Err: {counts['error']}")
    if counts["error"]:
        print("  Errors:")
        for r in results:
            if r["status"] == "error":
                print(f"    {r['id']}")
    return 0 if counts["error"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
