# Deep Analysis: Platform Limit Reason Check

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422383 |
| **Title** | Platform Limit Reason Check |
| **Date** | 2026-07-19 |
| **Target Program** | NWP (Newport) |
| **Feature** | Telemetry -- PLR (Performance Limit Reasons) |
| **Sub-Feature** | PLR coarse/fine grain reason bit verification via TPMI + mailbox |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Parent TCD** | [22022421017 -- Performance Limit Reason](https://hsdes.intel.com/appstore/article-one/#/22022421017) |
| **Parent TPF** | [16030767513 -- PLR](https://hsdes.intel.com/appstore/article-one/#/16030767513) |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

PLR is PCode infrastructure that runs in the slow loop context (every 1 ms). On NWP, PLR uses TPMI interface (MSR/PCS deprecated). Two granularity levels: Coarse Grain (aggregated -- thermal, power, platform) and Fine Grain (per-domain -- specific flow or event). PLR_DIE_LEVEL and PLR_MAILBOX are the main interfaces. Log bits use RW0C semantics (write 0 to clear, write 1 ignored).

Tags: `Ready_for_testing`, `PMSS_NWP_READINESS_CHECK`.

---

## Test Case Intent

Validates the **PLR (Performance Limit Reason)** mechanism defined in [TCD 22022421017 -- Performance Limit Reason](https://hsdes.intel.com/appstore/article-one/#/22022421017). Verifies that PLR correctly reports coarse-grain and fine-grain throttle reasons when performance-limiting conditions are induced (PROCHOT, RAPL, thermal, ICCMAX), and that log bits can be cleared via RW0C semantics. Environment: NWP post-silicon with PythonSV access.

> **Original HSD flow preserved:** PLR runs in slow loop (1 ms). Collects reasons from Slow Limits, Fast Limits/WP4, TRL. Reports via TPMI. Steps: 1. Initial state -- all PLR bits clear. 2. Induce limit conditions (PROCHOT, EMTTM). 3. Read PLR via mailbox. 4. Clear and verify. 5. ITD offset check. Scripts: `runPmx.py -p turbo`, `-p cpu_rapl`, `-p platform_rapl`, `-p emtt_thermal`, `-p prochot_thermal`.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon with PythonSV access |
| BIOS knobs | Default (PLR always active) |
| Feature state | PLR enabled; Socket RAPL PL1/PL2 active |
| Throttle injection | Ability to assert PROCHOT_N, lower RAPL PL1, inject thermal limit |
| Tool | PythonSV with NWP namednodes; `runPmx.py` (adapted to `nwp.xml`) |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Start workload on all cores | System at turbo frequency | Workload fails |
| 2 | Read PLR_DIE_LEVEL via TPMI: `sv.socket0.cbb{0,1}.base.tpmi.perf_limit_reasons.show()` | All coarse/fine PLR bits = 0 (no active limiters) | PLR bits unexpectedly set at baseline |
| 3 | Read PLR via mailbox: issue read to PLR_MAILBOX_INTERFACE, read PLR_MAILBOX_DATA | Mailbox returns valid response; coarse + fine bits = 0 | Mailbox RUN_BUSY timeout or error |
| 4 | **Induce RAPL PL1 throttle**: set PL1 below current power via TPMI | Frequency drops; RAPL PL1 throttle active | No throttle observed |
| 5 | Read PLR_DIE_LEVEL coarse: verify POWER bit (2) set | PLR coarse bit 2 = 1 | POWER bit not set |
| 6 | Read PLR_DIE_LEVEL fine: verify PL1 bit (32) set | PLR fine bit 32 = 1 | PL1 fine bit not set |
| 7 | Remove RAPL PL1 throttle (restore PL1 to TDP) | Throttle ceases | System remains throttled |
| 8 | Verify PLR_DIE_LEVEL: POWER bit still set (log bit -- persists until cleared) | Coarse bit 2 = 1 (sticky) | Bit auto-cleared (RW0C violation) |
| 9 | Clear PLR bits: write 0 to PLR_DIE_LEVEL via TPMI | All bits cleared | Bits not cleared |
| 10 | **Induce thermal throttle**: assert PROCHOT_N or force TCC limit | Frequency drops; thermal throttle active | No throttle |
| 11 | Read PLR_DIE_LEVEL coarse: verify THERMAL bit (3) set | PLR coarse bit 3 = 1 | THERMAL bit not set |
| 12 | Read PLR_DIE_LEVEL coarse: verify PLATFORM bit (4) set (if PROCHOT used) | PLR coarse bit 4 = 1 | PLATFORM bit not set |
| 13 | Remove thermal throttle (deassert PROCHOT) | Throttle ceases | System remains throttled |
| 14 | **Induce multiple simultaneous limiters**: set PL1 low + assert PROCHOT | Both POWER (2) and PLATFORM (4) coarse bits set | Only one bit set |
| 15 | Clear all PLR bits; verify cleared | All bits = 0 | Bits persist after clear |
| 16 | Read PLR via MSR 0x19C per-core (iterate both CBBs): `pd.debug.access_to_msr(0x19C, core=N)` for N across active cores | Per-core MSR returns consistent limit status | MSR read error or inconsistency |
| 17 | Compare TPMI PLR and MSR 0x19C: POWER_LIMITATION_STATUS (bit 11 of 0x19C) aligns with PLR POWER bit | Consistent across interfaces | Cross-interface mismatch |

---

### Pass / Fail Criteria

**Bar:** Per [TCD 22022421017](https://hsdes.intel.com/appstore/article-one/#/22022421017): PLR coarse and fine grain bits correctly identify the active limiter; log bits persist until cleared via RW0C; multiple simultaneous limiters result in multiple bits set.

- **PASS**: All of:
  - RAPL PL1 throttle sets POWER coarse (bit 2) + PL1 fine (bit 32)
  - Thermal/PROCHOT throttle sets THERMAL (bit 3) + PLATFORM (bit 4) as applicable
  - Multiple simultaneous limiters set all applicable bits
  - Log bits persist until RW0C clear
  - PLR_MAILBOX returns valid coarse + fine data
  - MSR 0x19C per-core aligns with TPMI PLR
- **FAIL**: Any PLR bit not set for active limiter OR log bit auto-clears OR mailbox error OR MSR/TPMI mismatch

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| PLR_DIE_LEVEL | `sv.socket0.cbb{0,1}.base.tpmi.perf_limit_reasons` | Correct bits set per active limiter |
| PERF_STATUS | `sv.socket0.nio.punit.tpmi.socket_rapl.perf_status` | Throttle counter incrementing during limit |
| MSR 0x19C | `pd.debug.access_to_msr(0x19C, core=0)` | Power/current/cross-domain limit bits consistent with TPMI |
| MCA status | `sv.socket0.cbb{0,1}.base.ubox.mca_err_src_log` | No MCA errors |

---

### Post-Process

Capture PLR_DIE_LEVEL and PLR_MAILBOX_DATA dumps for both CBBs after each throttle scenario. Archive for regression tracking.

---

### References

- [TCD 22022421017 -- Performance Limit Reason](https://hsdes.intel.com/appstore/article-one/#/22022421017)
- [TPF 16030767513 -- PLR](https://hsdes.intel.com/appstore/article-one/#/16030767513)
- [DMR PM HAS -- PLR Section](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PLR.html)
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [TCD 16031169448 -- Socket RAPL Reporting / Observability](https://hsdes.intel.com/appstore/article-one/#/16031169448) -- PLR priority ordering
- [Original HSD scripts: runPmx.py -p turbo, -p cpu_rapl, -p platform_rapl, -p emtt_thermal, -p prochot_thermal]
