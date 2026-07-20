# TCD: [ITD] Memory/CFC Rail ITD

| Field | Value |
|-------|-------|
| **TCD ID** | [16031170074](https://hsdes.intel.com/appstore/article-one/#/16031170074) |
| **Title** | [ITD] Memory/CFC Rail ITD |
| **Status** | draft |
| **Parent TPF** | [16031170066 — ITD Compensation](https://hsdes.intel.com/appstore/article-one/#/16031170066) |
| **Split from** | [22022420603 — ITD](https://hsdes.intel.com/appstore/article-one/#/22022420603) |
| **Feature** | ITD Compensation |
| **Sub-Feature** | Memory/CFC Rail (VccCFCMEM + MLC SSA) |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-07-19 |
| **Co-Design T2 ref** | Ingest tracker §3B row S6 |
| **Spec refs** | DMR thermal / ITD: Memory fabric domains |

---

## Section 1: Architecture / Micro-architecture and Functionality

**Memory/CFC Rail ITD** validates temperature-dependent voltage compensation for VccCFCMEM (memory fabric) and MLC SSA domains. These domains target the memory controller fabric and mid-level cache voltage rails, compensating for temperature-dependent threshold voltage shifts to maintain margin.

> **Architecture overview:** See TPF — ITD Compensation §Design Details.

### Key Behavioral Facts

- FW owner: IMH Primecode
- Fuse-programmed slope/cutoff per domain
- Memory fabric ITD is critical during memory-intensive workloads where thermal stress is highest

---

## Section 2: Functional Requirements / Spec Refs

| FR ID | Requirement | Spec ref |
|---|---|---|
| FR1 | VccCFCMEM ITD: fuse slope × (temp - cutoff) compensation | DMR thermal / ITD: Memory fabric |
| FR2 | MLC SSA ITD compensation functional | DMR thermal / ITD |
| FR3 | Fuse coefficients per domain | DMR thermal / ITD fuse |

---

## Section 5: Pass/Fail Bar

| Bar | Measurable criterion | Spec ref |
|---|---|---|
| VccCFCMEM compensation | Temperature change → VID adjusts per fuse slope within spec'd tolerance | DMR thermal / ITD |
| MLC SSA compensation | MLC SSA domain voltage tracks temperature per fuse coefficients | DMR thermal / ITD |

---

## Section 6: Corner Cases / Coverage

| Scenario | TC ID | Env | Verdict |
|---|---|---|---|
| VccCFCMEM ITD at min/max temp | TBD | FV, HSLE | |
| MLC SSA ITD at operating extremes | TBD | FV, HSLE | |
| Memory-intensive workload thermal stress → ITD compensation | TBD | FV | |

---

## Section 8: Open Items

- Map existing TCs from parent ITD TCD (22022420603) to this split
- Confirm MLC SSA domain fuse coefficient expected values
