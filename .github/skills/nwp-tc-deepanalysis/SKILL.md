---
name: nwp-tc-deepanalysis
description: >
  Unified NWP TC deep-analysis skill — generates LLM-backed KB markdown files by
  reading TC descriptions, KB feature content, and Co-Design MCP/spec inputs.
  Primary output is markdown under KB/pm_tc_kb for FV/PSS deep-analysis workflows.
---

# NWP TC Deepanalysis Skill

> Orchestrating agent: `@nwp_pm_testplanner`
> Repo root: `c:/github/nwp_testplan/`

Core output contract:
- Generate or update LLM-backed markdown files in `KB/pm_tc_kb/**/HSD_{id}_{slug}.inference.md`
- Build content using TC description + relevant KB article(s) + Co-Design MCP/spec data

---

## Part 0 — Persistent Reference (do not re-fetch unless explicitly stale)

> This section stores authoritative IDs, paths, and state so the agent does not
> need to re-query HSD or re-scan the filesystem on every invocation.
> **Update this section** when TPs are added/removed, TC counts change significantly,
> or grading status updates.

### Phoenix Folder (NWP PM umbrella)

| Item | Value |
|------|-------|
| Folder ID | `22022534050` |
| Folder name | `Power_Management` |
| Phoenix URL | https://hsdes.intel.com/appstore/phoenix/my-items?uFolder=22022534050&v=server.test_plan&family=Newport&family_group=NEWPORT |
| Parent project ID | `22020919772` |
| Workflow | `22011658183` |

### NWP PM Test Plans (15 TPs — last verified 2026-06-17)

| TP ID | Title | Feature Area | Grading Status |
|-------|-------|-------------|----------------|
| `22022420505` | [NWP PM] CBB CCF PM | CCF Active/Idle/NonAutoGV/Ring Freq/PMON | ✅ Graded (2026-06-17) |
| `16030686481` | [NWP PM] P-State / HWP (PNC Core) | Core P-states, HWP, ACP | Pending |
| `15019477771` | [NWP PM] RAPL | Socket RAPL, DRAM RAPL, Fast RAPL, PMAX, SIMPL, SVID | Pending |
| `15019477838` | [NWP PM] PKGC (Package C-State) | PkgC6 ZBB, PKGC infrastructure | Pending |
| `15019477845` | [NWP PM] Power Control (SIMPL/PMAX/SVID) | SIMPL, PMAX, SVID, IccMax | Pending |
| `15019478558` | [NWP PM] C-State (PantherCove PNC) | CC1/C6A/C6S/C6SP/MC6, MSR control | Pending |
| `16030762529` | [NWP PM] Autonomous Idle PM (AIPM) | AIPM, autonomous frequency scaling | Pending |
| `16030762839` | [NWP PM] SST (Speed Select Technology) | SST-TF/PCT (supported); SST-BF/PP/CP/HGS (ZBB) | ✅ Graded (2026-06-17) |
| `16030763137` | [NWP PM] Thermal Management | DTS, EMTTM, ITD, TCC, VR thermal | Pending |
| `16030763243` | [NWP PM] Fabric DVFS (UFS) | CBB CCF ring GV (yes); NIO IO/Mem fabric (ZBB) | Pending |
| `16030765561` | [NWP PM] PM Interfaces (OS2P/TPMI/PECI/PMT) | TPMI, PECI, PMT, OSPL | Pending |
| `16030765631` | [NWP PM] PM Cross Product | Cross-feature interactions | Pending |
| `16030767511` | [NWP PM] Telemetry (PEM/PLR) | PEM, PLR, IMON, power telemetry | Pending |
| `16030785148` | [NWP PM] Platform TCD transformation | FV Platform + PV test cases | Pending |
| `22022561851` | NWP PM Staging - DMR Cloned (Deprecated) | Deprecated staging area | N/A |

### Feature → TP routing (use this before querying HSD)

| User asks about | Walk this TP |
|----------------|-------------|
| CCF ring GV / Fast Ring C3 / Ring C3 / PMON / CCF PM | `22022420505` |
| P-state / HWP / ACP / PEGA P-state | `16030686481` |
| Socket RAPL / DRAM RAPL / Fast RAPL | `15019477771` |
| PMAX / SIMPL / IccMax / SVID | `15019477845` |
| PKGC / Package C-State | `15019477838` |
| Core C-States / CC1 / CC6 / MC6 / C-state MSR | `15019478558` |
| AIPM / Autonomous idle | `16030762529` |
| SST-TF / PCT / SST-BF / SST-PP / SST-CP / HGS | `16030762839` |
| Thermal / DTS / EMTTM / ITD / VR thermal | `16030763137` |
| Fabric DVFS / UFS / Mesh GV / CCF ring freq | `16030763243` |
| TPMI / PECI / PMT / OSPL / PM interfaces | `16030765561` |
| Cross-product PM | `16030765631` |
| PEM / PLR / Telemetry | `16030767511` |
| Platform TC / FV hierarchy / PV test cases | `16030785148` |

### Key TPF IDs (frequently used sub-nodes)

| Artifact | ID | Parent TP |
|----------|----|-----------|
| C-States TPF | `16030703129` | `15019478558` |
| PKGC TPF | `16030703128` | `15019477838` |
| Fabric DVFS TPF | `22022420435` | `16030763243` |
| RAPL TPF (post-split) | `22022562316` | `15019477771` |
| Power & Current Protection TPF | `22022564393` | `15019477845` |
| CBB CCF Active States TPF | `22022420507` | `22022420505` |
| CBB CCF Idle States TPF | `22022420512` | `22022420505` |
| CBB CCF Ring Freq Scalability TPF | `22022420514` | `22022420505` |
| CBB Uniform Fabric Frequency TPF | `22022420515` | `22022420505` |
| SST TPF (SST-TF) | _(walk `16030762839`)_ | `16030762839` |

### Pipeline Coverage (last updated 2026-06-17)

| Segment | HTML files | Cache files | TC scope |
|---------|-----------|-------------|---------|
| FV | 313 | 0 (cache cleared) | 844 TCs (nwp_pm_fv_cache.json) |
| PSS | 64 | 0 (cache cleared) | 62 TRs (nwp_master_test_plan.csv) |

**Key files:**
- FV content: `nwp_pm_fv/data/nwp_pm_fv_content.json` (442 FV + PV TCs)
- FV cache: `nwp_pm_fv_cache.json` (844 total TCs from full TP walk)
- PSS master: `nwp_pm_pss/data/nwp_master_test_plan.csv`
- Unified HTML out: `tc_description_output/` (all generated files)
- Hierarchy HTML: `nwp_pm_hierarchy.html` (full interactive view)

### Graded TPs (TC grading comments posted to HSD)

| TP | TCs graded | Date | Comment IDs (first/last) |
|----|-----------|------|--------------------------|
| `22022420505` CBB CCF PM | 15 | 2026-06-17 | 1667580755 – 1667580775 |
| `16030762839` SST | 40 | 2026-06-17 | 1667580954 – 1667580996 |

---

## Part 0A — KB Flywheel (Operating Loop)

The KB files in this repo are the **first-touch knowledge layer**. Every enrichment session
follows this loop — do not skip steps:

```
┌─────────────────────────────────────────────────────────────────┐
│  1. READ KB FIRST                                               │
│     KB/pm_features/{feature}/*.md                              │
│     KB/pm_tc_kb/**/*.inference.md                              │
│     KB/pm_tcd_kb/**/*.md                                       │
│     → Quick context: architecture, NWP delta, register paths,  │
│       prior enrichment, known open items                        │
└────────────────┬────────────────────────────────────────────────┘
                 │ gaps or stale sections found
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. TOUCH MCP / HAS FOR DEPTH                                  │
│     codesign-ask-specs-and-wikis  (HAS/MAS/wikis)              │
│     fetch_webpage  (direct HAS URL crawl)                       │
│     HSDTool  (HSD article fetch)                               │
│     → Resolve gaps, confirm register fields, get exact values   │
└────────────────┬────────────────────────────────────────────────┘
                 │ new learnings from MCP / HAS
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. PRODUCE OUTPUT (inference.md / TCD HTML / HSD description) │
│     → Synthesize KB context + MCP depth + prompt intent        │
│     → Better result than MCP-only because KB pre-loads NWP     │
│       topology, ZBB table, and prior session findings           │
└────────────────┬────────────────────────────────────────────────┘
                 │ new learnings discovered during output
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. WRITE LEARNINGS BACK TO KB (mandatory)                     │
│     KB/pm_features/{feature}/*.md  ← feature-level facts       │
│     KB/pm_tcd_kb/**/*.md           ← TCD-level context         │
│     KB/pm_tc_kb/**/*.inference.md  ← TC-level analysis         │
│                                                                 │
│     Rules:                                                      │
│     - Always include the doc/HSD/spec reference link           │
│     - Tag the update with date: "Updated: YYYY-MM-DD"           │
│     - Only write verified facts; mark uncertain items as ⚠     │
│     - Next session starts from this richer KB → better output  │
└─────────────────────────────────────────────────────────────────┘
```

### What goes where

| Learning type | KB target | Example |
|--------------|-----------|---------|
| Feature architecture, fuses, frequency hierarchy | `KB/pm_features/{feature}/*.md` | PCT frequency hierarchy table from PCT HAS |
| DMR vs NWP delta, BIOS knobs, DQ rules | `KB/pm_features/{feature}/*.md` | DMR vs GNR CAPID4/default differences |
| TCD context: what scenario is tested, section content | `KB/pm_tcd_kb/{tp_slug}/TCD_{id}_{slug}.md` | Enabling & Discovery scope, MADT ordering requirement |
| Per-TC NWP analysis, register paths, PythonSV code | `KB/pm_tc_kb/{fv\|pss}/HSD_{id}_{slug}.inference.md` | NWP CLOS loop bounds, nio.punit path |

### KB write rule

After **any** enrichment where MCP or HAS provides a fact not already in KB:

```python
# Append to the relevant KB file
kb_file = Path('KB/pm_features/sst/pct.md')
text = kb_file.read_text(encoding='utf-8')
if 'fact-anchor-string' not in text:
    text += '\n\n## New Section (YYYY-MM-DD)\n\n...<learned content with [Source](url)>...'
    kb_file.write_text(text, encoding='utf-8')
```

Commit KB updates together with the enrichment output so the repo always reflects current knowledge.

---

## Part 1 — Quality Guardrails

1. **Reference hygiene**: only include HAS/MAS/HSD/spec links actually cited in the body. No speculative references.
2. **Read/preview before write**: for any HSD create/update/move, do discovery/read-back first, then execute.
3. **Mandatory section policy**: fill all required TC/TCD sections or explicitly mark `N/A`/`Not Applicable`.
4. **No-email write policy**: all automation is silent (no watcher notification).
5. **Payload compatibility**: attempt write with `{"send_mail": "false"}` in `fieldValues`; if HTTP 400, retry without `send_mail`, then read-back verify.
6. **Rendering boundary**: generate/update `cache/*.inference.md` first; render HTML only via official scripts — never hand-write HTML.
7. **TC content discipline**: remove instructional/template boilerplate from final TC output; mandatory sections must be filled.
8. **Toolkit-first execution**: prefer `hsd_utils` reusable modules for fetch/traverse/compare/update operations; do not create new one-off root scripts for repeat jobs.
9. **ID validation before write**: treat TP/TPF/TCD/TC IDs in this file as examples; always read-back and confirm parent chain before any mutation.
10. **Description preservation on overwrite**: before replacing a TC description with LLM-backed/template-updated content, you MUST back up the existing description as a visible HSD comment first. Use the `subject="comments"` POST pattern below (NOT `test_case.notes`, NOT `/rest/article/{id}/comment` — both are wrong). This is mandatory for the first time a TC description is changed; skip only if the description is empty/placeholder.

    ```python
    # Step A — read existing description
    r = S.get(f"{BASE}/article/{tc_id}?fields=description")
    orig_desc = r.json()["data"][0]["description"]  # may be empty

    # Step B — post as comment (only if orig_desc is non-empty)
    if orig_desc and orig_desc.strip():
        cmt_payload = {
            "subject": "comments",        # MUST be plural — 'comment' returns 400
            "tenant": "server",
            "fieldValues": [
                {"parent_id": str(tc_id)}, # MUST be inside fieldValues, NOT top-level
                {"description": "<p><strong>[Original description preserved before template update]</strong></p>" + orig_desc},
                {"send_mail": "false"}
            ]
        }
        cmt_r = S.post(f"{BASE}/article/", json=cmt_payload)
        assert cmt_r.status_code == 200, f"Comment backup failed: {cmt_r.text}"
        comment_id = cmt_r.json().get("new_id")
        # comment_id is now a child article of tc_id, visible in HSD Comments tab

    # Step C — now overwrite description with new template content
    # (only after comment backup is confirmed)
    ```

    **Verified pitfalls** (from session 2026-07-02):
    - `/rest/article/{id}/comment` → 404 (wrong path)
    - `/rest/comment/{id}` → 404 (wrong path)
    - `test_case.notes` field → saves in Notes section, NOT the Comments tab
    - `forum` / `community` / `notes` as fieldValues keys → "NOT a valid field" error
    - `article_comment` endpoint → 200 with empty body, silently no-ops
    - `parent_id` at top JSON level → HTTP 400

### Post-Cleanup Operating Model (2026-06)

- Canonical reusable API: `hsd_utils/session.py`, `hsd_utils/queries.py`, `hsd_utils/operations.py`, `hsd_utils/hierarchy.py`, `hsd_utils/batch_ops.py`
- Preferred pattern:
  1. Read via toolkit helpers (`get_article`, `get_children`, `walk_hierarchy`, `fetch_batch`, `traverse_hierarchy`)
  2. Analyze/plan changes from in-memory data
  3. Apply mutations via `set_field`, `move_tcd`, `set_owner`, `set_planning_fields`
  4. Read-back verify and log traceability note
- Deprecated pattern: creating throwaway `move_*`, `set_*`, `retheme_*`, `verify_*` scripts at repo root.

### Primary Repo Workstreams

This repo is primarily used for three kinds of work. Optimize agent behavior around these instead of treating all tasks as generic HSD automation.

1. **TC Description Modernization**
  - Update HSD test-case descriptions using LLM-backed content plus the current repo template structure.
  - **Mandatory backup-first procedure** (for first-time description replacement on a TC with existing content):
    1. `GET /rest/article/{tc_id}?fields=description` — read the current description.
    2. If non-empty: `POST /rest/article/` with `subject="comments"`, `parent_id` in `fieldValues`, and the original description as the comment body. Verify HTTP 200 and record `new_id`.
    3. Only then: `PUT /rest/article/{tc_id}` with the new template description.
    4. Read-back verify the new description is live.
  - **Reference format**: use the same HTML structure as TC [22022421939](https://hsdes.intel.com/appstore/article-one/#/22022421939) — `Validation Scope`, `Preconditions` (table), `Test Steps` (table with #/Action/Expected), `Health Check - Registers and Logs`, `Post-Process`, `HAS Reference`. Section headers use `background:#cce4f7;color:#004a80;border-left:4px solid #0071c5`.
  - Preferred inputs: neighboring cache exemplars, KB feature docs, current HSD metadata, and any approved generated HTML preview.

2. **Per-TC Deep Analysis for NWP Readiness**
  - Build or refine per-TC analysis of how a DMR-origin test maps to NWP, including micro-architectural deltas, interface changes, disposition, and runnable adaptations.
  - Primary working corpus: `KB/pm_tc_kb/**/*.inference.md` and corresponding unified HTML output.

3. **PSS-Specific Test Case Reporting**
  - Generate or refine PSS-specific reporting, summaries, and deep-analysis output under `nwp_pm_pss/`.
  - This includes TR→TC→TCD→TP hierarchy reasoning, PSS HTML generation, and reporting-friendly presentation for NWP PM readiness.

---

## Part 2 — NWP Architecture Constants

### Topology
- **CBBs**: 2 (die 0–1) — DMR has 4
- **NIO**: 1 (die 8) — derived from IMH2
- **Cores**: 96 total (48 per CBB, 24 DCMs × 2 PNC cores)
- **Core uarch**: PantherCove (PNC)
- **SMT**: None

### Register Path Convention
| DMR Path | NWP Path |
|----------|----------|
| `sv.socket0.imh0.punit.*` | `sv.socket0.nio.punit.*` — register names and fields identical to DMR; path prefix swap only |
| `sv.socket0.imh1.*` | N/A (single NIO) |
| `sv.socket0.cbb[0-3].*` | `sv.socket0.cbb[0-1].*` |

### ZBB Features (always disposition = Skip)
| Feature | Reason |
|---------|--------|
| PkgC6 | `FUSE_PKG_C_STATE=0` |
| Ring C6 / MC6 | ZBB |
| SST-BF / SST-PP / SST-CP | ZBB |
| HGS | ZBB |
| Platform RAPL / Psys | ZBB |
| RACL | Single NIO + single VCCIN |
| SSR / APD / PPD / LPM | No Memory PM (`HSD 22021155412`) |
| PCIe L1 | No PCIe L1 (`HSD 22021155368`) |
| IO / Memory Fabric DVFS | NIO mesh fixed at 2 GHz (`HSD 14024876702`) |

### Key HSD IDs
| Artifact | ID |
|----------|----|
| NWP PM Test Plan (TP) | `16030686481` |
| C-States TPF | `16030703129` |
| PKGC TPF | `16030703128` |
| Fabric DVFS TPF | `22022420435` |
| RAPL TPF | `22022562316` |
| Power & Current Protection TPF | `22022564393` |

---

## Part 2A — NWP PM Phoenix Hierarchy (Test Plan Folder Map)

> Phoenix link: https://hsdes.intel.com/appstore/phoenix/my-items?uFolder=22022534050&v=server.test_plan&family=Newport&family_group=NEWPORT

**Top-level folder:** `22022534050` — `Power_Management` (NWP PM umbrella)

### Child Test Plans (15 TPs under 22022534050)

| TP ID | Title | Feature Area |
|-------|-------|-------------|
| `22022420505` | [NWP PM] CBB CCF PM | CBB CCF Active/Idle/NonAutoGV/Ring Freq/Uniform Fabric |
| `16030686481` | [NWP PM] P-State / HWP (PNC Core) | Core P-states, HWP, ACP |
| `15019477771` | [NWP PM] RAPL (Running Average Power Limit) | Socket RAPL, DRAM RAPL, Fast RAPL, PMAX, SIMPL, SVID |
| `15019477838` | [NWP PM] PKGC (Package C-State) | PkgC6 ZBB on NWP, PKGC infrastructure |
| `15019477845` | [NWP PM] Power Control (SIMPL/PMAX/SVID) | SIMPL, PMAX, SVID, IccMax |
| `15019478558` | [NWP PM] C-State (PantherCove PNC) | CC1, CC1e, CC6A/S/SP, MC6, C-state MSR control |
| `16030762529` | [NWP PM] Autonomous Idle PM (AIPM) | AIPM, autonomous frequency scaling |
| `16030762839` | [NWP PM] SST (Speed Select Technology) | SST-TF, PCT (supported); SST-BF/PP/CP/HGS (ZBB) |
| `16030763137` | [NWP PM] Thermal Management | DTS, EMTTM, ITD, TCC, VR thermal |
| `16030763243` | [NWP PM] Fabric DVFS (UFS) | CBB CCF ring GV (supported); NIO IO/Mem fabric (ZBB) |
| `16030765561` | [NWP PM] PM Interfaces (OS2P/TPMI/PECI/PMT) | TPMI, PECI, PMT, OSPL |
| `16030765631` | [NWP PM] PM Cross Product | Cross-feature interactions |
| `16030767511` | [NWP PM] Telemetry (PEM/PLR) | PEM, PLR, IMON, power telemetry |
| `16030785148` | [NWP PM] Platform TCD transformation | Platform-level / PV test cases (442 FV TCs) |
| `22022561851` | NWP PM Staging - DMR Cloned Features (Deprecated) | Deprecated staging area |

### How to walk the hierarchy programmatically

```python
from hsd_utils import get_session, get_children, walk_hierarchy

s = get_session()
FOLDER = "22022534050"

# Get all TPs under the NWP PM folder
tps = get_children(s, FOLDER, child_subject="test_plan",
                   fields="id,title,status")

# Walk a single TP fully (TP → TPF → TCD → TC)
root_info, hierarchy, tc_stats = walk_hierarchy(
    tp_id="16030762839",   # SST TP
    skip_ids=[]
)
```

### Feature → TP mapping (for grading and enrichment routing)

| Feature | TP to walk |
|---------|-----------|
| Socket RAPL / DRAM RAPL / PMAX / SVID / SIMPL | `15019477771` or `15019477845` |
| Core C-States (C1/C6A/C6S/C6SP/MC6) | `15019478558` |
| CCF Ring GV / Fast Ring C3 / PMON | `22022420505` |
| SST-TF / PCT | `16030762839` |
| Fabric DVFS (CBB CCF supported; NIO ZBB) | `16030763243` |
| Thermal / EMTTM / DTS | `16030763137` |
| TPMI / PECI / PMT | `16030765561` |
| PEM / PLR / Telemetry | `16030767511` |
| P-State / HWP / ACP | `16030686481` |
| Platform / PV TCs | `16030785148` |

---

## Part 3 — HSD Access Model (Toolkit-first, REST fallback)

### Preferred Entry Points

```python
from hsd_utils import (
  get_session,
  get_article, get_children, query_driven,
  set_field, set_owner, move_tcd, set_planning_fields,
  walk_hierarchy,
  fetch_batch, traverse_hierarchy, compare_tps, analyze_batch, filter_batch, status_report,
)
```

- Use direct REST only when toolkit coverage is missing.
- When adding reusable behavior, extend `hsd_utils/*` instead of introducing ad-hoc root scripts.

## Part 3A — HSD REST API (fallback)

### Auth and Session

> Prerequisite: `kinit <idsid>@AMR.CORP.INTEL.COM`

```python
import requests, urllib3, time, json
from requests_kerberos import HTTPKerberosAuth, OPTIONAL
urllib3.disable_warnings()

BASE = "https://hsdes-api.intel.com/rest"
TENANT = "server"

S = requests.Session()
S.auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL)
S.verify = False
```

**Fresh-session variant** (long-running loops — avoids SSL reset after ~100 calls):
```python
def fresh_req(method, url, retries=5, **kwargs):
    for attempt in range(1, retries + 1):
        try:
            s = requests.Session()
            s.auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL)
            s.verify = False
            resp = getattr(s, method)(url,
                headers={"Content-Type": "application/json", "Accept": "application/json",
                         "Connection": "close"},
                timeout=30, **kwargs)
            s.close()
            return resp
        except Exception as e:
            print(f"  [retry {attempt}/{retries}] {type(e).__name__}")
            time.sleep(3 * attempt)
    return None
```

**Rate-limit rule**: `time.sleep(0.1)` between GETs; `time.sleep(1)` after creates/PUTs.

## HSD Hierarchy
[](https://github.com/intel-sandbox/PRISM-feature-validation-plan-suite/blob/master/skill/SKILL.md#hsd-hierarchy)

```
Test Plan (TP)                        ← fvps tp create
  └── Test Plan Feature (TPF)         ← fvps tpf create / fvps tpf create-batch
    └── Test Case Definition (TCD) ← fvps tcd publish
      └── Test Case (TC)       ← fvps tc publish
```

All use `server.test_plan` / `server.test_case_definition` / `server.test_case`:

- **TP**: `server.test_plan` with `nodetype = "plan"` — top-level container
- **TPF**: `server.test_plan` with `nodetype = "feature"` — feature node under TP
- **TCD**: `server.test_case_definition` — test case detail under TPF
- **TC**: `server.test_case` — individual test case under TCD

### Hierarchy and Subject Names

```
Test Plan (TP)       subject = "test_plan"              NWP PM TP: 16030686481
  └── TPF            subject = "test_plan"              ← same subject as TP!
        └── TCD      subject = "test_case_definition"
              └── TC  subject = "test_case"
                    └── TR  subject = "test_result"     ← PSS primary record
```

> ID safety: confirm current TP/TPF/TCD mapping via `get_article()` + `parent_id` chain before write operations.

| Parent | `child_subject` |
|--------|----------------|
| TP | `"test_plan"` — NOT `"test_plan_folder"` |
| TPF | `"test_case_definition"` |
| TCD | `"test_case"` |
| TC | `"test_result"` |

### Read Operations

```python
# Single article
r = S.get(f"{BASE}/article/{ID}", params={"tenant": TENANT,
    "fields": "id,title,status,description,owner,parent_id"})
article = r.json()["data"][0]

# Children (one level)
r = S.get(f"{BASE}/article/{PARENT_ID}/children",
    params={"tenant": TENANT, "child_subject": "test_case_definition",
            "fields": "id,title,status,owner", "max_results": 500})
children = r.json()["data"]
```

Toolkit equivalents:

```python
article = get_article(ID, fields="id,title,status,description,owner,parent_id")
children = get_children(PARENT_ID, "test_case_definition", fields="id,title,status,owner", max_results=500)
```

**HSDTool MCP** (preferred for single fetch or EQL search):
```
HSDTool get_article  tenant:server  subject:test_case  id:<id>
  fields: id,title,description_text,status,priority,owner,feature_tag,tag,val_environment

HSDTool query  tenant:server  subject:test_case
  eql: feature_tag LIKE '%rapl%' AND status IN ('open','active')
```

### Write Operations

```python
# Reject a TC — fieldValues order is MANDATORY: status first, reason second
def reject_tc(tc_id, reason_code="zbb"):
    payload = {"tenant": TENANT, "subject": "test_case",
               "fieldValues": [{"status": "rejected"}, {"reason": reason_code},
                                {"send_mail": "false"}]}
    r = S.put(f"{BASE}/article/{tc_id}", json=payload)
    return r.status_code == 200
# If HTTP 400 → retry without send_mail

# Update any field
def update_article(article_id, subject, field_dict):
    payload = {"tenant": TENANT, "subject": subject,
               "fieldValues": [{k: v} for k, v in field_dict.items()] + [{"send_mail": "false"}]}
    r = S.put(f"{BASE}/article/{article_id}", json=payload)
    return r.status_code == 200

# Create TPF
r = S.post(f"{BASE}/article/", json={"tenant": TENANT, "subject": "test_plan",
    "fieldValues": [{"title": "Feature Area"}, {"description": "<p>...</p>"},
                    {"parent_id": "16030686481"}, {"send_mail": "false"}]})
new_id = r.json().get("new_id") or r.json().get("id")   # try new_id → id → data[0].id

# Move TCD between TPFs
def move_tcd(tcd_id, new_tpf_id):
    payload = {"tenant": TENANT, "subject": "test_case_definition",
               "fieldValues": [{"parent_id": str(new_tpf_id)}, {"send_mail": "false"}]}
    return S.put(f"{BASE}/article/{tcd_id}", json=payload).status_code == 200

# Post comment  — POST uses "comments" (plural), GET uses "comment" (singular)
r = S.post(f"{BASE}/article/", json={"tenant": TENANT, "subject": "comments",
    "fieldValues": [{"description": "<p>snapshot</p>"}, {"parent_id": tc_id},
                    {"send_mail": "false"}]})
```

Toolkit equivalents:

```python
# update single field
code = set_field(article_id, subject="test_case", field="status", value="rejected")

# move TCD
code = move_tcd(tcd_id, new_tpf_id)

# owner updates
code = set_owner(article_id, owner="bg3", subject="test_case")

# planning fields quirk handled internally
ok = set_planning_fields(tc_id, planning_status="Open", drive_to_date="2026-12-31")
```

### Common Pitfalls

| # | Pitfall | Fix |
|---|---------|-----|
| 1 | SSL reset in long loops | Use `fresh_req()` |
| 2 | `send_mail="false"` → HTTP 400 | Retry without `send_mail`, then read-back verify |
| 3 | Wrong `child_subject` | Returns empty `data:[]` silently — check hierarchy table |
| 4 | TC reject field order | `status` first, `reason` second in `fieldValues` |
| 5 | New article ID | Try `new_id` → `id` → `data[0].id` |
| 6 | TPF vs TP subject | Same subject — distinguish by `parent_id` |
| 7 | Comment create/read plural/singular | POST `"comments"`, GET `"comment"` |

**Traceability**: embed `[val_agent] {action} — {date}` in all automated writes.

---

## Part 4 — Pipeline File Paths

| Artifact | FV | PSS |
|----------|----|-----|
| Master list | `nwp_pm_fv/data/nwp_pm_fv_content.json` | `nwp_pm_pss/data/nwp_master_test_plan.csv` |
| Metadata JSON | `nwp_pm_fv/data/metadata/HSD_{id}_metadata.json` | `nwp_pm_pss/data/metadata/HSD_{id}_metadata.json` |
| Cache file | `KB/pm_tc_kb/fv/HSD_{id}_{slug}.inference.md` | `KB/pm_tc_kb/pss/HSD_{id}_{slug}.inference.md` |
| HTML output | `tc_description_output/HSD_{id}_{slug}.html` | `tc_description_output/HSD_{id}_{slug}.html` |
| HTML generator | `tools/html/generate_unified_html.py --segment fv|pss|all` | `tools/html/generate_unified_html.py --segment fv|pss|all` |
| Index pages | `tc_description_output/nwp_pm_fv_test_cases.html` | `tc_description_output/nwp_pss_test_cases.html` |

### Practical Interpretation of These Paths

- `KB/pm_tc_kb/fv/`: FV inference files (423 files). `KB/pm_tc_kb/pss/`: PSS inference files (73 files). Flat structure — no feature subfolders.
- `tc_description_output/`: rendered unified presentation output for FV and PSS.
- `nwp_pm_pss/`: PSS-specific source inputs and reporting metadata (master CSV, metadata chain), not the final HTML destination.

> Slug: title lowercased, spaces/special chars → `_`, ~50 chars max.

### HSD Metadata Fields

**FV** (`server.test_case`): `id, title, description_text, status, priority, owner, updated_date, feature_tag, tag, val_environment, command_line, automation, pre_condition_text`

**PSS** — fetch chain TR → TC → TCD → TP via `parent_id`:
1. TR (`server.test_result`): `id, title, description, status, owner, parent_id, tag`
2. TC (`server.test_case`): `id, title, description, status, priority, owner, parent_id, val_environment, val_framework`
3. TCD (`server.test_case_definition`): `id, title, description, parent_id`
4. TP (`server.test_plan`): `id, title`

### HTML Generation Commands

```powershell
cd c:/github/nwp_testplan
python tools/html/generate_unified_html.py --segment fv --hsd <ID> --force
python tools/html/generate_unified_html.py --segment pss --hsd <ID> --force
python tools/html/generate_unified_html.py --segment all --force
python tools/html/generate_unified_html.py --status
```

---

## Part 5 — Enrichment Sections (A–F)

---

## Part 4A — TCD Section Content Requirements

When writing or reviewing a **TCD description**, each numbered section must meet the following
content bar. This applies to all NWP PM TCDs — the example column is scoped to PCT Enabling & Discovery.

| Section | What Must Be Included | PCT Enabling & Discovery Example |
|---------|----------------------|----------------------------------|
| **1. Architecture / Micro-arch and Functionality** | Block diagram or logical decomposition; major functions/scenarios; key blocks in pipeline; interfaces to other blocks/FSMs; external dependencies | PCT purpose (GPU-serving HP cores), frequency hierarchy (P0max/P0half/P0n/F2/F3), DMR vs GNR differences (CAPID4 not used, default disabled), DLCP concept, cross-product rules (PCT+SST-BF mutex) |
| **2. Interfaces and Protocols** | Inputs/outputs described; signal/interface names consistent; timing, ordering, handshake assumptions; legal and illegal transactions; side effects; backpressure/retries/timeouts | Discovery registers table: SST_HEADER.CAPABILITY_MASK, SST_TF_INFO_0/2/10, SST_CLOS_ASSOC, SST_CP_CONTROL, MSR 0x771, MSR 0x1AD, PctHpModuleCount; TPMI access protocol |
| **3. Reset, Power, Clocking** | Reset sources/domains; default/reset values; retention vs non-retention; power state behavior; clock deps; init/bring-up sequence; bring-down/recovery | PCT CLOS state not retained across reset; PrimeCode re-reads SST_TF fuses at Phase 5 on every boot; BIOS must reprogram CLOS/ASSOC/MSR 0x1AD after each boot |
| **4. Programming Model** | Relevant registers with meaning, reset value, access type; legal encodings; reserved values; R/W side effects; locking/privilege/security; FW/SW sequencing requirements | Enabling path step-by-step: PrimeCode Phase 5 init → BIOS CPL3 CLOS programming → MSR 0x1AD override; BIOS knobs (PCT HP Partition Count, PCT Core Selection); MADT ordering requirement |
| **5. Operational Behavior** | Normal flow step-by-step; state machine/mode transitions; entry/exit conditions; performance/latency expectations | BIOS enables PCT before OS handoff; PCode runs standard SST-TF flow (no PCT-specific Pcode); runtime: OS/VMM affinitizes workloads to HP cores; Intel SST tool can reconfigure at runtime |
| **6. Corner Cases & Error Handling** | Invalid inputs; unsupported combinations; error detection; error reporting/logging/status visibility; recovery/retry; undefined behavior | PCT Partition Count = 0 (disabled — fallback to conventional turbo); uneven core count (surplus PCT cores become LP); DLCP SKU with CLOS_ASSOC ignored; mutex violation (SST-BF + PCT) |
| **7. Security / Safety / Policy** | Security assumptions; access control/lock/privilege; sensitive/safety-relevant states; abuse/misuse scenarios; safety/reliability constraints | TPMI lock bit prevents OS from overriding CLOS post-CPL3; PCT is SoC-wide (cannot be per-VM at register level); DLCP HP positions are fuse-fixed (cannot be SW-selected on DLCP SKUs) |
| **8. References** | All cited HAS/MAS/spec/HSD links with scope annotation | PCT HAS, PCT White Paper, DMR Turbo HAS, CPUPM BIOS Knobs, NWP PM MAS, CCB HSD 14026595435, HSD 14025997048 |

**Quality bar:**
- Section 1 must not be generic ("validate X on NWP") — it must describe what the feature IS and what specific scenario is being tested
- Section 2 must list concrete register/interface names, not just "see HAS"
- Section 4 must include the boot-time register programming sequence in order
- All HAS/spec citations in Section 8 must match content actually used in the body

**TCD scope discipline:** A TCD titled "Enabling & Discovery" covers:
- **Enabling**: verifying the BIOS activation path programs the correct CLOS/ASSOC/CP registers, and MSR 0x1AD reflects the HP TRL
- **Discovery**: verifying OS/SW can read SST_HEADER.CAPABILITY_MASK, SST_TF_INFO_0/2/10, SST_CLOS_ASSOC, HWP MSR to discover PCT HP/LP assignment

It does **not** cover: frequency accuracy validation, RAPL+PCT ordered throttling, DLCP module mask correctness under load — those belong in separate TCDs.

### Section B: Swimlane/Sequence (MANDATORY format)

The unified HTML generator parses Section B by heading — wrong headings = plain text fallback.

```markdown
## Section B: Interactions

### Swimlane Data
| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1    | BIOS  | Program CSR PKG_RAPL_LIMIT | [CSR] |

### Sequence Data
| # | From | To | Message | Interface |
|---|------|----|---------|-----------|
| 1 | BIOS | PrimeCode | CSR PKG_RAPL_LIMIT | [CSR] |
```

**Accepted swimlane headings**: `Swimlane Data`, `Swimlane Diagram`, `Swimlane`, `Execution Flow`, `Critical Execution Path`
**Accepted sequence headings**: `Sequence Data`, `Sequence Diagram`, `Component Interaction`, `IP-to-IP Interactions`

**Swimlane actors**: OS/Test, BIOS, PrimeCode (NIO), PCode (CBB×2), VR (SVID), HW
**Interface labels**: `[CSR]`, `[TPMI MMIO]`, `[HPM]`, `[SVID]`, `[PMSB CRWR]`, `[HW wire]`, `[Internal]`, `[Test logic]`

### Disposition Decision Tree (Step D)
```
1. TC tests a ZBB feature → Skip
2. TC cross-products ZBB with supported feature → Skip
3. TC needs DMR-specific script with no NWP equivalent → Needs_Adaptation
4. TC uses runPmx.py/flexconPM.py with only config change → Runnable_On_N-1
5. TC tests register identical on NWP → Runnable_As-Is
6. Insufficient info → TBD
```

### Section Labels
| Section | FV Label | PSS Label |
|---------|----------|-----------|
| A | A: NWP Delta | A: Execution Path |
| B | B: Interactions | B: Interactions |
| C | C: Coverage | C: Coverage |
| D | D: Spec Refs | D: Spec Refs |
| E | E: Risk Assessment | E: Risk |
| F | F: Recommendations | F: Recommendations |

---

## Part 6 — KB Article Enrichment

### Feature → KB File Mapping
| Feature | KB Path |
|---------|---------|
| Socket RAPL / Power/RAPL | `KB/pm_features/power_rapl/socket_rapl.md` |
| PMAX / PL4 | `KB/pm_features/power_rapl/pmax.md` |
| SIMPL / IccMax | `KB/pm_features/power_rapl/simpl.md` |
| SVID | `KB/pm_features/power_rapl/svid.md` |
| Memory Thermal | `KB/pm_features/power_rapl/memory_pm.md` |
| SoC Thermal | `KB/pm_features/soc_thermal/soc_thermal_main.md` |
| Core C-States | `KB/pm_features/core_c_states/core_c_states_main.md` |
| Pstate Stack | `KB/pm_features/pstate_stack/pstate_stack_main.md` |
| SST | `KB/pm_features/sst/sst_main.md` |
| Fabric DVFS | `KB/pm_features/fabric_dvfs/fabric_dvfs_main.md` |
| Platform PM Interface / TPMI | `KB/pm_features/platform_pm_interface/tpmi_infrastructure.md` |
| OSPL | `KB/pm_features/ospl/ospl_main.md` |
| PM Cross Products | `KB/pm_features/pm_cross_products/pm_cross_products_main.md` |

**SoC Thermal sub-file by title keyword**:
`dts/temperature reporting` → `cbb_dts_telemetry.md` / `imh_dts_telemetry.md` | `emttm` → `emttm.md` | `prochot` → `prochot.md` | `itd` → `itd.md` | `thermtrip` → `thermtrip.md` | `vr_hot` → `vr.md`

### Target KB Article Structure
After enrichment, each KB article should have:
1. `## Baseline (DMR)` — what, topology, key mechanism, boot phase (≤500 words)
2. `## HW Touchpoints` — table: IP Block | Die | Role | Key Signals | HAS Reference
3. `## FW Touchpoints` — table: Agent | Location | Role | Key Functions | Source
4. `## OS Interfaces` — table: Interface | ID/Address | Access | Description | Spec Reference
5. `## KPI & Timing` — table: Parameter | Value | Units | Condition | Source
6. `## NWP Delta` — what changes vs DMR
7. `## Legacy (Human-Curated Reference)` — all original sections preserved verbatim as H3

### MCP Enrichment Queries
```
# HW touchpoints
codesign-ask-specs-and-wikis: "What hardware IP blocks are involved in {FEATURE} on DMR?
  List each with: die location, role, key signals, inter-die connections."

# FW touchpoints
codesign-ask-specs-and-wikis: "What firmware agents implement {FEATURE} on DMR?
  Include PCode, PrimeCode, Acode, BIOS. Key functions and HPM/sideband messages."

# OS interfaces
codesign-ask-specs-and-wikis: "What OS-visible interfaces expose {FEATURE} on DMR?
  MSRs, TPMI opcodes, CPUID leaves, ACPI objects, PECI commands."

# NWP delta
codesign-ask-specs-and-wikis: "What changes for {FEATURE} on Newport vs DMR?
  Topology differences, register path changes, ZBB differences."
```

**Local HAS file check first**: before MCP queries, check `KB/pm_features/PNC PM HAS 0.5_text.txt` for core-level PM features (C-states, DTS, THERM_STATUS, budget negotiation).

---

## Part 7 — Cache File Format

### Template Usage Contract (mandatory)

Use templates with strict separation of scope:

1. `KB/tc_hsd_description.html.j2`
  - Use this template only to generate or refresh the **TC description section** content.
  - This is the template for HSD-facing description shaping.

2. `KB/templates/deep_analysis.html.j2`
  - Keep using this template for the **overall deep-analysis rendering**.
  - Do not replace this with the TC description template.

Before rendering either template, ensure all required data fields are present in `KB/**/*.md` sources (especially `KB/pm_tc_kb/**/*.inference.md`).

Required data completeness checks for KB markdown:

- Metadata present: HSD ID, title, feature, sub-feature, date/version
- Intent section present: purpose and scope of the TC
- Steps section present: pre-conditions, execution steps, pass/fail criteria
- Deep-analysis sections present: Section A through Section F (Section E when applicable)
- Interaction tables present for Section B: Swimlane Data and Sequence Data headings/tables
- References present: valid KB/HSD/spec citations used by the generated content

If required fields are missing, enrich `KB/**/*.md` first, then render templates.

### Cache Files Are Canonical Generation Inputs

- `KB/pm_tc_kb/**/*.inference.md` is a high-value working corpus, not disposable scratch output.
- When generating or refining FV test-case descriptions, first inspect neighboring cache files for the same feature/sub-feature and mirror the newest effective structure already in use.
- Prefer adapting an existing cache style over inventing a fresh markdown layout.
- Treat the cache file as the editable contract for description generation; downstream HTML should be rendered from it.

### Current Real-World Template Shape

Recent FV cache files commonly use a richer generated template than the minimal schema below. Typical sections include:

1. `# Deep Analysis: {Title}`
2. Top metadata table (`HSD ID`, `Title`, `Date`, `Feature`, `Sub-Feature`, `NWP Disposition`, optional owner/status/env/tags)
3. `## Test Case Intent`
4. `### Pre-Conditions`
5. `### Test Steps`
6. `### Pass / Fail Criteria`
7. `## Section A: ...`
8. `## Section B: ...`
9. `## Section C: ...`
10. `## Section D: ...`
11. `## Section E: ...` when applicable
12. `## Section F: Recommendation`

Use the minimal schema below as a fallback contract, but prefer the live cache corpus when it is richer or more current.

```markdown
# NWP {FV|PSS} Analysis

## Metadata
- HSD ID: {id}
- Title: {title}
- Feature: {feature}
- Sub Feature: {sub_feature}

## KB References
- KB Article: KB/pm_features/{feature}/{subfeature}.md

## User Notes
- (none)

## Version History
- v1 ({date}): Initial enrichment

## Refined Intent
{one sentence}

## Refined Test Steps
Pre-Conditions:
  - {condition}

Step 1 — {action} (TPMI offset 0xNN / MSR 0xNNN):
  PythonSV:
    ```python
    sv.socket0.nio.punit.<register>.read()
    ```
  Verification: {what to check}

Pass/Fail Criteria:
  PASS: {conditions}
  FAIL: {conditions}

## Section A: NWP Delta
## Section B: Interactions
### Swimlane Data
| Step | Actor | Action | Interface |
### Sequence Data
| # | From | To | Message | Interface |
## Section C: Coverage
## Section D: Spec Refs
## Section E: Risk Assessment
## Section F: Recommendations
```

### Authoring Rule for Test-Case Description Work

- If the request is about improving generated FV test-case descriptions, start from `KB/pm_tc_kb/` before consulting older root scripts or ad-hoc HTML outputs.
- Use a same-feature exemplar whenever possible, for example RAPL-to-RAPL or SST-to-SST, instead of cross-feature borrowing.
- If Section B heading variants appear in older cache files, normalize new output toward the headings required by the active HTML generator.

---

## Part 8 — PSS Grading (Section G)

Grading is integrated into the deep-analysis pipeline. Output goes to `## Section G: PSS Grading`
in the inference.md — it becomes a tab in the HTML automatically. No HSD comment posting.

### When to Grade

- User says "grade this TC", "NWP Grade TC `<ID>`", "assess readiness", "what environment can this run in?"
- After enriching a new TC (add Section G before generating HTML)

### 6-Dimension Rubric

| # | Dimension | Legal Values | Guidance |
|---|-----------|--------------|---------|
| 1 | **NWP Delta** | `Yes` / `No` | Does NWP topology/path differ from DMR in a way that affects this TC? |
| 2 | **Applicable NWP** | `Yes` / `No` | Is the feature present and non-ZBB on NWP? |
| 3 | **PSS Environment** | `VP` / `VP+HSLE` / `HSLE` / `VP_CONTENT` | Which pre-silicon environment can run this content? |
| 4 | **Silicon Only** | `Yes` / `Partial` | Does full validation require post-silicon? |
| 5 | **Test Content** | `DMR_L` / `DMR_M` / `NWP_N` | Origin and adaptation level |
| 6 | **OS** | `sv-os` / `linux-os` | Execution environment |

**PSS Environment rules:**
- CCF PMA registers (`ccf_pma.*`) → `VP+HSLE` or `HSLE`
- PUNIT-path registers (`punit_regs.*`, TPMI) → `VP` for write/readback; `VP+HSLE` for effect observation
- MSR counter increment (residency, TSC) → `HSLE` or silicon
- BIOS knob override needed → `VP_CONTENT`

**Test Content rules:**
- Same feature, same registers, only CBB loop change → `DMR_L`
- Same feature, IMH→NIO path change or NWP-specific TPMI → `DMR_M`
- Feature ZBB'd or completely new NWP-only feature → `NWP_N`

### Section G Format (write to inference.md)

```markdown
## Section G: PSS Grading

### Grading Table

| Sl No | Dimension | Value | Rationale |
|-------|-----------|-------|----------|
| 1 | NWP Delta | Yes / No | <TC-specific evidence> |
| 2 | Applicable NWP | Yes / No | <ZBB check or feature presence> |
| 3 | PSS Environment | VP / VP+HSLE / HSLE / VP_CONTENT | <register path reasoning> |
| 4 | Silicon Only | Yes / Partial | <timing/analog dependency> |
| 5 | Test Content | DMR_L / DMR_M / NWP_N | <adaptation level> |
| 6 | OS | sv-os / linux-os | <execution stack> |

### Verdict

**{VERDICT_LABEL}** — {2-sentence summary.}

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

### After Writing Section G

```powershell
python tools/html/generate_unified_html.py --segment fv --hsd <ID> --force
# G: PSS Grading tab appears automatically
```

> ⚠️ Grading must be LLM-reasoned per TC using actual TC content — never use a pre-written matrix.
