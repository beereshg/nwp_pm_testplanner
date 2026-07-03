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

### Test Case Intent

Verify PMAX control fuses are correctly programmed and propagated to runtime registers: `punit_supervises_pmax = 1`, `punit_root_supervisor = 1`, `pmax_mt_en = 1`, `pmax_l1_en = 1`. Fuse-to-register propagation confirms PrimeCode correctly initializes PMAX at boot. NWP: IMH0 only.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` and `sv.socket0.imh0.fuses.*` reachable |
| Platform S0 | Fully booted post-PH6 |
| PMx | `python flexconPM.py` (NWPSV.ini) available |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Read punit_supervises_pmax and root_supervisor fuses. `sup = sv.socket0.imh0.fuses.punit.pmsrvr_throttle_pmax_service_punit_supervises_pmax_fuse.read(); root = sv.socket0.imh0.fuses.punit.pmsrvr_throttle_pmax_service_punit_root_supervisor_fuse.read(); assert sup == 1; assert root == 1` | Both fuses = 1 | Fuse = 0 — PMAX supervision not enabled; check SKU |
| 2 | Read pmax_mt_en fuse and verify propagated to register. `mt_fuse = sv.socket0.imh0.fuses.pmax_top.pmax_control2_pmax_mt_en.read(); mt_reg = sv.socket0.imh0.pmax.pmax0.pmax_control2.pmax_mt_en.read(); assert mt_fuse == 1; assert mt_fuse == mt_reg` | MT fuse = 1; propagated to register | Fuse/register mismatch — PrimeCode init failure |
| 3 | Read pmax_l1_en fuse. `l1_fuse = sv.socket0.imh0.fuses.pmax_top.pmax_control2_pmax_l1_en.read(); assert l1_fuse == 1` | L1 enable fuse = 1 | L1 fuse = 0 — soft throttle L1 path disabled |
| 4 | Run flexconPM. `python flexconPM.py  # uses NWPSV.ini` | flexconPM PASS for NWP | flexconPM FAIL — collect run log |

---

### Pass / Fail Criteria

- **PASS**: All 4 fuse checks pass; fuse values correctly propagated to registers; flexconPM PASS.
- **FAIL**: Any fuse = 0 or fuse/register mismatch.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| punit_supervises_pmax fuse | sv.socket0.imh0.fuses.punit.* | = 1 |
| punit_root_supervisor fuse | sv.socket0.imh0.fuses.punit.* | = 1 |
| pmax_mt_en fuse | sv.socket0.imh0.fuses.pmax_top.* | = 1; matches pmax_control2.pmax_mt_en |
| pmax_l1_en fuse | sv.socket0.imh0.fuses.pmax_top.* | = 1 |

---

### Post-Process

Read-only test. Collect fuse dump on failure.

---

### References

- [DMR PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/dmr_pmax.html) — PMAX fuse structure; punit_supervises_pmax; pmax_mt_en; pmax_l1_en
- [DMR PMax Detector HAS](https://docs.intel.com/documents/arch_datacenter/pmax/dmr/dmr_pmax_detector_has/dmr_pmax_detector_has.html) — fuse propagation to runtime registers

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
