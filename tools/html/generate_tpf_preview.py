"""
Generate TPF / TP description preview HTML.

KB-FIRST workflow (KB flywheel):
  1. Looks for KB cache at KB/pm_tpf_kb/**/{TPF_ID}*.md
  2. If found, builds 8-section HTML from KB (KB-sourced mode)
  3. If not found, fetches current description from HSD (HSD-fallback mode)

TPF 8-section structure (Phoenix §3.1 aligned):
  1. Feature Classification & Introduction
  2. Design Details          ← architecture diagrams / block flows (extracted from TCDs)
  3. Validation Strategy     ← tier rationale (PSS / FV / PV)
  4. Tier Coverage           ← bug coverage matrix, scenario coverage
  5. Risks & Dependencies
  6. DFX Considerations
  7. Common Corner Cases     ← cross-TCD corner cases
  8. TCD Coverage Summary & References

Usage:
  python tools/html/generate_tpf_preview.py --tpf <TPF_ID>
  python tools/html/generate_tpf_preview.py --tpf <TPF_ID> --force
  python tools/html/generate_tpf_preview.py --tpf <TPF_ID> --hsd-only

Output:
  tpf_description_output/TPF_{id}_{slug}_preview.html
"""
from __future__ import annotations
import argparse, datetime, html as _h, re, sys
from pathlib import Path

REPO_ROOT   = Path(__file__).resolve().parents[2]
OUTPUT_DIR  = REPO_ROOT / "tpf_description_output"
KB_TPF_ROOT = REPO_ROOT / "KB" / "pm_tpf_kb"

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).parent))

# Reuse rendering utilities from TCD generator — no duplication
from generate_tcd_preview import (
    slug, parse_block, md_table, md_bullets, refs_html,
    _convert_inline_md_global,
)
from hsd_utils import get_session, get_article, get_children


def find_tpf_kb_file(tpf_id: str) -> Path | None:
    matches = list(KB_TPF_ROOT.rglob(f"*{tpf_id}*.md"))
    return matches[0] if matches else None


# ── TPF-specific renderer ──────────────────────────────────────────────────────

def build_tpf_desc_from_kb(kb_text: str) -> str:
    """Build structured 8-section TPF HTML from KB markdown."""
    SEC = 'style="background:rgb(0,113,197);color:white;padding:15px 25px;font-size:1.3em;font-weight:bold;"'
    CNT = 'style="padding:25px;"'
    H3  = 'style="color:rgb(0,113,197);border-bottom:2px solid rgb(0,113,197);padding-bottom:8px;margin-top:20px;"'
    BOX = 'style="background:rgb(248,249,250);border-left:4px solid rgb(0,113,197);padding:15px;margin:15px 0;"'
    DIV = 'style="background:white;margin-bottom:25px;border-radius:10px;box-shadow:rgba(0,0,0,0.08) 0px 2px 10px;overflow:hidden;"'
    NA  = f'<div {BOX}><p style="color:#666;font-style:italic;margin:0;">Not documented.</p></div>'

    def sec(num, title, body):
        return f"<div {DIV}><div {SEC}>{num}. {title}</div><div {CNT}>{body}</div></div>"

    def h3(t):
        return f'<h3 {H3}>{_h.escape(t)}</h3>'

    def _inline(s: str) -> str:
        return _convert_inline_md_global(_h.escape(s))

    def render_block(block: list[str], fallback: str = "") -> str:
        """Generic markdown → HTML renderer for a KB section block."""
        if not block:
            return fallback or NA
        out = ""
        in_pre, pre_buf, pre_lang = False, [], ""
        in_raw, raw_buf = False, []
        cur_tbl: list[str] = []
        cur_bul: list[str] = []
        cur_ol:  list[str] = []

        def flush_pending() -> str:
            nonlocal cur_tbl, cur_bul, cur_ol
            r = ""
            if cur_tbl:
                r += md_table(cur_tbl); cur_tbl = []
            if cur_bul:
                r += md_bullets(cur_bul); cur_bul = []
            if cur_ol:
                r += '<ol style="margin:6px 0 10px 16px;line-height:1.7;">'
                for li in cur_ol:
                    r += f'<li>{_inline(re.sub(r"^\\d+[.)\\s]+", "", li.strip()))}</li>'
                r += '</ol>'
                cur_ol = []
            return r

        for line in block:
            s = line.strip()
            if s == "<!-- raw-html -->":
                out += flush_pending(); in_raw = True; continue
            if s == "<!-- /raw-html -->":
                out += "\n".join(raw_buf); raw_buf, in_raw = [], False; continue
            if in_raw:
                raw_buf.append(line); continue
            if s.startswith("```"):
                out += flush_pending()
                if in_pre:
                    content = "\n".join(pre_buf)
                    if pre_lang == "mermaid":
                        out += f'<div class="mermaid" style="background:#f8fafc;padding:16px;border-radius:6px;margin:12px 0;">{content}</div>'
                    else:
                        out += f'<pre style="background:rgb(248,249,250);border-left:4px solid rgb(0,113,197);padding:12px;font-family:Consolas,monospace;font-size:0.85em;white-space:pre-wrap;">{_h.escape(content)}</pre>'
                    pre_buf, in_pre, pre_lang = [], False, ""
                else:
                    pre_lang = s[3:].strip().lower(); in_pre = True
                continue
            if in_pre:
                pre_buf.append(line); continue
            if s.startswith("|"):
                out += md_bullets(cur_bul) if cur_bul else ""
                cur_bul = []; cur_tbl.append(line)
            elif s.startswith(("- ", "* ")):
                out += md_table(cur_tbl) if cur_tbl else ""
                cur_tbl = []; cur_bul.append(line)
            elif re.match(r"^\d+[.)]\s", s):
                out += flush_pending(); cur_ol.append(s)
            elif s.startswith("### "):
                out += flush_pending(); out += h3(s.lstrip("# ").strip())
            elif s and not s.startswith("#"):
                out += flush_pending()
                out += f'<p style="margin:6px 0 10px;line-height:1.6;">{_inline(s)}</p>'

        out += flush_pending()
        return out or fallback or NA

    # TPF sections: (section_number, html_label, kb_heading_keyword)
    SECTIONS = [
        ("1", "Feature Classification &amp; Introduction", "Feature Classification"),
        ("2", "Design Details",                             "Design Details"),
        ("3", "Validation Strategy",                        "Validation Strategy"),
        ("4", "Tier Coverage",                              "Tier Coverage"),
        ("5", "Risks &amp; Dependencies",                   "Risks"),
        ("6", "DFX Considerations",                         "DFX"),
        ("7", "Common Corner Cases",                        "Common Corner"),
        ("8", "TCD Coverage Summary &amp; References",      "TCD Coverage"),
    ]

    html = ""
    for num, label, key in SECTIONS:
        block = parse_block(kb_text, key)
        if num == "8":
            # Section 8: render ref bullet links + any other content
            ref_lines = [l for l in block if re.match(r"-\s+\[", l.strip())]
            body = refs_html(ref_lines) if ref_lines else render_block(block)
        else:
            body = render_block(block)
        html += sec(num, label, body)
    return html


# ── TCD summary table ─────────────────────────────────────────────────────────

def build_tcd_table(tcds: list[dict]) -> str:
    if not tcds:
        return "<p style='color:#888;font-style:italic;margin:4px 0;'>No TCDs found.</p>"
    TH = 'style="background:#1e3a5f;color:white;padding:6px 10px;text-align:left;font-size:11px;"'
    TD = 'style="padding:6px 10px;border-bottom:1px solid #e5e7eb;font-size:12px;"'
    TR2 = 'style="background:rgb(248,249,250);"'
    rows = ""
    for i, t in enumerate(tcds):
        tid = _h.escape(str(t.get("id", "")))
        ttl = _h.escape(t.get("title", ""))
        st  = _h.escape(t.get("status", ""))
        col = "#2e7d32" if st == "open" else "#888"
        rows += (f'<tr {TR2 if i%2==0 else ""}>'
                 f'<td {TD}><a href="https://hsdes.intel.com/appstore/article-one/#/{tid}" target="_blank">{tid}</a></td>'
                 f'<td {TD}>{ttl}</td>'
                 f'<td {TD} style="color:{col}">{st}</td></tr>')
    return (f'<table style="width:100%;border-collapse:collapse;">'
            f'<thead><tr><th {TH}>TCD ID</th><th {TH}>Title</th><th {TH}>Status</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>')


# ── Main generate ─────────────────────────────────────────────────────────────

def generate(tpf_id: str, force: bool = False, hsd_only: bool = False) -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    s = get_session()

    tpf = get_article(tpf_id, fields="id,title,description,status,owner,parent_id", session=s)
    if not tpf:
        print(f"ERROR: TPF {tpf_id} not found in HSD"); return 1

    tcds = get_children(tpf_id, "test_case_definition",
                        fields="id,title,status", session=s)

    title  = tpf.get("title", tpf_id)
    status = tpf.get("status", "")
    owner  = tpf.get("owner", "")
    parent = str(tpf.get("parent_id", ""))
    now    = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    out_path = OUTPUT_DIR / f"TPF_{tpf_id}_{slug(title)}_preview.html"
    if out_path.exists() and not force:
        print(f"SKIP (exists): {out_path.name}  -- use --force to overwrite"); return 0

    kb_file = None if hsd_only else find_tpf_kb_file(tpf_id)
    if kb_file:
        kb_text      = kb_file.read_text(encoding="utf-8", errors="replace")
        desc_html    = build_tpf_desc_from_kb(kb_text)
        source_badge = "KB-SOURCED"
        source_note  = str(kb_file.relative_to(REPO_ROOT))
    else:
        desc_html    = tpf.get("description", "") or "<p>No description.</p>"
        source_badge = "HSD-LIVE"
        source_note  = "fetched from HSD"

    tcd_tbl      = build_tcd_table(tcds)
    parent_link  = (f'<a href="https://hsdes.intel.com/appstore/article-one/#/{_h.escape(parent)}"'
                    f' target="_blank" style="color:#90caf9;">{_h.escape(parent or "—")}</a>')

    html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>TPF Preview: {_h.escape(title)}</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({{startOnLoad:true,theme:'default',themeVariables:{{primaryColor:'#e8eef7',primaryBorderColor:'#0f4c81'}}}});</script>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:'Segoe UI',Arial,sans-serif;background:#f0f4f9;font-size:13px;color:#1f2937;}}
    .hdr{{background:#0f4c81;color:#fff;padding:14px 24px;}}
    .hdr h1{{font-size:17px;font-weight:600;}}
    .hdr .sub{{font-size:11px;opacity:.82;margin-top:4px;}}
    .hdr a{{color:#90caf9;}}
    .badge{{background:rgba(255,255,255,.2);border-radius:12px;padding:2px 10px;font-size:11px;margin-left:8px;}}
    .wrap{{max-width:960px;margin:18px auto;padding:0 16px 40px;}}
    .desc-box{{}}
  </style>
</head>
<body>
<div class="hdr">
  <h1>TPF Preview: {_h.escape(title)} <span class="badge">{source_badge}</span></h1>
  <div class="sub">
    <a href="https://hsdes.intel.com/appstore/article-one/#/{tpf_id}" target="_blank">{tpf_id}</a>
    &nbsp;|&nbsp; Parent TP: {parent_link}
    &nbsp;|&nbsp; Status: {_h.escape(status)} &nbsp;|&nbsp; Owner: {_h.escape(owner)}
    &nbsp;|&nbsp; Generated: {now} &nbsp;|&nbsp; Source: {_h.escape(source_note)}
  </div>
</div>
<div class="wrap">
  <div class="desc-box">
    {desc_html}
  </div>
</div>
</body>
</html>"""

    out_path.write_text(html_out, encoding="utf-8")
    print(f"GENERATED [{source_badge}:{kb_file.name if kb_file else 'live'}]: {out_path}  ({len(html_out):,} chars, {len(tcds)} TCDs)")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate TPF description preview HTML")
    ap.add_argument("--tpf",      required=True,        help="TPF / TP HSD ID")
    ap.add_argument("--force",    action="store_true",  help="Overwrite existing output")
    ap.add_argument("--hsd-only", action="store_true",  help="Skip KB cache, fetch from HSD")
    args = ap.parse_args()
    sys.exit(generate(args.tpf, args.force, getattr(args, "hsd_only", False)))
