# TC Description: RAPL Energy Status Reporting

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422023](https://hsdes.intel.com/appstore/article-one/#/22022422023) |
| **Title** | RAPL Energy status reporting |
| **Date** | 2026-07-18 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | ENERGY_STATUS counter — monotonicity, encoding, fuzzing |
| **Parent TCD** | [22022420821 -- Socket RAPL Registers Verification - CSR and TPMI](https://hsdes.intel.com/appstore/article-one/#/22022420821) |
| **Owner** | mps |
| **Status** | open / ready_for_content_review |
| **Priority** | 2-high |
| **Tags** | `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK` |
| **Val Environment** | silicon, virtual_platform |
| **Val Framework** | os-svos, python-sv |
| **Automation** | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Cache version** | 3 |

---

## Test Case Intent

Validates the **Energy Counter Interface** scenario defined in [TCD 22022420821 -- Socket RAPL Registers Verification](https://hsdes.intel.com/appstore/article-one/#/22022420821) §5-A: "ENERGY_STATUS counter is monotonic; 0.0625 J/LSB encoding; TIME field 10 ns units; energy fuzzing via MSR 0xBC.bit0." The TPMI ENERGY_STATUS register is the primary energy accumulation counter used by OS power management. This TC verifies the counter increments monotonically, computes average power accurately using the HAS formula (avg_power_W = (E2-E1) / 2^energy_unit / delta_time_s), and validates the fuzzing behavior via MSR 0xBC (ENERGY_FILTERING_ENABLE). CSR and TPMI energy counters must agree.

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon system or VP (Simics) |
| OS / Driver | SVOS with PythonSV environment; ptu available for workload |
| BIOS | Default RAPL settings; PL1 = TDP |
| Starting state | System booted; PrimeCode PH6 init complete; RAPL active |
| TPMI energy path | sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_energy_status |
| CSR energy path | sv.socket0.nio.punit.ptpcioregs.ptpcioregs.package_energy_status_cfg |
| Power unit path | sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_power_unit |
| Energy encoding | ENERGY [31:0] at 0.0625 J/LSB (energy_unit from power_unit bits [12:8]); TIME [63:32] at 10 ns |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Read TPMI socket_rapl_power_unit. Extract energy_unit field [12:8]. Verify encoding = 4 (0.0625 J/LSB = 1/2^4). | energy_unit = 4; 1 LSB = 0.0625 J. | energy_unit wrong — all power calculations will be incorrect. |
| 2 | Read TPMI socket_rapl_energy_status at idle. Record ENERGY [31:0] as E1 and TIME [63:32] as T1. Wait 1 second. Read again as E2, T2. | E2 > E1 (counter monotonically increasing). T2 > T1 (time field progressing in 10 ns units). | E2 <= E1 (counter stale or regressing). |
| 3 | Compute idle power: avg_power_W = (E2 - E1) / 2^energy_unit / ((T2 - T1) * 10e-9). Compare to expected idle power for NWP platform. | Computed power within +/-15% of expected idle power (platform-dependent, typically 50-150W). | Computed power wildly off or negative. |
| 4 | Read CSR package_energy_status_cfg. Compare ENERGY field to TPMI ENERGY_STATUS ENERGY field. | CSR and TPMI energy values agree (within 1-2 LSB due to read timing). | CSR/TPMI mismatch exceeds tolerance. |
| 5 | Start sustained all-core workload (ptu -ct 1). Wait 5 seconds for power stabilization. | Power draw approaches TDP; cores running at throttled or P1 frequency. | Workload fails to start. |
| 6 | Read ENERGY_STATUS E3, T3. Wait 1 second. Read E4, T4. Compute workload power. | Workload power within +/-10% of expected TDP. Significantly higher than idle power from step 3. | Workload power does not approach TDP or is same as idle. |
| 7 | Verify monotonicity: take 5 rapid reads of ENERGY_STATUS. Verify each subsequent read >= previous. | All 5 reads show ENERGY monotonically non-decreasing. | Any read shows ENERGY < previous (counter regression). |
| 8 | Test energy fuzzing: read MSR 0xBC (IA32_MISC_PACKAGE_CTLS). Set bit 0 (ENERGY_FILTERING_ENABLE = 1). Read ENERGY_STATUS multiple times. | MSR 0xBC writable (not deprecated). With fuzzing enabled, ENERGY_STATUS values may show noise/jitter — per spec, values are fuzzed to prevent energy side-channel attacks. | MSR 0xBC write fails (#GP) or no observable change in ENERGY_STATUS behavior. |
| 9 | Disable fuzzing: clear MSR 0xBC bit 0. Verify ENERGY_STATUS returns to clean monotonic behavior. | ENERGY_STATUS resumes clean monotonic increments without fuzzing artifacts. | Counter behavior unchanged after fuzzing toggle. |
| 10 | Stop workload. Restore original state. Verify no MCA or hang. | Test exits cleanly. | System instability. |

### Pass / Fail Criteria

- **PASS**: Per TCD 22022420821 §5-A — ENERGY_STATUS counter monotonically increasing at idle and under load. Energy unit encoding correct (0.0625 J/LSB). Computed power matches expected idle and workload values within tolerance. CSR and TPMI energy counters agree. TIME field progresses in 10 ns units. MSR 0xBC fuzzing toggle works as specified. No MCA or hang.
- **FAIL**: Counter stale, regressing, or not monotonic. Computed power wildly off. CSR/TPMI mismatch. TIME field stale. MSR 0xBC not writable or fuzzing has no effect. System instability.

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| TPMI ENERGY_STATUS | sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_energy_status | Monotonic; ENERGY [31:0] incrementing; TIME [63:32] progressing |
| CSR package_energy_status_cfg | sv.socket0.nio.punit.ptpcioregs.ptpcioregs.package_energy_status_cfg | Matches TPMI energy value |
| TPMI socket_rapl_power_unit | sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_power_unit | energy_unit = 4 |
| MSR 0xBC | rdmsr/wrmsr 0xBC | Writable; bit 0 toggles fuzzing |

### Post-Process

N/A

### References

- [TCD 22022420821 -- Socket RAPL Registers Verification](https://hsdes.intel.com/appstore/article-one/#/22022420821)
- [Wave 3 Common HAS -- Socket RAPL](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html)
- [DMR RAPL Simplification](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm%20features/dmr_rapl_simplification.html)

---

## Section A: NWP Delta

NIO replaces IMH. Energy encoding and MSR 0xBC behavior unchanged from DMR.

| Aspect | DMR | NWP |
|--------|-----|-----|
| TPMI energy_status | sv.socket0.imh0.punit.ptpcfsms... | sv.socket0.nio.punit.ptpcfsms... |
| CSR energy_status | sv.socket0.imh0.punit.ptpcioregs... | sv.socket0.nio.punit.ptpcioregs... |

## Section F: Recommendations

Recommendation: ADOPT — imh0 -> nio paths; verify monotonicity and fuzzing. Priority: High — energy reporting is the primary OS power measurement interface.
```

---

## Section F: Recommendation

**Recommendation: ADOPT — Register paths already show NWP `imh0`; adapt Simics inject → use real SVID IMON on silicon**

1. `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3`
2. NWP silicon: use real SVID IMON telemetry (not Simics injection)
3. Verify CSR and TPMI energy status agree; measure idle and workload power accuracy

**Priority**: High — `plc.feature.p2`; energy status reporting accuracy is fundamental to RAPL power management and telemetry
