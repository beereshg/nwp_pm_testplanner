# Deep Analysis: [Thermal Interrupts] Verify THRESHOLD_1 Interrupt

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421629 |
| **Title** | [Thermal Interrupts] Verify THRESHOLD_1 Interrupt |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | Threshold 1 thermal interrupt — core MSR 0x19b and package MSR 0x1b2 |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Verifies **THRESHOLD_1** — programmable thermal threshold interrupt. Fields:
- `THRESHOLD_1_INT_ENABLE`: enable interrupt generation on threshold 1 crossing
- `THRESHOLD_1_REL_TEMP`: threshold 1 temperature, degrees below Tj_max

Tested on both core MSR 0x19b and package MSR 0x1b2. Directly applicable on NWP.

---

## Section B: NWP-Specific Test Procedure

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Set THRESHOLD_1_REL_TEMP to small value (e.g., 5°C below Tj_max) | Core and package MSRs |
| 2 | Enable THRESHOLD_1_INT_ENABLE | Core (per 96 NWP cores) + Package |
| 3 | Run thermal_interrupt PMx | `python runPmx.py -x nwp.xml -p thermal_interrupt -tM 60 -M 5` |
| 4 | Drive temperature to exceed threshold | Thermal load |
| 5 | Verify THRESHOLD_1 interrupt fires on crossing | APIC thermal interrupt |
| 6 | Verify fires again on return crossing (bidirectional) | Both up and down crossings |

### NWP Pass Criteria
- THRESHOLD_1_REL_TEMP programmed correctly in both MSRs
- Interrupt fires on both rising and falling temperature crossing of THRESHOLD_1
- Both core-level and package-level enable bits functional

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; THRESHOLD_1 same mechanism**

1. `python runPmx.py -x nwp.xml -p thermal_interrupt -tM 60 -M 5`

**Priority**: Medium — `plc.feature.p1`; programmable threshold interrupt verification
