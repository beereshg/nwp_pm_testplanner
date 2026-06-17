#!/usr/bin/env python3
"""
NWP TC Grading — LLM-reasoning workflow.

For each TC:
  1. Fetch full article content (description, command line, tags, etc.)
  2. Print TC content for LLM to read and reason about
  3. LLM generates TC-specific grading rationale per 6 dimensions
  4. Post grading comment to HSD (send_mail omitted)

Usage:
  python tools/grading/grade_tc.py <HSD_ID> [<HSD_ID2> ...]
  python tools/grading/grade_tc.py --tp <TP_ID>   # all open TCs under TP
  python tools/grading/grade_tc.py --fetch-only 22022422850  # just print content

This script handles fetch (step 1) and post (step 4).
Grading reasoning (steps 2-3) is performed by the LLM using nwp-tc-grading skill.
"""
import argparse
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from hsd_utils import create_article, get_article, get_children, get_session


TC_FIELDS = ("id,title,description,status,reason,tag,"
             "test_case.val_environment,test_case.command_line,"
             "test_case.free_tag_1,test_case.free_tag_2,test_case.free_tag_3,"
             "test_case.origin_project,test_case.val_framework,parent_id,owner")

def fetch_article(session, article_id):
    return get_article(article_id, fields=TC_FIELDS, session=session)


def fetch_comments(session, article_id):
    return get_children(
        article_id,
        child_subject="comment",
        fields="id,owner,submitted_date,description",
        max_results=10,
        session=session,
    )


def fetch_children(session, parent_id, child_sub, fields="id,title,status", max_results=300):
    return get_children(
        parent_id,
        child_subject=child_sub,
        fields=fields,
        max_results=max_results,
        session=session,
    )

def get_open_tcs_under_tp(session, tp_id):
    tcs = []
    for tpf in fetch_children(session, tp_id, "test_plan", max_results=1000):
        tpf_id = tpf.get("id")
        if not tpf_id:
            continue
        for tcd in fetch_children(session, tpf_id, "test_case_definition", fields="id,title", max_results=1000):
            tcd_id = tcd.get("id")
            if not tcd_id:
                continue
            for tc in fetch_children(
                session,
                tcd_id,
                "test_case",
                fields="id,title,status,owner",
                max_results=1000,
            ):
                if "rejected" not in tc.get("status","").lower():
                    tcs.append({**tc,"tpf":tpf["title"],"tcd":tcd["title"]})
            time.sleep(0.05)
        time.sleep(0.1)
    return tcs

def print_tc_for_grading(tc, comments=None):
    print("\n" + "="*70)
    print(f"TC ID   : {tc.get('id')}")
    print(f"Title   : {tc.get('title')}")
    print(f"Status  : {tc.get('status')}  Reason: {tc.get('reason','')}")
    print(f"Owner   : {tc.get('owner')}  Origin: {tc.get('test_case.origin_project','')}")
    print(f"Feature : {tc.get('test_case.free_tag_1','')} / {tc.get('test_case.free_tag_3','')}")
    print(f"Val Env : {tc.get('test_case.val_environment','')}")
    print(f"Framework: {tc.get('test_case.val_framework','')}")
    print(f"Command : {tc.get('test_case.free_tag_2','')}")
    print(f"Tags    : {tc.get('tag','')}")
    desc = tc.get("description","") or ""
    text = re.sub(r"<[^>]+>"," ",desc)
    text = re.sub(r"&[a-zA-Z]+;"," ",text)
    text = re.sub(r"\s+"," ",text).strip()
    print(f"\n--- Description (stripped) ---\n{text[:3000]}")
    if comments:
        print(f"\n--- Recent comment ({comments[-1].get('owner')}, {comments[-1].get('submitted_date','')[:10]}) ---")
        cdesc = re.sub(r"<[^>]+>"," ",comments[-1].get("description","") or "")
        cdesc = re.sub(r"\s+"," ",cdesc).strip()
        print(cdesc[:500])
    print("="*70)

def post_comment(session, tc_id, html):
    new_id = create_article(
        "comments",
        field_values=[
            {"description": html},
            {"parent_id": str(tc_id)},
            {"send_mail": "false"},
        ],
        session=session,
    )
    if new_id:
        return True, new_id
    return False, "create_article failed"

def build_grading_comment(tc_id, tc_title, rows, notes):
    TH = 'style="border-color:rgb(230,230,230);background-color:rgb(245,245,245);"'
    TD = 'style="border-color:rgb(230,230,230);"'
    row_html = "".join(f'<tr><td {TD}>{n}</td><td {TD}><strong>{c}</strong></td>'
                       f'<td {TD}>{v}</td><td {TD}>{su}</td></tr>\n'
                       for n,c,v,su in rows)
    note_html = "".join(f'<tr><td {TD}>{a}</td><td {TD}>{d}</td></tr>\n' for a,d in notes)
    return (f'<div style="font-family:\'Segoe UI\';line-height:20px;">\n'
            f'<h3><strong>TC Grading &mdash; HSD {tc_id} ({tc_title})</strong></h3>\n'
            f'<table><thead><tr><th {TH}>Sl No</th><th {TH}>Category</th>'
            f'<th {TH}>Value</th><th {TH}>Summary</th></tr></thead><tbody>\n'
            f'{row_html}</tbody></table>\n<hr />\n'
            f'<h3><strong>Key Notes (Condensed)</strong></h3>\n'
            f'<table><thead><tr><th {TH}>Area</th><th {TH}>Detail</th></tr></thead><tbody>\n'
            f'{note_html}</tbody></table>\n<hr /><p><br /></p>\n</div>')

def main():
    parser = argparse.ArgumentParser(description="NWP TC Grader")
    parser.add_argument("tc_ids", nargs="*", help="HSD TC IDs")
    parser.add_argument("--tp", help="Grade all open TCs under TP ID")
    parser.add_argument("--fetch-only", action="store_true")
    args = parser.parse_args()
    session = get_session()
    tc_ids = list(args.tc_ids)
    if args.tp:
        stubs = get_open_tcs_under_tp(session, args.tp)
        tc_ids = [t["id"] for t in stubs]
        print(f"Open TCs under TP {args.tp}: {len(tc_ids)}")
    if not tc_ids:
        parser.print_help(); return
    for tc_id in tc_ids:
        tc = fetch_article(session, tc_id)
        comments = fetch_comments(session, tc_id)
        print_tc_for_grading(tc, comments[-1:] if comments else None)
        if args.fetch_only:
            print("  [fetch-only mode — LLM reads above, then calls build_grading_comment + post_comment]")
        else:
            print(f"\n  [Grade TC {tc_id} using nwp-tc-grading skill, then call post_comment()]")

if __name__ == "__main__":
    main()
