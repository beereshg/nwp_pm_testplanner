#!/usr/bin/env python3
"""
hsd_create_tpf.py — Create a new TPF under a TP and optionally move TCDs into it.

Usage:
    # Create TPF under a TP
    python tools/hsd/hsd_create_tpf.py --tp 16030762839 --title "NWP PM DLCP"

    # Create TPF and move a TCD into it
    python tools/hsd/hsd_create_tpf.py --tp 16030762839 --title "NWP PM DLCP" --move 16030982802

    # Create TPF and move multiple TCDs
    python tools/hsd/hsd_create_tpf.py --tp 16030762839 --title "NWP PM DLCP" --move 16030982802 22022420855

    # Move TCD to existing TPF (no create)
    python tools/hsd/hsd_create_tpf.py --move 16030982802 --to 16031169314

    # Dry-run
    python tools/hsd/hsd_create_tpf.py --tp 16030762839 --title "NWP PM DLCP" --move 16030982802 --dry-run
"""
import argparse
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from hsd_utils import operations
from hsd_utils.session import get_session, HSD_URL


def main():
    p = argparse.ArgumentParser(
        description="Create a TPF under a TP and/or move TCDs into a TPF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    # Create mode
    p.add_argument("--tp", metavar="TP_ID",
                   help="Parent TP ID for the new TPF")
    p.add_argument("--title", metavar="TITLE",
                   help="Title for the new TPF")

    # Move mode
    p.add_argument("--move", nargs="+", metavar="TCD_ID",
                   help="TCD ID(s) to move")
    p.add_argument("--to", metavar="TPF_ID", dest="target_tpf",
                   help="Existing TPF ID to move TCDs into (skip create)")

    p.add_argument("--dry-run", action="store_true",
                   help="Print plan without calling HSD API")
    args = p.parse_args()

    # Validate arguments
    if args.target_tpf and args.tp:
        p.error("Use --tp to create a new TPF, or --to for an existing one, not both")
    if args.tp and not args.title:
        p.error("--title is required when creating a new TPF with --tp")
    if not args.tp and not args.target_tpf and not args.move:
        p.error("Nothing to do — provide --tp/--title to create, or --move/--to to move")
    if args.move and not args.tp and not args.target_tpf:
        p.error("--move requires either --tp (create new TPF) or --to (existing TPF)")

    s = get_session()
    tpf_id = args.target_tpf

    # ── Create TPF ───────────────────────────────────────────────────────
    if args.tp:
        print(f"Creating TPF under TP {args.tp}: {args.title}")
        if args.dry_run:
            print("  [DRY RUN] Would create TPF")
            tpf_id = "<new>"
        else:
            tpf_id = operations.create_article(
                subject="test_plan",
                field_values=[
                    {"title": args.title},
                    {"parent_id": args.tp},
                    {"send_mail": "false"},
                ],
                session=s,
            )
            if not tpf_id:
                print("ERROR: Failed to create TPF", file=sys.stderr)
                sys.exit(1)
            print(f"  Created TPF {tpf_id}: {HSD_URL.format(tpf_id)}")

    # ── Move TCDs ────────────────────────────────────────────────────────
    if args.move:
        print(f"\nMoving {len(args.move)} TCD(s) to TPF {tpf_id}")
        ok = fail = 0
        for tcd_id in args.move:
            if args.dry_run:
                print(f"  [DRY RUN] Would move TCD {tcd_id} -> TPF {tpf_id}")
                ok += 1
                continue
            code = operations.move_tcd(tcd_id, tpf_id, session=s)
            if code == 200:
                print(f"  OK TCD {tcd_id} -> TPF {tpf_id}  ({HSD_URL.format(tcd_id)})")
                ok += 1
            else:
                print(f"  FAIL TCD {tcd_id}: HTTP {code}", file=sys.stderr)
                fail += 1
        print(f"\nSummary: {ok} moved, {fail} failed")
        if fail:
            sys.exit(1)

    # ── Final links ──────────────────────────────────────────────────────
    if tpf_id and tpf_id != "<new>":
        print(f"\nTPF: {HSD_URL.format(tpf_id)}")


if __name__ == "__main__":
    main()
