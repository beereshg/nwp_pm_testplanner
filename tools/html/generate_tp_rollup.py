"""TP-level rollup HTML generator for NWP PM test plans.
Usage:  python tools/html/generate_tp_rollup.py --tp 16030762839 [--force]
"""
from __future__ import annotations
import argparse, datetime as dt, html, re, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from generate_unified_html import html_template

REPO_ROOT  = Path(__file__).resolve().parents[2]
CACHE_ROOT = REPO_ROOT / "KB" / "pm_tc_kb"
OUTPUT_DIR = REPO_ROOT / "KB" / "pm_tc_deepanalysis"

TP_TITLES = {
    "16030762839": "[NWP PM] SST (Speed Select Technology)",
    "22022420505": "[NWP PM] CBB CCF PM",
    "16030686481": "[NWP PM] P-State / HWP (PNC Core)",
    "15019477771": "[NWP PM] RAPL",
    "15019477838": "[NWP PM] PKGC",
    "15019477845": "[NWP PM] Power Control (SIMPL/PMAX/SVID)",
    "15019478558": "[NWP PM] C-State (PantherCove PNC)",
    "16030762529": "[NWP PM] Autonomous Idle PM (AIPM)",
    "16030763137": "[NWP PM] Thermal Management",
    "16030763243": "[NWP PM] Fabric DVFS (UFS)",
    "16030765561": "[NWP PM] PM Interfaces",
    "16030765631": "[NWP PM] PM Cross Product",
    "16030767511": "[NWP PM] Telemetry (PEM/PLR)",
    "16030785148": "[NWP PM] Platform TCD transformation",
}

def _first(txt, pat, default=""):
    m = re.search(pat, txt)
    return m.group(1).strip() if m else default

def _normalise_disp(raw):
    key = raw.lower().replace(" ","_").replace("/","_").replace("-","_")
    MAP = {"runnable_as_is":"Runnable_As-Is","runnable_on_n_1":"Runnable_On_N-1",
           "needs_adaptation":"Needs_Adaptation","skip_zbb":"Skip_ZBB",
           "tbd":"TBD","unknown":"Unknown"}
    for k,v in MAP.items():
        if k in key: return v
    return raw or "Unknown"

def _parse_tc(f):
    txt = f.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"HSD_(\d+)", f.name)
    hsd_id = m.group(1) if m else f.stem
    title = "Untitled"
    for line in txt.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            m2 = re.match(r"HSD\s*\d+:\s*(.+)", title)
            title = m2.group(1).strip() if m2 else title
            break
    raw = ""
    for pat in [r"\*\*NWP Disposition\*\*\s*\|\s*\*\*([^*|\n]+)\*\*",
                r"Disposition[:\s*]+([A-Za-z_/\-]+)"]:
        m3 = re.search(pat, txt)
        if m3: raw = m3.group(1).strip("* "); break
    areas = {"PCT":["pct","priority core turbo"],"SST-TF":["sst-tf","sst_tf","turbo frequency"],
             "SST-PP":["sst-pp","sst_pp","performance profile"],"HGS":["hgs","hardware guided"]}
    lower = txt[:800].lower()
    feat = "SST"
    for a,kws in areas.items():
        if any(k in lower for k in kws): feat = a; break
    return {"id":hsd_id,"title":title,"disposition":_normalise_disp(raw),"feature":feat,
            "status":_first(txt,r"\*\*HSD Status\*\*:\s*([^\n|]+)").strip("|").strip(),
            "rec":_first(txt,r"\*\*Recommendation:\s*([^\n*]+)"),
            "tags":_first(txt,r"\*\*Priority Tag\*\*:\s*([^\n]+)")}

def _find_tp_dir(tp_id):
    for d in CACHE_ROOT.iterdir():
        if d.is_dir() and d.name.startswith(tp_id): return d
    raise FileNotFoundError(f"No KB folder for TP {tp_id}")

# ─── Markdown section builders ────────────────────────────────────────────────

def _sec_overview(tp_id, tp_title, tcs):
    by_disp = defaultdict(int); by_feat = defaultdict(int)
    for t in tcs: by_disp[t["disposition"]] += 1; by_feat[t["feature"]] += 1
    total = len(tcs)
    runnable = sum(v for k,v in by_disp.items() if "runnable" in k.lower())
    skip     = sum(v for k,v in by_disp.items() if "skip" in k.lower())
    adapt    = sum(v for k,v in by_disp.items() if "adapt" in k.lower())
    other    = total - runnable - skip - adapt
    d_rows = "\n".join(f"| {d} | {c} | {int(c/total*100)}% |"
                       for d,c in sorted(by_disp.items(),key=lambda x:-x[1]))
    f_rows = "\n".join(f"| {f} | {c} |"
                       for f,c in sorted(by_feat.items(),key=lambda x:-x[1]))
    return f"""# TP Rollup: {tp_title}

**TP ID**: [{tp_id}](https://hsdes.intel.com/appstore/article/#{tp_id}) | **Segment**: FV | **TCs**: {total} | **Date**: {dt.date.today()}

## NWP Readiness Summary

| Category | Count |
|----------|-------|
| Runnable on NWP | {runnable} |
| Needs Adaptation | {adapt} |
| Skip (ZBB) | {skip} |
| TBD / Unknown | {other} |
| **Total** | **{total}** |

## Disposition Breakdown

| Disposition | Count | % |
|------------|-------|---|
{d_rows}

## Feature Area Distribution

| Feature Area | TC Count |
|-------------|---------|
{f_rows}

## NWP SST Scope

| Sub-Feature | DMR | NWP | Note |
|------------|-----|-----|------|
| SST-TF (Turbo Frequency) | Active | Active | Underlying mechanism for PCT |
| PCT (Priority Core Turbo) | Active | Active | 8 HP cores / 4 partitions @ 4.4 GHz |
| SST-PP (Perf Profile) | Active | ZBB | HSD 22021155414 |
| SST-CP standalone | Active | ZBB | CP throttle active as PCT mechanism only |
| SST-BF (Base Frequency) | Active | ZBB | No base freq differentiation |
| HGS (HW-Guided Sched) | Active | ZBB | ok_going_zero.txt lines 195-197 |

## Universal NWP Topology Deltas

| Dimension | DMR | NWP | Impact on All TCs |
|-----------|-----|-----|------------------|
| CBB count | 4 CBBs | 2 CBBs | Loop bounds; register iteration |
| Core count | 128 | 96 (48/CBB) | HP core count = 8 (2 per partition) |
| IMH/NIO path | imh0/imh1 | nio (single) | sv.socket0.imh0.* -> sv.socket0.nio.* |
| Test config | dmr.xml | nwp.xml | Universal swap for all runnable TCs |
| TRL fuse values | DMR-specific | NWP-specific | Read at runtime from SST_TF_INFO_2..7 |
"""

def _sec_inventory(tcs):
    rows = "\n".join(
        f"| [{t['id']}](https://hsdes.intel.com/appstore/article/#{t['id']}) "
        f"| {t['title']} | {t['feature']} | {t['disposition']} | {t['status'] or '-'} |"
        for t in tcs)
    return f"""## TC Inventory ({len(tcs)} Test Cases)

| HSD ID | Title | Feature | Disposition | HSD Status |
|--------|-------|---------|------------|------------|
{rows}
"""

def _sec_by_feature(tcs):
    by_feat = defaultdict(list)
    for t in tcs: by_feat[t["feature"]].append(t)
    out = "## Analysis by Feature Area\n\n"
    ZBB_NOTES = {"SST-PP":"SST-PP is ZBB on NWP (HSD 22021155414). All SST-PP TCs are skipped.",
                 "HGS":"HGS is ZBB on NWP (ok_going_zero.txt). All HGS TCs are skipped."}
    for feat in ["SST-TF","PCT","SST-PP","HGS","SST"]:
        if feat not in by_feat: continue
        fts = by_feat[feat]
        run = sum(1 for t in fts if "runnable" in t["disposition"].lower())
        sk  = sum(1 for t in fts if "skip" in t["disposition"].lower())
        ad  = sum(1 for t in fts if "adapt" in t["disposition"].lower())
        rows = "\n".join(
            f"| [{t['id']}](https://hsdes.intel.com/appstore/article/#{t['id']}) "
            f"| {t['title']} | {t['disposition']} "
            f"| {(t['rec'][:90]+'...') if len(t['rec'])>90 else (t['rec'] or '-')} |"
            for t in fts)
        note = f"\n{ZBB_NOTES[feat]}\n" if feat in ZBB_NOTES else ""
        out += f"""### {feat} ({len(fts)} TCs — {run} runnable, {sk} skip, {ad} adapt)
{note}
| HSD ID | Title | Disposition | Recommendation |
|--------|-------|------------|----------------|
{rows}

"""
    return out

def _sec_exec_plan(tcs):
    run  = [t for t in tcs if "runnable" in t["disposition"].lower()]
    adpt = [t for t in tcs if "adapt" in t["disposition"].lower()]
    skip = [t for t in tcs if "skip" in t["disposition"].lower()]
    hdr  = "| HSD ID | Title | Feature |\n|--------|-------|---------|\n"
    def rows(lst):
        return "\n".join(f"| [{t['id']}](https://hsdes.intel.com/appstore/article/#{t['id']}) | {t['title']} | {t['feature']} |" for t in lst)
    return f"""## Execution Plan

### Runnable on NWP — {len(run)} TCs
Config-file substitution only; core logic unchanged.

{hdr}{rows(run)}

### Needs Adaptation — {len(adpt)} TCs
Script-level changes (topology constants, CLOS count).

{hdr}{rows(adpt)}

### Skip (ZBB) — {len(skip)} TCs
Not applicable on NWP initial silicon.

{hdr}{rows(skip)}

## Recommended Execution Sequence

| Phase | TCs | Rationale |
|-------|-----|-----------|
| 1 Gate | 22022422200, 22022422217 | TPMI register population + fuse chain; gate for all SST-TF/PCT tests |
| 2 TF Core | 22022422201, 22022422202, 22022422205, 22022422212, 22022422216 | Enable/disable, CLOS assignment, HP elevation, bucket validation |
| 3 PCT E2E | 22022422103, 22022422104, 22022422105, 22022422116, 22022422117, 22022422118 | PCT TPMI, HP core selection, TDP convergence, DQ rules |
| 4 Deferred | 22022422100, 22022422110, 22022422188, 22022422194, 22022422195, 22022422197, 22022422198 | ZBB or BIOS structural changes; revisit for future stepping |
"""

def _sec_adaptations():
    return """## Common Adaptations (All Runnable TCs)

| Pattern | DMR Value | NWP Value | Priority |
|---------|-----------|-----------|---------|
| Test config file | dmr.xml / DMRSV.ini | nwp.xml / NWPSV.ini | High |
| Register path prefix | sv.socket0.imh0.punit.* | sv.socket0.nio.punit.* | High |
| CBB loop bound | range(4) | range(2) | High |
| Core count constant | 128 | 96 (48 per CBB) | High |
| HP core count (PCT) | 4 (1 per partition x 4) | 8 (2 per partition x 4) | High |
| TRL ratio values | Hard-coded DMR values | Read SST_TF_INFO_2..7 at runtime | High |
| runPmx.py module config | graniterapids NWP XML | newport XML for sst_tf / pct | Medium |
| DLCP SKU guard | Not required | Add check before SW CLOS write | Medium |
| PCT Enable BIOS knob | Standalone knob | Integrated into PCT Partition Count | Low |

## PythonSV Reference

```python
# NWP SST register paths (NIO replaces IMH)
nio = sv.socket0.nio

# SST feature capability
cap = nio.tpmi_sst.sst_header.capability_mask.read()
print(f"SST capability mask: 0x{cap:08X}")

# SST-TF feature_supported flag
tf_ok = nio.tpmi_sst.sst_tf_info_0.feature_supported.read()
print(f"SST-TF supported: {tf_ok}")

# PCT HP core count per partition (SST_TF_INFO_8)
for part in range(4):
    hp = nio.tpmi_sst.sst_tf_info_8[part].hp_core_count.read()
    print(f"  Partition {part}: {hp} HP cores")

# SST-TF enable state (SST_PP_CONTROL.feature_state bit 1)
fs = nio.tpmi_sst.sst_pp_control.feature_state.read()
print(f"SST-TF enabled: {(fs >> 1) & 1}")

# CBB loop — NWP has cbb0 and cbb1 only
for idx in range(2):
    cbb = getattr(sv.socket0, f"cbb{idx}")
    # per-CBB register reads/assertions here
```
"""

def _sec_risks():
    return """## Risk Register

| Severity | Risk | Detail / Mitigation | Affected TCs |
|----------|------|---------------------|-------------|
| High | SST-TF TPMI registers not populated | PrimeCode Phase 5 gap would fail all TCs. Verify via gate TC 22022422200 first. | 22022422200, 22022422217 |
| Medium | DLCP SKU CLOS assignment ignored | On DLCP, HP assignment is fuse-controlled; SW CLOS writes may be no-ops. Add SKU check. | 22022422205, 22022422104 |
| Medium | PCT Partition Count BIOS knob change | NWP BIOS eliminated standalone PCT Enable; TC 22022422100 already rejected. Re-evaluate after BIOS stabilises. | 22022422100 |
| Medium | runPmx.py NWP XML config missing | sst_tf and pct module XMLs may not exist for NWP. Verify with FW team before running. | 22022422103, 22022422116-118 |
| Low | Hard-coded DMR TRL ratios | Tests using fixed DMR TRL values will fail on NWP. Must read SST_TF_INFO_2..7 at runtime. | 22022422116, 22022422216 |
| Low | Virtual_platform SST-TF fuse model gaps | VP may not model all SST-TF fuse arrays. Run 22022422217 early to validate VP fidelity. | 22022422217 |
| Info | SST-PP / HGS future enablement | 7 ZBB TCs ready to re-activate if features enabled in future stepping. | 22022422110, 22022422188-198 |

## Open Actions

| # | Action | Suggested Owner | Gate TC |
|---|--------|----------------|---------|
| 1 | Verify runPmx.py NWP XML for sst_tf + pct modules | mmaltese | 22022422200 |
| 2 | Confirm NWP BIOS PCT Partition Count knob matches spec table 4 | akurathi / BIOS team | 22022422100 |
| 3 | Add DLCP SKU guard to CLOS-assignment test steps | Test owner | 22022422205 |
| 4 | Capture NWP SST-TF fuse expected values | FW / test owner | 22022422217 |
"""

def _build_md(tp_id, tp_title, tcs):
    overview = _sec_overview(tp_id, tp_title, tcs)
    return "\n".join([
        overview,
        "## Section A: NWP Delta\n" + "\n".join(overview.splitlines()[overview.splitlines().index("## NWP SST Scope"):]),
        "## Section B: Interactions\n" + _sec_by_feature(tcs),
        "## Section C: Coverage\n" + _sec_inventory(tcs),
        "## Section D: Spec Refs\n" + _sec_adaptations(),
        "## Section E: Risk Assessment\n" + _sec_risks(),
        "## Section F: Recommendations\n" + _sec_exec_plan(tcs),
    ])

def parse_args():
    p = argparse.ArgumentParser(description="Generate TP-level rollup HTML for NWP PM")
    p.add_argument("--tp", required=True, help="TP HSD ID e.g. 16030762839")
    p.add_argument("--force", action="store_true")
    return p.parse_args()

def main():
    args = parse_args()
    tp_id = args.tp.strip()
    tp_title = TP_TITLES.get(tp_id, f"TP {tp_id}")
    tp_dir = _find_tp_dir(tp_id)
    fv_dir = tp_dir / "fv"
    if not fv_dir.exists():
        print(f"No fv/ dir under {tp_dir}"); return 1
    tcs = [_parse_tc(f) for f in sorted(fv_dir.glob("*.inference.md"))]
    if not tcs:
        print("No TC files found"); return 1
    slug = tp_dir.name.replace(tp_id + "_", "")
    out_file = OUTPUT_DIR / f"TP_{tp_id}_{slug}_rollup.html"
    if out_file.exists() and not args.force:
        print(f"Already exists (use --force): {out_file}"); return 0
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    md = _build_md(tp_id, tp_title, tcs)
    final_html = html_template(f"TP Rollup: {tp_title}", "FV", f"TP {tp_id} — {len(tcs)} TCs", md)
    out_file.write_text(final_html, encoding="utf-8")
    print(f"Generated: {out_file}  ({len(tcs)} TCs)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
