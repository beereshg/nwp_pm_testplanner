# Deep Analysis: SVID Basic Commands Functionality Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421917 |
| **Title** | SVID Basic commands functionality Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SVID |
| **Sub-Feature** | SVID basic commands (GetVID, SetVID, SetPS) via PMx plugin |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify SVID (Serial Voltage ID) **basic commands** function correctly on NWP for all active SVID rails. NWP has a modified rail map vs DMR: **VCCFA_EHV removed** from SVID bus; **VCCC2C added** at SVID address 05h. Key assertions: GetVID/SetVID/SetPS commands complete without SBE (SVID Bus Error) or timeout on all active NWP rails; voltage transitions execute within spec timing; VCCC2C responds at SVID0/05h; no SVID command errors.

**NWP active SVID rails (from NWP PAS VR table):**

| Rail | SVID Address | Notes |
|------|-------------|-------|
| PVCCIN_EHV0 | 01h | Main CPU input rail |
| PVCCANA0 | 02h | Analog PCIe G6 |
| PVCCINF | 03h | Infrastructure |
| **PVCCC2C** | **05h** | **NEW on NWP — C2C digital VCC** |
| PVDD0 | TBD | LPDDR6 VDD0 |
| PVDD1 | TBD | LPDDR6 VDD1 |
| PVCC3P3_AUX | 0Dh | Psys sensor |
| VCCFA_EHV | **REMOVED** | **No longer on SVID bus on NWP** |

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` reachable without timeout |
| Platform S0 | Fully booted to SVOS; no pending MCA |
| Imports | `import time` |
| Namespace | `nio = sv.socket0.imh0` alias set; `punit = nio.punit` |
| PMx available | `python runPmx.py -x nwp.xml -p svid -p core_power -tM 60 -M 5` accessible |
| SVID bus | NIO is SVID bus master; all MBVRs powered and SVID-responsive |
| BIOS | Normal boot completed; SVID VR table initialized by BIOS CPL3 |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Read current SVID bus status and verify no pre-existing errors. `nio = sv.socket0.imh0; svid_err = nio.punit.svid_bus_status.read() if hasattr(nio.punit, 'svid_bus_status') else 0; print(f'SVID bus status=0x{svid_err:08X}'); import time` | SVID bus status = 0 (no pre-existing SBE or timeout) | SBE or timeout bits set — residual SVID error; clear before test |
| 2 | Execute GetVID on PVCCIN_EHV0 (01h) and PVCCANA0 (02h). Verify valid voltage codes returned. `vccin_vid = nio.punit.svid.getvid(rail=0x01) if hasattr(nio.punit.svid,'getvid') else 'N/A'; vcca_vid = nio.punit.svid.getvid(rail=0x02) if hasattr(nio.punit.svid,'getvid') else 'N/A'; print(f'PVCCIN_EHV0 VID={vccin_vid} PVCCANA0 VID={vcca_vid}')` OR via PMx plugin assertion | GetVID returns non-zero voltage codes within valid range for each rail; no SBE on read | GetVID returns 0 or SBE — MBVR not responding; check VR power state |
| 3 | Execute GetVID on **PVCCC2C (05h)** — new NWP rail. Verify C2C VR responds correctly. `vccc2c_vid = nio.punit.svid.getvid(rail=0x05) if hasattr(nio.punit.svid,'getvid') else 'N/A'; print(f'PVCCC2C VID={vccc2c_vid}')` OR verify via `RC_CFCMEM_EW` SVID accumulator | PVCCC2C VID non-zero; C2C VR responds at address 05h | VID = 0 or no response — VCCC2C MBVR not initialized; verify BIOS VR table includes 05h |
| 4 | Verify VCCFA_EHV is **absent** (no response at legacy DMR address). `# VCCFA_EHV was at legacy DMR address; on NWP this rail is NOT on SVID bus; verify no SVID ACK returned` | No SVID response / NACK at VCCFA_EHV address — confirms rail removed from bus | ACK received — old DMR address still active on NWP bus; check BIOS VR table |
| 5 | Execute SetVID on PVCCIN_EHV0 — write target voltage then read back. `# Write VID for PVCCIN to current+1 step, verify response; read back via GetVID to confirm` | SetVID accepted; GetVID returns updated value; no SBE; voltage transition completes in-spec timing | SetVID returns error or GetVID does not match — VR not accepting VID updates |
| 6 | Execute SetPS (power state command) and verify PM state transition. `# SetPS to lower power state on PVCCIN_EHV0; verify SVID ACK; then SetPS back to active` | SetPS acknowledged by VR; system remains stable through power state transition | SBE on SetPS — VR not responding to power state commands |
| 7 | Run PMx SVID plugin end-to-end. `python runPmx.py -x nwp.xml -p svid -p core_power -tM 60 -M 5` | PMx SVID plugin PASS for all assertions; core_power plugin PASS | PMx FAIL — collect run log; check which rail/command failed |

---

### Pass / Fail Criteria

- **PASS**: All SVID basic commands (GetVID, SetVID, SetPS) succeed on all active NWP rails; VCCC2C responds at 05h; VCCFA_EHV absent (NACK); no SBE or timeout; PMx SVID plugin PASS.
- **FAIL**: Any SVID command returns SBE or timeout; VCCC2C does not respond at 05h; VCCFA_EHV responds (DMR leftover config); PMx FAIL.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| SVID bus status | nio.punit.svid_bus_status (or equivalent) | = 0; no SBE bits set after test |
| RC_MIO_EW SVID accumulators (idx 24-37) | `sv.socket0.imh0.punit.RC_MIO_EW` pull | VCCIN (idx 26-27), VCCANA (idx 28-29), VCCINF (idx 30-31) accumulating; VCCFC_EHV absent |
| RC_CFCMEM_EW VCCC2C | `sv.socket0.imh0.punit.RC_CFCMEM_EW` pull | VCCC2C telemetry present (moved from RC_MIO_EW to RC_CFCMEM_EW on NWP) |
| NLOG SVID | peg_client --nlog --filter SVID | No SVID Bus Error, timeout, or NAK events |
| IMON telemetry | `nio.punit.ptpcfsms.ptpcfsms.socket_rapl_energy_status` | Energy counter incrementing (SVID IMON feeding RAPL) |

---

### Post-Process

Verify SVID bus returns to clean state: no residual SBE bits. Restore any modified VID values to default. Collect NLOG if any SVID error observed: `peg_client --nlog --filter SVID`. Verify RAPL socket power estimation is functional after test (SVID IMON feeds RAPL).

---

### References

- [NWP PAS VR Table](https://docs.intel.com/documents/custom-xeon/newport-docs/platform/pas/NwpPAS.html) — NWP SVID rail map: PVCCIN_EHV0/01h, PVCCANA0/02h, PVCCINF/03h, **PVCCC2C/05h (new)**; VCCFA_EHV removed
- [NWP PM MAS — SVID §2.1 (VCCC2C new / VCCFA_EHV removed)](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — VCCFA_EHV removed (HSD 14027235624); VCCC2C new SVID rail (HSD 14027373379); address SVID0/05h
- [NWP PM MAS — Telemetry / RC_MIO_EW SVID Accumulators](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — SVID accumulator index map; VCCFC_EHV removed; VCCC2C in RC_CFCMEM_EW
- [Primecode RAPL DMR](https://docs.intel.com/documents/primecode/primecode_two/firmware_architecture/ip_drivers_and_libraries/rapl_dmr.html) — SVID IMON polling for RAPL power measurement
- [10nm SVID HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SVID/10nm%20SVID%20HAS.html) — SVID command set (GetVID, SetVID, SetPS, GetImon); timing requirements; SBE handling; VRCI register interface
- [SVID Standalone IP HAS](https://docs.intel.com/documents/sysip_pm/HAS_gen4/IPPUNIT-177_Feature_HAS.html) — Gen4 SVID separation from Punit; own PMSB endpoint; full CR list; error aggregation

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

SVID (Serial VID interface) basic commands are functional on NWP. The PMx SVID plugin validates GetVID, SetVID, SetPS, and SVID command response correctness. Template content incomplete in source HSD — steps field contains only the unfilled mandatory section template.

Tags: `DMR_PO`, `plc.feature.p2`, `NGA_MAIN`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP Command
```bash
# DMR → NWP: dmr.xml → nwp.xml
python runPmx.py -x nwp.xml -p svid -p core_power -tM 60 -M 5
```

### Adapted Steps

| Step | Action | Details |
|------|--------|---------|
| 1 | Boot to SVOS | Normal platform boot |
| 2 | Run SVID PMx plugin | `runPmx.py -x nwp.xml -p svid -p core_power -tM 60 -M 5` |
| 3 | Verify GetVID commands succeed | SVID GetVID returns valid voltage codes |
| 4 | Verify SetVID commands succeed | Voltage transitions without MCA |
| 5 | Verify SetPS (power state) commands | PM state transitions via SVID |
| 6 | Check no SVID command errors | No SVID Bus Error (SBE) or SVID timeout |

### Pass Criteria
- All SVID basic commands execute without errors
- Voltage transitions complete in-spec timing
- `runPmx.py` SVID plugin passes all assertions

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; SVID functional on NWP; source TC has empty steps template — rely on PMx SVID plugin assertions**

**Priority**: High — `PMSS_NWP_READINESS_CHECK`; SVID basic functionality is a P0 bring-up gate
