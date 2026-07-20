# TCD: [Thermal GPIO] PROCHOT_N Interface

| Field | Value |
|-------|-------|
| **TCD ID** | [16031170069](https://hsdes.intel.com/appstore/article-one/#/16031170069) |
| **Title** | [Thermal GPIO] PROCHOT_N Interface |
| **Status** | draft |
| **Parent TPF** | [16031170064 — Thermal GPIO & External Events](https://hsdes.intel.com/appstore/article-one/#/16031170064) |
| **Split from** | [22022420589 — GPIO Interface](https://hsdes.intel.com/appstore/article-one/#/22022420589) |
| **Feature** | Thermal GPIO |
| **Sub-Feature** | PROCHOT_N |
| **NWP Disposition** | Needs_Adaptation (NWP removes PROCHOT output mode) |
| **KB last updated** | 2026-07-19 |
| **Co-Design T2 ref** | Ingest tracker §3A row S1 |
| **Spec refs** | NWP GPIO HAS: PROCHOT_N section |

---

## Section 1: Architecture / Micro-architecture and Functionality

**PROCHOT_N Interface** validates the PROCHOT_N input pin electrical assertion, the firmware response (External_PROCHOT set, TCC activation, frequency clamp), and the deassertion recovery path. On NWP, PROCHOT_N is **input-only** — the output mode available on prior platforms has been removed.

> **Architecture overview:** See TPF — Thermal GPIO & External Events §Design Details for full-stack GPIO thermal signal architecture.

### Key Behavioral Facts

- PROCHOT_N assertion sets `EXTERNAL_PROCHOT` status bit
- TCC (Thermal Control Circuit) becomes active on assertion — PCode clamps frequency
- TCC remains active until PROCHOT_N is deasserted
- Bump fuse `PTPCFSMS_GPIO_BUMP_ENABLES_ENABLE_XXPROCHOT_N_FUSE` gates the signal

### NWP Delta

- **Output mode removed:** NWP PROCHOT_N is input-only; DMR tests using PROCHOT output assertion must be adapted
- PROCHOT response latency requirements apply per NWP GPIO HAS

---

## Section 2: Functional Requirements / Spec Refs

| FR ID | Requirement | Spec ref |
|---|---|---|
| FR1 | PROCHOT_N assertion → EXTERNAL_PROCHOT set | NWP GPIO HAS: PROCHOT_N |
| FR2 | TCC active during assertion; freq clamp applied | NWP GPIO HAS + DMR thermal flows |
| FR3 | Deassertion → TCC inactive; frequency recovery | NWP GPIO HAS: PROCHOT_N |
| FR4 | Bump fuse enable/disable respected | NWP GPIO HAS: GPIO_BUMP_ENABLES |

---

## Section 3: Interfaces

| Interface | Direction | Description |
|---|---|---|
| PROCHOT_N pin | Input | Platform/BMC/VR asserts to request throttle |
| EXTERNAL_PROCHOT status | Internal | Set by HW on assertion; read via TPMI/MSR |
| PCode frequency clamp | Internal | PCode reduces frequency on EXTERNAL_PROCHOT |

---

## Section 4: Programming Model

- **Register:** PROCHOT status readable via thermal status TPMI/MSR
- **Fuse:** `PTPCFSMS_GPIO_BUMP_ENABLES_ENABLE_XXPROCHOT_N_FUSE`
- **PCode response:** Frequency clamp to TCC activation level

---

## Section 5: Pass/Fail Bar

| Bar | Measurable criterion | Spec ref |
|---|---|---|
| Assertion response | PROCHOT_N asserted → EXTERNAL_PROCHOT=1 AND TCC active within spec'd latency | NWP GPIO HAS |
| Recovery | PROCHOT_N deasserted → EXTERNAL_PROCHOT=0 AND frequency restored within spec'd recovery window | NWP GPIO HAS |
| Fuse gating | Bump fuse disabled → PROCHOT_N assertion produces no EXTERNAL_PROCHOT, no TCC activation | NWP GPIO HAS |

---

## Section 6: Corner Cases / Coverage

| Scenario | TC ID | Env | Verdict |
|---|---|---|---|
| PROCHOT_N assertion → TCC active | TBD | FV, HSLE | |
| PROCHOT_N deassertion → recovery | TBD | FV, HSLE | |
| PROCHOT_N with bump fuse disabled | TBD | FV, HSLE | |
| PROCHOT_N during active RAPL PL1 throttle | TBD | FV | |
| PROCHOT_N assertion + VR_HOT simultaneous | TBD | FV | |

---

## Section 7: Automation & Dependencies

- Depends on GPIO injection capability (PythonSV or HSLE pin injection)
- Related: Prochot Flow TCD (22022420609) covers the full firmware response flow

---

## Section 8: Open Items

- Confirm spec'd assertion-to-TCC latency value for NWP
- Confirm spec'd recovery window value for NWP
- Determine which TCs from parent GPIO TCD (22022420589) map to this split
