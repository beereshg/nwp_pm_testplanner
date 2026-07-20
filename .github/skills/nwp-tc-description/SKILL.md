---
name: nwp-tc-description
description: >
  Unified NWP PM TC skill covering TC description authoring (HOW content)
  plus pipeline infrastructure (KB flywheel, NWP architecture constants,
  HSD API patterns, enrichment sections A-F, KB article enrichment,
  cache file format, Phoenix hierarchy). TCD owns WHAT; TC describes HOW.
---

# NWP TC Description Skill

> Repo root: `c:/github/nwp_testplan/`
> Hierarchy: TP → TPF → **TCD** → **TC** → TR
> Phoenix: TC = "HOW to validate". TC inherits WHAT from parent TCD.
> Related: `nwp-tcd-description` (WHAT), `nwp-tpf-description` (Design Details)

---

## Content Routing — What belongs in a TC vs TCD

| Content type | TC (HOW) | TCD (WHAT) | TPF (Design Details) |
|-------------|----------|-----------|---------------------|
| Test step sequence (numbered) | ✅ | ❌ | ❌ |
| Tool command lines (`kayak`, `python`, `isst`) | ✅ | ❌ | ❌ |
| BIOS register execution sequence (step-by-step procedure) | ✅ | ❌ | ❌ |
| BIOS register theory / invariants (WHAT registers are involved) | references TCD §4 | ✅ | ❌ |
| **Pass/fail criteria bar** | references TCD §5 only | ✅ — **owned by TCD** | ❌ |
| OS API calls / sysfs paths used in execution | ✅ | ❌ | ❌ |
| Environment setup (BIOS knobs, driver state) | ✅ | ❌ | ❌ |
| Expected output snippets / register dump | ✅ | ❌ | ❌ |
| Scenario WHAT (what is being proven) | references TCD §1/§5 | ✅ | ❌ |
| Feature architecture diagrams / flows | ❌ | ❌ | ✅ |
| NWP-specific constants (freq targets, core count) | ❌ | ✅ (brief) | ✅ (full) |

> **M:N guardrail:** TC↔TCD is many-to-many. TC §1 and §5 must *link* to TCD content, never restate it. If TCD §5 criteria change, all N test cases pick up the change without TC edits.

---

## TC Title Convention (Layered Model)

Every TC title follows the format: `{TCD-ID} / {backend} / {variant}`

### Format

```
{FEATURE}-{LAYER}-{NNN} / {backend} / {variant-axes}
```

### Components

| Component | Values | Examples |
|-----------|--------|----------|
| `{TCD-ID}` | Parent TCD's layered ID | `PCT-SCENARIO-004` |
| `{backend}` | `FV` (silicon), `PSS` (Simics/VP), `PV` (platform) | `FV` |
| `{variant-axes}` | Tile, corner, DQ-cause, partition-count, tool | `thermal-DQ / CBB0` |

### Examples

```
PCT-CONTRACT-001 / FV / partition=2 / CBB0
PCT-CONTRACT-001 / PSS / DQ-Rule Register Check (FlexconPM)
PCT-SCENARIO-004 / FV / thermal-DQ / CBB0
PCT-SCENARIO-004 / FV / HWP-DQ / CBB1
PCT-SOAK-001 / FV / 25C / unit-A / 72h
```

### Rules

- TC title must start with its parent TCD's layered ID
- Slash-separated segments after backend are the fan-out axes
- Never restate the TCD's invariant in the TC title — it's inherited
- A TC that validates register configuration (e.g., FlexconPM) belongs under
  a CONTRACT-layer TCD, not a SCENARIO-layer TCD

### TC Reorganization Trigger

When reorganizing TCs under a retitled TCD, apply these checks:

| Check | Action |
|-------|--------|
| TC validates **register state** (post-boot checks, FlexconPM) | Move to `CONTRACT-*` TCD |
| TC validates **runtime behavior** (inject event → observe response) | Keep under `SCENARIO-*` TCD |
| TC validates **meter accuracy** (counters vs reference) | Move to `OBS-*` TCD |
| TC is rejected/ZBB | Leave in place (don't move rejected TCs) |
| TC duplicates intent of sibling under different backend | Same TCD, different title suffix |

### Fan-Out Axes (TC instantiation)

One TCD fans out across these axes at TC level:

| Axis | Typical Values | When to fan |
|------|---------------|-------------|
| Backend | FV / PSS / PV | Always (minimum 1 per applicable backend) |
| Tile | CBB0 / CBB1 | Per-tile when TCD mentions "per tile" |
| Corner | 25°C / 85°C / Vmin / Vmax | Layer 4 (soak) only, unless TCD specifies |
| Partition count | 1 / 2 / 4 | PCT-specific: sweep configs |
| Scenario variant | thermal-DQ / HWP-DQ / core-offline | Per-TCD specific |
| Unit | unit-A / unit-B | Layer 4 (soak) — minimum 2 samples |

Healthy ratio: **1 TCD → 3 to ~20 TCs.** If ratio ≈ 1:1, TCDs are secretly procedures.

---

## When to Use

- User asks to write, enrich, or update a TC description
- TC description is generic ("run kayak") with no test steps or measurement procedure
- TC inherits a rich TCD and needs the HOW details filled in
- User says `enrich tc <ID>`, `write tc steps <ID>`, `update tc <ID>`

---

## TC Description Structure (5 sections)

Phoenix TC = HOW to validate. Sections map to Phoenix TC fields:

```
1. Validation Scope           ← Links to TCD §1 scenario + §5 row (≤80 words; never restate TCD)
2. Preconditions              ← Platform, BIOS knobs, driver state, tool availability
3. Automation                 ← Exact command line(s) to run the test
4. Test Steps                 ← Numbered sequence: action → expected result per step
5. Pass/Fail Measurement Method  ← HOW to evaluate against the bar in TCD §5; execution assertions only
```

**Guardrails:**
- §1 Scope: 1 sentence linking to TCD §5 row. Do NOT copy TCD scenario text — TCD is the single source.
- §5 Criteria: open with `Per TCD [ID] §5: [paste TCD bar link].` Then add any execution-specific assertions (e.g. no dmesg errors, timeout <N s). Never write a competing bar.

### Section 1: Validation Scope

One sentence linking to the parent TCD and the specific scenario row. Do NOT restate TCD content.

```markdown
Validates the [scenario name] scenario defined in [TCD ID — Title](url) §5, row [scenario].
Environment: [NWP-IMH post-silicon / PSS VP / HSLE XOS].
```

> TC↔TCD is M:N. Linking instead of restating means a TCD edit propagates to all N TCs without TC updates.

### Section 2: Preconditions

| Requirement | Detail |
|-------------|--------|
| Platform | NWP-IMH system / PSS VP (Simics) / HSLE XOS |
| BIOS knobs | `EDKII → Socket Config → ...` = `value` |
| OS / Driver | Ubuntu; `scaling_driver = intel_pstate`; `intel-speed-select` installed |
| Feature state | PCT enabled / disabled; partition_count = N |
| Tool | `kayak` installed; `sst_launcher.py` accessible |
| Starting state | e.g. "start from prior-enabled PCT state" |

### Section 3: Automation

```markdown
**Command line:**
`kayak -p kayak.plugins.sst.plugin tests\contents\powermanagement\sst\sst_launcher.py --test <TEST_NAME>`

**Script / tool:** `sst_launcher.py`
**Test function:** `SST_PCT_MODULE_*`
**Estimated runtime:** ~N minutes
```

For PythonSV-based TCs:
```python
# Automation entry point
python scripts/pm/pss/pct_test.py --scenario <scenario>
```

### Section 4: Test Steps

Numbered sequence. Each step = **one action** + **one expected result**.

```markdown
1. **Set BIOS knob** — PCT Partition Count = N. Expected: knob accepts value; no error in BIOS Setup.
2. **Boot system** — power cycle to Ubuntu. Expected: OS boot completes; `dmesg` shows no SST errors.
3. **Verify intel-speed-select topology** — run `intel-speed-select perf-profile info`. Expected: N HP modules reported with correct APIC IDs.
4. **Read cpufreq caps per core** — for each cpu in all_cpus, read `/sys/bus/cpu/devices/cpuN/cpufreq/cpuinfo_max_freq`. Expected: HP cores = ~4.4 GHz ceiling; LP cores = ~2.3 GHz ceiling.
5. **Assert HP > LP** — verify `max(hp_freqs) > max(lp_freqs)`. Expected: assertion passes.
```

**Rules for test steps:**
- Each step must be independently verifiable
- Include the exact register path / sysfs path / command used
- Include the exact expected value or comparison
- Never omit the "Expected:" line — that IS the pass/fail logic

### Section 5: Pass/Fail Measurement Method

**The pass/fail bar (measurable threshold) is owned by the parent TCD §5.** TC §5 describes HOW to measure against that bar — which tool, which command, which register read sequence — and adds only execution-specific assertions (no timeouts, no dmesg errors) that are not feature-level.

```markdown
**Bar:** Per [TCD ID — Title](url) §5: [exact bar statement from TCD, e.g. “HP core cpuinfo_max_freq ≥ hp_trl_khz × 0.95”].

**Measurement procedure (this TC only):**
1. Read: `for c in hp_cpus: open(f'/sys/bus/cpu/devices/cpu{c}/cpufreq/cpuinfo_max_freq').read()`
2. Compare: `assert max_freq >= hp_trl_khz * 0.95` per core
3. Execution assertions: no SST-related dmesg errors; test completes < N minutes
```

> Never define a threshold value here. If TCD §5 bar changes (e.g. 0.95 → 0.98), all linked TCs inherit the change without TC edits.
- LP core `cpuinfo_max_freq` ≤ `lp_clip_khz × 1.05` for all LP CPUs
- `intel-speed-select` reports correct HP module count = `partition_count × 2`
- No dmesg errors related to SST or PCT during test

**FAIL** when ANY of the following are true:
- Any HP core `cpuinfo_max_freq` below HP TRL threshold
- Any LP core `cpuinfo_max_freq` above LP clip threshold
- `intel-speed-select` reports wrong HP count or missing modules
- SST-related dmesg errors observed
```

---

## HOW Content Patterns (reference)

### BIOS register sequence in TC (not TCD)

When a TC requires specific BIOS register programming, document it in the **Preconditions** or **Test Steps** — NOT in the TCD Section 4.

```markdown
# In TC Preconditions:
| Req | Detail |
|-----|--------|
| BIOS programming | BIOS CPL3 programs: SST_CLOS_CONFIG[0].max = SST_TF_INFO_2.ratio_0; SST_CP_CONTROL.priority_type = 1 |

# In TC Test Steps:
1. Confirm BIOS has programmed SST_CLOS_CONFIG[0].max:
   - Run: `sv.socket0.nio0.tpmi.sst_clos_config_0.read()`
   - Expected: value = SST_TF_INFO_2.ratio_0 (~0x2C for 4.4 GHz on NWP)
```

### OS API / sysfs assertions in TC (not TCD)

```markdown
# In TC Test Steps:
3. Read per-core frequency caps:
   - Run: `for c in range(96): open(f'/sys/bus/cpu/devices/cpu{c}/cpufreq/cpuinfo_max_freq').read()`
   - Expected: cores 0,24,48,72 (HP) report ≥4,400,000; all others report ≤2,300,000
```

### PythonSV assertions in TC (not TCD)

```markdown
4. Read TPMI CLOS assignment per core:
   - Run: `[nio.tpmi.sst_clos_assoc.read_field(f'clos_{i}') for i in range(96)]`
   - Expected: HP cores → 0 (CLOS[0]); LP cores → 3 (CLOS[3])
```

---

## Push to HSD

TCs use `subject: test_case`. **Always use `push_tc_description.py`** — it reads the
inference.md, extracts sections via `generate_tc_description.py` extractors, renders
through the Jinja2 template `KB/templates/tc_hsd_description.html.j2`, backs up the
existing HSD description as a comment, then PUTs the rendered HTML.

```bash
# Dry-run (preview only, no writes)
python tools/html/push_tc_description.py --hsd 22022421978

# Push one TC (prompts for confirmation)
python tools/html/push_tc_description.py --hsd 22022421978 --push

# Push without per-TC prompt
python tools/html/push_tc_description.py --hsd 22022421978 --push --yes

# Push all TCs with KB inference.md
python tools/html/push_tc_description.py --all --push --yes

# Limit to FV segment
python tools/html/push_tc_description.py --all --segment fv --push --yes
```

> **NEVER extract raw HTML from `generate_unified_html.py` output** for HSD push.
> That script generates a multi-tab analysis page with `<style>` blocks, JavaScript,
> and wrapper chrome that HSDES strips. The Jinja2 template produces inline-styled
> HTML that HSDES renders correctly.

### Jinja2 Pipeline Flow

```
inference.md  →  generate_tc_description.py extractors  →  Jinja2 render  →  HSD PUT
                 (section headings → structured dict)       (tc_hsd_description.html.j2)
```

### Required Section Headings in inference.md

The extractors in `generate_tc_description.py` search for these headings (first match wins):

| Jinja2 Variable | Extractor Headings (priority order) |
|-----------------|-------------------------------------|
| `tc.scope` | `## Test Case Intent`, `### Test Case Intent`, `### Intent`, `### Refined Intent` |
| `tc.preconditions` | `### Pre-Conditions`, `## Pre-Conditions`, `### Preconditions` |
| `tc.steps` | `### Test Steps`, `## Test Steps`, `### Adapted Test Steps` |
| `tc.passfail` | `### Pass / Fail Criteria`, `### Pass/Fail Criteria`, `## Pass/Fail Criteria` |
| `tc.health_checks` | `### Health Checks`, `## Health Check` |
| `tc.notes` | `## Section E: Risk Assessment`, `### Notes`, `## User Notes` |
| `tc.opens` | `## Section E: Risk Assessment` (filters severity=high/medium) |
| `tc.post_process` | `## Post-Process`, `### Post-Process`, `#### Post-Process` |
| `config.fr_hsd` / `config.specs` | `## Section D: Spec Refs`, `## KB References`, `### Reference Documents`, `### References`, `## References` |

### Inference.md Section Format for Jinja2 Compatibility

The cache file **must** use these heading names for the push pipeline to extract content:

```markdown
## Test Case Intent
<scope paragraph — links to TCD, ≤80 words>

### Pre-Conditions
| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon ... |
| BIOS knobs | ... |

### Test Steps
| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | ... | ... | ... |

### Pass / Fail Criteria
- **PASS**: <criteria>
- **FAIL**: <criteria>

### Health Checks
| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| ... | ... | ... |

### Post-Process
N/A

### References
- [TCD 16031169418](https://hsdes.intel.com/appstore/article-one/#/16031169418)
- [Wave 3 HAS](https://docs.intel.com/...)
```

> **Subject**: `test_case` (not `test_case_definition` — that is TCD)

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Test steps in TCD Section 4 | Move numbered test steps to TC; TCD Section 4 = feature programming theory only |
| Pass/fail criteria missing | Always required in TC Section 5 — block TC if absent |
| **Criteria bar authored in TC (Mistake 2)** | **Move the measurable threshold to TCD §5.** TC §5 = measurement procedure + link to TCD bar only. Authoring the bar in TC creates contradictory thresholds across M:N TCs. |
| `kayak` command in TCD | Command lines belong in TC Section 3, not TCD |
| OS API calls (`cpuinfo_max_freq`, `isst`) in TCD | Move to TC test steps; TCD references the observable outcome only |
| BIOS register sequence in TCD Section 4 | Move specific test-time register reads/writes to TC preconditions or steps; TCD Section 4 = what registers are involved conceptually |
| Missing "Expected:" in test step | Every step must have an expected result — it IS the pass/fail logic |

---

# Agent-Context Reference (loaded with skill, not standalone content)

> The sections below provide NWP architecture constants, Phoenix hierarchy IDs,
> HSD access patterns, enrichment section formats, and KB article mappings used
> by the `@nwp_pm_testplanner` agent mode. They are NOT TC authoring guidance —
> the TC HOW content is above this line (lines 1–218).

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

## Part 1 — Quality Guardrails

1. **Reference hygiene**: only include HAS/MAS/HSD/spec links actually cited in the body. No speculative references.
2. **Read/preview before write**: for any HSD create/update/move, do discovery/read-back first, then execute.
3. **Mandatory section policy**: fill all required TC/TCD sections or explicitly mark `N/A`/`Not Applicable`.
4. **No-email write policy**: all automation is silent (no watcher notification).
5. **Payload compatibility**: attempt write with `{"send_mail": "false"}` in `fieldValues`; if HTTP 400, retry without `send_mail`, then read-back verify.
6. **Rendering boundary**: generate/update `cache/*.inference.md` first; render HTML only via official scripts — never hand-write HTML. To push a TC description to HSD, always use `push_tc_description.py` (see Part 4).
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

## Part 3 — HSD Access Model

### Tools (use in this order)

| Operation | Tool | Example |
|-----------|------|---------|
| **Read article** | `HSDTool` MCP | `HSDTool get_article tenant:server subject:test_case id:<id>` |
| **EQL search** | `HSDTool` MCP | `HSDTool query tenant:server subject:test_case eql: feature_tag LIKE '%rapl%'` |
| **Walk hierarchy** | `hsd_utils/hierarchy.py` | `walk_hierarchy(tp_id="16030762839")` |
| **Update field** | `tools/hsd/hsd_update.py` | `python tools/hsd/hsd_update.py <ID> --subject test_case --field status --value rejected` |
| **Push description** | `tools/hsd/push_preview.py` | `python tools/hsd/push_preview.py tcd_description_output/TCD_*_preview.html` |
| **Create TPF** | `tools/hsd/hsd_create_tpf.py` | `python tools/hsd/hsd_create_tpf.py --parent <TP_ID> --title "Feature Area"` |
| **Move / set owner** | `hsd_utils/operations.py` | `move_tcd(tcd_id, new_tpf_id)` / `set_owner(id, "bg3")` |

### HSD Hierarchy (subject & child_subject reference)

```
Test Plan (TP)       subject = "test_plan"
  └── TPF            subject = "test_plan"              ← same subject as TP!
        └── TCD      subject = "test_case_definition"
              └── TC  subject = "test_case"
                    └── TR  subject = "test_result"
```

| Parent | `child_subject` to use |
|--------|------------------------|
| TP → TPFs | `"test_plan"` — NOT `"test_plan_folder"` |
| TPF → TCDs | `"test_case_definition"` |
| TCD → TCs | `"test_case"` |
| TC → TRs | `"test_result"` |

### Common Pitfalls

| # | Pitfall | Fix |
|---|---------|-----|
| 1 | Wrong `child_subject` | Returns empty `data:[]` silently — check hierarchy table above |
| 2 | `send_mail="false"` → HTTP 400 | Retry without `send_mail`, then read-back verify |
| 3 | TC reject field order | `status` first, `reason` second in `fieldValues` |
| 4 | TPF vs TP subject | Same subject `"test_plan"` — distinguish by `parent_id` |
| 5 | Comment create/read singular vs plural | POST `"comments"`, GET `"comment"` |
| 6 | New article ID location | Try `new_id` → `id` → `data[0].id` |

**Traceability**: embed `[val_agent] {action} — {date}` in all automated writes.

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

### Enrichment Order: Co-Design MCP First, KB Fallback

**Step 1 — Query Co-Design MCP** (authoritative, always run first):

Call `codesign-ask-specs-and-wikis` for each missing section. These queries return spec-grounded answers from HAS/MAS/wiki sources.

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

**Step 2 — Fill gaps from local KB files** (cached supplementary data):

After MCP results are collected, check local KB articles (see Feature → KB File Mapping above) for any sections the MCP response did not cover — especially:
- Topology diagrams and ASCII art not returned by MCP
- KPI & Timing tables with precise numeric values
- NWP Delta details captured from prior analysis sessions
- Legacy human-curated notes

Also check `KB/pm_features/PNC PM HAS 0.5_text.txt` for core-level PM features (C-states, DTS, THERM_STATUS, budget negotiation) — this local file has detail that MCP may not fully reproduce.

**Step 3 — Merge and deduplicate**: MCP content takes precedence when both sources cover the same field. Local KB content fills in where MCP is silent or incomplete.

---

## Part 7 — Cache File Authoring Rules

- `KB/pm_tc_kb/**/*.inference.md` is the canonical generation input — not disposable scratch.
- When enriching a TC, first inspect neighboring cache files for the same feature and mirror the newest effective structure already in use (RAPL→RAPL, SST→SST — not cross-feature borrowing).
- Treat the cache file as the editable contract; downstream HTML is rendered from it via `tools/hsd/push_preview.py`.
- If Section B heading variants appear in older cache files, normalize new output toward the headings required by the active HTML generator (see Part 5).

---
