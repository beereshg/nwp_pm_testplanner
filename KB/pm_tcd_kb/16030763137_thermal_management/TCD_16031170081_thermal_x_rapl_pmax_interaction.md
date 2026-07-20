# TCD: [Core/CBB Thermal] Thermal x RAPL/PMAX Interaction

| Field | Value |
|-------|-------|
| **TCD ID** | [16031170081](https://hsdes.intel.com/appstore/article-one/#/16031170081) |
| **Title** | [Core/CBB Thermal] Thermal x RAPL/PMAX Interaction |
| **Status** | draft |
| **Parent TPF** | [16031170062 — Core/CBB Thermal Control](https://hsdes.intel.com/appstore/article-one/#/16031170062) |
| **Feature** | Thermal Cross-Product |
| **Sub-Feature** | Thermal x RAPL/FastRAPL/PMAX limiter arbitration |
| **NWP Disposition** | New |
| **KB last updated** | 2026-07-19 |
| **Co-Design ref** | Ingest tracker N2; Co-Design thermal x RAPL query 2026-07-19 |
| **Spec refs** | DMR thermal flows: limiter arbitration; DMR feature index: RAPL/FastRAPL/PMAX adjacent features |

---

## Section 1: Architecture / Micro-architecture and Functionality

**Thermal x RAPL/PMAX Interaction** validates the PCode arbitration behavior when thermal throttling (EMTTM/PROCHOT) and power limiting (RAPL PL1/PL2, PMAX) are active simultaneously. The system must enforce the most restrictive limiter without oscillation.

> **Architecture overview:** See TPF — Core/CBB Thermal Control §Design Details.

### Key Behavioral Facts (from Co-Design spec query)

- **Most restrictive wins:** When both thermal and RAPL/PMAX limits are active, the lower frequency/power bound always prevails. No override — both are considered, lowest wins.
- **Dynamic arbitration:** PCode evaluates all active limiters (thermal, RAPL, PMAX) and applies the lowest allowable frequency/power. No fixed priority — most restrictive is always enforced.
- **Status bits per limiter:**
  - Thermal: EMTTM/PROCHOT status bits
  - RAPL: RAPL PL1/PL2 active status bits
  - PMAX: PMAX Health Indicator Status register (PMT telemetry)
- **No oscillation by design:** PCode PID loop is designed to prevent thermal↔RAPL oscillation. Thermal backs off gradually (PID), RAPL adjusts power budget — no rapid flip-flopping expected.

---

## Section 2: Functional Requirements / Spec Refs

| FR ID | Requirement | Spec ref |
|---|---|---|
| FR1 | Thermal + RAPL both active → lower frequency bound wins | DMR thermal flows: limiter arbitration |
| FR2 | Status bits correctly indicate active limiter (thermal vs RAPL vs PMAX) | DMR thermal status + RAPL status registers |
| FR3 | No oscillation between thermal and RAPL limiters | PCode PID design |
| FR4 | PMAX Health Indicator reflects PMAX limiting when active | PMT telemetry spec |

---

## Section 5: Pass/Fail Bar

| Bar | Measurable criterion | Spec ref |
|---|---|---|
| Lower bound wins | Thermal throttle to F_thermal + RAPL PL1 to F_rapl → observed freq = min(F_thermal, F_rapl) | DMR thermal flows |
| Status bits accurate | When thermal is the active limiter: EMTTM status = 1 AND RAPL status = 0 (or vice versa) | DMR thermal + RAPL status regs |
| No oscillation | Frequency stable (no >2 transitions/sec between thermal and RAPL limiting) over 10s observation window | PCode PID design |
| PMAX interaction | Thermal + PMAX both active → PMAX Health Indicator = limiting; freq = min(F_thermal, F_pmax) | PMT telemetry |

---

## Section 6: Corner Cases / Coverage

| Scenario | TC ID | Env | Verdict |
|---|---|---|---|
| EMTTM active + RAPL PL1 active → lower bound | TBD | FV, VP | |
| PROCHOT active + RAPL PL1 active → lower bound | TBD | FV | |
| Thermal + PMAX active simultaneously | TBD | FV | |
| Thermal limiter releases → RAPL becomes sole limiter | TBD | FV, VP | |
| RAPL releases → thermal becomes sole limiter | TBD | FV, VP | |
| All three (thermal + RAPL + PMAX) active | TBD | FV | |
| Status bit accuracy under limiter transitions | TBD | FV, VP | |

---

## Section 8: Open Items

- Confirm exact TPMI register names for thermal/RAPL/PMAX status bits on NWP
- Determine if FastRAPL adds distinct cross-product behavior vs standard RAPL PL1
- Confirm oscillation detection criteria (frequency stability threshold)
