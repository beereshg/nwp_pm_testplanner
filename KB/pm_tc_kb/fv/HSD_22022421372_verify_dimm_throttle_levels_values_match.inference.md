# Deep Analysis: [PECI] Verify DIMM Throttle Levels Values Match Default

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421372 |
| **Title** | [PECI] Verify DIMM throttle levels values match with default values |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Memory Thermal Management |
| **Sub-Feature** | PECI CLTT — DIMM throttle level defaults (same registers as MR4) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies DIMM throttle level register defaults for PECI-based CLTT — same `dimm_therm_thr_lvl` register as MR4 mode (TC 22022421334), but tested in PECI CLTT mode.

Tags: `DMR_PO`, `plc.ti_gate.b0`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Throttle Level Defaults (same register, PECI mode)

| CSR Field | Default | Description |
|-----------|---------|-------------|
| `dimm_throttle_therm_low_level [7:0]` | 0x0FF | Max transactions at THRT_LO |
| `dimm_throttle_therm_mid_level [15:8]` | TBD | Max transactions at THRT_MID |
| `dimm_throttle_therm_high_level [23:16]` | TBD | Max transactions at THRT_HIGH |
| `dimm_throttle_therm_crit_level [31:24]` | TBD | Max transactions at THRT_CRIT |

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p mt_basic_checks -tM 60 --retry_count 2
```

### Pass Criteria
- `dimm_therm_thr_lvl` fields match defaults in PECI CLTT mode
- Defaults same as MR4 mode (shared register)

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; same `dimm_therm_thr_lvl` register as MR4 TC; verify in PECI mode context**

**Priority**: Medium — `plc.feature.p1`; PECI mode throttle level defaults same importance as MR4 mode
