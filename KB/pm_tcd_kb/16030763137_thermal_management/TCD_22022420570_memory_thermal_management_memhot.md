# TCD: [Memory Thermal Management] Memhot

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420570](https://hsdes.intel.com/appstore/article-one/#/22022420570) |
| **Title** | [Memory Thermal Management] Memhot |
| **Status** | open |
| **Parent TP** | [16030763137 -- NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Feature** | Memory Thermal |
| **Sub-Feature** | Memhot_In (MEMHOT_IN GPIO) — external thermal event throttles all MCs via Punit |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**Memory Thermal -- Memhot** covers two complementary hardware/firmware paths that protect the memory subsystem from overheating:

- **Memhot_In (`MEMHOT_IN_N`):** An **input pin** from an external platform agent (BMC, memory VR) that forces the Memory Controller to throttle DIMMs to a pre-programmed throttle level within **100 µs** of assertion. Fast-response emergency path.
- **Memhot_Out (`MEMHOT_OUT_N`):** An **output pin** driven by the MC when hottest-DIMM temperature (written by PCode into `MH_TEMP_STAT`) exceeds configured thresholds. Used by the platform for fan-speed / cooling response.

On NWP: 2 CBBs + NIO/IMH-P root die (imh0 + imh1). `MEMHOT_IN_N` is multiplexed with a strap pin during reset (acts as `XTAL_MODE0` until `GLOBAL_RESET_N`); Memhot functionality is only valid after reset release.

### Block Diagram

```
  External Agent / BMC / Memory VR
         |  external memhot assertion
         v
  MEMHOT_IN_N GPIO (IMH Root Die)
         |  MEMHOT_IN event
         v
  PUnit / PCode / Primecode
  Thermal policy + propagation
         |             |             |
         | propagate   | write       | status /
         | throttle    | hottest     | control
         | request     | DIMM info   |
         v             v             v
  Memory Controllers  MH_TEMP_STAT  TPMI / MSR / PMSB
  |  throttle DIMMs   |  threshold   Status + observability
  |  on MEMHOT_IN     |  basis
  v                   v
  DIMMs / DDR5 <---- (DIMM temp / MR4 data fed to FW)
         |
  Memory Controllers --> MEMHOT_OUT_N GPIO
                               |
                               v
                     Platform Cooling / Fan Control
                     (increase fan speed on MEMHOT_OUT)

  PCode also propagates to:
    IMH Root Die (root-die thermal control)
    CBB0 / CBB1 (cross-die thermal coordination)
```

### Memhot_In vs Memhot_Out

| Mode | Signal | Trigger | Action | Timing |
|------|--------|---------|--------|--------|
| Memhot_In | `MEMHOT_IN_N` (input) | External agent asserts | MC throttles DIMMs to pre-programmed level | < 100 µs response |
| Memhot_Out | `MEMHOT_OUT_N` (output) | DIMM temp > threshold in `MH_TEMP_STAT` | MC asserts output; platform increases cooling | Based on slow-loop |

### Key Registers

| Register | Purpose |
|----------|---------|
| `MH_TEMP_STAT` | Hottest DIMM temperature -- written by PCode for Memhot_Out generation |
| `DIMM_TEMP_EV_OFST` | Threshold enable bits for Memhot_Out assertion |
| `MEMHOT_EXT_THRT` | Per-MC Memhot throttle level configuration |

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421411](https://hsdes.intel.com/appstore/article-one/#/22022421411) | [Memhot] MR4 Verify Memhot_In mode functionality | Runnable_On_N-1 |
| [22022421412](https://hsdes.intel.com/appstore/article-one/#/22022421412) | [Memhot] MR4 Verify Memhot_Out mode functionality | Runnable_On_N-1 |
| [22022421415](https://hsdes.intel.com/appstore/article-one/#/22022421415) | [Memhot] Memhot Disables MR4-based | Runnable_On_N-1 |
| [22022421422](https://hsdes.intel.com/appstore/article-one/#/22022421422) | [Memhot] Verify Memhot_In mode functionality | Runnable_On_N-1 |
| [22022421423](https://hsdes.intel.com/appstore/article-one/#/22022421423) | [Memhot] Verify Memhot_Out mode functionality | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| **MEMHOT_IN_N** | IMH GPIO bump | External platform Memhot assertion (emergency input) |
| **MEMHOT_OUT_N** | IMH GPIO bump | Platform indication that memory is hot (cooling trigger) |
| **MH_TEMP_STAT** | MC CSR (written by PCode) | Hottest DIMM data for Memhot_Out threshold comparison |
| **DIMM_TEMP_EV_OFST** | MC CSR | Enable bits + offset for Memhot_Out assertion |
| TPMI | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.*` | Thermal status visibility |
| MSR | 0x19C, 0x1A2, 0x1A3, etc. | Thermal status bits |
| PMSB | `sv.socket0.cbb0.compute*.pma*.gpsb` | PMA-level thermal telemetry |
| HPM | CBB ↔ IMH HPM messages | Cross-die thermal coordination |

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

All 5 TCs in this TCD validate different aspects of this chain for the **Memhot** scenario.

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| `MEMHOT_IN_N` asserted during reset strap window | Pin acts as `XTAL_MODE0` strap; Memhot behavior only valid after `GLOBAL_RESET_N` release |
| External Memhot event clears before 100 µs | MC may not complete full throttle; verify exit behavior is clean |
| Hottest DIMM info stale in `MH_TEMP_STAT` | `MEMHOT_OUT_N` should not assert incorrectly; output depends on valid data from PCode |
| Memhot_In and MR4-based CLTT both active | Memhot takes precedence; MR4-based throttle disabled per TC 22022421415 |
| Platform ignores `MEMHOT_OUT_N` | CPU-side assertion still correct; fan/cooling is platform responsibility |
| Multiple DIMMs simultaneously above threshold | Hottest DIMM value used; `MH_TEMP_STAT` reflects maximum |
| `MEMHOT_IN_N` glitch (sub-µs pulse) | Verify no false persistent throttle; debounce or min-pulse requirements |

---

## Section 7: Security / Safety / Policy

- TCC thresholds may be BIOS-locked before OS handoff
- VR Hot and Prochot are safety-critical paths; test injection requires privileged access
- Thermal MSR overrides require OS privilege level

---

## Section 8: References

- [Newport NIO GPIO HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/gpio/newport_nio_gpio_has.html) -- MEMHOT_IN_N, MEMHOT_OUT_N signals; reset overlay; 100 µs response; MH_TEMP_STAT; DIMM_TEMP_EV_OFST
- [NWP PM MAS -- Memory Thermal](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- Memhot scope, NWP memory thermal
- [Server Memory Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/memory_thermal/memory_thermals.html) -- Memhot_In/Out purpose, architectural context, root-die propagation
- [DMR DDR5/MCR HAS -- Memhot](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/DMR_DDR5_MCR.html) -- MR4-based CLTT/memhot/memtrip for DDR5/MCR
- [Primecode Feature HAS Index](https://docs.intel.com/documents/primecode/fhas/index.html) -- SoC thermal flows; Memhot as Primecode feature area; iMH thermal management
