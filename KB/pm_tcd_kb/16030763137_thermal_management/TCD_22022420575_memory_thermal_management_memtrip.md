# TCD: [Memory Thermal Management] Memtrip

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420575](https://hsdes.intel.com/appstore/article-one/#/22022420575) |
| **Title** | [Memory Thermal Management] Memtrip |
| **Status** | open |
| **Parent TP** | [16030763137 -- NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Feature** | Memory Thermal |
| **Sub-Feature** | Memtrip disable — verify MEMTRIP can be optionally disabled via `thermtrip_config_cfg` |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**Memtrip** is a **catastrophic memory thermal trip mechanism** — distinct from Memhot (corrective throttling) and CLTT (threshold-based throttling). Memtrip fires when DIMM temperature exceeds a catastrophic threshold that could cause **permanent system damage**. `MEMTRIP_N` is OR'd with `THERMTRIP_N` to trigger an immediate protective platform response.

**Key architectural facts (from Newport PM MAS + GPIO HAS):**
- Each MC compares MR4 temperature against a **catastrophic Memtrip threshold** programmed by BIOS
- Only the MC channels exceeding the threshold are throttled locally
- Die-level `MEMTRIP_N` = **OR of all MC channel Memtrip indications**
- PUnit asserts both **`MEMTRIP_N`** and **`THERMTRIP_N`** on internal Memtrip -- platform must execute protective shutdown
- `MEMTRIP_N` is a **separate pin** to distinguish memory-origin trip from CPU thermal trip
- Both MR4-based and PECI-based thermal sources can trigger Memtrip (separate TCs for each)

### Block Diagram

```
  DIMMs / Memory Devices
  Catastrophic temperature condition
         |
         |  MR4-based path          PECI-based path
         |  (TC 22022421434)         (TC 22022421439)
         v                                v
  Memory Controller (MC)
  Compare DIMM temp vs DIMM_TEMP_MEMTRIP_THRESHOLD
  (programmed by BIOS)
         |  if temp > threshold:
         |  throttle MC channel locally
         |  assert internal Memtrip
         v
  PCode / Punit
  Aggregate Memtrip from all MC channels
  Die-level Memtrip = OR of all MC Memtrip signals
         |
         +---- assert MEMTRIP_N ------> Platform / BMC
         |     (memory-origin trip     Protective shutdown /
         |      identification)        VR ramp-down
         |
         +---- assert THERMTRIP_N ---> Platform / BMC
               (OR'd with MEMTRIP_N    Hardware protection
                for immediate action)  immediate response

  Memtrip disable path (TC 22022421425):
  BIOS can disable MR4-based Memtrip source
  --> verify Memtrip not asserted when disabled

  Memtrip to Thermtrip path (TC 22022421437):
  Verify THERMTRIP_N asserts when MEMTRIP_N fires
  --> platform sees Thermtrip for catastrophic action
```

### Memtrip vs Memhot Comparison

| Feature | Memtrip | Memhot |
|---------|---------|--------|
| Severity | Catastrophic — permanent damage risk | Corrective — throttle to reduce temp |
| Action | Assert MEMTRIP_N + THERMTRIP_N → shutdown | Assert MEMHOT signal → fan ramp / throttle |
| Recovery | Platform shutdown/reset; no auto-recovery | Clears when temperature drops |
| Sources | MR4, PECI | MR4, PECI, GPIO MEMHOT_IN |
| BIOS threshold | `DIMM_TEMP_MEMTRIP_THRESHOLD` | `DIMM_TEMP_EV_OFST` thresholds |

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421425](https://hsdes.intel.com/appstore/article-one/#/22022421425) | [Memtrip] Disables Memtrip MR4-based | Runnable_On_N-1 |
| [22022421434](https://hsdes.intel.com/appstore/article-one/#/22022421434) | [Memtrip] MR4 based | Runnable_On_N-1 |
| [22022421437](https://hsdes.intel.com/appstore/article-one/#/22022421437) | [Memtrip] Memtrip to Thermtrip | Runnable_On_N-1 |
| [22022421439](https://hsdes.intel.com/appstore/article-one/#/22022421439) | [Memtrip] PECI based | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| **DIMM_TEMP_MEMTRIP_THRESHOLD** | MC CSR (`DIMM_TEMP_TH_0/1`) | Catastrophic DIMM temperature threshold (BIOS-programmed) |
| **MEMTRIP_N** | IMH GPIO | Package-level catastrophic memory trip signal |
| **THERMTRIP_N** | IMH GPIO | OR'd with MEMTRIP_N; triggers platform protective shutdown |
| MR4 thermal path | MC MR4 reads | DIMM temperature source for MR4-based Memtrip |
| PECI thermal path | PECI interface | DIMM temperature source for PECI-based Memtrip |
| TPMI | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.*` | Thermal status and throttle visibility |
| MSR | 0x19C, 0x1A2, 0x1A3, etc. | Thermal status bits |
| PMSB | `sv.socket0.cbb0.compute*.pma*.gpsb` | PMA-level telemetry |

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

All 4 TCs in this TCD validate different aspects of this chain for the **Memtrip** scenario.

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| Memtrip disabled, temperature still at threshold | `MEMTRIP_N` does NOT assert; no Thermtrip escalation |
| Only one MC channel at catastrophic threshold | Only that channel throttles locally; die-level `MEMTRIP_N` still asserts (OR logic) |
| Memtrip propagates to Thermtrip | `THERMTRIP_N` asserts; platform executes protective shutdown |
| MR4-based and PECI-based paths both active | Source selection / precedence follows BIOS programming |
| Catastrophic threshold exceeded transiently | Trip still asserted correctly; protective action not bypassed |
| Platform Thermtrip response varies by board | CPU-side Memtrip assertion is correct regardless of platform response |
| Memtrip source cleared after trip | Platform shutdown/reset occurs; system re-initialization required |

---

## Section 7: Security / Safety / Policy

- TCC thresholds may be BIOS-locked before OS handoff
- VR Hot and Prochot are safety-critical paths; test injection requires privileged access
- Thermal MSR overrides require OS privilege level

---

## Section 8: References

- [Newport NIO GPIO HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/gpio/newport_nio_gpio_has.html) -- MEMTRIP_N, THERMTRIP_N definitions; OR behavior; separate memory-trip pin
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- Memtrip generation, MC-local throttle, package signaling, Memtrip/Thermtrip assertion
- [Server Memory Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/memory_thermal/memory_thermals.html) -- Memtrip architecture, threshold aggregation, catastrophic trip behavior
- [DMR DDR5/MCR HAS -- Memtrip](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/DMR_DDR5_MCR.html) -- MR4-based CLTT/memhot/memtrip for DDR5/MCR
- [Primecode Feature HAS Index](https://docs.intel.com/documents/primecode/fhas/index.html) -- Memtrip as Primecode feature area; iMH thermal management
