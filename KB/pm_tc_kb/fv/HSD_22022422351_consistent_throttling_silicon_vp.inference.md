# Deep Analysis: Consistent throttling_silicon_vp

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422351 |
| **Title** | Consistent throttling_silicon_vp |
| **Date** | 2026-07-19 |
| **Target Program** | NWP (Newport) |
| **Feature** | Telemetry -- PEM (Power and Energy Monitoring) |
| **Sub-Feature** | Consistent throttling via Virtual Platform (Simics) |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Parent TCD** | [22022421010 -- Consistent Throttling](https://hsdes.intel.com/appstore/article-one/#/22022421010) |
| **Parent TPF** | [16030767512 -- PEM](https://hsdes.intel.com/appstore/article-one/#/16030767512) |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

PEM consistent throttling validates that 1 minute of continuous, uninterrupted throttle is accurately captured by PEM counters read via the **Virtual Platform (Simics)** interface. PEM is functional on NWP. Test formula: `Total time = LPF ramp + PEM counter captured time ~ 1 minute`.

Tags: `Ready_for_testing`, `PMSS_NWP_READINESS_CHECK`.

---

## Test Case Intent

Validates the **Consistent Throttling** scenario defined in [TCD 22022421010 -- Consistent Throttling](https://hsdes.intel.com/appstore/article-one/#/22022421010), using the **Virtual Platform (Simics)** readback interface. Verifies that PEM counters accurately capture total throttle duration (LPF ramp + sustained throttle ~ 60 s) when throttle is continuous (no gaps). Environment: NWP Simics VP (PSS environment).

> **Original HSD flow preserved:** 1. Enable PEM through TPMI. 2. Enforce throttling for 1 minute contiguously without gaps. 3. Check respective counters for total time of throttling via VP interface. Configuration: BMC setup, LPF ramp calculation from thermal team.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP Simics VP (PSS environment) |
| BIOS knobs | Default (PEM always active when RAPL enabled) |
| BMC / OOB | N/A (VP model) |
| Feature state | PEM enabled via TPMI; Socket RAPL PL1/PL2 active |
| Throttle method | PROCHOT injection or RAPL PL1 set below active power level |
| Thermal team input | LPF ramp duration (ms) for the platform configuration |
| Tool | PythonSV with NWP namednodes; `telemetryAPIs.py` (if available) |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Clear PEM_STATUS: write 0 to all bits via TPMI `sv.socket0.cbb{0,1}.base.tpmi.pem_status` | All PEM_STATUS bits = 0 | PEM_STATUS bits not cleared (RW0C failure) |
| 2 | Record LPF ramp duration from thermal team (T_lpf_ms) | LPF ramp value obtained | Missing LPF ramp data |
| 3 | Start continuous workload on all cores (e.g., stress-ng or PEGA) | System under load; frequency at turbo | Workload fails to start |
| 4 | Induce sustained throttle: set RAPL PL1 below current power (or assert PROCHOT_N) | Throttle begins; PEM_STATUS PL1 or PLATFORM bit set | No throttle detected |
| 5 | Maintain throttle continuously for 60 seconds (no gaps) | Throttle sustained without interruption | Throttle gaps detected |
| 6 | Read PEM counters via **Virtual Platform (Simics)**: PythonSV TPMI model read in VP | PEM counter value returned | Interface read failure |
| 7 | Calculate: `PEM_time = PEM_counter_value (ms)` | PEM_time value obtained | Counter reads 0 or invalid |
| 8 | Verify: `T_lpf_ms + PEM_time ~ 60000 ms (±10%)` | Total within 54000–66000 ms | Total outside ±10% of 60 s |
| 9 | Read PEM_STATUS bits | PL1 or PLATFORM bit set (depending on throttle method); ANY bit set | Expected PEM_STATUS bits not set |
| 10 | Remove throttle (restore PL1 or deassert PROCHOT) | Throttle ceases; frequency returns to turbo | System remains throttled |

---

### Pass / Fail Criteria

**Bar:** Per [TCD 22022421010](https://hsdes.intel.com/appstore/article-one/#/22022421010): PEM counters must capture total consistent throttle duration within ±10% of actual throttle time.

- **PASS**: `LPF ramp + PEM counter = 60 s ± 10%` AND correct PEM_STATUS bits set AND VP interface returns valid PEM data
- **FAIL**: PEM counter total deviates > 10% from 60 s OR PEM_STATUS bits not set for active limiter OR VP readback path returns no data / error

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| PEM_STATUS | `sv.socket0.cbb{0,1}.base.tpmi.pem_status` | Expected excursion bits set during throttle |
| PERF_STATUS | `sv.socket0.nio.punit.tpmi.socket_rapl.perf_status` | Throttle counter incrementing during throttle |
| MCA status | `sv.socket0.cbb{0,1}.base.ubox.mca_err_src_log` | No MCA errors during test |
| dmesg | `dmesg \| grep -i 'mce\|error'` | No machine check or fatal errors |

---

### Post-Process

Capture PEM_STATUS register dump for both CBBs after throttle period. Archive for regression comparison.

---

### References

- [TCD 22022421010 -- Consistent Throttling](https://hsdes.intel.com/appstore/article-one/#/22022421010)
- [TPF 16030767512 -- PEM](https://hsdes.intel.com/appstore/article-one/#/16030767512)
- [DMR PM HAS -- PEM Section](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PEM.html)
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
