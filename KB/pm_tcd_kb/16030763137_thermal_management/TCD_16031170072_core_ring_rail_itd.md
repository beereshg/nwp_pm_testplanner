# TCD: [ITD] Core/Ring Rail ITD

| Field | Value |
|-------|-------|
| **TCD ID** | [16031170072](https://hsdes.intel.com/appstore/article-one/#/16031170072) |
| **Title** | [ITD] Core/Ring Rail ITD |
| **Status** | draft |
| **Parent TPF** | [16031170066 — ITD Compensation](https://hsdes.intel.com/appstore/article-one/#/16031170066) |
| **Split from** | [22022420603 — ITD](https://hsdes.intel.com/appstore/article-one/#/22022420603) |
| **Feature** | ITD Compensation |
| **Sub-Feature** | Core/Ring Rail (VccCore + VccRing) |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-07-19 |
| **Co-Design T2 ref** | Ingest tracker §3B row S4 |
| **Spec refs** | DMR thermal / ITD: VccCore + VccRing domains |

---

## Section 1: Architecture / Micro-architecture and Functionality

**Core/Ring Rail ITD** validates VccCore and VccRing temperature-dependent voltage compensation. VccCore ITD is **Acode autonomous** — each core's Acode periodically reads its DTS temperature and adjusts voltage via WP recalculation. VccRing ITD is **CBB PCode driven** — PCode computes per-FIVR domain using min/max temperature across CCF FIVR domains.

> **Architecture overview:** See TPF — ITD Compensation §Design Details for full ITD compensation architecture across all domains.

### Key Behavioral Facts

- **VccCore (ACP):** Acode autonomous; periodic temp readout → voltage correction in WP recalculation
- **VccRing (CCF):** CBB PCode; min/max temp of CCF FIVR domains → slope-based compensation
- Both use fuse-programmed `ITD_SLOPE`, `ITD_CUTOFF_TJ` coefficients
- Compensation visible via VID readback and TPMI/PMSB status

---

## Section 2: Functional Requirements / Spec Refs

| FR ID | Requirement | Spec ref |
|---|---|---|
| FR1 | VccCore ITD: Acode applies slope × (temp - cutoff) voltage correction | DMR thermal / ITD: VccCore |
| FR2 | VccRing ITD: PCode computes min/max CCF FIVR temp → slope compensation | DMR thermal / ITD: VccRing |
| FR3 | ITD slope/cutoff per fuse coefficients | DMR thermal / ITD fuse definitions |
| FR4 | Compensation tracks temperature within spec'd tolerance | DMR thermal / ITD spec |

---

## Section 3: Interfaces

| Interface | Direction | Description |
|---|---|---|
| DTS per-core temp | Input | Temperature source for VccCore ITD |
| CCF FIVR domain temps | Input | Temperature sources for VccRing ITD |
| VID / FIVR voltage | Output | Compensated voltage target |
| TPMI / PMSB status | Output | ITD compensation readback |

---

## Section 4: Programming Model

- **Fuses:** `IMH_DOMAIN_ITD_SLOPE`, `ITD_CUTOFF_TJ` per domain
- **Acode WP:** VccCore compensation in workpoint recalculation path
- **PCode CCF:** VccRing compensation in CCF GV slow-loop

---

## Section 5: Pass/Fail Bar

| Bar | Measurable criterion | Spec ref |
|---|---|---|
| VccCore compensation | Temperature injected → VID reflects ITD slope × (T - cutoff) within spec'd tolerance | DMR thermal / ITD |
| VccRing compensation | CCF domain temp change → VccRing VID adjusts per fuse slope | DMR thermal / ITD |
| Fuse coefficient checkout | Fuse values readable → match expected ITD_SLOPE and ITD_CUTOFF_TJ | DMR thermal / ITD fuse |

---

## Section 6: Corner Cases / Coverage

| Scenario | TC ID | Env | Verdict |
|---|---|---|---|
| VccCore ITD at min operating temp | TBD | FV, HSLE | |
| VccCore ITD at max operating temp | TBD | FV, HSLE | |
| VccRing ITD: all CCF FIVRs same temp | TBD | FV, HSLE | |
| VccRing ITD: CCF FIVRs at different temps (min/max spread) | TBD | FV, HSLE | |
| Fuse slope = 0 (ITD effectively disabled for domain) | TBD | FV | |

---

## Section 7: Automation & Dependencies

- Requires temperature injection (DTS override or thermal stimulus)
- Requires VID readback capability for compensation verification
- FW owner: Acode (VccCore), CBB PCode (VccRing)

---

## Section 8: Open Items

- Map existing TCs from parent ITD TCD (22022420603) to this split
- Confirm spec'd tolerance for ITD voltage compensation accuracy
