# Deep Analysis: [VR Hot] Verify VR_THERM_ALERT_DISABLE

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421676 |
| **Title** | [VR Hot] Verify VR_THERM_ALERT_DISABLE |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | VR Hot — VR_THERM_ALERT_DISABLE bit disables CBB notification |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **VR_THERM_ALERT_DISABLE** functionality:
- When VR Hot event occurs (~97% heat indication from VR), PrimeCode notifies CBB via HPM message `DNS_EVENT_DELIVERY [VR_THERM_ALERT]`
- CBB action: throttle Core and Ring to P1; update perf limit reasons
- `VR_THERM_ALERT_DISABLE` bit disables this CBB notification — verifying the disable suppresses the throttle action

On NWP:
- 2 CBBs receive VR Hot HPM messages from imh0
- `VR_THERM_ALERT_DISABLE` can be set per-CBB or globally via Punit/fuse
- Tags: `DMR_PO`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`

---

## Section B: NWP-Specific Test Procedure

### VR Hot Notification Flow (NWP)

| Flow | Description |
|------|-------------|
| VR Hot detected | imh0 Pcode detects VR Therm Alert (~97% temp) |
| CBB notification | HPM message `DNS_EVENT_DELIVERY [VR_THERM_ALERT]` → cbb0, cbb1 |
| CBB action | Core + Ring throttle to P1; perf limit reason updated |
| Disable | `VR_THERM_ALERT_DISABLE=1` → HPM message suppressed → no CBB throttle |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run prochot_thermal PMx | `python runPmx.py -x nwp.xml -p prochot_thermal -tM 20 -M 5` |
| 2 | Verify normal VR Hot CBB notification (baseline) | VR Hot → CBBs throttle → perf_limit_reasons updated |
| 3 | Set `VR_THERM_ALERT_DISABLE=1` | Punit register or fuse override at imh0 |
| 4 | Inject VR Hot condition | ~97% VR heat indication |
| 5 | Verify CBB does NOT throttle (notification suppressed) | No perf limit reason; no P1 throttle on cbb0/cbb1 |
| 6 | Verify perf limit reasons NOT updated | `sv.socket0.cbb[0-1].punit.perf_limit_reasons.*` = unchanged |
| 7 | Restore disable=0; verify normal operation | VR Hot notification resumes |

### NWP Key Notes
- NWP 2 CBBs: verify disable affects both `cbb0` and `cbb1` notifications
- Single `imh0` is the notification source — disable at imh0 level
- `DNS_EVENT_DELIVERY [VR_THERM_ALERT]` is the HPM message to check
- 97% threshold is the VR Hot assertion point (pre-thermtrip)

### Pass Criteria
- With disable=0: VR Hot → CBBs throttle to P1; perf_limit_reasons updated
- With disable=1: VR Hot → CBBs NOT throttled; perf_limit_reasons unchanged
- Disable applies to both CBB0 and CBB1 notification paths

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; verify disable affects both cbb0 and cbb1 HPM notifications**

1. `python runPmx.py -x nwp.xml -p prochot_thermal -tM 20 -M 5`
2. NWP: 2 CBBs; verify disable suppresses VR_THERM_ALERT HPM to both
3. Test both: disable=0 (throttle active) and disable=1 (throttle suppressed)

**Priority**: Medium — `plc.feature.p1`; VR Hot disable is configuration validation completing the VR Hot test suite
