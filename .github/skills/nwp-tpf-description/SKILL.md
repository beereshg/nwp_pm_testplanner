---
name: nwp-tpf-description
description: >
  Generate, preview, and update NWP PM TPF / TP descriptions in HSD.
  Follows KB → HTML → push-to-HSD pipeline (same flywheel as nwp-tcd-description).
  Owns the "Design Details" section — architecture diagrams and block flows extracted
  from TCD descriptions live here, not in individual TCDs.
---

# NWP TPF Description Skill

> Repo root: `c:/github/nwp_testplan/`
> Depends on: `nwp-tcd-description` skill (push pattern, stale file handling, PowerShell fix)
> Generator: `tools/html/generate_tpf_preview.py` (imports render utils from `generate_tcd_preview.py`)

---

## When to Use

- User asks to enrich, preview, or update a TP / TPF description
- Architecture diagrams or boot flow diagrams are duplicated across multiple TCD Section 1s
- TPF is missing Risks & Dependencies, DFX, or Common Corner Cases sections
- TPF TCD coverage table is stale (titles or counts changed)
- User says `enrich tpf <ID>`, `preview tpf <ID>`, `update tpf <ID>`

---

## Workflow

```
Step 1: Fetch       HSD TPF → KB/pm_tpf_kb cache (.md)
Step 2: Extract     Design Details from TCD KB files → TPF Section 2
Step 3: Enrich      Add Risks/DFX/Corner Cases from HAS/MAS/KB
Step 4: Preview     cache → tpf_description_output/TPF_{id}_{slug}_preview.html
Step 5: Confirm     user reviews HTML preview
Step 6: Update TCD  Strip extracted diagrams from TCD Section 1, add TPF reference line
Step 7: Update HSD  PUT TPF description (then PUT updated TCDs)
```

**Never update HSD without explicit user confirmation after preview.**
**Update TPF first, then TCDs — never leave TCDs diagram-free before TPF is live.**

---

## Step 1 — Fetch and Cache TPF

```python
import sys; sys.path.insert(0, '.')
from hsd_utils import get_session, get_article, get_children

s = get_session()
TPF_ID = '<tpf_id>'

tpf  = get_article(TPF_ID, fields='id,title,description,status,owner,parent_id', session=s)
tcds = get_children(TPF_ID, 'test_case_definition', fields='id,title,status', session=s)
```

**Cache file path:**
`KB/pm_tpf_kb/{tp_id}_{tp_slug}/TPF_{tpf_id}_{slug}.md`

Example: `KB/pm_tpf_kb/16030762839_sst_speed_select_technology/TPF_16030762939_nwp_pm_pct_priority_core_turbo.md`

---

## Step 2 — Design Details Extraction Contract

**What moves FROM TCD Section 1 TO TPF Section 2:**

| Content type | Example (PCT) | Action |
|-------------|---------------|--------|
| Boot/reset flow ASCII diagram (feature-wide) | PCT boot-to-OS flow: PrimeCode → BIOS → Ubuntu | Move to TPF §2 |
| Architecture diagram (applies to all TCDs under this TPF) | WP4 broadcast / ordered throttle HTML diagram | Move to TPF §2 |
| Frequency hierarchy table | P0max → LP_CLIP with NWP values | Move to TPF §2 |
| HP core selection algorithm | First-per-partition / APIC-ID ordering rule | Move to TPF §2 |
| Per-TCD-specific scope text | "This TCD covers BIOS knob validation only" | Keep in TCD |
| TC coverage map table | Links to child TCs with scope | Keep in TCD |
| NWP-specific constants table | Total cores, partition count, max_partitions | Keep in TCD (reference values) |
| Programming model register/MSR table (feature-wide) | Full register list from TCD §4 | Move to TPF §2 → `### Interface & Register Matrix` |
| Debug observability list (MSRs, tools, BIOS knobs — cross-TCD) | Tools + commands to observe feature state | Move to TPF §2 → `### Observability` |
| SKU / config behavioral distinctions (affects multiple TCDs) | Fuse/BIOS-knob gating table from TCD §1 or §4 | Move to TPF §2 → `### SKU / Config Distinctions` |

**What stays in TCD Section 1 after extraction:**

```markdown
## Section 1: Architecture / Micro-architecture and Functionality

[One-paragraph scope statement for THIS TCD — no diagrams.]

> **Architecture overview:** See [TPF 16030762939 — NWP PM PCT](url) §Design Details
> for boot flow, CLOS mechanism, ordered throttle diagram, and frequency hierarchy.

### TC Coverage Map
| TC | Title | Scope |
...
```

---

## Step 2b — §2 Completeness Lint (Run After Any TCD Promotion)

Run these two lints after editing TPF §2 and before generating the preview.

**Lint A — Layer claim coverage:**
Every layer in the Full-Stack Cross-Layer Diagram must be claimed by at least one non-❌ tier in the Validation-Tier Layer Claim table. Rows with PSS=❌, FV=❌, PV=❌ are validation gaps — surface each in §5 Accepted Coverage Limitations.

```python
# Quick section health-check — run from repo root before generate_tpf_preview.py
from tools.html.generate_tcd_preview import parse_block
kb_text = open('<kb_file>', encoding='utf-8').read()
for section in ['Design Details', 'Validation Strategy', 'Tier Coverage', 'Risks', 'DFX', 'Common Corner']:
    block = parse_block(kb_text, section)
    status = '⚠️  EMPTY — check for duplicate ## heading' if len(block) < 3 else '✓'
    print(f'{section:<22}: {len(block):>4} lines  {status}')
```

**Lint B — TCD extraction completeness (block-by-block diff):**
Before pushing, diff the promoted content:
1. List every `###` heading removed from the source TCD KB
2. Confirm each maps to a `###` heading in TPF §2 (use the table below)
3. Any unmatched heading = dropped content → add it to the appropriate landing zone

A regenerated diagram may look "prettier" but drop panels from the original — verify subsection count matches.

| TCD source heading removed | Required TPF §2 landing zone |
|---|---|
| `### Boot Flow` / `### Reset Sequence` | `### {Feature} Boot / Reset Flow` |
| `### Architecture Block` / `### Ordered Throttle` | `### {Feature} Architecture Block` |
| `### Frequency Hierarchy` / `### Frequency Table` | `### Frequency Hierarchy` |
| `### Selection Algorithm` / `### Assignment` | `### Key Selection / Assignment Algorithm` |
| `### Register Table` / `### MSR Table` / `### Programming Model` | `### Interface & Register Matrix` |
| `### Observability` / `### Debug Registers` / `### Debug Knobs` | `### Observability` |
| `### SKU` / `### Config` / `### Platform Variations` | `### SKU / Config Distinctions` |
| `### Firmware Agent Responsibilities` (§1 intra-doc) | `### Agent Source Ownership` — extract `Key Artifact` column only; `Role` column is redundant with §2 full-stack diagram |
| Unrecognized heading | ⚠️  Flag for manual placement — do NOT silently drop |

---

## Step 3 — TPF KB File Format (8 sections)

**File path:** `KB/pm_tpf_kb/{folder}/TPF_{id}_{slug}.md`

The generator (`generate_tpf_preview.py`) maps KB headings to numbered HTML sections via keyword matching:

| KB heading keyword | HTML section label | Phoenix §3.1 mapping |
|--------------------|--------------------|----------------------|
| `Feature Classification` | 1. Feature Classification & Introduction | Introduction + design details focus |
| `Design Details` | 2. Design Details | Block diagrams / state diagrams / pipeline flows |
| `Validation Strategy` | 3. Validation Strategy | Validation strategy highlights |
| `Tier Coverage` | 4. Tier Coverage | Validation strategy — tier-level coverage |
| `Risks` | 5. Risks & Dependencies | Risks and dependencies |
| `DFX` | 6. DFX Considerations | DFX |
| `Common Corner` | 7. Common Corner Cases | Potential corner cases (cross-TCD) |
| `TCD Coverage` | 8. TCD Coverage Summary & References | References + TCD coverage table |

### Recommended TPF KB Structure

```markdown
# TPF {ID} — {Title}

| Field | Value |
|-------|-------|
| **TPF ID** | [{ID}](url) |
| **Title** | {title} |
| **Parent TP** | [{tp_id} — {tp_title}](url) |
| **KB last updated** | {date} |

---

## Section 1: Feature Classification & Introduction

[Feature overview: what the feature is, silicon-heavy vs firmware-heavy classification,
 key capability gating mechanism (fuse, BIOS knob, etc.)]

> **§1 scope rule:** §1 contains ONLY: feature intro paragraph, gating mechanism (fuse name or BIOS
> knob path), and feature-specific constants. Do NOT put firmware agent roles here — they duplicate
> the §2 full-stack diagram. If §1 has a `### Firmware Agent Responsibilities` table:
> - Extract the `Key Artifact` column → add a `### Agent Source Ownership` table in §2
> - Delete the Role column (already covered by the full-stack diagram layer boxes)
> - See Common Pitfall: *§1 restates §2 layer responsibilities*

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| *(key feature constants: core counts, frequency targets, fuse names, max partitions, etc.)* | | |

---

## Section 2: Design Details

[Architecture diagrams extracted from TCDs — boot flow, CLOS mechanism, frequency hierarchy,
 key register sequences that apply across ALL TCDs under this TPF.]

> **⚠️ Insertion rule:** When adding a `### SubSection` into this block via `replace_string_in_file`,
> start the `newString` at `### SubSection` — **do NOT repeat `## Section 2: Design Details`** in the
> replacement. A duplicate `## ` heading causes `parse_block()` to stop immediately and renders the
> section as "Not documented." Verify with:
> ```python
> from tools.html.generate_tcd_preview import parse_block
> block = parse_block(kb_text, 'Design Details')
> assert len(block) > 10, f"Section 2 empty — check for duplicate ## heading (got {len(block)} lines)"
> ```

### ⚡ MANDATORY: Full-Stack Cross-Layer Diagram

**One diagram showing every layer from OS/tool down to silicon is required in every TPF.**
Derive layer names from the feature's HAS/MAS — do NOT hard-code PCT's five layers.
RALP's stack, SST-TF's stack, and PCT's stack decompose differently; the template mandates
a stack with tier claims; the spec supplies the layer names.

<!-- raw-html -->
<!-- Example structure — adapt layer names to feature HAS: -->
<div style="border:2px solid #333;border-radius:8px;padding:12px;font-family:Arial,sans-serif;max-width:600px">
  <div style="background:#4472C4;color:#fff;padding:8px;margin:4px;border-radius:4px;text-align:center"><strong>Layer N: OS / Tool</strong> — userspace tools, kernel drivers</div>
  <div style="background:#ED7D31;color:#fff;padding:8px;margin:4px;border-radius:4px;text-align:center"><strong>Layer N-1: Firmware Policy</strong> — PCode / OCode / BIOS knob control</div>
  <div style="background:#A020F0;color:#fff;padding:8px;margin:4px;border-radius:4px;text-align:center"><strong>Layer N-2: Enforcement / Control</strong> — frequency / throttle enforcement</div>
  <div style="background:#70AD47;color:#fff;padding:8px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 2: Platform Agent</strong> — Acode, PCU interface</div>
  <div style="background:#FF0000;color:#fff;padding:8px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 1: Silicon / HW</strong> — PHM, HPM, WPM, CLU hardware</div>
</div>
<!-- /raw-html -->

### ⚡ MANDATORY: Validation-Tier Layer Claim

**Placed directly under the full-stack diagram.**
Every row (= every stack layer) must be claimed by at least one non-❌ tier.
Rows where PSS=❌, FV=❌, PV=❌ are validation gaps → surface each in §5 Accepted Coverage Limitations.

> **§3 pointer (required):** Validation Strategy §3 must reference this table:
> *"Layer coverage is mapped in §2 — Validation-Tier Layer Claim table identifies which tier
> validates each stack layer and flags any unclaimed layers as accepted gaps."*

| Layer (from full-stack diagram) | PSS | FV | PV | Notes |
|---|---|---|---|---|
| OS / Tool Layer | ❌ | ❌ | ✅ | Requires booted OS + tool stack |
| Firmware Policy Layer | ✅ | ✅ | ✅ | All tiers validate |
| Enforcement / Control Layer | ✅ | ✅ | ❌ | Model-level only pre-Si |
| Platform Agent Layer | ✅ | ✅ | ✅ | Covered across tiers |
| Silicon / HW Layer | ✅ | ✅ | ❌ | RTL / model coverage; PV observes indirectly |

### {Feature} Boot / Reset Flow

```
ASCII diagram here
```

### {Feature} Architecture Block (within-layer view)

<!-- raw-html -->
<existing HTML diagram from TCD>
<!-- /raw-html -->

### Frequency Hierarchy

| Level | Value | Notes |
...

### Key Selection / Assignment Algorithm

[HP core selection, CLOS assignment, etc.]

### Interface & Register Matrix

**Named landing zone.** Feature-wide register / MSR table promoted from TCD §4 (Programming Model).
Provides stable anchor for TCD cross-references: link here rather than duplicating the table in each TCD.

| Register / MSR | Field | Default | Feature effect | Tier validated |
|---|---|---|---|---|
| *(populate from HAS §Programming Model or TCD §4)* | | | | |

### Observability

**Named landing zone.** Debug MSRs, tool commands, and BIOS knobs used to observe feature
state — promoted from any TCD whose observability list applies across multiple TCD scopes.

| Observable | Type | Tool / Command | What it shows |
|---|---|---|---|
| *(populate from TCD observability or HAS debug section)* | | | |

### SKU / Config Distinctions

**Named landing zone.** Platform-specific behavioral variations promoted from TCDs — fuse-gated,
BIOS-knob-controlled, or config-restricted behaviors that affect multiple TCDs under this TPF.

| SKU / Config | Distinction | TCDs affected |
|---|---|---|
| *(populate from HAS §SKU or TCD config tables)* | | |

### Agent Source Ownership

**Named landing zone.** Source file / FAS ownership for each layer — promoted from §1 if a
`### Firmware Agent Responsibilities` table was present there (extract `Key Artifact` column;
discard the `Role` column, which is redundant with the full-stack diagram layer boxes).
Use this when a frequency / power anomaly needs to be traced to the right codebase.

| Layer / Agent | Key Artifact (source file / FAS) |
|---|---|
| *(populate from HAS §Implementation or §1 agent table `Key Artifact` column)* | |

---

## Section 3: Validation Strategy

[Three-tier rationale: PSS / FV / PV — what each validates and why all are needed.]

> **PSS sub-environments:** PSS is not monolithic. Expand PSS columns in §4 to `PSS (VP) / PSS (HSLE) / PSS (XOS)` because each covers different IP scope:
> - **VP (Simics):** firmware + simplified silicon model; safe for negative/destructive tests
> - **HSLE:** single IMH or CBB RTL; can validate within-die PCode logic; cannot model cross-die protocol
> - **HSLE XOS (both dies):** IMH+CBB RTL together; mandatory for any cross-die protocol bug class

### Tier Definitions

| Tier | Environment | Interface | What it validates |
|---|---|---|---|
| PSS — VP | Simics (virtual platform) | PythonSV → TPMI model | Firmware logic, BIOS flows, safe negative testing |
| PSS — HSLE | Single-die RTL | PythonSV → TPMI RTL | Within-die PCode + Acode interaction |
| PSS — XOS | Both-die RTL (IMH+CBB) | PythonSV → full RTL | Cross-die HPM protocol, full ordered throttle |
| FV | Post-silicon NWP | PythonSV → namednodes | Real silicon behavior, real power/frequency |
| PV | Post-silicon NWP + Ubuntu | `intel-speed-select` → sysfs | OS/driver layer, E2E user-visible capability |

---

## Section 4: Tier Coverage

[Bug coverage matrix (which tier catches which bug class) + scenario coverage across tiers.]

**PSS sub-environment key** — split PSS columns by environment; each row only covers the PSS environments that can reach the bug:

| Symbol | Meaning |
|---|---|
| ✅ | Catches / detects this bug class |
| ❌ | Cannot catch — wrong environment or interface |
| ⚠️ | Partial / limited detection (model gap, heuristic only) |
| `indirect` | PV can observe the symptom at the OS/tool layer but cannot directly attribute it — FV is the isolation environment |
| `✅ safe` / `❌ risky` | Environment-safety annotation: valid for BIOS negative validation where VP is safe (no silicon at risk) but FV would risk real silicon damage |

### Bug Coverage Matrix

| Bug Category | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV |
|---|---|---|---|---|---|
| Firmware-layer bug (PCode / PrimeCode TPMI write logic) | ✅ | ⚠️ | ✅ | ✅ | indirect |
| Cross-die protocol bug (IMH↔CBB HPM) | ❌ | ❌ | ✅ | ✅ | indirect |
| Silicon HW bug (TPMI decoder, fuse gating) | ❌ | ❌ | ❌ | ✅ | indirect |
| OS / driver bug (intel-speed-select, intel_pstate) | ❌ | ❌ | ❌ | ❌ | ✅ |
| Real-power / TDP convergence | ❌ | ❌ | ❌ | ✅ | ✅ |
| BIOS negative validation | ✅ safe | ❌ | ❌ | ❌ risky | ❌ |
| *(add feature-specific rows from HAS bug taxonomy)* | | | | | |

> **BIOS negative validation rule:** VP (Simics) is the **only** safe environment for injecting invalid BIOS
> values — no silicon at risk. FV is marked `❌ risky` because invalid programming can damage or lock real
> silicon state. Do NOT run BIOS negative tests on FV without explicit hardware team sign-off.

### Scenario Coverage Across Tiers

| Scenario | PSS | FV | PV | Unique value |
|---|---|---|---|---|
| *(add feature scenarios)* | | | | |

---

## Section 5: Risks & Dependencies

**Split §5 into two sub-sections** when coverage gaps have been analysed:

### Active Risks

- **{Risk 1}**: description + mitigation
- **{Risk 2}**: ...

### Accepted Coverage Limitations (by design — no new TCs required)

Document inherent gaps that have no actionable TC. Required fields: current coverage, accepted rationale.

| Gap ID | Description | Coverage Today | Accepted Rationale |
|--------|-------------|----------------|-------------------|
| **G-N** | What cannot be tested | FV only / PV only / env-only | Why this is the only correct detection path (e.g. silicon-level HW bug; driver requires booted OS; model gap by design) |

**When to use the accepted limitations table:**
- After running a formal coverage gap analysis (see Common Pitfalls below)
- G-numbered gaps that have no lightweight pre-silicon equivalent
- Inherent architectural limitations (e.g. Acode VP model gap, cross-die HPM HSLE XOS only)
- NOT for gaps that have candidate TCs — those go in TCD §6 as *(TC TBD)*

---

## Section 6: DFX Considerations

- **{DFX item}**: ...

---

## Section 7: Common Corner Cases

[Cross-TCD corner cases — conditions that affect multiple TCDs under this TPF.]

| Corner Case | Affected TCDs | Expected Behavior |
...

**Coverage gap table (use when formal gap analysis has been done):**

After a gap analysis session, replace or extend the corner cases table with the full
5-column gap table. P1 (actionable) gaps belong here; accepted/inherent gaps go in §5.

| Gap ID | Gap | Current Coverage | Missing Tier | Recommended TC |
|--------|-----|-----------------|-------------|----------------|
| **G-N** | scenario | existing TC or `none` | FV / PV / PSS | new TC stub or `accepted` |

---

## Section 8: TCD Coverage Summary & References

### Child TCDs

| TCD ID | Title | Segment | TC Count |
...

### References

- [Feature HAS](url)
- [NWP PM MAS — feature section](url)
- [Relevant HSD](url)
```

---

## Step 4 — Generate Preview HTML

```powershell
# From repo root
python tools/html/generate_tpf_preview.py --tpf <TPF_ID> --force
# Output: tpf_description_output/TPF_{id}_{slug}_preview.html
```

Preview includes:
- Header bar with TPF ID, parent TP link, status, owner
- **Child TCDs panel** (live from HSD — always current count)
- 8 numbered sections from KB

---

## Step 5 — User Reviews

User checks:
- Section 2 (Design Details) — **full-stack cross-layer diagram present** (not only within-layer views); every layer has a tier claim in the Validation-Tier Layer Claim table; no unclaimed rows
- Section 2 (Design Details) — Interface & Register Matrix, Observability, and SKU/Config Distinctions landing zones populated (or explicitly marked `N/A — not applicable for this feature`)
- Section 3 (Validation Strategy) — references §2 Validation-Tier Layer Claim table by name
- Section 4 (Tier Coverage) — bug matrix and scenario coverage complete
- Section 8 — TCD table matches live children (generator fetches live from HSD)
- **Completeness diff** — every `###` heading removed from source TCD KBs appears in TPF §2 (verify using Lint B from Step 2b)

---

## Step 6 — TCD Update After Extraction

For each TCD whose Section 1 had diagrams extracted to TPF Section 2:

1. Open the TCD KB file
2. Remove the diagram blocks (ASCII / raw-html) from Section 1
3. Replace with a single reference line:
   ```markdown
   > **Architecture overview:** See [TPF {ID} — {Title}]({url}) §2 Design Details
   > for boot flow, {feature} mechanism, and frequency hierarchy.
   ```
4. Regenerate TCD preview: `python tools/html/generate_tcd_preview.py --tcd <ID> --force`
5. Push TCD to HSD only after TPF is live

---

## Step 7 — Push to HSD

```powershell
# Auto-detects HSD ID (16030762939) and subject (test_plan) from filename
python tools/hsd/push_preview.py tpf_description_output/TPF_{TPF_ID}_{slug}_preview.html

# Dry-run first if unsure
python tools/hsd/push_preview.py --dry-run tpf_description_output/TPF_{TPF_ID}_{slug}_preview.html
```

Expected output:
```
  file    : tpf_description_output/TPF_{ID}_..._preview.html
  hsd_id  : {ID}  (https://hsdes.intel.com/appstore/article-one/#/{ID})
  subject : test_plan
  content : {N} chars
  result  : 200 OK
```

> **Never use temp `.py` files or inline Python in PowerShell heredocs.**
> PowerShell parses `<` as an operator even inside quoted strings.
> `push_preview.py` handles desc-box extraction, Kerberos auth, and subject routing internally.
> See also: `tools/hsd/hsd_update.py` for raw field updates (no desc-box extraction).

---

## KB File Naming Convention

| Artifact | Path pattern |
|----------|-------------|
| TPF KB cache | `KB/pm_tpf_kb/{tp_id}_{tp_slug}/TPF_{tpf_id}_{slug}.md` |
| Preview HTML | `tpf_description_output/TPF_{tpf_id}_{slug}_preview.html` |

**Parent folder naming:** Use the TP (parent of TPF) ID + slug, not the TPF ID.
Example: TPF `16030762939` lives under TP `16030762839_sst_speed_select_technology/`.

---

## Phoenix Alignment Checklist

| Phoenix §3.1 Requirement | TPF Section | Status |
|--------------------------|-------------|--------|
| Introduction | 1 — Feature Classification | ✅ |
| Scope and assumptions | 1 + 3 — Classification + Strategy | ✅ |
| Validation strategy highlights | 3 — Validation Strategy | ✅ |
| Design details (focus area) | 1 — Classification | ✅ |
| Block diagrams / state diagrams / flows | **2 — Design Details** | ✅ (extracted from TCDs) |
| Risks and dependencies | 5 — Risks & Dependencies | ✅ |
| DFX considerations | 6 — DFX | ✅ |
| Potential corner cases | 7 — Common Corner Cases | ✅ |

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Pushing TCD diagram removal before TPF is live | Always push TPF first; TCD update second |
| Diagram in TPF + same diagram in TCD | Extract means remove from TCD — do not keep duplicates |
| Wrong HSD subject for TPF PUT | Use `subject: test_plan` (TPF and TP share the same subject) |
| Child TCD table in Section 8 is stale | Generator fetches live children from HSD — table is always current; Section 8 KB text is for references only |
| No KB file → generator falls back to HSD-LIVE | Creates preview from raw HSD HTML (unstructured) — enrich KB first for structured output |
| Using TCD regex extraction for TPF push | TPF regex `(.*?)</div>\s*</div>\s*</body>` works for TPF. TCD preview has deeper nesting — use index-based extraction for TCD (see `nwp-tcd-description` skill) |
| §5 is a flat bullet list after gap analysis | After a formal gap analysis, split §5 into "Active Risks" + "Accepted Coverage Limitations" table. Actionable gaps (candidate TC exists) stay in TCD §6 as *(TC TBD)*, NOT in TPF §5 |
| Coverage gap table mixes actionable + accepted gaps | Keep them separate: accepted/inherent gaps (no TC possible) → TPF §5 table; gaps with candidate TCs → TCD §6 bullets |
| **Duplicate `## Section N:` heading causes empty section** | When inserting a `### subsection` into an existing `## Section N:` block using `replace_string_in_file`, the `newString` must **NOT** repeat the `## Section N:` heading. Start `newString` at the first `### SubSection` line. Duplicate `## ` headings cause `parse_block()` to stop at the second one and return an empty block (rendered as "Not documented."). |
| `<!-- raw-html -->` diagram renders in preview but empty in HSD | Verify the `<!-- raw-html --> ... <!-- /raw-html -->` block is inside the correct `## Section N:` block (not orphaned before or after it). Run `parse_block(kb_text, 'Design Details')` and check `len(block)` before pushing. |
| **Full-stack diagram missing — only within-layer views present** | §2 must include one diagram showing all layers from OS/tool down to silicon. Boot-flow, mechanism diagrams, and frequency tables are within-layer views and do NOT substitute. Derive layer names from the feature's HAS/MAS; the template mandates the structure, the spec supplies the names. |
| **Validation-tier layer claim table missing from §2** | Required directly under the full-stack diagram. Every stack layer must be claimed by ≥1 tier. Unclaimed rows → flag in §5 Accepted Coverage Limitations. This is the sentence that justifies the TCD structure below the TPF; §3 must reference it by name. |
| **TCD content promoted but silently dropped** | Run Lint B (Step 2b): for each `###` heading removed from source TCD KB, confirm it exists in a TPF §2 landing zone. A redrawn "prettier" diagram may omit original panels — verify subsection count matches. || **§1 restates §2 layer responsibilities** | §1 should contain only: feature intro, gating mechanism (fuse/BIOS knob), and constants. If §1 has a table listing firmware agents + roles, it’s duplicating the §2 Full-Stack diagram. Apply the intra-document extraction rule: move the `Key Artifact` column (source file / FAS ownership) to a new `### Agent Source Ownership` table in §2; delete the rest. §2 then has layer + owner + where-to-look in one view. |