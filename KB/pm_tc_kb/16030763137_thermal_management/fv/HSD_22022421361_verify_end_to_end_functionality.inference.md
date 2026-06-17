# Deep Analysis: [PECI] Verify End-to-End Functionality

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421361 |
| **Title** | [PECI] Verify end to end functionality |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Memory Thermal Management |
| **Sub-Feature** | PECI-based CLTT end-to-end — BMC writes temp via TPMI → MC throttles at each threshold |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This is the **comprehensive PECI-based CLTT end-to-end test**: set BIOS knob → configure thresholds → BMC writes temperatures progressively → verify throttle at each crossing.

**Note**: test steps have a typo `dmr,xml` (comma instead of period) — NWP command uses `nwp.xml` (correct syntax).

Tags: `NGA_MAIN`, `plc.ti_gate.b0`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### PECI CLTT Threshold Configuration

| CSR Field | Default | Description |
|-----------|---------|-------------|
| `dimm_temp_low_maxthreshold` | 0x55 (85°C) | → THRT_MID |
| `dimm_temp_mid_maxthreshold` | 0x5A (90°C) | → THRT_HIGH |
| `dimm_temp_high_maxthreshold` | 0x5F (95°C) | → THRT_CRIT |
| `dimm_temp_memtrip_threshold` | TBD | → MEMTRIP |
| `dimm_temp_2xrefresh_threshold` | TBD | → 2x DRAM refresh |

### Adapted Command (NWP)
```bash
# Typo in original: "dmr,xml" → correct NWP command:
python runPmx.py -x nwp.xml -p cltt_peci -tM 60 -M 10 --retry_count 2
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Set BIOS knob `thermalthrottlingsupport` = PECI mode | BIOS config |
| 2 | Configure `dimm_temp_thresh[0:1]` | Low/mid/high thresholds |
| 3 | BMC writes temp below all thresholds via TPMI | No throttle |
| 4 | BMC writes temp above low threshold | MC throttles at THRT_MID bandwidth |
| 5 | BMC writes temp above mid threshold | MC throttles at THRT_HIGH bandwidth |
| 6 | BMC writes temp above high threshold | MC throttles at THRT_CRIT bandwidth |
| 7 | BMC writes temp above memtrip threshold | MEMHOT/MEMTRIP asserted |

### Pass Criteria
- Each temperature write → correct throttle level
- THRT_MID, THRT_HIGH, THRT_CRIT bandwidth limits correct
- MEMTRIP asserts at memtrip threshold
- `cltt_peci` PMx script passes for NWP

---

## Section F: Recommendation

**Recommendation: ADOPT — Note typo fix `dmr,xml` → `nwp.xml`; `cltt_peci` PMx plugin needs NWP verification; BMC TPMI interface same**

**Priority**: High — `NGA_MAIN`, `plc.feature.p1`; PECI CLTT end-to-end is the primary data center memory thermal validation path
