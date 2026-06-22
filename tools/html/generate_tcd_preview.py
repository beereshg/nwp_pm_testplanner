"""
Generate TCD description preview HTML from HSD live data.

Usage:
  python tools/html/generate_tcd_preview.py --tcd <TCD_ID>
  python tools/html/generate_tcd_preview.py --tcd <TCD_ID> --force

Output:
  tcd_description_output/TCD_{id}_{slug}_preview.html

Workflow: fetch TCD -> render preview -> user reviews -> confirm -> update HSD
"""
from __future__ import annotations
import argparse, datetime, html as _h, re, sys, time
from pathlib import Path

REPO_ROOT  = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "tcd_description_output"
sys.path.insert(0, str(REPO_ROOT))

from hsd_utils import get_session, get_article, get_children


def slug(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return s[:50]


def build_tc_table(tcs: list[dict]) -> str:
    if not tcs:
        return "<p style='color:#888;font-style:italic'>No TCs found.</p>"
    rows = ""
    for tc in tcs:
        tid   = _h.escape(str(tc.get("id", "")))
        ttl   = _h.escape(tc.get("title", ""))
        st    = _h.escape(tc.get("status", ""))
        env   = _h.escape((tc.get("test_case.val_environment","") or "")[:35])
        feat  = _h.escape(tc.get("test_case.free_tag_1","") or "")
        color = "#2e7d32" if st == "open" else "#888"
        rows += (f'<tr><td><a href="https://hsdes.intel.com/appstore/article-one/#/{tid}" '
                 f'target="_blank">{tid}</a></td>'
                 f'<td>{ttl}</td>'
                 f'<td style="color:{color}">{st}</td>'
                 f'<td>{env}</td><td>{feat}</td></tr>')
    return (
        '<table style="width:100%;border-collapse:collapse;font-size:12px;margin:8px 0;">'
        '<thead><tr style="background:#e8eef7;">'
        '<th style="padding:6px 8px;text-align:left;">ID</th>'
        '<th style="padding:6px 8px;text-align:left;">Title</th>'
        '<th style="padding:6px 8px;text-align:left;">Status</th>'
        '<th style="padding:6px 8px;text-align:left;">Val Env</th>'
        '<th style="padding:6px 8px;text-align:left;">Feature</th>'
        '</tr></thead><tbody>' + rows + '</tbody></table>'
    )


def generate(tcd_id: str, force: bool = False) -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    s = get_session()

    tcd = get_article(tcd_id,
        fields="id,title,description,status,owner,parent_id", session=s)
    if not tcd:
        print(f"ERROR: TCD {tcd_id} not found"); return 1

    tcs = get_children(tcd_id, "test_case",
        fields="id,title,status,test_case.val_environment,test_case.free_tag_1,test_case.free_tag_2",
        session=s)

    title    = tcd.get("title", tcd_id)
    status   = tcd.get("status", "")
    owner    = tcd.get("owner", "")
    parent   = tcd.get("parent_id", "")
    desc_htm = tcd.get("description", "") or "<p>No description.</p>"
    now      = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    tc_table = build_tc_table(tcs)

    out_path = OUTPUT_DIR / f"TCD_{tcd_id}_{slug(title)}_preview.html"
    if out_path.exists() and not force:
        print(f"SKIP (exists): {out_path.name} -- use --force to overwrite")
        return 0

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline';"/>
  <title>TCD Preview: {_h.escape(title)}</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:'Segoe UI',Arial,sans-serif;background:#f0f4f9;font-size:13px;color:#1f2937;}}
    .hdr{{background:#0f4c81;color:#fff;padding:14px 24px;}}
    .hdr h1{{font-size:17px;font-weight:600;}}
    .hdr .sub{{font-size:11px;opacity:.82;margin-top:4px;}}
    .hdr a{{color:#90caf9;}}
    .wrap{{max-width:960px;margin:18px auto;padding:0 16px 40px;}}
    .notice{{background:#fff8e1;border:1px solid #ffe082;border-radius:6px;
             padding:10px 14px;margin-bottom:14px;font-size:12px;color:#7a5c00;}}
    .meta-bar{{background:#fff;border:1px solid #d9e2ec;border-radius:8px;
               padding:12px 16px;margin-bottom:14px;display:flex;gap:24px;flex-wrap:wrap;}}
    .meta-item{{font-size:12px;}} .meta-item b{{color:#0f4c81;}}
    .tc-box{{background:#fff;border:1px solid #d9e2ec;border-radius:8px;
             padding:14px 16px;margin-bottom:14px;}}
    .tc-box h3{{color:#0f4c81;font-size:13px;margin-bottom:8px;}}
    .desc-box{{background:#fff;border:1px solid #d9e2ec;border-radius:8px;padding:22px 26px;}}
    .desc-box h3{{color:rgb(0,113,197);}}
  </style>
</head>
<body>
<div class="hdr">
  <h1>TCD Preview: {_h.escape(title)}</h1>
  <div class="sub">
    <a href="https://hsdes.intel.com/appstore/article-one/#/{tcd_id}" target="_blank">{tcd_id}</a>
    &nbsp;|&nbsp; Status: {_h.escape(status)}
    &nbsp;|&nbsp; Owner: {_h.escape(owner)}
    &nbsp;|&nbsp; Parent TP: <a href="https://hsdes.intel.com/appstore/article-one/#/{parent}" target="_blank">{parent}</a>
    &nbsp;|&nbsp; Preview: {now}
  </div>
</div>
<div class="wrap">
  <div class="notice">
    &#9432; <b>Preview only</b> &mdash; this renders the current HSD description as-is.
    Review carefully, then say <b>&#x201C;update HSD&#x201D;</b> to push any changes.
  </div>
  <div class="tc-box">
    <h3>Test Cases under this TCD ({len(tcs)})</h3>
    {tc_table}
  </div>
  <div class="desc-box">
    {desc_htm}
  </div>
</div>
</body>
</html>"""

    out_path.write_text(html, encoding="utf-8")
    print(f"GENERATED: {out_path}  ({len(html):,} chars, {len(tcs)} TCs)")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Generate TCD description preview HTML")
    p.add_argument("--tcd", required=True, help="TCD HSD ID")
    p.add_argument("--force", action="store_true", help="Overwrite existing")
    args = p.parse_args()
    return generate(args.tcd, force=args.force)


if __name__ == "__main__":
    raise SystemExit(main())
