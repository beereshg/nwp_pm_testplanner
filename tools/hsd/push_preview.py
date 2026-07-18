#!/usr/bin/env python3
"""
push_preview.py — Push a KB-generated HTML preview to its HSD article description.

Extracts the inner HTML of the <div class="desc-box"> from a preview file and
updates the HSD description field via REST API (Kerberos auth, no temp files).

Usage
-----
    # Push a single TPF preview (HSD ID + subject auto-detected from filename)
    python tools/hsd/push_preview.py tpf_description_output/TPF_16030762939_*_preview.html

    # Push a TCD preview
    python tools/hsd/push_preview.py tcd_description_output/TCD_22022420862_*_preview.html

    # Push a TC description preview
    python tools/hsd/push_preview.py tc_description_output/TC_16030717717_*_preview.html

    # Dry-run (print extracted content without pushing)
    python tools/hsd/push_preview.py --dry-run tpf_description_output/TPF_*.html

    # Override auto-detection (single file only)
    python tools/hsd/push_preview.py some_file.html --id 16030762939 --subject test_plan

    # Push multiple previews in one call
    python tools/hsd/push_preview.py tcd_description_output/TCD_*_preview.html

Auto-detection rules (from filename):
    TPF_<id>_*_preview.html  →  subject: test_plan
    TCD_<id>_*_preview.html  →  subject: test_case_definition
    TC_<id>_*_preview.html   →  subject: test_case
"""

import argparse
import os
import re
import sys
import pathlib

# Allow running from any directory inside the repo
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from hsd_utils import operations
from hsd_utils.session import get_session, HSD_URL

SUBJECT_MAP = {
    "TPF": "test_plan",
    "TCD": "test_case_definition",
    "TC":  "test_case",
}


def extract_desc_box(html: str) -> str:
    """Extract the innerHTML of <div class="desc-box"> from a preview HTML file."""
    marker = 'class="desc-box">'
    try:
        start = html.index(marker) + len(marker)
    except ValueError:
        raise ValueError('No <div class="desc-box"> found — is this a preview HTML file?')
    # rindex finds the LAST </div> before </body> — matches the closing tag of desc-box
    end = html.rindex("</div>", 0, html.index("</body>"))
    return html[start:end].strip()


def detect_from_filename(html_path: str):
    """Return (hsd_id, subject) detected from preview HTML filename, or (None, None)."""
    name = os.path.basename(html_path)
    m = re.match(r"^(TPF|TCD|TC)_(\d+)_.*_preview\.html$", name, re.IGNORECASE)
    if not m:
        return None, None
    prefix = m.group(1).upper()
    return m.group(2), SUBJECT_MAP.get(prefix)


def push_one(html_path: str, hsd_id: str, subject: str, session, dry_run: bool) -> bool:
    """Extract desc-box from html_path and push to HSD. Returns True on success."""
    with open(html_path, encoding="utf-8") as f:
        html = f.read()
    try:
        content = extract_desc_box(html)
    except ValueError as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return False

    url = HSD_URL.format(hsd_id)
    print(f"\n  file    : {html_path}")
    print(f"  hsd_id  : {hsd_id}  ({url})")
    print(f"  subject : {subject}")
    print(f"  content : {len(content)} chars")

    if dry_run:
        print("  result  : [DRY RUN] not pushed")
        return True

    code = operations.set_field(hsd_id, subject, "description", content, session=session)
    if code == 200:
        print(f"  result  : 200 OK")
        return True
    else:
        print(f"  result  : {code} ERROR", file=sys.stderr)
        return False


def main():
    p = argparse.ArgumentParser(
        description="Push KB preview HTML desc-box content to HSD article description",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("html_files", nargs="+", metavar="PREVIEW_HTML",
                   help="One or more *_preview.html files to push")
    p.add_argument("--id", help="Override HSD ID (single file only)")
    p.add_argument("--subject",
                   choices=["test_plan", "test_case_definition", "test_case",
                            "test_plan_folder", "test_result"],
                   help="Override subject (single file only)")
    p.add_argument("--dry-run", action="store_true",
                   help="Extract content and print without calling HSD API")
    args = p.parse_args()

    if (args.id or args.subject) and len(args.html_files) > 1:
        sys.exit("ERROR: --id / --subject overrides can only be used with a single HTML file.")

    session = None if args.dry_run else get_session()

    ok = True
    for html_path in args.html_files:
        hsd_id, subject = detect_from_filename(html_path)
        if args.id:
            hsd_id = args.id
        if args.subject:
            subject = args.subject
        if not hsd_id:
            print(f"ERROR: Cannot detect HSD ID from '{html_path}'. Use --id.", file=sys.stderr)
            ok = False
            continue
        if not subject:
            print(f"ERROR: Cannot detect subject from '{html_path}'. Use --subject.", file=sys.stderr)
            ok = False
            continue
        ok = push_one(html_path, hsd_id, subject, session, args.dry_run) and ok

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
