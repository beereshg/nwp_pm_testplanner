# Deep Analysis: RAPL Perf Status

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422038 |
| **Title** | RAPL Perf status |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | RAPL perf status counter — increments when throttled below PL1/PL2/Fast RAPL |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **RAPL Perf Status counter** increments whenever the system is throttled below PL1, PL2, or Fast RAPL limits. Registers (directly NWP paths):
- CSR: `@sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_rapl_perf_status`
- TPMI: `@sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_perf_status`

Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP RAPL Perf Status Registers

| Register | NWP Path |
|----------|----------|
| CSR perf status | `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_rapl_perf_status` |
| TPMI perf status | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_perf_status` |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run cpu_rapl PMx | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| 2 | Read RAPL perf status at idle (no throttle) | Baseline counter value |
| 3 | Set PL1 below current power (trigger PL1 throttle) | Counter should increment |
| 4 | Read RAPL perf status under PL1 throttle | Counter > baseline |
| 5 | Trigger PL2 throttle | Counter increments during PL2 excursion |
| 6 | Trigger Fast RAPL | Counter increments during Fast RAPL |
| 7 | Restore PL1 to TDP (no throttle) | Counter stops incrementing |
| 8 | Verify CSR and TPMI counters agree | Both should show same count |

### Perf Status Counter Behavior

```python
# NWP RAPL perf status verification
csr_ps = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_rapl_perf_status
tpmi_ps = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_perf_status

baseline_csr = csr_ps.read()
# Trigger RAPL throttle (set low PL1)
import time; time.sleep(1)
throttled_csr = csr_ps.read()
assert throttled_csr > baseline_csr, "Perf status should increment during RAPL throttle"
assert csr_ps.read() == tpmi_ps.read(), "CSR and TPMI should agree"
```

### Pass Criteria
- RAPL perf status counter increments during PL1/PL2/Fast RAPL throttle
- Counter does NOT increment at idle (no throttle)
- CSR and TPMI perf status registers agree (same value)
- Counter does not overflow or wrap unexpectedly

---

## Section F: Recommendation

**Recommendation: ADOPT — Register paths already show NWP `imh0`; verify counter on both CSR and TPMI**

1. `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3`
2. Verify `package_rapl_perf_status` (CSR) and `socket_rapl_perf_status` (TPMI) increment under throttle
3. Confirm CSR and TPMI agree; counter stops when throttle cleared

**Priority**: High — `plc.feature.p2`; RAPL perf status is the primary OS-visible throttle counter — used by Linux/Windows power management monitoring
