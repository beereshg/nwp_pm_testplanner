# Deep Analysis: Corelating timings_silicon_TPMI

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422358 |
| **Title** | Corelating timings_silicon_TPMI |
| **Date** | 2026-07-19 |
| **Target Program** | NWP (Newport) |
| **Feature** | Telemetry -- PEM (Power and Energy Monitoring) |
| **Sub-Feature** | Correlating timings -- PEM_STATUS bit set latency via TPMI (in-band MMIO) |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Parent TCD** | [22022421012 -- Corelating timings](https://hsdes.intel.com/appstore/article-one/#/22022421012) |
| **Parent TPF** | [16030767512 -- PEM](https://hsdes.intel.com/appstore/article-one/#/16030767512) |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that after introducing a throttle event, the **time taken to set PEM_STATUS bit** matches the configured TW (Time Window / EWMA window) setting within +/-10% tolerance, measured via the **TPMI (in-band MMIO)** interface. Tests PEM event response latency accuracy.

Tags: `Ready_for_testing`, `PMSS_NWP_READINESS_CHECK`.

---

## Test Case Intent

Validates the **Correlating Timings** scenario defined in [TCD 22022421012 -- Corelating timings](https://hsdes.intel.com/appstore/article-one/#/22022421012), using the **TPMI (in-band MMIO)** readback interface. Verifies PEM_STATUS bit set latency matches the TW (Time Window) setting. Environment: NWP post-silicon with PythonSV access.

> **Original HSD flow preserved:** 1. Enable PEM through TPMI. 2. Introduce throttling event. 3. Check time taken to set respective bit in PEM_STATUS via TPMI interface -- should be ~ TW setting. Configuration: BMC setup, LPF ramp calculation from thermal team.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon with PythonSV access |
| BIOS knobs | Default (PEM always active when RAPL enabled) |
| BMC / OOB | N/A (in-band) |
| Feature state | PEM enabled via TPMI; TW (Time Window) setting configured to known value |
| Throttle method | PROCHOT injection or RAPL PL1 set below active power level |
| Thermal team input | LPF ramp duration and TW setting for the platform configuration |
| Tool | PythonSV with NWP namednodes; high-resolution timer for latency measurement |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Clear PEM_STATUS: write 0 to all bits via TPMI `sv.socket0.cbb{0,1}.base.tpmi.pem_status` | All PEM_STATUS bits = 0 | PEM_STATUS bits not cleared |
| 2 | Record TW (Time Window) setting from PEM configuration registers | TW value obtained (e.g., 100 ms, 500 ms) | TW not configured |
| 3 | Start workload on cores (e.g., stress-ng or PEGA) | System under load | Workload fails |
| 4 | Record timestamp T0; induce throttle event (assert PROCHOT or lower PL1) | Throttle event initiated at T0 | Throttle not applied |
| 5 | Poll PEM_STATUS via **TPMI (in-band MMIO)**: `sv.socket0.cbb{0,1}.base.tpmi.pem_status.show()` | PEM_STATUS excursion bit transitions from 0 to 1 | Bit never set |
| 6 | Record timestamp T1 when PEM_STATUS bit first set | T1 captured | Timeout waiting for bit |
| 7 | Calculate latency: `T_set = T1 - T0` | T_set value obtained | Invalid timestamps |
| 8 | Verify: `T_set ~ TW_setting (+/-10%)` | T_set within `TW * 0.9` to `TW * 1.1` | T_set outside +/-10% of TW |
| 9 | Remove throttle (restore PL1 or deassert PROCHOT) | Throttle ceases | System remains throttled |

---

### Pass / Fail Criteria

**Bar:** Per [TCD 22022421012](https://hsdes.intel.com/appstore/article-one/#/22022421012): PEM_STATUS bit set latency must match the TW (Time Window) setting within +/-10%.

- **PASS**: `T_set = TW_setting +/- 10%` AND PEM_STATUS bit correctly identifies the excursion source AND TPMI interface returns valid data
- **FAIL**: T_set deviates > 10% from TW_setting OR PEM_STATUS bit not set after throttle OR TPMI readback fails

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| PEM_STATUS | `sv.socket0.cbb{0,1}.base.tpmi.pem_status` | Expected excursion bit set after TW |
| PERF_STATUS | `sv.socket0.nio.punit.tpmi.socket_rapl.perf_status` | Throttle counter incrementing |
| MCA status | `sv.socket0.cbb{0,1}.base.ubox.mca_err_src_log` | No MCA errors |

---

### Post-Process

Record T_set latency and TW setting for regression tracking. Capture PEM_STATUS register dump at T1.

---

### References

- [TCD 22022421012 -- Corelating timings](https://hsdes.intel.com/appstore/article-one/#/22022421012)
- [TPF 16030767512 -- PEM](https://hsdes.intel.com/appstore/article-one/#/16030767512)
- [DMR PM HAS -- PEM Section](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PEM.html)
