# Deep Analysis: [Thermal Interrupts] Verify PROCHOT Interrupt

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421627 |
| **Title** | [Thermal Interrupts] Verify PROCHOT Interrupt |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | PROCHOT thermal interrupt — core MSR 0x19b and package MSR 0x1b2; DFX injection |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Verifies **PROCHOT_INT_ENABLE** — bidirectional PROCHOT# assertion interrupt. Fires on rising edge of PROCHOT# when enabled. Tested on both:
- Core MSR 0x19b (PROCHOT_INT_ENABLE)
- Package MSR 0x1b2 (PROCHOT_INT_ENABLE)

Uses DFX injection to assert PROCHOT#. On NWP, DFX PROCHOT injection path differs from OakStream naming.

---

## Section B: NWP-Specific Test Procedure

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Enable PROCHOT_INT_ENABLE in both MSR 0x19b (per-core) and 0x1b2 (pkg) | All 96 NWP cores |
| 2 | Run prochot PMx | `python runPmx.py -x nwp.xml -p thermal_interrupt -tM 60 -M 5` |
| 3 | DFX inject PROCHOT# | NWP DFX path (see note below) |
| 4 | Verify PROCHOT interrupt delivered on rising edge | APIC interrupt |
| 5 | Remove PROCHOT#; verify interrupt clears | Falling edge = no interrupt |

### NWP DFX PROCHOT Injection (Adaptation)

The DMR steps reference OakStream/Simics-specific paths:
```
oakstream.mb.mcp0.imh_die0.punit.punit[0]->prochot_trigger
```

On NWP silicon, use SVOS/Python PROCHOT injection:
```python
# NWP PROCHOT injection via PythonSV
sv.socket0.imh0.punit.prochot_trigger.write(1)
# Verify PROCHOT status
prochot_status = sv.socket0.imh0.punit.prochot_status.read()
print(f"PROCHOT status: {prochot_status}")
```

### NWP Pass Criteria
- PROCHOT interrupt fires on rising edge of PROCHOT# assertion
- Both core-level and package-level PROCHOT interrupt enables functional
- DFX inject PROCHOT# → interrupt delivered

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; PROCHOT interrupt same; DFX path differs**

1. `python runPmx.py -x nwp.xml -p thermal_interrupt -tM 60 -M 5`
2. Use NWP PythonSV PROCHOT inject path (not OakStream Simics syntax)

**Priority**: Medium — `plc.feature.p1`; PROCHOT interrupt silicon verification
