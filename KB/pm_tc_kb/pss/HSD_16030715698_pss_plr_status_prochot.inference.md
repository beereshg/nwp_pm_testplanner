# Deep Analysis: [PSS]PLR Status registers Check for Prochot Events

| Field | Value |
|-------|-------|
| **HSD ID** | 16030715698 |
| **Title** | [PSS]PLR Status registers Check for Prochot Events |
| **Date** | 2026-07-19 |
| **Target Program** | NWP (Newport) |
| **Segment** | PSS |
| **Feature** | Thermal GPIO > Prochot Flow |
| **NWP Disposition** | Runnable_On_N-1 |

## Test Case Intent

Validates PLR status bit set/unset for PROCHOT events in pre-silicon VP, defined in [TCD 22022420609 — Prochot Flow](https://hsdes.intel.com/appstore/article-one/#/22022420609) §5. Environment: NWP PSS VP (Simics).

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

PSS TC for PLR (Power Limit Reason) status register validation during PROCHOT events. Validates that PLR correctly reflects PROCHOT as the active power limiting reason.

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP VP (Simics) with PROCHOT injection and PLR register access
- PCode firmware loaded

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Read PLR status registers before PROCHOT injection | Baseline PLR state |
| 2 | Inject PROCHOT assertion | Assert PROCHOT_N input |
| 3 | Read PLR status registers | Verify PROCHOT bit set in PLR |
| 4 | Deassert PROCHOT | Release PROCHOT_N |
| 5 | Read PLR status registers | Verify PROCHOT bit cleared |

## Section C: Pass/Fail Measurement Method

**Bar:** Per TCD 22022420609 §5: PLR status correctly reflects PROCHOT as active limiter during assertion and clears on deassertion.
