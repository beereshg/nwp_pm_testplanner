---
name: nwp-tc-grading
description: >
  Grade any NWP PM test case (TC or TCD) against the 6-dimension rubric used for
  NWP readiness assessment: NWP Delta, Applicable NWP, PSS Environment, Silicon Only,
  Test Content, and OS. Use when a user says "grade this TC", "assess readiness",
  "NWP Grade TC <ID>", or provides a TC/TCD HSD link for NWP adaptation review.
  Returns a filled grading table and posts it as a comment on the HSD TC — no email sent.
---

# NWP TC Grading Skill

> Orchestrating agent: `@nwp_pm_testplanner`
> Repo root: `c:/github/nwp_testplan/`
> Depends on: `nwp-tc-deepanalysis` skill (architecture constants, ZBB table)

---

## When to Use

- User says "grade this TC", "assess NWP readiness", "fill grading table"
- User says **"NWP Grade TC `<HSD_ID>`"** — this is the canonical invocation keyword
- User provides a HSD link (TC, TCD, or TR) and asks for NWP applicability
- User wants to know which environment a test should run in (VP / HSLE / silicon)
- User asks "is this ZBB on NWP?", "what's the NWP delta?", "can this run in Simics?"

## When NOT to Use

- Full TC enrichment (use `nwp-tc-deepanalysis` skill instead)
- Rejection decisions — grading informs but does not replace human judgment
- PSS TR grading (use `nwp-tc-deepanalysis` PSS pipeline)

---

## NWP PM Phoenix Folder Reference

Top-level folder: **`22022534050`** — `Power_Management`
Phoenix: https://hsdes.intel.com/appstore/phoenix/my-items?uFolder=22022534050&v=server.test_plan&family=Newport&family_group=NEWPORT

| TP ID | Title |
|-------|-------|
| `22022420505` | [NWP PM] CBB CCF PM |
| `16030686481` | [NWP PM] P-State / HWP |
| `15019477771` | [NWP PM] RAPL |
| `15019477838` | [NWP PM] PKGC |
| `15019477845` | [NWP PM] Power Control |
| `15019478558` | [NWP PM] C-State |
| `16030762529` | [NWP PM] AIPM |
| `16030762839` | [NWP PM] SST |
| `16030763137` | [NWP PM] Thermal |
| `16030763243` | [NWP PM] Fabric DVFS |
| `16030765561` | [NWP PM] PM Interfaces |
| `16030765631` | [NWP PM] PM Cross Product |
| `16030767511` | [NWP PM] Telemetry |
| `16030785148` | [NWP PM] Platform TCD (442 FV TCs) |

---

## Grading Rubric

The 6-dimension grading table is the standard NWP PM readiness scorecard:

| # | Dimension | Legal Values | Guidance |
|---|-----------|--------------|---------|
| 1 | **NWP Delta** | `Yes` / `No` | Does NWP architecture differ from DMR in a way that affects this TC? |
| 2 | **Applicable NWP** | `Yes` / `No` | Is the feature/register present and non-ZBB on NWP? |
| 3 | **PSS Environment** | `VP` / `VP+HSLE` / `HSLE` / `VP_CONTENT` | Which pre-silicon environment can run this content? |
| 4 | **Silicon Only** | `Yes` / `Partial` | Does full validation require post-silicon? |
| 5 | **Test Content** | `DMR_L` / `DMR_M` / `NWP_N` | Origin and adaptation level of the test content |
| 6 | **OS** | `sv-os` / `linux-os` | Execution environment (SVOS+PythonSV vs OS-level test) |

---

## Dimension Definitions

### 1. NWP Delta — `Yes` / `No`

**Yes** if any of the following differ between DMR and NWP:
- CBB count (DMR=4, NWP=2)
- IMH topology (DMR=2 IMH, NWP=1 NIO)
- Register path (e.g. `imh0/imh1` → `nio`)
- Core count, cluster layout, or MSR loop range
- Feature availability (ZBB, fuse state)
- TPMI MMIO address, FID encoding, die-relative addressing

**No** if the test is purely algorithmic/SW and register paths are identical.

### 2. Applicable NWP — `Yes` / `No`

**Yes** — feature is architecturally present and not ZBB'd on NWP.

**No (reject as ZBB)** for any of these:
| Feature | ZBB Reason |
|---------|-----------|
| PkgC6 | `FUSE_PKG_C_STATE=0` |
| Ring C6 / MC6 | ZBB HSD |
| SST-BF / SST-PP / SST-CP | ZBB HSD 22021155414 |
| HGS | ZBB |
| Platform RAPL / Psys | ZBB |
| RACL | Single-VCCIN — not applicable |
| IO Fabric DVFS | NIO mesh fixed 2 GHz |
| Memory Fabric DVFS | NIO memory mesh fixed 2 GHz |
| ELC Mode | Fabric DVFS ZBB → context not exercised |

**Partial** — feature exists but is constrained (e.g. only C6S/C6A supported, not MC6).

### 3. PSS Environment

| Value | Meaning | Use When |
|-------|---------|---------|
| `VP` | Simics fmod_svos only | Register read/write/structure validation; no counter increment or traffic needed |
| `VP+HSLE` | Simics + emulation | Counter validation, fast C3 residency, CLR PMON increment require traffic model |
| `HSLE` | Emulation only | Full end-to-end timing-dependent behaviors; CCF PMA registers need HSLE model |
| `VP_CONTENT` | VP with special configuration | Content runs in VP but needs extra Simics config (BIOS knobs, fuse override) |

**Decision rules:**
- CCF PMA registers (`ccf_pma.*`) → `VP+HSLE` or `HSLE` (IOSF RSP=2 in fmod_svos)
- PUNIT-path registers (`punit_regs.*`, `punit_pmsb.*`, `gpsb_infvnn_crs.*`) → `VP`
- TPMI registers (`base.tpmi.*`) → `VP` for write/readback; `VP+HSLE` for effect observation
- MSR counter increment (residency, TSC) → `HSLE` or silicon
- Thermal injection, PEGA-driven frequency change → `HSLE` or silicon
- BIOS knob override needed → `VP_CONTENT`

### 4. Silicon Only — `Yes` / `Partial`

| Value | Meaning |
|-------|---------|
| `Yes` | All meaningful validation requires real silicon (timing, voltage, FIVR response, SVID) |
| `Partial` | Structural checks in VP/HSLE; quantitative accuracy requires silicon |

**Lean toward `Partial`** unless the feature literally cannot be modeled in any pre-Si environment (e.g. real power/thermal measurement, analog VR telemetry).

### 5. Test Content

| Value | Meaning |
|-------|---------|
| `DMR_L` | DMR test script, light adaptation needed (CBB count change, register path loop) |
| `DMR_M` | DMR test script, medium adaptation (new register paths, topology-aware logic) |
| `NWP_N` | Net-new content written for NWP (no DMR equivalent or DMR content fundamentally incompatible) |

**Classification guide:**
- Same feature, same registers, only CBB loop → `DMR_L`
- Same feature, IMH→NIO path change, or NWP-specific TPMI → `DMR_M`
- Feature ZBB'd or completely new NWP-only feature → `NWP_N`

### 6. OS

| Value | Meaning |
|-------|---------|
| `sv-os` | Runs under SVOS + PythonSV (FV content, register-level, no OS driver needed) |
| `linux-os` | Runs under Linux with driver stack (PV content, sysfs, kernel drivers, runPmx linux tests) |

**sv-os** is the default for Active PM / CBB CCF / TPMI / PMON / cstate content accessed via namednodes.
**linux-os** for: TPMI sysfs validation, OS-level RAPL power capping, PECI over OS, user-space PMX.

---

## Step-by-Step Grading Workflow

> ⚠️ **MANDATORY**: Grading must be LLM-reasoned per TC. Do NOT use a pre-written matrix.
> Each TC has different content, different command lines, different register paths, and different
> NWP-specific constraints. Grading must reflect evidence from the actual TC description.

### Step 0 — Load NWP constants

Read `nwp-tc-deepanalysis` skill for: ZBB feature table, register path mapping, topology constants, KB articles.

### Step 1 — Fetch TC/TCD content

```python
# Fetch the article with all relevant fields
HSDTool get_article
  tenant: server
  subject: test_case          # or test_case_definition
  id: <hsd_id>
  fields: id,title,description,status,reason,tag,
          test_case.val_environment,test_case.command_line,
          test_case.free_tag_1,test_case.free_tag_2,test_case.free_tag_3,
          test_case.origin_project,test_case.val_framework,parent_id
```

Also fetch comments to see any existing debug data, pre-migration description, or prior analysis.

### Step 2 — Read and extract signals from the actual TC content

**Do not skip this step.** Read the full description text and extract:

| Signal | Where to find it |
|--------|-----------------|
| What the test actually does | description → Validation Scope / Flow section |
| Which script/functions are called | description → Test Steps, or `test_case.free_tag_2` (command line) |
| Which registers are read/written | description → Test Steps code blocks |
| What pass/fail criteria rely on | description → Health Check / Pass/Fail section |
| Feature area | `test_case.free_tag_1`, `test_case.free_tag_3` |
| Environment the TC expects | `test_case.val_environment` |
| Origin project | `test_case.origin_project` |
| ZBB status | check `status=rejected`, `reason=zbb` |

### Step 3 — Reason through each dimension using TC-specific evidence

For **each** dimension, cite specific evidence from the TC content:

| What good reasoning looks like | What bad reasoning looks like |
|-------------------------------|-------------------------------|
| "TC calls `ccf_pmon_clr_disable_test` which accesses `ccf_pma.*` — IOSF RSP=2 in fmod_svos → VP+HSLE" | "CCF features need HSLE" (generic) |
| "Description says verify `fast_c3_residency.counter` increments → counter increment needs HSLE traffic model" | "residency counters need silicon" (no evidence) |
| "Script uses `sweep_pl1_limit` iterating over CBBs — DMR has 4 CBBs, NWP has 2 → CBB loop update needed" | "CBB loop 4→2" (no tie to actual script) |
| "TC description explicitly tests PkgC6 PLL shutdown path which is ZBB (FUSE_PKG_C_STATE=0) on NWP customer silicon" | "Ring C3 needs HSLE" |

### Step 4 — Apply ZBB table (mandatory check before grading Applicable NWP)

From `nwp-tc-deepanalysis` skill ZBB table:
- If TC tests PkgC6 → **Applicable NWP = No (ZBB)**
- If TC tests RACL / dual-VCCIN → **Applicable NWP = No**
- If TC tests IO Fabric DVFS / Memory Fabric DVFS → **Applicable NWP = No (ZBB)**
- If TC tests ELC Mode (requires Fabric DVFS context) → **Applicable NWP = No**
- Partial scope (e.g. Fast Ring C3 = Yes, Ring C3 via PkgC6 = ZBB on silicon but HSLE-only) → **Applicable NWP = Yes (Partial scope)**

### Step 5 — Output the grading table

Always output in this exact format with **TC-specific rationale** in each Summary cell:

```
| Sl no | Description       | Value              | Comments |
|-------|-------------------|--------------------|---------|
| 1     | NWP Delta         | Yes / No           | <rationale> |
| 2     | Applicable NWP    | Yes / No           | <rationale> |
| 3     | PSS Environment   | VP / VP+HSLE / HSLE / VP_CONTENT | <rationale> |
| 4     | Silicon Only      | Yes / Partial      | <rationale> |
| 5     | Test Content      | DMR_L / DMR_M / NWP_N | <rationale> |
| 6     | OS                | sv-os / linux-os   | <rationale> |
```

Then provide a **Summary** (2–4 sentences) covering: what the TC does, key NWP differences, recommended action.

---

## Step 6 — Write Grading Result to Section G of inference.md

Do **not** post to HSD. Write the grading output into the TC's inference.md cache file as
`## Section G: PSS Grading`. This makes it visible as a tab in the deep-analysis HTML.

### Section G format (append to inference.md)

```markdown
## Section G: PSS Grading

### Grading Table

| Sl No | Dimension | Value | Rationale |
|-------|-----------|-------|----------|
| 1 | NWP Delta | Yes / No | <evidence from TC> |
| 2 | Applicable NWP | Yes / No | <ZBB check or feature presence> |
| 3 | PSS Environment | VP / VP+HSLE / HSLE / VP_CONTENT | <register path reasoning> |
| 4 | Silicon Only | Yes / Partial | <timing/analog dependency assessment> |
| 5 | Test Content | DMR_L / DMR_M / NWP_N | <adaptation level> |
| 6 | OS | sv-os / linux-os | <execution stack> |

### Verdict

**{VERDICT_LABEL}** — {2-sentence summary: what the TC does, key NWP constraint, recommended action.}

### Environment Coverage

| Environment | Coverage | Notes |
|-------------|----------|-------|
| Simics VP | Yes/Partial/No | {what can be validated} |
| HSLE | Yes/Partial/No | {what requires emulation} |
| Post-Silicon | Yes/Partial/No | {silicon-only aspects} |

### Key Notes

| Area | Detail |
|------|--------|
| Reuse Level | High / Medium / Low |
| Main Adaptation | {1-line change required} |
| Limitation | {key pre-Si gap} |
| Validation Strategy | {which env covers which sub-test} |
```

### File location

Find the inference.md for the TC and append/replace Section G:

```python
from pathlib import Path, re

KB_ROOT = Path('KB/pm_tc_kb')
matches = list(KB_ROOT.rglob(f'**/*{TC_ID}*.inference.md'))
if matches:
    inf = matches[0]
    text = inf.read_text(encoding='utf-8')
    if '## Section G:' not in text:
        text += '\n\n' + SECTION_G_MARKDOWN
    else:
        text = re.sub(r'## Section G:.*', SECTION_G_MARKDOWN, text, flags=re.DOTALL)
    inf.write_text(text, encoding='utf-8')
    print(f'Written: {inf}')
```

After writing, regenerate HTML — Section G tab appears automatically:

```powershell
python tools/html/generate_unified_html.py --segment fv --hsd <ID> --force
```

---

## Example Grading — CBB CCF PMON (22022421190)

**Input signals:**
- Feature: CBB CCF Ring Frequency Scalability — PMON Telemetry
- Origin: DMR (DIAMOND RAPIDS)
- Script: `pmx_ccf_cbo.py` via `ccf_utils.ccf_pmon_clr_*`
- Val environment: `emulation.sle,silicon`

**Output:**

| Sl no | Description | Value | Comments |
|-------|-------------|-------|---------|
| 1 | NWP Delta | Yes | DMR has 4 CBBs; NWP has 2. Loop over `cbb0`, `cbb1` only. Register paths within each CBB are identical. |
| 2 | Applicable NWP | Yes | CCF PMON telemetry is supported on NWP; CBB PCode reused from DMR; no ZBB flag. |
| 3 | PSS Environment | VP+HSLE | CBO/SBO/CLR PMON register read/write: VP. CCF PMA `fast_c3_residency.counter` increment: requires HSLE (IOSF RSP=2 in fmod_svos). |
| 4 | Silicon Only | Partial | Structural PMON enable/disable: HSLE. Counter accuracy under real traffic + Fast C3 residency count: silicon. |
| 5 | Test Content | DMR_L | DMR script `pmx_ccf_cbo.py` needs minor NWP adaptation: CBB loop range 0–1, no other topology change. |
| 6 | OS | sv-os | PMON accessed via PythonSV namednodes under SVOS. No OS driver or Linux sysfs path. |

---

## Example Grading — ELC Mode (22022422047)

**Input signals:**
- Status: `rejected.zbb`, reason: `zbb`
- Description: RACL/Fabric DVFS context not applicable to NWP single-VCCIN

**Output:**

| Sl no | Description | Value | Comments |
|-------|-------------|-------|---------|
| 1 | NWP Delta | Yes | RACL requires dual-VCCIN (DMR); NWP has single-VCCIN + single NIO |
| 2 | Applicable NWP | No | ZBB. RACL not applicable (single VCCIN). IO/Memory Fabric DVFS ZBB → ELC Mode context not exercised |
| 3 | PSS Environment | N/A | ZBB — no execution path |
| 4 | Silicon Only | N/A | ZBB |
| 5 | Test Content | N/A | ZBB |
| 6 | OS | N/A | ZBB |

---

## Notes

- When `Applicable NWP = No`: mark all remaining fields as `N/A — ZBB` and state the ZBB HSD reference if available.
- When in doubt about PSS environment: err toward `VP+HSLE` rather than `VP` to avoid over-promising silicon coverage.
- For new TCs with `origin_project = DIAMOND RAPIDS`: assume `DMR_L` minimum unless topology analysis shows deeper incompatibility.
- Always cite the NWP architecture source (CBB HAS, NIO HAS, KB article) for non-obvious delta decisions.
