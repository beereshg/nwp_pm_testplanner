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
- Unified HTML out: `KB/pm_tc_deepanalysis/` (all generated files)
- Hierarchy HTML: `nwp_pm_hierarchy.html` (full interactive view)

### Graded TPs (TC grading comments posted to HSD)

| TP | TCs graded | Date | Comment IDs (first/last) |
|----|-----------|------|--------------------------|
| `22022420505` CBB CCF PM | 15 | 2026-06-17 | 1667580755 – 1667580775 |
| `16030762839` SST | 40 | 2026-06-17 | 1667580954 – 1667580996 |

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
10. **Description preservation on overwrite**: before replacing a TC description with LLM-backed/template-updated content, preserve the prior description in an HSD comment or equivalent traceable snapshot.

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
  - Preserve the old description in HSD comments before overwrite.
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
| `sv.socket0.imh0.punit.*` | `sv.socket0.nio.punit.*` |
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
| Cache file | `KB/pm_tc_kb/**/HSD_{id}_{slug}.inference.md` | `KB/pm_tc_kb/**/HSD_{id}_{slug}.inference.md` |
| HTML output | `KB/pm_tc_deepanalysis/HSD_{id}_{slug}.html` | `KB/pm_tc_deepanalysis/HSD_{id}_{slug}.html` |
| HTML generator | `tools/html/generate_unified_html.py --segment fv|pss|all` | `tools/html/generate_unified_html.py --segment fv|pss|all` |
| Index pages | `KB/pm_tc_deepanalysis/nwp_pm_fv_test_cases.html` | `KB/pm_tc_deepanalysis/nwp_pss_test_cases.html` |

### Practical Interpretation of These Paths

- `KB/pm_tc_kb/`: primary editable deep-analysis/template corpus for both FV and PSS.
- `KB/pm_tc_deepanalysis/`: rendered unified presentation output for FV and PSS.
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
