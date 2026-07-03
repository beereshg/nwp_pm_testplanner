# Deep Analysis: RAPL BIOS Knobs Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422018 |
| **Title** | RAPL BIOS Knobs Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | RAPL BIOS knob defaults + override verification |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **RAPL-related BIOS knobs**:
1. Default values match expected
2. Overriding knobs causes corresponding registers/limits to update correctly

BIOS knobs of interest (from GNR flexconSW-GNRSV.xml, adapted for NWP):

| # | BIOS Knob | Description | Default |
|---|-----------|-------------|---------|
| 1 | `TurboPowerLimitLock` | Enable/Disable locking of Package RAPL Limit MSR/TPMI | 0x0 (Disable) |
| 2 | `TurboPowerLimitCsrLock` | Enable/Disable locking of Package RAPL (CSR) | 0x0 (Disable) |
| + | Additional RAPL knobs | PL2 enable, tau, clamp, etc. | Per BIOS spec |

Tags: `DMR_PO`, `PMSS_NWP_READINESS_CHECK`. Uses `flexconPM.py`.

---

## Section B: NWP-Specific Test Procedure

### Flexcon Command (NWP)
```
flexconPM.py -c NWPSV.ini  (not DMRSV.ini)
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run flexconPM to check BIOS knob defaults | `flexconPM.py -c NWPSV.ini` |
| 2 | Verify `TurboPowerLimitLock` = 0x0 (disabled by default) | Check TPMI lock bit: `socket_rapl_pl1_control.lock` |
| 3 | Verify `TurboPowerLimitCsrLock` = 0x0 | Check CSR lock bit: `package_rapl_limit_cfg.lock` |
| 4 | Override each BIOS knob (e.g., set lock to 0x1) | BIOS knob write + reboot |
| 5 | Verify corresponding register/limit updated | Lock bit in TPMI/CSR register reflects BIOS knob |
| 6 | Verify locked registers cannot be overwritten by OS | Write while locked; read back — should be unchanged |

### NWP RAPL Lock Registers

| BIOS Knob | NWP TPMI Register | NWP CSR Register |
|-----------|-------------------|------------------|
| TurboPowerLimitLock | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control.lock` | — |
| TurboPowerLimitCsrLock | — | `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_rapl_limit_cfg.lock` |

### Pass Criteria
- All BIOS knob defaults match expected values for NWP platform
- Overriding each BIOS knob causes corresponding register to update
- Lock bit: once set, prevents further register writes until reset

---

## Section F: Recommendation

**Recommendation: ADOPT — `DMRSV.ini` → `NWPSV.ini`; adapt BIOS knob list from GNR to NWP flexconSW XML**

1. `flexconPM.py -c NWPSV.ini`
2. Verify all RAPL-related BIOS knob defaults for NWP
3. Test lock bit functionality via TPMI and CSR path
4. Use NWP flexcon config (`NWPSV.ini`) — not DMR or GNR configs

**Priority**: High — RAPL BIOS knob checkout is critical for bring-up; lock bits affect OS-level power capping capability
