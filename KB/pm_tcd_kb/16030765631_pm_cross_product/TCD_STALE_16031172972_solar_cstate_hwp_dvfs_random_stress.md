# TCD: Solar C-state x HWP x DVFS Random Stress

| Field | Value |
|-------|-------|
| **TCD ID** | [16031172972](https://hsdes.intel.com/appstore/article-one/#/16031172972) |
| **Title** | Solar C-state x HWP x DVFS Random Stress |
| **Status** | open |
| **Owner** | thangama |
| **Parent TPF** | [22022562325 — PM Integration Testing](https://hsdes.intel.com/appstore/article-one/#/22022562325) |
| **Parent TP** | [16030765631 — PM Cross Product](https://hsdes.intel.com/appstore/article-one/#/16030765631) |
| **KB last updated** | 2026-07-20 |
| **Feature** | Power / PM Cross-product — C-state x HWP x DVFS concurrent interaction |

## Section 1: Architecture / Micro-architecture and Functionality

Validates that concurrent C-state entry/exit transitions, HWP-requested P-state changes, and DVFS workpoint transitions coexist without hang, MCA, or frequency misresolution. The HWP arbiter must resolve accepted requests to spec-valid target operating points even under random C-state churn that suspends and resumes core frequency domains.

> **Architecture overview:** See [TPF 22022562325 — PM Integration Testing](https://hsdes.intel.com/appstore/article-one/#/22022562325) Section 2 Design Details for cross-product interaction architecture.

### NWP-Specific Deltas

- NWP has 2 CBBs (96 cores) vs DMR up to 4 CBBs — reduces cross-CBB interaction surface
- PkgC6 is ZBB on NWP — C-state depth limited to CC6 (core C6)
- HWP uses TPMI interface on NWP; legacy MSR 0x774 (HWP_REQUEST) deprecated
- IMH2 replaces IMH1 — uncore frequency managed differently from DMR

### TC Coverage Map

| TC | Scope | Environment |
|----|-------|-------------|
| [22022421701 — cstate_hwp_p0_pn_dvfs_random](https://hsdes.intel.com/appstore/article-one/#/22022421701) | Random C-state + HWP + DVFS, P0 floor | FV (silicon) |
| [22022421702 — cstate_hwp_p0_pn_dvfs_random_exercise](https://hsdes.intel.com/appstore/article-one/#/22022421702) | Same + post-stimulus state verification | FV (silicon) |
| [22022421705 — cstate_hwp_p1_pn_dvfs_random](https://hsdes.intel.com/appstore/article-one/#/22022421705) | Random C-state + HWP + DVFS, P1 floor | FV (silicon) |
| [22022421706 — cstate_hwp_p1_pn_dvfs_random_exercise](https://hsdes.intel.com/appstore/article-one/#/22022421706) | Same + post-stimulus state verification | FV (silicon) |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Role in This Scenario |
|-----------|----------------|----------------------|
| TPMI | HWP_REQUEST (TPMI) | HWP P-state request — sets desired operating point |
| TPMI | HWP_CAPABILITIES | Defines legal P-state range (Pn..P0) per core class |
| MSR | IA32_MPERF / IA32_APERF | Effective frequency measurement |
| MSR | IA32_PM_ENABLE | HWP enable/disable |
| CSR/PMSB | C-state residency counters | Core C6 entry/exit confirmation |
| HPM | DVFS target/actual | DVFS transition completion |

---

## Section 3: Reset, Power, and Clocking

- Scenario begins after full boot with HWP enabled (BIOS CPL3 handoff)
- C-state entry gates core clock; C-state exit restores clock and triggers DVFS re-evaluation
- HWP request is latched before C-state entry; on exit, PCode re-evaluates HWP target
- DVFS transitions may overlap with C-state exit — hardware must serialize correctly

---

## Section 4: Programming Model

HWP requests are programmed via TPMI HWP_REQUEST on NWP (replacing legacy MSR 0x774). The CCP DVFS architecture defines that workpoint transitions converge to the target operating point through a defined GV sequence. C-state entry suspends core frequency domain; exit triggers re-evaluation.

The interaction under test: when HWP requests arrive concurrently with C-state transitions and DVFS is actively changing workpoints, the hardware must not deadlock, produce an illegal frequency, or corrupt the P-state request pipeline.

---

## Section 5: Operational Behavior

### Pass/Fail Bar

| Criterion | Measurable Threshold | Spec Basis |
|-----------|---------------------|-----------|
| No MCA | Zero MCAs logged during and after stimulus | Architecture invariant |
| No hang | Test completes within timeout (no core/thread stuck) | Architecture invariant |
| Frequency convergence | After stimulus stops, APERF/MPERF ratio settles within HWP_CAP legal band | CCP PM HAS: DVFS/GV target-OP transition |
| C-state non-interference | Fabric DVFS requests complete despite C-state churn | DMR Fabric DVFS HAS: "C-State Change should not have impact on request" |

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| All cores in C6 during DVFS | DVFS transition with no active core | Covered by random stimulus (high C6 probability) | No action |
| HWP MIN > current DVFS floor | Request above DVFS-allowed range | Partial — depends on random config | Verify in exercise variant |
| Rapid C6 entry/exit oscillation | Sub-microsecond transitions during DVFS | Covered by random stimulus timing | No action |
| P0 floor with aggressive C-state | High-frequency floor + deep sleep | Explicitly tested in P0 variants | No action |

---

## Section 7: Security / Safety / Policy

- HWP requests are OS-owned; test must not bypass OS interface to avoid invalid state
- Energy-related side-channel: not in scope for this cross-product (separate TCD)

---

## Section 8: References

- [CCP PM HAS](https://docs.intel.com/documents/pm_doc/src/server/wave3_common/ccp/converged core perimeter pm has.html) — DVFS/GV target-OP transitions, HWP architecture
- [DMR Fabric DVFS HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM Features/DMR_Fabric_DVFS.html) — C-State cross-product table
- [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP P-state and C-state feature support
- [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/has/cbb overview/dmr_cbb_power_management.html) — CBB DVFS support
