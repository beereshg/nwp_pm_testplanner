# TCD: [Thermal GPIO] MEMHOT IN/OUT Interface

| Field | Value |
|-------|-------|
| **TCD ID** | [16031170070](https://hsdes.intel.com/appstore/article-one/#/16031170070) |
| **Title** | [Thermal GPIO] MEMHOT IN/OUT Interface |
| **Status** | draft |
| **Parent TPF** | [16031170064 — Thermal GPIO & External Events](https://hsdes.intel.com/appstore/article-one/#/16031170064) |
| **Split from** | [22022420589 — GPIO Interface](https://hsdes.intel.com/appstore/article-one/#/22022420589) |
| **Feature** | Thermal GPIO |
| **Sub-Feature** | MEMHOT IN/OUT |
| **NWP Disposition** | Needs_Adaptation |
| **KB last updated** | 2026-07-19 |
| **Co-Design T2 ref** | Ingest tracker §3A row S2 |
| **Spec refs** | NWP GPIO HAS: MEMHOT_IN_N / MEMHOT_OUT_N sections |

---

## Section 1: Architecture / Micro-architecture and Functionality

**MEMHOT IN/OUT Interface** validates the bidirectional MEMHOT thermal signal behavior: MEMHOT_IN (external platform request for memory throttle) and MEMHOT_OUT (CPU-driven indication that memory is hot). These are distinct signals with different semantics — MEMHOT_IN is a platform-to-CPU throttle request with a 100 us response requirement; MEMHOT_OUT is a CPU-to-platform notification based on DIMM temperature threshold crossing.

> **Architecture overview:** See TPF — Thermal GPIO & External Events §Design Details for full-stack GPIO thermal signal architecture.

### Key Behavioral Facts

- **MEMHOT_IN_N (input):** Platform requests memory throttle; memory power must reduce within **100 us**; overlaid on XTAL_MODE0 strap until GLOBAL_RESET_N
- **MEMHOT_OUT_N (output):** Driven when PCode writes hottest DIMM to `MH_TEMP_STAT` and MC compares vs `DIMM_TEMP_EV_OFST`
- Bump fuses gate both signals independently

---

## Section 2: Functional Requirements / Spec Refs

| FR ID | Requirement | Spec ref |
|---|---|---|
| FR1 | MEMHOT_IN_N assertion → MC memory throttle within 100 us | NWP GPIO HAS: MEMHOT_IN_N |
| FR2 | MEMHOT_OUT_N driven on MH_TEMP_STAT vs DIMM_TEMP_EV_OFST crossing | NWP GPIO HAS: MEMHOT_OUT_N |
| FR3 | Bump fuse enable/disable per signal | NWP GPIO HAS: GPIO_BUMP_ENABLES |
| FR4 | MEMHOT_IN overlaid on XTAL_MODE0 until GLOBAL_RESET_N | NWP GPIO HAS: MEMHOT_IN_N |

---

## Section 3: Interfaces

| Interface | Direction | Description |
|---|---|---|
| MEMHOT_IN_N pin | Input | Platform requests memory power reduction |
| MEMHOT_OUT_N pin | Output | CPU indicates hottest DIMM exceeded threshold |
| MH_TEMP_STAT register | Internal | PCode writes hottest DIMM temp |
| DIMM_TEMP_EV_OFST register | Internal | MC threshold for MEMHOT_OUT assertion |

---

## Section 4: Programming Model

- **MH_TEMP_STAT:** PCode populates with hottest DIMM temperature
- **DIMM_TEMP_EV_OFST:** MC register defining MEMHOT_OUT assertion threshold
- **Bump fuses:** Per-signal enable/disable

---

## Section 5: Pass/Fail Bar

| Bar | Measurable criterion | Spec ref |
|---|---|---|
| MEMHOT_IN throttle latency | MEMHOT_IN_N asserted → MC reduces memory power within 100 us | NWP GPIO HAS |
| MEMHOT_OUT threshold | MH_TEMP_STAT crosses DIMM_TEMP_EV_OFST → MEMHOT_OUT_N driven | NWP GPIO HAS |
| Fuse gating | Bump fuse disabled → signal assertion/driving blocked | NWP GPIO HAS |

---

## Section 6: Corner Cases / Coverage

| Scenario | TC ID | Env | Verdict |
|---|---|---|---|
| MEMHOT_IN → MC throttle within 100 us | TBD | FV, HSLE | |
| MEMHOT_OUT on threshold crossing | TBD | FV, HSLE | |
| MEMHOT_IN during active CLTT throttle | TBD | FV | |
| Both MEMHOT_IN + MEMHOT_OUT active simultaneously | TBD | FV | |
| MEMHOT_IN/OUT with bump fuse disabled | TBD | FV, HSLE | |
| MEMHOT_IN during GLOBAL_RESET_N (strap overlap) | TBD | FV | |

---

## Section 7: Automation & Dependencies

- Depends on GPIO injection capability and MC throttle observability
- Related: Memhot TCD (22022420570) in Memory Thermal TPF covers MC-side throttle policy

---

## Section 8: Open Items

- Determine which TCs from parent GPIO TCD (22022420589) map to this split
- Clarify MEMHOT_IN/OUT interaction with CLTT MR4-based throttle
