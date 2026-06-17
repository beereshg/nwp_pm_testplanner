# Deep Analysis: [TPMI/PMT] Verify Package Temperature PMT Register

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421576 |
| **Title** | [TPMI/PMT] Verify Package Temperature PMT Register |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > TPMI/PMT |
| **Sub-Feature** | PMT PCS Index 2 — Package Temperature |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **Package Temperature PMT register** (PCS index 2). This register reports temperature margin to throttle — the delta between maximum temperature and TJ_max. Individual dies calculate their own margins and send them to the root iMH via HPM `SOCKET_THERMAL`. Root PrimeCode takes the maximum across all dies and populates this register. On NWP: same architecture, single iMH receives from 2 CBBs. Primary adaptation: `dmr.xml` → `nwp.xml`, CBB count 2.

**Key Justification:**
- PMT Package Temperature register present on NWP
- Same HPM `SOCKET_THERMAL` aggregation: 2 CBBs → iMH on NWP
- `DMR_PO` tag: silicon validation bring-up priority
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon with thermal reporting active
- All CBBs sending temperature via `SOCKET_THERMAL` HPM

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run PMT thermal test | `python runPmx.py -x nwp.xml -p pmt_thermal -tM 60 --retry_count 2` |
| 2 | Read package temperature from each die | NWP: `sv.socket0.cbb{0,1}.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.package_temperature` |
| 3 | Read iMH aggregated package temperature | `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_temperature` |
| 4 | Verify iMH value = max across all sources | `max(cbb0_temp, cbb1_temp, imh0_internal_temp)` |
| 5 | Apply temperature stimulus and verify register updates | Stress workload; verify PMT temperature tracks |

### Formula

```
PACKAGE_TEMPERATURE_PMT = MAX(
    sv.socket0.cbb0.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.package_temperature,
    sv.socket0.cbb1.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.package_temperature,
    sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_temperature
)
```

### NWP Pass Criteria
- PMT `package_temperature` = max of all die temperatures
- Value updates with thermal changes within slow-loop interval
- HPM `SOCKET_THERMAL` correctly delivers CBB temperatures to iMH

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Die count | 4 CBBs + iMH(s) | 2 CBBs + 1 iMH | Fewer sources in max calculation |
| HPM `SOCKET_THERMAL` | 4 CBB sources | 2 CBB sources | Same mechanism; fewer HPM senders |
| PMT register path | `ptpcioregs.package_temperature` | Same on NWP iMH | Direct reuse |
| `sv.sockets.cbbs` DMR pattern | Iterates all CBBs | NWP: `cbb0`, `cbb1` | Update iteration |

---

## Section D: Key Registers & Validation Points

```python
# NWP Package Temperature PMT Validation
temps = {}

# CBB package temperatures
for cbb_idx in range(2):
    cbb = getattr(sv.socket0, f'cbb{cbb_idx}')
    try:
        temp = cbb.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.package_temperature.read()
        temps[f'cbb{cbb_idx}'] = temp
        print(f"CBB{cbb_idx} temperature: {temp}")
    except Exception as e:
        print(f"CBB{cbb_idx}: {e}")

# iMH aggregated package temperature
try:
    imh_temp = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_temperature.read()
    temps['imh0'] = imh_temp
    print(f"iMH0 package_temperature PMT: {imh_temp}")
except Exception as e:
    print(f"iMH0 PMT: {e}")

if temps:
    expected_max = max(temps.values())
    actual_pmt = temps.get('imh0', None)
    status = "PASS" if actual_pmt == expected_max else f"FAIL (expected {expected_max}, got {actual_pmt})"
    print(f"\nExpected PMT max: {expected_max} | Actual PMT: {actual_pmt} [{status}]")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **HPM `SOCKET_THERMAL` timing** — HPM delivery latency from CBB to iMH may cause transient mismatches; expect ±1 slow-loop tolerance | Low | Use average/stable workload for comparison |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; update CBB loop to 2**

Package Temperature PMT aggregation is architecturally identical on NWP. Straightforward port.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p pmt_thermal -tM 60 --retry_count 2`
2. Loop `range(2)` for CBBs (not 4)
3. `sv.socket0.cbb{0,1}` paths (not `sv.sockets.cbbs` iterator)

**Priority**: Medium — DMR_PO; fundamental thermal reporting bring-up verification
