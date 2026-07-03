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

### Test Case Intent

Verify PMAX Trigger Setup BIOS knob correctly programs `pmax_control.pmax_gpio_trigger_enable` (and related trigger config). Default is 0 (disabled). BIOS configures trigger; test reads TPMI post-boot to confirm. NWP: single `imh0` (not `sv.sockets.imhs.*`).

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| EFI Shell access | Navigate BIOS PMAX Detector Configuration menu |
| SV session | `sv.socket0.imh0` available post-boot |
| Expected default | BIOS Trigger Setup = 0 → `pmax_gpio_trigger_enable = 0` |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Boot to EFI Shell; verify BIOS PMAX Trigger Setup = 0 (default). | Trigger Setup = 0 visible in BIOS menu | Trigger Setup missing or unexpected value |
| 2 | Boot to OS; read `pmax_gpio_trigger_enable`. `pmax_ctrl = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.pmax_control; trig_en = pmax_ctrl.pmax_gpio_trigger_enable.read(); print(f'pmax_gpio_trigger_enable={trig_en}'); assert trig_en == 0` | pmax_gpio_trigger_enable = 0 (matches BIOS = 0) | Mismatch — BIOS knob not propagating |
| 3 | Change BIOS Trigger Setup to enabled; re-boot; verify register reflects new value. | pmax_gpio_trigger_enable = 1 (or configured value) | Still 0 after BIOS change — BIOS not writing to TPMI |
| 4 | Run PMx pmax_bios test. `python runPmx.py -x nwp.xml -p pmax_bios -tM 60 -M 5` | PMx PASS | PMx FAIL |

---

### Pass / Fail Criteria

- **PASS**: `pmax_gpio_trigger_enable` matches BIOS Trigger Setup knob value; PMx pmax_bios PASS.
- **FAIL**: Register does not reflect BIOS setting.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| pmax_gpio_trigger_enable | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.pmax_control | Matches BIOS Trigger Setup value |
| pmax_control.lock | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.pmax_control.lock | = 1 post-boot |

---

### Post-Process

Restore BIOS Trigger Setup to default. Collect register state on failure.

---

### References

- [Newport NIO GPIO HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/gpio/newport_nio_gpio_has.html) — PMAX_TRIGGER_IO; GPIO trigger enable/disable on NIO
- [OakStream CPUPM FAS](https://docs.intel.com/documents/System-firmware-bios/Domain/ServerCpuPm/Dmr/DMR/Oakstream_CPUPM_FAS.html) — BIOS PMAX trigger setup knob

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
