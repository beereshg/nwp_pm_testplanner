# Deep Analysis: PCT - Verify TDP Convergence

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422117 |
| **Title** | PCT - Verify TDP convergence |
| **Date** | 2026-05-29 |
| **Version** | v2 (full pipeline enrichment — swimlane/sequence + C/D/E sections) |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SST |
| **Sub-Feature** | PCT — RAPL TDP convergence with PCT: LP cores throttled first, HP cores maintained |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Test Case Intent

Verify the **Socket RAPL x PCT cross-product** behavior under **PL1/TDP enforcement** on NWP. When the socket is power-constrained by RAPL PL1, **PCT Ordered Throttling** must preserve HP priority:

- **LP cores throttled first** (Phase A)
- **HP cores maintained while LP cores still have reduction headroom** (Phase B)
- **HP cores reduced only after LP reduction is exhausted** (Phase C if needed)

This is the key functional invariant for RAPL x PCT interaction. If HP cores are reduced before LP-first behavior is observable, Ordered Throttling is not functioning correctly.

> Ordered Throttling Phases: Phase A (LP-only reduction) -> Phase B (LP at min, HP maintained) -> Phase C (HP reduction only if required)

> This TC does **not** validate boot-time configuration or standalone PCT frequency separation outside the power-constrained case.

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| 1 | Platform boots with PCT enabled (PCT Partition Count >= 2; default = 4) |
| 2 | SST-TF active; SST_CP_CONTROL.sst_cp_priority_type = 1 (Ordered Throttling) |
| 3 | HP cores assigned to CLOS[0]; LP cores to CLOS[3] |
| 4 | RAPL PL1 programmed below active platform power to force throttling |
| 5 | Sustained CPU workload on all active cores |
| 6 | No unrelated thermal/external limiter dominating the result |
| 7 | 
unPmx.py available with NWP XML (
wp.xml) |

### Recommended Baseline Registers

| Register | Purpose |
|----------|---------|
| SST_CP_CONTROL.sst_cp_priority_type | Confirm Ordered Throttling = 1 |
| SST_CLOS_ASSOC[] | HP/LP core mapping |
| SST_CLOS_CONFIG[0].max | HP ceiling = SST_TF_INFO_2.RATIO_0 |
| SST_CLOS_CONFIG[3].max | LP clip = SST_TF_INFO_0.LP_CLIP_RATIO_0 |
| TPMI PERF_STATUS.PWR_LIMIT_THROTTLE_CTR | RAPL throttle accounting |
| IA32_PERF_STATUS (MSR 0x198) | Per-core frequency observation |
| TPMI PL1_CONTROL | Confirm active RAPL PL1 value |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Confirm SST_CP_PRIORITY_TYPE = 1 (Ordered Throttling) per CBB | Ordered Throttling configured | != 1 |
| 2 | Program RAPL PL1 below current platform power; apply sustained workload | RAPL enforcement active; PERF_STATUS counter increments | RAPL not enforcing |
| 3 | Read LP core effective frequency via IA32_PERF_STATUS (MSR 0x198) | LP cores reduce first below unconstrained operating point | LP cores not reduced first |
| 4 | Read HP core effective frequency via IA32_PERF_STATUS (MSR 0x198) | HP cores remain at/near PCT TRL while LP cores still have reduction headroom | HP cores reduced before LP-first behavior exhausted |
| 5 | Compare HP vs LP during convergence window | Clear LP-first priority: LP throttled more than HP during Phase A/B | Simultaneous or inverted throttle order |
| 6 | Verify TPMI PERF_STATUS.PWR_LIMIT_THROTTLE_CTR increments under load | Counter active; RAPL is the limiter | No throttle accounting |
| 7 | Observe through convergence; confirm ordering rule maintained | Ordered phase behavior consistent throughout | No observable ordered throttling |
| 8 | Run automation: 
unPmx.py -x nwp.xml -p pct -tM 60 -M 10 --retry_count 2 | Automation PASS | Script FAIL or timeout |

### Pass / Fail Criteria

**PASS**: RAPL PL1 enforces power budget; LP cores throttled first (Phase A behavior); HP cores maintain PCT TRL while LP cores still have remaining reduction headroom; PERF_STATUS shows active throttle; ordering rule preserved throughout convergence; automation passes.

**FAIL**: HP cores throttled before LP-first behavior observed; no observable LP-first throttle order; Ordered Throttling not functioning; RAPL not enforcing; automation fails.

### Post-Process

Save: TPMI snapshots (before/during), per-core HP/LP frequency observations across convergence window, PERF_STATUS deltas, automation log, active RAPL PL1 value.

### Reference Documents

- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — Ordered Throttling phases, CLOS priority model
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST_CP_CONTROL.sst_cp_priority_type, SST_CLOS_CONFIG
- [Intel RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html) — TPMI PERF_STATUS, Socket RAPL PL1 algorithm
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP RAPL x PCT integration
- [PCT KB — pct.md](../../../pm_features/sst/pct.md)
- [CCB HSD 14026595435](https://hsdes.intel.com/appstore/article-one/#/14026595435) — NWP PCT target: 8 HP cores, ~4.4 GHz

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This PCT test verifies TDP convergence behavior: under RAPL PL1 enforcement, LP cores are throttled first while HP cores maintain their PCT frequency. SST-TF RAPL integration is functional on NWP.

Tags: `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p pct -tM 60 -M 10 --retry_count 2
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Enable PCT via BIOS knob (PCT Partition Count = 4) | 8 HP cores across 4 partitions of 24 |
| 2 | Run PTAT on all 96 cores to generate sustained power load | `ptat --all-cores --sustained` |
| 3 | Set RAPL PL1 to TDP value via TPMI SOCKET_RAPL_PL1_CONTROL | MSR 0x610 deprecated on NWP (HSD 14018460453) |
| 4 | Verify power converges to PL1 (monitor SOCKET_RAPL_ENERGY_STATUS) | Read via TPMI, not MSR 0x611 |
| 5 | When power-limited: read SST_CLOS_ASSOC + per-core frequency | LP cores should drop first |
| 6 | Confirm LP cores reach minimum freq (LP_CLIP_RATIO from SST_TF_INFO_0) | Before any HP reduction |
| 7 | Confirm HP cores maintain PCT TRL freq (SST_TF_INFO_2.RATIO_0 = 4.4 GHz) | HP priority preserved |
| 8 | Gradually increase PL1 — verify HP cores recover frequency before LP | Confirms ordered priority |
| 9 | Read SST_CP_CONTROL.SST_CP_PRIORITY_TYPE = 1 (Ordered Throttling) | Verify register set by BIOS |

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | BIOS | Enable PCT Partition Count = 4; program SST_CP_PRIORITY_TYPE = 1 | TPMI MMIO |
| 2 | BIOS | Program SOCKET_RAPL_PL1_CONTROL.PWR_LIM = TDP; PWR_LIM_EN = 1 | TPMI MMIO |
| 3 | OS/Test | Launch PTAT on all 96 cores | Kernel |
| 4 | PCode (CBB×2) | RAPL PID samples socket power (1ms loop) | HW counters |
| 5 | PCode (CBB×2) | PL1 exceeded: apply ordered throttle — LP cores drop frequency first | CLOS priority |
| 6 | HW (LP Core) | LP core frequency reduced toward LP_CLIP_RATIO minimum | PLL / FIVR |
| 7 | PCode (CBB×2) | Verify HP cores at SST_TF_INFO_2.RATIO_0 (4.4 GHz) while LP constrained | CLOS enforcement |
| 8 | OS/Test | Read SST_CLOS_ASSOC per core — confirm HP/LP assignment unchanged | TPMI MMIO |
| 9 | OS/Test | Read per-core frequency — LP < LP_CLIP, HP ≥ PCT TRL | MSR / TPMI |
| 10 | OS/Test | Read SOCKET_RAPL_ENERGY_STATUS — confirm power ≤ PL1 | TPMI MMIO |
| 11 | OS/Test | Increase PL1 — verify HP cores recover before LP frequency rises | TPMI MMIO |

### Sequence Data

| # | From | To | Message | Interface |
|---|------|----|---------|-----------|
| 1 | BIOS | TPMI SRAM | Write SOCKET_RAPL_PL1_CONTROL: PWR_LIM=TDP, PWR_LIM_EN=1 | TPMI MMIO |
| 2 | BIOS | TPMI SRAM | Write SST_CP_CONTROL.SST_CP_PRIORITY_TYPE = 1 (Ordered) | TPMI MMIO |
| 3 | PCode | HW counters | Sample socket power (RAPL energy accumulator, 1ms) | HW ring |
| 4 | PCode | CLOS arbiter | PL1 exceeded: generate ordered throttle — LP CLOS first | Internal |
| 5 | PCode | LP Core FIVR | Reduce LP frequency to LP_CLIP floor | HW wire |
| 6 | PCode | HP Core FIVR | Maintain HP frequency at SST_TF_INFO_2.RATIO_0 | HW wire |
| 7 | Test | TPMI SRAM | Read SOCKET_RAPL_ENERGY_STATUS — verify power convergence | TPMI MMIO |
| 8 | Test | TPMI SRAM | Read per-core SST_CLOS_ASSOC — confirm mapping intact | TPMI MMIO |
| 9 | Test | Core | Read per-core freq (via PSTATE_REQ or APERF/MPERF) | MSR |
| 10 | Test | TPMI SRAM | Adjust SOCKET_RAPL_PL1_CONTROL.PWR_LIM — verify priority recovery | TPMI MMIO |

### Pass Criteria

- Power converges to PL1 with PCT enabled
- `SST_CP_CONTROL.SST_CP_PRIORITY_TYPE = 1` confirmed (Ordered Throttling active)
- LP cores are prioritized for throttling (frequency drops before HP)
- HP cores maintain PCT TRL frequency while LP cores still above minimum
- HP TRL only reduced after LP cores reach LP_CLIP minimum frequency
- PCT priority ordering respected during RAPL enforcement

---

## Section C: Interface Coverage Assessment

| Interface | Type | Register / Address | Covered by TC? | Notes |
|-----------|------|--------------------|-----------------|-------|
| SOCKET_RAPL_PL1_CONTROL | TPMI | PWR_LIM, TIME_WINDOW, PWR_LIM_EN | **Yes** | Primary: set PL1 to TDP; NWP MSR deprecated |
| SOCKET_RAPL_ENERGY_STATUS | TPMI | Energy accumulator | **Yes** | Verify power converges ≤ PL1 |
| SST_CP_CONTROL | TPMI | SST_CP_PRIORITY_TYPE = 1 | **Yes** | Ordered throttling pre-condition |
| SST_CLOS_ASSOC | TPMI | Per-core CLOS assignment | **Yes** | Verify HP/LP intact under throttle |
| SST_TF_INFO_0 | TPMI | LP_CLIP_RATIO_0 | Partial | Implicit via frequency check |
| SST_TF_INFO_2 | TPMI | HP TRL ratio (4.4 GHz) | Partial | Implicit via HP frequency check |
| Per-core frequency | MSR/APERF | Actual operating frequency | **Should add** | APERF/MPERF ratio or P_STATE_REQ |
| MSR 0x610 | MSR | PKG_POWER_LIMIT | **No** | Deprecated on NWP — TPMI used |

---

## Section D: NWP Specification References

| Document | Link | Relevance |
|----------|------|-----------|
| PCT HAS | [PCT Architecture Spec](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) | Primary: ordered throttling with RAPL |
| Intel SST HAS | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) | SST_CP_PRIORITY_TYPE=1 ordered throttle mechanism |
| CBB SST Manager FAS | [CBB SST Manager FAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/FAS/SST_manager/cbb_SST_manager_FAS.html) | PCode RAPL PID + CLOS ordered throttle |
| NWP PM MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | Socket RAPL functional; TPMI interface |
| BIOS HSD 14018460453 | [HSD 14018460453](https://hsdes.intel.com/appstore/article/#/14018460453) | RAPL MSR deprecated on NWP |
| NWP PCT CCB | [HSD 14026595435](https://hsdes.intel.com/appstore/article/#/14026595435) | 8 HP cores, 4.4 GHz target |

---

## Section E: NWP Risk Assessment

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|------------|--------|------------|
| 1 | **RAPL MSR usage**: Test may attempt MSR 0x610/0x638 for PL1; these are deprecated on NWP | High | High | Ensure test uses TPMI SOCKET_RAPL_PL1_CONTROL path |
| 2 | **Power measurement**: PTAT workload power on 96-core NWP may exceed TDP differently than DMR 128-core; convergence time longer | Medium | Medium | Extend timeout (`-tM 60` → 90s) if needed |
| 3 | **LP minimum floor**: NWP LP_CLIP ratio may differ from DMR SKU; test must dynamically read SST_TF_INFO_0, not hardcode | Medium | Medium | Read LP_CLIP from TPMI before asserting LP frequency |
| 4 | **APERF/MPERF accuracy**: Frequency verification via APERF/MPERF requires sampling window; short windows may misread transients | Low | Low | Sample ≥ 100ms per core after steady state |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; RAPL TDP convergence with PCT functional; use TPMI for PL1 (MSR deprecated)**

**Priority**: Medium — `plc.feature.p1`; TDP convergence with HP priority is the key differentiation of PCT over flat turbo
