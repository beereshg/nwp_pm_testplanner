# TCD: ITD-CONTRACT-003 - Fabric/IO Domain Compensation

| Field | Value |
|-------|-------|
| **TCD ID** | [16031170073](https://hsdes.intel.com/appstore/article-one/#/16031170073) |
| **Title** | ITD-CONTRACT-003 - Fabric/IO Domain Compensation |
| **Status** | open |
| **Parent TPF** | [16031170066 — ITD Compensation](https://hsdes.intel.com/appstore/article-one/#/16031170066) |
| **Feature** | ITD Compensation |
| **Sub-Feature** | Fabric/IO Rail |
| **NWP Disposition** | Runnable_On_N-1 (NWP new domains: VCCCAB, VCCC2CDIG) |
| **KB last updated** | 2026-07-21 |
| **Spec refs** | DMR CBB HAS ITD: Fabric/IO domains, NWP IMH SoC PM MAS (new domains) |

---

## Definition Block

- **Layer:** 1 (Contract)
- **Sentence:** Fabric/IO domain ITD (VccInf, VccCFCIO, VccFIXDIG, VccUCIEA, VccC2IA, VccFCFCAB, VccCAB, VccC2CDIG) applies fuse-slope × (temp - cutoff) voltage compensation per domain via IMH Primecode.
- **Gate:** ITD-FUSE-001 (Coefficient Fuse Checkout)
- **Suspect:** IMH Primecode ITD compensation loop per fabric/IO domain
- **Setup:** ITD enabled, fuse checkout passed. Fabric/IO domains active.
- **Check:** Inject temperature change → read VID for each fabric/IO domain; compare against ITD algorithm output.
- **Invariant:** VID delta matches {manifest.itd_slope} × (T - {manifest.itd_cutoff_tj}) within spec'd tolerance per domain. NWP new domains (VccCAB, VccC2CDIG) compensate correctly with NWP-specific fuse coefficients.

---

## Section 1: Architecture / Micro-architecture and Functionality

**Fabric/IO Domain Compensation** validates temperature-dependent voltage compensation for VccInf, VccCFCIO, VccFIXDIG, VccUCIEA, VccC2IA, and VccFCFCAB/VccCAB domains. These are **Primecode-driven** ITD domains spanning the IO and fabric voltage rails. NWP adds two new ITD-capable domains vs DMR: **VCCCAB** and **VCCC2CDIG**.

> **Architecture overview:** See TPF — ITD Compensation §Design Details.

### NWP Delta

- **New domains:** `VCCCAB` and `VCCC2CDIG` added on NWP — no DMR N-1 baseline, require fresh validation
- FW owner for all fabric/IO domains: IMH Primecode
- UCIe boot-time one-time ITD correction (VccUCIEA) — verify interaction with VccC2IA

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
| VccInf (Inf) ITD verification | [22022421535](https://hsdes.intel.com/appstore/article-one/#/22022421535) | FV, HSLE | |
| VCCC2IA (UCIe) ITD verification | [22022421536](https://hsdes.intel.com/appstore/article-one/#/22022421536) | FV, HSLE | |
| VCCUCIEA ITD verification | [22022421546](https://hsdes.intel.com/appstore/article-one/#/22022421546) | FV, HSLE | |
| VCCCFCIO ITD verification | [22022421538](https://hsdes.intel.com/appstore/article-one/#/22022421538) | FV, HSLE | |
| VCCFIXDIG ITD verification | [22022421542](https://hsdes.intel.com/appstore/article-one/#/22022421542) | FV, HSLE | |
| VCCFCFCAB / VCCCAB (NWP new) ITD verification | [22022458470](https://hsdes.intel.com/appstore/article-one/#/22022458470) | FV | |
| VCCC2CDIG (NWP new) ITD compensation | **GAP — no TC** | FV | ⚠️ |
| VccInf ITD at operating range extremes | within 22022421535 | FV, HSLE | |
| VccUCIEA — UCIe boot-time one-time correction | within 22022421546 | FV, HSLE | |
| VCCCAB at extreme temp (NWP new, no N-1) | within 22022458470 | FV | |

---

## Section 8: Open Items

- ~~Map existing TCs from parent ITD TCD (22022420603) to this split~~ — **DONE** (6 TCs mapped)
- **GAP:** Create TC for VCCC2CDIG (NWP new domain) — no existing TC
- Confirm NWP VCCCAB / VCCC2CDIG fuse coefficient expected values
- Verify UCIe boot-time ITD (VccUCIEA) interaction with VccC2IA
