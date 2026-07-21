# TCD: ITD-FUSE-001 - ITD Coefficient Fuse Configuration Validity

| Field | Value |
|-------|-------|
| **TCD ID** | [16031185219](https://hsdes.intel.com/appstore/article-one/#/16031185219) |
| **Title** | ITD-FUSE-001 - ITD Coefficient Fuse Configuration Validity |
| **Status** | open |
| **Parent TPF** | [16031170066 — ITD Compensation](https://hsdes.intel.com/appstore/article-one/#/16031170066) |
| **Feature** | ITD Compensation |
| **Sub-Feature** | Fuse Coefficient Validation |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-07-21 |
| **Spec refs** | DMR CBB HAS ITD fuse definitions; NWP IMH SoC PM MAS; NWP CCRD spec (new domains) |
| **Split from** | [16031170075](https://hsdes.intel.com/appstore/article-one/#/16031170075) (decomposed) |

---

## Definition Block

- **Layer:** -1 (Fuse)
- **Sentence:** All ITD fuse coefficients across every voltage domain (CBB: ring/core/UCIe; IMH: cfcio/cfcmem/mio/ucie/vinf/cab) are programmed, accessible, and non-zero where mandatory.
- **Gate:** None (Layer -1 — always runs first in ITD enablement ladder)
- **Suspect:** Fuse programming (manufacturing); fuse RAM readback path; per-domain fuse addressing
- **Setup:** NWP silicon platform (ITD fuses programmed by manufacturing). PythonSV access to fuse registers.
- **Check:** For each ITD-capable domain: load fuse RAM, read per-domain slope, slope_2, cutoff_v, cutoff_v_2, cutoff_v_x, ITD_CUTOFF_TJ, MIN_ACCURATE_TEMP, TRUE_TD_ENABLE.
- **Invariant:** No mandatory fuse field is zero (which would indicate unprogrammed or corrupted fuse state). All coefficients consistent with documented domain spec. NWP new domains (VCCCAB, VCCC2CDIG) have valid NWP-specific fuse coefficients.

---

## Section 1: Architecture / Micro-architecture and Functionality

**ITD Coefficient Fuse Configuration Validity** is the foundational gate for all ITD validation. Every downstream ITD compensation test is invalid if fuses are wrong. This TCD verifies that the per-domain ITD fuse coefficients are programmed correctly and accessible via the FW readback path.

> **Architecture overview:** See [TPF 16031170066 — ITD Compensation](https://hsdes.intel.com/appstore/article-one/#/16031170066) §2 Design Details

### NWP Delta

- Two new ITD-capable domains vs DMR: **VCCCAB** and **VCCC2CDIG** — require NWP-specific fuse coefficients
- IMH2 fuse paths differ from DMR IMH1

### Fuse Fields Per Domain

| Fuse Field | Purpose | Mandatory |
|---|---|---|
| ITD_SLOPE | Primary slope coefficient | Yes |
| ITD_SLOPE_2 | Secondary slope (dual-slope algo) | Yes (where applicable) |
| ITD_CUTOFF_V | Voltage cutoff point | Yes |
| ITD_CUTOFF_V_2 | Secondary voltage cutoff | Domain-specific |
| ITD_CUTOFF_V_X | Crossover voltage for slope selection | Domain-specific |
| ITD_CUTOFF_TJ | Temperature cutoff (shared) | Yes |
| MIN_ACCURATE_TEMP | Below this, DTS unreliable → override | Yes |
| TRUE_TD_ENABLE | Master enable per domain | Yes |
| MIN_OVERRIDE_TEMP | Override temp when below MIN_ACCURATE_TEMP | Yes |

---

## Section 2: Functional Requirements / Spec Refs

| FR ID | Requirement | Spec ref |
|---|---|---|
| FR1 | All mandatory fuse fields non-zero for each ITD-capable domain | DMR CBB HAS ITD fuse |
| FR2 | Fuse coefficients readable via FW fuse RAM path | DMR thermal / fuse readback |
| FR3 | NWP new domains (VCCCAB, VCCC2CDIG) have valid fuse coefficients | NWP CCRD spec |
| FR4 | Per-domain TRUE_TD_ENABLE reflects manufacturing intent | DMR fuse spec |
| FR5 | Shared fuses (CUTOFF_TJ, MIN_ACCURATE_TEMP) consistent across domains | DMR thermal / ITD |

---

## Section 3: Test Strategy

| Approach | Detail |
|---|---|
| Fuse RAM readback | Load fuse RAM for each domain, read all coefficient fields |
| Non-zero check | Verify mandatory fields are non-zero |
| Cross-domain consistency | Verify shared fuses (CUTOFF_TJ) match across domains that share them |
| NWP new domain check | Verify VCCCAB and VCCC2CDIG have valid NWP-specific coefficients |

---

## Section 4: Programming Model

ITD fuse coefficients are stored in per-domain fuse blocks:
- **CBB domains:** `cbb.base.fuses.punit_fuses.fw_fuses_itd_*` (core, ring, UCIe)
- **IMH domains:** `imh.fuses.punit.pcode_*_itd_*` (cfcio, cfcmem, mio, ucie, vinf)
- **Shared:** `fw_fuses_itd_cutoff_tj`, `fw_fuses_itd_min_override_temp`

The fuse readback path:
1. FW loads fuse RAM during early boot
2. Coefficients stored in PCode vars (`pcode.vars.ring.vf_curve.at{slice}.itd.*`)
3. IMH Primecode reads via `imh.fuses.punit.pcode_{rc}_itd_{field}`

---

## Section 5: Pass/Fail Bar

| Bar | Measurable criterion | Spec ref |
|---|---|---|
| Non-zero mandatory | All mandatory ITD fuse fields are non-zero for every enabled domain | DMR CBB HAS ITD |
| Readback accessible | All fuse fields readable without error via PythonSV fuse path | DMR thermal |
| NWP new domains valid | VCCCAB and VCCC2CDIG fuse coefficients present and non-zero | NWP CCRD |
| Shared consistency | CUTOFF_TJ and MIN_ACCURATE_TEMP consistent where shared | DMR thermal |

---

## Section 6: Corner Cases / Coverage

| Scenario | TC ID | Env | Verdict |
|---|---|---|---|
| All-domain fuse non-zero check (CBB + IMH) | [22022421521](https://hsdes.intel.com/appstore/article-one/#/22022421521) | FV, HSLE, VP | ✅ |
| NWP new domain VCCCAB fuse validity | within 22022421521 | FV | ⚠️ verify |
| NWP new domain VCCC2CDIG fuse validity | within 22022421521 | FV | ⚠️ verify |
| MIN_ACCURATE_TEMP below-threshold guard behavior | *(TC TBD)* | FV, HSLE | ⚠️ GAP |
| Corrupted/zero fuse detection (negative) | *(TC TBD — VP only)* | VP | ⚠️ GAP |

---

## Section 7: Dependencies

| Dependency | Impact |
|---|---|
| Manufacturing fuse programming | Fuses must be burned correctly — this TCD detects if they weren't |
| Fuse RAM load (early boot) | Must complete before ITD kernel starts |

---

## Section 8: Open Items

| Item | Status | Notes |
|---|---|---|
| NWP VCCCAB/VCCC2CDIG fuse values | confirm | Verify expected non-zero values for NWP-specific domains |
| MIN_ACCURATE_TEMP guard TC | pending | May need dedicated TC or extend 22022421521 |
