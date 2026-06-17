"""
generate_report.py — Generate HTML report from sweep_results.json.
Usage:
  python generate_report.py                         # uses sweep_results.json
  python generate_report.py sweep_results.json      # explicit input
"""
import json, sys, os, re, datetime

INPUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "sweep_results.json")
OUTPUT = INPUT.replace(".json", ".html")

with open(INPUT) as f:
    data = json.load(f)

ts = data.get("timestamp", "")
features = data.get("features", {})

total_regs = sum(len(v) for v in features.values())
total_ok   = sum(1 for v in features.values() for r in v if r["status"] == "ok")
total_err  = total_regs - total_ok


def badge(status):
    if status == "ok":
        return '<span style="background:#22c55e;color:#fff;padding:2px 8px;border-radius:10px;font-size:0.75em;font-weight:700">OK</span>'
    return '<span style="background:#ef4444;color:#fff;padding:2px 8px;border-radius:10px;font-size:0.75em;font-weight:700">ERR</span>'


def format_value(val):
    if not val or val == "running>":
        return '<span style="color:#94a3b8">—</span>'
    lines = val.split("\n")
    if len(lines) == 1:
        color = "#f59e0b" if val != "0x0" and "0x0" not in val.replace("0x0\n","") else "#94a3b8"
        return f'<code style="color:{color}">{val}</code>'
    # multi-line: show only non-zero entries
    nonzero = [l for l in lines if "=0x0" not in l and l.strip() and "running>" not in l]
    if nonzero:
        return "<br>".join(f'<code style="color:#f59e0b">{l}</code>' for l in nonzero[:8])
    return f'<code style="color:#94a3b8">all 0x0 ({len(lines)} entries)</code>'


# Build sidebar nav
nav_items = "".join(
    f'<li><a href="#{fid}" style="color:#94a3b8;text-decoration:none;font-size:0.85em;'
    f'padding:4px 12px;display:block;border-radius:4px"'
    f'onmouseover="this.style.background=\'#1e293b\'" onmouseout="this.style.background=\'none\'">'
    f'{name}</a></li>'
    for fid, name in [(re.sub(r'\W', '_', k), k) for k in features]
)

# Build feature sections
sections = ""
for fname, regs in features.items():
    fid = re.sub(r'\W', '_', fname)
    ok  = sum(1 for r in regs if r["status"] == "ok")
    err = len(regs) - ok
    status_color = "#22c55e" if err == 0 else "#f59e0b" if ok > 0 else "#ef4444"
    rows = "".join(
        f"""<tr style="border-bottom:1px solid #1e293b">
          <td style="padding:10px 12px;color:#e2e8f0;font-size:0.85em">{r['label']}</td>
          <td style="padding:10px 12px;font-family:monospace;font-size:0.78em;color:#64748b;max-width:280px;word-break:break-all">{r['path']}</td>
          <td style="padding:10px 12px">{format_value(r['value'])}</td>
          <td style="padding:10px 12px;text-align:center">{badge(r['status'])}</td>
        </tr>"""
        for r in regs
    )
    sections += f"""
    <section id="{fid}" style="margin-bottom:40px">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
        <h2 style="margin:0;color:#f1f5f9;font-size:1.1em">{fname}</h2>
        <span style="background:{status_color};color:#fff;padding:2px 10px;border-radius:12px;font-size:0.75em;font-weight:700">{ok}/{len(regs)} OK</span>
      </div>
      <table style="width:100%;border-collapse:collapse;background:#0f172a;border-radius:8px;overflow:hidden">
        <thead>
          <tr style="background:#1e293b">
            <th style="padding:10px 12px;text-align:left;color:#64748b;font-size:0.78em;font-weight:600;width:28%">Register</th>
            <th style="padding:10px 12px;text-align:left;color:#64748b;font-size:0.78em;font-weight:600;width:34%">Path</th>
            <th style="padding:10px 12px;text-align:left;color:#64748b;font-size:0.78em;font-weight:600;width:30%">Value</th>
            <th style="padding:10px 12px;text-align:center;color:#64748b;font-size:0.78em;font-weight:600;width:8%">Status</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </section>"""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NWP PM Register Sweep — {ts[:10]}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #020617; color: #e2e8f0; display: flex; min-height: 100vh; }}
  aside {{ width: 220px; background: #0f172a; padding: 24px 0; position: fixed;
           top: 0; left: 0; bottom: 0; overflow-y: auto; border-right: 1px solid #1e293b; }}
  aside h3 {{ color: #475569; font-size: 0.7em; font-weight: 700; letter-spacing: 0.1em;
              text-transform: uppercase; padding: 0 16px 12px; }}
  main {{ margin-left: 220px; padding: 32px; flex: 1; max-width: 1200px; }}
  header {{ margin-bottom: 32px; padding-bottom: 24px; border-bottom: 1px solid #1e293b; }}
  .stat-card {{ display: inline-block; background: #0f172a; border: 1px solid #1e293b;
                border-radius: 8px; padding: 12px 24px; margin-right: 12px; text-align: center; }}
  .stat-num {{ font-size: 1.8em; font-weight: 700; }}
  .stat-label {{ font-size: 0.75em; color: #64748b; margin-top: 2px; }}
</style>
</head>
<body>
<aside>
  <h3>Features</h3>
  <ul style="list-style:none">{nav_items}</ul>
</aside>
<main>
  <header>
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:16px">
      <div>
        <h1 style="font-size:1.4em;color:#f1f5f9">NWP PM Register Sweep</h1>
        <p style="color:#64748b;font-size:0.85em;margin-top:4px">
          Active_PM · Simics nwp-7/2026ww23 · {ts[:19].replace('T',' ')}
        </p>
      </div>
    </div>
    <div>
      <div class="stat-card">
        <div class="stat-num" style="color:#f1f5f9">{total_regs}</div>
        <div class="stat-label">Total Registers</div>
      </div>
      <div class="stat-card">
        <div class="stat-num" style="color:#22c55e">{total_ok}</div>
        <div class="stat-label">Successful</div>
      </div>
      <div class="stat-card">
        <div class="stat-num" style="color:#ef4444">{total_err}</div>
        <div class="stat-label">Errors</div>
      </div>
      <div class="stat-card">
        <div class="stat-num" style="color:#f59e0b">{len(features)}</div>
        <div class="stat-label">Features</div>
      </div>
    </div>
  </header>
  {sections}
</main>
</body>
</html>"""

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Report: {OUTPUT}")
