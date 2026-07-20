# TCD: Solar Isolated P-state HWP Frequency Selection

| Field | Value |
|-------|-------|
| **TCD ID** | [16031172982](https://hsdes.intel.com/appstore/article-one/#/16031172982) |
| **Title** | Solar Isolated P-state HWP Frequency Selection |
| **Status** | open |
| **Owner** | thangama |
| **Parent TPF** | [22022562325](https://hsdes.intel.com/appstore/article-one/#/22022562325) |
| **Parent TP** | [16030765631 - PM Cross Product](https://hsdes.intel.com/appstore/article-one/#/16030765631) |
| **KB last updated** | 2026-07-20 |
| **Feature** | Power / PM Cross-product - Isolated P-state/HWP frequency (no C-state) |

## Section 1: Architecture / Micro-architecture and Functionality

Validates that P-state-requested workpoint changes and core GV transitions coexist correctly when no C-state stimulus is present. Cores remain in C0 throughout; isolates the P-state/GV frequency resolution path from C-state clock-gating complexity.

> **Architecture overview:** See [TPF 22022562325](https://hsdes.intel.com/appstore/article-one/#/22022562325) Section 2

### NWP-Specific Deltas

- NWP 2 CBBs (96 cores); P-state via TPMI
- **No IMH-side fabric DVFS** - Core GV is CBB-side only
- No C-state involvement - cores remain in C0

### TC Coverage Map

| TC | Scope | Environment |
|----|-------|-------------|
| [22022421718](https://hsdes.intel.com/appstore/article-one/#/22022421718) | pstate_dvfs_random | FV (silicon) |
| [22022421719](https://hsdes.intel.com/appstore/article-one/#/22022421719) | pstate_dvfs_random_exercise | FV (silicon) |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Role |
|-----------|----------------|------|
| TPMI | HWP_REQUEST or PERF_CTL | P-state request |
| TPMI | HWP_CAPABILITIES / PERF_STATUS | Legal range / granted |
| MSR | IA32_MPERF / IA32_APERF | Effective frequency |
| CBB internal | GV sequencer | V/F transition |

---

## Section 3: Reset, Power, and Clocking

- C-states disabled or held at C0; all cores active
- P-state requests drive GV sequencer; no clock-domain boundary race
- Tests frequency resolution path without clock ungating interaction

---

## Section 4: Programming Model

P-state requests (HWP or legacy) via TPMI. GV sequencer handles P-state-driven transitions. No C-state clock gating - only P-state and power-budget DVFS.

---

## Section 5: Operational Behavior

### Pass/Fail Bar

| Criterion | Measurable Threshold | Spec Basis |
|-----------|---------------------|-----------|
| No MCA | Zero MCAs | Architecture invariant |
| No hang | Test completes within timeout | Architecture invariant |
| V/F correctness | Final V/F matches resolved P-state/GV target | CCP PM HAS: workpoint correctness |
| Operating point legality | Frequency within HWP_CAP legal range | NWP IMH SoC PM MAS |

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| Rapid P-state changes | Multiple before prior GV completes | Covered by random | No action |
| P0 max vs power limit | Max freq vs budget conflict | Covered by random | No action |
| Pn min vs high GV demand | Min request contradicts upscale | Covered by random | No action |

---

## Section 7: Security / Safety / Policy

- P-state requests OS-owned; test respects interface boundaries

---

## Section 8: References

- [CCP PM HAS](https://docs.intel.com/documents/pm_doc/src/server/wave3_common/ccp/converged core perimeter pm has.html)
- [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [DMR Fabric DVFS HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM Features/DMR_Fabric_DVFS.html)
