# Deep Analysis: RAPL PL1/PL2 Limits and Tau Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422034 |
| **Title** | RAPL PL1/PL2 limits and Tau Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | PL1/PL2 register programming — lock bit, tau, clamp bit, default values |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **PL1 and PL2 register programming** using both TPMI and CSR:
1. Lock bit functionality — when set, prevents further writes
2. PL1 and PL2 tau programming per spec (default values)
3. Clamp bit functionality — enables clamping below Pn
4. PL1 and PL2 power programming

NWP register paths directly shown in test steps:
- TPMI: `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control`
- TPMI: `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl2_control`
- CSR: `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_rapl_limit_cfg`

Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP RAPL Limit Registers

| Function | TPMI Register | CSR Register |
|----------|---------------|-------------|
| PL1 limit | `ptpcfsms.socket_rapl_pl1_control.pl1_power` | `ptpcioregs.package_rapl_limit_cfg.pl1_power` |
| PL1 tau | `ptpcfsms.socket_rapl_pl1_control.tau1` | `ptpcioregs.package_rapl_limit_cfg.tau1` |
| PL1 lock | `ptpcfsms.socket_rapl_pl1_control.lock` | `ptpcioregs.package_rapl_limit_cfg.lock` |
| PL1 clamp | `ptpcfsms.socket_rapl_pl1_control.clamp` | — |
| PL2 limit | `ptpcfsms.socket_rapl_pl2_control.pl2_power` | — |
| PL2 tau | `ptpcfsms.socket_rapl_pl2_control.tau2` | — |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run cpu_rapl PMx | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| 2 | Read PL1/PL2 defaults from TPMI | Verify match fuse-driven defaults |
| 3 | **Lock bit test**: set lock=1 | `socket_rapl_pl1_control.lock.write(1)` |
| 4 | Attempt PL1 write while locked | Write PL1 value; read back — should be unchanged |
| 5 | **Tau programming**: write valid tau | Tau per spec encoding; read back matches |
| 6 | **Clamp bit test**: set clamp=1 | Enable below-Pn clamp; verify behavior |
| 7 | **PL1/PL2 programming**: set custom values | Verify RAPL enforces custom PL1/PL2 |

### Pass Criteria
- Lock bit = 1: subsequent PL1/PL2 writes rejected (read-back unchanged)
- Tau programming: written tau encoding reflected in register; RAPL uses correct tau
- Clamp bit: enables below-Pn throttle when set
- PL1/PL2 custom values: RAPL algorithm enforces programmed limits

---

## Section D: Key Registers & Validation Points

```python
# NWP PL1/PL2 verification
pl1_reg = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control
pl2_reg = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_pl2_control
csr_reg = sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_rapl_limit_cfg

pl1_reg.show()  # Show all fields: pl1_power, tau1, lock, clamp
pl2_reg.show()  # Show all fields: pl2_power, tau2
csr_reg.show()  # Show CSR equivalent
```

---

## Section F: Recommendation

**Recommendation: ADOPT — NWP register paths already in `imh0` space; test all 4 aspects: lock, tau, clamp, programming**

1. `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3`
2. Verify via TPMI (`ptpcfsms`) and CSR (`ptpcioregs`) paths
3. Test all 4 aspects: lock bit, tau programming, clamp bit, PL1/PL2 custom values

**Priority**: High — `plc.feature.p2`; PL1/PL2 register programming is the fundamental RAPL control interface; lock/clamp validation critical for system security and stability
