# Deep Analysis: DRAM RAPL ZBB Negative Checks

| Field | Value |
|-------|-------|
| **HSD ID** | [22022060651](https://hsdes.intel.com/appstore/article-one/#/22022060651) |
| **Title** | DRAM RAPL ZBB Negative Checks |
| **Segment** | PSS |
| **Target Program** | NWP (Newport) |
| **Feature** | Power / RAPL — DRAM RAPL |
| **Val Environment** | virtual_platform, emulation |
| **Parent TCD** | [22022060621 — NWP ZBB Negative Validation](https://hsdes.intel.com/appstore/article-one/#/22022060621) |

---

## Test Case Intent

**Objective:** Verify that DRAM RAPL is correctly ZBB'd on NWP. DRAM RAPL (MSRs 0x618-0x61B) provides per-channel DRAM power limits and energy accounting on DMR; it is removed from NWP scope. All DRAM RAPL MSRs must return 0 and writes must be silently dropped. Socket RAPL (MSR 0x610 / TPMI) must remain functional.

**Dual-Environment:** Runs on both VP (Simics) and emulation (HSLE).

### Pre-Conditions

| Pre-Condition | Expected State | Failure Indication |
|---------------|---------------|-------------------|
| Platform booted | NWP system accessible via PythonSV | Environment not booted |
| DRAM RAPL fuse disabled | pcode_dram_rapl_disable=1 | Fuse not set — wrong model config |
| MSR access available | pd.debug.access_to_msr(0x618) does not raise | MSR access not available |
| Socket RAPL TPMI accessible | sv.socket0.nio.punit.tpmi.socket_rapl_pl1_control readable | TPMI not initialized |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Read DRAM RAPL disable fuse: sv.socket0.nio.punit.fuses.punit.pcode_dram_rapl_disable | Returns 1 (DRAM RAPL disabled) | Returns 0 — DRAM RAPL unexpectedly enabled |
| 2 | Read MSR 0x618 (DRAM_POWER_LIMIT): should be 0 | MSR reads 0 | Non-zero — DRAM PL register active |
| 3 | Write non-zero to MSR 0x618 and read back | Readback = 0 (write silently dropped) | Readback reflects written value |
| 4 | Read MSR 0x619 (DRAM_ENERGY_STATUS): should be 0 | MSR reads 0 (no DRAM energy counter) | Non-zero — DRAM energy counter running |
| 5 | Read MSR 0x61A (DRAM_PERF_STATUS): should be 0 | MSR reads 0 | Non-zero — DRAM perf status active |
| 6 | Read MSR 0x61B (DRAM_POWER_INFO): should be 0 | MSR reads 0 | Non-zero — DRAM power info populated |
| 7 | Verify Socket RAPL PL1 TPMI reads valid TDP value | socket_rapl_pl1_control.pwr_lim returns non-zero TDP | Zero — Socket RAPL broken |
| 8 | Verify Socket RAPL ENERGY_STATUS increments under load | Two reads of TPMI socket_rapl_energy_status show increasing value | Stuck at 0 — Socket RAPL energy counting broken |

### Pass / Fail Criteria

**PASS:** DRAM RAPL disable fuse=1; MSRs 0x618-0x61B all read 0; write to 0x618 silently dropped; Socket RAPL TPMI PL1 non-zero; ENERGY_STATUS increments under load.

**FAIL:** Fuse=0 (wrong config); any DRAM RAPL MSR non-zero; write to 0x618 persists; Socket RAPL broken or energy counter stuck.

### Post-Process

Save: DRAM RAPL fuse, MSR 0x618-0x61B readbacks, Socket RAPL TPMI PL1 and ENERGY_STATUS samples, environment type.

### Reference Documents

- [Intel RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html) — DRAM domain MSRs 0x618-0x61B
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — DRAM RAPL ZBB scope
- [DMR RAPL Simplification HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html) — DRAM RAPL removal rationale
- [Socket RAPL KB](../../pm_features/power_rapl/socket_rapl.md)

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

DRAM RAPL is explicitly ZBB'd on NWP. NWP uses a different memory controller architecture that does not expose per-channel DRAM power limits. This negative test confirms ZBB enforcement across both VP and emulation.

Tags: plc.zbb.p1, PMSS_NWP_READINESS_CHECK.

---

## Section B: NWP-Specific Test Procedure

### DRAM RAPL ZBB Key Registers

| Register | MSR / Path | Expected on NWP | Purpose |
|----------|-----------|----------------|---------|
| DRAM RAPL disable fuse | sv.socket0.nio.punit.fuses.punit.pcode_dram_rapl_disable | 1 | ZBB fuse |
| DRAM_POWER_LIMIT | MSR 0x618 (deprecated) | 0 — write dropped | ZBB validation |
| DRAM_ENERGY_STATUS | MSR 0x619 (deprecated) | 0 — counter inactive | ZBB validation |
| DRAM_PERF_STATUS | MSR 0x61A (deprecated) | 0 | ZBB validation |
| DRAM_POWER_INFO | MSR 0x61B (deprecated) | 0 | ZBB validation |
| Socket RAPL PL1 | TPMI socket_rapl_pl1_control.pwr_lim | Non-zero TDP | Positive sanity |
| Socket RAPL ENERGY | TPMI socket_rapl_energy_status | Increments under load | Positive sanity |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Read DRAM fuse | sv.socket0.nio.punit.fuses.punit.pcode_dram_rapl_disable.get_value() |
| 2 | Read MSRs 0x618-0x61B | Via pd.debug.access_to_msr(offset, core=first_core) on first core |
| 3 | Write/readback 0x618 | Write 0xFFFF, read back — expect 0 |
| 4 | Verify Socket RAPL TPMI | Read socket_rapl_pl1_control + socket_rapl_energy_status |

### Pass Criteria

DRAM fuse=1; MSRs 0x618-0x61B return 0; Socket RAPL TPMI valid and energy counter active.
