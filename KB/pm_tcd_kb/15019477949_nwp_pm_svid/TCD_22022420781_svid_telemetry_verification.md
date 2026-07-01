# TCD: SVID Telemetry Verification

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420781](https://hsdes.intel.com/appstore/article-one/#/22022420781) |
| **Title** | SVID Telemetry Verification |
| **Parent TPF** | [15019477949](https://hsdes.intel.com/appstore/article-one/#/15019477949) |
| **Feature** | SVID |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-07-01 |

## Section 1: Architecture / Micro-architecture and Functionality

**SVID Telemetry** validates Imon (current) and Pmon (power = V x I) readings from each VR. SVID Imon is the primary input to Socket RAPL NN-PID — inaccurate Imon causes RAPL to mis-throttle.

**NWP telemetry changes:**
- VCCFC_EHV Imon/Pmon **REMOVED** from RC_MIO_EW (rail absent)
- VCCC2C Imon/Pmon **ADDED** in **RC_CFCMEM_EW** (not RC_MIO_EW)
- RC_MIO_EW SVID accumulator idx 24-37: VCCIN (26-27), VCCANA (28-29), VCCINF (30-31), PSYS_EHV (32-33)

### Block Diagram

```
NIO Primecode (~1 ms SVID poll)
    GetImon -> all active rails
    Accumulate in:
      RC_MIO_EW idx 24-37 (VCCIN, VCCANA, VCCINF, PSYS, VCCFIXDIG)
      RC_CFCMEM_EW        (VCCC2C -- new NWP rail)
    (VCCFA_EHV: REMOVED)
         |
         v
  socket_rapl_energy_status (RAPL NN-PID input)
  pkg_power_consumed (energy reporting)
```

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421924](https://hsdes.intel.com/appstore/article-one/#/22022421924) | SVID Imon Telemetry Verification | Runnable_On_N-1 |
| [22022421926](https://hsdes.intel.com/appstore/article-one/#/22022421926) | SVID Pmon Telemetry Verification | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| RC_MIO_EW idx 26-27 | sv.socket0.imh0 RC_MIO_EW | VCCIN I_OUT accumulator |
| RC_MIO_EW idx 28-29 | sv.socket0.imh0 RC_MIO_EW | VCCANA I_OUT accumulator |
| RC_MIO_EW idx 30-31 | sv.socket0.imh0 RC_MIO_EW | VCCINF I_OUT accumulator |
| RC_CFCMEM_EW VCCC2C | sv.socket0.imh0 RC_CFCMEM_EW | VCCC2C Imon/Pmon (NWP new) |
| socket_rapl_energy_status | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.socket_rapl_energy_status | RAPL counter fed by SVID Imon |
| imon_reading IMH0/CBBs | sv.socket0.imh0.pcudata.imon_reading | Per-die current reading |

---

## Section 3: Reset, Power, and Clocking

- SVID telemetry polling starts after PH6; ~1 ms cadence
- RC_MIO_EW SVID accumulators init to 0 at reset; increment each poll
- VCCC2C configured in RC_CFCMEM_EW separately from RC_MIO_EW

---

## Section 4: Programming Model

- SVID_IMON_MASK: bitmask for which rails are polled
- SVID_TELE_CFG / SVID_TELEMETRY_MAP_CFG: map rails to RC indexes
- Cross-check: RAPL energy_status rate should be within +-25% of Pmon sum

---

## Section 5: Operational Behavior

1. Primecode polls GetImon from each configured rail ~1 ms
2. Accumulated in RC_MIO_EW (idx 24-37) and RC_CFCMEM_EW (VCCC2C)
3. Pmon (P = V x I) computed; used for energy_status reporting
4. Test: workload -> verify accumulators incrementing -> RAPL cross-check

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| Imon = 0 under workload | Telemetry path broken; check SVID_IMON_MASK |
| VCCC2C absent from RC_CFCMEM_EW | C2C Imon not configured; RAPL underestimates |
| VCCFA_EHV in RC_MIO_EW | Stale DMR config; must be absent on NWP |
| RAPL/Pmon discrepancy > 25% | Imon calibration or scaling error |
| Accumulator stuck | SVID polling not running; check PH6 init |

---

## Section 7: Security / Safety / Policy

- Imon accuracy is safety-critical for RAPL throttling decisions
- Imon calibration fuses are OTP; errors require wafer-level fix

---

## Section 8: References

- [NWP PAS VR Table](https://docs.intel.com/documents/custom-xeon/newport-docs/platform/pas/NwpPAS.html) — NWP VR map; ICCmax.max per rail; Vnom for Pmon
- [10nm SVID HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SVID/10nm%20SVID%20HAS.html) — GetImon/GetPmon commands; IMON calibration; SVID_IMON_MASK; SVID_TELE_CFG
- [SVID Standalone IP HAS](https://docs.intel.com/documents/sysip_pm/HAS_gen4/IPPUNIT-177_Feature_HAS.html) — SVID telemetry configuration; SVID_TELEMETRY_MAP_CFG; push enable/masking
- [Primecode RAPL DMR](https://docs.intel.com/documents/primecode/primecode_two/firmware_architecture/ip_drivers_and_libraries/rapl_dmr.html) — SVID Imon polling (1 ms) as input to Socket RAPL NN-PID
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — RC_MIO_EW SVID accumulator idx map; VCCC2C in RC_CFCMEM_EW; VCCFC_EHV removed
