# Deep Analysis: [Thermal Reporting] Verify IA32_THERM_STATUS (Core MSR 0x19c)

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421647 |
| **Title** | [Thermal Reporting] Verify IA32_THERM_STATUS (Core MSR 0x19c) |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | Core MSR 0x19C IA32_THERM_STATUS — per-core thermal status |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **Core MSR 0x19C IA32_THERM_STATUS** — per-core thermal status updated by CBB:
- `THERMAL_MONITOR_STATUS` [0]: TM currently throttling
- `THERMAL_MONITOR_LOG` [1]: Sticky TM trip
- `PROCHOT` [2/3]: PROCHOT status/log
- `OOS_TIE_OFF` [4/5]: Out-of-spec status/log
- `Thresholds` [6–9]: Threshold 1 and 2 status/log
- `Temperature` [22:16]: Margin below Tj_max
- `Resolution` [29]: Temperature resolution
- `Valid` [31]: Temperature reading valid

On NWP (non-SMT): this is a **core-scoped** MSR (1 per physical core, not per thread).

**Key Justification:**
- `DMR_PO` + `plc.feature.p1` + `PMSS_NWP_READINESS_CHECK` tags
- Core thermal status directly applicable on NWP

---

## Section B: NWP-Specific Test Procedure

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run thermal_interrupt PMx | `python runPmx.py -x nwp.xml -p thermal_interrupt -tM 60 -M 5` |
| 2 | Read MSR 0x19C per core | All 96 NWP cores (2 CBBs × 48) |
| 3 | Verify VALID bit set and temperature non-zero | `ia32_therm_status[31] = 1` |
| 4 | Force thermal condition; verify TM bits | Assert PROCHOT or thermal limit |
| 5 | Verify sticky log bits set on event | Write back to clear |

### NWP Per-Core Read

```python
import svtools.common.baseaccess as baseaccess
base = baseaccess.getglobalbase()

for cbb_idx in range(2):
    cbb = getattr(sv.socket0, f'cbb{cbb_idx}')
    for module_idx in range(24):  # 48 cores per CBB, 2 cores per module
        for core_idx in range(2):
            # Read IA32_THERM_STATUS per core via apicid affinity
            abs_core = cbb_idx * 48 + module_idx * 2 + core_idx
            try:
                therm_status = base.rdmsr_on_core(0x19C, cbb_idx, abs_core % 48)
                temp_margin = (therm_status >> 16) & 0x7F
                valid = (therm_status >> 31) & 1
                print(f"CBB{cbb_idx} core{abs_core % 48}: margin={temp_margin}°C, valid={valid}")
            except Exception as e:
                pass
```

### NWP Pass Criteria
- MSR 0x19C valid and non-zero temperature on all 96 cores
- Thermal status bits update correctly on thermal event
- Sticky log bits clear on SW write

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; per-core thermal status same on NWP**

Required adaptations:
1. `python runPmx.py -x nwp.xml -p thermal_interrupt -tM 60 -M 5`
2. NWP non-SMT: per-core (not per-thread); 96 cores total
3. Avoid thread-indexed MSR access (use core affinity)

**Priority**: High — `DMR_PO` + `plc.feature.p1`; per-core thermal status bring-up check
