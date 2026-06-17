# Deep Analysis: [PECI] Verify DIMM Thresholds Match Default Values

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421352 |
| **Title** | [PECI] Verify DIMM thresholds match with default values programed by BIOS |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Memory Thermal Management |
| **Sub-Feature** | PECI-based CLTT — BIOS-programmed threshold defaults (dimm_temp_thresh) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies PECI-based CLTT threshold defaults. BIOS programs `dimm_temp_thresh` with low/mid/high/crit thresholds. Tags: `DMR_PO`, `plc.ti_gate.b0`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### PECI DIMM Threshold Registers

| CSR Field | Default | Description |
|-----------|---------|-------------|
| `dimm_temp_low_maxthreshold [7:0]` | 0x55 (85°C) | Above → throttle at THRT_MID |
| `dimm_temp_mid_maxthreshold [15:8]` | 0x5A (90°C) | Above → throttle at THRT_HIGH |
| `dimm_temp_high_maxthreshold [23:16]` | 0x5F (95°C) | Above → throttle at THRT_CRIT |
| `dimm_temp_high_maxthreshold [31:24]` | TBD | Fourth threshold |

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p mt_basic_checks -tM 60 --retry_count 2
```

### Pass Criteria
- All `dimm_temp_thresh` fields match BIOS-programmed default values for NWP
- `mt_basic_checks.py` PECI threshold check passes

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; PECI threshold defaults may differ for NWP platform — verify against NWP BIOS spec**

**Priority**: High — `plc.feature.p1`; PECI threshold defaults are critical for memory thermal safety at production temperatures
