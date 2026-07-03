---
name: tc-script-matcher
description: >
  Match NWP PM test cases (TCs) to their implementation scripts in a PythonSV PM
  repository. Given a Test Plan (TP) ID, walks the TP→TCD→TC hierarchy via hsd_utils,
  extracts Pre-conditions and Test Steps from each TC description, indexes all Python
  scripts in a target PM directory (using AST), and produces a TC-to-script alignment
  report with gap analysis and enhancement recommendations. Use when asked to:
  "find the script for TC X", "check if TCs under TP Y are covered by scripts",
  "validate test description matches script implementation", or
  "identify missing coverage in the PM test scripts".
---

# TC-to-Script Matcher Skill

> Repo root: `c:/github/nwp_testplan/`
> Script root: typically `C:\github\frameworks.validation.pythonsv.projects.diamondrapids\pm`
> Dependencies: `hsd_utils` (hierarchy walk), Python `ast` module (script indexing)

---

## When to Use

- User provides a TP ID and asks "which scripts cover these TCs?"
- User says "check script alignment for TP 16030762939"
- User wants to find gaps between TC description intent and script implementation
- User asks "what enhancements are needed for TC X script?"

---

## Workflow

```
Step 1: Walk TP hierarchy   TP → [TPF] → TCD → TC   (via hsd_utils get_children)
Step 2: Index PM scripts     AST-scan all .py files in PM directory
Step 3: Extract TC intent    Pre-conditions + Test Steps from HTML description
Step 4: Match TCs to scripts Keyword scoring + LLM understanding
Step 5: Gap analysis         Identify STRONG / WEAK / NO_MATCH + enhancements
```

---

## Step 1 — Walk TP Hierarchy

**CRITICAL:** The children API uses `child_subject` (not `subject`) as the query parameter.
The `hsd_utils.queries.get_children()` function uses this correctly.

```python
import sys, json, time
sys.path.insert(0, ".")
from hsd_utils.session import get_session
from hsd_utils.queries import get_article, get_children

sess = get_session()
TP_ID = "<tp_id>"

# Some TPs have TPF level, some have TCD directly under TP
# Try TCD first, then try TPF → TCD → TC

tcds_direct = get_children(TP_ID, "test_case_definition",
    fields="id,title,description", session=sess)

if tcds_direct:
    # TP → TCD → TC (no TPF level) — example: PCT TP 16030762939
    all_tcds = tcds_direct
else:
    # TP → TPF → TCD → TC — example: C-State TP 15019478558
    tpfs = get_children(TP_ID, "test_plan_feature",
        fields="id,title", session=sess)
    all_tcds = []
    for tpf in tpfs:
        tcds = get_children(tpf["id"], "test_case_definition",
            fields="id,title,description", session=sess)
        all_tcds.extend(tcds)
        time.sleep(0.2)

# Collect all TCs
all_tcs = []
for tcd in all_tcds:
    tcs = get_children(tcd["id"], "test_case",
        fields="id,title,description,test_case.test_commands,test_case.val_environment",
        session=sess)
    for tc in tcs:
        all_tcs.append({
            "tcd_id": str(tcd["id"]), "tcd_title": tcd["title"],
            "tc_id": str(tc["id"]), "tc_title": tc["title"],
            "cmd": tc.get("test_case.test_commands","") or "",
            "env": tc.get("test_case.val_environment","") or "",
            "desc": tc.get("description","") or "",
        })
    time.sleep(0.2)

print(f"Total TCs: {len(all_tcs)}")
```

### Hierarchy variants observed in NWP PM

| TP | Hierarchy | Note |
|----|-----------|------|
| C-State (15019478558) | TP → TPF → TCD → TC | 5 TPFs, 11 TCDs, 52 TCs |
| PCT (16030762939) | TP → TCD → TC | 5 TCDs direct, 28 TCs |
| Always try TCD direct first | — | 503 on TPF = no TPF level |

---

## Step 2 — Index PM Scripts

Build an AST-based index of all Python scripts in the PM directory:

```python
import pathlib, ast, json

PM_ROOT = pathlib.Path(r"C:\github\frameworks.validation.pythonsv.projects.diamondrapids\pm")

def extract_script_info(py_file):
    try:
        src = py_file.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(src)
    except:
        return None
    info = {
        "file": str(py_file.relative_to(PM_ROOT)),
        "module_doc": ast.get_docstring(tree) or "",
        "classes": [], "functions": [],
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = [{"name": m.name, "doc": ast.get_docstring(m) or ""}
                       for m in node.body if isinstance(m, ast.FunctionDef)]
            info["classes"].append({"name": node.name, "doc": ast.get_docstring(node) or "", "methods": methods})
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            info["functions"].append({"name": node.name, "doc": ast.get_docstring(node) or ""})
    return info

index = []
for f in PM_ROOT.rglob("*.py"):
    if "__pycache__" in str(f): continue
    info = extract_script_info(f)
    if info and (info["classes"] or info["functions"] or info["module_doc"]):
        index.append(info)

pathlib.Path("nwp_pm_analysis/pm_script_index.json").write_text(json.dumps(index,indent=2))
print(f"Indexed {len(index)} scripts")
```

### PM Directory Structure

```
pm/
  Active_PM/
    SST/
      pct/          pct_pmx.py (PMX test), pct_focus.py (library functions)
      sst_bf/       sst_bf_pmx.py, sst_bf_validate.py
      sst_cp/       sst_cp_pmx.py, sst_cp_validate.py
      sst_pp/       sst_pp_pmx.py, sst_pp_validate.py
      sst_tf/       sst_tf_pmx.py, sst_tf_validate.py
      utilities/    sst_feature_utils.py, sst_utils.py, sst_validate.py
  Idle_PM/
    autonomous_idle/  tcg.py, ssr.py
  pmx/              runPmx.py, dmr.xml, pmx_lib2.py
  pss/
    pct/            run_pct_pss_suite.py, tc_16030715xxx_*.py
    sst/            individual tc_*.py modules
  Solar/
    SOLAR_DMR_XMLS/ Exercise/ and Verify/ XML configs
  pmutils/          pega.py, pstatesDebug.py, convert.py
```

### PMX integration pattern

Scripts named `*_pmx.py` are PMX test modules invoked via:
```bash
runPmx.py -x dmr.xml -p <module_name> -tM <timeout> -M <loops>
```
Where `<module_name>` is the XML `<tag>` in `pmx/xml/dmr.xml`.

### PSS TC module pattern

PSS TCs follow the naming: `pss/<feature>/tc_<hsd_id>_<slug>.py`
Each has a `run()` function that returns True/False.
The suite runner is `pss/<feature>/run_<feature>_pss_suite.py`.

---

## Step 3 — Extract TC Intent from Description

TC descriptions are HTML. Extract Pre-conditions and Test Steps:

```python
import re, html

def strip_html(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()

def extract_sections(desc_html):
    text = strip_html(desc_html)
    sec = {"scope":"","preconditions":"","steps":"","pass_fail":""}
    for label, key in [
        ("Validation Scope","scope"),
        ("Precondition","preconditions"),
        ("Test Step","steps"),
        ("Pass","pass_fail"),
    ]:
        m = re.search(
            rf"{label}[s]?\s*(.{{20,600}}?)(?:Test Step|Pass|Fail|Health|Reference|$)",
            text, re.I|re.S
        )
        if m:
            sec[key] = m.group(1)[:400].strip()
    return sec
```

---

## Step 4 — Match TCs to Scripts

### Keyword scoring (fast, deterministic)

Build a keyword dictionary per known script, then score TC text against it:

```python
SCRIPT_KEYWORDS = {
    # Format: "relative/path/script.py": ["keyword1", "keyword2", ...]
    "Active_PM/SST/pct/pct_pmx.py":
        ["pct","turbo","hp core","lp core","ratio","convergence","tdp","frequency","tf enable"],
    "Active_PM/SST/pct/pct_focus.py":
        ["pct","capability","bios","nvram","clos","hp core","lp core","capid4"],
    "pss/pct/tc_16030715676_all_hp_in_c6.py":
        ["all hp","c6","hp cores in c6","c-state","residency"],
    "pss/pct/tc_16030715678_bios_menu.py":
        ["bios menu","bios knob","nvram","tpmi match"],
    # ... extend per feature
}

def score_match(tc_text, script_key, keyword_map):
    text_lower = tc_text.lower()
    kws = keyword_map.get(script_key, [])
    hits = [k for k in kws if k.lower() in text_lower]
    return len(hits), hits

def classify(score):
    if score >= 3: return "STRONG"
    if score >= 1: return "WEAK"
    return "NO_MATCH"
```

### LLM semantic matching (for WEAK/NO_MATCH)

When keyword scoring gives WEAK or NO_MATCH, use the LLM to read both the TC description and the script `module_doc` + function names/docstrings, then determine:
1. Which script(s) implement the TC intent
2. What gaps exist between description and implementation
3. What enhancements are recommended

Prompt pattern:
```
TC Title: {title}
TC Intent (from description): {scope} | Pre-conditions: {preconditions} | Steps: {steps}

Available scripts:
{for each script in top candidates: file + module_doc + class/function names}

Question:
1. Which script(s) best implement this TC's intent? Why?
2. What is covered correctly?
3. What is missing or misaligned?
4. What enhancements are needed?
```

---

## Step 5 — Gap Analysis Report Format

```
TC-to-Script Alignment Report: TP {tp_id} — {tp_title}
══════════════════════════════════════════════════════════
Total TCs: {n}   STRONG: {s}   WEAK: {w}   NO_MATCH: {m}

STRONG MATCHES (script clearly implements TC intent)
─────────────────────────────────────────────────────
✅ {tc_id}: {tc_title}
   Script: {script_path}
   Matched on: [{keywords}]
   Enhancement: {any gaps found}

WEAK MATCHES (partial alignment — needs review)
────────────────────────────────────────────────
⚠️  {tc_id}: {tc_title}
   Best candidate: {script_path} ({n} hits: [{keywords}])
   LLM assessment: {gap description}
   Recommended: {enhancement action}

NO MATCH (TC has no corresponding script)
──────────────────────────────────────────
❌ {tc_id}: {tc_title}
   Recommended: Create {suggested_path} implementing {intent}
```

---

## Enhancement Classification

Classify each TC's enhancement need into one of these categories:

| Category | Description | Action |
|----------|-------------|--------|
| `SCRIPT_MISSING` | No script implements this TC | Create new script |
| `CMD_MISSING` | TC has no `test_commands` field in HSD | Add command to TC |
| `CMD_WRONG` | TC command references wrong XML/config | Update TC command |
| `COVERAGE_GAP` | Script exists but misses key TC steps | Extend script |
| `DESCRIPTION_MISMATCH` | TC description doesn't match what script does | Update description |
| `NWP_ADAPTATION` | Script is DMR copy, no NWP changes | Port script to NWP |
| `OK` | TC description and script are aligned | No action needed |

---

## NWP-Specific Adaptation Checklist

When a script is identified as a DMR copy, check:

| Item | DMR | NWP |
|------|-----|-----|
| CBB count | `range(4)` | `range(2)` |
| Cores per CBB | 64 | 48 |
| IMH path | `socket.imhs[0]` | `socket.imhs[0]` (same) |
| TPMI path | `cbb.base.tpmi.*` | same |
| SST instance count | varies | 2 CBBs × N modules |
| PkgC6 | Supported | ZBB (must not enter) |

---

## PCT TP Example (16030762939) — Verified Results

TP: `[NWP PM] PCT (Priority Core Turbo)` → 5 TCDs (direct, no TPF) → 28 TCs

| Match | Count |
|-------|-------|
| STRONG | 18 |
| WEAK | 10 |
| NO_MATCH | 0 |

Key findings:
- PSS TCs (16030715xxx) have dedicated `pss/pct/tc_*.py` modules — good 1:1 coverage
- FV TCs (22022422xxx) map to `pct_pmx.py` + `pct_focus.py` — coverage is broad, not TC-specific
- DLCP TCs (16030982xxx) are WEAK — `sst_tf_info_10` and `MADT partition algorithm` not in existing scripts
- PV TCs (16030717xxx) are WEAK — PMSS sweep/discovery/custom-config not covered by standard PCT scripts
- `22022422110: PCT - SST-PP x PCT Basic Checks` → needs `sst_pp_validate.py` + `pct_pmx.py` together, no single script covers the cross-product scenario

Enhancements identified:
1. **16030982833**: DLCP `SST_TF_INFO_10` fuse-to-register — no script reads this register in PCT context → create `pss/pct/tc_16030982833_dlcp_sst_tf_info10.py`
2. **16030982837**: DLCP HP core position + HWP capabilities — `pct_focus.generate_core_list()` partially covers, but HWP cap check missing → extend `pct_focus.py`
3. **16030982844**: Per-SST-instance completeness (NWP 2-CBB) — needs NWP-specific loop `range(2)` → create with `cbb{0,1}` scope
4. **22022422110**: SST-PP × PCT cross-product — needs combined `sst_pp_validate` + `pct_pmx` invocation → create orchestrator TC script
5. **16030768620/621**: TPMI runtime enable/disable + negative — runtime toggle not in static `tc_16030715690` → extend with runtime write + re-read pattern

---

## Saved Artifacts

| File | Description |
|------|-------------|
| `nwp_pm_analysis/tp{tp_id}_{slug}_tcs.json` | Full TC list with descriptions |
| `nwp_pm_analysis/pm_script_index.json` | AST index of all PM scripts |
| `nwp_pm_analysis/tp{tp_id}_{slug}_analysis.json` | TC-to-script alignment results |