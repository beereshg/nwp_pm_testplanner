# Deep Analysis: RAPL Energy Status Reporting

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422023 |
| **Title** | RAPL Energy status reporting |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | RAPL energy status accuracy at idle and under workload |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **RAPL energy status reporting** accuracy:
1. Check energy status at idle — measured power should match expected idle power
2. Run workload — energy status should match expected workload power
3. Simics setup references OakStream telemetry inject for VCCIN Iout (silicon: SVID IMON telemetry)

NWP register paths are directly shown in test steps (already NWP `imh0` paths):
- CSR: `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_energy_status_cfg`
- TPMI: `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_energy_status`

Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP Energy Status Registers

| Register | NWP Path |
|----------|----------|
| CSR energy status | `sv.socket0.imh0.punit.ptpcioregs.ptpcioregs.package_energy_status_cfg` |
| TPMI energy status | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_energy_status` |

### Adapted Steps (Simics → Silicon Adaptation)

| Step | Action | NWP Silicon Path |
|------|--------|-----------------|
| 1 | System at idle; read energy status | CSR + TPMI registers above |
| 2 | Compute idle power from energy delta/time | `power_W = (E2 - E1) / (t2 - t1) * energy_unit` |
| 3 | Compare to expected idle power | Should be within ±X% tolerance |
| 4 | Run workload (PTU TDP) | `./ptu -ct 3` across 96 cores |
| 5 | Read energy status under workload | Same CSR + TPMI registers |
| 6 | Compute workload power; compare to expected | Power should approach TDP |

### Silicon Telemetry Adaptation
- **Simics** (OakStream): `oakstream.mb.mcp0.vccin1->mbvr_injection_state = TRUE; mbvr_iout_inject_val = 50.0`
- **NWP Silicon**: Actual SVID IMON telemetry from VR hardware — no injection needed; measure real energy
- NWP: use SVID `IMON_TELEMETRY` register from VR or from Punit SVID_VR_STATUS for cross-reference

### Pass Criteria
- Idle energy status matches expected idle power (within ±10% or per spec tolerance)
- Workload energy status matches expected TDP power (within tolerance)
- CSR and TPMI energy status registers agree
- Energy status increments monotonically (no regression)

---

## Section D: Key Registers & Validation Points

```python
import time

# Read energy status at idle (NWP)
e1 = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_energy_status.read()
t1 = time.time()
time.sleep(1)
e2 = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_energy_status.read()
t2 = time.time()
# Power unit from socket_rapl_power_unit register
power_unit_J = <read from socket_rapl_power_unit>
idle_power_W = (e2 - e1) * power_unit_J / (t2 - t1)
print(f"Idle power: {idle_power_W:.1f} W")
```

---

## Section F: Recommendation

**Recommendation: ADOPT — Register paths already show NWP `imh0`; adapt Simics inject → use real SVID IMON on silicon**

1. `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3`
2. NWP silicon: use real SVID IMON telemetry (not Simics injection)
3. Verify CSR and TPMI energy status agree; measure idle and workload power accuracy

**Priority**: High — `plc.feature.p2`; energy status reporting accuracy is fundamental to RAPL power management and telemetry
