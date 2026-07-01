# TCD: SVID Basic Functionality Verification

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420771](https://hsdes.intel.com/appstore/article-one/#/22022420771) |
| **Title** | SVID Basic Functionality Verification |
| **Parent TPF** | [15019477949](https://hsdes.intel.com/appstore/article-one/#/15019477949) |
| **Feature** | SVID |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-07-01 |

## Section 1: Architecture / Micro-architecture and Functionality

**SVID (Serial Voltage ID)** is a 3-wire synchronous serial bus (VCLK, VDIO, ALERT#) connecting the NIO die (master) to all MBVR slave VRs. This TCD validates SVID **basic command functionality and register state**.

**NWP SVID rail map (NWP PAS):**

| Rail | SVID Address | Notes |
|------|-------------|-------|
| PVCCIN_EHV0 | 01h | Main input rail |
| PVCCANA0 | 02h | Analog PCIe G6 |
| PVCCINF | 03h | Infrastructure |
| **PVCCC2C** | **05h** | **NEW on NWP** |
| PVDD0 | TBD | LPDDR6 VDD0 |
| PVDD1 | TBD | LPDDR6 VDD1 |
| PVCC3P3_AUX | 0Dh | Psys sensor |
| **VCCFA_EHV** | **REMOVED** | **Not on SVID bus** |

**Key facts:** NIO is sole SVID bus master; VCCC2C added at 05h (HSD 14027373379); VCCFA_EHV removed (HSD 14027235624); BIOS initializes VR table at CPL3; Primecode polls IMON every ~1 ms for RAPL.

### Block Diagram

```
NIO die (SVID bus master)
SVID bus: VCLK / VDIO / ALERT#
  01h PVCCIN_EHV0 -> ACK
  02h PVCCANA0    -> ACK
  03h PVCCINF     -> ACK
  05h PVCCC2C     -> ACK (NEW)
  0Dh PVCC3P3_AUX -> ACK
  (VCCFA_EHV legacy addr) -> NACK
Commands: GetVID / SetVID / SetPS / GetImon / GetReg
```

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421917](https://hsdes.intel.com/appstore/article-one/#/22022421917) | SVID Basic commands functionality Verification | Runnable_On_N-1 |
| [22022421920](https://hsdes.intel.com/appstore/article-one/#/22022421920) | SVID Registers Verification | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| svid_control | sv.socket0.imh0.pcudata.svid_control | SVID bus config / operating mode |
| svid_status | sv.socket0.imh0.pcudata.svid_status | SBE / NACK / timeout flags |
| CBB svid_control | sv.socket0.cbb{0,1}.base.pcudata.svid_control | Per-CBB SVID operating mode |
| pmax_control | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.pmax_control | SVID-driven Vtrip offset; LOCK bit |
| RC_MIO_EW idx 24-37 | sv.socket0.imh0 RC_MIO_EW | SVID current accumulators feeding RAPL |
| RC_CFCMEM_EW VCCC2C | sv.socket0.imh0 RC_CFCMEM_EW | VCCC2C Imon/Pmon (new NWP rail) |

---

## Section 3: Reset, Power, and Clocking

- BIOS initializes SVID VR address table and control registers at CPL3
- SVID polling active after PH6; Primecode polls IMON ~1 ms for RAPL power estimate
- SVID_STATUS error bits cleared by firmware before OS handoff

---

## Section 4: Programming Model

- Commands: GetVID (read voltage), SetVID (set voltage), SetPS (power state), GetImon (current)
- Test: `python runPmx.py -x nwp.xml -p svid -p core_power -tM 60 -M 5`
- NWP: remove VCCFA_EHV from test scope; add VCCC2C at 05h; use `sv.socket0.imh0` (single IMH)

---

## Section 5: Operational Behavior

1. BIOS programs SVID VR table; Primecode validates via GetVID at boot
2. P-state transitions: Primecode issues SetVID to adjust VCCIN voltage
3. ~1 ms loop: GetImon from each rail; accumulate in RC_MIO_EW / RC_CFCMEM_EW
4. ALERT# assertion triggers error interrupt; firmware logs SVID_STATUS

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| SBE on GetVID | SVID_STATUS error bits set; firmware retries |
| VCCC2C NACK at 05h | BIOS VR table missing VCCC2C entry |
| VCCFA_EHV ACK received | DMR leftover config; must be fixed |
| GetVID returns 0 | VR off or bus error; check VR enable |

---

## Section 7: Security / Safety / Policy

- SVID commands are privileged; only Primecode/PCode issues at runtime
- OS cannot change SVID rail configuration after BIOS handoff

---

## Section 8: References

- [NWP PAS VR Table](https://docs.intel.com/documents/custom-xeon/newport-docs/platform/pas/NwpPAS.html) — NWP SVID addresses; VCCC2C/05h; VCCFA_EHV removed
- [10nm SVID HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SVID/10nm%20SVID%20HAS.html) — SVID commands (GetVID, SetVID, SetPS, GetImon); SBE handling; VRCI registers
- [SVID Standalone IP HAS](https://docs.intel.com/documents/sysip_pm/HAS_gen4/IPPUNIT-177_Feature_HAS.html) — Gen4 SVID CR list; SVID_CONFIG; SVID_STATUS; SVID_VR_ERROR_STATUS
- [Primecode RAPL DMR](https://docs.intel.com/documents/primecode/primecode_two/firmware_architecture/ip_drivers_and_libraries/rapl_dmr.html) — SVID IMON polling for RAPL NN-PID (1 ms cadence)
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — VCCC2C new SVID rail; VCCFA_EHV removed; RC telemetry changes
