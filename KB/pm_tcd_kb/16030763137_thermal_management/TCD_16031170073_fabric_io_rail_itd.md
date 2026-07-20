# TCD: [ITD] Fabric/IO Rail ITD

| Field | Value |
|-------|-------|
| **TCD ID** | [16031170073](https://hsdes.intel.com/appstore/article-one/#/16031170073) |
| **Title** | [ITD] Fabric/IO Rail ITD |
| **Status** | draft |
| **Parent TPF** | [16031170066 — ITD Compensation](https://hsdes.intel.com/appstore/article-one/#/16031170066) |
| **Split from** | [22022420603 — ITD](https://hsdes.intel.com/appstore/article-one/#/22022420603) |
| **Feature** | ITD Compensation |
| **Sub-Feature** | Fabric/IO Rail |
| **NWP Disposition** | Runnable_On_N-1 (NWP new domains: VCCCAB, VCCC2CDIG) |
| **KB last updated** | 2026-07-19 |
| **Co-Design T2 ref** | Ingest tracker §3B row S5 |
| **Spec refs** | DMR thermal / ITD: Fabric/IO domains + NWP CCRD spec (new domains) |

---

## Section 1: Architecture / Micro-architecture and Functionality

**Fabric/IO Rail ITD** validates temperature-dependent voltage compensation for VccInf, VccCFCIO, VccFIXDIG, VccUCIEA, VccC2IA, and VccFCFCAB/VccCAB domains. These are **Primecode-driven** ITD domains spanning the IO and fabric voltage rails. NWP adds two new ITD-capable domains vs DMR: **VCCCAB** and **VCCC2CDIG**.

> **Architecture overview:** See TPF — ITD Compensation §Design Details.

### NWP Delta

- **New domains:** `VCCCAB` and `VCCC2CDIG` added on NWP — no DMR N-1 baseline, require fresh validation
- FW owner for all fabric/IO domains: IMH Primecode

---

## Section 2: Functional Requirements / Spec Refs

| FR ID | Requirement | Spec ref |
|---|---|---|
| FR1 | Fabric/IO domain ITD: fuse slope × (temp - cutoff) compensation | DMR thermal / ITD: Fabric/IO |
| FR2 | NWP new domains (VCCCAB, VCCC2CDIG) compensated correctly | NWP CCRD spec |
| FR3 | ITD fuse coefficients per domain | DMR thermal / ITD fuse |

---

## Section 5: Pass/Fail Bar

| Bar | Measurable criterion | Spec ref |
|---|---|---|
| Per-domain compensation | Temperature injected → VID reflects fuse slope within tolerance per domain | DMR thermal / ITD |
| NWP new domain | VCCCAB / VCCC2CDIG voltage adjusts with temperature per NWP fuse coefficients | NWP CCRD spec |
| Fuse checkout | All fabric/IO domain fuse coefficients readable and match expected values | DMR + NWP fuse specs |

---

## Section 6: Corner Cases / Coverage

| Scenario | TC ID | Env | Verdict |
|---|---|---|---|
| VccInf ITD at operating range extremes | TBD | FV, HSLE | |
| VccCFCIO ITD compensation | TBD | FV, HSLE | |
| VccFIXDIG ITD compensation | TBD | FV, HSLE | |
| VccUCIEA ITD — UCIe boot-time one-time correction | TBD | FV, HSLE | |
| VccC2IA ITD compensation | TBD | FV, HSLE | |
| VCCCAB (NWP new) ITD at extreme temp | TBD | FV | |
| VCCC2CDIG (NWP new) ITD compensation | TBD | FV | |

---

## Section 8: Open Items

- Map existing TCs from parent ITD TCD (22022420603) to this split
- Confirm NWP VCCCAB / VCCC2CDIG fuse coefficient expected values
- Verify UCIe boot-time ITD (VccUCIEA) interaction with VccC2IA
