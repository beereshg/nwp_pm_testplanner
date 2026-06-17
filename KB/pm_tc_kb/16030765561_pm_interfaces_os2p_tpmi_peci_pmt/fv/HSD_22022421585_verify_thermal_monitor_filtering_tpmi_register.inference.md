# Deep Analysis: [TPMI/PMT] Verify Thermal Monitor Filtering TPMI Register

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421585 |
| **Title** | [TPMI/PMT] Verify Thermal Monitor Filtering TPMI Register |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > TPMI/PMT |
| **Sub-Feature** | PMT PCS Index 20 (extension) — Thermal Monitor Filtering |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test is an extension of TC 22022421578 (Package Thermal Status TPMI) — it verifies the **Thermal Monitor Filtering TPMI register** that controls a time delay (Tau value) for the Thermal Monitor Status assertion. The filtering algorithm is:

```
if (PKG_MAX_TEMPERATURE >= EFFECTIVE_TJ_MAX):
    RAW_THERMAL_MONITOR_STATUS = 1
else:
    RAW_THERMAL_MONITOR_STATUS = 0

CURRENT_THERMAL_MONITOR_STATUS = EWMA_FILTER(RAW_THERMAL_MONITOR_STATUS, TAU)
```

The Tau value (filter time constant) is set in the Thermal Monitor Filtering TPMI register and controls how quickly the status bit responds to temperature crossing. The command uses a custom script `thermalManagement.py` / `Demo_DMR_TMF.py`. On NWP, same filtering mechanism exists. Primary adaptation: update script for NWP (XML reference), validate register path.

**Key Justification:**
- Thermal Monitor Filtering via Tau value is present on NWP
- Same EWMA (Exponentially Weighted Moving Average) filtering algorithm
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP
- Custom script needs NWP adaptation (`Demo_DMR_TMF.py` → NWP equivalent)

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon with thermal reporting active
- Tau value programmable via TPMI write
- `thermalManagement.py` module available (or `pm.Active_pm.Thermal_Management.CPU_Thermal_Management.Demo_DMR_TMF.py` adapted for NWP)

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Read current Tau value from Thermal Monitor Filtering TPMI register | `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.thermal_monitor_filter.read()` |
| 2 | Program a known Tau value | TPMI write; same register on NWP |
| 3 | Trigger temperature crossing (inject temp above EFFECTIVE_TJ_MAX) | NWP DTS override mechanism |
| 4 | Verify thermal monitor status asserts with expected delay derived from Tau | Poll `PACKAGE_THERM_STATUS.THERMAL_MONITOR_STATUS`; measure time to assert |
| 5 | Compare measured delay to expected delay from Tau formula | `Tau_seconds = (Tau_value * slow_loop_period)` or per TPMI HAS formula |
| 6 | Restore temperature and verify status de-asserts with same Tau delay | Same filter applies on de-assertion |

### Filtering Formula

```
# Per DMR TPMI HAS (same on NWP):
if CURRENT_THERMAL_MONITOR_STATUS == 1:
    # Once asserted, stay asserted for Tau slow loops before de-asserting
    FILTER_COUNTDOWN = TAU
elif RAW_THERMAL_MONITOR_STATUS == 0 and FILTER_COUNTDOWN > 0:
    FILTER_COUNTDOWN -= 1
    if FILTER_COUNTDOWN == 0:
        CURRENT_THERMAL_MONITOR_STATUS = 0
```

### NWP Pass Criteria
- Thermal Monitor Status assertion delayed by Tau × slow_loop_period after temp crossing
- Different Tau values produce proportionally different delays
- Filter behavior consistent with TPMI HAS specification

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Thermal Monitor Filtering TPMI | `ptpcioregs.thermal_monitor_filter` | Same on NWP | Direct reuse |
| Tau formula | Per DMR TPMI HAS | Same algorithm on NWP | No change |
| Custom script | `Demo_DMR_TMF.py` | NWP equivalent needed | Script uses `dmr` in filename; adapt for NWP |
| Slow loop period | ~1 second (approx) | Same on NWP | Same timing |

---

## Section D: Key Registers & Validation Points

```python
import time

# NWP Thermal Monitor Filtering Validation

# Read Tau value from TPMI
try:
    tmf = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.thermal_monitor_filter.read()
    print(f"THERMAL_MONITOR_FILTER (Tau): 0x{tmf:08X}")
    tau_value = tmf & 0xFF  # Tau typically in bits [7:0]
    print(f"Tau value: {tau_value}")
except Exception as e:
    print(f"THERMAL_MONITOR_FILTER: {e}")

# Poll thermal monitor status over time
try:
    for i in range(20):
        status = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_therm_status.thermal_monitor_status.read()
        temp = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_temperature.read()
        print(f"t={i}: TM_STATUS={status}, TEMP={temp}")
        time.sleep(1)
except Exception as e:
    print(f"Poll: {e}")
```

---

## Section F: Recommendation

**Recommendation: ADAPT — port `Demo_DMR_TMF.py` script to NWP; register path same**

Thermal Monitor Filtering is architecturally identical on NWP. The custom script name references DMR and needs NWP adaptation.

Required adaptations:
1. Port `pm.Active_pm.Thermal_Management.CPU_Thermal_Management.Demo_DMR_TMF.py` to NWP variant
2. `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.thermal_monitor_filter` — same path on NWP
3. Verify NWP slow loop period for Tau delay calculation

**Priority**: Low-Medium — PMT filtering verification; extends TC 22022421578
