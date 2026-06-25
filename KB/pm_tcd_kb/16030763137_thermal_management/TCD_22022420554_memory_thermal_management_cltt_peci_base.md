# TCD: [Memory Thermal Management] CLTT PECI based

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420554](https://hsdes.intel.com/appstore/article-one/#/22022420554) |
| **Title** | [Memory Thermal Management] CLTT PECI based |
| **Status** | open |
| **Parent TP** | [16030763137 -- NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Feature** | Memory Thermal |
| **Sub-Feature** | PECI-based CLTT — BMC writes DIMM temp via TPMI into MC registers |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**CLTT PECI-based Memory Thermal** covers hardware and firmware mechanisms for DIMM thermal monitoring via **PECI (Platform Environment Control Interface)**. Unlike MR4-based CLTT where the Memory Controller directly polls DIMMs, in the PECI path the **PECI interface carries DIMM thermal status and control information** from the platform thermal controller to the Memory Controller and IMH firmware agents. Primecode / PCode then enforce throttle limits on IMH and CBB dies.

On NWP: 2 CBBs + NIO/IMH-P root die (imh0 + imh1). PECI-based CLTT adds a platform-level thermal control path alongside local DTS / VR Hot / PROCHOT inputs.

### Block Diagram

```
  DIMMs / Memory Devices
         |  DIMM thermal data
         v
  Memory Controller (MC)          PECI / Platform Thermal Control
  (DIMM thermal update path) <--- (PECI-based thermal/control info)
         |  memory thermal status
         v
  IMH Root Die (imh0 + imh1) <------- Thermal Inputs
         |                            (DTS / VR Hot / PROCHOT)
         |  thermal telemetry / events        |
         v                            CBB0 <--+-- DTS/VR Hot/PROCHOT
  PCode / Primecode               CBB1 <--+-- DTS/VR Hot/PROCHOT
  Thermal Policy Agents                   |
    - Evaluate PECI + local thermal  die telemetry
    - Apply throttle policy               |
    - Cross-die coordination         (to FW)
         |
         +---- report -----> TPMI / MSR / PMSB
         |                  (status + observability)
         |
         +---- apply limits ----> IMH Root Die  (memory-side limits)
         +---- apply limits ----> CBB0           (compute-die limits)
         +---- apply limits ----> CBB1           (compute-die limits)
         |
         v
  Throttle / Limit Actions
  (freq reduction / thermal response)
```

### Feature Scope

| Layer | Component | Role |
|-------|-----------|------|
| Thermal source | DIMMs + PECI platform | DIMM temperature via PECI thermal path |
| Collection | MC + PECI interface | Receive PECI-based DIMM thermal info |
| Root die | IMH (imh0/imh1) | Aggregate memory thermal + local DTS/PROCHOT |
| Compute | CBB0, CBB1 | Receive propagated thermal limits; local DTS |
| Firmware | PCode / Primecode | Policy evaluation; throttle; HPM cross-die |
| Observability | TPMI / MSR / PMSB | Status readback for validation |

### PECI vs MR4 Comparison

| Aspect | CLTT MR4 | CLTT PECI |
|--------|----------|-----------|
| Thermal source | Direct DIMM MR4 reads by MC | Platform PECI path carries DIMM thermal status |
| Path | MC → IMH firmware | PECI → MC → IMH firmware |
| Latency | Direct, low-latency | Platform-mediated |
| NWP applicability | DDR5 native | Platform-dependent PECI support |

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421347](https://hsdes.intel.com/appstore/article-one/#/22022421347) | [PECI] Verify DIMM temp in MC is being updated by TPMI | Runnable_On_N-1 |
| [22022421352](https://hsdes.intel.com/appstore/article-one/#/22022421352) | [PECI] Verify DIMM thresholds match with default values prog | Runnable_On_N-1 |
| [22022421361](https://hsdes.intel.com/appstore/article-one/#/22022421361) | [PECI] Verify end to end functionality | Runnable_On_N-1 |
| [22022421372](https://hsdes.intel.com/appstore/article-one/#/22022421372) | [PECI] Verify DIMM throttle levels values match with default | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Path | Purpose |
|-----------|------|---------|
| **PECI** | Platform PECI bus → MC thermal path | PECI-based DIMM thermal status delivery (key for this TCD) |
| TPMI | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.*` | Thermal status, throttle registers (IMH-side) |
| MSR | Per-core/die MSRs (0x19C, 0x1A2, 0x1A3, 0x664, etc.) | Thermal status bits, DTS readings |
| PMSB | `sv.socket0.cbb0.compute*.pma*.gpsb` | PMA-level thermal telemetry |
| HPM | CBB ↔ IMH HPM messages | Cross-die thermal limit propagation |
| GPIO | IMH GPIO bumps | External VR Hot / PROCHOT input signals |

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

All 4 TCs in this TCD validate different aspects of this chain for the **CLTT PECI based** scenario.

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| Thermal event cleared before PCode responds | No false throttle; clean hysteresis exit |
| Multiple simultaneous thermal events | Priority arbitration; most restrictive wins |
| DTS reading at reset | Readings invalid until PH6 init complete |
| VR Hot on IMH vs CBB | Per-die scope; independent throttle paths |
| Throttle counter overflow | Software handles rollover; MSR is monotonic |

---

## Section 7: Security / Safety / Policy

- TCC thresholds may be BIOS-locked before OS handoff
- VR Hot and Prochot are safety-critical paths; test injection requires privileged access
- Thermal MSR overrides require OS privilege level

---

## Section 8: References

- [NWP PM MAS -- Memory Thermal](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- CLTT PECI scope, NWP memory thermal configuration
- [DMR DDR5/MCR HAS -- PECI CLTT](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/DMR_DDR5_MCR.html) -- PECI-based CLTT/memhot/memtrip for DDR5/MCR
- [Primecode Feature HAS Index](https://docs.intel.com/documents/primecode/fhas/index.html) -- SoC thermal flows; PECI-based DDR thermal management as Primecode feature area
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features) -- NWP memory thermal feature applicability
- [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html) -- Cross-die thermal limit propagation via HPM
