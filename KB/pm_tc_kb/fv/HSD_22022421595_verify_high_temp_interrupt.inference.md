# Deep Analysis: [Thermal Interrupts] Verify HIGH_TEMP Interrupt

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421595 |
| **Title** | [Thermal Interrupts] Verify HIGH_TEMP Interrupt |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | HIGH_TEMP thermal interrupt — core MSR 0x19b and package MSR 0x1b2 |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Verifies **HIGH_TEMP_INT_ENABLE** — thermal interrupt on transition from low to high temperature (above thermal monitor trip point). Tested on both:
- Core MSR 0x19B (`IA32_THERM_INTERRUPT`)
- Package MSR 0x1B2 (`IA32_PACKAGE_THERM_INTERRUPT`)

On NWP, same MSRs present. `dmr.xml` → `nwp.xml`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Enable HIGH_TEMP_INT in core MSR 0x19b | Per-core (96 NWP cores) |
| 2 | Enable HIGH_TEMP_INT in pkg MSR 0x1b2 | Package-scoped |
| 3 | Run thermal_interrupt PMx | `python runPmx.py -x nwp.xml -p thermal_interrupt -tM 60 -M 5` |
| 4 | Force temperature increase (reduce cooling or inject) | DFX thermal injection |
| 5 | Verify HIGH_TEMP interrupt delivered to OS | APIC thermal interrupt |
| 6 | Verify interrupt fires on high→low transition for LOW_TEMP as well | Counter-test |

### NWP Pass Criteria
- HIGH_TEMP interrupt fires when die temperature crosses thermal trip point upward
- Both core and package MSR enable bits functional
- No spurious interrupts when temperature below trip

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; HIGH_TEMP interrupt same mechanism**

1. `python runPmx.py -x nwp.xml -p thermal_interrupt -tM 60 -M 5`
2. NWP 96 cores: core interrupt enable needs to be set per-core

**Priority**: Medium — `plc.feature.p1` + `NGA_MAIN`; thermal interrupt bring-up check
