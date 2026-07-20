# TCD: Solar P-state x DVFS Isolated Interaction

| Field | Value |
|-------|-------|
| **TCD ID** | [16031172975](https://hsdes.intel.com/appstore/article-one/#/16031172975) |
| **Title** | Solar P-state x DVFS Isolated Interaction |
| **Status** | open |
| **Owner** | thangama |
| **Parent TPF** | [22022562325 — PM Integration Testing](https://hsdes.intel.com/appstore/article-one/#/22022562325) |
| **Parent TP** | [16030765631 — PM Cross Product](https://hsdes.intel.com/appstore/article-one/#/16030765631) |
| **KB last updated** | 2026-07-20 |
| **Feature** | Power / PM Cross-product — Isolated P-state x DVFS interaction (no C-state stimulus) |

## Section 1: Architecture / Micro-architecture and Functionality

Validates that P-state-requested workpoint changes and DVFS transitions coexist correctly when no C-state stimulus is present. This isolates the P-state/DVFS frequency resolution path from C-state clock-gating complexity, testing that the GV sequencer correctly resolves the final voltage/frequency operating point under random P-state requests.

> **Architecture overview:** See [TPF 22022562325 — PM Integration Testing](https://hsdes.intel.com/appstore/article-one/#/22022562325) Section 2 Design Details for cross-product interaction architecture.

### NWP-Specific Deltas

- NWP has 2 CBBs (96 cores) vs DMR up to 4 CBBs
- P-state uses TPMI interface on NWP (both HWP and legacy modes)
- DVFS workpoint transitions follow CCP DVFS architecture
- No C-state involvement — cores remain in C0 throughout

### TC Coverage Map

| TC | Scope | Environment |
|----|-------|-------------|
| [22022421718 — pstate_dvfs_random](https://hsdes.intel.com/appstore/article-one/#/22022421718) | Random P-state + DVFS, no C-state stimulus | FV (silicon) |
| [22022421719 — pstate_dvfs_random_exercise](https://hsdes.intel.com/appstore/article-one/#/22022421719) | Same + post-stimulus state verification | FV (silicon) |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Role in This Scenario |
|-----------|----------------|----------------------|
| TPMI | HWP_REQUEST or PERF_CTL | P-state frequency request |
| TPMI | HWP_CAPABILITIES or PERF_STATUS | Legal frequency range / granted state |
| MSR | IA32_MPERF / IA32_APERF | Effective frequency measurement |
| HPM | DVFS target/actual | DVFS workpoint transition status |

---

## Section 3: Reset, Power, and Clocking

- Scenario begins after full boot; C-states disabled or held at C0
- All cores remain active — clock domains never gated
- P-state requests drive GV sequencer; DVFS responds to power budget changes
- Tests the frequency resolution path without clock-domain boundary interaction

---

## Section 4: Programming Model

P-state requests (HWP or legacy) are programmed via TPMI. The CCP DVFS architecture defines workpoint transitions through the GV sequencer. When no C-state stimulus is present, the GV sequencer only handles P-state-driven transitions and power-budget-driven DVFS — there is no clock ungating race.

The interaction under test: random P-state requests arriving concurrently with DVFS transitions must produce a final V/F that matches the resolved P-state/DVFS target operating point. No illegal intermediate frequencies or deadlocks.

---

## Section 5: Operational Behavior

### Pass/Fail Bar

| Criterion | Measurable Threshold | Spec Basis |
|-----------|---------------------|-----------|
| No MCA | Zero MCAs logged during and after stimulus | Architecture invariant |
| No hang | Test completes within timeout | Architecture invariant |
| V/F correctness | Final voltage/frequency matches the resolved P-state/DVFS target operating point | CCP PM HAS: workpoint transition correctness |
| Operating point legality | Frequency always within HWP_CAP or granted-ratio legal range | NWP IMH SoC PM MAS: P-state feature support |

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| Rapid P-state request changes | Multiple requests before prior DVFS completes | Covered by random stimulus | No action |
| P0 max request during power-limited DVFS | Max frequency vs power budget conflict | Covered by random config | No action |
| Pn min request during high DVFS demand | Minimum request contradicts DVFS upscale | Covered by random stimulus | No action |
| DVFS transition in progress when request arrives | GV sequencer busy at request time | Covered by random timing | No action |

---

## Section 7: Security / Safety / Policy

- P-state requests are OS-owned; test respects OS interface boundaries
- No security-sensitive interaction in this isolated cross-product

---

## Section 8: References

- [CCP PM HAS](https://docs.intel.com/documents/pm_doc/src/server/wave3_common/ccp/converged core perimeter pm has.html) — DVFS/GV workpoint transition correctness, P-state architecture
- [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP P-state feature support
- [DMR Fabric DVFS HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM Features/DMR_Fabric_DVFS.html) — DVFS transition architecture
- [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/has/cbb overview/dmr_cbb_power_management.html) — CBB DVFS support
