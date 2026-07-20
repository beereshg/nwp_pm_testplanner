# TCD: [Thermal GPIO] MEMTRIP/THERMTRIP Package Signaling

| Field | Value |
|-------|-------|
| **TCD ID** | [16031170071](https://hsdes.intel.com/appstore/article-one/#/16031170071) |
| **Title** | [Thermal GPIO] MEMTRIP/THERMTRIP Package Signaling |
| **Status** | draft |
| **Parent TPF** | [16031170064 — Thermal GPIO & External Events](https://hsdes.intel.com/appstore/article-one/#/16031170064) |
| **Split from** | [22022420589 — GPIO Interface](https://hsdes.intel.com/appstore/article-one/#/22022420589) |
| **Feature** | Thermal GPIO |
| **Sub-Feature** | MEMTRIP / THERMTRIP Package Signaling |
| **NWP Disposition** | Needs_Adaptation |
| **KB last updated** | 2026-07-19 |
| **Co-Design T2 ref** | Ingest tracker §3A row S3 |
| **Spec refs** | NWP GPIO HAS: MEMTRIP_N / THERMTRIP_N sections |

---

## Section 1: Architecture / Micro-architecture and Functionality

**MEMTRIP/THERMTRIP Package Signaling** validates the catastrophic thermal signal assertion at the GPIO package level: MEMTRIP_N for memory-origin catastrophic temperature and THERMTRIP_N for CPU-origin catastrophic temperature. These signals are the platform-visible endpoints of the catastrophic shutdown chain.

> **Architecture overview:** See TPF — Thermal GPIO & External Events §Design Details and TPF — Thermtrip/Catastrophic Shutdown for full catastrophic chain architecture.

### Key Behavioral Facts

- **MEMTRIP_N (output):** Asserted on catastrophic memory temperature; OR'd with THERMTRIP_N; separate pin distinguishes memory-origin vs CPU-origin trip
- **THERMTRIP_N (bidirectional):** Wire-OR'd across dice; bidirectional so remote dielets sense assertion; must ignore until fuses downloaded + first measurement valid
- Bump fuses gate both signals

---

## Section 2: Functional Requirements / Spec Refs

| FR ID | Requirement | Spec ref |
|---|---|---|
| FR1 | MEMTRIP_N asserted on catastrophic memory temp | NWP GPIO HAS: MEMTRIP_N |
| FR2 | THERMTRIP_N wire-OR across dice; bidirectional | NWP GPIO HAS: THERMTRIP_N |
| FR3 | THERMTRIP_N ignore until fuses downloaded + first valid measurement | NWP GPIO HAS: THERMTRIP_N |
| FR4 | Bump fuse gating per signal | NWP GPIO HAS: GPIO_BUMP_ENABLES |

---

## Section 3: Interfaces

| Interface | Direction | Description |
|---|---|---|
| MEMTRIP_N pin | Output | Memory-origin catastrophic trip indication |
| THERMTRIP_N pin | Bidirectional | CPU-origin trip; wire-OR cross-die sensing |

---

## Section 4: Programming Model

- **THERMTRIP guard:** Assertion ignored before fuse download + first valid measurement
- **Bump fuses:** Per-signal enable/disable
- **Distinction:** MEMTRIP vs THERMTRIP origin identification for platform debug

---

## Section 5: Pass/Fail Bar

| Bar | Measurable criterion | Spec ref |
|---|---|---|
| MEMTRIP assertion | Catastrophic memory temp → MEMTRIP_N asserted | NWP GPIO HAS |
| THERMTRIP wire-OR | THERMTRIP_N asserted on one die → sensed by all dice | NWP GPIO HAS |
| THERMTRIP guard | Before fuse download: THERMTRIP_N assertion ignored; after: trip active | NWP GPIO HAS |
| Fuse gating | Bump fuse disabled → no trip signal | NWP GPIO HAS |

---

## Section 6: Corner Cases / Coverage

| Scenario | TC ID | Env | Verdict |
|---|---|---|---|
| MEMTRIP assertion on catastrophic memory temp | TBD | FV, HSLE | |
| THERMTRIP wire-OR cross-die propagation | TBD | XOS, FV | |
| THERMTRIP guard: before fuse download | TBD | FV, HSLE | |
| THERMTRIP guard: after first valid measurement | TBD | FV, HSLE | |
| Both MEMTRIP + THERMTRIP active | TBD | FV | |
| Fuse-disabled MEMTRIP/THERMTRIP | TBD | FV, HSLE | |

---

## Section 7: Automation & Dependencies

- Cross-die THERMTRIP requires XOS or multi-die silicon
- Related: Thermtrip TCD (22022420625) covers firmware catastrophic shutdown chain
- Related: Memtrip TCD (22022420575) covers MC-side catastrophic behavior

---

## Section 8: Open Items

- Determine which TCs from parent GPIO TCD (22022420589) map to this split
- Verify NWP THERMTRIP_N guard timing (fuse download + first measurement window)
