# TCD 16031169298 — PCT - DQ Rules

| Field | Value |
|-------|-------|
| **TCD ID** | [16031169298](https://hsdes.intel.com/appstore/article-one/#/16031169298) |
| **Title** | PCT - DQ Rules |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030762939 — [NWP PM] PCT (Priority Core Turbo)](https://hsdes.intel.com/appstore/article-one/#/16030762939) |
| **Sibling TCDs** | [22022420855](https://hsdes.intel.com/appstore/article-one/#/22022420855) — PCT - BIOS Enabling |
| | [16031169297](https://hsdes.intel.com/appstore/article-one/#/16031169297) — PCT - TPMI Runtime Control |
| | [22022420858](https://hsdes.intel.com/appstore/article-one/#/22022420858) — PCT - Functionality |
| | [16031169308](https://hsdes.intel.com/appstore/article-one/#/16031169308) — PCT - Negative / Boundary Validation |
| | [16030982802](https://hsdes.intel.com/appstore/article-one/#/16030982802) — PCT - DLCP (Die Level Cherry Picking) |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Architecture / Micro-architecture and Functionality

This TCD validates **FlexconPM DQ (Design Qualification) Rules** for PCT: a suite of silicon bring-up assertions that verify SST_TF_INFO register field values match the NWP spec after PrimeCode Phase 5 initialization. DQ compliance is a prerequisite for silicon qualification — any assertion failure indicates the part does not meet spec. Scope also includes the SST-PP × PCT mutual exclusion check.

> **Architecture overview:** See [TPF 16030762939 — PCT](https://hsdes.intel.com/appstore/article-one/#/16030762939) §2 Design Details for the full-stack PCT architecture, CLOS mechanism, ordered throttle, and frequency hierarchy.
>
> **Scope boundary:** Negative path validation (invalid BIOS configs, invalid TPMI writes, boundary conditions) is covered by sibling TCD [16031169308 — PCT - Negative / Boundary Validation](https://hsdes.intel.com/appstore/article-one/#/16031169308).

### NWP-Specific Constants

| Parameter | Value | Relevance to this TCD |
|-----------|-------|----------------------|
| `max_partitions` | 4 (SST_TF_INFO_8.NUM_CORE_0 / MAX_LPIDS) | DQ rule validates correct partition count derivation |
| Total cores | 96 (2 CBBs × 48) | Core count consistency check in SST_TF_INFO_1.NUM_CORE_x |
| `SST_TF_INFO_10.PCT_Module_Mask` | DLCP fuse; `0` on non-DLCP parts | DQ rule must verify fuse-to-register correctness |
| FlexconPM suite | SST-TF DQ assertions | Validates SST_TF_INFO_* field values against NWP spec |
| SST-PP status | ZBB'd on NWP ([HSD 22021155414](https://hsdes.intel.com/appstore/article/#/22021155414)) | SST-PP × PCT mutual exclusion → SST-PP must be disabled |

### TC Coverage Map

| TC | Title | Scope | Status |
|----|-------|-------|--------|
| [22022422118](https://hsdes.intel.com/appstore/article-one/#/22022422118) | PCT - DQ Rules (FlexconPM) | FlexconPM compliance assertions on real silicon (FV) | open |
| [16030715682](https://hsdes.intel.com/appstore/article-one/#/16030715682) | [PSS] PCT - DQ Rules (FlexconPM) | DQ assertions in PSS model environment | open |
| [22022422110](https://hsdes.intel.com/appstore/article-one/#/22022422110) | PCT - SST-PP x PCT Basic Checks | SST-PP × PCT mutual exclusion verification | rejected |

---

## Section 2: Interfaces and Protocols

| Register / Interface | Access | Role in DQ Validation |
|---------------------|--------|-----------------------|
| `SST_TF_INFO_0` (TPMI) | RO | `FEATURE_SUPPORTED` must be 1 when SST-TF enabled; `LP_CLIP_RATIO_0..5` must be valid, non-increasing with higher Cdyn levels |
| `SST_TF_INFO_1` (TPMI) | RO | `NUM_CORE_0..7`: HP core counts per bucket; must be non-decreasing order; last bucket = module core count |
| `SST_TF_INFO_2..7` (TPMI) | RO | `RATIO_0..7`: Turbo ratio limits per bucket per Cdyn level; must be non-increasing; HP max turbo ≤ max TRL for same Cdyn |
| `SST_TF_INFO_8` (TPMI) | RO | `NUM_CORE_0..2`: HP core counts (OKS/DMR/NWP generation); partition count derivation |
| `SST_TF_INFO_9` (TPMI) | RO | `RATIO_0..5`: All-cores-active turbo ratios per Cdyn level |
| `SST_TF_INFO_10` (TPMI) | RO | `QUALIFIED_MODULE_MASK` (PCT_Module_Mask): DLCP — which modules are qualified for HP operation; `0` on non-DLCP parts |
| FlexconPM assertion framework | Tool | Reads TPMI registers and asserts field values match DQ spec requirements |

---

## Section 3: Reset, Power, and Clocking

- **Test timing:** DQ checks execute after PrimeCode Phase 5 (SST_TF_INFO_* registers populated from fuses and immutable post-reset) and after BIOS CPL3 PCT configuration completes. Tests run at steady-state OS/FV level.
- SST_TF_INFO_* registers are **read-only after Phase 5** — DQ checks read, never write.
- No power-state or clocking dependencies — DQ assertions are static register value checks against spec-expected ranges.

---

## Section 4: Programming Model

### FlexconPM DQ Assertion Categories (HAS-derived)

FlexconPM reads SST_TF_INFO TPMI registers and asserts spec compliance across these categories:

**PCT-Specific DQ Rules:**

| Rule | Assertion | Source |
|------|-----------|--------|
| PCT requires SST-TF | If PCT enabled → `SST_TF_INFO_0.FEATURE_SUPPORTED = 1` and all SST-TF fuses valid | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |
| PCT × SST-BF mutually exclusive | If PCT enabled → SST-BF disabled | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |
| PCT × FCT mutually exclusive | If PCT enabled → FCT disabled | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |

**SST-TF Fuse Validity Rules:**

| Rule | Assertion | Source |
|------|-----------|--------|
| All fuses valid | All SST-TF fuses (LP clip, numcore, ratios) must have valid non-zero values for all enabled PP levels | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| LP clip monotonicity | `LP_CLIP_RATIO_x` must be non-increasing with higher Cdyn levels | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| Core count ordering | `NUM_CORE_x` must be non-decreasing across buckets; last bucket = module core count | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| Ratio ordering | `RATIO_x` must be non-increasing across buckets for same core count | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| HP ratio ceiling | SST-TF HP max turbo ratios ≤ max TRL ratios for each Cdyn level | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| Iccmax ordering | Iccmax must be in decreasing order across PP levels | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| Unsupported features zeroed | If feature not supported, all related fields must be 0 | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |

**DLCP-Specific Rule:**

| Rule | Assertion | Source |
|------|-----------|--------|
| Module mask correctness | `SST_TF_INFO_10.QUALIFIED_MODULE_MASK` must be `1` for qualified modules, `0` otherwise; `0` on non-DLCP parts | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |

### SST-PP × PCT Mutual Exclusion (TC 22022422110 — rejected)

TC 22022422110 validated that SST-PP and PCT cannot be co-enabled. This TC was **rejected** because SST-PP is ZBB'd on NWP ([HSD 22021155414](https://hsdes.intel.com/appstore/article/#/22021155414)), making the cross-product scenario untestable. The DQ rule (PCT × SST-BF/FCT mutual exclusion) is still validated via FlexconPM assertions in TC 22022422118.

---

## Section 5: Operational Behavior

### Pass/Fail Bar

| Scenario | Pass Criterion | TC |
|----------|----------------|-----|
| FlexconPM PCT DQ assertions (FV silicon) | All PCT-specific and SST-TF fuse validity DQ assertions **PASS**; zero violations; SST_TF_INFO_* register values match spec-expected ranges for the NWP SKU | [22022422118](https://hsdes.intel.com/appstore/article-one/#/22022422118) |
| FlexconPM PCT DQ assertions (PSS model) | All PCT DQ assertions pass in PSS model environment; model-gap assertions flagged as known model limitations | [16030715682](https://hsdes.intel.com/appstore/article-one/#/16030715682) |
| Mutual exclusion (PCT vs SST-BF/FCT) | FlexconPM asserts SST-BF and FCT are disabled when PCT is enabled; assertion passes | [22022422118](https://hsdes.intel.com/appstore/article-one/#/22022422118) |
| LP clip monotonicity | `LP_CLIP_RATIO_0 ≥ LP_CLIP_RATIO_1 ≥ ... ≥ LP_CLIP_RATIO_5` for each enabled PP level | [22022422118](https://hsdes.intel.com/appstore/article-one/#/22022422118) |
| HP ratio ceiling | SST-TF HP max turbo ratios ≤ max TRL ratios for each Cdyn level | [22022422118](https://hsdes.intel.com/appstore/article-one/#/22022422118) |
| Core count ordering | `NUM_CORE_0 ≤ NUM_CORE_1 ≤ ... ≤ NUM_CORE_7`; last bucket = module core count | [22022422118](https://hsdes.intel.com/appstore/article-one/#/22022422118) |

**Failure mode:** Any FlexconPM assertion failure = DQ bug (silicon fuse programming does not meet spec). This blocks silicon qualification.

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| **DLCP mask on non-DLCP SKU** | `SST_TF_INFO_10.QUALIFIED_MODULE_MASK` must be `0` on non-DLCP parts; any non-zero value = fuse error | ⚠️ Covered within FlexconPM suite (TC 22022422118) but not a standalone assertion target | Confirm FlexconPM explicitly checks mask=0 on non-DLCP |
| **All-zero fuse values on SST-TF-enabled SKU** | If SST-TF feature_supported=1 but all ratio/clip fuses are zero = invalid | ✅ Covered by FlexconPM "all fuses must be valid" rule (TC 22022422118) | No action |
| **SST-PP × PCT on NWP** | SST-PP ZBB'd — mutual exclusion untestable | ✅ TC 22022422110 correctly rejected | No action |
| **LP_CLIP_RATIO equals HP ratio** | Edge case where LP and HP cores would run at same frequency = PCT ineffective | ⚠️ Not a DQ failure per spec but indicates a validation gap | Note as "not-DQ" — validated by Functionality TCD |
| **PSS model gap in DQ assertions** | Simics model may not enforce all fuse values at RTL precision; PSS DQ may pass when silicon would fail | ⚠️ TC 16030715682 runs PSS DQ but model gaps are known | FV TC 22022422118 is ground truth; document known PSS gaps |
| **Multi-PP-level DQ consistency** | DQ rules must be validated across all enabled PP levels, not just default | ⚠️ Single-PP-level (NWP has no SST-PP switching) | Confirm FlexconPM iterates all PP levels even when only 1 active |

---

## Section 7: Security / Safety / Policy

- FlexconPM DQ rules enforce silicon correctness at bring-up — a DQ failure indicates the silicon does not meet spec and blocks qualification.
- DQ assertions are read-only: they read SST_TF_INFO_* registers and compare against expected values. No write operations to silicon.
- `SST_TF_INFO_*` registers are read-only post Phase 5 — any mechanism that could modify them post-reset would be a security concern.

---

## Section 8: References

- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — DQ requirements, mutual exclusion rules, DLCP module mask
- [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST_TF_INFO register fields, fuse validity rules, ratio/core-count ordering invariants
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PCT scope, FlexconPM reference
- [TPF 16030762939 — PCT](https://hsdes.intel.com/appstore/article-one/#/16030762939) — Feature architecture
- Sibling TCD: [16031169308 — PCT - Negative / Boundary Validation](https://hsdes.intel.com/appstore/article-one/#/16031169308) — negative path and boundary condition coverage
- Co-Design HAS query (2026-07-18): FlexconPM DQ assertion specifics, SST_TF_INFO field validation rules