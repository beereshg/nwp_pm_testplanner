# Deep Analysis: [Thermal Interrupts] Verify LOW_TEMP Interrupt

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421618 |
| **Title** | [Thermal Interrupts] Verify LOW_TEMP Interrupt |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | LOW_TEMP thermal interrupt — core MSR 0x19b and package MSR 0x1b2 |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Verifies **LOW_TEMP_INT_ENABLE** — thermal interrupt on high-to-low temperature transition below thermal monitor trip temperature. Tested on both core MSR 0x19b and package MSR 0x1b2. Same mechanism as HIGH_TEMP but fires on cooling transition.

On NWP, same MSRs present. `dmr.xml` → `nwp.xml`.

---

## Section B: NWP-Specific Test Procedure

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Enable LOW_TEMP_INT in core MSR 0x19b [1] | Per-core (96 NWP cores) |
| 2 | Enable LOW_TEMP_INT in pkg MSR 0x1b2 [1] | Package-scoped |
| 3 | First trigger HIGH_TEMP (raise temperature above trip) | Required to enter "high" state |
| 4 | Run thermal_interrupt PMx | `python runPmx.py -x nwp.xml -p thermal_interrupt -tM 60 -M 5` |
| 5 | Remove thermal stress; temperature drops below trip | Cooling recovery |
| 6 | Verify LOW_TEMP interrupt delivered | APIC thermal interrupt on cooling |

### NWP Pass Criteria
- LOW_TEMP interrupt fires on high→low transition below trip point
- Both core (per 96 cores) and package MSR enables functional
- No spurious interrupt when temperature above trip

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; LOW_TEMP interrupt same mechanism**

1. `python runPmx.py -x nwp.xml -p thermal_interrupt -tM 60 -M 5`

**Priority**: Medium — `plc.feature.p1`; thermal interrupt cooling transition verification
