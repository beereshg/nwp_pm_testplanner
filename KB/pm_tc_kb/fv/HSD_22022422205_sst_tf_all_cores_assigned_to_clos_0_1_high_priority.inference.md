# Deep Analysis: SST-TF - All cores assigned to CLOS 0/1 (High Priority)

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422205 |
| **Title** | SST-TF - All cores assigned to CLOS 0/1 (High Priority) |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SST > SST-TF (Turbo Frequency) |
| **NWP Disposition** | **Needs_Adaptation** |
| **HSD Status** | rejected (reason: zbb) |
| **Disposition Rationale** | HSD was rejected as ZBB, but KB analysis shows SST-TF IS active on NWP as the underlying mechanism for PCT. The test exercises the SST-TF enable path and CLOS assignment — both functional on NWP. Adaptation needed: (1) command must use NWP config instead of dmr.xml, (2) topology constants differ (2 CBBs / 96 cores vs 4 CBBs / 128 cores), (3) DLCP SKUs may not support SW CLOS assignment. |
| **Version** | v1 |
| **Generated** | 2026-05-29 |

---

## Test Case

### Test Intent

This test validates that SST-TF correctly grants elevated Turbo Ratio Limits (TRL) to high-priority cores when all cores are assigned to CLOS 0 or CLOS 1 (both HP groups). The test confirms that with SST-TF enabled and no power-limiting condition active, all cores achieve the higher HP TRL ratios defined in the SST_TF_INFO registers, rather than the default non-TF ratios.

On NWP, SST-TF is the underlying mechanism for PCT (Priority Core Turbo). The SST-TF enable path via `SST_PP_CONTROL.feature_state[1]` remains functional. This test is therefore relevant for NWP validation — it exercises the TF TRL elevation path that PCT relies on.

### Pre-Conditions

- SST-TF fuse (`SST_TF_ENABLE`) must be set for the active PP level
- `TURBO_DISABLE` fuse must be 0
- System must NOT be power-limited (PL1/PL2 set high enough for all cores at HP TRL)
- BIOS SST knobs enabled (or programmed via PythonSV/TPMI)
- SVOS with PythonSV or pmss environment
- NWP: Verify SKU is not DLCP-only (DLCP uses fuse-based HP assignment, not SW CLOS)

### Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Enable SST-TF by writing 0x1 to TPMI `sst_pp_control.feature_state[bit 1]` | Same — TPMI path identical on NWP |
| 2 | Set all cores to CLOS 0 via TPMI `sst_clos_assoc_0` to `sst_clos_assoc_N` | NWP has 96 cores across 2 CBBs (vs 128 across 4); adjust register count. Verify CLOS assignment works on non-DLCP SKU |
| 3 | (Coverage variant) Set all cores to CLOS 1 | Same — CLOS 1 is also HP |
| 4 | (Coverage variant) Randomly assign cores to mix of CLOS 0 and CLOS 1 | Same |
| 5 | Run all-core workload (not power limited) | Ensure PL1/PL2 set sufficiently high for 96 cores at NWP HP TRL |
| 6 | Read `IA32_PERF_STATUS` (MSR 0x198) per core; verify cores achieve HP TRL from `SST_TF_INFO_2` ratios | Same MSR; NWP TRL ratios may differ from DMR — read NWP-specific fuse values |
| 7 | Read `perf_limit_reasons` and verify no unexpected throttling | Same register path on NWP |
| 8 | Disable SST-TF (`feature_state[1] = 0`); verify cores fall back to normal TRL | Same — PCode slow-loop detects change and reloads TRL tables |

### Pass/Fail Criteria

**PASS:**
- All cores achieve HP TRL ratio (from `SST_TF_INFO_2..7`) when SST-TF enabled and all cores in CLOS 0/1
- `perf_limit_reasons` shows no unexpected throttling flags
- After SST-TF disable, cores revert to normal (non-TF) TRL within one PCode slow-loop cycle
- TRL fallback ratio matches `SST_PP_INFO_4` (base SST-PP TRL)

**FAIL:**
- Any core stuck at LP clip ratio despite CLOS 0/1 assignment
- Unexpected PLR bits set (thermal, power limit, etc.)
- Cores do not revert after SST-TF disable

---

## Section A: NWP Architecture Delta

### Disposition: Needs_Adaptation

**Key finding:** The HSD was rejected as ZBB with notes stating "SST Features ZBB / Fused Off." However, KB analysis reveals that SST-TF is **active on NWP** — it is the underlying mechanism for PCT (Priority Core Turbo). The blanket ZBB classification for all SST features incorrectly swept SST-TF into the ZBB category. This test should be **reconsidered for NWP execution** with adaptations.

### DMR → NWP Architecture Delta

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| SST-TF status | Active (standalone) | Active (via PCT mechanism) | SST-TF enable path works; test is valid |
| CBB count | 4 CBBs | 2 CBBs | CLOS register scope reduced; 96 total cores vs 128 |
| Cores per CBB | 32 | 48 (24 DCMs × 2 PNC) | CLOS_ASSOC register field mapping differs |
| SMT | SMT enabled | No SMT (single-threaded) | Logical core count = physical core count |
| HP TRL ratios | DMR fuse values | NWP fuse values | Expected ratios differ; read from SST_TF_INFO_2..7 |
| DLCP SKU | Optional | Present on some SKUs | DLCP SKUs use fuse-based HP assignment; SW CLOS assignment may be ignored |
| Test command | `runPmx.py -x dmr.xml -p sst_tf` | Needs `-x nwp.xml` | Config file must match NWP topology |
| CLOS_ASSOC comment | N/A | "CLOS Assoc not supported on DLCP SKU" | Test must target non-DLCP SKU or verify DLCP behavior |
| PCT core count | N/A (no PCT on DMR) | 8 HP cores across 4 partitions | When PCT is active, HP cores are a subset; this test sets ALL to HP which may conflict with PCT partition model |

### Adaptation Requirements

1. **Command update**: Change `-x dmr.xml` to `-x nwp.xml` in `runPmx.py` invocation
2. **Topology constants**: Update any hardcoded CBB counts (4→2) and core counts (128→96)
3. **SKU guard**: Add pre-condition check for DLCP SKU — skip or adapt if DLCP-only
4. **TRL validation values**: Read NWP-specific `SST_TF_INFO_2..7` for expected HP TRL ratios (do not hardcode DMR values)
5. **PCT interaction**: When PCT is active, verify that setting all cores to CLOS 0 does not conflict with PCT partition assignments

---

## Section B: Interactions

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | BIOS | Program SST fuses → TPMI registers at reset Phase 5 (sstTfInfoInit) | TPMI SRAM |
| 2 | BIOS | Write SST_TF_INFO_0 (LP clip ratios per CDYN) | TPMI SRAM |
| 3 | BIOS | Write SST_TF_INFO_1 (HP core-count-per-bucket) | TPMI SRAM |
| 4 | BIOS | Write SST_TF_INFO_2..7 (HP TRL ratios per bucket × CDYN) | TPMI SRAM |
| 5 | PCode (CBB×2) | TrlManager::init() — load all 4 TRL tables from TPMI IO space | TPMI IO |
| 6 | OS/Test | Enable SST-TF: write 0x1 to SST_PP_CONTROL.feature_state[1] | TPMI MMIO |
| 7 | PCode (CBB×2) | SstManager slow-loop detects feature_state[1] change | Internal |
| 8 | PCode (CBB×2) | Send HPM_MSG_COMPUTE_CLOS_CONFIG with HP module counts | HPM |
| 9 | PCode (CBB×2) | TrlManager reloads HP CLOS TRL (SST_TF_INFO_2..7) and LP CLOS TRL (SST_TF_INFO_0) | TPMI IO |
| 10 | OS/Test | Write CLOS 0 to all cores via SST_CLOS_ASSOC_0..N | TPMI MMIO |
| 11 | PCode (CBB×2) | CLOS update flow detects HP CCP mask change → signals workpoint calc | Internal |
| 12 | PCode (CBB×2) | Workpoint calc: all cores HP → ratio = max(SST_PP_TRL, HP_CLOS_TRL) | Internal |
| 13 | HW | Core FIVR + PLL enforces elevated HP TRL frequency | HW wire |
| 14 | OS/Test | Run all-core workload (not power limited) | Test logic |
| 15 | OS/Test | Read IA32_PERF_STATUS (MSR 0x198) per core — verify HP TRL achieved | MSR |
| 16 | OS/Test | Read perf_limit_reasons — verify no unexpected throttling | CSR |
| 17 | OS/Test | Disable SST-TF: write 0x0 to SST_PP_CONTROL.feature_state[1] | TPMI MMIO |
| 18 | PCode (CBB×2) | SstManager detects disable → TrlManager clears HP/LP differentiation | Internal |
| 19 | PCode (CBB×2) | Workpoint calc: all cores → normal TRL (no HP/LP split) | Internal |
| 20 | OS/Test | Verify cores fall back to normal TRL via MSR 0x198 | MSR |

### Sequence Data

| # | From | To | Message | Interface |
|---|------|----|---------|-----------|
| 1 | PrimeCode (NIO) | TPMI SRAM | sstTfInfoInit(): write SST_TF_INFO_0..8 from fuses | TPMI SRAM |
| 2 | PCode (CBB) | TPMI IO | TrlManager::init() → load_hp_clos_trl() reads SST_TF_INFO_2..7 | TPMI IO |
| 3 | PCode (CBB) | TPMI IO | TrlManager::init() → load_lp_clos_trl() reads SST_TF_INFO_0 | TPMI IO |
| 4 | OS/Test | TPMI | Write SST_PP_CONTROL.feature_state[1] = 1 (enable TF) | TPMI MMIO |
| 5 | PCode (CBB) | PCode (CBB) | SstManager slow-loop: detect feature_state change | Internal |
| 6 | PCode (CBB Root) | PCode (CBB Leaf) | HPM_MSG_COMPUTE_CLOS_CONFIG (hp_module_count) | HPM |
| 7 | PCode (CBB) | TPMI IO | TrlManager reloads HP/LP CLOS TRL tables | TPMI IO |
| 8 | OS/Test | TPMI | Write SST_CLOS_ASSOC_0..N = CLOS 0 for all cores | TPMI MMIO |
| 9 | PCode (CBB) | PCode (CBB) | CLOS update flow → HP CCP mask update → signal WP calc | Internal |
| 10 | PCode (CBB) | Core FIVR | Workpoint calc → elevated HP TRL → frequency change | HW wire |
| 11 | OS/Test | Core | Read MSR 0x198 (IA32_PERF_STATUS) — verify HP ratio | MSR |
| 12 | OS/Test | PrimeCode (NIO) | Read perf_limit_reasons — verify no throttling | CSR |
| 13 | OS/Test | TPMI | Write SST_PP_CONTROL.feature_state[1] = 0 (disable TF) | TPMI MMIO |
| 14 | PCode (CBB) | Core FIVR | Workpoint calc → normal TRL → frequency fallback | HW wire |
| 15 | OS/Test | Core | Read MSR 0x198 — verify normal TRL | MSR |

---

## Section C: Interface Coverage Assessment

| Interface | Register / Path | Tested? | Coverage Notes |
|-----------|----------------|---------|----------------|
| TPMI SST_PP_CONTROL.feature_state[1] | SST-TF enable/disable | ✅ Yes | Steps 6, 17 — both enable and disable |
| TPMI SST_CLOS_ASSOC_0..N | Per-core CLOS assignment | ✅ Yes | Step 10 — all cores to CLOS 0 (coverage variant: CLOS 1, mixed) |
| TPMI SST_TF_INFO_0 | LP clip ratios | ⚠️ Indirect | LP clip not exercised when all cores HP; need separate LP test |
| TPMI SST_TF_INFO_2..7 | HP TRL ratios per CDYN | ✅ Yes | Validated via MSR 0x198 readback |
| MSR 0x198 (IA32_PERF_STATUS) | Current operating ratio | ✅ Yes | Step 15 — per-core readback |
| CSR perf_limit_reasons | PLR status bits | ✅ Yes | Step 16 — verify no unexpected throttling |
| MSR 0x1AD (PRIMARY_TURBO_RATIO_LIMIT) | HP TRL override | ⚠️ Not directly | Updated by PCode but not explicitly read in test steps |
| HPM_MSG_COMPUTE_CLOS_CONFIG | HP module count broadcast | ❌ No | Internal PCode message; not directly observable from test |
| PCode slow-loop TF detection | SstManager state change | ⚠️ Indirect | Verified by observing frequency change after enable/disable |

### Coverage Gaps

1. **LP CLOS path**: This test sets all cores to HP (CLOS 0/1). A complementary test with all cores in LP (CLOS 3) would validate LP clip ratio enforcement.
2. **CDYN-level differentiation**: Test uses "all-core workload" but does not specify CDYN level (SSE vs AVX2 vs AVX3). TRL ratios are CDYN-indexed — coverage would improve by running multiple workload types.
3. **MSR 0x1AD readback**: Reading PRIMARY_TURBO_RATIO_LIMIT after SST-TF enable would validate the PCode→MSR update path.
4. **SST_TF_INFO_8**: Feature revision ≥ 2 uses additional bucket info; not covered by this test.

---

## Section D: NWP Specification References

| Spec | URL | Relevance |
|------|-----|-----------|
| Intel SST HAS (Wave3 Common) | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) | SST-TF register definitions, TRL bucket model, CLOS assignments |
| SST TPMI HAS | [SST TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/IC_SST_TPMI.html) | TPMI register interface for SST-TF and CLOS |
| PCT HAS (Arch Common) | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) | PCT architecture — SST-TF is the underlying mechanism |
| IC PCT HAS | [IC PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/IC_PCT.html) | IC PCT implementation details |
| NWP PM MAS | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM feature support status; SST-TF active via PCT |
| NWP HAS - PM | [NWP HAS PM](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features) | NWP PM feature list |
| DMR Turbo HAS | [DMR Turbo HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html) | TRL interaction with SST-TF |
| TPMI HAS | [TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html) | TPMI interface architecture |

---

## Section E: Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| DLCP SKU blocks SW CLOS assignment | Medium | High — test cannot execute on DLCP SKUs | Add SKU pre-check; run on non-DLCP SKU or adapt for DLCP behavior |
| NWP HP TRL ratios differ from DMR | High | Medium — test may use wrong expected values | Read NWP-specific SST_TF_INFO_2..7 for expected ratios; do not hardcode DMR values |
| 2 CBB topology causes CLOS register mismatch | Medium | Medium — incorrect CLOS assignment | Update CLOS_ASSOC register iteration to cover 96 cores across 2 CBBs |
| PCT partition conflict when all cores set to HP | Low | Medium — PCT may reassign CLOS after test writes | Disable PCT partition mode before running test, or verify PCT allows all-HP configuration |
| PCode slow-loop latency masks TF enable | Low | Low — test may read stale TRL if checked too early | Add delay (>1 slow-loop cycle) after TF enable before reading MSR 0x198 |
| NWP SST-TF fuse not set on validation silicon | Low | High — feature not available | Verify SST_TF_ENABLE fuse before test; skip if fuse disabled |
| dmr.xml config used instead of nwp.xml | High | High — test fails or targets wrong topology | Update command: `-x nwp.xml` |

---

## Section F: Recommendations

1. **Reconsider ZBB rejection**: SST-TF is active on NWP via PCT. This test exercises the TF TRL elevation mechanism that PCT relies on. Recommend changing HSD status from `rejected.zbb` to `active` with NWP adaptation notes.

2. **Create NWP config**: Ensure `nwp.xml` exists for runPmx.py with correct topology (2 CBBs, 96 cores, no SMT).

3. **Add DLCP SKU guard**: Insert pre-condition check to detect DLCP SKU (fuse-based HP assignment). Either skip the CLOS assignment steps on DLCP or validate DLCP behavior separately.

4. **Parameterize expected TRL ratios**: Read expected HP TRL values from `SST_TF_INFO_2..7` on the DUT rather than hardcoding DMR ratios. This makes the test portable across programs.

5. **Add CDYN-variant coverage**: Run the test with multiple workload types (SSE, AVX2, AVX3, AMX) to validate CDYN-indexed TRL differentiation.

6. **Add LP companion test**: Create a complementary test with all cores in CLOS 3 (LP) to validate LP clip ratio enforcement.

7. **Verify MSR 0x1AD update**: Add a step to read `PRIMARY_TURBO_RATIO_LIMIT` (MSR 0x1AD) after SST-TF enable to validate the PCode → MSR propagation path.

8. **Timing consideration**: Ensure adequate delay after SST-TF enable/disable (at least 1 PCode slow-loop cycle) before reading frequency status to avoid stale results.
