# Deep Analysis: PCT - BIOS Menu

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422100](https://hsdes.intel.com/appstore/article-one/#/22022422100) |
| **Title** | PCT - BIOS Menu |
| **Date** | 2026-06-23 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SST |
| **Sub-Feature** | PCT — BIOS Setup knob visibility, defaults, and range validation |
| **Parent TCD** | [22022420855 — PCT - Enabling & Discovery](https://hsdes.intel.com/appstore/article-one/#/22022420855) |
| **NWP Disposition** | **Rejected** |
| **Val Environment** | virtual_platform |
| **Owner** | mps |
| **Tags** | plc.feature.p1, PMSS_NWP_READINESS_CHECK |

## Version History
- v1 (2026-05-29): Initial — sections A only
- v2 (2026-06-23): Full enrichment — all sections A-G, NWP BIOS knob analysis, rejection reason

---

## Test Case Intent

Verify that the BIOS Setup menu exposes correct PCT configuration knobs with proper defaults
and value ranges, as specified in PCT HAS Table 4. Specific checks:
- PCT knobs visible when `CAPID4.bit29=1` (SST-TF/PCT capable)
- PCT knobs hidden/grayed when `CAPID4.bit29=0`
- Correct defaults (PCT Enable, HP core count, core selection mode)
- Valid value ranges accepted; out-of-range rejected
- Knob values persist across reset

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP with BIOS exposing PCT knobs; CAPID4.bit29=1 |
| Access | BIOS Setup menu access (not UEFI shell) |
| SST-TF fused | PCT_Module_Mask fuse set (silicon must support PCT) |

### PCT BIOS Knobs (from PCT HAS Table 4)

| Knob Name | Options | Default | Validation Rule |
|-----------|---------|---------|-----------------|
| PCT Enable | Enable / Disable | Enable | If CAPID4.bit29=0 → skip PCT, hide all knobs |
| PCT Core Count | Auto / Manual | Auto | Auto=4 HP cores; Manual: min=4, max≤SST_TF_INFO_1.NUM_CORE_0, multiple of 4 |
| PCT Core Select | Auto / Manual | Auto | Auto=first core per partition; Manual: min=0, max<(cores per partition) |
| MSR 0x1AD override | (internal) | SST_TF_INFO_2.RATIO_0 | Must NOT be 0xFF ([HSD 14025997048](https://hsdes.intel.com/appstore/article-one/#/14025997048)) |

### Pass / Fail Criteria

- **PASS**: All PCT knobs present when CAPID4.bit29=1; defaults match HAS; valid ranges accepted; knobs hidden when not capable
- **FAIL**: Missing knobs on capable platform; wrong defaults; invalid range accepted; knobs visible on incapable platform

---

## Section A: NWP Delta

**Disposition: Rejected** — BIOS Menu test is platform-specific (BIOS setup structure) and was found to not apply to NWP as written.

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| PCT capability | ✅ | ✅ PCT functional | PCT itself not ZBB'd |
| Standalone "PCT Enable" knob | ✅ Present | ⚠️ **Eliminated** — integrated into PCT Partition Count | Test fails if looking for separate Enable knob |
| PCT Partition Count default | 0 (disabled) | **4 on NWP** (auto-enabled when fused) | Default value check must use NWP value |
| HP Cores on NWP | Varies | **8** (2 per partition × 4 partitions on 96-core NWP) | Fixed count |
| SST-PP × PCT knob cross-product | Present | **N/A** — SST-PP ZBB'd on NWP | Remove PP-related knob verification |
| DLCP knobs | May be exposed | **Not applicable** on NWP (DLCP-specific) | Skip DLCP knob check |
| CBB topology knobs | 4 CBBs × 32 cores | 2 CBBs × 48 cores | Partition algorithm differs |

### Rejection Reason Analysis

The HSD is marked rejected. Most likely reasons:
1. **SST-PP cross-product knobs**: Original test likely verifies BIOS knobs combining PCT + SST-PP levels. SST-PP is ZBB'd on NWP.
2. **"PCT Enable" knob eliminated**: NWP BIOS may not have a standalone PCT Enable knob — it's integrated into Partition Count.
3. **DLCP-specific knobs**: Not applicable on NWP.
4. **BIOS setup path changed**: Exact menu path may differ between DMR and NWP BIOS.

PCT itself **is** functional on NWP — the BIOS menu test was rejected because the DMR-specific BIOS menu structure doesn't directly map.

---

## Section B: BIOS Knob Interactions

### Knob Dependency Chain

```
CAPID4.bit29 = 0 → Hide ALL PCT knobs → no programming
CAPID4.bit29 = 1 → Show PCT knobs:
  PCT Core Count (Auto=4 / Manual: 4..NUM_CORE_0, ×4)
       │
       └─ PCT Core Select (Auto=first core / Manual: 0..cores_per_partition-1)
              │
              └─ BIOS CPL3: programs SST_CLOS_ASSOC, SST_CLOS_CONFIG, MSR 0x1AD
```

### MSR 0x1AD Override

BIOS must program MSR 0x1AD = `SST_TF_INFO_2.RATIO_0` (HP TRL ratio), NOT 0xFF.
- [HSD 14025997048](https://hsdes.intel.com/appstore/article-one/#/14025997048): 0xFF is invalid on NWP

---

## Section C: Coverage

| Coverage Area | DMR Coverage | NWP Applicable | Gap |
|--------------|-------------|----------------|-----|
| PCT knob visibility (CAPID4 gating) | ✅ | ✅ | Path change only |
| PCT Core Count defaults and ranges | ✅ | ⚠️ Default=4 on NWP | Update expected default |
| PCT Core Select mode | ✅ | ✅ | No change |
| Standalone "PCT Enable" knob | ✅ | ❌ Eliminated on NWP | Remove from test |
| SST-PP × PCT cross-product knobs | ✅ | ❌ SST-PP ZBB'd | Remove |
| DLCP knobs | ✅ | ❌ Not on NWP | Remove |
| MSR 0x1AD override validation | ✅ | ✅ | Same rule (not 0xFF) |

---

## Section D: Spec Refs

| Reference | Link |
|-----------|------|
| PCT HAS Table 4 (BIOS knobs) | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |
| NWP PM MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |
| MSR 0x1AD 0xFF bug | [HSD 14025997048](https://hsdes.intel.com/appstore/article-one/#/14025997048) |
| PCT KB article | [KB/pm_features/sst/pct.md](../../../pm_features/sst/pct.md) |

---

## Section E: Risk Assessment

| # | Risk | Severity | Notes |
|---|------|----------|-------|
| 1 | "PCT Enable" standalone knob absent on NWP BIOS | High | NWP integrates it into Partition Count |
| 2 | SST-PP cross-product knobs in test — SST-PP ZBB'd | High | Causes test failure on NWP |
| 3 | PCT Partition Count default = 4 on NWP (not 0) | Medium | Expected default differs from DMR |
| 4 | DLCP knob checks fail (not present on NWP) | Low | Remove DLCP from test scope |
| 5 | MSR 0x1AD 0xFF — NWP BIOS must use RATIO_0 | High | Validate explicitly; 0xFF causes issues |

---

## Section F: Recommendations

**Rejected — BIOS Menu test requires significant rewrite for NWP.**

To re-open for NWP:
1. Remove "PCT Enable" standalone knob check (integrated into Partition Count on NWP)
2. Remove SST-PP × PCT cross-product knob checks (SST-PP ZBB'd)
3. Remove DLCP knob checks (not applicable on NWP)
4. Update PCT Core Count default: DMR=0 → NWP=4
5. Validate MSR 0x1AD = `SST_TF_INFO_2.RATIO_0` (not 0xFF, per HSD 14025997048)
6. Update BIOS menu navigation path for NWP BIOS structure

---

## Section G: PSS Grading

| Sl No | Dimension | Value | Rationale |
|-------|-----------|-------|-----------|
| 1 | NWP Delta | Yes | BIOS knob structure changed; SST-PP cross-product removed; default values differ |
| 2 | Applicable NWP | **Partial (needs rewrite)** | PCT functional; BIOS test requires adaptation before it can run |
| 3 | PSS Environment | VP (after rewrite) | BIOS setup menu access needed |
| 4 | Silicon Only | No | VP can exercise BIOS menu |
| 5 | Test Content | DMR_M | Medium adaptation: remove 3 knob categories, update defaults |
| 6 | OS | BIOS | BIOS setup menu (pre-OS) |

### Verdict

**Rejected — BIOS knob structure changed.** PCT feature is functional on NWP but the DMR-specific BIOS menu test fails due to: (1) eliminated PCT Enable knob, (2) SST-PP cross-product knobs (SST-PP ZBB'd), (3) DLCP knobs not present. Rewrite required before re-opening.


> **Version**: v1
> **Generated**: 2026-05-29
> **HSD Status**: rejected (zbb)
> **Feature**: SST / PCT (Priority Core Turbo)
> **Family**: Newport
> **Val Environment**: virtual_platform

---

## Test Case

### Test Intent

This test validates **PCT BIOS Setup Knobs** — verifying that the BIOS menu exposes correct PCT configuration options with proper defaults and ranges. The test inspects BIOS menu structure for PCT-related settings and confirms they match architecture specification (table 4 from PCT HAS).

### Pre-Conditions
1. Platform boots to BIOS Setup menu
2. SST-TF capability is present (PCT is built on SST-TF)
3. PCT fuses are enabled (PCT_ENABLE, PCT_Module_Mask)

### Test Steps (Inferred from TCD)

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Enter BIOS Setup menu on NWP platform with PCT capability (CAPID4.bit29=1) | BIOS Setup menu accessible; no hang | BIOS hang or inaccessible |
| 2 | Navigate to PCT/SST knob section; verify **PCT Partition Count** knob is present (replaces standalone PCT Enable) | PCT Partition Count knob visible with options 0 / 2 / 4; default = 4 | Knob absent or default != 4 |
| 3 | Verify **PCT Core Selection** knob is present with Auto/Manual options; default = Auto | Knob present; default = Auto | Knob absent or wrong default |
| 4 | Set PCT Partition Count to a non-default value; save and reboot | Setting persists after reboot; TPMI SST_CLOS_ASSOC reflects new HP count | Setting reverts or TPMI mismatch |
| 5 | Verify that SST-PP and DLCP cross-product knobs are absent (ZBB'd on NWP) | No SST-PP × PCT knob; no DLCP knob in menu | Stale DMR knobs present |
| 6 | Set PCT Partition Count = 0 (disabled); verify PCT inactive after reboot | PCT disabled; SST_CP_CONTROL.sst_cp_enable = 0 | PCT still active |

> **NWP note**: Steps are provided as a reference for when this TC is re-opened after rewrite. Currently rejected because DMR-specific knob structure doesn't map to NWP BIOS.

### Pass/Fail Criteria
- **Pass**: All PCT BIOS knobs present, defaults match spec, values persist
- **Fail**: Missing knobs, incorrect defaults, or values don't persist

---

## Section A: NWP Architecture Delta

### Disposition: ⚠️ Modify (update for NWP BIOS structure)

**Important**: PCT is **supported on NWP** (1 of only 2 active SST features). However, the **BIOS menu structure has evolved** from DMR, requiring test modification.

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| PCT Enable knob | Standalone knob | **Eliminated** — integrated into PCT Partition Count | Test must not look for separate "PCT Enable" |
| PCT Partition Count | 0, 2, 4, 8 | 0 (disabled), 2, 4 (default) | Default is 4 on NWP; verify correct range |
| HP Cores total | 4 or 8 | 8 (2 per partition × 4 partitions) | Fixed HP count on NWP |
| PCT + SST-PP interaction | Cross-product with PP levels | **N/A — SST-PP is ZBB'd** | Remove PP-dependent knob verification |
| CBB topology | 4 CBBs × 32 cores | 2 CBBs × 48 cores | Partition algorithm differs |

### HSD Status Analysis

The HSD is marked `rejected.zbb` but **PCT itself is NOT ZBB'd on NWP**. The rejection likely relates to:

1. **SST-PP related knobs**: The original BIOS menu test may verify PP level + PCT cross-product configurations (SST-PP IS ZBB'd)
2. **Eliminated "PCT Enable" knob**: Test may fail when looking for a knob that no longer exists
3. **DLCP knobs**: Die Level Cherry Picking knobs may not be exposed on NWP

**Recommendation**: Update HSD status to reflect correct disposition — this test should be **Modified**, not rejected.

### NWP PCT BIOS Knobs (Expected)

| Knob Name | NWP Options | Default | Notes |
|-----------|-------------|---------|-------|
| PCT Partition Count | 0, 2, 4 | 4 | 0 = PCT disabled; replaces standalone "PCT Enable" |
| HP Cores Per Partition | 1, 2 | 2 | 8 HP cores total on NWP |
| PCT Core Select Mode | Auto | Auto | Manual mode TBD on NWP |
| SST-TF Enable | Enabled (via PCT) | Enabled | SST-TF is the underlying mechanism |

### DMR BIOS Knobs (Reference — may not all exist on NWP)

| Knob Name | DMR Options | DMR Default | NWP Status |
|-----------|-------------|-------------|------------|
| PCT Enable | Enable, Disable | Disable | **Eliminated** — use Partition Count = 0 |
| PCT Partition Count | 0, 2, 4, 8 | 0 | Modified range on NWP |
| SST-PP Level | 0, 1, 2, 3, 4 | 0 | **ZBB'd on NWP** — remove from test |
| SST-PP Lock | Lock, Unlock | Unlock | **ZBB'd on NWP** — remove from test |
| SST-BF Enable | Enable, Disable | Disable | **ZBB'd on NWP** — remove from test |

---

## Section B: Interactions

### Component Swimlane

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PCT BIOS Menu Validation Flow                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ Phase         │ BIOS           │ Fuses        │ TPMI          │ PCode       │
├───────────────┼────────────────┼──────────────┼───────────────┼─────────────┤
│ 1. Boot       │ Read PCT fuses │◄────────────│               │             │
│               │ (PCT_ENABLE,   │ PCT_ENABLE   │               │             │
│               │  partition cap)│ PCT_Module_  │               │             │
│               │                │ Mask         │               │             │
├───────────────┼────────────────┼──────────────┼───────────────┼─────────────┤
│ 2. Setup Menu │ Present knobs  │              │               │             │
│               │ (PCT Partition │              │               │             │
│               │  Count, HP     │              │               │             │
│               │  Cores/Part)   │              │               │             │
├───────────────┼────────────────┼──────────────┼───────────────┼─────────────┤
│ 3. User       │ User selects   │              │               │             │
│    Config     │ PCT options    │              │               │             │
├───────────────┼────────────────┼──────────────┼───────────────┼─────────────┤
│ 4. Apply      │ Write SST-TF   │              │◄──────────────│             │
│               │ TPMI registers │              │ SST_CLOS_*    │             │
│               │                │              │ SST_PP_CTRL   │             │
├───────────────┼────────────────┼──────────────┼───────────────┼─────────────┤
│ 5. Runtime    │                │              │ Read TPMI    ─┼────────────►│
│               │                │              │               │ Enforce     │
│               │                │              │               │ CLOS limits │
└───────────────┴────────────────┴──────────────┴───────────────┴─────────────┘
```

### Sequence Table

| Step | Actor | Action | Target | Expected Result |
|------|-------|--------|--------|-----------------|
| 1 | Test Framework | Enter BIOS Setup | BIOS | Setup menu displayed |
| 2 | Test Framework | Navigate to PCT section | BIOS Menu | PCT section found under Processor Configuration |
| 3 | Test Framework | Enumerate PCT knobs | BIOS Menu | PCT Partition Count, HP Cores present |
| 4 | Test Framework | Verify defaults | BIOS Menu | Partition Count = 4, HP Cores = 2 |
| 5 | Test Framework | Change PCT Partition Count to 2 | BIOS Menu | Value accepted |
| 6 | Test Framework | Save and reset | BIOS | System resets |
| 7 | Test Framework | Re-enter Setup | BIOS | Menu displayed |
| 8 | Test Framework | Verify PCT Partition Count | BIOS Menu | Value persists as 2 |
| 9 | Test Framework | Restore default | BIOS Menu | Partition Count = 4 |

---

## Section C: Interface Coverage Assessment

| Interface | DMR Coverage | NWP Relevance | Gap |
|-----------|-------------|---------------|-----|
| BIOS PCT Enable knob | Verified | **Eliminated** | Update test to skip |
| BIOS PCT Partition Count | Verified | **Required** — key knob | ✅ Covered |
| BIOS HP Cores Per Partition | Verified | **Required** | ✅ Covered |
| BIOS SST-PP Level | Verified | **ZBB'd** — remove | Update test to skip |
| BIOS SST-PP Lock | Verified | **ZBB'd** — remove | Update test to skip |
| BIOS SST-BF Enable | Verified | **ZBB'd** — remove | Update test to skip |
| TPMI SST_PP_CONTROL readback | Verified | Partial (TF only) | Update expected values |

### Coverage Gaps

1. **NWP-specific partition algorithm**: 2 CBBs × 48 cores = 96 cores. Verify partition boundaries differ from DMR (4 CBBs × 32 cores).
2. **DLCP knob absence**: Confirm Die Level Cherry Picking knobs are hidden or absent on NWP.
3. **Negative: PP knobs must be hidden**: When SST-PP is ZBB'd, verify PP-related knobs are not exposed.

---

## Section D: NWP Specification References

| Document | Section | Relevance |
|----------|---------|-----------|
| [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) | Table 4: PCT BIOS Setup Knobs | Primary reference for knob names, options, defaults |
| [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) | BIOS Interface | SST-TF/CP TPMI registers |
| [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | SST-TF (PCT profile) | NWP scope: only PCT active |
| [HSD 14026595435](https://hsdes.intel.com/appstore/article/#/14026595435) | NWP PCT CCB | 8 HP cores, 4.4 GHz target |
| [HSD 22021155414](https://hsdes.intel.com/appstore/article/#/22021155414) | NWP SST ZBB | SST-PP, SST-CP, SST-BF, HGS ZBB'd |

---

## Section E: NWP Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Test fails looking for eliminated "PCT Enable" knob | High | Medium | Update test to use PCT Partition Count = 0 for disable |
| Test verifies ZBB'd SST-PP knobs | High | Medium | Remove SST-PP knob verification steps |
| BIOS may hide PCT section entirely if fuses not set | Medium | High | Verify PCT_ENABLE fuse on test unit |
| Partition algorithm produces different core mapping | Medium | Medium | Update expected partition boundaries for 2 CBBs |
| DLCP mode not available on NWP | Low | Low | Skip DLCP-specific knob verification |

---

## Section F: Recommendations

### Modification Checklist

1. **Update HSD status**: Change from `rejected.zbb` to `open` with disposition `Modify` — PCT IS supported on NWP
2. **Remove PCT Enable verification**: The standalone "PCT Enable" knob is eliminated on NWP — use PCT Partition Count = 0 to disable
3. **Remove SST-PP knob verification**: All SST-PP related knobs (Level, Lock, etc.) are ZBB'd on NWP
4. **Remove SST-BF/HGS knob verification**: Both are ZBB'd on NWP
5. **Update expected defaults**:
   - PCT Partition Count: 4 (not 0)
   - HP Cores Per Partition: 2
   - Total HP Cores: 8
6. **Update config file**: Change `runPmx.py -x dmr.xml` → `runPmx.py -x nwp.xml`
7. **Add negative verification**: Confirm ZBB'd knobs are hidden/grayed

### Negative Test Derivation (ZBB'd Features)

Although PCT is supported, the ZBB'd SST features provide negative test opportunities:

| Negative Test | Description | Expected Result |
|---------------|-------------|-----------------|
| SST-PP knobs hidden | Verify SST-PP Level, SST-PP Lock not visible in BIOS | Knobs not present |
| SST-BF knobs hidden | Verify SST-BF Enable not visible | Knob not present |
| HGS knobs hidden | Verify HGS-related knobs not visible | Knobs not present |
| PCT + PP cross-product blocked | Attempt to configure PCT with non-zero PP level | Operation blocked or no effect |

---

## User Notes

*(Add refinement notes here)*

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1 | 2026-05-29 | Initial enrichment — disposition Modify, PCT supported but BIOS structure changed |
