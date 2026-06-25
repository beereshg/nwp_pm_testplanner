# Deep Analysis: PMAX Offset and Offset Sign BIOS Knob Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421787 |
| **Title** | PMAX Offset and Offset Sign Bios Knob Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | PMAX |
| **Sub-Feature** | PMAX Vtrip offset BIOS knob — VccIn adjustment options in EFI Shell BIOS menu |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify PMAX Vtrip offset BIOS knob correctly programs `pmax_control.pmax_vtrip_0_offset` (and sign bit) via EFI Shell. BIOS PMAX Detector Configuration menu shows `VccIn 0 Adjustment` with configurable offset and sign. NWP: VccIn 0 only (no VccIn 1 / IMH1). `NGA_MAIN` priority.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| EFI Shell access | Boot to EFI Shell; navigate BIOS PMAX Detector Configuration menu |
| SV session | `sv.socket0.imh0` available post-boot |
| BIOS version | BIOS supporting VccIn 0 Adjustment knob for NWP |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Boot to EFI Shell; navigate to Advanced → Power Management → PMAX Detector Configuration. Verify VccIn 0 Adjustment option present (NWP: VccIn 0 only). | VccIn 0 Adjustment visible; no VccIn 1 option (NWP single IMH0) | VccIn 1 still shown — BIOS not updated for NWP; or VccIn 0 missing |
| 2 | Set VccIn 0 Adjustment offset and sign; boot to OS. Verify `pmax_control.pmax_vtrip_0_offset` reflects BIOS setting. `pmax_ctrl = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.pmax_control; vtrip=pmax_ctrl.pmax_vtrip_0_offset.read(); print(f'vtrip_offset={vtrip} ({vtrip*2}mV)')` | Vtrip offset matches BIOS-programmed value; sign bit correct | Mismatch — BIOS knob not propagating to TPMI |
| 3 | Run PMx pmax_bios test. `python runPmx.py -x nwp.xml -p pmax_bios -tM 60 -M 5` | PMx PASS | PMx FAIL — collect run log |

---

### Pass / Fail Criteria

- **PASS**: VccIn 0 Adjustment visible in BIOS; offset propagates to `pmax_vtrip_0_offset`; PMx pmax_bios PASS.
- **FAIL**: BIOS knob absent or does not propagate; register mismatch.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| pmax_vtrip_0_offset | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.pmax_control.pmax_vtrip_0_offset | Matches BIOS VccIn 0 Adjustment value |
| pmax_control.lock | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.pmax_control.lock | = 1 after boot (BIOS locked) |

---

### Post-Process

Restore BIOS offset to default after test. Collect BIOS screenshot and register dump on failure.

---

### References

- [DMR PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/dmr_pmax.html) — Vtrip offset signed 7-bit encoding; BIOS knob propagation
- [OakStream CPUPM FAS](https://docs.intel.com/documents/System-firmware-bios/Domain/ServerCpuPm/Dmr/DMR/Oakstream_CPUPM_FAS.html) — BIOS PMAX offset knob definition

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies PMAX Vtrip offset BIOS knob via EFI Shell. BIOS menu shows:
- VccIn 0 (and VccIn 1 on DMR) Adjustment options
- PMAX Config Offset values

**NWP key difference**: DMR has VccIn 0 **and** VccIn 1 (for IMH0 and IMH1) → NWP has **VccIn 0 only** (single IMH0).

Tags: `DMR_PO`, `plc.feature.p2`, `NGA_MAIN`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p pmax_bios -tM 60 -M 5
```

### BIOS Menu Path (NWP)
1. Boot to EFI Shell
2. Navigate: `Advanced → Power Management Configuration → PMAX Detector Configuration`
3. Verify: **VccIn 0 Adjustment** option displayed (NWP: only VccIn 0, no VccIn 1)
4. Verify PMAX Config Offset value programmed correctly

### NWP BIOS Knob Register
```python
# NWP: verify PMAX offset via register (post-BIOS)
pmax_ctrl = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.pmax_control
# Check Vtrip offset field set per BIOS knob
```

### Pass Criteria
- VccIn 0 Adjustment option visible in BIOS PMAX menu
- PMAX Config Offset value matches BIOS knob setting
- `pmax_control` register reflects the offset after boot
- `pmax_bios` PMx plugin passes

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; NWP has VccIn 0 only (no VccIn 1 / IMH1); PMAX offset BIOS knob architecture same**

**Priority**: High — `NGA_MAIN`, `plc.feature.p2`; BIOS knob controls Vtrip offset which affects PMAX trigger threshold
