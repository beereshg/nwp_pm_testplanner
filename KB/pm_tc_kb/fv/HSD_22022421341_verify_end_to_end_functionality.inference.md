# Deep Analysis: [MR4] Verify End-to-End Functionality

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421341 |
| **Title** | [MR4] Verify end to end Functionality |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Memory Thermal Management |
| **Sub-Feature** | MR4-based CLTT end-to-end — BIOS knob, thresholds, throttle, memhot, memtrip |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This is the **comprehensive MR4-based CLTT end-to-end test**: configure BIOS knob → set thresholds → warm DIMM → verify throttle at each band → verify memhot/memtrip assertion at each crossing.

Uses `cltt.py`. Tags: `NGA_MAIN`, `plc.ti_gate.b0`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### MR4 CLTT Registers

| Register | Fields | Description |
|----------|--------|-------------|
| `mr4_temp_thresh[0:1]` | low/mid/high/memtrip/2xrefresh | MR4 temp threshold crossings |
| `thr_ctrl0` | throttle control | Enable throttle per threshold |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Set BIOS knob `thermalthrottlingsupport` = MR4 mode | BIOS knob config |
| 2 | Configure MR4 thresholds: `mr4_temp_thresh[0:1]` | Low/mid/high bands |
| 3 | Run memory traffic workload | Stress memory bandwidth |
| 4 | Warm DIMM to low threshold | Verify throttle at THRT_MID bandwidth |
| 5 | Warm DIMM to mid threshold | Verify throttle at THRT_HIGH bandwidth |
| 6 | Warm DIMM to high threshold | Verify throttle at THRT_CRIT bandwidth |
| 7 | Cross memtrip threshold | Verify MEMHOT output; verify MEMTRIP |
| 8 | Run `cltt.py` | Full automated CLTT verification |

### NWP Command
```bash
cltt.py
# (with NWP python package path)
```

### Pass Criteria
- Each temperature threshold crossing triggers correct throttle level
- MEMHOT output asserts when programmed threshold crossed
- MEMTRIP asserts when memtrip threshold crossed
- `cltt.py` passes for NWP MR4 mode

---

## Section F: Recommendation

**Recommendation: ADOPT — MR4 CLTT end-to-end; `cltt.py` needs NWP package; adapt paths; BIOS knob same name on NWP**

**Priority**: High — `NGA_MAIN`, `plc.feature.p1`; end-to-end MR4 CLTT is the primary memory thermal management validation
