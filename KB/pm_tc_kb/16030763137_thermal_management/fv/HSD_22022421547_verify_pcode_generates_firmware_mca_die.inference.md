# Deep Analysis: [MCAs] Verify Pcode Generates Firmware MCA "DIE TOO HOT" on Invalid Temperature

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421547 |
| **Title** | [MCAs] Verify Pcode generates firmware MCA "DIE TOO HOT" on invalid temperature |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | Pcode MCA — DIE TOO HOT firmware MCA on POST_CATASTROPHIC_TEMPERATURE |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies Pcode generates a **firmware MCA "DIE TOO HOT"** when a die temperature exceeds the `POST_CATASTROPHIC_TEMPERATURE` (135°C constant):

Background from test steps:
- Thermal sensor data arrives at Punit via telemetry from Resource Controllers (RCs), pushed periodically
- After calibration, Pcode compares temperature to `POST_CATASTROPHIC_TEMPERATURE = 135°C`
- Above 135°C → Pcode triggers firmware MCA (`MCA_RECOVERABLE_DIE_TOO_HOT`)
- Implementation: `MCA_recoverable_die_too_hot.py`

On NWP:
- Same temperature threshold (135°C constant)
- RC telemetry pushed from CBBs (2) to imh0 Punit
- Tags: `DMR_PO`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`

---

## Section B: NWP-Specific Test Procedure

### Thermal MCA Architecture (NWP)

| Component | Role |
|-----------|------|
| CBB Resource Controllers (×2) | Push thermal telemetry to imh0 Punit periodically |
| imh0 Punit Pcode | Calibrates and compares to 135°C threshold |
| POST_CATASTROPHIC_TEMPERATURE | 135°C (compile-time constant in Pcode) |
| MCA action | Pcode triggers `MCA_RECOVERABLE_DIE_TOO_HOT` |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run `MCA_recoverable_die_too_hot.py` | Python script (PMx or standalone) targeting NWP |
| 2 | Inject invalid (>135°C) temperature via thermal telemetry | Override DTS/telemetry on cbb0 or cbb1 die |
| 3 | Wait for Pcode Slowloop to process telemetry | Punit receives pushed telemetry from RC |
| 4 | Verify firmware MCA "DIE TOO HOT" is generated | Check MCA log; Punit MCA status registers |
| 5 | Verify MCA code and die identity reported correctly | Per-die attribution (cbb0 vs cbb1) |
| 6 | Recover from MCA; verify system stability | Standard MCA recovery flow |

### NWP Notes
- 2 CBBs: test with cbb0 as source and separately with cbb1 as source
- Single imh0: all telemetry flows through `sv.socket0.imh0.punit.*`
- Script `MCA_recoverable_die_too_hot.py` must target NWP (use NWP-adapted register paths)
- `POST_CATASTROPHIC_TEMPERATURE = 135°C` is a Pcode constant (not a fuse) — same on NWP

### Pass Criteria
- DIE TOO HOT firmware MCA generated when temperature > 135°C injected
- MCA correctly identifies the affected die (cbb0 or cbb1)
- MCA recovery completes without system hang
- No MCA generated below the 135°C threshold

---

## Section D: Key Registers & Validation Points

```python
# Check Punit thermal telemetry registers (NWP)
sv.socket0.imh0.punit.pkg_therm_status.show()

# Check MCA status after DIE TOO HOT trigger
# (Check IA32_MCi_STATUS registers for Pcode-originated MCA bank)
# Pcode MCA bank: check Machine Check Architecture registers
```

---

## Section F: Recommendation

**Recommendation: ADOPT — NWP 2 CBBs; test both die sources; MCA threshold (135°C) same as DMR**

1. Adapt `MCA_recoverable_die_too_hot.py` to NWP register paths
2. Test with injected temperature > 135°C from cbb0, then cbb1
3. Verify Pcode DIE TOO HOT MCA generation and attribution
4. Verify clean MCA recovery

**Priority**: High — `plc.feature.p1`; firmware MCA on catastrophic temperature is critical safety coverage
