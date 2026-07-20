# TCD: Solar C-state x Legacy P-state x Core GV Random Stress

| Field | Value |
|-------|-------|
| **TCD ID** | [16031172980](https://hsdes.intel.com/appstore/article-one/#/16031172980) |
| **Title** | Solar C-state x Legacy P-state x Core GV Random Stress |
| **Status** | open |
| **Owner** | thangama |
| **Parent TPF** | [22022562325](https://hsdes.intel.com/appstore/article-one/#/22022562325) |
| **Parent TP** | [16030765631 - PM Cross Product](https://hsdes.intel.com/appstore/article-one/#/16030765631) |
| **KB last updated** | 2026-07-20 |
| **Feature** | Power / PM Cross-product - C-state x Legacy P-state x Core GV |

## Section 1: Architecture / Micro-architecture and Functionality

Validates that concurrent C-state entry/exit, legacy (non-HWP) P-state requests, and core GV workpoint transitions coexist without hang, MCA, or frequency misresolution. Legacy P-state arbitration uses a different path than HWP - this TCD validates the non-HWP arbitration logic under C-state churn.

> **Architecture overview:** See [TPF 22022562325](https://hsdes.intel.com/appstore/article-one/#/22022562325) Section 2

### NWP-Specific Deltas

- NWP has 2 CBBs (96 cores) vs DMR up to 4
- PkgC6 ZBB on NWP - C-state limited to CC6
- Legacy P-state uses TPMI on NWP; MSR 0x199 deprecated
- **No IMH-side fabric DVFS on NWP** - Core GV is CBB-side only

### TC Coverage Map

| TC | Scope | Environment |
|----|-------|-------------|
| [22022421709](https://hsdes.intel.com/appstore/article-one/#/22022421709) | cstate_legacy_pstate_p0_pn_pstate_dvfs_random | FV (silicon) |
| [22022421710](https://hsdes.intel.com/appstore/article-one/#/22022421710) | cstate_legacy_pstate_p0_pn_pstate_dvfs_random_exercise | FV (silicon) |
| [22022421712](https://hsdes.intel.com/appstore/article-one/#/22022421712) | cstate_legacy_pstate_p1_pn_pstate_dvfs_random | FV (silicon) |
| [22022421714](https://hsdes.intel.com/appstore/article-one/#/22022421714) | cstate_legacy_pstate_p1_pn_pstate_dvfs_random_exercise | FV (silicon) |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Role |
|-----------|----------------|------|
| TPMI | PERF_CTL | Legacy P-state target ratio |
| TPMI | PERF_STATUS | Granted P-state readback |
| MSR | IA32_MPERF / IA32_APERF | Effective frequency |
| CSR/PMSB | C-state residency counters | CC6 entry/exit |
| CBB internal | GV sequencer | Core V/F transition |

---

## Section 3: Reset, Power, and Clocking

- Scenario begins with HWP disabled (legacy P-state mode)
- Legacy P-state request latched before C-state entry; re-evaluated on exit
- Core GV transitions serialized with C-state exit by hardware
- P-state floor (P0 vs P1) determines minimum operating point

---

## Section 4: Programming Model

Legacy P-state via TPMI PERF_CTL on NWP. Single target ratio (unlike HWP min/max/desired triple). CCP GV architecture services legacy requests through same sequencer but different arbitration input. No IMH-side DVFS on NWP.

---

## Section 5: Operational Behavior

### Pass/Fail Bar

| Criterion | Measurable Threshold | Spec Basis |
|-----------|---------------------|-----------|
| No MCA | Zero MCAs during and after stimulus | Architecture invariant |
| No hang | Test completes within timeout | Architecture invariant |
| Legacy P-state arbitration | Frequency resolves to correctly arbitrated legacy result | CCP PM HAS: workpoint transitions |
| C-state non-interference | C-state churn does not prevent GV completion | DMR Fabric DVFS HAS |
| PERF_STATUS consistency | Reflects granted ratio after settle | NWP IMH SoC PM MAS |

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| Legacy request during C6 exit | Wakeup/freq race | Covered by random timing | No action |
| P0 request at Pn floor | Max freq at min floor | Explicit in P0 variants | No action |
| Rapid P-state toggling during C-state | Multiple requests per exit | Covered by random | No action |
| GV busy when legacy request arrives | Request collision | Implicit - exercise verifies | No action |

---

## Section 7: Security / Safety / Policy

- Legacy P-state interface is OS-owned (kernel cpufreq)
- No security-sensitive interaction

---

## Section 8: References

- [CCP PM HAS](https://docs.intel.com/documents/pm_doc/src/server/wave3_common/ccp/converged core perimeter pm has.html)
- [DMR Fabric DVFS HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM Features/DMR_Fabric_DVFS.html)
- [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
