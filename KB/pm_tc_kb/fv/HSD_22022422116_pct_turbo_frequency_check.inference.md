# HSD 22022422116: PCT - Turbo Frequency Check

> **Version**: v1
> **Generated**: 2026-05-29
> **HSD Status**: open
> **Feature**: SST / PCT (Priority Core Turbo)
> **Family**: Newport
> **Val Environment**: silicon
> **Priority Tag**: plc.feature.p1, PMSS_NWP_READINESS_CHECK
> **Owner**: mmaltese

---

## Test Case

### Test Case Intent

This test validates the primary functional invariant of **PCT (Priority Core Turbo)** on NWP: **HP cores** run at the elevated PCT HP ratio while **LP cores** are clipped to the LP frequency ceiling, under sustained all-core load with C-states disabled. If HP and LP cores do not converge to their respective CLOS-assigned ceilings, the PCT policy is not functioning correctly.

This TC validates: HP/LP runtime frequency separation, consistency with programmed PCT CLOS ceilings, sustained frequency behavior under all-core load, and automation-based execution.

> Does **not** validate boot-time discovery or default enablement (covered by TC 22022422103 and TC 16030768619).

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| 1 | Platform boots with PCT enabled (PCT Partition Count >= 2; default = 4) |
| 2 | SST-TF active (SST_PP_CONTROL.feature_state[1] = 1) |
| 3 | HP cores assigned to CLOS[0]; LP cores to CLOS[3] |
| 4 | All C-states disabled (BIOS or MSR 0xE2) — all cores in C0 |
| 5 | All logical processors online |
| 6 | No active thermal / external limiter that would invalidate frequency observation |
| 7 | 
unPmx.py available with NWP XML configuration (
wp.xml) |

### Recommended Baseline Registers

| Register | Purpose |
|----------|---------|
| SST_PP_CONTROL.feature_state[1] | Confirm SST-TF active |
| SST_CLOS_ASSOC[] | Confirm HP/LP classification |
| SST_CLOS_CONFIG[0].max | HP ratio ceiling |
| SST_CLOS_CONFIG[3].max | LP clip ceiling |
| SST_TF_INFO_2.RATIO_0 | HP target ratio source |
| SST_TF_INFO_0.LP_CLIP_RATIO_0 | LP clip source |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Disable all C-states; confirm all cores in C0 | No C-state residency | Cores entering C-states |
| 2 | Confirm PCT active state and HP/LP CLOS mapping via TPMI | SST-TF enabled; CLOS assignments correct | PCT disabled or wrong mapping |
| 3 | Write IA32_HWP_REQUEST (MSR 0x774) for max-perf on all cores | HWP max request accepted | MSR write failure |
| 4 | Apply sustained CPU workload to all cores | All cores loaded; no idle | Partial loading |
| 5 | Read effective frequency on HP cores via IA32_PERF_STATUS (MSR 0x198) | HP cores at PCT TRL = SST_TF_INFO_2.RATIO_0 (~4.4 GHz NWP) | HP cores below expected HP ceiling |
| 6 | Read effective frequency on LP cores via IA32_PERF_STATUS (MSR 0x198) | LP cores at LP clip = SST_TF_INFO_0.LP_CLIP_RATIO_0 (~P1) | LP cores exceed LP clip |
| 7 | Compare HP and LP observed frequencies | Clear HP > LP frequency separation | No separation or inversion |
| 8 | Run automation: 
unPmx.py -x nwp.xml -p pct -tM 60 -M 10 --retry_count 2 | Automation PASS | Script FAIL or timeout |
| 9 | Verify post-run CLOS configuration consistent | PCT/CLOS state unchanged after run | State corruption or drift |

### Pass / Fail Criteria

**PASS**: PCT active; 8 HP cores track PCT TRL (SST_CLOS_CONFIG[0].max = SST_TF_INFO_2.RATIO_0 ~4.4 GHz); 88 LP cores clipped to LP ceiling (SST_CLOS_CONFIG[3].max = SST_TF_INFO_0.LP_CLIP_RATIO_0 ~P1); HP freq > LP freq under sustained load; automation passes.

**FAIL**: Any HP core below PCT TRL; any LP core exceeding LP clip; no frequency separation; PCT/SST-TF inactive; automation fails.

### Post-Process

Save: TPMI snapshots (before/after), HP/LP per-core frequency observations, automation log, C-state residency evidence.

## Section A: NWP Architecture Delta

### Disposition: Runnable_On_N-1

PCT is **supported on NWP** and this test exercises the core PCT feature invariant. The test uses `runPmx.py` which requires only an XML config change (`dmr.xml` → `nwp.xml`). The underlying PCT mechanism (CLOS-based frequency partitioning via SST-TF) is identical on NWP.

| Aspect | DMR | NWP | Impact on This Test |
|--------|-----|-----|---------------------|
| CBB count | 4 CBBs × 32 cores = 128 cores | 2 CBBs × 48 cores = 96 cores | Core iteration range changes; partition sizes differ |
| HP core count | 4 or 8 (SKU-dependent) | **8 HP cores** (2 per partition × 4 partitions) | Verify 8 cores achieve HP ratio, 88 cores clipped |
| PCT frequency target | SKU-dependent | **4.4 GHz** (POR-1, CCB 14026595435) | Expected HP ratio value may differ |
| PCT Enable knob | Standalone knob | **Eliminated** — integrated into PCT Partition Count (0=disabled) | No test impact (test verifies frequency, not knobs) |
| SST-PP cross-product | PCT operates across multiple PP levels | **SST-PP ZBB'd** — single boot PP level only | Simplifies test — no PP switching during PCT verification |
| SMT | 2 threads per core | **No SMT** — single-threaded cores | Core count = thread count; no per-thread HWP ambiguity |
| LP clip ratio | ~P1 (SST_TF_INFO_0.LP_CLIP_RATIO_0) | ~P1 (same mechanism, NWP fuse values) | Expected LP frequency differs by SKU |
| DLCP | PCT_Module_Mask fuse selects HP positions | **TBD** — NWP DLCP support unconfirmed | May affect HP core identification; verify SST_TF_INFO_10 |
| Test command | `runPmx.py -x dmr.xml -p pct` | `runPmx.py -x nwp.xml -p pct` | XML config swap only |
| Die topology (MADT) | 2 IMH + 4 CBBs | 1 NIO + 2 CBBs | Partition → core mapping uses different MADT ordering |

### NWP PCT Configuration Summary

| Parameter | NWP Value | Source |
|-----------|-----------|--------|
| HP core count | 8 (2 per partition × 4 partitions) | CCB [HSD 14026595435](https://hsdes.intel.com/appstore/article/#/14026595435) |
| PCT frequency target | 4.4 GHz (POR-1) | CCB [HSD 14026595435](https://hsdes.intel.com/appstore/article/#/14026595435) |
| Total cores | 96 (2 CBBs × 48 cores) | NWP architecture |
| Default partitions | 4 (24 cores/partition) | Standard PCT algorithm |
| CLOS assignment | HP → CLOS[0], LP → CLOS[3] | [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |
| SST-PP interaction | None (ZBB'd) | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p pct -tM 60 -M 10 --retry_count 2
```

---

## Section B: Interactions — Swimlane & Sequence Diagram

### Swimlane: PCT Turbo Frequency Verification Flow

| # | OS/Test | BIOS | PrimeCode (NIO) | PCode (CBB×2) | Core FIVR/PLL | Verification |
|---|---------|------|-----------------|---------------|---------------|--------------|
| 1 | | **[Config]** Read PCT fuses: PCT_ENABLE, PCT_Module_Mask, SST_TF_CONFIG arrays | | | | |
| 2 | | **[Config]** Divide 96 cores into 4 partitions (24 cores each); select 2 HP cores/partition = 8 HP total | | | | |
| 3 | | **[Config]** Program per-dielet SST-TF TPMI: SST_CLOS_CONFIG[0].max = TRL ratio (HP), SST_CLOS_CONFIG[3].max = LP clip (LP) | | | | |
| 4 | | **[Config]** Set SST_CLOS_ASSOC[]: HP cores → CLOS[0], LP cores → CLOS[3]; SST_CP_CONTROL = Ordered; SST_PP_CONTROL.feature_state[1] = 1 | | | | |
| 5 | | **[Config]** Override MSR 0x1AD with SST_TF_INFO_2.RATIO_0 (HP TRL); Disable C-states | | | | |
| 6 | | | **[Config]** Reset Phase 5: Read SST_TF fuses → populate SST_TF_INFO_0..10 TPMI registers | | | |
| 7 | | | | **[HW]** SST-TF active: enforce CLOS-based per-core frequency limits | **[HW]** HP PLLs target PCT TRL; LP PLLs clipped to LP_CLIP | |
| 8 | **[Action]** Write MSR 0x774 (IA32_HWP_REQUEST) = max freq on ALL 96 cores | | | | | |
| 9 | **[Action]** Apply sustained CPU load across all cores | | | **[HW]** HP CLOS[0] resolves to PCT TRL ratio; LP CLOS[3] resolves to LP clip | **[HW]** HP FIVRs deliver PCT voltage/freq; LP FIVRs at P1 voltage/freq | |
| 10 | | | | | | **[Verify]** Read MSR 0x198 (IA32_PERF_STATUS) on each core |
| 11 | | | | | | **[Verify]** HP cores: actual_freq == SST_TF_INFO_2.RATIO_0 |
| 12 | | | | | | **[Verify]** LP cores: actual_freq == SST_TF_INFO_0.LP_CLIP_RATIO_0 |
| 13 | | | | | | **[Verify]** Frequency separation: HP freq > LP freq |

### Component Interaction Sequence

```
    BIOS         TPMI(SST)      PrimeCode(NIO)   PCode(CBB×2)    Core FIVR/PLL    OS/Test
     │               │               │               │               │               │
 1.  │──[TPMI MMIO]─►│ Write SST_CLOS_CONFIG[0].max = HP TRL ratio  │               │
 2.  │──[TPMI MMIO]─►│ Write SST_CLOS_CONFIG[3].max = LP clip ratio │               │
 3.  │──[TPMI MMIO]─►│ Write SST_CLOS_ASSOC[]: HP→CLOS[0], LP→CLOS[3]              │
 4.  │──[TPMI MMIO]─►│ Write SST_PP_CONTROL.feature_state[1]=1      │               │
 5.  │──[MSR]────────┼──────────────►│ Override MSR 0x1AD with HP TRL│               │
     │               │               │               │               │               │
 6.  │               │               │──[Phase 5]───►│ SST_TF fuses → SST_TF_INFO regs│
     │               │               │               │               │               │
 7.  │               │               │               │──[CLOS enf]──►│ HP: PLL → TRL freq
 8.  │               │               │               │──[CLOS enf]──►│ LP: PLL → clip freq
     │               │               │               │               │               │
 9.  │               │               │               │               │◄──[MSR 0x774]──│ HWP req = max
10.  │               │               │               │               │◄──[workload]───│ Sustained load
     │               │               │               │               │               │
11.  │               │               │               │               │──[MSR 0x198]──►│ Read PERF_STATUS
12.  │               │               │               │               │               │ Verify HP == TRL
13.  │               │               │               │               │               │ Verify LP == clip
14.  │               │               │               │               │               │ Verify HP > LP
```

---

## Section C: Interface Coverage Assessment

| Interface | Register / MSR | Covered by Test | Coverage Notes |
|-----------|---------------|-----------------|----------------|
| **IA32_HWP_REQUEST** (0x774) | Per-core HWP desired freq | ✅ Written | Step 2: max freq request drives all cores to ceiling |
| **IA32_PERF_STATUS** (0x198) | Per-core actual frequency | ✅ Read | Step 3: primary verification — actual freq vs expected |
| **SST_CLOS_CONFIG[0]** | HP frequency bounds (min=P1, max=TRL) | ⚠️ Implicit | Not directly read by test, but validates its effect |
| **SST_CLOS_CONFIG[3]** | LP frequency bounds (min=Pn, max=clip) | ⚠️ Implicit | Not directly read by test, but validates its effect |
| **SST_CLOS_ASSOC[]** | Per-core CLOS assignment | ⚠️ Implicit | BIOS-programmed; test relies on correct assignment |
| **SST_TF_INFO_2.RATIO_0** | HP TRL ratio | ❌ Not read | Test should read to get expected HP value |
| **SST_TF_INFO_0.LP_CLIP_RATIO_0** | LP clip ratio | ❌ Not read | Test should read to get expected LP value |
| **SST_PP_CONTROL.feature_state[1]** | SST-TF enable bit | ❌ Not verified | Pre-condition: should verify TF is active |
| **MSR 0x1AD** (TRL) | Primary TRL override | ❌ Not read | Should verify BIOS override matches SST_TF_INFO_2 |
| **IA32_HWP_CAPABILITIES** (0x771) | Per-core highest_perf (DLCP differentiation) | ❌ Not read | DLCP: HP cores report P0max, LP report clip |
| **SST_TF_INFO_10** | DLCP PCT HP module mask | ❌ Not read | NWP DLCP support TBD; would identify HP core positions |
| **perf_limit_reasons** | Throttle indicators | ❌ Not checked | Should verify no unexpected throttle during test |

### Coverage Gaps

1. **No pre-condition validation**: Test does not verify SST-TF is active or CLOS assignment is correct before measuring frequency
2. **No expected-value derivation**: Test should read SST_TF_INFO_2/SST_TF_INFO_0 to derive expected HP/LP frequencies rather than hardcoding
3. **No DLCP awareness**: If NWP uses DLCP, test should read SST_TF_INFO_10 to identify which cores are HP vs LP
4. **No throttle check**: Should verify `perf_limit_reasons` is clear — thermal/RAPL throttle could mask PCT frequency behavior

---

## Section D: NWP Specification References

| Type | Document | Section | Relevance |
|------|----------|---------|-----------|
| HAS | [PCT HAS (Arch Common)](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) | §2 Architecture, §3 DLCP, §4 DQ Rules | Authoritative PCT architecture — CLOS mapping, frequency hierarchy, partition algorithm |
| HAS | [Intel SST HAS (Wave3 Common)](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) | §3 SST-TF, §4 CLOS | SST-TF underlying mechanism — CLOS_CONFIG, CLOS_ASSOC registers |
| HAS | [SST TPMI HAS (Wave3 Common)](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/IC_SST_TPMI.html) | Register definitions | TPMI register layouts for SST_TF_INFO, SST_CLOS_CONFIG |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | §3 ZBB list, SST-TF (PCT profile) | NWP feature support confirmation |
| FAS | [Primecode SST FHAS (DMR)](https://docs.intel.com/documents/primecode/fhas/DMR/SST/SST.html) | SST-TF firmware flows | PrimeCode SST TPMI register init |
| FAS | [CBB SST Manager FAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/FAS/SST_manager/cbb_SST_manager_FAS.html) | PCode SST manager | CLOS enforcement, TRL management |
| FAS | [Oakstream CPUPM FAS](https://docs.intel.com/documents/System-firmware-bios/Domain/ServerCpuPm/Dmr/DMR/Oakstream_CPUPM_FAS.html) | BIOS PCT programming | Partition algorithm, CLOS assignment, TRL override |
| CCB | [HSD 14026595435](https://hsdes.intel.com/appstore/article/#/14026595435) | NWP PCT scope | 8 HP cores, 4.4 GHz target, POR-1 status |
| CCB | [HSD 14023051596](https://hsdes.intel.com/appstore/article/#/14023051596) | DMR PCT feature item | DMR-CCB: Support Priority Core Turbo (priority 2-high) |
| KB | [KB/pm_features/sst/pct.md](../../KB/pm_features/sst/pct.md) | Full KB article | HW/FW/OS touchpoints, NWP delta, KPI & timing |

---

## Section E: NWP Risk Assessment

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| 1 | **LP ratio resolution incorrect on NWP** — DMR sighting: "pCode is not well programming LP ratios when SST TF is enabled" (A0); "Modules assigned as LP are resolving wrong ratios with SST TF enabled" (X4) | Medium | High — LP cores could run at wrong frequency, failing this test | Verify SST_CLOS_CONFIG[3].max matches SST_TF_INFO_0.LP_CLIP_RATIO_0 before running test; check PCode `sst_manager.cpp::update_cfgs()` |
| 2 | **CLOS association mapping error** — DMR sighting: "SST_CLOS_ASSOC_0.CLOS_ID_MODULE3 mapped to 2 modules" | Medium | High — wrong cores get HP treatment, frequency verification fails on wrong core set | Pre-read SST_CLOS_ASSOC[] to confirm HP/LP assignment before measuring frequency |
| 3 | **DLCP HP core identification ambiguity** — NWP DLCP support is unconfirmed; if PCT_Module_Mask fuse is used, arbitrary core selection via BIOS knob may not work | Low | Medium — test may not know which cores are HP if DLCP fixes positions | Read SST_TF_INFO_10 and IA32_HWP_CAPABILITIES(0x771).highest_perf to identify HP cores |
| 4 | **Partition algorithm difference due to 2 CBBs × 48 cores** — NWP has fewer, larger dies than DMR; MADT core ordering differs | Low | Medium — partition → core mapping mismatch could cause wrong cores flagged as HP | Validate partition layout against MADT x2APIC ordering; confirm partition count and HP assignment via runPmx |
| 5 | **Vrel risk → PCT fallback to legacy SST-TF** — CCB 14026595435 notes Vrel risk; if it materializes, PCT frequency target drops | Low | Low — test still validates frequency separation, just at different values | Read SST_TF_INFO_2 at runtime for expected HP value; don't hardcode 4.4 GHz |
| 6 | **SST-TF enable hang** — DMR sighting: "Enabling SST Turbo Frequency when modules in CLOS3/CLOS2 groups results in system hang" | Low | Critical — system hang prevents any test execution | Confirm BIOS enables SST-TF cleanly at boot; if hang occurs, check PCode `sst_manager.cpp` CLOS handling |
| 7 | **TRL bucket count mismatch** — DMR sighting: "PP3_SST_TF bucket-2 core count greater than PP3 online core count" | Low | Medium — TRL table inconsistency could cause wrong HP ratio | Verify SST_TF_INFO_2 TRL buckets align with fused core count on NWP |

### DMR Bug History (SST/PCT Domain)

| Sighting | Title | Relevance to This TC |
|----------|-------|---------------------|
| DMR A0 | pCode not programming LP ratios correctly with SST TF enabled | **Direct** — LP ratio verification is step 3 of this test |
| DMR X4 | Modules assigned as LP resolving wrong ratios with SST TF | **Direct** — LP frequency mismatch is the primary failure mode |
| DMR X4 | SST_CLOS_ASSOC_0 mapped to 2 modules | **Related** — CLOS mapping errors affect HP/LP classification |
| DMR X1 | Enabling SST-TF results in system hang | **Blocking** — hang prevents test execution entirely |
| DMR X4 | pCode not resolving correctly resolved_module_mask TPMI register | **Related** — affects module-level HP identification |

---

## Section F: Recommendations

1. **ADOPT with config change** — swap `dmr.xml` → `nwp.xml` in command line; no logic changes needed. NWP PCT is functionally identical to DMR PCT at the CLOS enforcement level.

2. **Add pre-condition checks** — before frequency measurement, verify:
   - `SST_PP_CONTROL.feature_state[1] == 1` (SST-TF active)
   - `SST_CLOS_ASSOC[]` shows expected HP/LP core mapping
   - `perf_limit_reasons` is clear (no thermal/RAPL throttle masking results)

3. **Derive expected values dynamically** — read `SST_TF_INFO_2.RATIO_0` for expected HP frequency and `SST_TF_INFO_0.LP_CLIP_RATIO_0` for expected LP frequency at runtime rather than hardcoding targets.

4. **Add DLCP awareness** — if NWP uses Die Level Cherry Picking, read `SST_TF_INFO_10` PCT_Module_Mask and `IA32_HWP_CAPABILITIES(0x771).highest_perf` per core to correctly identify which cores are HP vs LP.

5. **Update core iteration** — adjust from 4 CBBs × 32 cores to 2 CBBs × 48 cores (96 total; 8 HP, 88 LP).

6. **Monitor DMR LP ratio bugs** — the most common DMR SST-TF failure mode was incorrect LP ratio resolution. This is the exact failure this test catches. Confirm PCode `sst_manager.cpp::update_cfgs()` is correct for NWP topology.

**Priority**: **High** — tagged `plc.feature.p1`; this is the foundational PCT frequency correctness test. PCT is 1 of only 2 active SST features on NWP.
