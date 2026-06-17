# HSD 22022422200: SST-TF - TPMI Register Check

> **Version**: v1
> **Generated**: 2026-05-29
> **HSD Status**: open
> **Feature**: SST / SST-TF (Turbo Frequency)
> **Family**: Newport
> **Val Environment**: silicon
> **Priority Tag**: DMR_PO, plc.feature.p1, PMSS_NWP_READINESS_CHECK
> **Owner**: mmaltese

---

## Test Case

### Test Intent

This test validates that **SST-TF TPMI registers are correctly populated after boot/reset**. PrimeCode programs SST_TF_INFO_0..8 registers at reset Phase 5 from SST-TF fuse arrays. This test reads back every SST-TF TPMI register and compares each field against the source fuse values and BIOS configuration. It is the **foundational enablement gate** — all SST-TF/PCT functional tests depend on correct TPMI register population.

Key behavioural rule from HSD TCD: `sst_tf_info_0.feature_supported` will be `0x0` even if `pcode_sst_tf_enable == 0x1` if either:
- Turbo is disabled by fuse (`pcode_turbo_disable == 0x1`), or
- Turbo is disabled by BIOS (`io_firm_config.turbo_mode_disable == 0x1`)

Note: the `sst_tf_info_0.feature_supported` write for BIOS disable occurs at CPL3 (runtime, after boot), not at reset Phase 5. Fuse-based turbo disable during runtime will **not** update `sst_tf_info_0`.

### Pre-Conditions
1. Platform booted to SVOS
2. SST-TF fuses present (SST_TF_ENABLE, SST_TF_CONFIG arrays)
3. Turbo not disabled by fuse or BIOS (for positive check)
4. PythonSV installed with TPMI register access capability
5. `runPmx.py` test framework available with NWP XML config

### Test Steps (from HSD TCD)
1. Boot platform to SVOS with default BIOS settings
2. Run `validateTF.test_tpmi_regs` method (via `runPmx.py -p sst_tf` or standalone script)
3. For each applicable PP level, read all SST-TF TPMI registers:
   - `SST_TF_INFO_0`: `feature_supported`, LP_CLIP_RATIO_0..5 (per CDYN level)
   - `SST_TF_INFO_1`: HP core-count-per-bucket (TRL bucket boundaries)
   - `SST_TF_INFO_2..7`: HP TRL ratios per bucket per CDYN level (6 CDYN × 3 buckets)
   - `SST_TF_INFO_8`: HP bucket core-counts for CLOS resolution (feature_revision >= 2)
4. Compare each register field against source fuse values
5. Verify `SST_PP_CONTROL.feature_state[1]` reflects BIOS SST-TF enable setting

### Pass/Fail Criteria
- **Pass**: All SST-TF TPMI registers match fuse values; `feature_supported = 1` when turbo enabled; LP clip ratios and HP TRL ratios all match fused values per PP level and CDYN level
- **Fail**: Any register field mismatch; `feature_supported` incorrect for turbo enable/disable state; missing or corrupted register values

---

## Section A: NWP Architecture Delta

### Disposition: Runnable_On_N-1

SST-TF is **supported on NWP** as the underlying mechanism for PCT (1 of only 2 active SST features). The TPMI register programming flow in PrimeCode (`sstTfInfoInit()`) is identical. The test uses `runPmx.py` which requires only XML config change.

| Aspect | DMR | NWP | Impact on This Test |
|--------|-----|-----|---------------------|
| CBB count | 4 CBBs | 2 CBBs | TPMI registers read from 2 CBBs instead of 4; iteration range changes |
| SST-TF TPMI registers | SST_TF_INFO_0..8 per PP level | Same register set, same offsets | No register layout change |
| CDYN levels | 6 (SSE, AVX2, AVX3, TMUL, AMX, +1) | 6 (same) | No change to LP clip or HP TRL array dimensions |
| HP TRL buckets | 3 | 3 | No change to bucket count |
| SST_TF_INFO_8 | Present (feature_revision >= 2) | Same (inherited) | Verify NWP OSXML provides the SST_TF_INFO_8 register offset |
| PP levels | Multiple active PP levels (SST-PP) | **Single PP level** (SST-PP ZBB'd) | Only PP level 0 needs validation; simplifies multi-level check |
| Fuse array names | SST_TF_CONFIG_[0..4] arrays | Same naming (NWP inherits DMR fuse definitions) | Fuse value comparison unchanged |
| PrimeCode init function | `sst_tpmi_general.cpp::sstTfInfoInit()` | Same function, same version | No code path change |
| `feature_supported` logic | `SST_TF_ENABLE && !TURBO_DISABLE` | Same logic | Conditional check unchanged |
| Test command | `runPmx.py -x dmr.xml -p sst_tf` | `runPmx.py -x nwp.xml -p sst_tf` | XML config swap only |
| Test script path | `graniterapids/pm/sst/sst_tf/sst_tf_validate.py` | Same script (platform-generic), needs NWP XML | Confirm `validateTF.test_tpmi_regs` works with NWP topology |

### NWP SST-TF TPMI Register Map

| Register | Per PP Level | Content | Fuse Source |
|----------|-------------|---------|-------------|
| `SST_TF_INFO_0` | Yes | `feature_supported`, LP_CLIP_RATIO_0..5 | SST_TF_ENABLE, SST_TF_CONFIG_LP_CLIP_RATIO |
| `SST_TF_INFO_1` | Yes | HP core-count-per-bucket (3 buckets) | SST_TF_CONFIG_TRL_CORES |
| `SST_TF_INFO_2` | Yes | HP TRL ratios: CDYN 0 (SSE), buckets 0..2 | SST_TF_CONFIG_TRL_RATIOS_CDYN_INDEX0 |
| `SST_TF_INFO_3` | Yes | HP TRL ratios: CDYN 1 (AVX2), buckets 0..2 | SST_TF_CONFIG_TRL_RATIOS_CDYN_INDEX1 |
| `SST_TF_INFO_4` | Yes | HP TRL ratios: CDYN 2 (AVX3), buckets 0..2 | SST_TF_CONFIG_TRL_RATIOS_CDYN_INDEX2 |
| `SST_TF_INFO_5` | Yes | HP TRL ratios: CDYN 3 (TMUL), buckets 0..2 | SST_TF_CONFIG_TRL_RATIOS_CDYN_INDEX3 |
| `SST_TF_INFO_6` | Yes | HP TRL ratios: CDYN 4 (AMX), buckets 0..2 | SST_TF_CONFIG_TRL_RATIOS_CDYN_INDEX4 |
| `SST_TF_INFO_7` | Yes | HP TRL ratios: CDYN 5, buckets 0..2 | SST_TF_CONFIG_TRL_RATIOS_CDYN_INDEX5 |
| `SST_TF_INFO_8` | Yes | HP bucket core-counts for CLOS resolution | SST_TF_CONFIG_TRL_CORES (feature_revision >= 2) |

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p sst_tf -tM 60 -M 5 --retry_count 2
```

---

## Section B: Interactions

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | PrimeCode (NIO) | Reset Phase 5: read SST_TF_ENABLE fuse per PP level | [Fuse read] |
| 2 | PrimeCode (NIO) | Read TURBO_DISABLE fuse; compute `tf_supported = SST_TF_ENABLE && !TURBO_DISABLE` | [Fuse read] |
| 3 | PrimeCode (NIO) | Write SST_TF_INFO_0 per PP level: `feature_supported`, LP_CLIP_RATIO_0..5 from SST_TF_CONFIG_LP_CLIP_RATIO fuse arrays | [TPMI MMIO] |
| 4 | PrimeCode (NIO) | Write SST_TF_INFO_1: HP core-count-per-bucket from SST_TF_CONFIG_TRL_CORES fuses | [TPMI MMIO] |
| 5 | PrimeCode (NIO) | Write SST_TF_INFO_2..7: HP TRL ratios per bucket × CDYN from SST_TF_CONFIG_TRL_RATIOS fuses | [TPMI MMIO] |
| 6 | PrimeCode (NIO) | Write SST_TF_INFO_8: HP bucket core-counts (feature_revision >= 2) | [TPMI MMIO] |
| 7 | PrimeCode (NIO) | Lock read-only TPMI registers | [TPMI MMIO] |
| 8 | BIOS | CPL3: if turbo disabled by BIOS knob, write SST_TF_INFO_0.feature_supported = 0 | [TPMI MMIO] |
| 9 | PCode (CBB×2) | Init: TrlManager reads IO_SST_TF_INFO_0..8 from TPMI IO space → loads HP/LP CLOS TRL tables | [TPMI IO read] |
| 10 | PCode (CBB×2) | Slow loop: SstManager checks SST_PP_CONTROL.feature_state[1] for SST-TF enable | [TPMI IO read] |
| 11 | OS/Test | Run `validateTF.test_tpmi_regs` via `runPmx.py -p sst_tf` | [Test logic] |
| 12 | OS/Test | Read SST_TF_INFO_0..8 TPMI registers per PP level per CBB dielet | [TPMI MMIO] |
| 13 | OS/Test | Read source fuse values: SST_TF_ENABLE, SST_TF_CONFIG arrays | [Fuse read] |
| 14 | OS/Test | Compare each TPMI register field against source fuse; verify feature_supported matches turbo enable state | [Test logic] |
| 15 | OS/Test | Read SST_PP_CONTROL.feature_state[1] — verify SST-TF enabled | [TPMI MMIO] |

### Sequence Data

| # | From | To | Message | Interface |
|---|------|----|---------|-----------|
| 1 | PrimeCode (NIO) | Fuse Controller | Read SST_TF_ENABLE, TURBO_DISABLE fuses | [Fuse read] |
| 2 | PrimeCode (NIO) | TPMI SRAM | Write SST_TF_INFO_0: feature_supported + LP_CLIP_RATIO_0..5 | [TPMI MMIO] |
| 3 | PrimeCode (NIO) | TPMI SRAM | Write SST_TF_INFO_1: HP core-count-per-bucket | [TPMI MMIO] |
| 4 | PrimeCode (NIO) | TPMI SRAM | Write SST_TF_INFO_2..7: HP TRL ratios (6 CDYN × 3 buckets) | [TPMI MMIO] |
| 5 | PrimeCode (NIO) | TPMI SRAM | Write SST_TF_INFO_8: HP bucket core-counts | [TPMI MMIO] |
| 6 | BIOS | TPMI SRAM | CPL3: override SST_TF_INFO_0.feature_supported = 0 if turbo disabled | [TPMI MMIO] |
| 7 | PCode (CBB) | TPMI SRAM | Read IO_SST_TF_INFO_0..8 → load TRL tables | [TPMI IO read] |
| 8 | PCode (CBB) | TPMI SRAM | Read SST_PP_CONTROL.feature_state[1] → detect SST-TF enable | [TPMI IO read] |
| 9 | OS/Test | TPMI SRAM | Read SST_TF_INFO_0..8 per PP level | [TPMI MMIO] |
| 10 | OS/Test | Fuse Controller | Read SST_TF_CONFIG fuse arrays (golden reference) | [Fuse read] |
| 11 | OS/Test | OS/Test | Compare TPMI register values vs fuse values → pass/fail | [Test logic] |

---

## Section C: Interface Coverage Assessment

| Interface | Register / Address | Covered by Test | Coverage Notes |
|-----------|-------------------|-----------------|----------------|
| **SST_TF_INFO_0** | `feature_supported`, LP_CLIP_RATIO_0..5 | ✅ Read + compared | Core validation — feature enable and LP clip ratios |
| **SST_TF_INFO_1** | HP core-count-per-bucket | ✅ Read + compared | TRL bucket boundaries |
| **SST_TF_INFO_2..7** | HP TRL ratios per CDYN (6 regs) | ✅ Read + compared | Full HP TRL matrix: 6 CDYN × 3 buckets |
| **SST_TF_INFO_8** | HP bucket core-counts (feat_rev >= 2) | ✅ Read + compared | Newer register — verify NWP has feature_revision >= 2 |
| **SST_PP_CONTROL.feature_state[1]** | SST-TF enable bit | ✅ Read | Confirms SST-TF is active |
| **SST_TF_ENABLE fuse** | Per-PP-level enable | ✅ Read (golden ref) | Source truth for feature_supported |
| **TURBO_DISABLE fuse** | Global turbo disable | ✅ Read (golden ref) | Affects feature_supported derivation |
| **io_firm_config.turbo_mode_disable** | BIOS turbo disable | ⚠️ Implicit | TCD documents the interaction but test may not explicitly verify BIOS disable → feature_supported=0 path |
| **SST_CLOS_ASSOC** | Per-core CLOS assignment | ❌ Not checked | Covered by other SST-TF tests (PCT functional tests) |
| **MSR 0x1AD** | PRIMARY_TURBO_RATIO_LIMIT | ❌ Not checked | Updated from SST_PP_INFO_4 by PCode; separate test |
| **IO_SST_TF_INFO_0..8** (PCode IO) | PCode's TPMI IO space copies | ❌ Not accessible from OS | Internal to PCode — only verifiable via PCode debug |
| **SST_TF_INFO_0 CPL3 update** | feature_supported cleared at CPL3 for BIOS turbo disable | ⚠️ Timing-sensitive | Write occurs at CPL3, not Phase 5 — test runs post-boot so sees final state |

### Coverage Gaps

1. **BIOS turbo disable path**: TCD documents that `feature_supported` is cleared at CPL3 (not Phase 5) when BIOS disables turbo. Test should explicitly verify this path with turbo disabled by BIOS knob.
2. **Multi-PP-level validation**: On NWP, only PP level 0 is relevant (SST-PP ZBB'd). Test should confirm no spurious data in other PP level slots.
3. **Per-CBB consistency**: NWP has 2 CBBs — test should verify both CBBs have identical SST-TF TPMI values (same NIO programs both).
4. **Warm reset persistence**: TPMI registers should survive warm reset (NVM-backed). Test should verify post-warm-reset values match cold boot.

---

## Section D: NWP Specification References

| Type | Document | Section | Relevance |
|------|----------|---------|-----------|
| HAS | [Intel SST HAS — SST-TF Registers](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html#sst-tf-registers) | SST-TF register definitions | Authoritative register layout: SST_TF_INFO_0..8 field definitions |
| HAS | [Intel SST HAS (Wave3 Common)](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) | §3 SST-TF | SST-TF architecture — CLOS model, TRL tables, feature enable logic |
| HAS | [SST TPMI HAS (Wave3 Common)](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/IC_SST_TPMI.html) | Register offsets | TPMI register memory map for SST |
| HAS | [PCT HAS (Arch Common)](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) | §2 PCT + SST-TF | PCT uses SST-TF registers; confirms SST_TF_INFO_10 (DLCP) |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | §3 SST-TF (PCT profile) | NWP feature support confirmation — SST-TF active |
| FAS | [Primecode SST FHAS (DMR)](https://docs.intel.com/documents/primecode/fhas/DMR/SST/SST.html) | TPMI register init | PrimeCode `sstTfInfoInit()` flow |
| Source | `src/flow/sst/sst_tpmi_general/v2_0/sst_tpmi_general.cpp` | `sstTfInfoInit()` | PrimeCode function that writes SST_TF_INFO_0..8 |
| Source | `src/flow/sst/sst_tpmi_compute/v1_0/sst_tpmi_compute.cpp` | `getTrlRatioForSstTfInit()` | Fuse accessor for TRL ratios |
| Source | PCode `source/pcode/flows/trls/trl_manager.cpp` | `load_hp_clos_trl()`, `load_lp_clos_trl()` | PCode TRL table loading from TPMI IO |
| KB | [KB/pm_features/sst/tf.md](../../KB/pm_features/sst/tf.md) | Full KB article | HW/FW/OS touchpoints, execution flow, NWP delta |

---

## Section E: NWP Risk Assessment

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| 1 | **LP clip ratio programming error** — DMR sightings: "pCode not programming LP ratios correctly with SST TF enabled" (A0); "Modules assigned as LP resolving wrong ratios" (X4); "LAVA attribute SSTTF_CFG0_CDYN4_LP_CLIP_FREQ wrong for specific SKUs" | Medium | High — LP_CLIP_RATIO fields in SST_TF_INFO_0 would not match fuse, directly caught by this test | Cross-check SST_TF_INFO_0 LP clip values against raw fuse reads for all 6 CDYN levels |
| 2 | **SST_TF_INFO_8 missing on NWP** — this register is gated by `feature_revision >= 2`. If NWP OSXML does not define the SST_TF_INFO_8 offset, PrimeCode will skip the write and PCode's `load_hp_clos_trl()` will read stale/zero data | Low | High — HP TRL bucket resolution would fail silently | Verify NWP OSXML provides SST_TF_INFO_8 register; check `feature_revision_default_value` in TPMI mailbox RDL |
| 3 | **TRL bucket count mismatch** — DMR sighting: "PP3_SST_TF bucket-2 core count greater than PP3 online core count" | Low | Medium — bucket boundaries in SST_TF_INFO_1 would not match physical core count | Compare SST_TF_INFO_1 HP core-count-per-bucket against actual online core count (96 on NWP) |
| 4 | **BIOS turbo disable race** — TCD documents that `sst_tf_info_0.feature_supported` write for BIOS turbo disable happens at CPL3, not Phase 5. If test reads before CPL3 completes, stale value may be seen | Low | Medium — transient pass for a functionally broken state | Ensure test runs after CPL3 is complete (post-OS boot); add check for `io_firm_config.turbo_mode_disable` coherence |
| 5 | **TPMI register access breaks GPSB** — DMR sighting: "Reading CBB TPMI via PYSV breaks GPSB access" | Low | Medium — test infrastructure issue, not silicon bug | Use validated TPMI access path; avoid concurrent GPSB operations |
| 6 | **Per-CBB register inconsistency** — NWP has 2 CBBs programmed by same NIO. If NIO programs only one CBB's TPMI, the other will have stale/zero values | Very Low | High — half the platform would have wrong SST-TF config | Read and compare SST_TF_INFO registers from both CBB0 and CBB1 |
| 7 | **Fuse mismatch on early NWP silicon** — DMR sighting: "Q9UC VIS QDF has incorrect fuses on PP level 4 CDYN index 1". Early NWP steppings may have fuse programming errors | Low | Medium — test correctly detects this as a fuse issue, not firmware bug | Flag fuse value mismatches with clear messaging so triage distinguishes fuse vs FW bugs |

### DMR Bug History (SST-TF TPMI Domain)

| Sighting | Title | Relevance to This TC |
|----------|-------|---------------------|
| DMR A0 | pCode not programming LP ratios correctly with SST TF enabled | **Direct** — LP_CLIP_RATIO in SST_TF_INFO_0 is a primary check target |
| DMR X4 | Modules assigned as LP resolving wrong ratios with SST TF | **Direct** — wrong LP ratios would be caught by fuse comparison |
| DMR PM | LAVA attribute SSTTF_CFG0_CDYN4_LP_CLIP_FREQ wrong for specific SKUs | **Direct** — SKU-specific fuse errors detected by this test |
| DMR X4 | PP3_SST_TF bucket-2 core count > PP3 online core count | **Direct** — SST_TF_INFO_1 bucket validation |
| DMR A0 X4 | Q9UC VIS QDF incorrect fuses on PP level 4 CDYN index 1 | **Related** — fuse programming error on specific QDF |
| DMR X1 PO | Reading CBB TPMI via PYSV breaks GPSB access | **Infrastructure** — test execution risk |
| DMR X4 | pCode not resolving correctly resolved_module_mask TPMI register | **Related** — TPMI register population issue |

---

## Section F: Recommendations

1. **ADOPT with config change** — swap `dmr.xml` → `nwp.xml` in `runPmx.py` command. SST-TF TPMI register programming is architecturally identical on NWP. The `validateTF.test_tpmi_regs` method is platform-generic.

2. **Verify per-CBB consistency** — NWP has 2 CBBs (vs DMR's 4). Read SST_TF_INFO registers from both CBB0 and CBB1 and confirm identical values, since both are programmed by the same NIO.

3. **Simplify PP-level iteration** — since SST-PP is ZBB'd on NWP, only PP level 0 contains valid data. Test may skip multi-PP-level checks or explicitly verify other PP level slots are empty/zero.

4. **Confirm SST_TF_INFO_8 availability** — verify NWP OSXML defines the SST_TF_INFO_8 register offset. If `feature_revision < 2` on NWP, this register may not exist and the test should skip its check.

5. **Add BIOS turbo disable negative test** — per TCD, `feature_supported` should be 0 when BIOS disables turbo. Add a variant that toggles the BIOS `turbo_mode_disable` knob and verifies `SST_TF_INFO_0.feature_supported = 0`.

6. **Update core iteration for 96 cores** — verify SST_TF_INFO_1 HP bucket core-counts are consistent with NWP's 96-core topology (2 CBBs × 48 cores).

**Priority**: **High** — tagged `DMR_PO`, `plc.feature.p1`. This is the SST-TF enablement gate test. All PCT functional tests (frequency verification, CLOS assignment, TRL resolution) depend on correct TPMI register population. Must pass before running any SST-TF/PCT functional test.
