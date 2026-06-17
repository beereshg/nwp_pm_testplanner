# Deep Analysis: [TPMI/PMT] Verify Aggregate Margin to Tcontrol PMT Register

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421558 |
| **Title** | [TPMI/PMT] Verify Aggregate Margin to Tcontrol PMT Register |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > TPMI/PMT |
| **Sub-Feature** | PMT PCS Index 10 — Aggregate Margin to Tcontrol |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **Aggregate Margin to Tcontrol PMT register** (PCS index 10). The formula is:

```
MARGIN_TO_TCONTROL = (EFFECTIVE_TJ_MAX - FUSED_T_CONTROL_OFFSET + DTS_CONFIG3.TCONTROL_OFFSET) - MAX_TEMPERATURE
```

where `MAX_TEMPERATURE` is the hottest temperature across all package dies, collected via HPM `SOCKET_THERMAL`. On NWP, the same PMT register and calculation exist. The register paths use the root iMH as the aggregator (same single-IMH path on NWP). Key NWP adaptation: `dmr.xml` → `nwp.xml`, and the CBB register path is `cbb{0,1}` (not `cbbs` with 4 instances).

**Key Justification:**
- PMT Aggregate Margin to Tcontrol is present on NWP
- `NGA_MAIN` tag: high priority for NGA silicon automation
- Same HPM SOCKET_THERMAL aggregation mechanism (2 CBBs → 1 iMH on NWP)
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon with all CBBs active and thermal reporting initialized
- PMT enabled and readable
- `EFFECTIVE_TJ_MAX` known (from fuses + BIOS TCC offset)

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run PMT thermal test | `python runPmx.py -x nwp.xml -p pmt_thermal -tM 60 --retry_count 2` |
| 2 | Read `EFFECTIVE_TJ_MAX` (per TC 14019959390) | Same calculation; NWP fused TJ_MAX value |
| 3 | Read `PKG_MAX_TEMPERATURE` — hottest temp across dies | NWP: 2 CBBs (`cbb0`, `cbb1`) + `imh0`; read from iMH aggregator |
| 4 | Read `T_CONTROL_OFFSET` fuse and `DTS_CONFIG3.TCONTROL_OFFSET` | Same register names on NWP |
| 5 | Calculate expected `MARGIN_TO_TCONTROL` | `(EFFECTIVE_TJ_MAX - FUSED_T_CONTROL_OFFSET + TCONTROL_OFFSET) - MAX_TEMPERATURE` |
| 6 | Read PMT register and compare | `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.margin_to_tcontrol` |

### NWP Register Paths

| Register | DMR Path | NWP Path |
|----------|---------|---------|
| Package temperature (CBB) | `sv.sockets.cbbs.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.package_temperature` | `sv.socket0.cbb{0,1}.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.package_temperature` |
| Package temperature (iMH) | `sv.sockets.imhs.uncore.pm_gen4_punit0.ptpcioregs.ptpcioregs.package_temperature` | `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_temperature` |

### NWP Pass Criteria
- PMT `MARGIN_TO_TCONTROL` matches formula calculation within ±1°C tolerance
- Value updates on slow loop interval (~1 sec typical)
- Value becomes negative when temperature exceeds Tcontrol → thermal throttle expected

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Max temp aggregation | 4 CBBs → iMH | 2 CBBs → iMH | Fewer sources; same aggregation logic |
| PMT register | `ptpcioregs.margin_to_tcontrol` | Same register name on NWP | Direct reuse |
| `EFFECTIVE_TJ_MAX` calculation | Per TC 14019959390 | Same formula on NWP | Verify NWP-specific TJ_MAX fuse value |
| `sv.sockets` pattern | Multi-socket/CBB iteration | NWP: `sv.socket0.cbb{0,1}` | Update iteration loop |

---

## Section D: Key Registers & Validation Points

```python
# NWP: Aggregate Margin to Tcontrol PMT
import max as max_func

# Read package temperature from each source (NWP: 2 CBBs + 1 iMH)
temps = []
for cbb_idx in range(2):
    cbb = getattr(sv.socket0, f'cbb{cbb_idx}')
    try:
        temp = cbb.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.package_temperature.read()
        temps.append(temp)
        print(f"CBB{cbb_idx} Package Temp: {temp}")
    except Exception as e:
        print(f"CBB{cbb_idx}: {e}")

try:
    imh_temp = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_temperature.read()
    temps.append(imh_temp)
    print(f"iMH0 Package Temp: {imh_temp}")
except Exception as e:
    print(f"iMH0 temp: {e}")

pkg_max_temp = max(temps) if temps else None
print(f"PKG_MAX_TEMPERATURE: {pkg_max_temp}")

# Read PMT margin_to_tcontrol
try:
    margin = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.margin_to_tcontrol.read()
    print(f"PMT MARGIN_TO_TCONTROL: {margin}")
except Exception as e:
    print(f"PMT MARGIN: {e}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **NWP `EFFECTIVE_TJ_MAX`** — depends on NWP-specific TJ_MAX fuse and BIOS TCC offset; verify from NWP thermal HAS | Low | Same formula; just different fuse values |
| 2 | **`sv.sockets` iteration** — DMR test may use `sv.sockets.cbbs` iterator; NWP: use `cbb0`, `cbb1` | Low | Update test script CBB iteration |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; update CBB iteration to 2**

PMT Aggregate Margin to Tcontrol calculation is identical. NWP adaptation is minimal.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p pmt_thermal -tM 60 --retry_count 2`
2. Update CBB iteration: `range(2)` for NWP (not 4)
3. Verify NWP TJ_MAX fuse value for expected calculation

**Priority**: High — NGA_MAIN; thermal margin reporting is a key validation metric
