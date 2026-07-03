# Deep Analysis: PCT - DQ Rules (FlexconPM)

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422118 |
| **Title** | PCT - DQ Rules (FlexconPM) |
| **Date** | 2026-05-29 |
| **Version** | v2 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SST |
| **Sub-Feature** | PCT DQ validation -- FlexconPM rules for PCT_ENABLE, SST-TF, SST-BF, FCT constraints |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Segment** | FV |
| **Owner** | mmaltese |
| **Tags** | plc.feature.p1, PMSS_NWP_READINESS_CHECK |

---

## Test Case Intent

This test validates the **Design Qualification (DQ) rules** for PCT (Priority Core Turbo) fuse and configuration consistency using the FlexconPM framework. DQ rules are manufacturing quality gates that ensure fuse programming follows architectural constraints. The test reads fuse values and TPMI registers from the target silicon and verifies mutual exclusion, dependency, and ordering rules.

### Pre-Conditions

1. Silicon with PCT-capable SKU (PCT_ENABLE fused)
2. SST-TF enabled in BIOS (PCT Partition Count > 0)
3. FlexconPM framework installed with NWP configuration (NWPSV.ini)
4. PythonSV environment with namednodes access to TPMI SST registers

### Test Steps

1. Read PCT_ENABLE fuse value from CAPID registers
2. If PCT_ENABLE = Enabled:
   a. Verify SSTTF_ENABLE = Enabled (dependency rule)
   b. Verify SSTBF = Disabled (mutual exclusion)
   c. Verify FCT (SSTPP0_TURBO_MAX_3_IND) = Disabled (mutual exclusion)
   d. Verify PP 0 supports PCT if SKU supports PCT
3. Read TRL bucket configuration from SST_TF_INFO registers:
   a. Verify first TF TRL bucket NumCore = 4C or 8C
   b. Verify 2nd and 3rd TF TRL bucket NumCore > 8 cores (multiple of 4)
   c. Verify TF TRL Ratio of bucket 0 > bucket 1 > bucket 2 (non-increasing)
   d. Verify NumCore[i+1] >= NumCore[i] (non-decreasing core counts)
   e. Verify last bucket NumCore[7] = total cores in package
4. Read LP clip ratios from SST_TF_INFO_0:
   a. Verify LP clip ratios are non-increasing across CDYN levels
   b. Verify LP clip ratio >= P1_Lo
5. Report pass/fail for each DQ rule

### Pass / Fail Criteria

- **PASS**: All DQ rules satisfied -- PCT fuse consistency validated
- **FAIL**: Any DQ rule violation detected (dependency, mutex, ordering)

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test runs flexcon_pm.py DQ rules to validate PCT fuse and configuration consistency. The test is architecturally portable from DMR to NWP because:

1. **PCT is supported on NWP** -- one of only 2 SST features active (SST-TF + PCT). Confirmed via [HSD 14026595435](https://hsdes.intel.com/appstore/article/#/14026595435).
2. **DQ rules are architecture-invariant** -- the fuse dependency/mutex rules (PCT to SSTTF, PCT to SSTBF, PCT to FCT) are identical on DMR and NWP.
3. **Mutex rules trivially satisfied on NWP** -- SST-BF and SST-PP are ZBBd on NWP, so the SSTBF = Disabled and FCT = Disabled checks pass by default.
4. **Adaptation required**: Config file change from DMRSV.ini to NWPSV.ini to reflect NWP topology (2 CBBs x 48 cores, 96 total).

### DMR to NWP Delta Table

| Aspect | DMR | NWP | Impact on DQ Rules |
|--------|-----|-----|-------------------|
| CBB count | 4 CBBs x 32 cores = 128 | 2 CBBs x 48 cores = 96 | NumCore[7] (last bucket) = 96 on NWP vs 128 on DMR |
| PCT core count | 8 HP (configurable) | 8 HP across 4 partitions | No change to DQ rules |
| SST-BF | Active (can be enabled) | ZBBd (always disabled) | Mutex rule PCT-SSTBF trivially passes |
| SST-PP dynamic | Active | ZBBd | Mutex check with FCT simplified |
| FCT | Active (can be enabled) | ZBBd (always disabled) | Mutex rule PCT-FCT trivially passes |
| PCT Partition Count | Default 4 | Default 4 (24 cores/partition) | Same algorithm, different partition sizes |
| Config file | DMRSV.ini | NWPSV.ini | FlexconPM config adaptation needed |
| CAPID4.bit29 | Not used (DMR+) | Not used | PCT capability via partition count knob |
| TRL bucket NumCore[0] | 4C or 8C | 4C or 8C | Same constraint |
| DLCP | PCT_Module_Mask fuse | TBD -- manufacturing fused core masks | Verify SST_TF_INFO_10 populated |

---

## Section B: Interactions

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | BIOS | Read PCT_ENABLE fuse from CAPID registers at boot | CSR |
| 2 | BIOS | Read SSTTF_ENABLE, SSTBF, FCT fuse values | CSR |
| 3 | BIOS | Validate fuse DQ rules (PCT-SSTTF dependency, PCT-SSTBF mutex, PCT-FCT mutex) | Internal |
| 4 | PrimeCode (NIO) | Read SST_TF_CONFIG fuses at reset Phase 5 -- populate TRL buckets and LP clip ratios into TPMI SRAM | Fuse to TPMI |
| 5 | PrimeCode (NIO) | Write SST_TF_INFO_0 (LP clip ratios), SST_TF_INFO_2 (HP TRL ratios), SST_TF_INFO_10 (DLCP mask) to TPMI | TPMI MMIO |
| 6 | BIOS | Read SST_TF_INFO registers; program SST_CLOS_CONFIG/ASSOC for HP and LP cores | TPMI MMIO |
| 7 | OS/Test | Launch FlexconPM DQ validation script | Test logic |
| 8 | OS/Test | Read PCT_ENABLE fuse via PythonSV namednodes | CSR |
| 9 | OS/Test | Read SSTTF_ENABLE, SSTBF, FCT fuse values via namednodes | CSR |
| 10 | OS/Test | Verify dependency: PCT_ENABLE=1 implies SSTTF_ENABLE=1 | Test logic |
| 11 | OS/Test | Verify mutex: PCT_ENABLE=1 implies SSTBF=0 | Test logic |
| 12 | OS/Test | Verify mutex: PCT_ENABLE=1 implies FCT=0 | Test logic |
| 13 | OS/Test | Read SST_TF_INFO_2 TRL bucket NumCore and Ratio arrays via TPMI | TPMI MMIO |
| 14 | OS/Test | Verify NumCore[0] = 4C or 8C; NumCore[i+1] >= NumCore[i]; Ratio[i] >= Ratio[i+1] | Test logic |
| 15 | OS/Test | Read SST_TF_INFO_0 LP clip ratios per CDYN level | TPMI MMIO |
| 16 | OS/Test | Verify LP clip ratios non-increasing across CDYN; LP clip >= P1_Lo | Test logic |
| 17 | OS/Test | Report pass/fail for all DQ rules | Test logic |

### Sequence Data

| # | From | To | Message | Interface |
|---|------|----|---------|-----------|
| 1 | BIOS | Fuse Controller | Read PCT_ENABLE, SSTTF_ENABLE, SSTBF, FCT fuse values | CSR |
| 2 | BIOS | BIOS | Validate fuse DQ dependency/mutex rules (boot-time check) | Internal |
| 3 | PrimeCode (NIO) | Fuse Controller | Read SST_TF_CONFIG fuse arrays (TRL ratios, NumCore, LP clip) | CSR |
| 4 | PrimeCode (NIO) | TPMI SRAM | Write SST_TF_INFO_0/2/10 registers from fuse values | TPMI MMIO |
| 5 | BIOS | TPMI SRAM | Read SST_TF_INFO; program SST_CLOS_CONFIG[0] (HP) and SST_CLOS_CONFIG[3] (LP) | TPMI MMIO |
| 6 | BIOS | TPMI SRAM | Write SST_CLOS_ASSOC -- assign HP cores to CLOS[0], LP cores to CLOS[3] | TPMI MMIO |
| 7 | BIOS | TPMI SRAM | Write SST_PP_CONTROL.feature_state[1] = 1 (activate SST-TF/PCT) | TPMI MMIO |
| 8 | OS/Test | Fuse Controller | Read PCT_ENABLE via namednodes sv.socket0.getbypath('capid.capid4') | CSR |
| 9 | OS/Test | Fuse Controller | Read SSTTF_ENABLE, SSTBF, FCT fuse values | CSR |
| 10 | OS/Test | TPMI SRAM | Read SST_TF_INFO_2 (TRL bucket ratios and NumCore) | TPMI MMIO |
| 11 | OS/Test | TPMI SRAM | Read SST_TF_INFO_0 (LP clip ratios per CDYN level) | TPMI MMIO |
| 12 | OS/Test | OS/Test | Evaluate all DQ rules: dependency, mutex, ordering, clip constraints | Test logic |
| 13 | OS/Test | OS/Test | Report pass/fail verdict per rule | Test logic |

---

## Section C: Interface Coverage Assessment

| Interface | Type | Covered by TC | Read/Write | NWP Validation Notes |
|-----------|------|---------------|------------|---------------------|
| PCT_ENABLE fuse (CAPID4.bit29) | CSR/Fuse | Yes | Read | GNR-specific; NWP uses partition count knob -- verify fuse still readable |
| SSTTF_ENABLE fuse | CSR/Fuse | Yes | Read | Dependency check: PCT requires SSTTF |
| SSTBF fuse | CSR/Fuse | Yes | Read | ZBB on NWP -- always 0; mutex trivially satisfied |
| FCT (SSTPP0_TURBO_MAX_3_IND) fuse | CSR/Fuse | Yes | Read | ZBB on NWP -- always 0; mutex trivially satisfied |
| SST_TF_INFO_2 (HP TRL ratios) | TPMI MMIO | Yes | Read | Bucket ratio ordering validated |
| SST_TF_INFO_2 (NumCore per bucket) | TPMI MMIO | Yes | Read | Bucket 0 = 4C/8C; non-decreasing |
| SST_TF_INFO_0 (LP clip ratios) | TPMI MMIO | Yes | Read | Non-increasing across CDYN levels |
| SST_TF_INFO_10 (DLCP mask) | TPMI MMIO | Partial | Read | DLCP on NWP TBD -- check if register is populated |
| SST_CLOS_CONFIG[0] (HP bounds) | TPMI MMIO | Not in DQ | Read | Verified by separate PCT activation TCs |
| SST_CLOS_CONFIG[3] (LP bounds) | TPMI MMIO | Not in DQ | Read | Verified by separate PCT activation TCs |
| SST_CLOS_ASSOC (per-core CLOS) | TPMI MMIO | Not in DQ | Read | Verified by PCT core assignment TCs |
| MSR 0x1AD (TRL override) | MSR | Not in DQ | Read | Verified by PCT runtime TCs |
| IA32_HWP_CAPABILITIES (0x771) | MSR | Not in DQ | Read | Verified by PCT HP/LP differentiation TCs |

### Coverage Gaps

1. **DLCP (SST_TF_INFO_10)**: DQ rules do not explicitly validate PCT_Module_Mask fuse consistency against SST_TF_INFO_10. Consider adding a DLCP mask validation DQ rule if NWP uses DLCP.
2. **PP 0 PCT support check**: HSD description mentions PP 0 must support PCT if the SKU supports PCT -- verify FlexconPM script checks this.

---

## Section D: NWP Specification References

| Document | Section | Relevance |
|----------|---------|-----------|
| [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) | DQ Rules, Fuse Dependencies | Primary source for PCT enable/disable qualification rules, mutex constraints, TRL bucket rules |
| [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) | SST-TF Architecture, CLOS | SST-TF mechanism underlying PCT; TPMI register definitions |
| [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | SST Feature Support | NWP SST scope: SST-TF (PCT) active; SST-PP, SST-CP, SST-BF, HGS ZBBd |
| [DMR Overview HAS](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/DMR_Overview_HAS.html) | CBB Feature List | PCT as distinct feature item (HSD 14023051596) |
| [HSD 14026595435](https://hsdes.intel.com/appstore/article/#/14026595435) | NWP PCT CCB | NWP: 8 HP cores, 4 partitions, 4.4 GHz target (POR-1) |
| [HSD 22021155414](https://hsdes.intel.com/appstore/article/#/22021155414) | NWP SST ZBB | SST-PP, SST-CP, SST-BF, HGS ZBBd on NWP |

---

## Section E: Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| FlexconPM NWPSV.ini not yet available or incomplete | Medium | High -- test cannot run without proper NWP config | Pre-check: verify NWPSV.ini exists with correct NWP topology (2 CBBs, 96 cores); fall back to manual register reads if FlexconPM blocked |
| NWP TRL bucket sizes differ from DMR assumptions | Low | Medium -- DQ rule thresholds (4C/8C for bucket 0) may need update for 48-core CBBs | Verify TRL bucket definitions from NWP fuse spec; 4C/8C constraint is per-bucket, not per-die |
| DLCP not implemented on NWP | Medium | Low -- DQ test may skip SST_TF_INFO_10 check; not a failure | Add conditional: if SST_TF_INFO_10 is zero/unpopulated, skip DLCP DQ rules and log warning |
| Mutex rules trivially pass (SST-BF/FCT always disabled) | N/A | Low -- reduced test coverage value for mutex rules | Accept: DQ rules still validate the fuse encoding is correct even when ZBBd features are disabled |
| Vrel risk causes PCT fallback to legacy SST-TF | Low | Medium -- PCT DQ rules still apply to SST-TF fuse programming | Monitor CCB HSD 14026595435 for Vrel status updates |
| LP clip ratio not yet confirmed for NWP SKU | Medium | Medium -- test may fail if LP clip value is unexpected | Obtain NWP-specific LP clip ratio from BIOS FAS or TPMI dump before running DQ validation |

---

## Section F: Recommendations

1. **ADOPT with adaptation**: Change FlexconPM config from DMRSV.ini to NWPSV.ini to reflect NWP topology (2 CBBs x 48 cores = 96 total). Verify config file exists and contains correct core/die topology.

2. **Verify TRL bucket constraints**: Confirm NWP fuse programming uses the same TRL bucket NumCore rules (first bucket = 4C or 8C). NWP has 48 cores per CBB (vs 32 on DMR) -- ensure NumCore[7] = 96 (package total) or 48 (per-die total) depending on scope.

3. **Add DLCP conditional check**: If NWP uses DLCP (PCT_Module_Mask fuse), add DQ rule for SST_TF_INFO_10 consistency. If DLCP is not used, skip with logged warning rather than failing.

4. **Confirm LP clip ratio**: Obtain NWP SKU-specific LP clip ratio from BIOS FAS or TPMI register dump. Current expectation: LP clip >= P1_Lo (fused per SKU via SST_TF_CONFIG).

5. **Priority**: Medium -- plc.feature.p1 tag; DQ rules are a manufacturing quality gate for PCT SKU configuration. Run early in NWP bring-up to catch fuse programming errors before PCT activation testing.

6. **Dependency**: This TC should run before PCT activation tests (CLOS programming, HP/LP frequency verification) to ensure fuse foundation is correct.
