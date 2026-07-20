# TCD: SB Harasser Robustness During PM Transitions

| Field | Value |
|-------|-------|
| **TCD ID** | [16031172983](https://hsdes.intel.com/appstore/article-one/#/16031172983) |
| **Title** | SB Harasser Robustness During PM Transitions |
| **Status** | open |
| **Owner** | thangama |
| **Parent TPF** | [22022562325](https://hsdes.intel.com/appstore/article-one/#/22022562325) |
| **Parent TP** | [16030765631 - PM Cross Product](https://hsdes.intel.com/appstore/article-one/#/16030765631) |
| **KB last updated** | 2026-07-20 |
| **Feature** | Power / PM Cross-product - Sideband harasser traffic during PM state transitions |

## Section 1: Architecture / Micro-architecture and Functionality

Validates that PM state transitions (C-state entry/exit, P-state changes, core GV) complete correctly when sideband harasser traffic is actively stressing the GPSB/PMSB fabrics. The SB harasser is a firmware debug/validation feature that generates periodic configurable sideband messages to stress fabric bandwidth and arbitration.

> **Architecture overview:** See [TPF 22022562325](https://hsdes.intel.com/appstore/article-one/#/22022562325) Section 2

### NWP-Specific Deltas

- NWP IMH2 sideband topology differs from DMR IMH1
- SB harasser configurable via PCode mailbox commands
- No IMH-side fabric DVFS on NWP; CBB GV x SB harasser is in scope

### TC Coverage Map

| TC | Scope | Environment |
|----|-------|-------------|
| [22022423114](https://hsdes.intel.com/appstore/article-one/#/22022423114) | CBB DVFS x SB Harasser traffic | FV (silicon) |
| [22022423116](https://hsdes.intel.com/appstore/article-one/#/22022423116) | PEGA C states x SB Harasser traffic | FV (silicon) |
| [22022423117](https://hsdes.intel.com/appstore/article-one/#/22022423117) | Solar C States x SB Harasser traffic | FV (silicon) |
| [22022423119](https://hsdes.intel.com/appstore/article-one/#/22022423119) | Solar P States x SB Harasser traffic | FV (silicon) |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Role |
|-----------|----------------|------|
| GPSB | Sideband fabric | Harasser traffic path |
| PMSB | PM sideband fabric | PM message path (must not be blocked) |
| PCode mailbox | Harasser config | Enable/disable, rate, pattern |
| CSR/PMSB | PM state handshake | Q-channel, HPM messages |

---

## Section 3: Reset, Power, and Clocking

- SB harasser enabled after boot via PCode mailbox
- PM transitions use same sideband fabric as harasser
- Harasser must not block or corrupt PM handshake messages
- Reset clears harasser state

---

## Section 4: Programming Model

SB harasser configured via PCode mailbox to generate periodic GPSB traffic at configurable rate and pattern. PM transitions (C-state Q-channel handshake, P-state HPM messages, GV commands) share the sideband fabric. The test validates that fabric arbitration correctly prioritizes PM protocol messages over harasser background traffic.

---

## Section 5: Operational Behavior

### Pass/Fail Bar

| Criterion | Measurable Threshold | Spec Basis |
|-----------|---------------------|-----------|
| No hang | PM transitions complete within timeout despite harasser | Sideband arbitration spec |
| No corruption | PM state changes produce correct final state | Architecture invariant |
| No MCA | Zero MCAs | Architecture invariant |
| Transitions complete | C-state/P-state/GV transitions either complete or abort cleanly | Protocol-level guarantee |

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| Max-rate harasser during C6 entry | Saturated fabric during Q-channel | Covered by CBB DVFS TC | No action |
| Harasser during GV transition | SB congestion at freq change | Covered by CBB DVFS TC | No action |
| PEGA C-state + harasser | Aggressive idle + SB stress | Explicit TC (22022423116) | No action |
| Solar random + harasser | Full cross-product stress | Explicit TCs | No action |

---

## Section 7: Security / Safety / Policy

- SB harasser is validation-only; not exposed in production
- Harasser uses same privilege level as PCode

---

## Section 8: References

- [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/soc_pm_has/dmr_soc_pm_has.html) - sideband architecture
- [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) - NWP sideband topology
- [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/has/cbb overview/dmr_cbb_power_management.html) - GPSB/PMSB
