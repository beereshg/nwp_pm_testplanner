# Deep Analysis: [Thermal Interrupts] Verify IA32_THERM_INTERRUPT (Core MSR 0x19b)

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421614 |
| **Title** | [Thermal Interrupts] Verify IA32_THERM_INTERRUPT (Core MSR 0x19b) |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | Core MSR 0x19B IA32_THERM_INTERRUPT — per-core thermal interrupt control |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Verifies **Core MSR 0x19B IA32_THERM_INTERRUPT** — per-core thermal interrupt enable register. Controls:
- HIGH_TEMP, LOW_TEMP, PROCHOT, OUT_OF_SPEC (see note), THRESHOLD_1, THRESHOLD_2

**Note**: OUT_OF_SPEC interrupt at core scope is ZBB'd (package MSR 0x1b2 only for OOS). This ZBB also applies on NWP.

On NWP (non-SMT): per physical core (1 per core, not per thread).

**Key Justification:**
- `DMR_PO` + `plc.feature.p1` + `PMSS_NWP_READINESS_CHECK` tags

---

## Section B: NWP-Specific Test Procedure

### MSR 0x19B Scope on NWP

```python
import svtools.common.baseaccess as baseaccess
base = baseaccess.getglobalbase()

# Set HIGH_TEMP interrupt enable per core
therm_int_val = 0x1  # HIGH_TEMP_INT_ENABLE bit 0
for cbb_idx in range(2):
    for core_idx in range(48):
        try:
            base.wrmsr_on_core(0x19B, therm_int_val, cbb_idx, core_idx)
        except Exception as e:
            pass

# Run thermal_interrupt PMx
# python runPmx.py -x nwp.xml -p thermal_interrupt -tM 60 -M 5
```

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Set interrupt enables in MSR 0x19b per-core | 96 NWP cores |
| 2 | Run thermal_interrupt PMx | `python runPmx.py -x nwp.xml -p thermal_interrupt -tM 60 -M 5` |
| 3 | Trigger conditions; verify per-core interrupts | Each core generates interrupt independently |
| 4 | Verify OOS interrupt NOT from core MSR (package only) | ZBB on NWP too |

### NWP Pass Criteria
- Per-core MSR 0x19b accessible and writable
- HIGH, LOW, PROCHOT, THR1, THR2 interrupt enables functional
- OOS interrupt: package MSR only (core OOS ZBB'd)
- Per-core interrupts delivered to correct core's LAPIC

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; core thermal interrupt MSR same; OOS still ZBB at core scope**

1. `python runPmx.py -x nwp.xml -p thermal_interrupt -tM 60 -M 5`
2. NWP non-SMT: per-core MSR write (no thread index)

**Priority**: High — `DMR_PO` + `plc.feature.p1`; core thermal interrupt bring-up gate
