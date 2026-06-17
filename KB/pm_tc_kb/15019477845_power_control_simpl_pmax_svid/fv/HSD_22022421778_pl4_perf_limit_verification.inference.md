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
