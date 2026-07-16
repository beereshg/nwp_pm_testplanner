"""
Generate TCD description preview HTML.

KB-FIRST workflow (KB flywheel):
  1. Looks for KB cache at KB/pm_tcd_kb/**/{TCD_ID}*.md
  2. If found, builds structured 8-section HTML from KB (KB-sourced mode)
  3. If not found, fetches current description from HSD (HSD-fallback mode)

Usage:
  python tools/html/generate_tcd_preview.py --tcd <TCD_ID>
  python tools/html/generate_tcd_preview.py --tcd <TCD_ID> --force
  python tools/html/generate_tcd_preview.py --tcd <TCD_ID> --hsd-only  # force HSD fetch

Output:
  tcd_description_output/TCD_{id}_{slug}_preview.html
"""
from __future__ import annotations
import argparse, datetime, html as _h, re, sys
from pathlib import Path

REPO_ROOT   = Path(__file__).resolve().parents[2]
OUTPUT_DIR  = REPO_ROOT / "tcd_description_output"
KB_TCD_ROOT = REPO_ROOT / "KB" / "pm_tcd_kb"
sys.path.insert(0, str(REPO_ROOT))

from hsd_utils import get_session, get_article, get_children


def slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:50]


def find_kb_file(tcd_id: str) -> Path | None:
    matches = list(KB_TCD_ROOT.rglob(f"*{tcd_id}*.md"))
    return matches[0] if matches else None


# ── Markdown → HTML helpers ───────────────────────────────────────────────────

def _convert_inline_md_global(s: str) -> str:
    """Convert inline markdown (bold, code, links, strikethrough) in an already HTML-escaped string."""
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'`([^`]+)`', r'<code style="font-family:Consolas,monospace;font-size:0.9em;">\1</code>', s)
    s = re.sub(r'~~(.+?)~~', r'<del style="color:#888">\1</del>', s)
    def _md_link(m):
        txt, href = m.group(1), m.group(2).replace('&amp;', '&')
        return f'<a href="{href}" target="_blank">{txt}</a>'
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', _md_link, s)
    return s


def md_table(lines: list[str]) -> str:
    rows = [re.split(r"\s*\|\s*", l.strip().strip("|")) for l in lines if l.strip().startswith("|")]
    if len(rows) < 3:
        return ""
    TH = 'style="background:rgb(0,113,197);color:white;padding:7px 10px;text-align:left;"'
    TD = 'style="padding:7px 10px;border-bottom:1px solid #e5e7eb;"'
    TR2 = 'style="background:rgb(248,249,250);"'
    out = '<table style="width:100%;border-collapse:collapse;font-size:0.9em;margin:10px 0;">'
    out += "<thead><tr>" + "".join(f"<th {TH}>{_convert_inline_md_global(_h.escape(c.strip()))}</th>" for c in rows[0]) + "</tr></thead><tbody>"
    for i, row in enumerate(rows[2:]):
        out += f'<tr {TR2 if i%2==0 else ""}>' + "".join(f"<td {TD}>{_convert_inline_md_global(_h.escape(c.strip()))}</td>" for c in row) + "</tr>"
    return out + "</tbody></table>"


def md_bullets(lines: list[str]) -> str:
    items = [re.sub(r"^[-*]\s+", "", l.strip()) for l in lines if l.strip().startswith(("- ", "* "))]
    if not items:
        return ""
    LI = 'style="margin:5px 0;line-height:1.5;"'
    def _inline(s: str) -> str:
        return _convert_inline_md_global(_h.escape(s))
    return '<ul style="margin:10px 0;padding-left:25px;">' + "".join(f"<li {LI}>{_inline(i)}</li>" for i in items) + "</ul>"


def parse_block(text: str, heading: str) -> list[str]:
    lines, in_sec, result = text.splitlines(), False, []
    for line in lines:
        if line.startswith("## "):
            if in_sec:
                break
            if heading.lower() in line.lower():
                in_sec = True
            continue
        if in_sec:
            result.append(line)
    return result


def refs_html(lines: list[str]) -> str:
    out = '<ul style="margin:10px 0;padding-left:25px;line-height:1.8;">'
    for l in lines:
        m = re.match(r"-\s+\[([^\]]+)\]\(([^)]+)\)(.*)", l.strip())
        if m:
            extra = _h.escape(re.sub(r"^\s*[-—]\s*", " — ", m.group(3).strip()))
            out += f'<li style="margin:5px 0;"><a href="{m.group(2)}" target="_blank">{_h.escape(m.group(1))}</a>{extra}</li>'
    return out + "</ul>"


def build_desc_from_kb(kb_text: str) -> tuple[str, list[str]]:
    """Build structured 8-section HSD description HTML from KB markdown.
    Returns (desc_html, source_refs[]).
    """
    SEC = 'style="background:rgb(0,113,197);color:white;padding:15px 25px;font-size:1.3em;font-weight:bold;"'
    CNT = 'style="padding:25px;"'
    H3  = 'style="color:rgb(0,113,197);border-bottom:2px solid rgb(0,113,197);padding-bottom:8px;margin-top:20px;"'
    BOX = 'style="background:rgb(248,249,250);border-left:4px solid rgb(0,113,197);padding:15px;margin:15px 0;"'
    DIV = 'style="background:white;margin-bottom:25px;border-radius:10px;box-shadow:rgba(0,0,0,0.08) 0px 2px 10px;overflow:hidden;"'

    def sec(num, title, body):
        return f"<div {DIV}><div {SEC}>{num}. {title}</div><div {CNT}>{body}</div></div>"

    def h3(t):
        return f"<h3 {H3}>{t}</h3>"

    def table_lines(block):
        return [l for l in block if l.strip().startswith("|")]

    def bullet_lines(block):
        return [l for l in block if l.strip().startswith(("- ", "* "))]

    def _convert_inline_md(s: str) -> str:
        """Convert inline markdown (bold, code, links, strikethrough) in an already HTML-escaped string."""
        return _convert_inline_md_global(s)

    def text_para(block):
        parts = [l.strip() for l in block
                 if l.strip()
                 and not l.strip().startswith(("#", "|", "- ", "* ", "```", "<!--", "<"))
                 and not re.match(r'^\d+[.)\s]', l.strip())]
        if not parts:
            return ""
        # Convert markdown per-line (before joining) to avoid cross-line bold matching issues
        converted = [_convert_inline_md(_h.escape(p)) for p in parts]
        return f'<p style="margin:10px 0 12px;line-height:1.6;">{" ".join(converted)}</p>'

    # --- Section 1: Architecture
    # Support both "What is PCT" (older style) and "Architecture / Micro-arch" (new style)
    what_block = (parse_block(kb_text, "What is PCT")
                  or parse_block(kb_text, "Architecture")
                  or parse_block(kb_text, "Feature Overview"))
    # Cap intro_para at the first raw-html block or code fence — don't include markers as text
    intro_limit = next((i for i, l in enumerate(what_block) if l.strip() in ("<!-- raw-html -->", "```")), 8)
    intro_para = text_para(what_block[:intro_limit])

    # For richer Architecture blocks, render the full block as markdown
    if what_block and len(what_block) > 10:
        arch_extra = ""
        in_pre = False
        in_raw_arch = False
        raw_arch_buf = []
        pre_buf = []
        current_tbl = []
        bullet_lines_all = []
        ol_lines = []

        def flush_table(tbl):
            if not tbl:
                return ""
            return md_table(tbl)

        for l in what_block:
            s = l.strip()
            # Raw HTML passthrough in Architecture block
            if s == "<!-- raw-html -->":
                in_raw_arch = True
                continue
            if s == "<!-- /raw-html -->":
                arch_extra += "\n".join(raw_arch_buf)
                raw_arch_buf, in_raw_arch = [], False
                continue
            if in_raw_arch:
                raw_arch_buf.append(l)
                continue
            if s.startswith("```"):
                if in_pre:
                    arch_extra += f'<pre style="background:rgb(248,249,250);border-left:4px solid rgb(0,113,197);padding:12px;font-family:Consolas,monospace;font-size:0.85em;white-space:pre-wrap;">{_h.escape(chr(10).join(pre_buf))}</pre>'
                    pre_buf = []
                in_pre = not in_pre
            elif in_pre:
                pre_buf.append(l)
            elif s.startswith("|"):
                current_tbl.append(l)
            else:
                # Flush pending table when non-table line encountered
                if current_tbl:
                    arch_extra += flush_table(current_tbl)
                    current_tbl = []
                if s.startswith(("- ", "* ")):
                    if ol_lines:
                        arch_extra += '<ol style="margin:6px 0 10px 16px;line-height:1.7;">'
                        for ol_l in ol_lines:
                            arch_extra += f'<li>{_h.escape(re.sub(r"^\d+[.)\s]+","",ol_l.strip()))}</li>'
                        arch_extra += '</ol>'
                        ol_lines = []
                    bullet_lines_all.append(l)
                elif re.match(r'^\d+[.)]\s', s):
                    if bullet_lines_all:
                        arch_extra += md_bullets(bullet_lines_all)
                        bullet_lines_all = []
                    ol_lines.append(s)
                elif s.startswith("### "):
                    # Sub-heading within Architecture — flush buffers then render as h3
                    if current_tbl:
                        arch_extra += flush_table(current_tbl)
                        current_tbl = []
                    if bullet_lines_all:
                        arch_extra += md_bullets(bullet_lines_all)
                        bullet_lines_all = []
                    if ol_lines:
                        arch_extra += '<ol style="margin:6px 0 10px 16px;line-height:1.7;">'
                        for ol_l in ol_lines:
                            arch_extra += f'<li>{_h.escape(re.sub(r"^\d+[.)\s]+","",ol_l.strip()))}</li>'
                        arch_extra += '</ol>'
                        ol_lines = []
                    arch_extra += h3(s.lstrip("# ").strip())
        # Flush any remaining
        if current_tbl:
            arch_extra += flush_table(current_tbl)
        if bullet_lines_all:
            arch_extra += md_bullets(bullet_lines_all)
        if ol_lines:
            arch_extra += '<ol style="margin:6px 0 10px 16px;line-height:1.7;">'
            for ol_l in ol_lines:
                arch_extra += f'<li>{_h.escape(re.sub(r"^\d+[.)\s]+","",ol_l.strip()))}</li>'
            arch_extra += '</ol>'
    else:
        arch_extra = ""
    freq_tbl   = md_table(table_lines(parse_block(kb_text, "Frequency Hierarchy") or parse_block(kb_text, "Frequency Hierarchy")))
    kd_bullets = md_bullets(bullet_lines(parse_block(kb_text, "Key Design Points")))
    dlcp_bul   = md_bullets(bullet_lines(parse_block(kb_text, "DLCP")))
    xp_bul     = md_bullets(bullet_lines(parse_block(kb_text, "Cross-Product Rules")))
    bios_tbl   = md_table(table_lines(parse_block(kb_text, "BIOS Knobs")))
    dmr_tbl    = md_table(table_lines(parse_block(kb_text, "DMR vs GNR") or parse_block(kb_text, "DMR Changes")))

    body1 = (intro_para + arch_extra +
        (h3("Frequency Hierarchy") + freq_tbl if freq_tbl else "") +
        (h3("Key Design Points") + kd_bullets if kd_bullets else "") +
        (h3("DLCP (Die Level Cherry Picking)") + dlcp_bul if dlcp_bul else "") +
        (h3("Cross-Product Rules") + xp_bul if xp_bul else "") +
        (h3("BIOS Knobs") + bios_tbl if bios_tbl else "") +
        (h3("NWP vs DMR Delta") + dmr_tbl if dmr_tbl else ""))

    def render_block_generic(block, fallback=""):
        """Render a KB section block generically: pre-blocks, tables, bullets, paragraphs.
        Handles multiple tables and sub-headings (###) in order — each ### flushes pending content."""
        if not block:
            return fallback

        def _inline(s):
            s = _h.escape(s)
            return _convert_inline_md(s)

        out = ""
        in_pre, pre_buf = False, []
        in_raw, raw_buf = False, []
        cur_tbl, cur_bul = [], []

        def flush_tbl():
            nonlocal cur_tbl
            if cur_tbl:
                out_tbl = md_table(cur_tbl)
                cur_tbl = []
                return out_tbl
            return ""

        def flush_bul():
            nonlocal cur_bul
            if cur_bul:
                o = md_bullets(cur_bul)
                cur_bul = []
                return o
            return ""

        for l in block:
            s = l.strip()
            # Raw HTML passthrough: <!-- raw-html --> ... <!-- /raw-html -->
            if s == "<!-- raw-html -->":
                out += flush_tbl() + flush_bul()
                in_raw = True
                continue
            if s == "<!-- /raw-html -->":
                out += "\n".join(raw_buf)
                raw_buf, in_raw = [], False
                continue
            if in_raw:
                raw_buf.append(l)
                continue
            if s.startswith("```"):
                out += flush_tbl() + flush_bul()
                if in_pre:
                    out += f'<pre style="background:rgb(248,249,250);border-left:4px solid rgb(0,113,197);padding:12px;font-family:Consolas,monospace;font-size:0.85em;white-space:pre-wrap;">{_h.escape(chr(10).join(pre_buf))}</pre>'
                    pre_buf, in_pre = [], False
                else:
                    in_pre = True
            elif in_pre:
                pre_buf.append(l)
            elif s.startswith("|"):
                out += flush_bul()
                cur_tbl.append(l)
            elif s.startswith(("- ", "* ")):
                out += flush_tbl()
                cur_bul.append(l)
            elif s.startswith("### "):
                out += flush_tbl() + flush_bul()
                out += h3(s.lstrip("# ").strip())
            elif s and not s.startswith("#"):
                out += flush_tbl() + flush_bul()
                out += f'<p style="margin:6px 0 10px;line-height:1.6;">{_inline(s)}</p>'

        out += flush_tbl() + flush_bul()
        return out or fallback

    NOT_APPLICABLE = f'<div {BOX}><p style="color:#666;font-style:italic;margin:0;">Not applicable — see feature context in Section 1.</p></div>'

    # --- Section 2: Interfaces and Protocols
    disc_block = parse_block(kb_text, "Interfaces and Protocols")
    body2 = render_block_generic(disc_block, NOT_APPLICABLE)

    # --- Section 3: Reset, Power, and Clocking
    reset_block = parse_block(kb_text, "Reset, Power") or parse_block(kb_text, "Reset")
    body3 = render_block_generic(reset_block, NOT_APPLICABLE)

    # --- Section 4: Programming Model
    prog_block = parse_block(kb_text, "Programming Model")
    enab_tbl   = md_table(table_lines(prog_block))
    body4 = render_block_generic(prog_block, NOT_APPLICABLE)

    # --- Section 5: Operational Behavior
    ops_block = parse_block(kb_text, "Operational Behavior")
    body5 = render_block_generic(ops_block, NOT_APPLICABLE)

    # --- Section 6: Corner Cases & Error Handling
    corner_block = parse_block(kb_text, "Corner Cases") or parse_block(kb_text, "Corner")
    body6 = render_block_generic(corner_block, NOT_APPLICABLE)

    # --- Section 7: Security / Safety / Policy
    sec7_block = parse_block(kb_text, "Security") or parse_block(kb_text, "Safety")
    body7 = render_block_generic(sec7_block, NOT_APPLICABLE)

    ref_block = parse_block(kb_text, "References")
    body8 = refs_html(ref_block)

    # --- Extra sections: TC Intent Summary, TC Coverage Map, NWP-Specific Deltas, etc.
    #     Any ## Section N: heading that isn't one of the 7 standard sections or References
    extra_sections_html = ""
    standard_keys = {"architecture", "micro-architecture", "interfaces", "protocols",
                     "reset", "power", "clocking", "programming", "operational",
                     "corner", "error", "security", "safety", "policy", "references"}
    all_headings = re.findall(r'^## (?:Section \d+:\s*)?(.*)', kb_text, re.MULTILINE)
    for heading in all_headings:
        h_lower = heading.strip().lower()
        if any(k in h_lower for k in standard_keys):
            continue
        extra_block = parse_block(kb_text, heading.strip().split(":")[0].strip() if ":" in heading else heading.strip())
        if not extra_block:
            # Try with the full heading text
            extra_block = parse_block(kb_text, heading.strip())
        if extra_block:
            extra_body = render_block_generic(extra_block, "")
            if extra_body.strip():
                extra_sections_html += sec("✦", heading.strip(), extra_body)

    desc_html = "".join([
        sec("1", "Architecture / Micro-architecture and Functionality", body1),
        sec("2", "Interfaces and Protocols", body2),
        sec("3", "Reset, Power, and Clocking", body3),
        sec("4", "Programming Model", body4),
        sec("5", "Operational Behavior", body5),
        sec("6", "Corner Cases &amp; Error Handling", body6),
        sec("7", "Security / Safety / Policy", body7),
        extra_sections_html,
        sec("8", "References", body8),
    ])
    source_refs = [m.group(1) for l in ref_block for m in [re.match(r"-\s+\[([^\]]+)\]", l.strip())] if m]
    return desc_html, source_refs


# ── TC table helper ───────────────────────────────────────────────────────────

def build_tc_table(tcs: list[dict]) -> str:
    if not tcs:
        return "<p style='color:#888;font-style:italic'>No TCs found.</p>"
    rows = ""
    for tc in tcs:
        tid  = _h.escape(str(tc.get("id", "")))
        ttl  = _h.escape(tc.get("title", ""))
        st   = _h.escape(tc.get("status", ""))
        env  = _h.escape((tc.get("test_case.val_environment", "") or "")[:35])
        feat = _h.escape(tc.get("test_case.free_tag_1", "") or "")
        col  = "#2e7d32" if st == "open" else "#888"
        rows += (f'<tr><td><a href="https://hsdes.intel.com/appstore/article-one/#/{tid}" target="_blank">{tid}</a></td>'
                 f'<td>{ttl}</td><td style="color:{col}">{st}</td><td>{env}</td><td>{feat}</td></tr>')
    return ('<table style="width:100%;border-collapse:collapse;font-size:12px;margin:8px 0;">'
            '<thead><tr style="background:#e8eef7;">'
            '<th style="padding:6px 8px;text-align:left;">ID</th><th style="padding:6px 8px;text-align:left;">Title</th>'
            '<th style="padding:6px 8px;text-align:left;">Status</th><th style="padding:6px 8px;text-align:left;">Val Env</th>'
            '<th style="padding:6px 8px;text-align:left;">Feature</th>'
            '</tr></thead><tbody>' + rows + '</tbody></table>')


# ── Main generate ─────────────────────────────────────────────────────────────

def generate(tcd_id: str, force: bool = False, hsd_only: bool = False) -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    s = get_session()

    tcd = get_article(tcd_id, fields="id,title,description,status,owner,parent_id", session=s)
    if not tcd:
        print(f"ERROR: TCD {tcd_id} not found"); return 1

    tcs = get_children(tcd_id, "test_case",
        fields="id,title,status,test_case.val_environment,test_case.free_tag_1", session=s)

    title  = tcd.get("title", tcd_id)
    status = tcd.get("status", "")
    owner  = tcd.get("owner", "")
    parent = tcd.get("parent_id", "")
    now    = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    out_path = OUTPUT_DIR / f"TCD_{tcd_id}_{slug(title)}_preview.html"
    if out_path.exists() and not force:
        print(f"SKIP (exists): {out_path.name} -- use --force to overwrite")
        return 0

    # KB-first: use KB cache if available
    kb_file = None if hsd_only else find_kb_file(tcd_id)
    if kb_file:
        kb_text  = kb_file.read_text(encoding="utf-8", errors="replace")
        desc_htm, source_refs = build_desc_from_kb(kb_text)
        source_badge = "KB-SOURCED"
    else:
        desc_htm = tcd.get("description", "") or "<p>No description.</p>"
        source_badge = "HSD-LIVE"

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
    .desc-box{{background:#fff;border:1px solid #d9e2ec;border-radius:8px;padding:22px 26px;}}
  </style>
</head>
<body>
<div class="hdr">
  <h1>TCD Preview: {_h.escape(title)} <span style="background:rgba(255,255,255,.2);border-radius:12px;padding:2px 10px;font-size:11px;">{source_badge}</span></h1>
  <div class="sub">
    <a href="https://hsdes.intel.com/appstore/article-one/#/{tcd_id}" target="_blank">{tcd_id}</a>
    &nbsp;|&nbsp; Status: {_h.escape(status)} &nbsp;|&nbsp; Owner: {_h.escape(owner)}
    &nbsp;|&nbsp; Parent: <a href="https://hsdes.intel.com/appstore/article-one/#/{parent}" target="_blank">{parent}</a>
    &nbsp;|&nbsp; {now}
  </div>
</div>
<div class="wrap">
  <div class="desc-box">{desc_htm}</div>
</div>
</body>
</html>"""

    out_path.write_text(html, encoding="utf-8")
    mode = f"KB:{kb_file.name}" if kb_file else "HSD-live"
    print(f"GENERATED [{mode}]: {out_path}  ({len(html):,} chars, {len(tcs)} TCs)")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Generate TCD description preview HTML (KB-first)")
    p.add_argument("--tcd", required=True, help="TCD HSD ID")
    p.add_argument("--force", action="store_true", help="Overwrite existing")
    p.add_argument("--hsd-only", action="store_true", help="Force HSD fetch even if KB file exists")
    args = p.parse_args()
    return generate(args.tcd, force=args.force, hsd_only=args.hsd_only)


if __name__ == "__main__":
    raise SystemExit(main())
    raise SystemExit(main())
