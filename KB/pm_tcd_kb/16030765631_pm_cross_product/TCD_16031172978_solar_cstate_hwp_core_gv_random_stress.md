# TCD: Solar C-state x HWP x Core GV Random Stress

| Field | Value |
|-------|-------|
| **TCD ID** | [16031172978](https://hsdes.intel.com/appstore/article-one/#/16031172978) |
| **Title** | Solar C-state x HWP x Core GV Random Stress |
| **Status** | open |
| **Owner** | thangama |
| **Parent TPF** | [22022562325](https://hsdes.intel.com/appstore/article-one/#/22022562325) |
| **Parent TP** | [16030765631 - PM Cross Product](https://hsdes.intel.com/appstore/article-one/#/16030765631) |
| **KB last updated** | 2026-07-20 |
| **Feature** | Power / PM Cross-product - C-state x HWP x Core GV concurrent interaction |

## Section 1: Architecture / Micro-architecture and Functionality

Validates that concurrent C-state entry/exit transitions, HWP-requested P-state changes, and core GV workpoint transitions coexist without hang, MCA, or frequency misresolution. The HWP arbiter must resolve accepted requests to spec-valid target operating points even under random C-state churn that suspends and resumes core frequency domains.

> **Architecture overview:** See [TPF 22022562325 - PM Integration Testing](https://hsdes.intel.com/appstore/article-one/#/22022562325) Section 2 Design Details

### NWP-Specific Deltas

- NWP has 2 CBBs (96 cores) vs DMR up to 4 CBBs
- PkgC6 is ZBB on NWP - C-state depth limited to CC6
- HWP uses TPMI interface on NWP; legacy MSR 0x774 deprecated
- **No IMH-side fabric DVFS on NWP** - Core GV is CBB-side only
- IMH2 replaces IMH1 - uncore frequency is fixed

### TC Coverage Map

| TC | Scope | Environment |
|----|-------|-------------|
| [22022421701](https://hsdes.intel.com/appstore/article-one/#/22022421701) | cstate_hwp_p0_pn_dvfs_random | FV (silicon) |
| [22022421702](https://hsdes.intel.com/appstore/article-one/#/22022421702) | cstate_hwp_p0_pn_dvfs_random_exercise | FV (silicon) |
| [22022421705](https://hsdes.intel.com/appstore/article-one/#/22022421705) | cstate_hwp_p1_pn_dvfs_random | FV (silicon) |
| [22022421706](https://hsdes.intel.com/appstore/article-one/#/22022421706) | cstate_hwp_p1_pn_dvfs_random_exercise | FV (silicon) |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Role |
|-----------|----------------|------|
| TPMI | HWP_REQUEST | HWP P-state request |
| TPMI | HWP_CAPABILITIES | Legal P-state range (Pn..P0) |
| MSR | IA32_MPERF / IA32_APERF | Effective frequency measurement |
| MSR | IA32_PM_ENABLE | HWP enable |
| CSR/PMSB | C-state residency counters | CC6 entry/exit |
| CBB internal | GV sequencer | Core voltage/frequency transition |

---

## Section 3: Reset, Power, and Clocking

- Scenario begins after full boot with HWP enabled (BIOS CPL3 handoff)
- C-state entry gates core clock; exit restores and triggers GV re-evaluation
- HWP request latched before C-state entry; on exit PCode re-evaluates target
- Core GV transitions may overlap with C-state exit - hardware serializes

---

## Section 4: Programming Model

HWP requests via TPMI HWP_REQUEST on NWP. CCP architecture defines GV transitions converge to target operating point. C-state entry suspends core frequency domain; exit triggers re-evaluation. No IMH-side DVFS exists on NWP - all frequency changes are CBB core-domain GV.

---

## Section 5: Operational Behavior

### Pass/Fail Bar

| Criterion | Measurable Threshold | Spec Basis |
|-----------|---------------------|-----------|
| No MCA | Zero MCAs during and after stimulus | Architecture invariant |
| No hang | Test completes within timeout | Architecture invariant |
| Frequency convergence | APERF/MPERF settles within HWP_CAP legal band | CCP PM HAS: GV target-OP transition |
| C-state non-interference | Core GV requests complete despite C-state churn | DMR Fabric DVFS HAS: C-State Change non-impact |

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| All cores in C6 during GV | GV with no active core | Covered by random stimulus | No action |
| HWP MIN > current GV floor | Request above allowed range | Partial - random config | Verify in exercise |
| Rapid C6 oscillation | Sub-us transitions during GV | Covered by random timing | No action |
| P0 floor + aggressive C-state | High freq floor + deep sleep | Explicit in P0 variants | No action |

---

## Section 7: Security / Safety / Policy

- HWP requests are OS-owned; test respects OS interface
- Energy side-channel not in scope (separate TCD)

---

## Section 8: References

- [CCP PM HAS](https://docs.intel.com/documents/pm_doc/src/server/wave3_common/ccp/converged core perimeter pm has.html)
- [DMR Fabric DVFS HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM Features/DMR_Fabric_DVFS.html)
- [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/has/cbb overview/dmr_cbb_power_management.html)
