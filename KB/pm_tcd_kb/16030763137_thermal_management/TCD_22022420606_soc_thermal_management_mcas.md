# TCD: [SoC Thermal Management] MCAs

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420606](https://hsdes.intel.com/appstore/article-one/#/22022420606) |
| **Title** | [SoC Thermal Management] MCAs |
| **Status** | open |
| **Parent TP** | [16030763137 -- NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Feature** | SoC Thermal |
| **Sub-Feature** | Pcode MCA — DIE TOO HOT firmware MCA on POST_CATASTROPHIC_TEMPERATURE |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**SoC Thermal MCAs** covers the **firmware MCA generation path** for thermal fault reporting. When pCode detects a **"DIE TOO HOT"** overtemperature condition, it signals the MCA infrastructure via `IO_FIRMWARE_MCA_COMMAND`, and PUnit MCA hardware logs the event in the PUnit MC bank. This is a **reporting/logging/RAS path** — distinct from the thermal throttle chain.

**Key facts (from PUnit TRM + DMR CBB MCA FHAS + NWP RAS HAS):**
- pCode writes `IO_FIRMWARE_MCA_COMMAND` (addr `0xFB8EC`) to signal firmware-detected MCA
- `FIRMWARE_MCA_TYPE[7:0]` = thermal error code; `ERROR_TYPE[28:26]` = UC or UCNA
- PUnit MCA HW detects non-zero write → logs event in PUnit MC bank
- NWP MCA behavior follows **DMR SoC RAS MCA** model
- Thermal invalid-DTS condition post-PM-enable → UCNA (same infrastructure path)

### Block Diagram

```
  DTS / Thermal Sensors
         |  temperature inputs
         v
  PCode / Primecode Thermal Monitoring
         |  <--- Thermal Thresholds / Tjmax Policy
         |       die_max_temp >= critical threshold
         |
         v  overtemp detection: "DIE TOO HOT"
  Firmware MCA Logic
  IO_FIRMWARE_MCA_COMMAND (addr 0xFB8EC):
    FIRMWARE_MCA_TYPE[7:0]  = thermal error code
    ERROR_TYPE[28:26]       = 0=UC or 1=UCNA
    PCODE_GLOBAL_FATAL[31]  = fatal flag
         |
         v  firmware MCA event
  PUnit MC Bank (RAS / MCA reporting path)
  Logs event via architectural MCA registers
         |
         v
  TPMI / MSR / PMSB (visibility)
  IA32_MCi_STATUS, IA32_MCi_MISC

  FW also coordinates with:
  IMH / NIO Root Die + CBB0 / CBB1
```

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421547](https://hsdes.intel.com/appstore/article-one/#/22022421547) | [MCAs] Verify Pcode generates firmware MCA "DIE TOO HOT" | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Path | Purpose |
|-----------|------|--------|
| **`IO_FIRMWARE_MCA_COMMAND`** | Package CSR `0xFB8EC` | pCode writes to signal firmware MCA; TYPE[7:0], ERROR_TYPE[28:26] |
| **PUnit MC Bank** | MCA register path | Receives + logs firmware MCA; readable via `IA32_MCi_STATUS/MISC` |
| TPMI | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.*` | Thermal status registers |
| MSR | `IA32_MCi_STATUS`, `IA32_MCi_MISC` | MCA bank status after firmware MCA logged |
| PMSB | `sv.socket0.imh0.compute*.pma*.gpsb` | PMA-level thermal telemetry |
| DTS | Per-die DTS paths | Temperature source for overtemp classification |

---

## Section 3: Reset, Power, and Clocking

- Thermal DTS sensors initialize during PH1 (BIOS TPMI init); readings valid after PH6
- TCC threshold programmed by BIOS; runtime update via TPMI
- VR Hot and Prochot signals are asynchronous; PCode responds within 1 slow-loop (~1 ms)
- Thermal state persists across warm reset; cold reset re-initializes all thresholds

---

## Section 4: Programming Model

- BIOS programs TCC thresholds and thermal knobs during CPL3
- PCode slow-loop (~1 ms) polls thermal telemetry and applies throttle decisions
- OS reads thermal data via MSRs and TPMI; writes to override registers require privilege
- Test methodology: PMx `prochot_thermal` / `thermal_mgt` plugin or direct register injection

---

## Section 5: Operational Behavior

Thermal events trigger a response chain:
1. Hardware sensor (DTS / VR Hot / Prochot) asserts
2. PCode detects via PMSB poll or interrupt within 1 slow-loop
3. PCode applies throttle: reduce core/mesh frequency toward P1 or Pm
4. PCode reports via TPMI status registers and MSR thermal bits
5. On event clear: PCode ramps frequency back to autonomous level

All 1 TCs in this TCD validate different aspects of this chain for the **MCAs** scenario.

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| Die too hot condition before DTS valid / PM enabled | No false MCA until PM enable criteria met (telemetry valid) |
| Invalid DTS temperature after PM enabled | May trigger UCNA (thermal invalid), not DIE TOO HOT; distinguish in validation |
| Thermal condition clears before MCA is logged | MCA logging follows firmware sampling policy; no spurious duplicate |
| Persistent die-too-hot condition | Firmware may re-report per implementation policy; verify de-duplication behavior |
| Simultaneous throttle + MCA | Throttling and MCA logging are independent paths; both should activate |
| MCA logged early in reset sequence | PUnit MCA infra exists early; validation must account for reset-time semantics |

---

## Section 7: Security / Safety / Policy

- TCC thresholds may be BIOS-locked before OS handoff
- VR Hot and Prochot are safety-critical paths; test injection requires privileged access
- Thermal MSR overrides require OS privilege level

---

## Section 8: References

- [NWP RAS HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/ras/nwp_ras_has.html) -- NWP MCA behavior follows DMR SoC RAS MCA model
- [PUnit TRM](https://docs.intel.com/documents/sysip_pm/punit/trm/trm.html) -- `IO_FIRMWARE_MCA_COMMAND` register (addr 0xFB8EC); PUnit MC bank logging
- [DMR CBB MCA FHAS](https://docs.intel.com/documents/arch_datacenter/DMR/RAS/FHAS_CBB_MCA.html) -- Firmware MCA command fields; ERROR_TYPE encoding
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP SoC Thermal; thermal MCA scope
- [DMR SoC Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/thermals/dmr_thermal.html) -- Thermal MCA context; invalid-temperature UCNA path
