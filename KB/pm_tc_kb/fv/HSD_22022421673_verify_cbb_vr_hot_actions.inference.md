# Deep Analysis: [VR Hot] Verify CBB VR Hot Actions

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421673 |
| **Title** | [VR Hot] Verify CBB VR Hot Actions |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | VR Hot — CBB MBVR SVID Therm Alert detection and throttle response |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies CBB **VR Hot** detection and response:
1. IMH Primecode polls CBB MBVR stack via `SVID_VR_STATUS` for SVID ALERTs in the Slow Loop
2. When VR temperature exceeds TEMP_MAX, the MBVR asserts VR Hot via `SVID_STATUS.THERM_ALERT` bit
3. Pcode action: throttle CBB Core and Ring to P1; update perf limit reasons; send HPM message

On NWP:
- 2 CBBs (cbb0, cbb1) each have a MBVR stack
- Single `imh0` polls both CBB MBVR stacks
- SVID register polling path: `sv.socket0.imh0.punit.svid_vr_status.*`
- Tags: `Ready_for_testing`, `NGA_MAIN`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`

---

## Section B: NWP-Specific Test Procedure

### VR Hot Detection Path (NWP)

| Component | Register | Path |
|-----------|----------|------|
| CBB MBVR VR Hot | `SVID_VR_STATUS.THERM_ALERT` | Polled by imh0 Pcode Slowloop |
| Pcode throttle action | Core and Ring → P1 | HPM message from imh0 to cbb0/cbb1 |
| Perf limit reason | VR Hot bit | `sv.socket0.cbb[0-1].punit.perf_limit_reasons.*` |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run prochot_thermal PMx (VR Hot flow) | `python runPmx.py -x nwp.xml -p prochot_thermal -tM 20 -M 5` |
| 2 | Inject VR Hot condition on cbb0 MBVR | Assert `SVID_STATUS.THERM_ALERT` bit for cbb0 VR stack |
| 3 | Verify Pcode detects SVID alert in Slowloop | Check telemetry / Punit state |
| 4 | Verify cbb0 Core + Ring throttled to P1 | `sv.socket0.cbb0.punit.ufs_status.current_ratio` |
| 5 | Verify HPM message sent, perf limit reason updated | VR Hot reason in `perf_limit_reasons` |
| 6 | Remove VR Hot; verify cbb0 recovery | Ratio returns to normal |
| 7 | Repeat steps 2–6 for cbb1 | Verify both CBB MBVR stacks detected |

### NWP Key Notes
- NWP: single `imh0` polls SVID for both cbb0 and cbb1 MBVR stacks
- Pcode Slowloop frequency determines detection latency
- Core and Ring throttle to P1 (P1 = max non-turbo on NWP)
- HPM message path: imh0 → cbb0/cbb1 DNS_EVENT_DELIVERY [VR_THERM_ALERT]

### Pass Criteria
- VR Hot detected in Pcode Slowloop for each CBB MBVR
- Core and Ring ratio drops to P1 on VR Hot
- Perf limit reason reflects VR Hot
- Recovery to normal frequency after VR Hot cleared

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; test both CBB MBVR stacks (cbb0, cbb1)**

1. `python runPmx.py -x nwp.xml -p prochot_thermal -tM 20 -M 5`
2. Inject VR Hot on cbb0 MBVR, then cbb1 MBVR, verify each detected and throttled
3. NWP: single `imh0` Slowloop polls both CBB SVID stacks
4. Verify HPM message and perf_limit_reasons for each CBB

**Priority**: High — `plc.feature.p1`; VR Hot protection is critical thermal/VR safety coverage
