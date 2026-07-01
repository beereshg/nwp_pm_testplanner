# Deep Analysis: SVID Imon Telemetry Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421924 |
| **Title** | SVID Imon telemetry Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SVID |
| **Sub-Feature** | SVID Imon (current monitor) telemetry accuracy — per-VR current readings |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify SVID **Imon (current monitor)** telemetry readings from each VR are non-zero under active workload, within tolerance vs measured/expected values, and correctly accumulate in the `RC_MIO_EW` SVID accumulator entries (indexes 24-37). Imon accuracy is critical for RAPL power estimation and IccMax enforcement. NWP delta: **VCCC2C Imon is in `RC_CFCMEM_EW`** (not `RC_MIO_EW`); **VCCFA_EHV Imon absent** (rail removed).

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` reachable |
| Platform S0 | Fully booted; workload available (PTU or PTAT) |
| Imports | `import time` |
| Workload | Active load required to produce non-zero Imon readings |
| RC_MIO_EW | Primecode RC telemetry poll active |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Read Imon baseline at idle. `imh0 = sv.socket0.imh0; imon_vccin = imh0.pcudata.imon_reading.read(); print(f'IMH0 Imon baseline={imon_vccin}')` | Non-zero even at idle (standby current) | Zero — Imon telemetry path broken or VR not communicating |
| 2 | Start workload and read Imon from IMH0 and both CBBs under load. `# Start PTU/PTAT workload; import time; time.sleep(5); for i in [0,1]: imon=sv.socket0.cbb[i].base.pcudata.imon_reading.read(); print(f'CBB{i} Imon={imon}')` | Imon increases under load vs idle; both CBBs report current draw | Imon flat during workload — telemetry not updating; check RC_MIO_EW accumulator |
| 3 | Verify RC_MIO_EW SVID accumulator indexes 24-37 are updating. Key rails: VCCIN (idx 26-27), VCCANA (idx 28-29), VCCINF (idx 30-31). | SVID accumulator entries for active rails incrementing each telemetry poll (~1 ms) | Accumulators stuck — SVID polling not running; check Primecode telemetry init |
| 4 | Verify VCCC2C Imon appears in RC_CFCMEM_EW (not RC_MIO_EW). `# VCCC2C moved to RC_CFCMEM_EW on NWP; check CFCMEM accumulator for C2C rail` | VCCC2C current accumulator present and incrementing in RC_CFCMEM_EW | VCCC2C absent — C2C rail telemetry path not configured for NWP |
| 5 | Verify VCCFA_EHV Imon is absent from RC_MIO_EW. `# Legacy DMR VCCFA_EHV accumulator should not be present or should be zero` | No VCCFA_EHV accumulator entries in RC_MIO_EW | VCCFA_EHV still appearing — RC telemetry table not updated for NWP |
| 6 | Run PMx SVID Imon test. `python runPmx.py -x nwp.xml -p svid -p core_power -tM 60 -M 5` | PMx SVID Imon assertions PASS; within ±20% of expected | PMx FAIL — collect run log; identify which VR Imon out of tolerance |

---

### Pass / Fail Criteria

- **PASS**: All active VR Imon readings non-zero under load; within ±20% tolerance; RC_MIO_EW accumulators updating; VCCC2C in RC_CFCMEM_EW; VCCFA_EHV absent; PMx PASS.
- **FAIL**: Any Imon = 0 under workload; accumulator stuck; VCCC2C absent; VCCFA_EHV present; PMx FAIL.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| IMH0 Imon | sv.socket0.imh0.pcudata.imon_reading | Non-zero under workload |
| CBB0/1 Imon | sv.socket0.cbb{0,1}.base.pcudata.imon_reading | Non-zero; increases with load |
| RC_MIO_EW idx 26-27 (VCCIN) | sv.socket0.imh0 RC_MIO_EW SVID accum | Incrementing each ~1 ms poll |
| RC_CFCMEM_EW VCCC2C | sv.socket0.imh0 RC_CFCMEM_EW | VCCC2C Imon accumulator present |
| socket_rapl_energy_status | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_energy_status | Incrementing — Imon feeding RAPL power estimate |
| NLOG SVID | peg_client --nlog --filter SVID | No Imon telemetry errors |

---

### Post-Process

Stop workload. Collect NLOG if any accumulator stuck or Imon out of tolerance. Verify RAPL socket energy counter still incrementing post-test (Imon feeds RAPL).

---

### References

- [NWP PAS VR Table](https://docs.intel.com/documents/custom-xeon/newport-docs/platform/pas/NwpPAS.html) — NWP SVID rail map; ICCmax.max values per rail
- [NWP PM Telemetry — RC_MIO_EW SVID Accumulators](c:\github\nwp_testplan\KB\pm_features\nwp_architecture\nwp_nio_pm_telemetry.md) — SVID accumulator index 24-37; VCCFC_EHV removed; VCCC2C in RC_CFCMEM_EW
- [NWP HAS Impact §2.1](c:\github\nwp_testplan\KB\pm_features\nwp_architecture\nwp_has_impact_on_pm_fv.md) — add VCCC2C Imon telemetry (HSD 14027373379); remove VCCFA_EHV
- [Primecode RAPL DMR](https://docs.intel.com/documents/primecode/primecode_two/firmware_architecture/ip_drivers_and_libraries/rapl_dmr.html) — SVID IMON polling for RAPL socket power measurement
- [DMR SVID HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/svid/svid.html) — SVID Imon command (GetImon); calibration; tolerance spec

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Verifies SVID Imon (current monitor) telemetry readings from each VR. Imon values should be accurate and within tolerance vs actual measured current. Template content incomplete in source HSD.

Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP Command
```bash
python runPmx.py -x nwp.xml -p svid -p core_power -tM 60 -M 5
```

### NWP Imon Register Paths
```python
# NWP: 2 CBBs + 1 IMH
for cbb_idx in range(2):
    imon = sv.socket0.cbb[cbb_idx].base.pcudata.imon_reading
    print(f"CBB{cbb_idx} Imon: {imon}")

imh0_imon = sv.socket0.imh0.pcudata.imon_reading
print(f"IMH0 Imon: {imh0_imon}")
```

### Pass Criteria
- Imon readings non-zero under active workload
- Readings within ±20% of measured/expected values
- PMx SVID plugin Imon assertions pass

---

## Section F: Recommendation

**Recommendation: ADOPT — `nwp.xml`; NWP 2 CBBs + 1 IMH Imon paths; template incomplete — rely on PMx assertions for tolerance checks**

**Priority**: High — `PMSS_NWP_READINESS_CHECK`; Imon accuracy is required for RAPL power accounting and IccMax enforcement
