# Deep Analysis: Inconsistent Throttling_silicon_I3C

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422363 |
| **Title** | Inconsistent Throttling_silicon_I3C |
| **Date** | 2026-07-19 |
| **Target Program** | NWP (Newport) |
| **Feature** | Telemetry -- PEM (Power and Energy Monitoring) |
| **Sub-Feature** | Inconsistent throttling (gaps) via I3C (BMC OOB) |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Parent TCD** | [22022421014 -- Inconsistent Throttling](https://hsdes.intel.com/appstore/article-one/#/22022421014) |
| **Parent TPF** | [16030767512 -- PEM](https://hsdes.intel.com/appstore/article-one/#/16030767512) |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Tests PEM accuracy with **gaps in throttle events** (5-second gaps between throttle periods). PEM must correctly accumulate only the actual throttle time (not the gaps). Formula: `PEM counter (ms) = total induced throttle time +/- 10%`. Readback via **I3C (BMC OOB)**.

Tags: `Ready_for_testing`, `PMSS_NWP_READINESS_CHECK`.

---

## Test Case Intent

Validates the **Inconsistent Throttling** scenario defined in [TCD 22022421014 -- Inconsistent Throttling](https://hsdes.intel.com/appstore/article-one/#/22022421014), using the **I3C (BMC OOB)** readback interface. Verifies PEM counters accumulate only actual throttle-ON intervals and correctly exclude gap periods. Environment: NWP post-silicon with BMC I3C link.

> **Original HSD flow preserved:** 1. Enable PEM through TPMI. 2. Introduce throttling events with gaps of 5 seconds in between throttling events. 3. Check PEM counters and status output via I3C interface. Configuration: BMC setup, LPF ramp calculation from thermal team. Pass criteria: induced throttle = PEM counter value (ms) with ~10% variance.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon with BMC I3C link |
| BIOS knobs | Default (PEM always active when RAPL enabled) |
| BMC / OOB | BMC I3C link configured and operational |
| Feature state | PEM enabled via TPMI; Socket RAPL PL1/PL2 active |
| Throttle method | PROCHOT injection or RAPL PL1 toggle (cycle: throttle ON N seconds, OFF 5 seconds) |
| Thermal team input | LPF ramp duration (ms) for the platform configuration |
| Tool | PythonSV with NWP namednodes; timer for throttle cycling |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Clear PEM_STATUS: write 0 to all bits via TPMI `sv.socket0.cbb{0,1}.base.tpmi.pem_status` | All PEM_STATUS bits = 0 | PEM_STATUS bits not cleared |
| 2 | Start workload on all cores (e.g., stress-ng or PEGA) | System under load; frequency at turbo | Workload fails |
| 3 | Begin throttle cycling: throttle ON for T_on seconds, then OFF for 5 seconds, repeat N cycles | Throttle cycles as programmed | Throttle not toggling |
| 4 | Record total throttle-ON time: `T_total_throttle = N * T_on` (seconds) | T_total_throttle calculated | Invalid cycle count |
| 5 | After all cycles complete, read PEM counters via **I3C (BMC OOB)**: BMC I3C read of PEM counters | PEM counter value returned (ms) | Interface read failure |
| 6 | Verify: `PEM_counter_ms ~ T_total_throttle * 1000 (+/-10%)` | PEM counter within `T_total_throttle * 900` to `T_total_throttle * 1100` ms | PEM counter deviates > 10% |
| 7 | Verify PEM counter does NOT include gap time | PEM counter < `(T_total_throttle + N*5) * 1000` | PEM counter includes gaps |
| 8 | Read PEM_STATUS bits | Expected excursion bit set; ANY bit set | PEM_STATUS bits not set |
| 9 | Remove workload and throttle | System returns to idle | System remains throttled |

---

### Pass / Fail Criteria

**Bar:** Per [TCD 22022421014](https://hsdes.intel.com/appstore/article-one/#/22022421014): PEM counters must capture only active throttle time (excluding gaps) within +/-10%.

- **PASS**: `PEM counter = total throttle-ON time +/- 10%` AND gap time NOT counted AND correct PEM_STATUS bits set AND I3C readback returns valid data
- **FAIL**: PEM counter includes gap time OR deviates > 10% from actual throttle-ON time OR PEM_STATUS bits not set OR I3C readback fails

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| PEM_STATUS | `sv.socket0.cbb{0,1}.base.tpmi.pem_status` | Expected excursion bits set during throttle-ON |
| PERF_STATUS | `sv.socket0.nio.punit.tpmi.socket_rapl.perf_status` | Throttle counter reflects throttle-ON intervals only |
| MCA status | `sv.socket0.cbb{0,1}.base.ubox.mca_err_src_log` | No MCA errors |

---

### Post-Process

Record PEM counter value, T_total_throttle, number of cycles, and gap duration for regression tracking.

---

### References

- [TCD 22022421014 -- Inconsistent Throttling](https://hsdes.intel.com/appstore/article-one/#/22022421014)
- [TPF 16030767512 -- PEM](https://hsdes.intel.com/appstore/article-one/#/16030767512)
- [DMR PM HAS -- PEM Section](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PEM.html)
