# Deep Analysis: [MR4] Verify DIMM Throttle Levels Values Match Default

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421334 |
| **Title** | [MR4] Verify DIMM throttle levels values match with default values |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Memory Thermal Management |
| **Sub-Feature** | MR4 CLTT — DIMM throttle level defaults (THRT_LO/MID/HIGH/CRIT) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies DIMM throttle level register defaults for MR4-based CLTT. Throttle levels control max DRAM transactions allowed per thermal band.

Tags: `DMR_PO`, `plc.ti_gate.b0`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### DIMM Throttle Level Register

| CSR Field | Default | Description |
|-----------|---------|-------------|
| `dimm_throttle_therm_low_level [7:0]` | 0x0FF | Max transactions in THRT_LO region |
| `dimm_throttle_therm_mid_level [15:8]` | TBD | Max transactions in THRT_MID region |
| `dimm_throttle_therm_high_level [23:16]` | TBD | Max transactions in THRT_HIGH region |
| `dimm_throttle_therm_crit_level [31:24]` | TBD | Max transactions in THRT_CRIT region |

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p mt_basic_checks -tM 60 --retry_count 2
```

### Pass Criteria
- `dimm_therm_thr_lvl` fields match BIOS-programmed defaults
- `mt_basic_checks.py` DIMM throttle level check passes

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; DIMM throttle level register architecture same on NWP**

**Priority**: Medium — `plc.feature.p1`; throttle levels must match spec defaults to ensure correct thermal bandwidth reduction
