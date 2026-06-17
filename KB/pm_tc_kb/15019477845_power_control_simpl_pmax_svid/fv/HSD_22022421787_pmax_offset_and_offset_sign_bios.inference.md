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
