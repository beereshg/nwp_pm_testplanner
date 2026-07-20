# Deep Analysis: [VR Hot] Verify VR_THERM_ALERT_DISABLE_emulation

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421679 |
| **Title** | [VR Hot] Verify VR_THERM_ALERT_DISABLE_emulation |
| **Date** | 2026-07-19 |
| **Target Program** | NWP (Newport) |
| **Segment** | FV |
| **Feature** | Thermal GPIO > VR Hot |
| **NWP Disposition** | Runnable_On_N-1 |

## Test Case Intent

Validates the VR_THERM_ALERT_DISABLE register behavior in emulation environment — verifying that thermal alert disable path correctly suppresses VR Hot response, defined in [TCD 22022420628 — VR Hot](https://hsdes.intel.com/appstore/article-one/#/22022420628) §5. Environment: NWP FV (emulation).

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Emulation variant of VR_THERM_ALERT_DISABLE validation. Tests the VR thermal alert disable register to confirm that when set, VR Hot events do not trigger PCode throttle response. Same as silicon TC (22022421676) but in emulation environment.

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP emulation environment (HSLE) with VR Hot injection
- PCode firmware loaded
- PythonSv access to VR_THERM_ALERT_DISABLE register

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Set VR_THERM_ALERT_DISABLE = 1 | Write via PythonSv |
| 2 | Inject VR Hot event | Use emulation VR thermal injection |
| 3 | Verify NO PCode throttle response | Frequency should remain unchanged |
| 4 | Verify PLR HOT_VR NOT set | PLR should not reflect VR Hot |
| 5 | Clear VR_THERM_ALERT_DISABLE = 0 | Restore default |
| 6 | Inject VR Hot again | VR Hot should now trigger response |
| 7 | Verify PCode throttle active | Frequency reduced; PLR HOT_VR set |

## Section C: Pass/Fail Measurement Method

**Bar:** Per TCD 22022420628 §5: VR_THERM_ALERT_DISABLE=1 → no throttle on VR Hot; =0 → normal VR Hot response.
