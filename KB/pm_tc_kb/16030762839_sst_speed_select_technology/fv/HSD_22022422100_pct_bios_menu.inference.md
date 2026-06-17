# HSD 22022422100: PCT - BIOS Menu

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
1. Enter BIOS Setup menu
2. Navigate to Advanced → Processor Configuration → SST/PCT section
3. Verify PCT-related knobs are present:
   - PCT Partition Count (0, 2, 4, 8 — default varies by SKU)
   - HP Cores Per Partition (1, 2 — default 1 or 2)
   - PCT Core Select Mode (Auto, Manual)
4. Verify default values match architecture spec
5. Toggle knobs and confirm changes persist across reset
6. Verify hidden/grayed knobs for non-PCT SKUs

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
