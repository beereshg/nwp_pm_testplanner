# Deep Analysis: Platform RAPL / PSYS ZBB Negative Checks

| Field | Value |
|-------|-------|
| **HSD ID** | [22022060649](https://hsdes.intel.com/appstore/article-one/#/22022060649) |
| **Title** | Platform RAPL / PSYS ZBB Negative Checks |
| **Segment** | PSS |
| **Target Program** | NWP (Newport) |
| **Feature** | Power / RAPL — Platform RAPL (PSYS) |
| **Val Environment** | virtual_platform, emulation |
| **Parent TCD** | [22022060621 — NWP ZBB Negative Validation](https://hsdes.intel.com/appstore/article-one/#/22022060621) |

---

## Test Case Intent

**Objective:** Verify that Platform RAPL (PSYS — platform-level power limit and energy accounting) is correctly ZBB'd (zero-bug baseline disabled) on NWP. The PSYS domain is not present in NWP silicon; all related MSRs must return 0 and writes must be silently dropped. Socket RAPL shall remain fully functional.

**Dual-Environment:** Runs on both VP (Simics — boot-time fuse model) and emulation (HSLE — runtime hardware model accuracy).

### Pre-Conditions

| Pre-Condition | Expected State | Failure Indication |
|---------------|---------------|-------------------|
| Platform booted | NWP system accessible via PythonSV | Environment not booted |
| PSYS fuse disabled | pcode_psys_enable=0 on NIO/IMH | PSYS fuse set — wrong SKU or model config |
| MSR access available | pd.debug.access_to_msr(0x65C) does not raise | MSR access layer not loaded |
| Socket RAPL TPMI accessible | sv.socket0.nio.punit.tpmi readable | TPMI not initialized |
| VP/Emulation environment identified | a.getaccess() returns simics or hsle | Unknown environment type |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Read PSYS fuse: sv.socket0.nio.punit.fuses.punit.pcode_psys_enable | Returns 0 (PSYS disabled) | Returns 1 — PSYS unexpectedly enabled |
| 2 | Read MSR 0x65C (PLATFORM_POWER_LIMIT): should be 0 on NWP | MSR reads 0x0000000000000000 | Non-zero — PSYS PL register active |
| 3 | Write a non-zero value to MSR 0x65C and read back | Readback still = 0 (write silently dropped) | Readback reflects written value — PSYS write not blocked |
| 4 | Read MSR 0x64C (PLATFORM_ENERGY_STATUS): should be 0 | MSR reads 0 (no platform energy counter) | Non-zero — PSYS energy counter active |
| 5 | Read MSR 0x64D (PLATFORM_POWER_INFO): should be 0 | MSR reads 0 | Non-zero — PSYS power info populated |
| 6 | Verify Socket RAPL PL1 still readable via TPMI | sv.socket0.nio.punit.tpmi.socket_rapl_pl1_control.read() returns non-zero TDP | Zero or exception — Socket RAPL broken by ZBB config |
| 7 | On emulation only: run sustained workload; verify no PSYS throttle event | No PSYS throttle bit in PERF_STATUS; Socket RAPL throttles normally | PSYS throttle bit set — PSYS engaged unexpectedly |

### Pass / Fail Criteria

**PASS:** PSYS fuse=0; MSRs 0x65C/0x64C/0x64D read 0; write to 0x65C silently dropped; Socket RAPL TPMI accessible and returns valid TDP value; no PSYS throttle event.

**FAIL:** PSYS fuse=1 (wrong model config); any PSYS MSR returns non-zero; write to 0x65C persists; Socket RAPL broken; PSYS throttle event fired.

### Post-Process

Save: PSYS fuse value, MSR 0x65C/0x64C/0x64D readback, Socket RAPL TPMI PL1 value, workload PERF_STATUS snapshot (emulation), environment type (VP vs emulation).

### Reference Documents

- [Intel RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html) — PSYS domain definition, MSR 0x65C/0x64C/0x64D
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — PSYS ZBB scope, RAPL TPMI paths
- [DMR RAPL Simplification HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html) — PSYS removal rationale
- [Socket RAPL KB — socket_rapl.md](../../pm_features/power_rapl/socket_rapl.md)

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Platform RAPL (PSYS) is explicitly ZBB'd on NWP. The PSYS domain was present in DMR/GNR but removed from NWP silicon scope. This negative test validates the ZBB is correctly enforced in firmware, model, and hardware. Must run on both VP and emulation.

Tags: plc.zbb.p1, PMSS_NWP_READINESS_CHECK.

---

## Section B: NWP-Specific Test Procedure

### PSYS ZBB Key Registers

| Register | Path | Expected on NWP | Purpose |
|----------|------|----------------|---------|
| PSYS fuse | sv.socket0.nio.punit.fuses.punit.pcode_psys_enable | 0 | PSYS disabled |
| PLATFORM_POWER_LIMIT | MSR 0x65C (deprecated) | 0 — write silently dropped | Validate ZBB |
| PLATFORM_ENERGY_STATUS | MSR 0x64C (deprecated) | 0 — no energy counter | Validate ZBB |
| PLATFORM_POWER_INFO | MSR 0x64D (deprecated) | 0 | Validate ZBB |
| Socket RAPL PL1 | TPMI socket_rapl_pl1_control | Non-zero TDP (positive sanity) | Socket RAPL still works |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Read PSYS fuse | sv.socket0.nio.punit.fuses.punit.pcode_psys_enable.get_value() |
| 2 | Read MSR 0x65C | pd.debug.access_to_msr(0x65C, core=first_core) |
| 3 | Write/readback MSR 0x65C | Write 0xFFFF, read back — expect 0 |
| 4 | Verify Socket RAPL TPMI | sv.socket0.nio.punit.tpmi.socket_rapl_pl1_control.read() |
| 5 | Emulation: workload + PERF_STATUS | Check no PSYS throttle bit in TPMI PERF_STATUS |

### Pass Criteria

PSYS fuse=0; MSRs 0x65C/0x64C/0x64D return 0; Socket RAPL TPMI valid.
