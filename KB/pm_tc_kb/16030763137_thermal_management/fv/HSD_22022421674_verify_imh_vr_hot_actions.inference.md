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
