# Deep Analysis: SVID Pmon Telemetry Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421926 |
| **Title** | SVID Pmon Telemetry Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SVID |
| **Sub-Feature** | SVID Pmon (power monitor) telemetry accuracy — per-VR power readings |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify SVID **Pmon (power monitor)** telemetry readings from each VR reflect accurate per-VR power (P = V × I) under workload. Pmon feeds RAPL socket energy accounting: if Pmon is inaccurate, RAPL will over/under-throttle. NWP delta: **VCCC2C Pmon in RC_CFCMEM_EW**; **VCCFA_EHV Pmon absent**. Pmon is the primary input to PrimeCode Socket RAPL NN-PID power estimate.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` reachable |
| Platform S0 | Fully booted; workload available (PTU or PTAT) |
| RAPL enabled | Socket RAPL PL1/PL2 active (Primecode SVID polling running) |
| Imon passing | TC 22022421924 (Imon Verification) should pass first |
| Workload | Active load required for non-zero Pmon |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Read Pmon baseline at idle for IMH0. `imh0 = sv.socket0.imh0; pmon = imh0.pcudata.pmon_reading.read(); print(f'IMH0 Pmon baseline={pmon}')` | Non-zero at idle (standby power) | Zero — Pmon path broken or Vmon/Imon not combining |
| 2 | Start workload; read Pmon from IMH0 and both CBBs under load. `import time; time.sleep(5); for i in [0,1]: p=sv.socket0.cbb[i].base.pcudata.pmon_reading.read(); print(f'CBB{i} Pmon={p}')` | Pmon increases under load; both CBBs report power | Flat Pmon during workload — Imon or Vmon not updating |
| 3 | Cross-check: Pmon sum vs RAPL socket_rapl_energy_status rate. `rapl_e1 = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_energy_status.read(); import time; time.sleep(1.0); rapl_e2 = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_energy_status.read(); rapl_rate = (rapl_e2 - rapl_e1) / 8.0; print(f'RAPL rate ~{rapl_rate:.1f}W/s')` | RAPL energy rate consistent with Pmon power readings (±25%); confirms Pmon feeds RAPL accurately | Large discrepancy — Pmon scaling/calibration error |
| 4 | Verify VCCC2C Pmon in RC_CFCMEM_EW. `# Check RC_CFCMEM_EW for C2C rail power accumulator` | VCCC2C power accumulator present and incrementing | VCCC2C absent — C2C rail Pmon not configured |
| 5 | Verify VCCFA_EHV Pmon absent. | No VCCFA_EHV Pmon entries | VCCFA_EHV still present — stale DMR config |
| 6 | Run PMx SVID Pmon test. `python runPmx.py -x nwp.xml -p svid -p core_power -tM 60 -M 5` | PMx SVID Pmon assertions PASS | PMx FAIL — collect log |

---

### Pass / Fail Criteria

- **PASS**: All active VR Pmon non-zero under load; RAPL energy rate consistent with Pmon (±25%); VCCC2C in RC_CFCMEM_EW; VCCFA_EHV absent; PMx PASS.
- **FAIL**: Pmon = 0; RAPL/Pmon discrepancy > 25%; VCCC2C absent; VCCFA_EHV present; PMx FAIL.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| IMH0 Pmon | sv.socket0.imh0.pcudata.pmon_reading | Non-zero under workload |
| CBB0/1 Pmon | sv.socket0.cbb{0,1}.base.pcudata.pmon_reading | Non-zero; increases with load |
| socket_rapl_energy_status | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_energy_status | Incrementing; rate ±25% of Pmon sum |
| RC_CFCMEM_EW VCCC2C | sv.socket0.imh0 RC_CFCMEM_EW | VCCC2C power accumulator present |
| NLOG RAPL | peg_client --nlog --filter RAPL | No power-estimate errors |

---

### Post-Process

Stop workload. Verify RAPL energy counter continues incrementing. Collect NLOG on Pmon discrepancy. Report Pmon readings and RAPL rate on failure.

---

### References

- [NWP PAS VR Table](https://docs.intel.com/documents/custom-xeon/newport-docs/platform/pas/NwpPAS.html) — NWP SVID rails; Vnom per rail (needed for Pmon = V × I calculation)
- [NWP PM MAS — RC_MIO_EW SVID Accumulators](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — SVID accumulator map; VCCC2C in RC_CFCMEM_EW; VCCFA_EHV removed
- [NWP PM MAS — VCCC2C Pmon](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — add VCCC2C Pmon; remove VCCFA_EHV Pmon
- [Primecode RAPL DMR](https://docs.intel.com/documents/primecode/primecode_two/firmware_architecture/ip_drivers_and_libraries/rapl_dmr.html) — SVID Pmon as input to Socket RAPL NN-PID power estimate (1 ms polling)
- [10nm SVID HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SVID/10nm%20SVID%20HAS.html) — SVID Pmon command (GetPmon); P = V × I calculation; calibration; SVID_PWRIN_MASK register
- [IccMax Pmax Management HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Power%20Delivery/IccMax%20Pmax%20Management%20HAS.html) — DC loadline read from VCCIN VR via SVID (reg 23h+36h); Pmon for Pmax budgeting

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Verifies SVID Pmon (power monitor) telemetry from each VR. Pmon combines Vmon and Imon to compute per-VR power (P = V × I). Template content incomplete in source HSD.

Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP Command
```bash
python runPmx.py -x nwp.xml -p svid -p core_power -tM 60 -M 5
```

### NWP Pmon Register Paths
```python
# NWP: 2 CBBs + 1 IMH
for cbb_idx in range(2):
    pmon = sv.socket0.cbb[cbb_idx].base.pcudata.pmon_reading
    print(f"CBB{cbb_idx} Pmon: {pmon}")

imh0_pmon = sv.socket0.imh0.pcudata.pmon_reading
print(f"IMH0 Pmon: {imh0_pmon}")
```

### Pass Criteria
- Pmon readings non-zero under active workload
- Pmon consistent with known TDP/power estimates
- PMx SVID plugin Pmon assertions pass

---

## Section F: Recommendation

**Recommendation: ADOPT — `nwp.xml`; NWP 2 CBBs + 1 IMH Pmon paths; template incomplete — rely on PMx assertions; Pmon used for RAPL energy accounting accuracy**

**Priority**: High — `PMSS_NWP_READINESS_CHECK`; Pmon accuracy is foundational for RAPL power reporting
