#!/usr/bin/env python3
"""
hsd_fetch.py — Fetch any HSD article's fields and print to stdout.

Usage:
    python hsd_fetch.py <HSD_ID> [--fields FIELD1,FIELD2,...] [--plain] [--json]

Options:
    --fields    Comma-separated field names to fetch (default: full PM set)
    --plain     Strip HTML tags and print plain text (default: raw HTML)
    --json      Print full JSON response

Examples:
    python hsd_fetch.py 22022422865
    python hsd_fetch.py 16030717882 --plain
    python hsd_fetch.py 22022422865 --fields title,status,owner,description --plain
    python hsd_fetch.py 22022421965 --json > out.json
"""
import sys, re, json, argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from hsd_utils import queries, session as hsd_session

DEFAULT_FIELDS = (
    "id,title,owner,status,reason,priority,subject,parent_id,"
    "description,tag,component,updated_date"
)

def strip_html(html: str) -> str:
    plain = re.sub(r'<[^>]+>', ' ', html or '')
    plain = re.sub(r'&amp;', '&', plain)
    plain = re.sub(r'&lt;', '<', plain)
    plain = re.sub(r'&gt;', '>', plain)
    plain = re.sub(r'&nbsp;', ' ', plain)
    plain = re.sub(r'&#\d+;', ' ', plain)
    return re.sub(r'\s+', ' ', plain).strip()


def main():
    ap = argparse.ArgumentParser(description="Fetch an HSD article")
    ap.add_argument("hsd_id", help="HSD article ID")
    ap.add_argument("--fields", default=DEFAULT_FIELDS, help="Comma-separated fields to fetch")
    ap.add_argument("--plain", action="store_true", help="Strip HTML from description")
    ap.add_argument("--short", action="store_true", help="Print metadata only — skip description entirely")
    ap.add_argument("--json", action="store_true", help="Output raw JSON")
    args = ap.parse_args()

    art = queries.get_article(args.hsd_id, fields=args.fields)

    if not art:
        print(f"ERROR: Article {args.hsd_id} not found or Kerberos auth failed.", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(art, indent=2, ensure_ascii=False))
        return

    # Pretty print
    skip_in_summary = {'description'}
    print(f"{'='*60}")
    print(f"HSD: {args.hsd_id}  |  {hsd_session.HSD_URL.format(args.hsd_id)}")
    print(f"{'='*60}")
    for k, v in art.items():
        if k == 'description':
            continue
        print(f"  {k:<20}: {v}")

    desc = art.get('description', '') or ''
    if desc:
        print(f"\n--- Description ({len(desc)} chars) ---")
        if args.short:
            print(f"[skipped — use without --short to see description]")
        elif args.plain:
            print(strip_html(desc))
        else:
            print(desc)


if __name__ == '__main__':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()
