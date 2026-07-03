# Deep Analysis: [Thermal Reporting] Verify POWER_CTL

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421660 |
| **Title** | [Thermal Reporting] Verify POWER_CTL |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | MSR 0x1FC POWER_CTL — PROCHOT enable, C1E enable, thermal eff_tj_max |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **MSR 0x1FC POWER_CTL** — package-multicast register with key fields:
- `ENABLE_BIDIR_PROCHOT` [0]: enables response to PROCHOT# input (allows platform to throttle CPU)
- `C1E_ENABLE` [1]: enables C1E; **CBB uses this for eff_tj_max calculation**

The `C1E_ENABLE` interaction with `eff_tj_max` is critical — changing C1E enable affects effective Tj_max used in thermal management.

On NWP, `POWER_CTL` is the same package register. C1E_ENABLE affect on eff_tj_max same.

**Key Justification:**
- `Ready_for_testing` + `plc.feature.p1` + `NGA_MAIN` + `PMSS_NWP_READINESS_CHECK` tags
- POWER_CTL register directly applicable on NWP

---

## Section B: NWP-Specific Test Procedure

### MSR 0x1FC Key Bits

| Bit | Field | Default | Description |
|-----|-------|---------|-------------|
| [0] | `ENABLE_BIDIR_PROCHOT` | 0 | Enables PROCHOT# input response |
| [1] | `C1E_ENABLE` | 0 | Enables C1E idle; affects eff_tj_max |

### C1E + eff_tj_max Interaction

When `C1E_ENABLE = 1`:
- CBB uses `eff_tj_max = tj_max + c1e_offset` (slightly higher effective limit)
- This affects thermal throttling threshold

### NWP Verification

```python
import svtools.common.baseaccess as baseaccess
base = baseaccess.getglobalbase()

power_ctl = base.rdmsr(0x1FC)
bidir_prochot = (power_ctl >> 0) & 1
c1e_enable = (power_ctl >> 1) & 1
print(f"MSR 0x1FC POWER_CTL: 0x{power_ctl:08X}")
print(f"  ENABLE_BIDIR_PROCHOT: {bidir_prochot}")
print(f"  C1E_ENABLE: {c1e_enable}")

# Verify C1E_ENABLE matches expected BIOS setting
# Toggle C1E_ENABLE; verify eff_tj_max changes in MCP_THERMAL_REPORT_1
```

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Read MSR 0x1FC baseline | Verify default values |
| 2 | Enable BIDIR_PROCHOT; assert PROCHOT# | `POWER_CTL[0] = 1`; verify throttling |
| 3 | Disable BIDIR_PROCHOT; verify throttle released | Same |
| 4 | Toggle C1E_ENABLE; verify eff_tj_max changes | Read MCP_THERMAL_REPORT_1 before/after |

### NWP Pass Criteria
- `ENABLE_BIDIR_PROCHOT` correctly enables/disables PROCHOT# response
- `C1E_ENABLE` correctly affects `eff_tj_max` in CBB thermal calculation
- Register accessible as package-multicast (all CBBs see same value)

---

## Section F: Recommendation

**Recommendation: ADOPT — thermalManagement.py; POWER_CTL same on NWP**

Required adaptations:
1. NWP single IMH: package-multicast reaches both CBBs
2. Verify `eff_tj_max` calculation path in NWP CBB thermal implementation

**Priority**: Medium — `plc.feature.p1` + `NGA_MAIN`; POWER_CTL thermal + C1E interaction
