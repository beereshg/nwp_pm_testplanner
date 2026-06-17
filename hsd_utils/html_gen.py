"""
HTML generation for NWP PM test-plan hierarchies.

Two entry points:

* ``generate_fv_html``  — FV hierarchy (two-tab layout: All TCs + PSS TCs).
* ``generate_pss_html`` — PSS hierarchy (single-page, PSS-badge variant).

Both accept the structured data returned by ``hsd_utils.hierarchy.walk_hierarchy``.
"""
from __future__ import annotations
from collections import defaultdict
from typing import Any

from .session import HSD_URL

# ── Shared CSS + JS ───────────────────────────────────────────────────────────

_CSS_COMMON = """
  body { font-family: Segoe UI, Arial, sans-serif; font-size: 13px; margin: 20px; background: #f8f9fa; }
  h1 { color: #343a40; }
  h2 { color: #495057; margin-top: 30px; }
  details { margin: 4px 0; }
  summary { cursor: pointer; padding: 4px 8px; border-radius: 4px; list-style: none; }
  summary::-webkit-details-marker { display: none; }
  summary::before { content: "▶ "; font-size: 10px; }
  details[open] > summary::before { content: "▼ "; }
  .tp  > summary { background: #343a40; color: #fff; font-weight: bold; font-size: 14px; }
  .tpf > summary { background: #495057; color: #fff; font-size: 13px; margin-left: 16px; }
  .tcd > summary { background: #dee2e6; color: #343a40; margin-left: 32px; }
  .tc-row { display: flex; gap: 12px; padding: 3px 8px; margin-left: 48px;
             border-bottom: 1px solid #f0f0f0; background: #fff; }
  .tc-row:hover { background: #e9ecef; }
  .hsd-id { min-width: 110px; font-family: monospace; }
  .owner  { min-width: 100px; color: #0066cc; }
  .badge  { color: #fff; padding: 1px 6px; border-radius: 10px; font-size: 11px; }
  .title  { flex: 1; }
  table { border-collapse: collapse; width: 100%; max-width: 700px; }
  th, td { border: 1px solid #dee2e6; padding: 6px 12px; text-align: left; }
  th { background: #343a40; color: #fff; }
  tr:nth-child(even) { background: #f2f2f2; }
  .total-row { font-weight: bold; background: #dee2e6 !important; }
"""

_CSS_FV_EXTRA = """
  /* Tabs */
  .tab-bar { display: flex; gap: 4px; margin: 16px 0 0 0; border-bottom: 2px solid #343a40; }
  .tab-btn { padding: 8px 20px; cursor: pointer; border: none; background: #e9ecef;
             border-radius: 6px 6px 0 0; font-size: 13px; font-weight: 600;
             color: #495057; transition: background .15s; }
  .tab-btn.active { background: #343a40; color: #fff; }
  .tab-btn:hover:not(.active) { background: #ced4da; }
  .tab-content { display: none; padding-top: 16px; }
  .tab-content.active { display: block; }
  /* PSS table */
  .pss-table { border-collapse: collapse; width: 100%; max-width: 1100px; }
  .pss-table th, .pss-table td { border: 1px solid #dee2e6; padding: 5px 10px; text-align: left; }
  .pss-table th { background: #343a40; color: #fff; }
  .pss-table tr:nth-child(even) { background: #f2f2f2; }
  .pss-table tr:hover { background: #e2e8f0; }
  /* Platform tag */
  .pv-tag { background: #e65c00; color: #fff; padding: 1px 6px; border-radius: 10px;
            font-size: 11px; margin-left: 4px; font-weight: 600; }
  /* Owner drilldown */
  .owner-section { margin: 18px 0 10px; border-left: 4px solid #0066cc; padding-left: 12px; }
  .owner-section h3 { margin: 0 0 6px; color: #0066cc; font-size: 14px; }
  .owner-drilldown { border-collapse: collapse; width: 100%; max-width: 1200px; margin-bottom: 24px; }
  .owner-drilldown th { background: #343a40; color: #fff; padding: 6px 10px; text-align: left; font-size: 12px; }
  .owner-drilldown td { border-bottom: 1px solid #dee2e6; padding: 5px 10px; font-size: 12px; vertical-align: top; }
  .owner-drilldown tr:hover { background: #e8f0fe; }
  .owner-drilldown .tp-cell { color: #343a40; font-weight: 600; font-size: 11px; }
  .owner-drilldown .tcd-cell { color: #495057; font-size: 11px; }
  .owner-drilldown .tc-count { background: #0066cc; color: #fff; border-radius: 10px;
    padding: 1px 8px; font-size: 11px; display: inline-block; }
"""

_CSS_PSS_EXTRA = """
  .pss-tag { background: #6f42c1; color: #fff; padding: 1px 6px; border-radius: 10px;
             font-size: 11px; margin-left: 4px; }
"""

_JS_TABS = """
<script>
function showTab(name) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  document.querySelector('[data-tab="' + name + '"]').classList.add('active');
}
</script>
"""


# ── Shared helpers ────────────────────────────────────────────────────────────

def _esc(s: Any) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _hsd_link(aid: str, label: str | None = None) -> str:
    url  = HSD_URL.format(aid)
    text = _esc(label or str(aid))
    return f'<a href="{url}" target="_blank">{text}</a>'


def _status_badge(status: str) -> str:
    color = {
        "open":     "#28a745",
        "blocked":  "#fd7e14",
        "rejected": "#dc3545",
    }.get(str(status).lower(), "#6c757d")
    tw={'open':'bg-green-600','rejected':'bg-red-500','blocked':'bg-amber-500'}.get(status,'bg-slate-400')
    return f'<span class="inline-block px-2 py-0.5 rounded-full text-[11px] font-semibold text-white {tw}">{_esc(status)}</span>'


def _owner_summary_table(tc_stats: list[tuple[str, str]]) -> tuple[list[str], dict, dict, list]:
    """Return (lines, owner_open, owner_other, all_owners) for a summary table."""
    owner_open:  dict[str, int] = defaultdict(int)
    owner_other: dict[str, int] = defaultdict(int)
    for owner, status in tc_stats:
        if status == "open":
            owner_open[owner]  += 1
        else:
            owner_other[owner] += 1
    all_owners = sorted(set(list(owner_open.keys()) + list(owner_other.keys())))
    lines: list[str] = []
    lines.append("<table>")
    lines.append("<tr><th>Owner</th><th>Open</th><th>Other (blocked/rejected/…)</th><th>Total</th></tr>")
    grand_open = grand_other = 0
    for owner in all_owners:
        o = owner_open.get(owner, 0)
        x = owner_other.get(owner, 0)
        grand_open  += o
        grand_other += x
        lines.append(f"<tr><td>{_esc(owner)}</td><td>{o}</td><td>{x}</td><td>{o+x}</td></tr>")
    lines.append(
        f'<tr class="total-row"><td>TOTAL</td><td>{grand_open}</td>'
        f'<td>{grand_other}</td><td>{grand_open+grand_other}</td></tr>'
    )
    lines.append("</table>")
    return lines, owner_open, owner_other, all_owners


# ── FV HTML generator ─────────────────────────────────────────────────────────

def generate_fv_html(
    root_id: str,
    root_info: dict[str, Any],
    hierarchy: list[dict[str, Any]],
    tc_stats: list[tuple[str, str]],
    output_path: str,
    excluded_ids: set[str] | None = None,
) -> None:
    """Write a two-tab FV hierarchy HTML file to *output_path*.

    Tab 1 — All TCs: collapsible TP→TPF→TCD→TC tree + owner summary table.
    Tab 2 — PSS TCs: flat table of all TCs whose title starts with ``[PSS]``.
    """
    excl = excluded_ids or set()
    lines: list[str] = []

    # ── <head> ────────────────────────────────────────────────────────────────
    lines.append('<!DOCTYPE html>\n<html lang="en">\n<head>')
    lines.append('<meta charset="UTF-8">')
    lines.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    lines.append('<title>NWP PM Test Plan Hierarchy</title>')
    lines.append('<script src="https://cdn.tailwindcss.com"></script>')
    lines.append('<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>')
    lines.append('''<style>
      [x-cloak]{display:none!important}
      details>summary{list-style:none}
      details>summary::-webkit-details-marker{display:none}
      details>summary::marker{display:none}
      details[open]>.summary-arrow::before{content:"▼ "}
      .summary-arrow::before{content:"▶ ";font-size:10px;opacity:.7}
    </style>''')
    lines.append('</head>')
    lines.append('<body class="bg-slate-50 text-slate-800 font-sans text-sm min-h-screen">')

    # ── Page header ───────────────────────────────────────────────────────────
    excl_note = (
        f' &nbsp;·&nbsp; Deprecated: {", ".join(f"<code class=\'bg-indigo-100 text-indigo-900 px-1 rounded font-mono\'>{i}</code>" for i in sorted(excl))} excluded'
        if excl else ""
    )
    total_open  = sum(1 for _, st in tc_stats if st == "open")
    total_other = len(tc_stats) - total_open

    lines.append(f'''<div class="bg-indigo-700 text-white px-6 py-4 shadow-lg">
  <h1 class="text-2xl font-bold tracking-tight">📋 NWP PM Test Plan Hierarchy</h1>
  <p class="text-indigo-200 text-xs mt-1">
    Root: {_hsd_link(root_id, root_info.get("title", root_id))}{excl_note}
    &nbsp;·&nbsp;
    <strong class="text-white">{len(tc_stats)}</strong> total TCs &nbsp;·&nbsp;
    <strong class="text-green-400">{total_open}</strong> open &nbsp;·&nbsp;
    <strong class="text-red-400">{total_other}</strong> rejected/blocked
  </p>
</div>''')

    # ── Alpine tab controller ─────────────────────────────────────────────────
    lines.append('<div x-data="{ tab: \'all\' }" class="max-w-screen-2xl mx-auto px-4 py-4">')

    # Tab bar
    tab_defs = [
        ("all",      "📋 All TCs"),
        ("pss",      "🔖 PSS TCs"),
        ("platform", "🖥️ Platform [PV]"),
        ("owners",   "👤 Owner View"),
    ]
    lines.append('<div class="flex gap-1 border-b-2 border-indigo-600 mb-4 flex-wrap">')
    for tid, tlabel in tab_defs:
        lines.append(
            f'<button @click="tab=\'{tid}\'" '
            f':class="tab===\'{tid}\' ? \'bg-slate-900 text-white\' : \'bg-slate-200 text-slate-500 hover:bg-slate-300\'" '
            f'class="px-5 py-2 rounded-t font-semibold text-sm transition-colors">'
            f'{tlabel}</button>'
        )
    lines.append('</div>')

    # ══ TAB: All TCs ══════════════════════════════════════════════════════════
    lines.append('<div x-show="tab===\'all\'" x-cloak>')

    # Owner summary card
    _, owner_open_d, owner_other_d, all_owners = _owner_summary_table(tc_stats)
    lines.append('<div class="mb-6">')
    lines.append('<h2 class="text-lg font-bold text-indigo-700 mb-2">TC Summary by Owner</h2>')
    lines.append('<div class="overflow-x-auto"><table class="text-sm border-collapse rounded-lg overflow-hidden shadow-sm">')
    lines.append('<thead><tr class="bg-indigo-700 text-white"><th class="px-4 py-2 text-left">Owner</th><th class="px-4 py-2">Open</th><th class="px-4 py-2">Other</th><th class="px-4 py-2">Total</th></tr></thead><tbody>')
    for owner in all_owners:
        o = owner_open_d.get(owner, 0)
        x = owner_other_d.get(owner, 0)
        lines.append(f'<tr class="border-b hover:bg-indigo-50"><td class="px-4 py-1.5 text-indigo-700 font-medium">{_esc(owner)}</td>'
                     f'<td class="px-4 py-1.5 text-center text-green-600 font-semibold">{o}</td>'
                     f'<td class="px-4 py-1.5 text-center text-red-500">{x}</td>'
                     f'<td class="px-4 py-1.5 text-center font-bold">{o+x}</td></tr>')
    go = sum(owner_open_d.values()); gx = sum(owner_other_d.values())
    lines.append(f'<tr class="bg-indigo-50 font-bold border-t-2 border-indigo-300"><td class="px-4 py-2">TOTAL</td>'
                 f'<td class="px-4 py-2 text-center text-green-700">{go}</td>'
                 f'<td class="px-4 py-2 text-center text-red-600">{gx}</td>'
                 f'<td class="px-4 py-2 text-center">{go+gx}</td></tr>')
    lines.append('</tbody></table></div></div>')

    # Hierarchy tree
    lines.append('<h2 class="text-lg font-bold text-indigo-700 mb-2">Test Plan Hierarchy</h2>')
    lines.append('<div class="space-y-1">')
    for tp_data in hierarchy:
        tp_id     = tp_data["id"]
        all_tcs   = [tc for tpf in tp_data["tpfs"] for td in tpf["tcds"] for tc in td["tcs"]]
        all_tcs  += [tc for td in tp_data.get("direct_tcds", []) for tc in td["tcs"]]
        tp_tc_n   = len(all_tcs)
        tp_open_n = sum(1 for tc in all_tcs if tc.get("status") == "open")
        lines.append(
            f'<details class="rounded-lg overflow-hidden shadow-sm">'
            f'<summary class="summary-arrow bg-indigo-700 text-white px-4 py-2.5 cursor-pointer font-bold flex justify-between items-center hover:bg-indigo-600">'
            f'<span>{_hsd_link(tp_id)} &nbsp; {_esc(tp_data["title"])}'
            f' <span class="text-indigo-200 text-xs font-normal ml-2">owner: {_esc(tp_data["owner"])}</span></span>'
            f'<span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-500 text-white">'
            f'{tp_open_n}&nbsp;/&nbsp;{tp_tc_n}&nbsp;TCs</span>'
            f'</summary>'
            f'<div class="bg-white pl-4 space-y-0.5 pb-2 border-l-4 border-indigo-300">'
        )
        for tpf_data in tp_data["tpfs"]:
            tpf_id   = tpf_data["id"]
            tpf_tc_n = sum(len(td["tcs"]) for td in tpf_data["tcds"])
            lines.append(
                f'<details class="ml-2">'
                f'<summary class="summary-arrow bg-slate-500 text-white px-3 py-1.5 cursor-pointer flex justify-between items-center rounded mt-1 hover:bg-slate-400 text-xs">'
                f'<span>{_hsd_link(tpf_id)} &nbsp; {_esc(tpf_data["title"])}'
                f' <span class="opacity-80 ml-2 text-indigo-100">owner: {_esc(tpf_data["owner"])}</span></span>'
                f'<span class="bg-indigo-400 text-white text-xs px-2 py-0.5 rounded-full">{len(tpf_data["tcds"])} TCDs / {tpf_tc_n} TCs</span>'
                f'</summary>'
                f'<div class="bg-slate-50 pl-3 space-y-0.5 pb-1">'
            )
            for tcd_data in tpf_data["tcds"]:
                lines.extend(_render_tcd_fv_tw(tcd_data))
            lines.append('</div></details>')  # tpf

        for tcd_data in tp_data.get("direct_tcds", []):
            lines.extend(_render_tcd_fv_tw(tcd_data))
        lines.append('</div></details>')  # tp
    lines.append('</div>')  # space-y-1
    lines.append('</div>')  # tab-all

    # ══ TAB: PSS TCs ══════════════════════════════════════════════════════════
    pss_rows = _collect_pss_rows(hierarchy)
    pss_rows.sort(key=lambda x: int(x[0]))
    pss_open  = sum(1 for r in pss_rows if r[3] == "open")
    pss_other = len(pss_rows) - pss_open
    pss_by_owner_open:  dict[str, int] = defaultdict(int)
    pss_by_owner_other: dict[str, int] = defaultdict(int)
    for r in pss_rows:
        if r[3] == "open": pss_by_owner_open[r[2]]  += 1
        else:               pss_by_owner_other[r[2]] += 1
    pss_owners = sorted(set(list(pss_by_owner_open) + list(pss_by_owner_other)))

    lines.append('<div x-show="tab===\'pss\'" x-cloak>')
    lines.append(f'<div class="flex gap-4 mb-4">')
    for label, val, color in [("Total", len(pss_rows), "bg-indigo-600"), ("Open", pss_open, "bg-green-600"), ("Other", pss_other, "bg-red-500")]:
        lines.append(f'<div class="{color} text-white rounded-lg px-5 py-3 text-center shadow"><div class="text-2xl font-bold">{val}</div><div class="text-xs opacity-80">{label}</div></div>')
    lines.append('</div>')

    lines.append('<div class="overflow-x-auto mb-4"><table class="text-sm border-collapse rounded-lg overflow-hidden shadow-sm">')
    lines.append('<thead><tr class="bg-indigo-700 text-white"><th class="px-4 py-2 text-left">Owner</th><th class="px-4 py-2">Open</th><th class="px-4 py-2">Other</th><th class="px-4 py-2">Total</th></tr></thead><tbody>')
    for owner in pss_owners:
        o = pss_by_owner_open.get(owner,0); x = pss_by_owner_other.get(owner,0)
        lines.append(f'<tr class="border-b hover:bg-indigo-50"><td class="px-4 py-1.5 text-indigo-700 font-medium">{_esc(owner)}</td><td class="px-4 py-1.5 text-center text-green-600 font-semibold">{o}</td><td class="px-4 py-1.5 text-center text-red-500">{x}</td><td class="px-4 py-1.5 text-center font-bold">{o+x}</td></tr>')
    lines.append(f'<tr class="bg-indigo-50 font-bold border-t-2 border-indigo-300"><td class="px-4 py-2">TOTAL</td><td class="px-4 py-2 text-center text-green-700">{pss_open}</td><td class="px-4 py-2 text-center text-red-600">{pss_other}</td><td class="px-4 py-2 text-center">{len(pss_rows)}</td></tr>')
    lines.append('</tbody></table></div>')

    lines.append('<h2 class="text-lg font-bold text-indigo-700 mb-2">PSS TC List</h2>')
    lines.append('<div class="overflow-x-auto"><table class="w-full text-xs border-collapse shadow rounded-lg overflow-hidden">')
    lines.append('<thead><tr class="bg-indigo-700 text-white"><th class="px-3 py-2 text-left">ID</th><th class="px-3 py-2">Owner</th><th class="px-3 py-2">Status</th><th class="px-3 py-2 text-left">Title</th><th class="px-3 py-2 text-left">TP</th><th class="px-3 py-2 text-left">TCD</th></tr></thead><tbody>')
    for (tc_id, tc_title, owner, status, tp_title, tpf_title, tcd_title) in pss_rows:
        lines.append(
            f'<tr class="border-b hover:bg-indigo-50">'
            f'<td class="px-3 py-1.5 font-mono">{_hsd_link(tc_id, tc_id)}</td>'
            f'<td class="px-3 py-1.5 text-indigo-600 font-medium text-center">{_esc(owner)}</td>'
            f'<td class="px-3 py-1.5 text-center">{_status_badge(status)}</td>'
            f'<td class="px-3 py-1.5">{_esc(tc_title)}</td>'
            f'<td class="px-3 py-1.5 text-slate-400">{_esc(tp_title)}</td>'
            f'<td class="px-3 py-1.5 text-slate-400">{_esc(tcd_title)}</td>'
            f'</tr>'
        )
    lines.append('</tbody></table></div></div>')  # tab-pss

    # ══ TAB: Platform TCs ══════════════════════════════════════════════════════
    pv_all_rows  = sorted(_collect_platform_rows(hierarchy), key=lambda x: int(x[0]))
    pv_open_rows = [r for r in pv_all_rows if r[3] == "open"]
    pv_total = len(pv_all_rows); pv_open_cnt = len(pv_open_rows)
    pv_by_owner: dict[str, int] = defaultdict(int)
    for r in pv_open_rows: pv_by_owner[r[2]] += 1
    pv_owners = sorted(pv_by_owner.keys())

    lines.append('<div x-show="tab===\'platform\'" x-cloak>')
    lines.append(f'<div class="flex gap-4 mb-4">')
    for label, val, color in [("Open", pv_open_cnt, "bg-green-600"), ("Total", pv_total, "bg-indigo-600")]:
        lines.append(f'<div class="{color} text-white rounded-lg px-5 py-3 text-center shadow"><div class="text-2xl font-bold">{val}</div><div class="text-xs opacity-80">{label}</div></div>')
    lines.append('</div>')

    lines.append('<div class="overflow-x-auto mb-4"><table class="text-sm border-collapse rounded-lg overflow-hidden shadow-sm">')
    lines.append('<thead><tr class="bg-indigo-700 text-white"><th class="px-4 py-2 text-left">Owner</th><th class="px-4 py-2">Open TCs</th></tr></thead><tbody>')
    for owner in pv_owners:
        lines.append(f'<tr class="border-b hover:bg-indigo-50"><td class="px-4 py-1.5 text-indigo-700 font-medium">{_esc(owner)}</td><td class="px-4 py-1.5 text-center font-semibold">{pv_by_owner[owner]}</td></tr>')
    lines.append(f'<tr class="bg-indigo-50 font-bold border-t-2 border-indigo-300"><td class="px-4 py-2">TOTAL</td><td class="px-4 py-2 text-center">{pv_open_cnt} open / {pv_total} total</td></tr>')
    lines.append('</tbody></table></div>')

    lines.append(f'<h2 class="text-lg font-bold text-indigo-700 mb-2">Platform TC List <span class="text-sm font-normal text-slate-400">(open only — {pv_open_cnt}/{pv_total})</span></h2>')
    lines.append('<div class="overflow-x-auto"><table class="w-full text-xs border-collapse shadow rounded-lg overflow-hidden">')
    lines.append('<thead><tr class="bg-indigo-700 text-white"><th class="px-3 py-2 text-left">ID</th><th class="px-3 py-2">Owner</th><th class="px-3 py-2 text-left">Title</th><th class="px-3 py-2 text-left">TP</th><th class="px-3 py-2 text-left">TCD</th></tr></thead><tbody>')
    for (tc_id, tc_title, owner, status, tp_title, tpf_title, tcd_title) in pv_open_rows:
        lines.append(
            f'<tr class="border-b hover:bg-orange-50">'
            f'<td class="px-3 py-1.5 font-mono">{_hsd_link(tc_id, tc_id)}</td>'
            f'<td class="px-3 py-1.5 text-indigo-600 font-medium text-center">{_esc(owner)}</td>'
            f'<td class="px-3 py-1.5">{_esc(tc_title)} <span class="inline-block px-1.5 py-0.5 rounded-full text-[10px] font-bold text-white bg-orange-600 ml-1">PV</span></td>'
            f'<td class="px-3 py-1.5 text-slate-400">{_esc(tp_title)}</td>'
            f'<td class="px-3 py-1.5 text-slate-400">{_esc(tcd_title)}</td>'
            f'</tr>'
        )
    if not pv_all_rows:
        lines.append('<tr><td colspan="5" class="px-4 py-4 text-slate-400 italic">No Platform TCs found.</td></tr>')
    lines.append('</tbody></table></div></div>')  # tab-platform

    # ══ TAB: Owner View ════════════════════════════════════════════════════════
    owner_drill = _collect_owner_drilldown(hierarchy)
    lines.append('<div x-show="tab===\'owners\'" x-cloak>')
    lines.append('<h2 class="text-lg font-bold text-indigo-700 mb-1">Owner → TP → TCD → TCs <span class="text-sm font-normal text-slate-400">(open TCs only)</span></h2>')

    for owner in sorted(owner_drill.keys()):
        tp_map = owner_drill[owner]
        open_owner = sum(1 for tcd_map in tp_map.values()
                         for tcs in tcd_map.values() for _, _, st in tcs if st == "open")
        if open_owner == 0:
            continue
        lines.append(
            f'<div class="mb-6 border-l-4 border-blue-600 pl-3">'
            f'<h3 class="text-indigo-700 font-bold text-sm mb-2">👤 {_esc(owner)} '
            f'<span class="bg-indigo-500 text-white text-xs px-2 py-0.5 rounded-full ml-1">{open_owner} open</span></h3>'
        )
        lines.append('<div class="overflow-x-auto"><table class="w-full text-xs border-collapse rounded-lg overflow-hidden shadow-sm mb-2">')
        lines.append('<thead><tr class="bg-indigo-700 text-white"><th class="px-3 py-2 text-left w-64">Test Plan</th><th class="px-3 py-2 text-left">TCD</th><th class="px-3 py-2 w-16 text-center">Count</th><th class="px-3 py-2 text-left">TCs</th></tr></thead><tbody>')

        for tp_title in sorted(tp_map.keys()):
            tcd_map = tp_map[tp_title]
            tp_open = sum(1 for tcs in tcd_map.values() for _, _, st in tcs if st == "open")
            if tp_open == 0:
                continue
            # TP summary row
            lines.append(
                f'<tr class="bg-indigo-50 border-t-2 border-indigo-300">'
                f'<td colspan="2" class="px-3 py-1.5 font-bold text-indigo-700">{_esc(tp_title)}</td>'
                f'<td class="px-3 py-1.5 text-center"><span class="bg-indigo-500 text-white text-xs px-2 py-0.5 rounded-full">{tp_open}</span></td>'
                f'<td class="px-3 py-1.5"></td>'
                f'</tr>'
            )
            for tcd_title in sorted(tcd_map.keys()):
                open_tcs = [(tcid, tt, st) for tcid, tt, st in tcd_map[tcd_title] if st == "open"]
                if not open_tcs:
                    continue
                tc_links = " &nbsp;·&nbsp; ".join(
                    f'{_hsd_link(tcid, tcid)} <span class="text-slate-500">{_esc(tt[:60])}</span>'
                    for tcid, tt, _ in sorted(open_tcs, key=lambda x: x[0])
                )
                lines.append(
                    f'<tr class="border-b hover:bg-indigo-50">'
                    f'<td class="px-3 py-1.5 text-slate-300 text-xs"></td>'
                    f'<td class="px-3 py-1.5 text-slate-700 font-medium">{_esc(tcd_title)}</td>'
                    f'<td class="px-3 py-1.5 text-center"><span class="bg-slate-100 text-slate-600 text-xs px-2 py-0.5 rounded-full">{len(open_tcs)}</span></td>'
                    f'<td class="px-3 py-1.5 leading-5">{tc_links}</td>'
                    f'</tr>'
                )
        lines.append('</tbody></table></div>')
        lines.append('</div>')  # owner section

    lines.append('</div>')  # tab-owners
    lines.append('</div>')  # Alpine root
    lines.append('</body></html>')
    _write(output_path, lines)


# ── PSS HTML generator ────────────────────────────────────────────────────────

def generate_pss_html(
    root_id: str,
    root_info: dict[str, Any],
    hierarchy: list[dict[str, Any]],
    tc_stats: list[tuple[str, str]],
    output_path: str,
    phoenix_url: str | None = None,
) -> None:
    """Write a single-page PSS hierarchy HTML file to *output_path*.

    TCs and TPs whose title starts with ``[PSS]`` are marked with a purple badge.
    An optional *phoenix_url* is shown in the page header.
    """
    lines: list[str] = []

    lines.append("<!DOCTYPE html>\n<html lang=\"en\">\n<head>")
    lines.append('<meta charset="UTF-8">')
    lines.append("<title>NWP PM PSS Test Plan Hierarchy</title>")
    lines.append(f"<style>{_CSS_COMMON}{_CSS_PSS_EXTRA}</style>")
    lines.append("</head>\n<body>")

    lines.append("<h1>NWP PM PSS Test Plan Hierarchy</h1>")
    folder_link = (
        f'Phoenix folder: <a href="{phoenix_url}" target="_blank">PM ({root_id})</a>'
        if phoenix_url else f"Root: {_hsd_link(root_id, root_info.get('title', root_id))}"
    )
    lines.append(
        f"<p>{folder_link} &nbsp;|&nbsp; Family: Newport"
        f" &nbsp;|&nbsp; Total TCs: <strong>{len(tc_stats)}</strong></p>"
    )

    lines.append("<h2>TC Summary by Owner</h2>")
    tbl_lines, *_ = _owner_summary_table(tc_stats)
    lines.extend(tbl_lines)

    lines.append("<h2>Test Plan Hierarchy</h2>")

    for tp_data in hierarchy:
        tp_id    = tp_data["id"]
        pss_mark = ' <span class="inline-block px-1.5 py-0.5 rounded-full text-[10px] font-bold text-white bg-violet-700 ml-1">PSS</span>' if "[PSS]" in tp_data["title"] else ""
        lines.append(
            f'<details class="tp"><summary>'
            f'{_hsd_link(tp_id, tp_data["title"])}{pss_mark}'
            f' &nbsp; <span class="owner">{_esc(tp_data["owner"])}</span>'
            f' {_status_badge(tp_data["status"])}'
            f'</summary>'
        )
        for tpf_data in tp_data["tpfs"]:
            tpf_id = tpf_data["id"]
            lines.append(
                f'<details class="tpf"><summary>'
                f'{_hsd_link(tpf_id, tpf_data["title"])}'
                f' &nbsp; <span class="owner">{_esc(tpf_data["owner"])}</span>'
                f' {_status_badge(tpf_data["status"])} ({len(tpf_data["tcds"])} TCDs)'
                f'</summary>'
            )
            for tcd_data in tpf_data["tcds"]:
                lines.extend(_render_tcd_pss(tcd_data))
            lines.append("</details>")  # tpf

        for tcd_data in tp_data.get("direct_tcds", []):
            lines.extend(_render_tcd_pss(tcd_data, margin="16px"))

        lines.append("</details>")  # tp

    lines.append("</body></html>")
    _write(output_path, lines)


# ── Internal rendering helpers ────────────────────────────────────────────────

def _render_tcd_fv_tw(tcd_data: dict) -> list[str]:
    """Tailwind-styled TCD block for the All TCs tree."""
    tcd_id = tcd_data["id"]
    open_n = sum(1 for tc in tcd_data["tcs"] if tc.get("status") == "open")
    rej_n  = len(tcd_data["tcs"]) - open_n
    lines  = [
        '<details class="ml-4 mt-1">',
        f'<summary class="summary-arrow bg-slate-50 hover:bg-indigo-50 px-3 py-1.5 cursor-pointer rounded flex justify-between items-center text-xs border border-slate-200">'
        f'<span class="font-medium text-slate-700">{_hsd_link(tcd_id)} &nbsp; {_esc(tcd_data["title"])}'
        f' <span class="text-slate-400 ml-1">owner: {_esc(tcd_data["owner"])}</span></span>'
        f'<span class="flex gap-1">'
        f'<span class="bg-green-500 text-white text-xs px-1.5 py-0.5 rounded-full">{open_n} open</span>'
        + (f'<span class="bg-red-400 text-white text-xs px-1.5 py-0.5 rounded-full">{rej_n} other</span>' if rej_n else '')
        + f'</span></summary>',
        '<div class="divide-y divide-gray-100 bg-white border border-gray-100 rounded ml-3 mb-1">',
    ]
    for tc in tcd_data["tcs"]:
        pv  = ' <span class="inline-block px-1.5 py-0.5 rounded-full text-[10px] font-bold text-white bg-orange-600 ml-1">PV</span>'  if tc["title"].startswith("[PV]")  else ""
        pss = ' <span class="inline-block px-1.5 py-0.5 rounded-full text-[10px] font-bold text-white bg-violet-700 ml-1">PSS</span>' if tc["title"].startswith("[PSS]") else ""
        st_color = {"open": "text-green-600", "rejected": "text-red-400", "blocked": "text-orange-500"}.get(tc["status"], "text-slate-400")
        lines.append(
            f'<div class="px-3 py-2 text-xs hover:bg-indigo-50 border-b border-slate-100">'
            f'<div class="flex items-center gap-2">'
            f'<span class="font-mono text-indigo-500">{_hsd_link(tc["id"], tc["id"])}</span>'
            f'<span class="{st_color} font-semibold">{_esc(tc["status"])}</span>'
            f'<span class="text-indigo-600 font-medium">{_esc(tc["owner"])}</span>'
            f'</div>'
            f'<div class="text-slate-700 mt-0.5 leading-snug">{_esc(tc["title"])}{pv}{pss}</div>'
            f'</div>'
        )
    lines.append('</div></details>')
    return lines


def _render_tcd_fv(tcd_data: dict) -> list[str]:
    tcd_id = tcd_data["id"]
    lines  = [
        '<details class="tcd">',
        f'<summary>{_hsd_link(tcd_id)} &nbsp; {_esc(tcd_data["title"])}'
        f' &nbsp; <span style="font-size:11px">owner: {_esc(tcd_data["owner"])}</span>'
        f' &nbsp; <span style="font-size:11px">({len(tcd_data["tcs"])} TCs)</span></summary>',
    ]
    for tc in tcd_data["tcs"]:
        lines.append(_render_tc_row(tc))
    lines.append("</details>")
    return lines


def _render_tcd_pss(tcd_data: dict, margin: str = "32px") -> list[str]:
    tcd_id = tcd_data["id"]
    lines  = [
        f'<details class="tcd" style="margin-left:{margin}"><summary>'
        f'{_hsd_link(tcd_id, tcd_data["title"])}'
        f' &nbsp; <span class="owner">{_esc(tcd_data["owner"])}</span>'
        f' {_status_badge(tcd_data["status"])} ({len(tcd_data["tcs"])} TCs)'
        f'</summary>',
    ]
    for tc in tcd_data["tcs"]:
        pss = ' <span class="inline-block px-1.5 py-0.5 rounded-full text-[10px] font-bold text-white bg-violet-700 ml-1">PSS</span>' if tc["title"].startswith("[PSS]") else ""
        lines.append(
            f'<div class="tc-row">'
            f'<span class="hsd-id">{_hsd_link(tc["id"])}</span>'
            f'<span class="owner">{_esc(tc["owner"])}</span>'
            f'{_status_badge(tc["status"])}'
            f'<span class="title">{_esc(tc["title"])}{pss}</span>'
            f'</div>'
        )
    lines.append("</details>")
    return lines


def _render_tc_row(tc: dict) -> str:
    pv = ' <span class="inline-block px-1.5 py-0.5 rounded-full text-[10px] font-bold text-white bg-orange-600 ml-1">PV</span>' if tc["title"].startswith("[PV]") else ""
    return (
        f'<div class="tc-row">'
        f'<span class="hsd-id">{_hsd_link(tc["id"], tc["id"])}</span>'
        f'<span class="owner">{_esc(tc["owner"])}</span>'
        f'{_status_badge(tc["status"])}'
        f'<span class="title">{_esc(tc["title"])}{pv}</span>'
        f'</div>'
    )


def _collect_pss_rows(
    hierarchy: list[dict],
) -> list[tuple[str, str, str, str, str, str, str]]:
    """Collect (tc_id, tc_title, owner, status, tp_title, tpf_title, tcd_title) for [PSS] TCs."""
    rows = []
    for tp_data in hierarchy:
        for tpf_data in tp_data["tpfs"]:
            for tcd_data in tpf_data["tcds"]:
                for tc in tcd_data["tcs"]:
                    if tc["title"].startswith("[PSS]"):
                        rows.append((
                            tc["id"], tc["title"], tc["owner"], tc["status"],
                            tp_data["title"], tpf_data["title"], tcd_data["title"],
                        ))
        for tcd_data in tp_data.get("direct_tcds", []):
            for tc in tcd_data["tcs"]:
                if tc["title"].startswith("[PSS]"):
                    rows.append((
                        tc["id"], tc["title"], tc["owner"], tc["status"],
                        tp_data["title"], "(direct)", tcd_data["title"],
                    ))
    return rows


def _collect_owner_drilldown(
    hierarchy: list[dict],
) -> dict[str, dict[str, dict[str, list[tuple[str, str, str]]]]]:
    """Return nested dict: owner -> tp_title -> tcd_title -> [(tc_id, tc_title, status)]."""
    result: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for tp_data in hierarchy:
        tp_key = tp_data["title"]
        for tpf_data in tp_data["tpfs"]:
            for tcd_data in tpf_data["tcds"]:
                tcd_key = tcd_data["title"]
                for tc in tcd_data["tcs"]:
                    result[tc["owner"]][tp_key][tcd_key].append(
                        (tc["id"], tc["title"], tc["status"])
                    )
        for tcd_data in tp_data.get("direct_tcds", []):
            tcd_key = tcd_data["title"]
            for tc in tcd_data["tcs"]:
                result[tc["owner"]][tp_key][tcd_key].append(
                    (tc["id"], tc["title"], tc["status"])
                )
    return result


def _collect_platform_rows(
    hierarchy: list[dict],
) -> list[tuple[str, str, str, str, str, str, str]]:
    """Collect (tc_id, tc_title, owner, status, tp_title, tpf_title, tcd_title)
    for ALL Platform TCs: val_framework contains 'os-linux' AND title starts with '[PV]'.
    Callers filter by status as needed.
    """
    rows = []
    for tp_data in hierarchy:
        for tpf_data in tp_data["tpfs"]:
            for tcd_data in tpf_data["tcds"]:
                for tc in tcd_data["tcs"]:
                    vf = tc.get("val_framework") or ""
                    if "os-linux" in vf and tc["title"].startswith("[PV]"):
                        rows.append((
                            tc["id"], tc["title"], tc["owner"], tc["status"],
                            tp_data["title"], tpf_data["title"], tcd_data["title"],
                        ))
        for tcd_data in tp_data.get("direct_tcds", []):
            for tc in tcd_data["tcs"]:
                vf = tc.get("val_framework") or ""
                if "os-linux" in vf and tc["title"].startswith("[PV]"):
                    rows.append((
                        tc["id"], tc["title"], tc["owner"], tc["status"],
                        tp_data["title"], "(direct)", tcd_data["title"],
                    ))
    return rows


def _write(output_path: str, lines: list[str]) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    import os
    print(f"\n✅ Written: {output_path}")
    print(f"   Open: file://{os.path.abspath(output_path)}")
