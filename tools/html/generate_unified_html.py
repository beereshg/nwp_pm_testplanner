"""Unified HTML generation for NWP PM FV and PSS cache content.

This script reads consolidated cache files from:
  - nwp_pm_cache/fv/*.inference.md
  - nwp_pm_cache/pss/*.inference.md

And writes rendered HTML to:
  - nwp_pm_fv/html/*.html
  - nwp_pm_pss/html/*.html
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CACHE_ROOT = REPO_ROOT / "nwp_pm_cache"
UNIFIED_OUTPUT_DIR = REPO_ROOT / "KB" / "pm_tc_deepanalysis"
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


def html_template(title: str, segment: str, source_file: str, body: str) -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: Segoe UI, Arial, sans-serif; background:#f6f8fb; color:#1f2937; margin:0; }}
    .wrap {{ max-width: 1180px; margin: 0 auto; padding: 24px; }}
    .meta {{ background:#0f4c81; color:#fff; padding:14px 16px; border-radius:8px; margin-bottom:16px; }}
    .meta h1 {{ margin:0; font-size:20px; }}
    .meta p {{ margin:6px 0 0; font-size:12px; opacity:0.95; }}
    .content {{ background:#fff; border:1px solid #d9e2ec; border-radius:8px; padding:20px; line-height:1.5; }}
    h1,h2,h3,h4,h5,h6 {{ color:#0f4c81; margin-top:20px; }}
    p {{ margin:8px 0; }}
    ul {{ margin:8px 0 8px 20px; }}
    pre {{ background:#f3f6fb; border:1px solid #d9e2ec; padding:10px; overflow:auto; border-radius:6px; }}
    code {{ font-family: Consolas, monospace; }}
    .md-table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
    .md-table th, .md-table td {{ border:1px solid #d9e2ec; padding:6px 8px; text-align:left; }}
    .md-table th {{ background:#e8eef7; }}
    .md-pre {{ white-space:pre-wrap; }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"meta\">
      <h1>{html.escape(title)}</h1>
      <p>Segment: {html.escape(segment.upper())} | Source: {html.escape(source_file)} | Generated: {html.escape(now)}</p>
    </div>
    <div class=\"content\">
      {body}
    </div>
  </div>
</body>
</html>
"""


def get_cache_files(segment: str, hsd_id: str | None) -> list[Path]:
    root = CACHE_ROOT / segment
    if not root.exists():
        return []
    files = sorted(root.glob("*.inference.md"))
    if hsd_id:
        token = f"HSD_{hsd_id}_"
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
        body = render_markdown_to_html(content)
        final_html = html_template(title, segment, cache_file.name, body)
        output_file.write_text(final_html, encoding="utf-8")
        generated += 1

    return len(files), generated, skipped


def status() -> int:
    print("NWP Unified Cache/HTML Status")
    print("-" * 36)
    unified_html_count = len(list(UNIFIED_OUTPUT_DIR.glob("*.html")))
    print(f"ALL html : {unified_html_count:4d} | path: {UNIFIED_OUTPUT_DIR}")
    for segment in ("fv", "pss"):
        cache_count = len(list((CACHE_ROOT / segment).glob("*.inference.md")))
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
