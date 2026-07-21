#!/usr/bin/env python3
"""
Generate TC description HTML from KB/pm_tc_kb inference.md files.

Uses KB/templates/tc_hsd_description.html.j2 — same format as HSD TC description field
(Validation Scope, Preconditions, Test Steps, Health Check, Post-Process, References).

Usage:
  python tools/html/generate_tc_description.py --hsd 22022422105
  python tools/html/generate_tc_description.py --hsd 22022422105 --force

Output:
  tc_description_output/HSD_{id}_{slug}_tc_desc.html
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
    """Join lines into a clean paragraph string, converting inline markdown."""
    import html as _html
    import re as _re
    def _inline(s):
        s = _html.escape(s)
        s = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        s = _re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
        return s
    parts = []
    for l in lines:
        s = l.strip()
        if not s or s.startswith("|") or s.startswith("---") or s.startswith("```"):
            continue
        if s.startswith("> "):
            parts.append(f'<span style="display:block;background:#f0f4f9;border-left:3px solid #1a5fa8;padding:4px 10px;margin:4px 0;font-size:0.92em;color:#1e3a5f;">{_inline(s[2:].strip())}</span>')
        else:
            parts.append(_inline(s))
    return " ".join(parts)


# ─── Section extractors ───────────────────────────────────────────────────────

def extract_scope(text: str) -> str:
    for heading in ("## Test Case Intent", "### Test Case Intent", "### Intent", "### Refined Intent"):
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
    for heading in ("## Section D: Spec Refs", "## KB References", "### Reference Documents", "### References", "## References"):
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


def _generate_hsd_fallback(hsd_id: str, force: bool = False) -> int:
    """Generate a minimal TC description HTML from live HSD data (no inference.md)."""
    from hsd_utils import get_session, get_article
    import html as _html

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    s = get_session()
    a = get_article(hsd_id, fields="id,title,status,owner,description,tag", session=s)
    title_raw = a.get("title", hsd_id)
    slug_raw  = re.sub(r"[^a-z0-9]+", "_", title_raw.lower()).strip("_")
    out_path  = OUTPUT_DIR / f"HSD_{hsd_id}_{slug_raw}_tc_desc.html"

    if out_path.exists() and not force:
        print(f"SKIP (exists): {out_path.name}  — use --force to overwrite")
        return 0

    desc_html = a.get("description", "") or "<p><em>No description in HSD.</em></p>"
    title_esc = _html.escape(title_raw)
    hsd_url   = f"https://hsdes.intel.com/appstore/article-one/#/{hsd_id}"

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline';"/>
  <title>TC: {title_esc}</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:'Segoe UI',Arial,sans-serif;background:#f0f4f9;color:#1f2937;font-size:13px;}}
    .header{{background:#0f4c81;color:#fff;padding:14px 24px;}}
    .header h1{{font-size:18px;font-weight:600;margin-bottom:4px;}}
    a.hsd-link{{color:#90caf9;font-size:11px;margin-left:8px;}}
    .notice{{background:#fff3cd;border:1px solid #ffc107;border-radius:6px;padding:10px 14px;
             margin:16px 28px;font-size:12px;color:#664d03;}}
    .content{{max-width:1100px;margin:20px auto;padding:0 28px 40px;
              background:#fff;border:1px solid #d9e2ec;border-radius:8px;}}
    .content {{padding:22px 26px;line-height:1.6;font-size:13px;}}
  </style>
</head>
<body>
<div class="header">
  <h1>{title_esc}
    <a class="hsd-link" href="{hsd_url}" target="_blank" rel="noopener">HSD {hsd_id} ↗</a>
  </h1>
</div>
<div class="notice">ⓘ <b>HSD-live fallback</b> — no KB inference.md found for this TC.
  Showing current HSD description. Add an inference.md to get tabbed deep-analysis output.</div>
<div class="desc-box">
{desc_html}
</div>
</body>
</html>"""

    out_path.write_text(page, encoding="utf-8")
    print(f"GENERATED [HSD-live]: {out_path}")
    return 0


def generate(hsd_id: str, force: bool = False) -> int:
    inf = find_inference_file(hsd_id)
    if not inf:
        return _generate_hsd_fallback(hsd_id, force)

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

    import html as _html
    hsd_url = f"https://hsdes.intel.com/appstore/article-one/#/{hsd_id}"

    # Wrap the Jinja2-rendered TC description in a minimal preview page
    # This is the same inline-styled HTML that gets pushed to HSD
    wrapper = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body{{font-family:"Segoe UI",Arial,sans-serif;font-size:13px;color:#333;line-height:1.6;max-width:900px;margin:20px auto;padding:0 20px;}}
</style></head><body>
<div class="desc-box">
{tc_desc_html}
</div>
</body></html>"""
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
