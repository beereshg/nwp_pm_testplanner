# Deep Analysis: [PSS]Injected Prochot Entry

| Field | Value |
|-------|-------|
| **HSD ID** | 16030715696 |
| **Title** | [PSS]Injected Prochot Entry |
| **Date** | 2026-07-19 |
| **Target Program** | NWP (Newport) |
| **Segment** | PSS |
| **Feature** | Thermal GPIO > Prochot Flow |
| **NWP Disposition** | Runnable_On_N-1 |

## Test Case Intent

Validates the injected PROCHOT assertion → frequency clamp → exit recovery scenario in pre-silicon VP environment, defined in [TCD 22022420609 — Prochot Flow](https://hsdes.intel.com/appstore/article-one/#/22022420609) §5. Environment: NWP PSS VP (Simics).

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

PSS simulation TC for PROCHOT injection path. Validates PCode frequency clamp behavior on external PROCHOT assertion in VP. NWP PROCHOT_N is input-only (output mode removed).

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP VP (Simics) with PROCHOT injection capability
- PCode firmware loaded with PROCHOT response logic

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Inject PROCHOT via Simics model | Assert PROCHOT_N input signal |
| 2 | Verify EXTERNAL_PROCHOT status bit set | Read thermal status register |
| 3 | Verify PCode frequency clamp applied | Check frequency reduced to TCC level |
| 4 | Deassert PROCHOT | Release PROCHOT_N signal |
| 5 | Verify frequency recovery | Frequency returns to pre-PROCHOT level |

## Section C: Pass/Fail Measurement Method

**Bar:** Per TCD 22022420609 §5: PROCHOT assertion → TCC active; deassertion → recovery.
