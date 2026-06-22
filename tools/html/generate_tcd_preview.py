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

def md_table(lines: list[str]) -> str:
    rows = [re.split(r"\s*\|\s*", l.strip().strip("|")) for l in lines if l.strip().startswith("|")]
    if len(rows) < 3:
        return ""
    TH = 'style="background:rgb(0,113,197);color:white;padding:7px 10px;text-align:left;"'
    TD = 'style="padding:7px 10px;border-bottom:1px solid #e5e7eb;"'
    TR2 = 'style="background:rgb(248,249,250);"'
    out = '<table style="width:100%;border-collapse:collapse;font-size:0.9em;margin:10px 0;">'
    out += "<thead><tr>" + "".join(f"<th {TH}>{_h.escape(c.strip())}</th>" for c in rows[0]) + "</tr></thead><tbody>"
    for i, row in enumerate(rows[2:]):
        out += f'<tr {TR2 if i%2==0 else ""}>' + "".join(f"<td {TD}>{_h.escape(c.strip())}</td>" for c in row) + "</tr>"
    return out + "</tbody></table>"


def md_bullets(lines: list[str]) -> str:
    items = [re.sub(r"^[-*]\s+", "", l.strip()) for l in lines if l.strip().startswith(("- ", "* "))]
    if not items:
        return ""
    LI = 'style="margin:5px 0;line-height:1.5;"'
    return '<ul style="margin:10px 0;padding-left:25px;">' + "".join(f"<li {LI}>{_h.escape(i)}</li>" for i in items) + "</ul>"


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

    def text_para(block):
        parts = [l.strip() for l in block if l.strip() and not l.strip().startswith(("#", "|", "-", "*", "```"))]
        return f'<p style="margin:10px 0 12px;line-height:1.6;">{_h.escape(" ".join(parts))}</p>' if parts else ""

    # --- Section 1: Architecture
    what_block = parse_block(kb_text, "What is PCT")
    intro_para = text_para(what_block[:6])
    freq_tbl   = md_table(table_lines(parse_block(kb_text, "Frequency Hierarchy") or parse_block(kb_text, "Frequency Hierarchy")))
    kd_bullets = md_bullets(bullet_lines(parse_block(kb_text, "Key Design Points")))
    dlcp_bul   = md_bullets(bullet_lines(parse_block(kb_text, "DLCP")))
    xp_bul     = md_bullets(bullet_lines(parse_block(kb_text, "Cross-Product Rules")))
    bios_tbl   = md_table(table_lines(parse_block(kb_text, "BIOS Knobs")))
    dmr_tbl    = md_table(table_lines(parse_block(kb_text, "DMR vs GNR") or parse_block(kb_text, "DMR Changes")))

    body1 = (intro_para +
        (h3("Frequency Hierarchy") + freq_tbl if freq_tbl else "") +
        (h3("Key Design Points") + kd_bullets if kd_bullets else "") +
        (h3("DLCP (Die Level Cherry Picking)") + dlcp_bul if dlcp_bul else "") +
        (h3("Cross-Product Rules") + xp_bul if xp_bul else "") +
        (h3("BIOS Knobs") + bios_tbl if bios_tbl else "") +
        (h3("NWP vs DMR Delta") + dmr_tbl if dmr_tbl else ""))

    # --- Section 2: Interfaces
    disc_block = parse_block(kb_text, "Interfaces and Protocols")
    body2 = h3("Discovery Registers") + (md_table(table_lines(disc_block)) or "")

    # --- Section 3: Reset
    body3 = (f'<div {BOX}><ul style="margin:0;padding-left:20px;line-height:1.8;">'
        "<li>PCT CLOS state is not retained across reset; must be reprogrammed at every boot</li>"
        "<li>PrimeCode reads SST_TF fuses at reset Phase 5 → writes SST_TF_INFO_0/2/10</li>"
        "<li>BIOS reprogram SST_CLOS_CONFIG/ASSOC, SST_CP_CONTROL, MSR 0x1AD after each boot</li>"
        "</ul></div>")

    # --- Section 4: Programming Model
    prog_block = parse_block(kb_text, "Programming Model")
    enab_tbl   = md_table(table_lines(prog_block))
    enab_pre   = ('<pre style="background:rgb(248,249,250);border-left:4px solid rgb(0,113,197);'
        'padding:15px;font-family:Consolas,monospace;font-size:0.88em;white-space:pre-wrap;">'
        'Boot sequence: PrimeCode Phase 5 \u2192 BIOS CPL3 CLOS programming \u2192 MSR 0x1AD override\n'
        'HP selection (NWP): 96 cores \u00f7 4 partitions = 24/partition; first 2 cores = HP \u21d2 8 HP total\n'
        'Note: MSR 0x1AD must be SST_TF_INFO_2.RATIO_0 (0xFF invalid, HSD 14025997048)</pre>')
    body4 = h3("Enabling Path") + enab_pre + enab_tbl

    # --- Section 5: Operational
    tc_block = parse_block(kb_text, "Test Cases")
    tc_tbl   = md_table(table_lines(tc_block))
    tc_tbl   = re.sub(r"\[(\d{10,})\]\([^)]+\)",
        lambda m: f'<a href="https://hsdes.intel.com/appstore/article-one/#/{m.group(1)}" target="_blank">{m.group(1)}</a>',
        tc_tbl)
    body5 = h3("Test Cases") + (tc_tbl or "<p>No TCs in KB file.</p>")

    # --- Sections 6–8 (compact)
    body6 = (f'<div {BOX}><ul style="margin:0;padding-left:20px;line-height:1.8;">'
        "<li>PCT Partition Count = 0 \u2192 conventional turbo fallback</li>"
        "<li>Uneven core count: surplus PCT cores become LP (not HP)</li>"
        "<li>DLCP SKU: SST_CLOS_ASSOC is ignored; Pcode uses PCT_Module_Mask fuse exclusively</li>"
        "<li>Mutex: SST-BF + PCT both enabled = DQ rule violation</li>"
        "</ul></div>")
    body7 = (f'<div {BOX}><ul style="margin:0;padding-left:20px;line-height:1.8;">'
        "<li>PCT is SoC-wide: non-HP cores are LP-clipped for all VMs once SST-TF is active</li>"
        "<li>TPMI lock bit: prevents OS from overriding CLOS assignments post-CPL3</li>"
        "<li>DLCP: HP core positions are fuse-fixed; SW cannot reassign HP on DLCP SKUs</li>"
        "</ul></div>")
    ref_block = parse_block(kb_text, "References")
    body8 = refs_html(ref_block)

    desc_html = "".join([
        sec("1", "Architecture / Micro-architecture and Functionality", body1),
        sec("2", "Interfaces and Protocols", body2),
        sec("3", "Reset, Power, and Clocking", body3),
        sec("4", "Programming Model", body4),
        sec("5", "Operational Behavior", body5),
        sec("6", "Corner Cases &amp; Error Handling", body6),
        sec("7", "Security / Safety / Policy", body7),
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
        notice_color = "#e8f5e9"
        notice_border = "#a5d6a7"
        notice_text = "#1b5e20"
        notice_icon = "&#10003;"
        notice_msg = (f"<b>KB-sourced preview</b> &mdash; built from "
                      f"<code>{kb_file.relative_to(REPO_ROOT)}</code>. "
                      f"Sources: {', '.join(source_refs[:4])}{'...' if len(source_refs) > 4 else ''}."
                      f" Say <b>&quot;update HSD&quot;</b> to push.")
    else:
        desc_htm = tcd.get("description", "") or "<p>No description.</p>"
        source_badge = "HSD-LIVE"
        notice_color = "#fff8e1"
        notice_border = "#ffe082"
        notice_text = "#7a5c00"
        notice_icon = "&#9432;"
        notice_msg = ("&#9432; <b>HSD-live preview</b> &mdash; showing current HSD description. "
                      "No KB file found for this TCD. Review, then say <b>&quot;update HSD&quot;</b> to push changes.")

    tc_table = build_tc_table(tcs)

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
    .notice{{background:{notice_color};border:1px solid {notice_border};border-radius:6px;
             padding:10px 14px;margin-bottom:14px;font-size:12px;color:{notice_text};}}
    .tc-box{{background:#fff;border:1px solid #d9e2ec;border-radius:8px;padding:14px 16px;margin-bottom:14px;}}
    .tc-box h3{{color:#0f4c81;font-size:13px;margin-bottom:8px;}}
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
  <div class="notice">{notice_icon} {notice_msg}</div>
  <div class="tc-box">
    <h3>Test Cases ({len(tcs)})</h3>{tc_table}
  </div>
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
