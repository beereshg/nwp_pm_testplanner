# Deep Analysis: [VR Hot] Verify IMH VR Hot Actions

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421674 |
| **Title** | [VR Hot] Verify IMH VR Hot Actions |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | VR Hot — iMH MBVR VR Hot detection via PMSB polling |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Test Case Intent

**Objective:** Verify that iMH (IMH die) VR Hot detection and throttle response works correctly on NWP. When the external MBVR (Multi-Board Voltage Regulator) on iMH0 asserts a thermal alert, Primecode detects it via active **PMSB polling** of `SVID_VR_STATUS.THERM_ALERT` (not via SVID PM_EVENT notification), reduces iMH mesh frequency to P1, and sends a frequency limit to CBB dies via HPM message.

### Pre-Conditions

| Pre-Condition | Expected State | Failure Indication |
|---------------|---------------|-------------------|
| NWP booted to OS | PCode running; imh0 accessible | System not booted |
| VR Hot injection available | PMSB or test hook to assert THERM_ALERT on iMH0 MBVR | Cannot inject VR Hot event |
| PMx prochot_thermal script available | `runPmx.py -x nwp.xml -p prochot_thermal` works | PMx script missing |
| Baseline mesh + CBB ratios known | Read `imh0.punit.ufs_status` + `cbb0/1.punit.ufs_status` | TPMI not initialized |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Run PMx: `runPmx.py -x nwp.xml -p prochot_thermal -tM 20 -M 5` | PMx starts; baseline ratios logged | PMx fails to start |
| 2 | Inject VR Hot on imh0 MBVR: assert `SVID_VR_STATUS.THERM_ALERT` via PMSB | THERM_ALERT visible in SVID_VR_STATUS | Injection fails; no THERM_ALERT |
| 3 | Verify Primecode detects via PMSB poll (NOT SVID PM_EVENT) | Pcode debug telemetry shows PMSB-path detection within 1 slow-loop | Detection via PM_EVENT instead -- architecture mismatch |
| 4 | Verify iMH mesh frequency drops to P1 | `sv.socket0.imh0.punit.ufs_status.current_ratio` = P1 (maximum non-turbo) | Ratio unchanged -- VR Hot response not firing |
| 5 | Verify HPM frequency limit sent to CBB dies | HPM message log shows freq limit to cbb0 and cbb1 | No HPM message -- CBBs not notified |
| 6 | Verify CBB dies throttle in response to IMH VR Hot limit | `sv.socket0.cbb[0-1].punit.ufs_status.current_ratio` reduced to iMH limit | CBBs unaffected -- HPM message not processed |
| 7 | Remove VR Hot; verify imh0 mesh + CBBs recover to baseline | Both imh0 and CBB ratios return to pre-VR-Hot values | Stuck at throttled ratio -- recovery broken |

### Pass / Fail Criteria

**PASS:** THERM_ALERT detected via PMSB poll; iMH mesh frequency = P1; HPM limit sent to cbb0/cbb1; CBBs throttle; full recovery after VR Hot cleared.

**FAIL:** VR Hot not detected (poll path broken); iMH mesh not reduced to P1; HPM message not sent; CBBs unaffected; stuck throttle after VR Hot release.

### Post-Process

Save: SVID_VR_STATUS before/during injection, imh0 mesh ratio trace, HPM message log, CBB ratio trace, recovery timestamp.

### Reference Documents

- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- iMH VR Hot response, PMSB polling path
- [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html) -- SVID_VR_STATUS.THERM_ALERT, iMH throttle on VR Hot

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **iMH VR Hot** detection and response via PMSB (not SVID):
- Primecode periodically polls `SVID_VR_STATUS` over **PMSB** for iMH external MBVR VR Hot
- (Note: iMH does NOT rely on SVID PM_EVENT notification for VR Hot — polls actively)
- On VR Hot: iMH reduces iMH mesh frequency to P1 and sends CBB die frequency limit via HPM message

On NWP:
- Single `imh0` with external MBVR stack
- Tags: `Ready_for_testing`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`

---

## Section B: NWP-Specific Test Procedure

### iMH VR Hot Flow (NWP)

| Step | Component | NWP Detail |
|------|-----------|------------|
| Poll | imh0 Pcode Slowloop polls SVID_VR_STATUS via PMSB | Not via SVID PM_EVENT |
| Detect | `SVID_STATUS.THERM_ALERT` asserted on iMH MBVR stack | External VR |
| Action 1 | Reduce iMH mesh frequency to P1 | `sv.socket0.imh0.punit.ufs_status.current_ratio` → P1 |
| Action 2 | Send CBB dies frequency limit via HPM message | imh0 → cbb0/cbb1 |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run prochot_thermal PMx | `python runPmx.py -x nwp.xml -p prochot_thermal -tM 20 -M 5` |
| 2 | Inject VR Hot on imh0 external MBVR | Assert SVID_STATUS.THERM_ALERT via PMSB |
| 3 | Verify Pcode detects via PMSB poll (not PM_EVENT) | Check Pcode telemetry/debug registers |
| 4 | Verify imh0 mesh ratio drops to P1 | `sv.socket0.imh0.punit.ufs_status.current_ratio` |
| 5 | Verify HPM freq limit message sent to cbb0, cbb1 | Punit HPM message log / telemetry |
| 6 | Verify CBB dies throttled in response | `sv.socket0.cbb[0-1].punit.ufs_status.current_ratio` at limit |
| 7 | Remove VR Hot; verify imh0 mesh + CBBs recover | Ratio returns to normal |

### NWP Key Notes
- iMH VR Hot polling is via **PMSB** (not SVID event) — critical architectural distinction
- P1 = maximum non-turbo ratio for NWP
- Single `imh0` — no secondary iMH MBVR to test
- CBB frequency limit via HPM distinguishes iMH VR Hot from CBB VR Hot

### Pass Criteria
- iMH VR Hot detected via PMSB poll
- imh0 mesh frequency drops to P1
- HPM frequency limit message sent to cbb0 and cbb1
- CBB dies throttle in response to iMH VR Hot
- Full recovery after VR Hot cleared

---

## Section F: Recommendation

**Recommendation: ADOPT — Key distinction: iMH VR Hot detection via PMSB poll (not SVID PM_EVENT)**

1. `python runPmx.py -x nwp.xml -p prochot_thermal -tM 20 -M 5`
2. NWP: single `imh0` with external MBVR; PMSB polling path
3. Verify both imh0 mesh throttle AND HPM message to CBBs
4. Distinguish from CBB VR Hot (TC 22022421673) — this is iMH-specific flow

**Priority**: High — `plc.feature.p1`; iMH VR Hot via PMSB is a distinct validation path from CBB VR Hot
