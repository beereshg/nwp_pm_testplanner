"""Unified HTML generation for NWP PM FV and PSS cache content.

This script reads consolidated cache files from:
  - KB/pm_tc_kb/**/*.inference.md

And writes rendered HTML to:
  - tc_description_output/*.html
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CACHE_ROOT = REPO_ROOT / "KB" / "pm_tc_kb"
UNIFIED_OUTPUT_DIR = REPO_ROOT / "tc_description_output"
OUTPUT_ROOTS = {
    "fv": UNIFIED_OUTPUT_DIR,
    "pss": UNIFIED_OUTPUT_DIR,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate FV/PSS HTML from unified cache")
    parser.add_argument(
        "--segment",
        choices=["all", "fv", "pss"],
        default="all",
        help="Select which cache segment to render",
    )
    parser.add_argument("--hsd", help="Render only a specific HSD id (digits only)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing HTML files")
    parser.add_argument("--status", action="store_true", help="Print cache/html counts and exit")
    return parser.parse_args()


def render_markdown_to_html(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    out: list[str] = []
    in_code = False
    in_list = False
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            if not in_code:
                if in_list:
                    out.append("</ul>")
                    in_list = False
                out.append("<pre><code>")
                in_code = True
            else:
                out.append("</code></pre>")
                in_code = False
            i += 1
            continue

        if in_code:
            out.append(html.escape(line))
            i += 1
            continue

        if stripped.startswith("|"):
            if in_list:
                out.append("</ul>")
                in_list = False

            table_lines: list[str] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1

            rows = [
                [c.strip() for c in row.strip("|").split("|")]
                for row in table_lines
            ]
            if len(rows) >= 2 and all(re.fullmatch(r"[-: ]+", c or "") for c in rows[1]):
                header = rows[0]
                body = rows[2:]
                out.append('<table class="md-table"><thead><tr>')
                out.extend(f"<th>{html.escape(cell)}</th>" for cell in header)
                out.append("</tr></thead><tbody>")
                for row in body:
                    out.append("<tr>")
                    out.extend(f"<td>{html.escape(cell)}</td>" for cell in row)
                    out.append("</tr>")
                out.append("</tbody></table>")
            else:
                out.append('<pre class="md-pre">')
                out.append(html.escape("\n".join(table_lines)))
                out.append("</pre>")
            continue

        if not stripped:
            if in_list:
                out.append("</ul>")
                in_list = False
            i += 1
            continue

        if stripped.startswith("#"):
            if in_list:
                out.append("</ul>")
                in_list = False
            level = min(len(stripped) - len(stripped.lstrip("#")), 6)
            text = stripped[level:].strip()
            out.append(f"<h{level}>{html.escape(text)}</h{level}>")
            i += 1
            continue

        if stripped.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{html.escape(stripped[2:].strip())}</li>")
            i += 1
            continue

        if in_list:
            out.append("</ul>")
            in_list = False
        out.append(f"<p>{html.escape(stripped)}</p>")
        i += 1

    if in_list:
        out.append("</ul>")
    if in_code:
        out.append("</code></pre>")

    return "\n".join(out)


def extract_title(markdown_text: str, fallback: str) -> str:
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
    return fallback


def split_into_sections(markdown_text: str) -> list[tuple[str, str]]:
    """Split markdown into [(heading, content), ...].

    Content before the first ## Section heading is collected as 'Overview'.
    Each '## Section X:' heading starts a new tab.
    """
    lines = markdown_text.splitlines()
    SEC_RE = re.compile(r"^##\s+Section\s+([A-G]):\s*(.+)", re.IGNORECASE)
    sections: list[tuple[str, list[str]]] = []
    current_head = "Overview"
    current_lines: list[str] = []

    for line in lines:
        m = SEC_RE.match(line)
        if m:
            sections.append((current_head, current_lines))
            label = f"{m.group(1)}: {m.group(2).strip()}"
            current_head = label
            current_lines = []
        else:
            current_lines.append(line)

    sections.append((current_head, current_lines))
    return [(h, "\n".join(ln)) for h, ln in sections if any(l.strip() for l in ln)]


def html_template(title: str, segment: str, source_file: str, body: str) -> str:
    """Build tabbed HTML from a flat markdown body string."""
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sections = split_into_sections(body)

    tab_buttons = []
    tab_panels  = []
    for i, (heading, content_md) in enumerate(sections):
        tab_id  = f"tab{i}"
        active  = " active" if i == 0 else ""
        safe_h  = html.escape(heading)
        panel_html = render_markdown_to_html(content_md)
        tab_buttons.append(
            f'<button class="tab{active}" data-tab="{tab_id}">{safe_h}</button>'
        )
        tab_panels.append(
            f'<div id="{tab_id}" class="panel{active}">{panel_html}</div>'
        )

    tabs_html   = "\n    ".join(tab_buttons)
    panels_html = "\n  ".join(tab_panels)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline';" />
  <title>{html.escape(title)}</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:'Segoe UI',Arial,sans-serif;background:#f0f4f9;color:#1f2937;font-size:13px;}}
    .header{{background:#0f4c81;color:#fff;padding:14px 24px;}}
    .header h1{{font-size:18px;font-weight:600;margin-bottom:2px;}}
    .header p{{font-size:11px;opacity:.85;margin-top:4px;}}
    .tab-bar{{display:flex;background:#1a5fa8;padding:0 16px;gap:2px;overflow-x:auto;}}
    .tab-bar .tab{{background:none;border:none;color:rgba(255,255,255,.72);padding:10px 16px;
        font-size:12px;font-weight:500;cursor:pointer;border-bottom:3px solid transparent;
        white-space:nowrap;transition:all .15s;}}
    .tab-bar .tab:hover{{color:#fff;background:rgba(255,255,255,.08);}}
    .tab-bar .tab.active{{color:#fff;border-bottom-color:#64b5f6;background:rgba(255,255,255,.12);}}
    .panels{{max-width:1200px;margin:20px auto;padding:0 16px 40px;}}
    .panel{{display:none;background:#fff;border:1px solid #d9e2ec;border-radius:8px;padding:22px 26px;line-height:1.6;}}
    .panel.active{{display:block;}}
    .panel h1{{color:#0f4c81;font-size:16px;margin:0 0 12px;}}
    .panel h2{{color:#0f4c81;font-size:15px;margin:18px 0 8px;border-bottom:1px solid #e8eef7;padding-bottom:4px;}}
    .panel h3{{color:#1a5fa8;font-size:13px;margin:14px 0 6px;}}
    .panel h4{{color:#555;font-size:12px;margin:10px 0 4px;}}
    .panel p{{margin:6px 0;}}
    .panel ul{{margin:6px 0 6px 18px;}}
    .panel li{{margin:3px 0;}}
    pre{{background:#f3f6fb;border:1px solid #d9e2ec;padding:10px;overflow:auto;border-radius:6px;font-size:11px;}}
    code{{font-family:Consolas,monospace;}}
    .md-table{{border-collapse:collapse;width:100%;margin:8px 0;font-size:12px;}}
    .md-table th,.md-table td{{border:1px solid #d9e2ec;padding:5px 8px;text-align:left;}}
    .md-table th{{background:#e8eef7;font-weight:600;}}
    .md-table tr:nth-child(even){{background:#f8fafc;}}
    .md-pre{{white-space:pre-wrap;}}
  </style>
</head>
<body>
  <div class="header">
    <h1>{html.escape(title)}</h1>
    <p>Segment: {html.escape(segment.upper())} | Source: {html.escape(source_file)} | Generated: {html.escape(now)}</p>
  </div>
  <div class="tab-bar">
    {tabs_html}
  </div>
  <div class="panels">
  {panels_html}
  </div>
<script>
const tabs  = Array.from(document.querySelectorAll('.tab-bar .tab'));
const panes = Array.from(document.querySelectorAll('.panel'));
tabs.forEach(t => t.addEventListener('click', () => {{
  tabs.forEach(b  => b.classList.remove('active'));
  panes.forEach(p => p.classList.remove('active'));
  t.classList.add('active');
  const p = document.getElementById(t.dataset.tab);
  if (p) p.classList.add('active');
  window.scrollTo({{top:0,behavior:'smooth'}});
}}));
</script>
</body>
</html>
"""


def get_cache_files(segment: str, hsd_id: str | None) -> list[Path]:
    # Recurse all subdirectories under KB/pm_tc_kb for the given segment
    files = sorted(CACHE_ROOT.rglob(f"**/{segment}/*.inference.md"))
    if hsd_id:
        token = str(hsd_id)
        files = [f for f in files if token in f.name]
    return files


def target_html_name(cache_file: Path) -> str:
    return cache_file.name.replace(".inference.md", ".html")


def render_segment(segment: str, hsd_id: str | None, force: bool) -> tuple[int, int, int]:
    files = get_cache_files(segment, hsd_id)
    output_dir = OUTPUT_ROOTS[segment]
    output_dir.mkdir(parents=True, exist_ok=True)

    generated = 0
    skipped = 0
    for cache_file in files:
        output_file = output_dir / target_html_name(cache_file)
        if output_file.exists() and not force:
            skipped += 1
            continue

        content = cache_file.read_text(encoding="utf-8", errors="replace")
        title = extract_title(content, cache_file.stem.replace(".inference", ""))
        # pass raw markdown — html_template splits into tabs and renders each section
        final_html = html_template(title, segment, cache_file.name, content)
        output_file.write_text(final_html, encoding="utf-8")
        generated += 1

    return len(files), generated, skipped


def status() -> int:
    print("NWP Unified Cache/HTML Status")
    print("-" * 36)
    unified_html_count = len(list(UNIFIED_OUTPUT_DIR.glob("*.html")))
    print(f"ALL html : {unified_html_count:4d} | path: {UNIFIED_OUTPUT_DIR}")
    for segment in ("fv", "pss"):
        cache_count = len(list(CACHE_ROOT.rglob(f"**/{segment}/*.inference.md")))
        print(f"{segment.upper():>3} cache: {cache_count:4d}")
    return 0


def main() -> int:
    args = parse_args()
    if args.status:
        return status()

    if args.hsd and not args.hsd.isdigit():
        raise SystemExit("--hsd must be numeric, e.g. 22021970066")

    segments = ["fv", "pss"] if args.segment == "all" else [args.segment]
    total_candidates = 0
    total_generated = 0
    total_skipped = 0

    for segment in segments:
        candidates, generated, skipped = render_segment(segment, args.hsd, args.force)
        total_candidates += candidates
        total_generated += generated
        total_skipped += skipped
        print(
            f"[{segment.upper()}] candidates={candidates} generated={generated} skipped={skipped} "
            f"output={OUTPUT_ROOTS[segment]}"
        )

    print(
        f"Done. total_candidates={total_candidates} generated={total_generated} skipped={total_skipped}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
