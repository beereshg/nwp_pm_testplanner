# Deep Analysis: [Thermal Interrupts] Verify THRESHOLD_2 Interrupt

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421633 |
| **Title** | [Thermal Interrupts] Verify THRESHOLD_2 Interrupt |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | Threshold 2 thermal interrupt — core MSR 0x19b and package MSR 0x1b2 |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Verifies **THRESHOLD_2** — second programmable thermal threshold interrupt. Fields:
- `THRESHOLD_2_INT_ENABLE`: enable interrupt on threshold 2 crossing
- `THRESHOLD_2_REL_TEMP`: degrees below Tj_max (same field structure as THRESHOLD_1)

Tested on both core MSR 0x19b and package MSR 0x1b2. Identical mechanism to THRESHOLD_1 with different threshold value. Directly applicable on NWP.

---

## Section B: NWP-Specific Test Procedure

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Set THRESHOLD_2_REL_TEMP to different value than THRESHOLD_1 (e.g., 10°C below Tj_max) | Core + Package MSRs |
| 2 | Enable THRESHOLD_2_INT_ENABLE | Core (96 cores) + Package |
| 3 | Run thermal_interrupt PMx | `python runPmx.py -x nwp.xml -p thermal_interrupt -tM 60 -M 5` |
| 4 | Drive temperature through THRESHOLD_2 (below THRESHOLD_1) | Thermal load |
| 5 | Verify THRESHOLD_2 interrupt fires independently of THRESHOLD_1 | Separate interrupt |
| 6 | Cross-product: enable both THRESHOLD_1 and THRESHOLD_2; verify both fire | Cascaded thresholds |

### NWP Pass Criteria
- THRESHOLD_2 fires independently from THRESHOLD_1
- Both up and down crossings trigger interrupt
- Core and package THRESHOLD_2 enables functional

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; THRESHOLD_2 same mechanism as THRESHOLD_1**

1. `python runPmx.py -x nwp.xml -p thermal_interrupt -tM 60 -M 5`

**Priority**: Medium — `plc.feature.p1`; second programmable threshold interrupt verification
