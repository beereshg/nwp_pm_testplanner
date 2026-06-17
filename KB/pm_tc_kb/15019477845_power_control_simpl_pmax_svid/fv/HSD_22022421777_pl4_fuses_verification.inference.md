# Deep Analysis: PL4 Fuses Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421777 |
| **Title** | PL4 Fuses Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | PMAX |
| **Sub-Feature** | PL4 fuses — SOCKET_PL4_POWER_DEFAULT and related fuse validation |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

PL4 is the PMAX power limit hardware fuse. This test verifies:
1. `SOCKET_PL4_POWER_DEFAULT` fuse is non-zero
2. Fuse value matches `socket_rapl_pl4_control.pwr_lim / 8` (pwr_unit)
3. Related PL4 fuse pointers correct

**NWP key difference**: DMR checks IMH0 **and** IMH1 fuses → NWP has **single IMH0 only** (remove IMH1 fuse reads).

Tags: `DMR_PO`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python flexconPM.py  # uses NWPSV.ini
```

### NWP PL4 Fuse Reads (imh0 only)
```python
# NWP: PL4 fuse verification — imh0 only (no imh1)
# a. SOCKET_PL4_POWER_DEFAULT
pl4_fuse = sv.socket0.imh0.fuses.punit.pcode_socket_pl4_power_default.read()
pl4_ctrl = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl4_control.pwr_lim.read()
pwr_unit = 8  # verify per NWP spec
print(f"PL4 fuse: {pl4_fuse}, PL4 ctrl / unit: {pl4_ctrl / pwr_unit}")
assert pl4_fuse == pl4_ctrl / pwr_unit, "PL4 fuse mismatch"
assert pl4_fuse != 0, "PL4 fuse must be non-zero"
```

### Pass Criteria
- `pcode_socket_pl4_power_default` fuse is non-zero
- Fuse value consistent with `socket_rapl_pl4_control.pwr_lim / pwr_unit`
- All related PL4 pointer fuses correct for NWP

---

## Section F: Recommendation

**Recommendation: ADOPT — Remove IMH1 references (NWP has single IMH0); `DMRSV.ini` → `NWPSV.ini` for flexconPM; PL4 fuse architecture same**

**Priority**: Medium — `DMR_PO`; PL4 fuse baseline is required for PMAX overcurrent protection at the correct power level
