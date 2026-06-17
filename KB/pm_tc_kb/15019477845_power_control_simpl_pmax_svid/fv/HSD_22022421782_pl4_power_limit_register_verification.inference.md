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
