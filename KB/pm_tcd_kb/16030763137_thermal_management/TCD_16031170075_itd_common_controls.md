# TCD: ~~ITD-FUSE-001 - ITD Coefficient Fuse Checkout~~ [DECOMPOSED]

> **⚠️ DECOMPOSED (2026-07-21):** This TCD has been split into 3 focused TCDs:
> - [16031185219](https://hsdes.intel.com/appstore/article-one/#/16031185219) — ITD-FUSE-001 - ITD Coefficient Fuse Configuration Validity (TC 22022421521)
> - [16031185220](https://hsdes.intel.com/appstore/article-one/#/16031185220) — ITD-CONTRACT-001b - ITD Disable/Re-Enable Control (TC 22022421528)
> - [16031185180](https://hsdes.intel.com/appstore/article-one/#/16031185180) — ITD-SCENARIO-003 - Pre-Training VCCUCIEA ITD Sequencing (TC 22022421534)
>
> All TCs have been re-homed. This TCD should be closed in HSD.

| Field | Value |
|-------|-------|
| **TCD ID** | [16031170075](https://hsdes.intel.com/appstore/article-one/#/16031170075) |
| **Title** | ~~ITD-FUSE-001 - ITD Coefficient Fuse Checkout~~ |
| **Status** | **DECOMPOSED** — close in HSD |
| **Parent TPF** | [16031170066 — ITD Compensation](https://hsdes.intel.com/appstore/article-one/#/16031170066) |
| **Feature** | ITD Compensation |
| **Sub-Feature** | Fuse Coefficient Checkout |
| **NWP Disposition** | Superseded |
| **KB last updated** | 2026-07-21 |
| **Spec refs** | DMR CBB HAS ITD fuse definitions, NWP IMH SoC PM MAS |

---

## Definition Block

- **Layer:** -1 (Fuse)
- **Sentence:** All ITD fuse coefficients (`*_ITD_SLOPE`, `*_ITD_SLOPE_2`, `*_ITD_CUTOFF_V`, `*_ITD_CUTOFF_V_2`, `ITD_CUTOFF_TJ`, `*_ITD_TEMP_OFFSET`, `MIN_ACCURATE_TEMP`, `TRUE_TD_ENABLE`) are readable and match platform-expected values per domain.
- **Gate:** None (FUSE layer — always first)
- **Suspect:** Fuse programming / shadow register load
- **Setup:** Platform booted; fuse shadow registers accessible.
- **Check:** Read all ITD fuse fields across all voltage domains; compare against expected platform coefficients.
- **Invariant:** Every ITD fuse field readable; value matches {manifest.itd_fuse_expected} per domain. No fuse reads as all-zero or all-one unless spec'd default.

---

## Section 1: Architecture / Micro-architecture and Functionality

**ITD Coefficient Fuse Checkout** validates that all ITD fuse coefficients are correctly programmed and accessible across all voltage domains. This is the foundational gate for all ITD validation — if fuses are wrong, all downstream compensation checks are invalid.

> **Architecture overview:** See TPF — ITD Compensation §Design Details.

### Fuse Fields Per Domain

| Fuse | Controls |
|---|---|
| `*_ITD_SLOPE` | Slope for voltage vs temperature (main/low voltage range) |
| `*_ITD_SLOPE_2` | Slope for high voltage range (dual-slope domains) |
| `*_ITD_CUTOFF_V` | Cutoff voltage below which SLOPE applies |
| `*_ITD_CUTOFF_V_2` | Cutoff voltage for second slope (dual-slope) |
| `*_ITD_CUTOFF_V_X` | Crossover/inflection voltage between SLOPE and SLOPE_2 |
| `*_ITD_TEMP_OFFSET` | Offset to min DTS temperature for cold spot compensation |
| `ITD_CUTOFF_TJ` | Reference temperature — above this, ITD not applied (True TD region) |
| `MIN_ACCURATE_TEMP` | Min reliable DTS temperature; below → use `ITD_MIN_OVERRIDE_TEMP` |
| `TRUE_TD_ENABLE` | Enables True TD (inverse ITD) for core/mesh above cutoff voltage |

### ITD-Capable Domains on NWP

VccCore (ACP), VccRing (CCF), VccInf, VccCFCIO, VccFIXDIG, VccUCIEA, VccC2IA (UCIe), VccCFCMEM, MLC SSA, VccFCFCAB/VccCAB, **VccC2CDIG** (NWP new)

---

## Section 2: Functional Requirements / Spec Refs

| FR ID | Requirement | Spec ref |
|---|---|---|
| FR1 | All per-domain ITD fuse coefficients readable | DMR CBB HAS ITD fuse |
| FR2 | Fuse values match platform-expected coefficients per domain | DMR CBB HAS ITD fuse |
| FR3 | `ITD_CUTOFF_TJ` global reference temperature readable and correct | DMR CBB HAS ITD |
| FR4 | `MIN_ACCURATE_TEMP` readable and correct | DMR CBB HAS ITD |
| FR5 | `TRUE_TD_ENABLE` readable and correct per domain | DMR CBB HAS ITD |
| FR6 | NWP new domain fuses (VccCAB, VccC2CDIG) present and correct | NWP IMH SoC PM MAS |

---

## Section 5: Pass/Fail Bar

| Bar | Measurable criterion | Spec ref |
|---|---|---|
| Fuse readability | All ITD fuse fields readable across all domains; no access faults | DMR CBB HAS ITD fuse |
| Fuse correctness | Every fuse value matches {manifest.itd_fuse_expected} per domain | DMR CBB HAS ITD fuse |
| Dual-slope fuses | Domains with dual-slope: `*_ITD_SLOPE_2`, `*_ITD_CUTOFF_V_2`, `*_ITD_CUTOFF_V_X` present and non-zero | DMR CBB HAS ITD |
| NWP new domains | VccCAB and VccC2CDIG fuse fields present and match expected | NWP IMH SoC PM MAS |

---

## Section 6: Corner Cases / Coverage

| Scenario | TC ID | Env | Verdict |
|---|---|---|---|
| Fuse coefficient checkout (all domains) | [22022421521](https://hsdes.intel.com/appstore/article-one/#/22022421521) | FV, HSLE, VP | |
| Per-domain slope/cutoff fuse verification | within 22022421521 | FV, HSLE | |
| Dual-slope fuse fields present for applicable domains | within 22022421521 | FV, HSLE | |
| NWP new domain fuses (VccCAB, VccC2CDIG) | within 22022421521 | FV | |
| MIN_ACCURATE_TEMP fuse value check | within 22022421521 | FV, HSLE | |
| TRUE_TD_ENABLE per-domain check | within 22022421521 | FV, HSLE | |

---

## Section 8: Open Items

- Confirm NWP VccCAB / VccC2CDIG expected fuse coefficient values
- Verify ITD_CUTOFF_TJ expected value for NWP (may differ from DMR)
- **Verify:** Does TC 22022421528 cover re-enable after disable? If not, split scenario
- **Verify:** Does TC 22022421521 explicitly test MIN_ACCURATE_TEMP boundary? If not, add scenario
