# Deep Analysis: [PSS]iMH North VR Hot Detection

| Field | Value |
|-------|-------|
| **HSD ID** | 16030715740 |
| **Title** | [PSS]iMH North VR Hot Detection |
| **Date** | 2026-07-19 |
| **Target Program** | NWP (Newport) |
| **Segment** | PSS |
| **Feature** | Thermal GPIO > VR Hot |
| **NWP Disposition** | Runnable_On_N-1 |

## Test Case Intent

Validates iMH VR Hot detection path — CBB and IMH go to P1, PLR HOT_VR set on all dies — in pre-silicon VP, defined in [TCD 22022420628 — VR Hot](https://hsdes.intel.com/appstore/article-one/#/22022420628) §5. Environment: NWP PSS VP (Simics).

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

PSS simulation TC for iMH North VR Hot detection. Validates that when VR Hot is detected on iMH north, both CBB and IMH fabric frequencies go to P1 and PLR HOT_VR status bit is set on all dies.

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP VP (Simics) with VR Hot injection on iMH
- PCode/Primecode firmware loaded
- Cross-die HPM messaging functional (XOS preferred)

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Inject VR Hot on iMH north VR | Use Simics VR thermal injection |
| 2 | Verify CBB fabric goes to P1 | Read CBB frequency — expect P1 |
| 3 | Verify IMH fabric goes to P1 | Read IMH frequency — expect P1 |
| 4 | Verify PLR HOT_VR set on all dies | Read PLR on CBB0, CBB1, IMH |
| 5 | Deassert VR Hot | Clear VR thermal injection |
| 6 | Verify frequency recovery | CBB/IMH resume normal frequency |

## Section C: Pass/Fail Measurement Method

**Bar:** Per TCD 22022420628 §5: VR Hot → CBB+IMH at P1; PLR HOT_VR set on all dies; recovery on VR temp drop.
