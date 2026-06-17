# Deep Analysis: SST-TF - Verify Dynamic Enable/Disable via TPMI

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422201 |
| **Title** | SST-TF - Verify dynamic enable/disable via TPMI |
| **Date** | 2026-05-29 |
| **Version** | v2 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SST |
| **Sub-Feature** | SST-TF dynamic enable/disable via TPMI sst_pp_control.feature_state[bit 1] |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Test Case

### Intent

Verify that SST-TF can be dynamically enabled and disabled at runtime by writing to TPMI field `sst_pp_control.feature_state[bit 1]`. The test validates the complete enable/disable flow including: feature availability check per PP level, CLOS dependency enforcement, error type reporting when prerequisites are not met, and symmetric disable-after-enable behavior.

### Pre-Conditions

- SVOS booted with SST-TF capable SKU
- BIOS SST knobs at default (TF not force-disabled)
- CLOS programming available (io_pm_qos_config.enable_clos accessible)
- For NWP: PP level fixed at PP0 (SST-PP is ZBB); SST-TF availability determined solely on PP0

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Verify TF is currently disabled: read `sst_pp_status.feature_state[bit 1]` | == 0x0 (TF off) |
| 2 | Enable TF: write `sst_pp_control.feature_state[bit 1] = 0x1` | Write accepted |
| 3 | Check TF availability on current PP level: read `sst_tf_info_0.feature_supported` | Reports TF support for PP0 |
| 4a | If PP does NOT support TF: verify `sst_pp_status.feature_error_type[2:0]` | == 0x1 (feature not supported by HW) |
| 4b | If PP does NOT support TF: verify `sst_pp_status.feature_state[bit 1]` | == 0x0 (TF was NOT enabled) |
| 5a | If PP supports TF AND `io_pm_qos_config.enable_clos == 0x1`: verify `sst_pp_status.feature_state[bit 1]` | == 0x1 (TF enabled successfully) |
| 5b | If PP supports TF AND `io_pm_qos_config.enable_clos == 0x0`: verify `sst_pp_status.feature_error_type[2:0]` | == 0x1 (dependency not met) |
| 5c | If PP supports TF AND CLOS disabled: verify `sst_pp_status.feature_state[bit 1]` | == 0x0 (TF not enabled due to CLOS dependency) |
| 6 | With TF enabled, disable TF: write `sst_pp_control.feature_state[bit 1] = 0x0` | Write accepted |
| 7 | Verify TF disabled: read `sst_pp_status.feature_state[bit 1]` | == 0x0 (TF off again) |

### Pass/Fail Criteria

- SST-TF enable/disable toggles correctly via TPMI write to `sst_pp_control.feature_state[bit 1]`
- Error type `0x1` correctly reported when PP level does not support TF or CLOS dependency not met
- Feature state in status register accurately reflects enable/disable outcome
- Symmetric behavior: enable then disable returns to original disabled state

---

## Section A: NWP Architecture Delta

### Disposition: Runnable_On_N-1

SST-TF dynamic enable/disable is **fully supported on NWP**. SST-TF is one of only 2 active SST features on NWP (SST-TF + PCT). The test requires a config adaptation: `dmr.xml` -> `nwp.xml` in the runPmx command. NWP is fixed at PP0 since SST-PP is ZBB, simplifying the test (no PP level iteration needed in static mode).

### DMR -> NWP Architecture Delta

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| SST-TF feature status | Active | Active | No change -- core flow identical |
| PP levels | Multiple PP levels active (SST-PP) | PP0 only (SST-PP ZBB) | NWP tests only PP0; no dynamic PP iteration needed |
| CBB count | 4 | 2 | SST-TF is per-package; no CBB-count dependency |
| Cores per CBB | 32 | 48 | HP/LP CLOS assignment covers more cores per CBB |
| Total cores | 128 | 96 | Affects HP/LP partition sizing |
| HP core count (PCT) | Variable per SKU | 8 HP cores (2 per partition x 4 partitions) | Fixed HP count on NWP; HP TRL bucket resolution uses 8 |
| CLOS dependency | io_pm_qos_config.enable_clos required for TF enable | Same -- CLOS required | No change |
| Error type reporting | sst_pp_status.feature_error_type[2:0] | Same register, same encoding | No change |
| Test config | `dmr.xml` | `nwp.xml` (runPmx config) | Config file change required |
| Test script | `sst_tf_validate.py` (validateTF.test_tpmi_control) | Same script, NWP-compatible | Verify NWP XML has correct TPMI offsets |
| DLCP interaction | Active | TBD -- SST_TF_INFO_10 validation pending | Confirm DLCP fuse state on NWP |

### NWP Simplification

Since SST-PP is ZBB on NWP, the test TC instruction "If in static PP, run this test only on the boot PP level. For full coverage, run this test in dynamic PP and iterate over all PP levels" simplifies to: **always run on PP0 only**. The dynamic PP iteration variant is not applicable on NWP.

---

## Section B: Interactions

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | BIOS | Programs SST_TF fuse-derived data into TPMI registers (SST_TF_INFO_0..8) at reset Phase 5 via PrimeCode sstTfInfoInit() | TPMI SRAM |
| 2 | BIOS | Programs CLOS assignments: HP cores -> CLOS[0], LP cores -> CLOS[3] via SST_CLOS_ASSOC registers | TPMI MMIO |
| 3 | BIOS | Optionally enables SST-TF at boot via SST_PP_CONTROL.feature_state[1] = 1 | TPMI MMIO |
| 4 | PCode (CBB) | SstManager slow loop detects feature_state[1] change; reads SST_PP_CONTROL via TPMI IO | TPMI IO |
| 5 | PCode (CBB) | SstManager sends HPM_MSG_COMPUTE_CLOS_CONFIG with HP module counts to TrlManager | HPM |
| 6 | PCode (CBB) | TrlManager loads HP CLOS TRL tables from IO_SST_TF_INFO_2..8 and LP CLOS from IO_SST_TF_INFO_0 | TPMI IO |
| 7 | PCode (CBB) | Workpoint calc applies per-CLOS frequency: HP cores get elevated TRL, LP cores get clipped ratio | Internal |
| 8 | OS/Test | Reads sst_pp_status.feature_state[1] to verify TF is currently disabled (== 0x0) | TPMI MMIO |
| 9 | OS/Test | Writes sst_pp_control.feature_state[1] = 0x1 to enable SST-TF | TPMI MMIO |
| 10 | PCode (CBB) | SstManager detects enable in slow loop; checks feature_supported and CLOS dependency | TPMI IO |
| 11 | PCode (CBB) | If valid: sets feature_state[1] = 1 in sst_pp_status; TrlManager reloads HP/LP tables | TPMI IO |
| 12 | PCode (CBB) | If invalid: sets feature_error_type[2:0] = 0x1; keeps feature_state[1] = 0 in status | TPMI IO |
| 13 | OS/Test | Reads sst_pp_status to verify enable outcome (feature_state and feature_error_type) | TPMI MMIO |
| 14 | OS/Test | Reads sst_tf_info_0.feature_supported to confirm PP0 supports TF | TPMI MMIO |
| 15 | OS/Test | Writes sst_pp_control.feature_state[1] = 0x0 to disable SST-TF | TPMI MMIO |
| 16 | PCode (CBB) | SstManager detects disable; TrlManager reverts to base SST-PP TRL (no HP/LP split) | TPMI IO |
| 17 | OS/Test | Reads sst_pp_status.feature_state[1] to verify TF disabled (== 0x0) | TPMI MMIO |

### Sequence Data

| # | From | To | Message | Interface |
|---|------|----|---------|-----------|
| 1 | BIOS | TPMI SRAM | Write SST_TF_INFO_0..8 (fuse-derived LP clip + HP TRL arrays) at reset Phase 5 | TPMI SRAM |
| 2 | BIOS | TPMI SRAM | Write SST_CLOS_ASSOC registers (HP->CLOS[0], LP->CLOS[3]) | TPMI MMIO |
| 3 | OS/Test | TPMI | Read sst_pp_status.feature_state[1] -- verify disabled (0x0) | TPMI MMIO |
| 4 | OS/Test | TPMI | Write sst_pp_control.feature_state[1] = 0x1 (enable request) | TPMI MMIO |
| 5 | PCode SstManager | TPMI IO | Read SST_PP_CONTROL -- detect feature_state[1] change (slow loop) | TPMI IO |
| 6 | PCode SstManager | TPMI IO | Read sst_tf_info_0.feature_supported for current PP level | TPMI IO |
| 7 | PCode SstManager | PCode TrlManager | Send HPM_MSG_COMPUTE_CLOS_CONFIG with HP module counts | HPM |
| 8 | PCode TrlManager | TPMI IO | Load IO_SST_TF_INFO_0 (LP clip ratios) | TPMI IO |
| 9 | PCode TrlManager | TPMI IO | Load IO_SST_TF_INFO_2..8 (HP TRL ratios per CDYN x bucket) | TPMI IO |
| 10 | PCode TrlManager | Workpoint Calc | Signal TRL table update -- HP cores elevated, LP cores clipped | Internal |
| 11 | PCode SstManager | TPMI IO | Write sst_pp_status: feature_state[1]=1, feature_error_type=0x0 | TPMI IO |
| 12 | OS/Test | TPMI | Read sst_pp_status -- verify feature_state[1] == 1 (enabled) | TPMI MMIO |
| 13 | OS/Test | TPMI | Write sst_pp_control.feature_state[1] = 0x0 (disable request) | TPMI MMIO |
| 14 | PCode SstManager | TPMI IO | Detect disable; TrlManager reverts to base SST-PP TRL tables | TPMI IO |
| 15 | PCode SstManager | TPMI IO | Write sst_pp_status: feature_state[1]=0 | TPMI IO |
| 16 | OS/Test | TPMI | Read sst_pp_status -- verify feature_state[1] == 0 (disabled) | TPMI MMIO |

---

## Section C: Interface Coverage Assessment

| Interface | Register / Field | Access | Tested By This TC | Coverage Notes |
|-----------|-----------------|--------|-------------------|----------------|
| TPMI SST | sst_pp_control.feature_state[1] | Write | Yes -- Steps 2, 6 (enable/disable) | Primary DUT interface |
| TPMI SST | sst_pp_status.feature_state[1] | Read | Yes -- Steps 1, 5a, 5c, 7 (verify state) | Status feedback |
| TPMI SST | sst_pp_status.feature_error_type[2:0] | Read | Yes -- Steps 4a, 5b (error check) | Error condition coverage |
| TPMI SST | sst_tf_info_0.feature_supported | Read | Yes -- Step 3 (availability check) | Per-PP-level capability |
| TPMI SST | io_pm_qos_config.enable_clos | Read | Yes -- Step 5 (CLOS dependency) | CLOS pre-condition check |
| TPMI SST | SST_CLOS_ASSOC | Read/Write | No -- programmed by BIOS, not toggled by test | Covered by PCT/CLOS TCs |
| PCode | SstManager slow loop | Internal | Indirect -- triggered by TPMI write | Not directly observable |
| PCode | TrlManager HP/LP table reload | Internal | Indirect -- effect visible via frequency | Not directly observable |
| MSR | 0x1AD PRIMARY_TURBO_RATIO_LIMIT | Read | No -- not explicitly checked | Could add as supplemental verification |
| HPM | HPM_MSG_COMPUTE_CLOS_CONFIG | Internal | Indirect | FW-internal message |

### Coverage Gaps

1. **MSR 0x1AD verification**: Test does not read PRIMARY_TURBO_RATIO_LIMIT to confirm HP TRL ratios are applied after TF enable
2. **Frequency verification**: Test verifies register state only; does not confirm actual core frequency changes (HP elevated, LP clipped)
3. **CLOS assignment verification**: BIOS-programmed CLOS assignments not verified by this TC (covered by separate PCT TCs)
4. **Error type 0x2/0x3**: Only error type 0x1 is tested; other error codes not exercised

---

## Section D: NWP Specification References

| Document | Section | Relevance |
|----------|---------|-----------|
| [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) | SST-TF Feature Control | sst_pp_control.feature_state and sst_pp_status register definitions |
| [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) | SST_TF_INFO Registers | SST_TF_INFO_0..8 register layouts, feature_supported bit |
| [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) | Error Type Encoding | feature_error_type values: 0x0=none, 0x1=not supported, 0x2=dependency |
| [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | SST-TF (PCT profile) | NWP-specific: SST-TF active via PCT only; SST-PP/BF/CP/HGS ZBB |
| [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) | Priority Core Turbo | PCT as consumer of SST-TF on NWP; HP core selection via CLOS[0] |
| PrimeCode source | `src/flow/sst/sst_tpmi_general/v2_0/sst_tpmi_general.cpp` | sstTfInfoInit() -- TPMI register programming at reset Phase 5 |
| PCode source | `source/pcode/flows/sst/sst_manager.cpp` | SstManager slow loop -- feature_state[1] change detection |
| PCode source | `source/pcode/flows/trls/trl_manager.cpp` | TrlManager HP/LP CLOS TRL table loading |
| Test script | `graniterapids/pm/sst/sst_tf/sst_tf_validate.py` | validateTF.test_tpmi_control method (reference implementation) |

---

## Section E: NWP Risk Assessment

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|------------|--------|------------|
| 1 | NWP `nwp.xml` runPmx config not available or missing SST-TF TPMI offsets | Medium | High -- test cannot run | Verify nwp.xml has SST TPMI register offsets before test execution |
| 2 | PP0 does not have SST-TF fused as supported on NWP validation SKU | Low | High -- test hits error path only, never positive enable | Check sst_tf_info_0.feature_supported on NWP validation parts; if 0, test only validates error reporting |
| 3 | CLOS dependency (io_pm_qos_config.enable_clos) not pre-configured by BIOS | Medium | Medium -- test gets error_type 0x1 instead of successful enable | Verify BIOS enables CLOS by default for PCT/SST-TF; add CLOS enable step if needed |
| 4 | PCode slow-loop latency between TPMI write and status update causes false failure | Low | Medium -- race condition in status read | Add polling/delay between sst_pp_control write and sst_pp_status read (1+ slow-loop period) |
| 5 | Test script `sst_tf_validate.py` has DMR-specific PP level iteration that fails on NWP | Medium | Medium -- script error on NWP single-PP topology | Review script for NWP single-PP-level compatibility; skip dynamic PP iteration |
| 6 | DLCP (SST_TF_INFO_10) fuse state unknown on NWP -- may interact with TF enable flow | Low | Low -- DLCP is independent path from dynamic TF enable | Confirm DLCP fuse off on NWP validation parts; no TF enable flow interaction expected |

---

## Section F: Recommendations

1. **ADOPT with config change**: Replace `dmr.xml` with `nwp.xml` in runPmx command: `python runPmx.py -x nwp.xml -p sst_tf -tM 60 -M 5 --retry_count 2`

2. **Remove dynamic PP iteration**: NWP is fixed at PP0 (SST-PP ZBB). The test instruction to "iterate over all PP levels in dynamic PP" is not applicable. Run on PP0 only.

3. **Add CLOS pre-condition check**: Before attempting TF enable, explicitly verify `io_pm_qos_config.enable_clos == 0x1`. If CLOS is not enabled, enable it first or document that the test is exercising the error path.

4. **Add slow-loop latency tolerance**: Insert a short delay or polling loop between `sst_pp_control` write and `sst_pp_status` read to account for PCode slow-loop processing time (detection is not interrupt-driven).

5. **Add MSR 0x1AD supplemental check**: After successful TF enable, read `PRIMARY_TURBO_RATIO_LIMIT` (MSR 0x1AD) to verify HP TRL ratios are programmed correctly. This confirms the full PCode flow executed (SstManager -> TrlManager -> MSR update).

6. **Verify NWP HP core count**: After TF enable, verify that the HP/LP partitioning matches expected NWP configuration (8 HP cores, 88 LP cores). Can read CLOS assignments or check HWP MSR differentiation.
