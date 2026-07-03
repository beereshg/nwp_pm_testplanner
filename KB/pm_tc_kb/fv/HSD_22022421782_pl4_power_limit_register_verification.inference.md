# Deep Analysis: PL4 Power Limit Register Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421782 |
| **Title** | PL4 Power Limit Register Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | PMAX |
| **Sub-Feature** | PL4 TPMI register — pwr_lim_en, pwr_lim, lock fields + mt offset registers |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Comprehensive verification of PL4 TPMI and PMAX hardware registers: `socket_rapl_pl4_control` (pwr_lim_en, pwr_lim, lock) and `pmax_config` MT offset registers (mt0_offset, mt1_offset, mt2_offset). MT offsets adjust Vtrip thresholds based on PL4. `NGA_MAIN` priority — automate for NGA regression. NWP: single IMH0.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` reachable |
| Platform S0 | Fully booted |
| BIOS | PMAX not locked; PL4 not enabled by BIOS |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Read socket_rapl_pl4_control fields. `pl4 = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl4_control; pl4.show(); assert pl4.pwr_lim_en.read()==0; assert pl4.lock.read()==0; assert pl4.pwr_lim.read()!=0` | pwr_lim_en=0; lock=0; pwr_lim non-zero | Any field out of expected — BIOS misconfiguration |
| 2 | Read MT offset registers. `pmax_cfg = sv.socket0.imh0.pmax.pmax0.pmax_config; mt0=pmax_cfg.mt0_offset.read(); mt1=pmax_cfg.mt1_offset.read(); mt2=pmax_cfg.mt2_offset.read(); print(f'mt0={mt0} mt1={mt1} mt2={mt2}')` | MT offsets match BIOS/fuse programmed values | Offsets all zero — BIOS did not program MT offsets |
| 3 | Verify MT offset sign (signed 7-bit: bit 6 = sign, bits[5:0] at 2mV/LSB). `for mt,name in [(mt0,'mt0'),(mt1,'mt1'),(mt2,'mt2')]: signed_val = mt if mt < 64 else mt - 128; print(f'{name}: raw={mt} signed={signed_val} => {signed_val*2}mV')` | All MT offsets decode as valid signed values | Negative offset > platform VccIN range — fuse error |

---

### Pass / Fail Criteria

- **PASS**: PL4 control: pwr_lim_en=0, lock=0, pwr_lim non-zero; MT offsets non-zero and correctly signed.
- **FAIL**: Any field out of expected state; MT offsets all zero.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| socket_rapl_pl4_control | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl4_control | pwr_lim_en=0; pwr_lim=non-zero; lock=0 |
| pmax_config MT offsets | sv.socket0.imh0.pmax.pmax0.pmax_config | mt0/mt1/mt2 non-zero; match BIOS config |

---

### Post-Process

Read-only test — no writes. Collect register dump on failure. Tag NGA_MAIN for automation.

---

### References

- [DMR PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/dmr_pmax.html) — PL4 to MT offset computation; signed 7-bit encoding
- [Punit Registers](https://docs.intel.com/documents/sysip_pm/punit/assets/punit_registers.html) — socket_rapl_pl4_control; pmax_config MT offset fields

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Comprehensive PL4 TPMI register verification including `socket_rapl_pl4_control` and `pmax_config` mt offset registers. NGA_MAIN priority.

Tags: `DMR_PO`, `NGA_MAIN`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p pmax -tM 60
```

### NWP Register Verification
```python
# NWP: PL4 register + mt offsets
pl4 = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl4_control
pl4.show()
# Verify: pwr_lim_en=0, pwr_lim=non-zero, lock=0

# MT offset registers
pmax_cfg = sv.socket0.imh0.pmax.pmax0.pmax_config
mt0_offset = pmax_cfg.mt0_offset.read()
mt1_offset = pmax_cfg.mt1_offset.read()
mt2_offset = pmax_cfg.mt2_offset.read()
print(f"MT offsets: mt0={mt0_offset}, mt1={mt1_offset}, mt2={mt2_offset}")
```

### Pass Criteria
- `pwr_lim_en = 0` (default disabled)
- `pwr_lim` = non-zero
- `lock = 0` (register unlocked)
- `mt0_offset`, `mt1_offset`, `mt2_offset` match BIOS/fuse settings
- `NGA_MAIN` — automate for NGA

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; `sv.socket0.imh0.*` only; `NGA_MAIN` prioritize for NGA automation**

**Priority**: High — `NGA_MAIN`, `DMR_PO`, `plc.feature.p2`; PL4 TPMI register baseline is the P1 requirement for PMAX validation
