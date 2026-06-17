# Deep Analysis: PMAX TRIGGER IO BIOS Knobs Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421788 |
| **Title** | PMAX TRIGGER IO Bios Knobs Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | PMAX |
| **Sub-Feature** | PMAX trigger setup BIOS knob — GPIO trigger enable via EFI Shell + TPMI register verification |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the PMAX Trigger Setup BIOS knob and its effect on `pmax_control.pmax_gpio_trigger_enable`. BIOS should configure the trigger; test reads TPMI to confirm.

**NWP key difference**: Steps reference `sv.sockets.imhs.punit.ptpcfsms.ptpcfsms.pmax_control` (plural) → NWP uses `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.pmax_control` (single imh0).

Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p pmax_bios -tM 60 -M 5
```

### NWP TPMI Register Reads
```python
# NWP: single imh0 (NOT sv.sockets.imhs.*)
pmax_ctrl = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.pmax_control
pmax_ctrl.show()
# Verify pmax_gpio_trigger_enable matches BIOS "Trigger Setup" knob value
# Default Trigger Setup = 0 → pmax_gpio_trigger_enable = 0
```

### BIOS Menu Steps (NWP)
1. Boot to EFI Shell
2. Navigate to PMAX Detector Configuration
3. Verify Trigger Setup Value = 0 (default)
4. After boot, read `pmax_control.pmax_gpio_trigger_enable` — expect = 0

### Pass Criteria
- BIOS PMAX Trigger Setup visible in menu
- `pmax_gpio_trigger_enable` matches BIOS knob (0 = disabled by default)
- `pmax_bios` PMx plugin passes for NWP

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; `sv.sockets.imhs.*` → `sv.socket0.imh0.*` (single IMH); PMAX trigger BIOS knob same**

**Priority**: Medium — `plc.feature.p2`; trigger I/O configuration determines whether GPIO-based PMAX trigger is active
