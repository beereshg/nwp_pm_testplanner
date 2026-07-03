# Deep Analysis: Turbo BIOS Configurations

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422408 |
| **Title** | Turbo BIOS Configurations |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | Turbo BIOS knob verification — TurboMode, EETurbo |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **Turbo BIOS knobs** using Flexcon:
- `TurboMode = 0x1` (enabled)
- `EETurbo = 0x1` (enabled — Energy Efficient Turbo)

Boot, set BIOS knobs, reboot, verify knobs persisted and Turbo is granted. Uses Flexcon with `DMRSV.ini` → `NWPSV.ini`.

On NWP, TurboMode and EETurbo are standard BIOS knobs. Direct Flexcon adaptation.

**Key Justification:**
- `Ready_for_testing` + `PMSS_NWP_READINESS_CHECK` tags
- Turbo BIOS configuration applicable on NWP

---

## Section B: NWP-Specific Test Procedure

### BIOS Knob Test Matrix

| Test | TurboMode | EETurbo | Expected Behavior |
|------|-----------|---------|-------------------|
| Enabled | 0x1 | 0x1 | Turbo granted; EE turbo active |
| Disabled | 0x0 | 0x0 | Turbo not granted |

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Boot NWP normally | Standard SVOS boot |
| 2 | Set BIOS knobs: TurboMode = 0x1, EETurbo = 0x1 | Via BIOS setup |
| 3 | Reboot NWP | Verify knobs survive reboot |
| 4 | Run Flexcon: `python flexcon.py -i NWPSV.ini --onlyspecifiedmodules -m flexconPM` | NWP config |
| 5 | Verify `TurboMode = 0x1` and `EETurbo = 0x1` in Flexcon output | Same knob names |

### NWP Pass Criteria
- Turbo knobs persist across reboot
- Turbo frequency granted when TurboMode = 0x1
- EETurbo enabled when EETurbo = 0x1
- Flexcon PM module passes on NWP

---

## Section F: Recommendation

**Recommendation: ADOPT — `DMRSV.ini` → `NWPSV.ini`; Turbo BIOS knobs same on NWP**

Required adaptations:
1. Replace `DMRSV.ini` with `NWPSV.ini` in Flexcon command
2. Verify Flexcon PM module handles NWP-specific Turbo register paths

**Priority**: Medium — `Ready_for_testing`; Turbo BIOS knob bring-up check
