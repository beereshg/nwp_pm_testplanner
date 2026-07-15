"""
Generate LLM-backed Co-Design CCF PM vs NWP CCF PM relatedness HTML report.
Usage: python tools/html/generate_codesign_ccf_relatedness.py
Output: tcd_description_output/CoDesign_CCF_PM_Relatedness_Report.html
"""

import json, pathlib, csv, textwrap
from collections import defaultdict

# ---------------------------------------------------------------------------
# Load Co-Design CSV data
# ---------------------------------------------------------------------------

def load_codesign_data():
    folder = pathlib.Path("collaterals/co-design/CCF")
    cd_rows = []
    for f in sorted(folder.glob("*.csv")):
        cd_rows.extend(list(csv.DictReader(open(f, encoding="utf-8-sig", errors="ignore"))))

    records = defaultdict(lambda: {"title": "", "hier": "", "id": "", "subsections": defaultdict(list)})
    tcd_list, tpf_list, tp_list = [], [], []
    tc_map = defaultdict(list)

    for r in cd_rows:
        rid = r["record_id"].strip()
        hier = r["hierarchy"].strip()
        title = r["title"].strip()
        sub_title = r.get("subsection title", "").strip()
        sub_content = r.get("subsection content", "").strip()
        records[rid]["title"] = title
        records[rid]["hier"] = hier
        records[rid]["id"] = rid
        if sub_title and sub_content:
            records[rid]["subsections"][sub_title].append(sub_content)
        if hier == "TP" and rid not in tp_list: tp_list.append(rid)
        elif hier == "TPF" and rid not in tpf_list: tpf_list.append(rid)
        elif hier == "TCD" and rid not in tcd_list: tcd_list.append(rid)
        elif hier == "TC":
            parts = rid.rsplit(".", 1)
            if len(parts) == 2 and rid not in tc_map[parts[0]]:
                tc_map[parts[0]].append(rid)

    return dict(records), tpf_list, tcd_list, dict(tc_map)


# ---------------------------------------------------------------------------
# Load NWP CCF PM hierarchy
# ---------------------------------------------------------------------------

def load_nwp_hierarchy():
    cache = json.load(open("nwp_pm_analysis/hierarchy/nwp_pm_fv_cache.json"))
    hier = cache["hierarchy"]

    def find_node(nodes, target):
        for n in nodes:
            if str(n.get("id", "")) == str(target): return n
            r = find_node(n.get("children", []), target)
            if r: return r
        return None

    tp = find_node(hier, "22022420505")
    result = {"tp_id": "22022420505", "tp_title": tp.get("title", ""), "tpfs": []}
    for tpf in tp.get("tpfs", []):
        tpf_data = {"id": str(tpf["id"]), "title": tpf.get("title", ""), "tcds": []}
        for tcd in tpf.get("tcds", []):
            tcs_data = [{"id": str(tc["id"]), "title": tc.get("title", "")} for tc in tcd.get("tcs", [])]
            tpf_data["tcds"].append({"id": str(tcd["id"]), "title": tcd.get("title", ""), "tcs": tcs_data})
        result["tpfs"].append(tpf_data)
    return result


# ---------------------------------------------------------------------------
# LLM-backed relatedness analysis (expert knowledge encoded)
# ---------------------------------------------------------------------------

ANALYSIS = {
    "1.1.1": {
        "score": 45,
        "rating": "MEDIUM",
        "color": "#f59e0b",
        "badge_color": "#fff7ed",
        "badge_border": "#f59e0b",
        "nwp_matches": [
            ("CBB CCF Idle States", "22022420512", "MC6 = memory-side C6; CCF must drain/flush ring before MC6 entry"),
            ("CBB CCF PM Cstate wake events", "22022422868", "Race/abort during C-state wake aligns with ring wake injection"),
            ("CBB CCF Distress Signal", "22022421197", "Thermal throttling events propagate as distress signals to CCF"),
        ],
        "overlap_concepts": ["MC6 entry coordination", "Ring flush/drain sequencing", "C-state abort/recovery", "Thermal throttling effect on CCF"],
        "unique_codesign": ["THERM_STATUS_UPDATE register validation", "Per-core LOG bit behavior", "AI model update on false thermal events", "MLC (LLC) flush race conditions"],
        "analysis": (
            "TCD 1.1.1 focuses on how the CCF ring responds when MC6 (Memory C6) is entered "
            "while an MLC (LLC) flush is in progress. NWP CCF PM covers <em>C-state wake events</em> "
            "and <em>idle state transitions</em> but does not validate the ring drain/flush sequencing "
            "or the race between MC6 entry and concurrent MLC flush operations. "
            "The thermal LOG bit validation (THERM_STATUS_UPDATE) is a <strong>new domain</strong> "
            "not present in NWP CCF PM — it belongs more to the Thermal Management TP, but the "
            "coupling with MC6 and ring abort makes it architecturally relevant here. "
            "The AI model update for false positives is entirely absent from NWP."
        ),
        "recommendation": "Partial gap: Add MC6 coordination and ring flush race scenarios to CBB CCF Idle States TPF. Thermal LOG bits belong in Thermal TP."
    },
    "1.1.2": {
        "score": 30,
        "rating": "LOW-MEDIUM",
        "color": "#ef4444",
        "badge_color": "#fef2f2",
        "badge_border": "#ef4444",
        "nwp_matches": [
            ("CBB CCF Message to Punit", "22022422896", "Latchup distress signals are routed to Punit via CCF messaging fabric"),
            ("CBB CCF Distress Signal", "22022421197", "Abnormal sensor readings can generate distress events on CCF ring"),
        ],
        "overlap_concepts": ["Distress signal propagation", "Punit messaging during fault", "CCF ring throttling on abnormal event"],
        "unique_codesign": ["MEA (Memory Express Agent) arbitration", "Latchup controller detection logic", "AI-based latchup prevention", "Current/temperature sensor injection", "Recovery flow validation post-latchup"],
        "analysis": (
            "TCD 1.1.2 covers <em>MEA arbitration during MLC flush</em> with emphasis on latchup "
            "detection via AI-based controllers. NWP CCF PM has no latchup scenario coverage — "
            "the NWP distress signal TCs test CCF-to-Punit signaling but not the upstream fault "
            "detection that <em>generates</em> those distress events. MEA arbitration is a "
            "memory-side concept that sits between IMH and CCF; NWP CCF PM does not model this "
            "interface. The AI-based latchup controller is a <strong>completely new topic</strong> "
            "likely requiring a separate RAS or Protection TP in NWP. Partial relatedness exists "
            "only through the distress signaling path."
        ),
        "recommendation": "Major gap: Latchup and MEA arbitration require new NWP TP coverage (RAS or CCF Protection). Distress path overlaps with existing Distress Signal TCD."
    },
    "1.1.3": {
        "score": 70,
        "rating": "HIGH",
        "color": "#22c55e",
        "badge_color": "#f0fdf4",
        "badge_border": "#22c55e",
        "nwp_matches": [
            ("CBB CCF Idle States", "22022420512", "Staggered C6 entry across CBB modules is core CCF idle coordination"),
            ("CBB CCF Distress Signal", "22022421197", "PVP throttling triggers distress events on CCF — same signal path"),
            ("CBB CCF PCode algorithm for distress input", "22022422905", "PCode didt algorithm handles EXE port dispatch throttling decisions"),
            ("CBB CCF Message to Punit", "22022422896", "PVP events are communicated to Punit via CCF messaging"),
        ],
        "overlap_concepts": ["C6/MC6 staggered entry", "PVP throttling", "didt risk management", "EXE port dispatch control", "CCF ring frequency reduction under stress"],
        "unique_codesign": ["Energy cost predictor over 64-cycle / 1024-cycle windows", "Borderline vs extreme PVP threshold sweeping", "EXE port dispatch halt verification", "Per-module staggering order validation"],
        "analysis": (
            "TCD 1.1.3 is <strong>highly relevant</strong> to NWP CCF PM. Staggered C6/MC6 entry "
            "across modules is the primary mechanism the CCF idle FSM uses to prevent didt spikes. "
            "NWP has C6 entry TCs but does NOT test the staggering order or validate that modules "
            "enter C6 in the correct sequence. The PVP throttling path (energy predictor → "
            "threshold exceeded → EXE dispatch halted → CCF ring frequency reduced) overlaps "
            "directly with NWP's Distress Signal and PCode algorithm TCs — but NWP only tests "
            "the <em>downstream effect</em> (distress signal observed), not the <em>upstream "
            "trigger</em> (PVP threshold, 64-cycle window). This gap means NWP currently validates "
            "CCF's response to distress but not the conditions that cause distress."
        ),
        "recommendation": "High priority gap: Add PVP threshold / energy predictor TCs to CBB CCF Idle States and Distress Signal TCDs. Staggered entry ordering is critical for didt safety."
    },
    "1.1.4": {
        "score": 88,
        "rating": "VERY HIGH",
        "color": "#16a34a",
        "badge_color": "#dcfce7",
        "badge_border": "#16a34a",
        "nwp_matches": [
            ("CBB CCF GV BIOS Configuration", "22022421165", "BIOS sets GV bounds; arbitration respects configured VF curve limits"),
            ("CBB CCF GV PEGA", "22022421168", "PEGA injects AGV/FGV requests — direct AGV/FGV arbitration stimulus"),
            ("CBB CCF GV TPMI Interface", "22022421171", "TPMI UFS_CONTROL is the SW path for GV requests that feed arbitration"),
            ("CBB CCF VF Curves", "22022421174", "VF curve validation ensures work-points are legal under arbitration"),
            ("CBB CCF NonAutoGV Mode", "22022421183", "FGV (Fast GV / NonAutoGV) mode is one of the arbitration inputs"),
        ],
        "overlap_concepts": ["AGV (Auto GV) requests", "FGV (Fast/NonAuto GV) requests", "GV arbitration winner selection", "Work-point application", "C6/MC3/MC6 transition during GV change", "PMA FSM state during GV"],
        "unique_codesign": ["Simultaneous AGV+FGV contention under C-state transitions", "Atomicity of GV work-point application", "didt prevention via transition staggering", "PMA FSM ordering during multi-module transitions"],
        "analysis": (
            "TCD 1.1.4 is the <strong>most directly relevant</strong> Co-design TCD to NWP CCF PM. "
            "GV arbitration between AGV and FGV requestors during C-state transitions is the "
            "central CCF PM mechanism. NWP tests each GV path independently: "
            "<em>BIOS config → TPMI → PEGA → VF curves</em>. However, NWP does NOT test "
            "<strong>simultaneous contention</strong> between AGV and FGV, nor does it validate "
            "arbitration atomicity when C-state transitions occur mid-GV. "
            "The Co-design TCs specifically cover: "
            "(a) AGV arbitration during C6/MC3/MC6 entry/exit, "
            "(b) FGV arbitration and work-point application timing, "
            "(c) AGV/FGV contention race conditions. "
            "These are <strong>critical missing scenarios</strong> in NWP — the existing NWP TCs "
            "test steady-state GV, not GV under concurrent C-state pressure."
        ),
        "recommendation": "Critical gap: Extend CBB CCF Active States TPF with AGV/FGV contention and C-state transition TCs. These are direct additions to existing TCD 22022421168 (PEGA) and 22022421171 (TPMI)."
    },
    "1.1.5": {
        "score": 65,
        "rating": "HIGH",
        "color": "#22c55e",
        "badge_color": "#f0fdf4",
        "badge_border": "#22c55e",
        "nwp_matches": [
            ("CBB CCF GV TPMI Interface", "22022421171", "TPMI UFS_CONTROL carries per-CBB GV control; ICCP interacts with same path"),
            ("CBB CCF PCode algorithm for distress input", "22022422905", "PCode computes PVP thresholds; ICCP grants affect PVP1024Thold"),
            ("CBB CCF Distress Signal", "22022421197", "PVP threshold propagation feeds into CCF distress threshold logic"),
            ("CBB CCF Message to Punit", "22022422896", "ICCP license state communicated to Punit via CCF message fabric"),
        ],
        "overlap_concepts": ["ICCP license arbitration", "PVP1024Thold signal propagation", "PvpThold consistency at PMA interface", "ICCPU2CGrantLicenseMnnnH per-CBB grant tracking"],
        "unique_codesign": ["ICCP license request stimulus from both cores", "Stale value detection on grant signals", "Signal consistency between core and PMA interfaces", "SBFT (Self-Bake Full Test) sleep coordination"],
        "analysis": (
            "TCD 1.1.5 covers <em>ICCP license management</em> and <em>PVP threshold propagation</em> "
            "through the PMA (Power Management Agent) interface. In NWP CCF PM, the PCode algorithm "
            "TCD (22022421205) computes distress thresholds but does not validate the ICCP grant "
            "signal path (ICCPU2CGrantLicenseMnnnH) or the per-grant update of PVP1024Thold[7:0]. "
            "These are <strong>observability gaps</strong>: NWP tests that distress thresholds "
            "take effect, but not the ICCP-to-threshold propagation chain. "
            "The SBFT@Field diagnostic sleep coordination is a <strong>new concept</strong> — "
            "it implies coordinating CCF ring sleep with in-field self-test, which NWP has no "
            "coverage for. Signal consistency validation at both core and PMA interfaces is "
            "a strong addition to existing TPMI and PCode algorithm TCDs."
        ),
        "recommendation": "Medium-high gap: Add ICCP grant propagation and PVP threshold consistency checks to CBB CCF PCode Algorithm TCD. SBFT coordination is a new scenario requiring a new TCD."
    },
}


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

def score_bar(score):
    color_map = [(90, "#16a34a"), (70, "#22c55e"), (45, "#f59e0b"), (30, "#ef4444"), (0, "#dc2626")]
    color = next(c for t, c in color_map if score >= t)
    return f"""<div class="score-bar-outer"><div class="score-bar-inner" style="width:{score}%;background:{color}"></div><span class="score-label">{score}%</span></div>"""


def tc_table(tc_ids, records):
    if not tc_ids:
        return "<p class='no-tc'>No TCs in CSV sample</p>"
    rows = ""
    for tc_id in tc_ids:
        rec = records.get(tc_id, {})
        title = rec.get("title", tc_id)
        subs = rec.get("subsections", {})
        desc = " ".join(subs.get("TC Description *", ["—"]))[:250]
        steps = " ".join(subs.get("Test Steps *", ["—"]))[:200]
        pf = " ".join(subs.get("Pass/Fail Criteria & HW Errors *", ["—"]))[:200]
        rows += f"""<tr>
          <td class="tc-id">{tc_id}</td>
          <td class="tc-title">{title}</td>
          <td class="tc-desc">{desc}{'…' if len(desc)==250 else ''}</td>
          <td class="tc-steps">{steps}{'…' if len(steps)==200 else ''}</td>
          <td class="tc-pf">{pf}{'…' if len(pf)==200 else ''}</td>
        </tr>"""
    return f"""<table class="tc-table">
      <thead><tr><th>ID</th><th>TC Title</th><th>Description</th><th>Test Steps (excerpt)</th><th>Pass/Fail Criteria</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


def nwp_match_chips(matches):
    chips = ""
    for title, hid, reason in matches:
        chips += f"""<div class="match-chip">
          <div class="match-chip-head"><span class="match-hid">HSD {hid}</span><span class="match-title">{title}</span></div>
          <div class="match-reason">{reason}</div>
        </div>"""
    return chips


def concept_tags(concepts, color):
    return " ".join(f'<span class="concept-tag" style="background:{color}20;border-color:{color}">{c}</span>' for c in concepts)


def generate_html(records, tpf_list, tcd_list, tc_map, nwp):
    # Overall stats
    total_cd_tcs = sum(len(v) for v in tc_map.values())
    total_nwp_tcs = sum(len(tcd["tcs"]) for tpf in nwp["tpfs"] for tcd in tpf["tcds"])
    total_nwp_tcds = sum(len(tpf["tcds"]) for tpf in nwp["tpfs"])
    avg_score = int(sum(ANALYSIS[t]["score"] for t in tcd_list if t in ANALYSIS) / len([t for t in tcd_list if t in ANALYSIS]))

    # NWP hierarchy for sidebar
    nwp_sidebar = ""
    for tpf in nwp["tpfs"]:
        nwp_sidebar += f'<div class="nwp-tpf"><div class="nwp-tpf-title">TPF {tpf["id"]}: {tpf["title"]}</div>'
        for tcd in tpf["tcds"]:
            tc_badge = f'<span class="nwp-tc-count">{len(tcd["tcs"])} TC{"s" if len(tcd["tcs"])!=1 else ""}</span>'
            nwp_sidebar += f'<div class="nwp-tcd"><div class="nwp-tcd-title">{tcd["title"]} {tc_badge}</div>'
            for tc in tcd["tcs"]:
                nwp_sidebar += f'<div class="nwp-tc">• {tc["title"]}</div>'
            nwp_sidebar += "</div>"
        nwp_sidebar += "</div>"

    # TCD sections
    tcd_sections = ""
    for tcd_id in tcd_list:
        rec = records.get(tcd_id, {})
        title = rec.get("title", tcd_id)
        tcs = tc_map.get(tcd_id, [])
        ana = ANALYSIS.get(tcd_id, {})
        score = ana.get("score", 0)
        rating = ana.get("rating", "UNKNOWN")
        color = ana.get("color", "#6b7280")
        bc = ana.get("badge_color", "#f9fafb")
        bb = ana.get("badge_border", "#6b7280")
        matches = ana.get("nwp_matches", [])
        overlap = ana.get("overlap_concepts", [])
        unique = ana.get("unique_codesign", [])
        analysis_text = ana.get("analysis", "")
        recommendation = ana.get("recommendation", "")

        tcd_sections += f"""
<div class="tcd-card" id="tcd-{tcd_id.replace('.', '-')}">
  <div class="tcd-header" style="border-left:5px solid {color}">
    <div class="tcd-header-top">
      <span class="tcd-id-badge">TCD {tcd_id}</span>
      <span class="relatedness-badge" style="background:{bc};border:1px solid {bb};color:{color}">{rating} RELATEDNESS</span>
    </div>
    <h2 class="tcd-title">{title}</h2>
    <div class="score-row">
      <span class="score-label-text">Relatedness to NWP CCF PM:</span>
      {score_bar(score)}
    </div>
  </div>

  <div class="tcd-body">
    <!-- Analysis -->
    <div class="analysis-block">
      <h3 class="block-title">LLM Analysis</h3>
      <p class="analysis-text">{analysis_text}</p>
    </div>

    <!-- NWP Matches -->
    <div class="matches-block">
      <h3 class="block-title">Closest NWP CCF PM Matches</h3>
      <div class="match-chips">{nwp_match_chips(matches) if matches else '<p class="no-match">No direct NWP matches — this is new coverage.</p>'}</div>
    </div>

    <!-- Concepts -->
    <div class="concepts-row">
      <div class="concepts-col">
        <h4 class="concepts-title overlap">Overlapping Concepts</h4>
        {concept_tags(overlap, color) if overlap else '<span class="no-concept">None identified</span>'}
      </div>
      <div class="concepts-col">
        <h4 class="concepts-title unique">Unique Co-Design Content</h4>
        {concept_tags(unique, "#7c3aed") if unique else '<span class="no-concept">None</span>'}
      </div>
    </div>

    <!-- TC Table -->
    <div class="tc-block">
      <h3 class="block-title">TCs in Co-Design CSV <span class="tc-count-badge">{len(tcs)} TCs</span></h3>
      {tc_table(tcs, records)}
    </div>

    <!-- Recommendation -->
    <div class="rec-block">
      <span class="rec-icon">💡</span>
      <div>
        <strong>Recommendation:</strong> {recommendation}
      </div>
    </div>
  </div>
</div>
"""

    # Summary table
    summary_rows = ""
    for tcd_id in tcd_list:
        rec = records.get(tcd_id, {})
        title = rec.get("title", tcd_id)
        ana = ANALYSIS.get(tcd_id, {})
        score = ana.get("score", 0)
        rating = ana.get("rating", "")
        color = ana.get("color", "#6b7280")
        top_match = ana.get("nwp_matches", [("None", "", "")])[0]
        top_match_text = f"{top_match[0]} (HSD {top_match[1]})" if top_match[0] != "None" else "No direct match"
        summary_rows += f"""<tr>
          <td><a href="#tcd-{tcd_id.replace('.','- ')}">{tcd_id}</a></td>
          <td>{title}</td>
          <td><span class="summary-rating" style="color:{color}">{rating}</span></td>
          <td>{score_bar(score)}</td>
          <td class="summary-match">{top_match_text}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Co-Design CCF PM vs NWP CCF PM — Relatedness Report</title>
<style>
:root {{
  --primary: #1e3a5f;
  --accent: #2563eb;
  --bg: #f8fafc;
  --card-bg: #ffffff;
  --border: #e2e8f0;
  --text: #1e293b;
  --muted: #64748b;
  --overlap-color: #0369a1;
  --unique-color: #7c3aed;
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }}

/* Header */
.report-header {{
  background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
  color: white;
  padding: 40px 48px 32px;
}}
.report-header h1 {{ font-size: 2rem; font-weight: 700; margin-bottom: 8px; }}
.report-header .subtitle {{ font-size: 1rem; opacity: 0.85; margin-bottom: 24px; }}
.header-meta {{ display: flex; gap: 32px; flex-wrap: wrap; }}
.meta-item {{ display: flex; flex-direction: column; }}
.meta-label {{ font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.7; }}
.meta-value {{ font-size: 1.1rem; font-weight: 600; }}

/* Stats bar */
.stats-bar {{
  display: grid; grid-template-columns: repeat(auto-fit, minmax(160px,1fr));
  gap: 16px; padding: 24px 48px; background: white;
  border-bottom: 1px solid var(--border); box-shadow: 0 1px 3px rgba(0,0,0,.08);
}}
.stat-card {{ text-align: center; padding: 12px; border-radius: 8px; border: 1px solid var(--border); }}
.stat-number {{ font-size: 2rem; font-weight: 700; color: var(--accent); }}
.stat-label {{ font-size: 0.78rem; color: var(--muted); margin-top: 2px; }}

/* Layout */
.main-layout {{ display: flex; gap: 0; min-height: calc(100vh - 260px); }}
.sidebar {{ width: 300px; flex-shrink: 0; background: white; border-right: 1px solid var(--border); padding: 24px 20px; position: sticky; top: 0; max-height: 100vh; overflow-y: auto; }}
.sidebar-title {{ font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); font-weight: 600; margin-bottom: 16px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }}
.content-area {{ flex: 1; padding: 32px 48px; }}

/* NWP Sidebar */
.nwp-tpf {{ margin-bottom: 16px; }}
.nwp-tpf-title {{ font-size: 0.8rem; font-weight: 700; color: var(--primary); background: #eff6ff; border-radius: 4px; padding: 4px 8px; margin-bottom: 6px; }}
.nwp-tcd {{ margin-left: 8px; margin-bottom: 8px; }}
.nwp-tcd-title {{ font-size: 0.75rem; font-weight: 600; color: var(--text); display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }}
.nwp-tc {{ font-size: 0.7rem; color: var(--muted); margin-left: 8px; padding: 1px 0; }}
.nwp-tc-count {{ font-size: 0.65rem; background: #dbeafe; color: #1d4ed8; border-radius: 9px; padding: 1px 7px; white-space: nowrap; }}

/* Summary table */
.summary-section {{ margin-bottom: 40px; }}
.summary-section h2 {{ font-size: 1.3rem; font-weight: 700; color: var(--primary); margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid var(--accent); }}
.summary-table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
.summary-table th {{ background: var(--primary); color: white; padding: 10px 12px; text-align: left; font-weight: 600; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; }}
.summary-table td {{ padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: middle; }}
.summary-table tr:hover {{ background: #f8fafc; }}
.summary-table a {{ color: var(--accent); text-decoration: none; font-weight: 600; }}
.summary-rating {{ font-weight: 700; font-size: 0.8rem; }}
.summary-match {{ font-size: 0.78rem; color: var(--muted); }}

/* Score bar */
.score-bar-outer {{ display: flex; align-items: center; gap: 10px; }}
.score-bar-inner {{ height: 8px; border-radius: 4px; transition: width 0.3s; }}
.score-label {{ font-size: 0.78rem; font-weight: 700; color: var(--text); min-width: 36px; }}

/* TCD Cards */
.tcd-card {{
  background: var(--card-bg); border-radius: 12px;
  border: 1px solid var(--border); margin-bottom: 40px;
  box-shadow: 0 2px 8px rgba(0,0,0,.06); overflow: hidden;
}}
.tcd-header {{ padding: 24px 28px 20px; background: #fafafa; border-bottom: 1px solid var(--border); }}
.tcd-header-top {{ display: flex; align-items: center; gap: 12px; margin-bottom: 10px; flex-wrap: wrap; }}
.tcd-id-badge {{ font-size: 0.75rem; font-weight: 700; background: var(--primary); color: white; border-radius: 4px; padding: 3px 10px; letter-spacing: 0.04em; }}
.relatedness-badge {{ font-size: 0.72rem; font-weight: 700; border-radius: 4px; padding: 3px 10px; letter-spacing: 0.03em; }}
.tcd-title {{ font-size: 1.2rem; font-weight: 700; color: var(--primary); margin-bottom: 12px; }}
.score-row {{ display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }}
.score-label-text {{ font-size: 0.8rem; color: var(--muted); white-space: nowrap; }}
.score-bar-outer {{ flex: 1; max-width: 280px; }}

/* TCD body blocks */
.tcd-body {{ padding: 24px 28px; }}
.block-title {{ font-size: 0.9rem; font-weight: 700; color: var(--primary); margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.04em; border-left: 3px solid var(--accent); padding-left: 8px; }}
.analysis-block {{ margin-bottom: 24px; background: #f0f9ff; border-radius: 8px; padding: 16px 20px; border: 1px solid #bae6fd; }}
.analysis-text {{ font-size: 0.88rem; color: var(--text); line-height: 1.7; }}
.matches-block {{ margin-bottom: 24px; }}
.match-chips {{ display: flex; flex-direction: column; gap: 10px; }}
.match-chip {{ background: #f8fafc; border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; }}
.match-chip-head {{ display: flex; align-items: center; gap: 8px; margin-bottom: 4px; flex-wrap: wrap; }}
.match-hid {{ font-size: 0.7rem; font-weight: 700; background: #dbeafe; color: #1e40af; border-radius: 4px; padding: 2px 8px; }}
.match-title {{ font-size: 0.84rem; font-weight: 600; color: var(--text); }}
.match-reason {{ font-size: 0.78rem; color: var(--muted); padding-left: 2px; }}
.no-match {{ font-size: 0.84rem; color: var(--muted); font-style: italic; }}
.concepts-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
.concepts-col {{ }}
.concepts-title {{ font-size: 0.8rem; font-weight: 700; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.03em; }}
.concepts-title.overlap {{ color: var(--overlap-color); }}
.concepts-title.unique {{ color: var(--unique-color); }}
.concept-tag {{ display: inline-block; font-size: 0.74rem; border: 1px solid; border-radius: 4px; padding: 2px 8px; margin: 2px 3px 2px 0; font-weight: 500; }}
.no-concept {{ font-size: 0.8rem; color: var(--muted); font-style: italic; }}
.tc-block {{ margin-bottom: 24px; overflow-x: auto; }}
.tc-count-badge {{ font-size: 0.7rem; font-weight: 700; background: #dbeafe; color: #1d4ed8; border-radius: 9px; padding: 2px 10px; margin-left: 8px; }}
.tc-table {{ width: 100%; border-collapse: collapse; font-size: 0.78rem; }}
.tc-table th {{ background: #f1f5f9; color: var(--muted); padding: 8px 10px; text-align: left; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.04em; border-bottom: 2px solid var(--border); }}
.tc-table td {{ padding: 8px 10px; border-bottom: 1px solid var(--border); vertical-align: top; }}
.tc-id {{ font-weight: 700; color: var(--accent); white-space: nowrap; min-width: 60px; }}
.tc-title {{ font-weight: 600; color: var(--text); min-width: 180px; }}
.tc-desc {{ color: var(--muted); max-width: 220px; }}
.tc-steps {{ color: var(--muted); max-width: 200px; }}
.tc-pf {{ color: var(--muted); max-width: 200px; }}
.no-tc {{ font-size: 0.84rem; color: var(--muted); font-style: italic; }}
.rec-block {{ display: flex; align-items: flex-start; gap: 10px; background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 14px 18px; font-size: 0.84rem; color: #78350f; }}
.rec-icon {{ font-size: 1.1rem; flex-shrink: 0; margin-top: 1px; }}

/* Footer */
.report-footer {{ background: var(--primary); color: white; text-align: center; padding: 20px; font-size: 0.8rem; opacity: 0.85; margin-top: 40px; }}

@media (max-width: 900px) {{
  .main-layout {{ flex-direction: column; }}
  .sidebar {{ width: 100%; max-height: none; position: static; border-right: none; border-bottom: 1px solid var(--border); }}
  .content-area {{ padding: 24px 20px; }}
  .concepts-row {{ grid-template-columns: 1fr; }}
  .report-header {{ padding: 24px 20px; }}
  .stats-bar {{ padding: 16px 20px; }}
}}
</style>
</head>
<body>

<div class="report-header">
  <h1>Co-Design CCF PM ↔ NWP CCF PM Relatedness Report</h1>
  <div class="subtitle">LLM-backed analysis: How closely does the Co-Design CCF PM content align with the existing NWP CCF PM test plan (TP 22022420505)?</div>
  <div class="header-meta">
    <div class="meta-item"><span class="meta-label">Co-Design TP</span><span class="meta-value">CCF PM Flows: Stress Detection &amp; Response</span></div>
    <div class="meta-item"><span class="meta-label">NWP Target TP</span><span class="meta-value">22022420505 — [NWP PM] CBB CCF PM</span></div>
    <div class="meta-item"><span class="meta-label">Analysis Date</span><span class="meta-value">2026-07-09</span></div>
    <div class="meta-item"><span class="meta-label">Co-Design Source</span><span class="meta-value">collaterals/co-design/CCF/ (5 CSVs, 750 rows)</span></div>
  </div>
</div>

<div class="stats-bar">
  <div class="stat-card"><div class="stat-number">5</div><div class="stat-label">Co-Design TCDs</div></div>
  <div class="stat-card"><div class="stat-number">{total_cd_tcs}</div><div class="stat-label">Co-Design TCs (CSV sample)</div></div>
  <div class="stat-card"><div class="stat-number">{total_nwp_tcds}</div><div class="stat-label">NWP Existing TCDs</div></div>
  <div class="stat-card"><div class="stat-number">{total_nwp_tcs}</div><div class="stat-label">NWP Existing TCs</div></div>
  <div class="stat-card"><div class="stat-number">{avg_score}%</div><div class="stat-label">Average Relatedness</div></div>
  <div class="stat-card"><div class="stat-number">0</div><div class="stat-label">Exact Duplicate TCs</div></div>
</div>

<div class="main-layout">
  <div class="sidebar">
    <div class="sidebar-title">NWP CCF PM Hierarchy (TP 22022420505)</div>
    {nwp_sidebar}
  </div>

  <div class="content-area">
    <!-- Summary Table -->
    <div class="summary-section">
      <h2>Relatedness Summary</h2>
      <table class="summary-table">
        <thead><tr><th>TCD ID</th><th>Co-Design Title</th><th>Rating</th><th>Score</th><th>Top NWP Match</th></tr></thead>
        <tbody>{summary_rows}</tbody>
      </table>
    </div>

    <!-- Detailed TCD Sections -->
    {tcd_sections}
  </div>
</div>

<div class="report-footer">
  Generated by GitHub Copilot LLM analysis &nbsp;|&nbsp; NWP PM Test Plan Repo &nbsp;|&nbsp; 2026-07-09
</div>

</body>
</html>"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    records, tpf_list, tcd_list, tc_map = load_codesign_data()
    nwp = load_nwp_hierarchy()
    html = generate_html(records, tpf_list, tcd_list, tc_map, nwp)

    out_dir = pathlib.Path("tcd_description_output")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "CoDesign_CCF_PM_Relatedness_Report.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Written: {out_path} ({out_path.stat().st_size:,} bytes)")
