# TCD: ITD-CONTRACT-004 - Memory/CFC Domain Compensation

| Field | Value |
|-------|-------|
| **TCD ID** | [16031170074](https://hsdes.intel.com/appstore/article-one/#/16031170074) |
| **Title** | ITD-CONTRACT-004 - Memory/CFC Domain Compensation |
| **Status** | open |
| **Parent TPF** | [16031170066 — ITD Compensation](https://hsdes.intel.com/appstore/article-one/#/16031170066) |
| **Feature** | ITD Compensation |
| **Sub-Feature** | Memory/CFC Rail (VccCFCMEM + MLC SSA) |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-07-21 |
| **Spec refs** | DMR CBB HAS ITD: Memory fabric domains, Wave3_common Socket Thermal Mgmt HAS |

---

## Definition Block

- **Layer:** 1 (Contract)
- **Sentence:** Memory/CFC domain ITD (VccCFCMEM + MLC SSA) applies fuse-slope × (temp - cutoff) voltage compensation per domain via IMH Primecode.
- **Gate:** ITD-FUSE-001 (Coefficient Fuse Checkout)
- **Suspect:** IMH Primecode ITD compensation loop for memory/CFC domains
- **Setup:** ITD enabled, fuse checkout passed. Memory controller active with DRAM trained.
- **Check:** Inject temperature change → read VID for VccCFCMEM and MLC SSA; compare against ITD algorithm output.
- **Invariant:** VID delta matches {manifest.itd_slope} × (T - {manifest.itd_cutoff_tj}) within spec'd tolerance per domain.

---

## Section 1: Architecture / Micro-architecture and Functionality

**Memory/CFC Domain Compensation** validates temperature-dependent voltage compensation for VccCFCMEM (memory fabric) and MLC SSA domains. These domains target the memory controller fabric and mid-level cache voltage rails, compensating for temperature-dependent threshold voltage shifts to maintain margin.

> **Architecture overview:** See TPF — ITD Compensation §Design Details.

### Key Behavioral Facts

- FW owner: IMH Primecode
- Fuse-programmed slope/cutoff per domain
- Memory fabric ITD is critical during memory-intensive workloads where thermal stress is highest
- Dual-slope may apply to memory domains — check fuse `*_ITD_SLOPE_2` presence

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
| Core MLC SSA (VCC MLC SSA) ITD verification | [22022421525](https://hsdes.intel.com/appstore/article-one/#/22022421525) | FV, HSLE | |
| VCCCFCMEM ITD verification | [22022421540](https://hsdes.intel.com/appstore/article-one/#/22022421540) | FV, HSLE | |
| VccCFCMEM ITD at min/max temp | within 22022421540 | FV, HSLE | |
| MLC SSA ITD at operating extremes | within 22022421525 | FV, HSLE | |
| Memory-intensive workload thermal stress → ITD compensation | within 22022421540 | FV | |

---

## Section 8: Open Items

- ~~Map existing TCs from parent ITD TCD (22022420603) to this split~~ — **DONE** (2 TCs mapped)
- Confirm MLC SSA domain fuse coefficient expected values
