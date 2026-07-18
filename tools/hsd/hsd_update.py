#!/usr/bin/env python3
"""
hsd_update.py — Update any HSD article field(s) from CLI or stdin.

Usage:
    # Update description from a file (LLM output saved as HTML)
    python hsd_update.py <HSD_ID> --subject <subject> --desc-file enriched.html

    # Update description from stdin (pipe LLM output directly)
    cat enriched.html | python hsd_update.py <HSD_ID> --subject test_case --desc-stdin

    # Change status + clear reason
    python hsd_update.py <HSD_ID> --subject test_case --status open --reason ""

    # Update any arbitrary field
    python hsd_update.py <HSD_ID> --subject test_case --field priority --value 2-high

    # Combined: update description AND reopen in one call sequence
    python hsd_update.py <HSD_ID> --subject test_case --desc-file enriched.html --status open --reason ""

Subjects:
    test_case, test_case_definition, test_plan, test_plan_folder, test_result
"""
import sys, argparse, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from hsd_utils import operations, session as hsd_session


def main():
    ap = argparse.ArgumentParser(description="Update an HSD article via REST API")
    ap.add_argument("hsd_id", help="HSD article ID")
    ap.add_argument("--subject", required=True,
                    help="HSD subject type: test_case, test_case_definition, test_plan, ...")

    # Description sources (mutually exclusive)
    desc_grp = ap.add_mutually_exclusive_group()
    desc_grp.add_argument("--desc-file", metavar="FILE",
                          help="Path to HTML file to use as new description")
    desc_grp.add_argument("--desc-stdin", action="store_true",
                          help="Read new description from stdin")

    # Status / reason shortcuts
    ap.add_argument("--status", help="New status (e.g. open, rejected, active)")
    ap.add_argument("--reason", help="New reason value (e.g. zbb, new, or empty string to clear)")

    # Generic field update
    ap.add_argument("--field", help="Any field name to update")
    ap.add_argument("--value", help="Value for --field")

    ap.add_argument("--dry-run", action="store_true",
                    help="Print what would be sent without calling the API")

    args = ap.parse_args()

    s = hsd_session.get_session()
    art_id  = str(args.hsd_id)
    subject = args.subject

    updates = []   # list of (field, value) tuples

    # ── Description ──────────────────────────────────────────────────────────
    if args.desc_file:
        p = pathlib.Path(args.desc_file)
        if not p.exists():
            print(f"ERROR: File not found: {p}", file=sys.stderr)
            sys.exit(1)
        new_desc = p.read_text(encoding='utf-8')
        # Guard: if the file is a preview page (contains desc-box), the caller
        # should use push_preview.py instead — pushing the whole page as
        # description would corrupt the HSD article with page chrome.
        if 'class="desc-box"' in new_desc:
            print(
                f"ERROR: {p.name} looks like a preview page (contains class=\"desc-box\").\n"
                f"  Use push_preview.py to push preview files:\n"
                f"    python tools/hsd/push_preview.py {p}",
                file=sys.stderr,
            )
            sys.exit(1)
        updates.append(('description', new_desc))
        print(f"  description: loaded from {p} ({len(new_desc)} chars)")

    elif args.desc_stdin:
        new_desc = sys.stdin.read()
        updates.append(('description', new_desc))
        print(f"  description: read from stdin ({len(new_desc)} chars)")

    # ── Status / reason (separate PUT calls to avoid 400) ────────────────────
    status_updates = []
    if args.status is not None:
        status_updates.append(('status', args.status))
    if args.reason is not None:
        status_updates.append(('reason', args.reason))

    # ── Generic field ─────────────────────────────────────────────────────────
    if args.field:
        if args.value is None:
            print("ERROR: --value required when --field is specified", file=sys.stderr)
            sys.exit(1)
        updates.append((args.field, args.value))

    if not updates and not status_updates:
        print("ERROR: Nothing to update. Specify --desc-file, --desc-stdin, --status, --reason, or --field.", file=sys.stderr)
        ap.print_help()
        sys.exit(1)

    print(f"Target: [{art_id}]  {hsd_session.HSD_URL.format(art_id)}")
    print(f"Subject: {subject}")

    if args.dry_run:
        print("\n[DRY RUN] Would send:")
        for f, v in updates:
            preview = str(v)[:120] + '...' if len(str(v)) > 120 else str(v)
            print(f"  {f}: {preview}")
        for f, v in status_updates:
            print(f"  {f}: {v}")
        return

    # ── Apply description + generic fields ─────────────────────────────────
    for field, value in updates:
        print(f"  Updating {field}...", end=' ', flush=True)
        code = operations.set_field(art_id, subject, field, value, session=s)
        print(f"HTTP {code}" + (" OK" if code == 200 else " FAILED"))
        if code != 200:
            sys.exit(1)

    # ── Apply status / reason (each as separate call) ──────────────────────
    for field, value in status_updates:
        print(f"  Updating {field} -> '{value}'...", end=' ', flush=True)
        code = operations.set_field(art_id, subject, field, value, session=s)
        print(f"HTTP {code}" + (" OK" if code == 200 else " FAILED"))
        if code != 200:
            sys.exit(1)

    print("Done.")


if __name__ == '__main__':
    main()
