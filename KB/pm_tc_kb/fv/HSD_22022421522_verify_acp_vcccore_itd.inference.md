# Deep Analysis: [ITD] Verify ACP (VccCore) ITD

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421522 |
| **Title** | [ITD] Verify ACP (VccCore) ITD |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > ITD |
| **Sub-Feature** | ACP (Autonomous Core Power) / VccCore |
| **NWP Disposition** | **Runnable_On_N-1** |

---


## Test Case Intent

Validates that VccCore (ACP) ITD compensation is correctly applied per core module. For each module: enables operating point reporting, reads core DTS temperature, reads actual voltage from the operating point register, reads current ratio and ICCP level, calculates base voltage from the multi-curve VF model (base + cdyn delta + aging delta), independently computes expected ITD offset using the dual-slope algorithm with per-core fuse coefficients, and verifies actual voltage matches expected within 26 mV guardband.

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

ACP (VccCore) ITD is controlled **autonomously by Acode** (per-core). Each core has an in-die FIVR fed by VccCore VR. Acode manages ITD+TTD simultaneously via: (1) periodic temperature readout folding voltage compensation into WP recalc, and (2) interrupt-based recalc when DTS crosses a threshold (non-sticky DTD bits). On NWP, PantherCove cores have the same Acode ITD architecture. NWP has 96 cores (2 CBBs × 48 cores) vs. DMR's structure, but the per-core Acode ITD mechanism is the same. Primary adaptation: `dmr.xml` → `nwp.xml`.

**Key Justification:**
- ACP (Acode) ITD for VccCore is present on NWP PantherCove cores
- Same 2-slope ITD algorithm with `VCCCORE_ITD_SLOPE/SLOPE_2` fuses
- `PMSS_NWP_READINESS_CHECK` tag: explicitly evaluated for NWP
- `DMR_PO` tag: silicon validation priority; WP test steps describe the Acode interrupt + periodic flow which is architecture-level (not DMR-specific)

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon platform with active cores (no SMT — NWP is non-SMT, 1 thread per core)
- ITD fuses non-zero (verified by TC 22022421521)
- PythonSv access to `sv.socket0.cbb0.*` and `sv.socket0.cbb1.*`
- Test command: `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3`

### Adapted Test Steps (from itd_pmx.py mainTest — Core class)

| Step | Action | Expected Result (PASS) | Failure Indication |
|------|--------|----------------------|-------------------|
| 1 | Enable operating point reporting on each PMA so voltage/ratio reads reflect real-time state | op_point_reporting_en = 1 for all modules | Write fails or register not accessible |
| 2 | Read per-core ITD fuse coefficients: slope, slope2, cutoff_v, cutoff_v2, cutoff_tj, min_override_temp, slope_above_cutoff_tj, min_accurate_temp | All fuses readable and slope/cutoff_v non-zero | Zero slope or cutoff_v — unprogrammed fuse |
| 3 | Read current core temperature from PMA thermal telemetry (value/2 − 64 = °C) | Temperature within valid range (−10°C to +110°C) | Out of range or read failure |
| 4 | Read current core voltage from operating point register (× 0.0025 V) | Voltage within FIVR operating range (0.4–1.2 V) | Zero or out-of-range voltage |
| 5 | Read current core ratio and ICCP grant level | Ratio > 0; ICCP level resolves to valid VF index | Zero ratio or invalid ICCP index |
| 6 | Calculate base voltage: interpolate base VF curve at ratio + cdyn delta VF at ICCP index + aging delta VF | Base voltage within valid range | VF curve lookup returns zero or out-of-bounds |
| 7 | Apply MIN_ACCURATE_TEMP guard: if temp < min_accurate_temp, substitute min_override_temp | Guard applied when temp is below threshold | Guard not applied — incorrect effective temp |
| 8 | Calculate expected ITD offset using dual-slope algorithm (min/max rule for core domains) | Offset non-negative in ITD zone | Negative offset in ITD zone |
| 9 | Compare expected voltage (base + offset) against actual core voltage | Delta ≤ 26 mV | Delta > 26 mV — ITD compensation mismatch |
| 10 | Repeat for every core module across all CBBs; log per-module results table | All modules show PASS | Any module shows FAIL |

### NWP-Specific Topology Notes
- NWP: 2 CBBs (`cbb0`, `cbb1`), 48 cores each, single-threaded (no SMT)
- DMR: 4 CBBs, 32 cores each, no SMT
- Core namespace on NWP: `sv.socket0.cbb{0,1}.compute[0-3].module[0-11]` (estimate; verify during bring-up)

### NWP Pass Criteria
- ACP ITD active: `itd.print_itd_info(0, 0)` shows non-zero VCCCORE compensation
- Interrupt path: DTS ±3°C threshold crossing triggers fast recalc (~30-60 μS)
- Periodic path: compensation updated within ~300 μS
- FIVR output matches expected ITD calculation from fuse values

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Core count | 4 CBBs × 32 cores = 128 | 2 CBBs × 48 cores = 96 | Loop count differs; per-core mechanism identical |
| SMT | No | No | Same — single-threaded core ITD |
| Acode ITD mechanism | Per-core, autonomous | Same on NWP | Direct reuse |
| VCCCORE FIVR | In-die FIVR per core | Same on NWP | Same compensation path |
| XML config | `dmr.xml` | `nwp.xml` | **Must update** |

---

## Section D: Key Registers & Validation Points

### PythonSv Validation Commands (NWP)

```python
from pm.focus import itd

# Print ITD info for socket 0
SockNum = 0
itd.print_itd_info(SockNum, 0)

# Per-core DTS read (NWP cbb0 example — 48 cores per CBB)
for cbb_idx in range(2):  # NWP has 2 CBBs
    cbb = getattr(sv.socket0, f'cbb{cbb_idx}')
    print(f"=== CBB{cbb_idx} Core DTS ===")
    try:
        # Adapt to actual NWP core hierarchy
        for core_idx in range(48):
            try:
                dts = cbb.getbypath(f"compute[{core_idx // 12}].module[{core_idx % 12}].dts.temperature").read()
                print(f"  Core[{core_idx}] DTS: {dts} °C")
            except Exception:
                pass
    except Exception as e:
        print(f"CBB{cbb_idx}: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **NWP core hierarchy path** — exact namednodes path for NWP cores needs bring-up validation | Low | Use `sv.socket0.cbb0.search('dts', 'c')` to locate correct path |
| 2 | **NWP Acode ACP ITD fuse names** — fuse names assumed same as DMR; verify with NWP MAS | Low | `itd.print_itd_info` should expose values |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; adapt core loop count**

ACP VccCore ITD is the same architecture on NWP. The only adaptation is the XML config and core count (96 vs 128).

Required adaptations:
1. `python runPmx.py -x nwp.xml -p itd_thermal -tM 9 -M 3`
2. Update per-core loop: 2 CBBs × 48 cores (not 4 CBBs × 32)
3. Verify NWP core DTS namednodes path during bring-up

**Priority**: Medium — DMR_PO; foundational ITD bring-up test
