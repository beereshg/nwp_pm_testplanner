# Deep Analysis: PMAX CONTROL Register Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421764 |
| **Title** | PMAX CONTROL Register Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | PMAX |
| **Sub-Feature** | PMAX control register — Vtrip offset, trigger programming, verified via `pmax_control` register |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

PMAX (Power Maximum) is functional on NWP (not on ZBB list). This test verifies `pmax_control` register fields including Vtrip offset and trigger configuration. BIOS locks this register at boot, so it is read-only at runtime.

**NWP key difference**: DMR has `imh0` and `imh1` → NWP has **single `imh0` only**. Remove all `imhX (X=0/1)` double-check iterations; only check `imh0`.

Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p pmax -tM 60
```

### NWP Register Path
```python
# NWP: single imh0 (no imh1)
pmax_ctrl = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.pmax_control
pmax_ctrl.show()  # Read all pmax_control fields

# Verify:
# - Vtrip offset programmed correctly
# - Trigger configuration matches BIOS
# - Register is locked (BIOS-locked after boot)
```

### Pass Criteria
- `pmax_control` fields match BIOS-programmed values
- Register locked after boot (cannot be modified at runtime)
- Vtrip offset and trigger fields non-zero / match spec
- `pmax` PMx plugin passes for NWP

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; remove imh1 references (NWP single imh0); PMAX control register architecture same**

**Priority**: Medium — `plc.feature.p2`; PMAX control register baseline is prerequisite for all PMAX functional tests
