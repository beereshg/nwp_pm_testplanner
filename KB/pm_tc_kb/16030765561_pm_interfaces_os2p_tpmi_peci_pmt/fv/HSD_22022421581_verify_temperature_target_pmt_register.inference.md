# Deep Analysis: [TPMI/PMT] Verify Temperature Target PMT Register

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421581 |
| **Title** | [TPMI/PMT] Verify Temperature Target PMT Register |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > TPMI/PMT |
| **Sub-Feature** | PMT PCS Index 16 — Temperature Target |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies three fields of the **Temperature Target PMT register** (PCS index 16):

1. **`TJ_MAX_TCC_OFFSET`** — customer-programmable offset, defaults to 0
2. **`FAN_TEMP_TARGET_OFFSET [15:8]`** — fan engagement temperature, relative to thermal monitor trip temperature; programmed by PrimeCode from `FUSED_T_CONTROL_OFFSET`
3. **`REF_TEMP [23:16]`** — `EFFECTIVE_TJMAX - FUSE_DTS_CAL_GUARDBAND`

On NWP, the same Temperature Target register exists with the same field definitions. The fuse names (`FUSED_T_CONTROL_OFFSET`, `FUSE_DTS_CAL_GUARDBAND`, `EFFECTIVE_TJMAX`) are the same architecture. Primary adaptation: `dmr.xml` → `nwp.xml` and verify NWP fuse values.

**Key Justification:**
- Temperature Target PMT register is present on NWP (same TPMI interface)
- Same three field checks with same fuse-based expected values
- `DMR_PO` tag: silicon validation bring-up priority
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP

---

## Section B: NWP-Specific Test Procedure

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Run PMT thermal test | `python runPmx.py -x nwp.xml -p pmt_thermal -tM 60 --retry_count 2` |
| 2 | Read `TJ_MAX_TCC_OFFSET` from Temperature Target register | Expect 0 default; may be customer-programmed via BIOS |
| 3 | Read `FAN_TEMP_TARGET_OFFSET [15:8]` | Verify = `FUSED_T_CONTROL_OFFSET` (from NWP fuse) |
| 4 | Read `REF_TEMP [23:16]` | Verify = `EFFECTIVE_TJMAX - FUSE_DTS_CAL_GUARDBAND` |
| 5 | Cross-reference with iMH fuses: `pcode_itd_cutoff_tj` as proxy for TJ_MAX (if direct fuse read available) | NWP fuse read via `sv.socket0.imh0.fuses.*` |

### Expected Values

| Field | Expected Value | Source |
|-------|----------------|--------|
| `TJ_MAX_TCC_OFFSET` | 0 (default) | BIOS programmable |
| `FAN_TEMP_TARGET_OFFSET` | `FUSED_T_CONTROL_OFFSET` fuse value | NWP thermal fuse |
| `REF_TEMP` | `EFFECTIVE_TJMAX - FUSE_DTS_CAL_GUARDBAND` | NWP TJ_MAX fuse minus guardband |

### NWP Pass Criteria
- All three fields match expected fuse-based values
- `REF_TEMP` correctly reflects NWP TJ_MAX and DTS calibration guardband
- `FAN_TEMP_TARGET_OFFSET` correctly programmed by PrimeCode at boot

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Temperature Target register | PMT PCS 16 | Same on NWP | Direct reuse |
| TJ_MAX fuse | DMR-specific value | NWP-specific value | Read NWP fuse for expected calculation |
| `FUSED_T_CONTROL_OFFSET` | DMR fuse | NWP fuse | NWP thermal management fuse |
| `FUSE_DTS_CAL_GUARDBAND` | DMR guardband | NWP guardband | May differ by a few °C |

---

## Section D: Key Registers & Validation Points

```python
# NWP Temperature Target PMT Validation

try:
    temp_target = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.temperature_target.read()
    print(f"TEMPERATURE_TARGET: 0x{temp_target:08X}")

    # Field extraction
    tcc_offset = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.temperature_target.tj_max_tcc_offset.read()
    fan_offset = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.temperature_target.fan_temp_target_offset.read()
    ref_temp = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.temperature_target.ref_temp.read()

    print(f"  TJ_MAX_TCC_OFFSET: {tcc_offset} (expected 0)")
    print(f"  FAN_TEMP_TARGET_OFFSET: {fan_offset} (expected = FUSED_T_CONTROL_OFFSET)")
    print(f"  REF_TEMP: {ref_temp} (expected = EFFECTIVE_TJMAX - DTS_CAL_GUARDBAND)")
except Exception as e:
    print(f"TEMPERATURE_TARGET: {e}")

# NWP fuse cross-reference
try:
    tj_cutoff = sv.socket0.imh0.fuses.punit.pcode_itd_cutoff_tj.read()
    print(f"ITD_CUTOFF_TJ fuse (proxy for TJ_MAX): {tj_cutoff}")
except Exception as e:
    print(f"TJ fuse: {e}")
```

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; read NWP fuse values for expected calculation**

Temperature Target PMT register is architecturally identical. Only fuse values differ (NWP TJ_MAX, T_CONTROL_OFFSET, DTS_CAL_GUARDBAND).

Required adaptations:
1. `python runPmx.py -x nwp.xml -p pmt_thermal -tM 60 --retry_count 2`
2. Get NWP-specific `FUSED_T_CONTROL_OFFSET` and `FUSE_DTS_CAL_GUARDBAND` values
3. Calculate NWP `EFFECTIVE_TJMAX` from NWP thermal HAS

**Priority**: Medium — DMR_PO; foundational temperature target bring-up verification
