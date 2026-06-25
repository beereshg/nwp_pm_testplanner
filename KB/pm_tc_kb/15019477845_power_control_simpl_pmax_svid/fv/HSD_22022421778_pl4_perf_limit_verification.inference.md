# Deep Analysis: PL4 Perf Limit Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421778 |
| **Title** | PL4 Perf Limit Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | PMAX |
| **Sub-Feature** | PL4 power limit — verify default: disabled (pwr_lim_en=0), set to 1.5-3x TDP |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify `socket_rapl_pl4_control` register has correct defaults: `pwr_lim_en=0` (not enforced by default), `pwr_lim` set to 1.5–3× TDP, `lock=0` (unlocked). PL4 is the hardware power cap; verifying its register state confirms correct BIOS initialization. NWP: single IMH0.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` reachable |
| Platform S0 | Fully booted |
| BIOS | BIOS must not lock PL4 for this test |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Read PL4 control register and verify defaults. `pl4 = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl4_control; en=pl4.pwr_lim_en.read(); lim=pl4.pwr_lim.read(); lock=pl4.lock.read(); pl1=sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control.pwr_lim.read(); pwr_unit=8; ratio=(lim/pwr_unit)/(pl1/pwr_unit); print(f'en={en} lim={lim/pwr_unit:.1f}W lock={lock} ratio={ratio:.2f}x'); assert en==0; assert lock==0; assert 1.5<=ratio<=3.0` | pwr_lim_en=0; lock=0; ratio 1.5–3× TDP | en=1 — PL4 unexpectedly enabled; lock=1 — BIOS locked; ratio OOR — check fuse |

---

### Pass / Fail Criteria

- **PASS**: `pwr_lim_en=0`; `lock=0`; PL4 power 1.5–3× TDP.
- **FAIL**: Any field out of expected state.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| socket_rapl_pl4_control | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl4_control | pwr_lim_en=0; lock=0; pwr_lim=1.5–3×TDP |

---

### Post-Process

No writes performed. Collect register state if any assertion fails.

---

### References

- [DMR PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/dmr_pmax.html) — PL4 control; pwr_lim_en default; lock semantics
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — TPMI PL4 encoding

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

PL4 is the hardware power limit for PMAX. By default, `pwr_lim_en = 0` (not enforced) but `pwr_lim` is set to 1.5-3× TDP. When enabled, PL4 triggers PMAX throttle when power exceeds PL4.

Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p pmax -tM 60
```

### NWP PL4 Register Verification
```python
# NWP: PL4 power limit register
pl4 = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl4_control
pl4.show()

# Read TDP (PL1) for comparison
pl1_pwr = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control.pwr_lim.read()
pl4_pwr = pl4.pwr_lim.read()

pwr_unit = 8  # verify against power_unit register
tdp_watts = pl1_pwr / pwr_unit
pl4_watts = pl4_pwr / pwr_unit
print(f"TDP: {tdp_watts}W, PL4: {pl4_watts}W, Ratio: {pl4_watts/tdp_watts:.2f}x")

# Verify ratio 1.5-3x TDP
assert 1.5 <= (pl4_watts / tdp_watts) <= 3.0, "PL4 must be 1.5-3x TDP"
```

### Pass Criteria
- `pwr_lim_en = 0` by default (PMAX not enabled by PL4 path at runtime)
- `pwr_lim` set to 1.5-3× TDP (accounts for power unit)
- `lock = 0` (register not locked by BIOS)

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; `sv.socket0.imh0.*` only; verify PL4:TDP ratio for NWP TDP spec values**

**Priority**: Medium — `plc.feature.p2`; PL4 default programming determines the overcurrent threshold for PMAX protection
