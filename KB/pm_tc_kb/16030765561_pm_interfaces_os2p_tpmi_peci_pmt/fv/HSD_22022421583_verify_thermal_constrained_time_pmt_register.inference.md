# Deep Analysis: [TPMI/PMT] Verify Thermal Constrained Time PMT Register

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421583 |
| **Title** | [TPMI/PMT] Verify Thermal Constrained Time PMT Register |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > TPMI/PMT |
| **Sub-Feature** | PMT PCS Index 32 — Thermal Constrained Time |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **Thermal Constrained Time PMT register** (PCS index 32) — a counter that accumulates time spent in thermally-constrained state (temperature exceeds Junction Temperature target). The test procedure is:
1. Note baseline counter value
2. Override temperature past Junction Temp (via DTS or DFX injection) to trigger thermal monitor
3. Verify counter increments while constrained
4. Remove override and verify counter stops incrementing

On NWP, the same Thermal Constrained Time counter exists in the PMT interface. Primary adaptation: `dmr.xml` → `nwp.xml`.

**Key Justification:**
- Thermal Constrained Time PMT counter present on NWP
- Same trigger mechanism (DTS temperature override or DFX injection)
- `DMR_PO` tag: silicon validation bring-up priority
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP

---

## Section B: NWP-Specific Test Procedure

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run PMT thermal test | `python runPmx.py -x nwp.xml -p pmt_thermal -tM 60 --retry_count 2` |
| 2 | Read baseline `THERMAL_CONSTRAINED_TIME` counter value | `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.thermal_constrained_time.read()` |
| 3 | Override temperature above Junction Temp via DTS or DFX injection | NWP DTS override mechanism (same as DMR; verify NWP DFX path) |
| 4 | Wait for counter to increment (thermal monitor active) | Poll counter; verify increment within slow-loop interval |
| 5 | Remove temperature override | Same |
| 6 | Verify counter stops incrementing when temperature returns below threshold | Same pass criterion |

### PMT Reference

- **PMT URL**: `https://docs.intel.com/documents/primecode/has/PMT_Definitions/dmr_imh/pmt_telemetry.html#package_temperature` (DMR reference; NWP equivalent URL TBD)
- **Counter resolution**: Typically accumulates in ms or 100ms increments per slow loop

### NWP Pass Criteria
- Baseline counter is stable (not incrementing in normal operation)
- Counter increments while temperature ≥ Junction Temp target
- Counter stops when temperature drops below threshold
- Counter value is monotonically non-decreasing (never decreases)

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Counter register | `ptpcioregs.thermal_constrained_time` | Same on NWP | Direct reuse |
| DTS temperature override | DMR DFX mechanism | NWP DFX/DTS override | Verify NWP DTS override method |
| Junction Temp threshold | DMR TJ_MAX | NWP TJ_MAX | Same detection logic; NWP-specific value |
| PMT documentation | DMR PMT HAS | NWP PMT HAS (TBD URL) | Get NWP PMT URL from NWP PM team |

---

## Section D: Key Registers & Validation Points

```python
import time

# NWP Thermal Constrained Time PMT Validation

# Step 2: Read baseline
try:
    t0 = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.thermal_constrained_time.read()
    print(f"Baseline THERMAL_CONSTRAINED_TIME: {t0}")
except Exception as e:
    print(f"Counter read: {e}")
    t0 = None

# (Step 3: Apply DTS override to trigger thermal monitor — platform-specific)
# sv.socket0.imh0.punit.dts_override.write(HIGH_TEMP_VALUE)

# Step 4: Poll counter increment
if t0 is not None:
    time.sleep(2)  # Wait for slow loop
    try:
        t1 = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.thermal_constrained_time.read()
        delta = t1 - t0
        print(f"After 2s: THERMAL_CONSTRAINED_TIME = {t1} (delta = {delta})")
        print("PASS" if delta > 0 else "FAIL (counter did not increment)")
    except Exception as e:
        print(f"Counter poll: {e}")
```

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; verify DTS override mechanism**

Thermal Constrained Time counter is architecturally identical. Primary risk is NWP DTS temperature override methodology.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p pmt_thermal -tM 60 --retry_count 2`
2. Verify NWP DTS override mechanism (same as DMR or NWP-specific DFX path)
3. Get NWP PMT documentation URL

**Priority**: Medium — DMR_PO; thermal constraint time tracking for compliance validation
