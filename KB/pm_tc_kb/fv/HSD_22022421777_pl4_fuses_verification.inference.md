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

### Test Case Intent

Verify `SOCKET_PL4_POWER_DEFAULT` fuse is non-zero and correctly propagated to `socket_rapl_pl4_control.pwr_lim`. PL4 is the hardware instantaneous power cap; its fuse must reflect the platform-rated maximum. NWP: single IMH0 only (no IMH1 fuse reads).

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` reachable |
| Platform S0 | Fully booted post-PH6 |
| pwr_unit | Confirm from `socket_rapl_power_unit` (expected = 8) |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Read PL4 fuse. `pl4_fuse = sv.socket0.imh0.fuses.punit.pcode_socket_pl4_power_default.read(); assert pl4_fuse != 0` | PL4 fuse non-zero | pl4_fuse = 0 — fuse not programmed; check SKU |
| 2 | Read PL4 TPMI register and verify fuse matches. `pl4_ctrl = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl4_control.pwr_lim.read(); pwr_unit = 8; assert pl4_fuse == pl4_ctrl / pwr_unit` | Fuse value matches TPMI pwr_lim / power_unit | Mismatch — PrimeCode did not propagate fuse correctly; check PH6 init |
| 3 | Verify ratio vs TDP. `pl1 = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control.pwr_lim.read(); ratio = (pl4_ctrl/pwr_unit) / (pl1/pwr_unit); assert 1.5 <= ratio <= 3.0` | PL4 = 1.5–3× TDP | Ratio out of range — check fuse programming |

---

### Pass / Fail Criteria

- **PASS**: PL4 fuse non-zero; matches TPMI pwr_lim; ratio to TDP in range 1.5–3×.
- **FAIL**: Fuse = 0; fuse != TPMI; ratio out of spec.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| pcode_socket_pl4_power_default | sv.socket0.imh0.fuses.punit.* | Non-zero |
| socket_rapl_pl4_control | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl4_control | pwr_lim matches fuse; pwr_lim_en=0 (disabled by default) |
| socket_rapl_power_unit | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_power_unit | power = 3 (1/8 W/LSB) |

---

### Post-Process

No registers modified. Collect fuse dump if mismatch found.

---

### References

- [DMR PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/dmr_pmax.html) — PL4 fuse to register propagation; SOCKET_PL4_POWER_DEFAULT
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — PL4 power unit encoding

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
