# TCD: Solar C-state x Legacy P-state x DVFS Random Stress

| Field | Value |
|-------|-------|
| **TCD ID** | [16031172973](https://hsdes.intel.com/appstore/article-one/#/16031172973) |
| **Title** | Solar C-state x Legacy P-state x DVFS Random Stress |
| **Status** | open |
| **Owner** | thangama |
| **Parent TPF** | [22022562325 — PM Integration Testing](https://hsdes.intel.com/appstore/article-one/#/22022562325) |
| **Parent TP** | [16030765631 — PM Cross Product](https://hsdes.intel.com/appstore/article-one/#/16030765631) |
| **KB last updated** | 2026-07-20 |
| **Feature** | Power / PM Cross-product — C-state x Legacy P-state x DVFS concurrent interaction |

## Section 1: Architecture / Micro-architecture and Functionality

Validates that concurrent C-state entry/exit transitions, legacy (non-HWP) P-state requests, and DVFS workpoint transitions coexist without hang, MCA, or frequency misresolution. The legacy P-state arbiter resolves requests through a different path than HWP — this TCD specifically validates the non-HWP arbitration logic under C-state churn.

> **Architecture overview:** See [TPF 22022562325 — PM Integration Testing](https://hsdes.intel.com/appstore/article-one/#/22022562325) Section 2 Design Details for cross-product interaction architecture.

### NWP-Specific Deltas

- NWP has 2 CBBs (96 cores) vs DMR up to 4 CBBs
- PkgC6 is ZBB on NWP — C-state limited to CC6
- Legacy P-state uses TPMI on NWP; deprecated MSR 0x199 (IA32_PERF_CTL) path
- NWP supports both HWP and legacy P-state modes — distinct validation paths required

### TC Coverage Map

| TC | Scope | Environment |
|----|-------|-------------|
| [22022421709 — cstate_legacy_pstate_p0_pn_pstate_dvfs_random](https://hsdes.intel.com/appstore/article-one/#/22022421709) | Random C-state + legacy P-state + DVFS, P0 floor | FV (silicon) |
| [22022421710 — cstate_legacy_pstate_p0_pn_pstate_dvfs_random_exercise](https://hsdes.intel.com/appstore/article-one/#/22022421710) | Same + post-stimulus state verification | FV (silicon) |
| [22022421712 — cstate_legacy_pstate_p1_pn_pstate_dvfs_random](https://hsdes.intel.com/appstore/article-one/#/22022421712) | Random C-state + legacy P-state + DVFS, P1 floor | FV (silicon) |
| [22022421714 — cstate_legacy_pstate_p1_pn_pstate_dvfs_random_exercise](https://hsdes.intel.com/appstore/article-one/#/22022421714) | Same + post-stimulus state verification | FV (silicon) |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Role in This Scenario |
|-----------|----------------|----------------------|
| TPMI | PERF_CTL (TPMI) | Legacy P-state request — sets target ratio |
| TPMI | PERF_STATUS | Current granted P-state readback |
| MSR | IA32_MPERF / IA32_APERF | Effective frequency measurement |
| CSR/PMSB | C-state residency counters | Core C6 entry/exit confirmation |
| HPM | DVFS target/actual | DVFS transition completion |

---

## Section 3: Reset, Power, and Clocking

- Scenario begins after full boot with HWP disabled (legacy P-state mode)
- Legacy P-state request latched before C-state entry; re-evaluated on exit
- DVFS transitions serialized with C-state exit by hardware
- P-state floor (P0 vs P1) determines minimum allowed operating point

---

## Section 4: Programming Model

Legacy P-state mode requests are programmed via TPMI PERF_CTL on NWP. Unlike HWP (which uses a min/max/desired triple), legacy mode uses a single target ratio. The CCP DVFS architecture services legacy requests through the same GV sequencer but with different arbitration input.

The interaction under test: legacy P-state requests arriving concurrently with C-state transitions and DVFS must resolve to the correctly arbitrated result — the final workpoint matches the legal legacy P-state outcome per the granted ratio.

---

## Section 5: Operational Behavior

### Pass/Fail Bar

| Criterion | Measurable Threshold | Spec Basis |
|-----------|---------------------|-----------|
| No MCA | Zero MCAs logged during and after stimulus | Architecture invariant |
| No hang | Test completes within timeout | Architecture invariant |
| Legacy P-state arbitration | Final frequency resolves to the correctly arbitrated legacy P-state result | CCP PM HAS: workpoint transitions |
| C-state non-interference | C-state churn does not prevent DVFS/P-state transition sequence completion | DMR Fabric DVFS HAS: C-state cross-product |
| PERF_STATUS consistency | PERF_STATUS reads reflect the granted ratio after transition settles | NWP IMH SoC PM MAS |

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| Legacy P-state request during C6 exit | Race between wakeup and frequency change | Covered by random stimulus timing | No action |
| P0 request at Pn floor | Maximum frequency request at minimum floor | Explicitly tested in P0 variants | No action |
| Rapid P-state toggling during C-state transitions | Multiple requests per C6 exit cycle | Covered by random stimulus | No action |
| DVFS in progress when legacy request arrives | DVFS/P-state request collision | Implicit in random — exercise variant verifies | Verify in exercise variant |

---

## Section 7: Security / Safety / Policy

- Legacy P-state interface is OS-owned (kernel cpufreq driver)
- No security-sensitive interaction in this cross-product

---

## Section 8: References

- [CCP PM HAS](https://docs.intel.com/documents/pm_doc/src/server/wave3_common/ccp/converged core perimeter pm has.html) — DVFS/GV workpoint transitions, legacy P-state handling
- [DMR Fabric DVFS HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM Features/DMR_Fabric_DVFS.html) — C-state cross-product table
- [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP P-state feature support, legacy mode
- [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/has/cbb overview/dmr_cbb_power_management.html) — CBB DVFS support
