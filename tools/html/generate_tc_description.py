#!/usr/bin/env python3
"""
Generate TC description HTML from KB/pm_tc_kb inference.md files.

Uses KB/templates/tc_hsd_description.html.j2 — same format as HSD TC description field
(Validation Scope, Preconditions, Test Steps, Health Check, Post-Process, References).

Usage:
  python tools/html/generate_tc_description.py --hsd 22022422105
  python tools/html/generate_tc_description.py --hsd 22022422105 --force

Output:
  KB/pm_tc_deepanalysis/HSD_{id}_{slug}_tc_desc.html
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

try:
    from jinja2 import Environment, FileSystemLoader
    _JINJA = True
except ImportError:
    _JINJA = False

TEMPLATE_DIR = REPO_ROOT / "KB" / "templates"
CACHE_ROOT   = REPO_ROOT / "KB" / "pm_tc_kb"
OUTPUT_DIR   = REPO_ROOT / "tc_description_output"


# ─── Markdown parser helpers ──────────────────────────────────────────────────

def _strip_bold(s: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"\1", s).strip()


def _parse_table(lines: list[str]) -> list[dict]:
    """Parse a markdown table into list of dicts keyed by header."""
    rows = [re.split(r"\s*\|\s*", l.strip().strip("|")) for l in lines if l.strip().startswith("|")]
    if len(rows) < 3:
        return []
    headers = [h.strip().lower() for h in rows[0]]
    result = []
    for row in rows[2:]:
        if row and not all(re.fullmatch(r"[-: ]+", c or "") for c in row):
            entry = {}
            for i, h in enumerate(headers):
                entry[h] = row[i].strip() if i < len(row) else ""
            result.append(entry)
    return result


def _section_lines(text: str, heading: str) -> list[str]:
    """Return lines under a given ## or ### heading until the next heading of same/higher level."""
    lines = text.splitlines()
    depth = heading.count("#")
    in_section = False
    result = []
    for line in lines:
        if re.match(r"^#{1,6}\s", line):
            cur_depth = len(line) - len(line.lstrip("#"))
            if re.match(r"^#{1,6}\s+" + re.escape(heading.lstrip("#").strip()), line):
                in_section = True
                continue
            if in_section and cur_depth <= depth:
                break
        elif in_section:
            result.append(line)
    return result


def _text_block(lines: list[str]) -> str:
    """Join lines into a clean paragraph string."""
    return " ".join(l.strip() for l in lines if l.strip() and not l.strip().startswith("|"))


# ─── Section extractors ───────────────────────────────────────────────────────

def extract_scope(text: str) -> str:
    for heading in ("## Test Case Intent", "### Refined Intent"):
        lines = _section_lines(text, heading)
        # stop at first sub-heading OR first bullet/dash line (preconditions / PASS/FAIL)
        trimmed = []
        for l in lines:
            s = l.strip()
            if s.startswith("###") or s.startswith("- ") or s.startswith("* "):
                break
            trimmed.append(l)
        block = _text_block(trimmed)
        if block:
            return block
    # fallback: first non-heading paragraph
    for line in text.splitlines():
        s = line.strip()
        if s and not s.startswith("#") and not s.startswith("|") and not s.startswith("```"):
            return s
    return ""


def extract_preconditions(text: str) -> list[dict]:
    """Return list of {item, requirement} — supports both table and bullet-list format."""
    for heading in ("### Pre-Conditions", "## Pre-Conditions", "### Preconditions"):
        lines = _section_lines(text, heading)
        # Try table first
        table_lines = [l for l in lines if l.strip().startswith("|")]
        rows = _parse_table(table_lines)
        if rows:
            result = []
            for r in rows:
                item = r.get("item") or r.get("#") or r.get(list(r.keys())[0] if r else "") or ""
                req  = r.get("requirement") or r.get(list(r.keys())[1] if len(r) > 1 else "") or ""
                result.append({"item": _strip_bold(item), "requirement": _strip_bold(req)})
            if result:
                return result
        # Fall back to bullet list
        bullet_lines = [l for l in lines if l.strip().startswith("- ")]
        if bullet_lines:
            result = []
            for i, l in enumerate(bullet_lines, 1):
                req = re.sub(r"^-\s+", "", l.strip())
                req = re.sub(r"`([^`]+)`", r"\1", req)  # strip backticks
                result.append({"item": str(i), "requirement": _strip_bold(req)})
            return result
    return []


def extract_steps(text: str) -> list[dict]:
    """Return list of {action, expected, failure}."""
    for heading in ("### Test Steps", "## Test Steps", "### Adapted Test Steps"):
        lines = _section_lines(text, heading)
        table_lines = [l for l in lines if l.strip().startswith("|")]
        rows = _parse_table(table_lines)
        if rows:
            result = []
            for r in rows:
                keys = list(r.keys())
                action   = r.get("action") or (r.get(keys[1]) if len(keys) > 1 else "") or ""
                expected = (r.get("expected result (pass)") or r.get("expected result") or
                            r.get("expected") or r.get("nwp adaptation") or
                            (r.get(keys[2]) if len(keys) > 2 else "") or "")
                failure  = (r.get("failure indication") or r.get("failure") or
                            (r.get(keys[3]) if len(keys) > 3 else "") or "")
                result.append({
                    "action":   _strip_bold(action),
                    "expected": _strip_bold(expected),
                    "failure":  _strip_bold(failure),
                })
            if result:
                return result
    return []


def extract_health_checks(text: str) -> list[dict]:
    """Return list of {name, access, criteria}."""
    for heading in ("### Health Checks", "## Health Check", "| Category |"):
        lines = _section_lines(text, heading) if not heading.startswith("|") else []
        if not lines:
            # try Section D register table
            lines = _section_lines(text, "## Section D: Spec Refs")
        table_lines = [l for l in lines if l.strip().startswith("|")]
        rows = _parse_table(table_lines)
        if rows:
            result = []
            for r in rows:
                keys = list(r.keys())
                name     = r.get("register") or r.get("register / log") or r.get("category") or (r.get(keys[0]) if keys else "") or ""
                access   = r.get("access") or r.get("field/offset") or (r.get(keys[1]) if len(keys) > 1 else "") or ""
                criteria = r.get("pass/fail criteria") or r.get("expected") or (r.get(keys[2]) if len(keys) > 2 else "") or ""
                if name and not name.lower().startswith("---"):
                    result.append({"name": _strip_bold(name), "access": _strip_bold(access), "criteria": _strip_bold(criteria)})
            if result:
                return result
    return []


def extract_passfail(text: str) -> dict:
    """Return {'pass': str, 'fail': str} from ### Pass / Fail Criteria section."""
    for heading in ("### Pass / Fail Criteria", "### Pass/Fail Criteria", "## Pass/Fail Criteria"):
        lines = _section_lines(text, heading)
        pass_str = fail_str = ""
        for l in lines:
            s = l.strip()
            if re.match(r"^-?\s*\*{0,2}PASS\*{0,2}:?", s, re.I):
                pass_str = _strip_bold(re.sub(r"^-?\s*\*{0,2}PASS\*{0,2}:?\s*", "", s, flags=re.I))
            elif re.match(r"^-?\s*\*{0,2}FAIL\*{0,2}:?", s, re.I):
                fail_str = _strip_bold(re.sub(r"^-?\s*\*{0,2}FAIL\*{0,2}:?\s*", "", s, flags=re.I))
        if pass_str or fail_str:
            return {"pass": pass_str, "fail": fail_str}
    return {}


def extract_notes(text: str) -> list[str]:
    """Return list of note strings from risk/open/notes sections."""
    notes = []
    for heading in ("## Section E: Risk Assessment", "### Notes", "## User Notes"):
        lines = _section_lines(text, heading)
        table_lines = [l for l in lines if l.strip().startswith("|")]
        rows = _parse_table(table_lines)
        for r in rows:
            keys = list(r.keys())
            risk = r.get("risk / open item") or r.get("risk") or (r.get(keys[1]) if len(keys) > 1 else "") or ""
            note = r.get("notes") or r.get("mitigation") or (r.get(keys[3]) if len(keys) > 3 else "") or ""
            if risk.strip():
                notes.append(f"{_strip_bold(risk)}" + (f" — {_strip_bold(note)}" if note.strip() else ""))
    return notes


def extract_opens(text: str) -> list[str]:
    opens = []
    for heading in ("## Section E: Risk Assessment",):
        lines = _section_lines(text, heading)
        table_lines = [l for l in lines if l.strip().startswith("|")]
        rows = _parse_table(table_lines)
        for r in rows:
            keys = list(r.keys())
            sev = r.get("likelihood") or r.get("severity") or (r.get(keys[2]) if len(keys) > 2 else "") or ""
            if sev.lower() in ("high", "medium"):
                risk = r.get("risk / open item") or r.get("risk") or (r.get(keys[1]) if len(keys) > 1 else "") or ""
                mit  = r.get("mitigation") or r.get("notes") or (r.get(keys[3]) if len(keys) > 3 else "") or ""
                if risk.strip():
                    opens.append(f"{_strip_bold(risk)}" + (f" → {_strip_bold(mit)}" if mit.strip() else ""))
    return opens


def extract_refs(text: str) -> tuple[list[dict], dict]:
    """Return (fr_hsd list, specs dict)."""
    fr_hsd = []
    specs  = {}
    for heading in ("## Section D: Spec Refs", "## KB References", "### Reference Documents"):
        lines = _section_lines(text, heading)
        for line in lines:
            # markdown link: [text](url)
            for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", line):
                title, url = match.group(1), match.group(2)
                hsd_m = re.search(r"hsdes.*?/(\d{10,})", url)
                if hsd_m:
                    fr_hsd.append({"id": hsd_m.group(1), "title": title})
                elif url.startswith("http"):
                    key = re.sub(r"\W+", "_", title)[:30]
                    specs[key] = {"name": title, "url": url}
    # deduplicate
    seen = set()
    fr_hsd_u = []
    for f in fr_hsd:
        if f["id"] not in seen:
            seen.add(f["id"])
            fr_hsd_u.append(f)
    return fr_hsd_u, specs


def extract_post_process(text: str) -> str:
    # Only use a dedicated Post-Process section — never pull from Section F
    for heading in ("## Post-Process", "### Post-Process", "#### Post-Process"):
        lines = _section_lines(text, heading)
        block = _text_block(lines[:5])
        if block and block.strip().upper() != "N/A":
            return block
    return "N/A"


# ─── Main ─────────────────────────────────────────────────────────────────────

def find_inference_file(hsd_id: str, segment: str | None = None) -> Path | None:
    pattern = f"**/*{hsd_id}*.inference.md"
    files = sorted(CACHE_ROOT.rglob(pattern))
    if segment:
        files = [f for f in files if f"/{segment}/" in f.as_posix()]
    return files[0] if files else None


def render_fallback(tc: dict, config: dict, title: str) -> str:
    """Plain-HTML fallback when Jinja2 is unavailable."""
    TH = 'style="background:#e8f0fe;text-align:left;padding:8px;"'
    TD = 'style="text-align:left;vertical-align:top;padding:8px;"'
    HDR = ('style="background:#cce4f7;color:#004a80;padding:12px 20px;'
           'font-size:1.2em;font-weight:bold;border-left:4px solid #0071c5;'
           'border-radius:0 6px 6px 0;"')
    lines = [f'<div style="font-family:Segoe UI,Arial,sans-serif;font-size:13px;color:#333;line-height:1.6;">']
    lines += [f'<div {HDR}>Validation Scope</div><br/>',
              f'<p style="margin:10px 0 16px 0;">{tc.get("scope","")}</p><br/>']
    if tc.get("preconditions"):
        lines += [f'<div {HDR}>Preconditions</div><br/>',
                  '<table style="width:100%;border-collapse:collapse;margin:10px 0 16px 0;font-size:0.9em;" border="1" cellpadding="6">',
                  f'<tr><th {TH}>Item</th><th {TH}>Requirement</th></tr>']
        for p in tc["preconditions"]:
            lines.append(f'<tr><td {TD}>{p["item"]}</td><td {TD}>{p["requirement"]}</td></tr>')
        lines += ['</table><br/>']
    if tc.get("steps"):
        lines += [f'<div {HDR}>Test Steps</div><br/>',
                  '<table style="width:100%;border-collapse:collapse;margin:10px 0 8px 0;font-size:0.9em;" border="1" cellpadding="6">',
                  f'<tr><th {TH}>#</th><th {TH}>Action</th><th {TH}>Expected Result (PASS)</th><th {TH}>Failure Indication</th></tr>']
        for i, s in enumerate(tc["steps"], 1):
            lines.append(f'<tr><td {TD}>{i}</td><td {TD}>{s["action"]}</td><td {TD}>{s["expected"]}</td><td {TD}>{s["failure"]}</td></tr>')
        lines += ['</table>']
    # ── Pass / Fail Criteria ──
    pf = tc.get("passfail", {})
    if pf:
        PF_HDR = ('style="background:#cce4f7;color:#004a80;padding:12px 20px;'
                  'font-size:1.2em;font-weight:bold;border-left:4px solid #0071c5;'
                  'border-radius:0 6px 6px 0;"')
        PASS_BOX = ('style="display:flex;align-items:flex-start;gap:10px;background:#e8f5e9;'
                    'border-left:4px solid #2e7d32;border-radius:0 4px 4px 0;'
                    'padding:10px 14px;margin:6px 0 4px;"')
        FAIL_BOX = ('style="display:flex;align-items:flex-start;gap:10px;background:#fff3f3;'
                    'border-left:4px solid #c62828;border-radius:0 4px 4px 0;'
                    'padding:10px 14px;margin:4px 0 12px;"')
        BADGE_P = ('style="min-width:46px;font-weight:bold;color:#2e7d32;'
                   'background:#c8e6c9;border-radius:4px;padding:2px 8px;'
                   'font-size:0.85em;text-align:center;"')
        BADGE_F = ('style="min-width:46px;font-weight:bold;color:#b71c1c;'
                   'background:#ffcdd2;border-radius:4px;padding:2px 8px;'
                   'font-size:0.85em;text-align:center;"')
        TEXT_S  = 'style="margin:0;font-size:0.9em;"'
        lines.append(f'<br/><div {PF_HDR}>Pass / Fail Criteria</div><br/>')
        if pf.get("pass"):
            lines.append(f'<div {PASS_BOX}><span {BADGE_P}>PASS</span><p {TEXT_S}>{pf["pass"]}</p></div>')
        if pf.get("fail"):
            lines.append(f'<div {FAIL_BOX}><span {BADGE_F}>FAIL</span><p {TEXT_S}>{pf["fail"]}</p></div>')
    if tc.get("notes"):
        lines += ['<h3>NOTEs</h3><div style="font-size:0.85em;color:#555;margin-left:12px;padding:10px;background:#f8f9fa;border-left:3px solid #999;">']
        for n in tc["notes"]:
            lines.append(f'<p style="margin:6px 0;">{n}</p>')
        lines += ['</div>']
    if tc.get("opens"):
        lines += ['<h3>OPENs</h3><div style="font-size:0.85em;color:#c62828;margin-left:12px;padding:10px;background:#fff3f3;border-left:3px solid #c62828;"><ul>']
        for o in tc["opens"]:
            lines.append(f'<li style="margin:4px 0;">{o}</li>')
        lines += ['</ul></div>']
    if tc.get("health_checks"):
        lines += [f'<br/><div {HDR}>Health Check — Registers &amp; Logs to Collect</div><br/>',
                  '<table style="width:100%;border-collapse:collapse;margin:10px 0 16px 0;font-size:0.9em;" border="1" cellpadding="6">',
                  f'<tr><th {TH}>Register / Log</th><th {TH}>Access</th><th {TH}>Pass/Fail Criteria</th></tr>']
        for h in tc["health_checks"]:
            lines.append(f'<tr><td {TD}>{h["name"]}</td><td {TD}>{h["access"]}</td><td {TD}>{h["criteria"]}</td></tr>')
        lines += ['</table>']
    lines += [f'<br/><div {HDR}>Post-Process</div><br/>',
              f'<p style="margin:10px 0;">{tc.get("post_process","N/A")}</p><br/>']
    lines += [f'<div {HDR}>References</div><br/><ul>']
    for f in config.get("fr_hsd", []):
        lines.append(f'<li><a href="https://hsdes.intel.com/appstore/article-one/#/{f["id"]}">HSD {f["id"]}</a> — {f["title"]}</li>')
    for spec in config.get("specs", {}).values():
        lines.append(f'<li><a href="{spec["url"]}">{spec["name"]}</a></li>')
    lines += ['</ul></div>']
    return "\n".join(lines)


def generate(hsd_id: str, force: bool = False) -> int:
    inf = find_inference_file(hsd_id)
    if not inf:
        print(f"ERROR: no inference.md found for HSD {hsd_id} in {CACHE_ROOT}")
        return 1

    text  = inf.read_text(encoding="utf-8", errors="replace")
    slug  = inf.stem.replace(".inference", "")

    # Extract title from metadata table or first heading
    title_m = re.search(r"\|\s*\*\*Title\*\*\s*\|\s*(.+?)\s*\|", text)
    title = title_m.group(1).strip() if title_m else slug

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

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{slug}_tc_desc.html"

    if out_path.exists() and not force:
        print(f"SKIP (exists): {out_path.name}  — use --force to overwrite")
        return 0

    if _JINJA:
        env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False)
        tmpl = env.get_template("tc_hsd_description.html.j2")
        tc_desc_html = tmpl.render(tc=tc, config=config)
    else:
        tc_desc_html = render_fallback(tc, config, title)

    # Extract per-section panels from the inference.md for deep-analysis tabs
    def _md_section_html(sec_heading: str) -> str:
        """Render a single ## section from the inference.md as HTML."""
        lines = _section_lines(text, sec_heading)
        if not lines:
            return "<p><em>Not available.</em></p>"
        from tools.html.generate_unified_html import render_markdown_to_html
        return render_markdown_to_html("\n".join(lines))

    # Extract HSD metadata fields for the header bar
    hsd_id_val  = hsd_id
    feature_m   = re.search(r"\|\s*\*\*Feature\*\*\s*\|\s*(.+?)\s*\|", text)
    subfeat_m   = re.search(r"\|\s*\*\*Sub-Feature\*\*\s*\|\s*(.+?)\s*\|", text)
    disp_m      = re.search(r"\|\s*\*\*NWP Disposition\*\*\s*\|\s*(.+?)\s*\|", text)
    env_m       = re.search(r"\|\s*\*\*Val Environment\*\*\s*\|\s*(.+?)\s*\|", text)
    feature     = re.sub(r"\*", "", feature_m.group(1)).strip()  if feature_m  else ""
    sub_feature = re.sub(r"\*", "", subfeat_m.group(1)).strip()  if subfeat_m  else ""
    disposition = re.sub(r"\*", "", disp_m.group(1)).strip()     if disp_m     else ""
    val_env     = re.sub(r"\*", "", env_m.group(1)).strip()      if env_m      else ""

    import html as _html
    hsd_url   = f"https://hsdes.intel.com/appstore/article-one/#/{hsd_id_val}"

    # Build each analysis tab panel
    sec_a = _md_section_html("## Section A: NWP Delta")
    sec_b = _md_section_html("## Section B: Interactions")
    sec_c = _md_section_html("## Section C: Coverage")
    sec_d = _md_section_html("## Section D: Spec Refs")
    sec_e = _md_section_html("## Section E: Risk Assessment")
    sec_f = _md_section_html("## Section F: Recommendations")

    wrapper = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline';"/>
  <title>TC: {_html.escape(title)}</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:'Segoe UI',Arial,sans-serif;background:#f0f4f9;color:#1f2937;font-size:13px;}}
    .header{{background:#0f4c81;color:#fff;padding:14px 24px;}}
    .header h1{{font-size:18px;font-weight:600;margin-bottom:4px;}}
    .header .chips{{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px;}}
    .chip{{background:rgba(255,255,255,.18);border-radius:12px;padding:2px 10px;font-size:11px;}}
    .chip.disp{{background:#1565c0;font-weight:bold;}}
    a.hsd-link{{color:#90caf9;font-size:11px;margin-left:8px;}}
    .tab-bar{{display:flex;background:#1a5fa8;padding:0 16px;gap:2px;overflow-x:auto;}}
    .tab-bar button{{background:none;border:none;color:rgba(255,255,255,.72);padding:10px 18px;
        font-size:12px;font-weight:500;cursor:pointer;border-bottom:3px solid transparent;
        white-space:nowrap;transition:all .15s;}}
    .tab-bar button:hover{{color:#fff;background:rgba(255,255,255,.08);}}
    .tab-bar button.active{{color:#fff;border-bottom-color:#64b5f6;background:rgba(255,255,255,.12);}}
    .panels{{max-width:1200px;margin:20px auto;padding:0 16px 40px;}}
    .panel{{display:none;background:#fff;border:1px solid #d9e2ec;border-radius:8px;padding:22px 26px;line-height:1.6;}}
    .panel.active{{display:block;}}
    .panel h2{{color:#0f4c81;font-size:15px;margin:18px 0 8px;border-bottom:1px solid #e8eef7;padding-bottom:4px;}}
    .panel h3{{color:#1a5fa8;font-size:13px;margin:14px 0 6px;}}
    .panel h4{{color:#555;font-size:12px;margin:10px 0 4px;}}
    .panel p{{margin:6px 0;}}
    .panel ul{{margin:6px 0 6px 18px;}}
    .panel pre{{background:#f3f6fb;border:1px solid #d9e2ec;padding:10px;overflow:auto;border-radius:6px;font-size:11px;}}
    .panel code{{font-family:Consolas,monospace;}}
    table.md-table{{border-collapse:collapse;width:100%;margin:8px 0;font-size:12px;}}
    table.md-table th,table.md-table td{{border:1px solid #d9e2ec;padding:5px 8px;text-align:left;}}
    table.md-table th{{background:#e8eef7;font-weight:600;}}
    table.md-table tr:nth-child(even){{background:#f8fafc;}}
    .tc-content{{font-size:12.5px;}}
    .tc-content h3{{color:#004a80;font-size:13px;margin:14px 0 4px;
        background:#cce4f7;padding:8px 14px;border-left:4px solid #0071c5;border-radius:0 4px 4px 0;font-weight:bold;}}
  </style>
</head>
<body>
<div class="header">
  <h1>{_html.escape(title)}
    <a class="hsd-link" href="{hsd_url}" target="_blank" rel="noopener">HSD {hsd_id_val} ↗</a>
  </h1>
  <div class="chips">
    <span class="chip">{_html.escape(feature)} › {_html.escape(sub_feature)}</span>
    <span class="chip disp">{_html.escape(disposition)}</span>
    <span class="chip">Env: {_html.escape(val_env)}</span>
  </div>
</div>

<div class="tab-bar">
  <button class="active" data-tab="tc">Test Case</button>
  <button data-tab="sec-a">A: NWP Delta</button>
  <button data-tab="sec-b">B: Interactions</button>
  <button data-tab="sec-c">C: Coverage</button>
  <button data-tab="sec-d">D: Spec Refs</button>
  <button data-tab="sec-e">E: Risks</button>
  <button data-tab="sec-f">F: Recommendations</button>
</div>

<div class="panels">
  <div id="tc" class="panel active tc-content">
{tc_desc_html}
  </div>
  <div id="sec-a" class="panel">{sec_a}</div>
  <div id="sec-b" class="panel">{sec_b}</div>
  <div id="sec-c" class="panel">{sec_c}</div>
  <div id="sec-d" class="panel">{sec_d}</div>
  <div id="sec-e" class="panel">{sec_e}</div>
  <div id="sec-f" class="panel">{sec_f}</div>
</div>

<script>
const btns  = Array.from(document.querySelectorAll('.tab-bar button'));
const panes = Array.from(document.querySelectorAll('.panel'));
btns.forEach(btn => btn.addEventListener('click', () => {{
  btns.forEach(b => b.classList.remove('active'));
  panes.forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  const p = document.getElementById(btn.dataset.tab);
  if (p) p.classList.add('active');
  window.scrollTo({{top:0,behavior:'smooth'}});
}}));
</script>
</body>
</html>"""
    out_path.write_text(wrapper, encoding="utf-8")
    print(f"GENERATED: {out_path}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Generate TC description HTML from inference.md")
    p.add_argument("--hsd", required=True, help="HSD ID (digits)")
    p.add_argument("--force", action="store_true", help="Overwrite existing output")
    args = p.parse_args()
    return generate(args.hsd, force=args.force)


if __name__ == "__main__":
    raise SystemExit(main())
