# Deep Analysis: PCT - All HP Cores in C6

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422104](https://hsdes.intel.com/appstore/article/#/22022422104) |
| **Title** | PCT - All HP cores in C6 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SST > PCT |
| **Sub-Feature** | PCT × C6 interaction — LP cores remain frequency-clipped when all HP cores idle in C6 |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Environment** | virtual_platform |
| **Owner** | mmaltese |
| **Command (DMR)** | `runPmx.py -x dmr.xml -p pct -tM 60 -M 10 --retry_count 2` |
| **Command (NWP)** | `runPmx.py -x nwp.xml -p pct -tM 60 -M 10 --retry_count 2` |
| **KB Article** | [KB/pm_features/sst/pct.md](KB/pm_features/sst/pct.md) |
| **Tags** | `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK` |

### Version History

| Version | Date | Changes | Trigger |
|---------|------|---------|---------|
| v1 | 2025-07-24 | Initial stub generation | `enrich 22022422104` |
| v2 | 2026-05-29 | Full 3-stage pipeline: HSD metadata + Co-Design MCP PCT×C6 spec query + KB enrichment; all sections A-F with swimlane/sequence | `enrich 22022422104` (full pipeline) |

---

## Test Case

### Test Case Intent

Verify that when **all HP cores are placed in C6** and **HWP requests maximum frequency** via
`IA32_HWP_REQUEST (MSR 0x774)`, the **LP cores remain clipped** to `LP_CLIP_RATIO` per PCT
policy on NWP. This is a **runtime functional validation** — not just a boot-time TPMI check.

The test validates the cross-product interaction between SST-TF CLOS frequency partitioning
and core C6 power management. When all HP (CLOS[0]) cores idle in C6, LP (CLOS[3]) cores
must still not gain access to the HP turbo budget. PCode recalculates TRL tables on active
core-count change, but the CLOS-based LP clip ceiling must remain enforced regardless of HP
C-state residency.

**Key distinction**: TC 22022422103 (TPMI register check) validates boot-time TPMI
programming. This TC validates **runtime behavior under HP-core C6 conditions**.


### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP silicon or emulation with PCT enabled and C6 capable |
| BIOS knobs | PCT Partition Count = 4 (default); HP core count = 8 across 4 partitions |
| FW stack | PCode, PrimeCode, PythonSV/PMx available; HWP enabled (`IA32_PM_ENABLE` = 1) |
| SST-TF active | `SST_PP_CONTROL.feature_state[1]` = 1; HP→CLOS[0], LP→CLOS[3] |
| C-state control | Ability to enable/disable C6 per core |
| HWP access | Ability to write `IA32_HWP_REQUEST (MSR 0x774)` |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Confirm PCT active: verify `SST_PP_CONTROL.feature_state[1]`=1 and CLOS assignments (HP→CLOS[0], LP→CLOS[3]) | 8 HP cores in CLOS[0]; 88 LP in CLOS[3] | PCT not enabled or CLOS mismatch |
| 2 | Record baseline LP frequency via `SST_CLOS_CONFIG[3].max` and HP via `SST_CLOS_CONFIG[0].max` | LP baseline ≤ LP_CLIP_RATIO (~P1); HP baseline at PCT TRL (~4.4 GHz) | Baseline register mismatch |
| 3 | Enable C6 on all cores; program `IA32_HWP_REQUEST (MSR 0x774)` to request max frequency | HWP max request active; C6 allowed | MSR write/readback mismatch |
| 4 | Drive all 8 HP cores into C6; verify residency via `IA32_CORE_C6_RESIDENCY (MSR 0x3FD)` | All HP cores in C6; residency counter incrementing | HP cores fail to enter/hold C6 |
| 5 | While HP cores in C6: read LP core effective frequency via `IA32_PERF_STATUS (MSR 0x198)` and `IA32_HWP_CAPABILITIES (MSR 0x771)` per LP core | LP ratio ≤ LP_CLIP_RATIO; `highest_perf` unchanged from baseline | LP cores exceed LP clip or gain HP budget |
| 6 | Wake HP cores from C6 (apply load); re-read LP core effective frequency | LP still clipped; HP resumes PCT TRL (~4.4 GHz) | LP or HP frequency incorrect after C6 exit |
| 7 | Run automation: `runPmx.py -x nwp.xml -p pct -tM 60 -M 10 --retry_count 2` | Automation PASS | Script FAIL or timeout |

### Pass/Fail Criteria

**PASS:**
- LP core effective frequency ≤ `LP_CLIP_RATIO` at all times (steps 5, 6)
- LP cores do **not** gain frequency headroom when HP cores are in C6
- HP cores achieve C6 residency (MSR 0x3FD counter incrementing)
- HP cores resume PCT TRL (~4.4 GHz on NWP) after C6 exit
- `IA32_HWP_REQUEST (0x774)` max-frequency request confirmed active
- `runPmx.py -x nwp.xml -p pct` passes

**FAIL:**
- LP core frequency exceeds `LP_CLIP_RATIO` while HP cores are in C6
- HP cores fail to enter or hold C6
- HP cores do not return to PCT TRL after C6 exit
- SST-TF CLOS enforcement lost during C-state transitions
- Any hang, MCA, soft hang, or PM error observed


---

## Section A: NWP Architecture Delta

**Disposition: Runnable_On_N-1**

PCT and Core C6 are both **fully supported on NWP**. The test validates their cross-product interaction, which is architecturally identical to DMR. The only adaptation required is the XML config file change (`dmr.xml` → `nwp.xml`) to account for NWP topology differences (2 CBBs × 48 cores vs 4 CBBs × 32 cores). The CLOS-based frequency partitioning mechanism and C6 interaction are unchanged.

Per Co-Design HAS/MAS: SST-TF CLOS frequency enforcement is independent of C-state residency — FACT prioritization does not consider sleep states. LP cores remain clipped to LP_P0n even when all HP cores are in C6. PCode does recalculate TRL tables based on active core count (not in C6), but the CLOS-based LP clip ceiling is maintained.

### DMR → NWP Delta Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBB count | 4 | 2 | Different partition-to-CBB mapping; fewer CBBs to iterate |
| Cores per CBB | 32 | 48 | More cores per partition (24 vs 8 on DMR) |
| Total cores | 128 | 96 | Different HP/LP core counts |
| HP cores (default) | 8 across 4 partitions | 8 across 4 partitions (2/partition) | Same HP count, different core IDs |
| Cores per partition | 32 | 24 | 96 ÷ 4 = 24 cores per partition |
| PCT TRL target | ~4.6 GHz | ~4.4 GHz (POR-1) | Different absolute frequency; ratio logic unchanged |
| Core C6 | Supported (C6A/C6S/C6S-P) | Supported (C6A/C6S/C6S-P) | Same C6 variants |
| PkgC6 | Supported | ZBB | No PkgC6 cross-product needed |
| MC6 (Module C6) | Supported | ZBB | MC6 cross-product not applicable |
| SST-PP switching | Active | ZBB | No PP-level switching during test |
| SST-BF | Active | ZBB | No SST-BF interference |
| CLOS enforcement | SST-TF CLOS[0]/CLOS[3] | Same | Identical CLOS mechanism |
| TRL table reload | On active core count change | Same | PCode recalculates on C6 entry/exit |
| LP clip invariant | LP_CLIP_RATIO from SST_TF_INFO_0 | Same | LP clip constant regardless of HP C-state |
| Test XML config | `dmr.xml` | `nwp.xml` | **Only required change** |

---

## Section B: Interactions

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | BIOS | Discover PCT capability; set PCT Partition Count = 4 | BIOS Setup |
| 2 | BIOS | Divide 96 cores into 4 partitions of 24; select 2 HP cores/partition | Internal |
| 3 | BIOS | Program SST_CLOS_CONFIG[0].max = PCT TRL ratio (HP ceiling) | TPMI MMIO |
| 4 | BIOS | Program SST_CLOS_CONFIG[3].max = LP_CLIP_RATIO (LP ceiling) | TPMI MMIO |
| 5 | BIOS | Program SST_CLOS_ASSOC: HP→CLOS[0], LP→CLOS[3] | TPMI MMIO |
| 6 | BIOS | Set SST_PP_CONTROL.feature_state[1] = 1 (activate SST-TF) | TPMI MMIO |
| 7 | BIOS | Override MSR 0x1AD with SST_TF_INFO_2.RATIO_0 (HP TRL) | MSR |
| 8 | PCode (CBB×2) | SstManager detects SST-TF enable in slow loop | Internal |
| 9 | PCode (CBB×2) | TrlManager loads HP/LP CLOS TRL tables from TPMI IO | TPMI IO |
| 10 | PCode (CBB×2) | Workpoint calc: HP cores → PCT TRL, LP cores → LP clip | Internal |
| 11 | OS/Test | Enable C-states, configure HWP max frequency (MSR 0x774) | MSR |
| 12 | OS/Test | Apply load to both HP and LP cores; verify baseline frequencies | Test logic |
| 13 | OS/Test | Remove load from HP cores — drive into C6 idle | HW wire |
| 14 | HW (Core) | HP cores execute C6 entry (Acode core_c6_enter) | Internal |
| 15 | PCode (CBB×2) | Detect HP core C6 entry; recalculate active core count | HPM / Internal |
| 16 | PCode (CBB×2) | TrlManager updates TRL for reduced active cores | Internal |
| 17 | PCode (CBB×2) | Workpoint calc: LP cores STILL clipped to LP_CLIP_RATIO | Internal |
| 18 | OS/Test | Read LP core effective frequency (MSR 0x198) | MSR |
| 19 | OS/Test | Verify LP frequency ≤ LP_CLIP_RATIO | Test logic |
| 20 | OS/Test | Wake HP cores from C6 (apply load) | HW wire |
| 21 | HW (Core) | HP cores execute C6 exit (Acode core_c6_exit) | Internal |
| 22 | PCode (CBB×2) | TrlManager recalculates with restored active core count | Internal |
| 23 | OS/Test | Verify HP cores resume PCT TRL frequency | MSR 0x198 |
| 24 | OS/Test | Verify LP cores remain clipped | MSR 0x198 |

### Sequence Data

| # | From | To | Message | Interface |
|---|------|----|---------|-----------|
| 1 | BIOS | TPMI | Write SST_CLOS_CONFIG[0].max = PCT TRL ratio | TPMI MMIO |
| 2 | BIOS | TPMI | Write SST_CLOS_CONFIG[3].max = LP_CLIP_RATIO | TPMI MMIO |
| 3 | BIOS | TPMI | Write SST_CLOS_ASSOC[]: HP→CLOS[0], LP→CLOS[3] | TPMI MMIO |
| 4 | BIOS | TPMI | Write SST_PP_CONTROL.feature_state[1] = 1 | TPMI MMIO |
| 5 | BIOS | Core | Override MSR 0x1AD with HP TRL | MSR |
| 6 | PCode | TPMI IO | Read SST_TF_INFO_0..8 → load TRL tables | TPMI IO |
| 7 | PCode | Core FIVR/PLL | Apply HP workpoint (PCT TRL) to CLOS[0] cores | HW wire |
| 8 | PCode | Core FIVR/PLL | Apply LP workpoint (LP clip) to CLOS[3] cores | HW wire |
| 9 | Test | Core | Write MSR 0x774 HWP_REQUEST max frequency | MSR |
| 10 | Test | Core | Remove HP core load → C6 entry | Test logic |
| 11 | Core (HP) | PCode | C6 entry notification (INC_GB/DEC_GB Acode flow) | HPM |
| 12 | PCode | PCode | Recalculate active core count; update TRL | Internal |
| 13 | PCode | Core FIVR/PLL | LP cores: maintain LP_CLIP_RATIO ceiling | HW wire |
| 14 | Test | Core (LP) | Read MSR 0x198 IA32_PERF_STATUS | MSR |
| 15 | Test | Test | Assert LP ratio ≤ LP_CLIP_RATIO | Test logic |
| 16 | Test | Core (HP) | Apply load → C6 exit | Test logic |
| 17 | Core (HP) | PCode | C6 exit notification | HPM |
| 18 | PCode | Core FIVR/PLL | Restore HP workpoint to PCT TRL | HW wire |

---

## Section C: Interface Coverage Assessment

| Interface | Covered | Direction | Notes |
|-----------|---------|-----------|-------|
| TPMI SST_CLOS_CONFIG[0] (HP ceiling) | ✅ Yes | Read | Verify HP max ratio at PCT TRL |
| TPMI SST_CLOS_CONFIG[3] (LP ceiling) | ✅ Yes | Read | Verify LP clip ratio unchanged |
| TPMI SST_CLOS_ASSOC (core→CLOS) | ✅ Yes | Read | Verify HP/LP assignments |
| TPMI SST_PP_CONTROL.feature_state[1] | ✅ Yes | Read | Verify SST-TF active |
| MSR 0x774 IA32_HWP_REQUEST | ✅ Yes | Write | Set max frequency request |
| MSR 0x198 IA32_PERF_STATUS | ✅ Yes | Read | Verify effective frequency |
| MSR 0x771 IA32_HWP_CAPABILITIES | ✅ Yes | Read | Verify highest_perf for LP vs HP |
| MSR 0x1AD PRIMARY_TURBO_RATIO_LIMIT | ⚠️ Indirect | Read | Set by BIOS; not directly verified in test |
| MSR 0xE2 MSR_POWER_CTL (C-state enable) | ✅ Yes | Write | Enable/disable C-states |
| MSR 0x3FD IA32_CORE_C6_RESIDENCY | ⚠️ Optional | Read | C6 residency confirmation |
| HPM COMPUTE_CLOS_CONFIG (PCode internal) | ❌ No | Internal | Not directly observable from test |
| TPMI SST_TF_INFO_0 (LP clip fuse source) | ⚠️ Indirect | Read | Fuse-populated; verify via CLOS_CONFIG |
| TPMI SST_TF_INFO_10 (DLCP mask) | ❌ No | Read | DLCP not exercised in this test |
| B2P Mailbox | ❌ No | N/A | Not used in this PCT flow |
| SVID (VR telemetry) | ❌ No | N/A | No voltage verification in this test |

---

## Section D: NWP Specification References

- **PCT HAS**: [PCT (Priority Core Turbo) HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — PCT architecture, DLCP, DQ rules, CLOS configuration
- **SST HAS**: [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST-TF mechanism, CLOS_CONFIG, TRL tables, feature_state control
- **NWP PM HAS**: [NWP HAS - PM](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features) — NWP PM feature support matrix
- **NWP PM MAS**: [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — SST-TF (PCT profile), ZBB features
- **DMR PM HAS**: [DMR SOC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html) — Baseline PM architecture
- **PNC PM HAS**: PantherCove PM HAS §8 — Core C-state architecture (C6A/C6S entry/exit)
- **NWP PCT CCB**: [HSD 14026595435](https://hsdes.intel.com/appstore/article/#/14026595435) — NWP PCT scope: 8 HP cores, 4.4 GHz target
- **NWP SST ZBB**: [HSD 22021155414](https://hsdes.intel.com/appstore/article/#/22021155414) — SST-PP/CP/BF/HGS ZBB confirmation

---

## Section E: NWP Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| LP frequency exceeds clip during HP C6 transition window | Low | High | PCode CLOS enforcement is synchronous with workpoint calc; LP clip is constant per ICCP license. Verify with sub-ms sampling. |
| TRL table recalculation race on C6 entry/exit | Low | Medium | PCode slow-loop handles TRL reload atomically; CLOS config is not re-indexed. Add C6 entry/exit cycling stress. |
| NWP partition-to-CBB mapping differs from DMR | Medium | Medium | NWP has 2 CBBs with 24 cores/partition (vs 8 on DMR). Verify HP core IDs span both CBBs correctly. |
| DLCP HP module mask fuse mismatch on NWP | Low | Low | DLCP not exercised in this test; separate DLCP test covers this. |
| PCT TRL ratio not fused correctly on NWP VP | Medium | Medium | VP environment may have placeholder fuse values. Verify SST_TF_INFO_2.RATIO_0 matches expected 4.4 GHz target. |
| Core C6 residency not achievable under PMx test harness | Low | Medium | PMx framework has proven C6 exerciser; NWP uses same PNC core C6 flow. |
| HWP interference with CLOS frequency limits | Low | Low | HWP request is capped by CLOS max; no override possible. Verify IA32_HWP_CAPABILITIES.highest_perf reflects CLOS limit. |

---

## Section F: Recommendations

1. **Adapt config**: Change `dmr.xml` → `nwp.xml` in command line. Verify NWP XML exists in PMx framework with correct CBB/core topology.
2. **Verify HP core IDs**: After PCT boot, dump SST_CLOS_ASSOC registers to confirm 8 HP cores are correctly distributed across 2 CBBs (4 per CBB, 2 per partition).
3. **Add sub-ms frequency sampling**: During HP C6 entry/exit transitions, sample LP core frequency at high rate to catch any transient CLOS enforcement gap.
4. **Verify TRL recalculation**: Read MSR 0x1AD before and after HP C6 transitions to confirm TRL tables are correctly recalculated for reduced active core count.
5. **Add C6 residency verification**: Read C6 residency counters (MSR 0x3FD or equivalent) to confirm HP cores actually entered C6 (not demoted to C1).
6. **Cross-reference LP clip ratio**: Compare `SST_CLOS_CONFIG[3].max` against `SST_TF_INFO_0.LP_CLIP_RATIO_0` to verify fuse-to-TPMI propagation.
7. **NWP VP validation**: On VP environment, verify fuse values produce expected PCT TRL and LP clip ratios before running functional test.
8. **Remove PkgC6/MC6 cross-product**: DMR test may have PkgC6 scenarios — remove on NWP since PkgC6/MC6 are ZBB'd.

---

## User Notes

> Instructions for LLM: Read all notes chronologically. Apply corrections/clarifications
> to relevant sections. Do not modify notes — append new entries only.

_(No user notes yet)_
