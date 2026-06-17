# Deep Analysis: PMAX Related Fuses Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421799 |
| **Title** | PMAX Related fuses Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | PMAX |
| **Sub-Feature** | PMAX fuses — supervision, MT enable, L1 enable, fuse-to-register propagation |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies PMAX fuses are correctly programmed and propagated to runtime registers. All fuse reads are on IMH0 only for NWP.

Tags: `DMR_PO`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python flexconPM.py  # uses NWPSV.ini
```

### NWP PMAX Fuse Verification
```python
# NWP: all fuse checks on imh0 only (no imh1)
# 1. PMAX supervision fuse
punit_sup = sv.socket0.imh0.fuses.punit.pmsrvr_throttle_pmax_service_punit_supervises_pmax_fuse.read()
assert punit_sup == 0x1, "punit_supervises_pmax fuse must = 1"

# 2. Root supervisor fuse
root_sup = sv.socket0.imh0.fuses.punit.pmsrvr_throttle_pmax_service_punit_root_supervisor_fuse.read()
assert root_sup == 0x1, "punit_root_supervisor fuse must = 1"

# 3. PMAX MT enable fuse → verify propagated to register
mt_en_fuse = sv.socket0.imh0.fuses.pmax_top.pmax_control2_pmax_mt_en.read()
mt_en_reg = sv.socket0.imh0.pmax.pmax0.pmax_control2.pmax_mt_en.read()
assert mt_en_fuse == 0x1, "pmax_mt_en fuse must = 1"
assert mt_en_fuse == mt_en_reg, "fuse must propagate to register"

# 4. PMAX L1 enable fuse
l1_en_fuse = sv.socket0.imh0.fuses.pmax_top.pmax_control2_pmax_l1_en.read()
assert l1_en_fuse == 0x1, "pmax_l1_en fuse must = 1"
```

### Pass Criteria
- All 4 PMAX fuse checks pass for IMH0
- Fuse values propagate correctly to runtime registers
- `flexconPM` passes for NWP

---

## Section F: Recommendation

**Recommendation: ADOPT — Remove IMH1 fuse checks (NWP has single IMH0); `DMRSV.ini` → `NWPSV.ini`; PMAX fuse architecture same**

**Priority**: Medium — `DMR_PO`; fuse verification must pass before any PMAX functional test — fuses define PMAX behavior
