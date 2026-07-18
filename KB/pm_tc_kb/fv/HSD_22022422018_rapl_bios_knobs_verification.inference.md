# TC Description: RAPL BIOS Knobs Verification

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422018](https://hsdes.intel.com/appstore/article-one/#/22022422018) |
| **Title** | RAPL BIOS Knobs Verification |
| **Date** | 2026-07-18 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | BIOS knob verification — PL1/PL2/tau/lock knobs reflected in TPMI/CSR |
| **Parent TCD** | [22022420813 -- Socket RAPL Fuse and BIOS Knobs](https://hsdes.intel.com/appstore/article-one/#/22022420813) |
| **Owner** | mps |
| **Status** | open / ready_for_content_review |
| **Priority** | 2-high |
| **Tags** | `DMR_PO`, `PMSS_NWP_READINESS_CHECK` |
| **Val Environment** | silicon, virtual_platform |
| **Val Framework** | os-svos, python-sv |
| **Automation** | `flexconPM.py -c NWPSV.ini` |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Cache version** | 3 |

---

## Test Case Intent

Validates the **BIOS knob verification** scenario defined in [TCD 22022420813 -- Socket RAPL Fuse and BIOS Knobs](https://hsdes.intel.com/appstore/article-one/#/22022420813) §5, row "BIOS knob verification": "BIOS-programmed PL1_CONTROL / PL2_CONTROL values match expected policy; LOCK bit reflects BIOS lock setting; PL values within fused MAX bounds." BIOS programs CSR package_rapl_limit_cfg at CPL3; PrimeCode reads CSR and programs TPMI accordingly. TPMI should reflect BIOS values within 1 LSB. When LOCK bit is set, runtime writes to PL1_CONTROL/PL2_CONTROL are rejected. This TC verifies the full BIOS -> PrimeCode -> TPMI programming chain and lock enforcement.

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP post-silicon system or VP (Simics) |
| OS / Driver | SVOS with PythonSV environment |
| BIOS | Known BIOS RAPL knob configuration; ability to modify BIOS knobs and reboot |
| Tool | flexconPM.py accessible with NWPSV.ini config |
| Starting state | System booted with known BIOS RAPL knob settings (PL1, PL2, tau, lock) |
| TPMI PL1 path | sv.socket0.nio.punit.tpmi.socket_rapl.pl1_control |
| TPMI PL2 path | sv.socket0.nio.punit.tpmi.socket_rapl.pl2_control |
| CSR path | sv.socket0.nio.punit.ptpcioregs.ptpcioregs.package_rapl_limit_cfg |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Run flexconPM BIOS knob checkout: flexconPM.py -c NWPSV.ini. This verifies all RAPL-related BIOS knobs match expected default values. | flexconPM reports all RAPL BIOS knob checks PASS. | Any BIOS knob default mismatch. |
| 2 | Read TPMI PL1_CONTROL.PWR_LIM [17:0]. Compare to expected BIOS PL1 setting (BIOS knob PackagePowerLimit). | PL1_CONTROL.PWR_LIM matches BIOS-configured PL1 value (U11.3 encoding, within 1 LSB). Default = fused TDP. | PL1 mismatch between BIOS knob and TPMI register. |
| 3 | Read TPMI PL2_CONTROL.PWR_LIM [17:0]. Compare to expected BIOS PL2 setting (BIOS knob ShortDurationPowerLimit). | PL2_CONTROL.PWR_LIM matches BIOS-configured PL2 value. Default = 1.2 x fused TDP. | PL2 mismatch. |
| 4 | Read TPMI PL1_CONTROL.TIME_WINDOW [24:18]. Verify encoded tau matches BIOS-configured time window. | TIME_WINDOW value produces tau within [1 s, 5 s] range (PrimeCode clips out-of-range values). | Tau out of expected range or does not match BIOS setting. |
| 5 | Read TPMI PL2_CONTROL.TIME_WINDOW [24:18]. Verify PL2 tau. | TIME_WINDOW produces tau within [11.7 ms, 39 ms] range. | PL2 tau out of valid range. |
| 6 | Read CSR package_rapl_limit_cfg. Verify CSR PL1/PL2 fields match TPMI PL1_CONTROL/PL2_CONTROL values. | CSR and TPMI agree on PL1 power limit, PL2 power limit, PL1 tau, PL2 tau (within 1 LSB). | CSR/TPMI mismatch on any field. |
| 7 | Verify LOCK bit default. Read TPMI PL1_CONTROL.LOCK [63]. Default BIOS setting TurboPowerLimitLock = 0x0 (disabled). | LOCK = 0 (unlocked). TPMI PL1_CONTROL writable by OS/SW. | LOCK = 1 when BIOS default should be unlocked. |
| 8 | Test LOCK enforcement: set BIOS knob TurboPowerLimitLock = 1, reboot. Read PL1_CONTROL.LOCK. | LOCK = 1. PL1_CONTROL is now locked. | LOCK bit not set after BIOS lock knob enabled. |
| 9 | Attempt to write PL1_CONTROL.PWR_LIM via TPMI while LOCK = 1. Read back PL1_CONTROL.PWR_LIM. | Write rejected; PL1_CONTROL.PWR_LIM unchanged from pre-write value. LOCK enforcement working. | PL1 value changed despite LOCK = 1 (lock bypass). |
| 10 | Verify CSR lock: read CSR package_rapl_limit_cfg lock bit. If TurboPowerLimitCsrLock = 1, verify CSR writes also rejected. | CSR lock bit reflects BIOS knob. Locked CSR rejects writes. | CSR lock mismatch or lock bypass. |

### Pass / Fail Criteria

- **PASS**: Per TCD 22022420813 §5 — TPMI PL1_CONTROL/PL2_CONTROL values match BIOS-configured PL1/PL2 (within 1 LSB). Time windows within valid clipped range. CSR and TPMI registers agree. LOCK bit reflects BIOS lock knob setting. When locked, runtime writes are rejected. flexconPM reports all BIOS knob checks PASS.
- **FAIL**: PL1/PL2 mismatch between BIOS knob and TPMI register. Time window out of valid range. CSR/TPMI disagreement. LOCK bit wrong. Locked register accepts writes. flexconPM reports any failure.

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| TPMI PL1_CONTROL | sv.socket0.nio.punit.tpmi.socket_rapl.pl1_control | PWR_LIM matches BIOS PL1; TIME_WINDOW in [1s, 5s]; LOCK matches BIOS knob |
| TPMI PL2_CONTROL | sv.socket0.nio.punit.tpmi.socket_rapl.pl2_control | PWR_LIM matches BIOS PL2; TIME_WINDOW in [11.7ms, 39ms] |
| CSR package_rapl_limit_cfg | sv.socket0.nio.punit.ptpcioregs.ptpcioregs.package_rapl_limit_cfg | Matches TPMI values; lock bit correct |
| TPMI PL_INFO | sv.socket0.nio.punit.tpmi.socket_rapl.pl_info | BIOS PL1 <= MAX_PL1; BIOS PL2 <= MAX_PL2 (within fused bounds) |

### Post-Process

N/A

### References

- [TCD 22022420813 -- Socket RAPL Fuse and BIOS Knobs](https://hsdes.intel.com/appstore/article-one/#/22022420813)
- [Wave 3 Common HAS -- Socket RAPL](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html)
- [OakStream CPUPM FAS](https://docs.intel.com/documents/System-firmware-bios/Domain/ServerCpuPm/Dmr/DMR/Oakstream_CPUPM_FAS.html)

---

## Section A: NWP Delta

NWP carries forward DMR BIOS RAPL knob programming model. NIO replaces IMH.

| Aspect | DMR | NWP |
|--------|-----|-----|
| TPMI PL1_CONTROL | sv.socket0.imh0.punit.tpmi.socket_rapl.pl1_control | sv.socket0.nio.punit.tpmi.socket_rapl.pl1_control |
| CSR path | sv.socket0.imh0.punit.ptpcioregs... | sv.socket0.nio.punit.ptpcioregs... |
| flexconPM config | DMRSV.ini | NWPSV.ini |

## Section F: Recommendations

Recommendation: ADOPT — DMRSV.ini -> NWPSV.ini; verify lock enforcement on both TPMI and CSR paths. Priority: High — BIOS knob checkout is critical for bring-up; lock bits affect OS-level power capping.
