# Deep Analysis: RAPL - Checkout Fuses Related to RAPL

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422017 |
| **Title** | RAPL - Checkout fuses related to RAPL |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | RAPL fuse checkout — verify fuses consumed by Pcode and reflected in mapped registers |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **RAPL-related fuses are consumed correctly by Pcode** and reflected in the associated registers. From test steps: MSR interface for RAPL is **deprecated in DMR** (and NWP) — MSRs `IA32_PKG_POWER_SKU_UNIT`, `PACKAGE_POWER_INFO`, `PACKAGE_RAPL_LIMIT`, `PACKAGE_ENERGY_STATUS` are superseded by TPMI/CSR registers.

Goal: Verify fuse values → Punit registers reflect correct fuse-driven defaults. Uses `flexconPM.py`. Tags: `DMR_PO`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP RAPL Fuse → Register Mapping

| Fuse | NWP Fuse Path | Register |
|------|---------------|---------|
| TDP (PL1 default) | `sv.socket0.imh0.fuses.punit.<tdp_fuse>` | `socket_rapl_pl1_control.pl1_power` |
| PL2 default | `sv.socket0.imh0.fuses.punit.<pl2_fuse>` | `socket_rapl_pl2_control.pl2_power` |
| Tau1 (PL1 tau) | `sv.socket0.imh0.fuses.punit.<tau1_fuse>` | `socket_rapl_pl1_control.tau1` |
| Power Unit | `sv.socket0.imh0.fuses.punit.<power_unit>` | `socket_rapl_power_unit.power_units` |

### Flexcon Command (NWP)
```
flexconPM.py -c NWPSV.ini  (not DMRSV.ini)
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Read NWP RAPL fuses | `sv.socket0.imh0.fuses.punit.<rapl_fuse_fields>` |
| 2 | Run flexconPM | `flexconPM.py -c NWPSV.ini` |
| 3 | Verify PL1 register = fuse-driven TDP | TPMI: `socket_rapl_pl1_control.pl1_power` |
| 4 | Verify PL2 register = fuse-driven PL2 | TPMI: `socket_rapl_pl2_control.pl2_power` |
| 5 | Verify Power Unit register correct | TPMI: `socket_rapl_power_unit` |
| 6 | Verify deprecated MSRs have no effect | Write to legacy RAPL MSRs; verify no register change |

### NWP Notes
- MSR interface deprecated on NWP (same as DMR)
- TPMI registers: `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.*`
- CSR registers: `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.*`
- `DMRSV.ini` → `NWPSV.ini` for Flexcon

### Pass Criteria
- All RAPL registers initialized to fuse-driven values after reset
- Deprecated MSRs: write has no effect on TPMI/CSR register values
- Flexcon verification passes for all RAPL fuse → register mappings

---

## Section F: Recommendation

**Recommendation: ADOPT — `DMRSV.ini` → `NWPSV.ini`; NWP RAPL fuse paths at `imh0.fuses.punit.*`; MSR deprecated same as DMR**

1. `flexconPM.py -c NWPSV.ini`
2. Read NWP RAPL fuses from `sv.socket0.imh0.fuses.punit.*`
3. Verify TPMI/CSR RAPL registers match fuse-driven values
4. Confirm deprecated MSR writes have no effect

**Priority**: High — RAPL fuse checkout is a fundamental bring-up validation step to confirm Pcode correctly consumed all RAPL fuses
