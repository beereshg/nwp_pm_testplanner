"""
Regenerate nwp_pm_content_analysis.html by:
1. Reading fresh hierarchy cache
2. Recomputing all stats
3. Updating stats header + per-domain counts + footer date in the existing HTML
"""
import json, re, sys
from pathlib import Path
from datetime import date

REPO = Path(__file__).resolve().parents[2]
CACHE = REPO / "nwp_pm_analysis" / "hierarchy" / "nwp_pm_fv_cache.json"
SRC   = REPO / "nwp_pm_analysis" / "html" / "nwp_pm_content_analysis.html"
OUT   = SRC  # overwrite in place

# ── Domain → TP title pattern mapping ────────────────────────────────────────
DOMAIN_MAP = {
    "RAPL":              ["RAPL"],
    "PkgC":              ["PKGC", "Package C-State"],
    "C-States (PNC)":    ["C-State (Panther", "PNC"],
    "P-State / HWP":     ["P-State", "HWP", "Pstate"],
    "Power Control":     ["Power Control", "SIMPL", "PMAX", "SVID"],
    "SST / Active PM":   ["SST", "Speed Select"],
    "AIPM":              ["AIPM", "Autonomous Idle"],
    "CCF":               ["CCF", "CBB CCF"],
    "Thermal":           ["Thermal", "CLTT"],
    "Platform PM":       ["Platform PM", "Platform Power"],
    "DVFS":              ["DVFS"],
    "Memory PM":         ["Memory", "DRAM RAPL", "MC Shallow"],
    "Telemetry":         ["Telemetry", "Perf Mon", "PMON"],
    "Other":             [],  # catch-all
}

# ── CBB/NIO classification (corrected per co-design spec tool) ───────────────
CBB_DOMAINS  = {"C-States (PNC)", "P-State / HWP", "CCF"}
NIO_DOMAINS  = {"RAPL", "Power Control", "AIPM", "Thermal"}
BOTH_DOMAINS = {"SST / Active PM", "PkgC", "Platform PM", "DVFS",
                "Memory PM", "Telemetry", "Other"}

def flatten_tcs(node):
    """Recursively yield all TC dicts from a hierarchy node."""
    for tc in node.get("tcs", []):
        yield tc
    for child in node.get("tpfs", []):
        yield from flatten_tcs(child)
    for child in node.get("tcds", []):
        yield from flatten_tcs(child)

def match_domain(tp_title: str) -> str:
    title_up = tp_title.upper()
    for domain, keywords in DOMAIN_MAP.items():
        if domain == "Other":
            continue
        for kw in keywords:
            if kw.upper() in title_up:
                return domain
    return "Other"

with open(CACHE) as f:
    cache = json.load(f)

hierarchy = cache["hierarchy"]
today = date.today().strftime("%Y-%m-%d")

# ── Compute global stats ──────────────────────────────────────────────────────
all_tcs   = [tc for tp in hierarchy for tc in flatten_tcs(tp)]
total     = len(all_tcs)
n_open    = sum(1 for tc in all_tcs if tc.get("status") == "open")
n_rej     = total - n_open

# CBB/NIO breakdown
domain_tcs = {d: [] for d in DOMAIN_MAP}
for tp in hierarchy:
    d = match_domain(tp["title"])
    for tc in flatten_tcs(tp):
        domain_tcs[d].append(tc)

cbb_count  = sum(len(domain_tcs[d]) for d in CBB_DOMAINS)
nio_count  = sum(len(domain_tcs[d]) for d in NIO_DOMAINS)
both_count = total - cbb_count - nio_count
cbb_pct    = round(cbb_count * 100 / total) if total else 0
nio_pct    = round(nio_count * 100 / total) if total else 0
both_pct   = 100 - cbb_pct - nio_pct

print(f"Total: {total}  Open: {n_open}  Rejected: {n_rej}")
print(f"CBB: {cbb_count} ({cbb_pct}%)  NIO: {nio_count} ({nio_pct}%)  Both: {both_count} ({both_pct}%)")

# ── Per-domain stats ──────────────────────────────────────────────────────────
for domain, tcs in domain_tcs.items():
    if tcs:
        open_n = sum(1 for tc in tcs if tc.get("status") == "open")
        print(f"  {domain}: {len(tcs)} total, {open_n} open, {len(tcs)-open_n} rej")

# ── Owner summary (open TCs only) ────────────────────────────────────────────
from collections import defaultdict
owner_open   = defaultdict(int)
owner_total  = defaultdict(int)
for tc in all_tcs:
    owner = tc.get("owner") or "unknown"
    owner_total[owner] += 1
    if tc.get("status") == "open":
        owner_open[owner] += 1

# Sort by open count desc
owner_rows = sorted(owner_open.items(), key=lambda x: -x[1])

def owner_summary_html(rows, total_open):
    bar_max = rows[0][1] if rows else 1
    h = '''<h2>Owner Summary — Open TCs</h2>\n'''
    h += '''<table>\n<thead><tr>
  <th>#</th><th>Owner</th><th>Open TCs</th><th>% of Open</th><th>Distribution</th><th>Total TCs</th>
</tr></thead>\n<tbody>\n'''
    for i, (owner, cnt) in enumerate(rows, 1):
        pct    = round(cnt * 100 / total_open) if total_open else 0
        bar_w  = round(cnt * 200 / bar_max)
        total  = owner_total[owner]
        h += (f'<tr>'
              f'<td style="text-align:center;color:#94a3b8;font-size:0.8em">{i}</td>'
              f'<td><strong>{owner}</strong></td>'
              f'<td style="text-align:center;font-weight:700;color:#2563eb">{cnt}</td>'
              f'<td style="text-align:center;color:#64748b">{pct}%</td>'
              f'<td><div style="background:#f1f5f9;border-radius:3px;height:8px;width:200px">'
              f'<div style="height:8px;width:{bar_w}px;background:#2563eb;border-radius:3px;min-width:2px"></div>'
              f'</div></td>'
              f'<td style="text-align:center;color:#94a3b8">{total}</td>'
              f'</tr>\n')
    h += '</tbody>\n</table>\n'
    return h

owner_html = owner_summary_html(owner_rows, n_open)

# ── Patch the existing HTML ───────────────────────────────────────────────────
html = SRC.read_text(encoding="utf-8")

# Read old stats from the current header line
m_old = re.search(r'(\d+) TCs across 14 TPs.*?(\d+) open.*?(\d+) rejected', html)
old_total, old_open, old_rej = (int(m_old.group(i)) for i in (1,2,3)) if m_old else (0,0,0)
print(f"Old stats: total={old_total} open={old_open} rej={old_rej}")

# Update header sub-line
html = re.sub(
    r'\d+ TCs across 14 TPs.*?Generated \d{4}-\d{2}-\d{2}',
    f'{total} TCs across 14 TPs &nbsp;|&nbsp; {n_open} open &nbsp;|&nbsp; {n_rej} rejected (ZBB) &nbsp;|&nbsp; Generated {today}',
    html
)

# Update stat cards with direct string replacement (safer than regex on HTML)
html = html.replace(f'<div class="v">{old_total}</div><div class="l">Total TCs</div>',
                    f'<div class="v">{total}</div><div class="l">Total TCs</div>')
html = re.sub(r'(<div class="v" style="color:#2563eb">)\d+(</div><div class="l">Open</div>)',
              rf'\g<1>{n_open}\2', html)
html = re.sub(r'(<div class="v" style="color:#94a3b8">)\d+(</div><div class="l">Rejected / ZBB</div>)',
              rf'\g<1>{n_rej}\2', html)

# CBB/NIO/Both — label includes the percentage, rebuild whole card value+label
html = re.sub(r'(<div class="v" style="color:#059669">)\d+(</div><div class="l">CBB-primary \()\d+(%</div></div>)',
              rf'\g<1>{cbb_count}\2{cbb_pct}\3', html)
html = re.sub(r'(<div class="v" style="color:#2563eb">)\d+(</div><div class="l">NIO-primary \()\d+(%</div></div>)',
              rf'\g<1>{nio_count}\2{nio_pct}\3', html)
html = re.sub(r'(<div class="v" style="color:#7c3aed">)\d+(</div><div class="l">Both dies \()\d+(%</div></div>)',
              rf'\g<1>{both_count}\2{both_pct}\3', html)

# Update footer date
html = re.sub(r'Generated \d{4}-\d{2}-\d{2} from Phoenix',
              f'Generated {today} from Phoenix', html)

# Inject owner summary before </main>
if '<h2>Owner Summary' in html:
    # already present — replace it
    html = re.sub(r'<h2>Owner Summary.*?</table>\n', owner_html, html, flags=re.DOTALL)
else:
    html = html.replace('</main>', owner_html + '</main>')

# Update ZBB scope box numbers (open/rejected counts)
html = re.sub(r'\d+ TCs \(\d+%\) already rejected',
              f'{n_rej} TCs ({round(n_rej*100/total)}%) already rejected', html)
html = re.sub(r'\d+ open TCs = validated NWP-applicable scope',
              f'{n_open} open TCs = validated NWP-applicable scope', html)

OUT.write_text(html, encoding="utf-8")
print(f"Written: {OUT}")
