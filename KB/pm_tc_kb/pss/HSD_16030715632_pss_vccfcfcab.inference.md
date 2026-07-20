# Deep Analysis: [PSS]VCCFCFCAB

| Field | Value |
|-------|-------|
| **HSD ID** | 16030715632 |
| **Title** | [PSS]VCCFCFCAB |
| **Date** | 2026-07-19 |
| **Target Program** | NWP (Newport) |
| **Source Program** | NWP-native |
| **Segment** | PSS |
| **Feature** | SoC Thermal Management > ITD |
| **Sub-Feature** | VCCFCFCAB (CAB) — NWP-native new domain |
| **NWP Disposition** | **Runnable_On_N-1** |

---


## Test Case Intent

Validates the VCCFCFCAB ITD compensation in pre-silicon VP scenario defined in [TCD 16031170073 — Fabric/IO Rail ITD](https://hsdes.intel.com/appstore/article-one/#/16031170073) §5. Environment: NWP PSS VP (Simics).

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

PSS simulation TC for VCCFCFCAB ITD compensation on NWP. VCCFCFCAB is a NWP-native new domain (Customer Accelerator Block FIVR). This TC validates the ITD slope/cutoff behavior for this new domain in the pre-silicon VP environment.

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP VP (Simics) with VCCFCFCAB domain modeled
- PCode/Primecode firmware loaded with ITD support for VCCFCFCAB
- PythonSv access for register readback

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Launch NWP VP with ITD enabled | Simics boot with VCCFCFCAB domain active |
| 2 | Inject temperature change via Simics model knob | Use DTS override for CAB thermal diode |
| 3 | Read VCCFCFCAB ITD compensation registers | Verify slope x (temp - cutoff) applied |
| 4 | Compare against fuse coefficients | pcode_cfc_itd_slope/cutoff for VCCFCFCAB |

---

## Section C: Pass/Fail Measurement Method

**Bar:** Per TCD [16031170073 — Fabric/IO Rail ITD] §5: ITD fuse coefficients applied per domain; NWP new domains (VCCCAB, VCCC2CDIG) compensated correctly.

**Measurement:** VCCFCFCAB RC voltage offset matches expected value from fuse slope/cutoff calculation.
