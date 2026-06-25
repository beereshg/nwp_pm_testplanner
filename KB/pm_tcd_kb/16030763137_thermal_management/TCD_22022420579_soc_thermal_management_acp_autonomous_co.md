# TCD: [SoC Thermal Management] ACP (Autonomous Core Perimeter)

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420579](https://hsdes.intel.com/appstore/article-one/#/22022420579) |
| **Title** | [SoC Thermal Management] ACP (Autonomous Core Perimeter) |
| **Status** | open |
| **Parent TP** | [16030763137 -- NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Feature** | SoC Thermal |
| **Sub-Feature** | SoC Thermal |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**ACP (Autonomous Core Perimeter)** is the **core-autonomous thermal management** component of the CBB thermal framework. ACP configures the **core temperature target**, operates **EMTTM (Enhanced Multi-Throttle Thermal Management)** to autonomously control core frequency under thermal pressure, handles **core cross-throttle** interactions with other CBB domains (CCF, Inf, D2D), and reports **performance/frequency limit reasons** to firmware and OS.

**Key architectural facts (from DMR CBB Thermal HAS):**
- CBB thermal management treats **CCF, Inf, D2D, and Core** as possible cross-throttle initiators
- ACP scope: configure core temperature target + report core perf limit reasons
- EMTTM includes **Autonomous ITD**, **Autonomous Thermal Control**, **Thermal Ceiling Throttling**, and **Autonomous EMTTM** — all enabled via the **Advanced Thermal Control** bit
- External VR Hot asserts fast throttle and triggers pCode-based prochot actions on core
- Thermal Reporting sends telemetry to root; calculates thermal monitor status
- Thermtrip topology uses daisy-chain aggregation through survivability filtering into PUnit

### Block Diagram

```
  Core Temperature Target Configuration
         |  temp target programming
         v
  ACP / Core Autonomous Thermal Logic  <--- Core DTS / Thermal Detectors
         |  <--- EMTTM / Advanced Thermal Control (Autonomous ITD, EMTTM,
         |        Thermal Ceiling Throttling -- enabled by AdvThermCtrl bit)
         |  <--- Cross-Throttle Initiators (CCF / Inf / D2D / Core)
         |
  local thermal status / limits
         |
         v
  PCode / Punit / Primecode Thermal Framework  <--- VR Hot / PROCHOT (external)
         |
         +---- report thermal info / PLR ----> TPMI / MSR / PMSB
         |                                     (PLR visibility, thermal info,
         |                                      freq reduction reasons)
         +---- die thermal coordination -----> CBB0
         +---- die thermal coordination -----> CBB1
         +---- package/root coordination ---> IMH / NIO Root Die
```

### Per-TC Architecture Mapping

| TC | What it validates | ACP Component |
|----|------------------|--------------| 
| 22022421444 | Core temperature target configuration | `TARGET` → ACP programming |
| 22022421445 | Core cross-throttle | `XTH` (CCF/Inf/D2D/Core) → ACP |
| 22022421452 | Core EMTTM disable | `EMTTM` Advanced Thermal Control bit |
| 22022421453 | Core thermal information | DTS + ACP → FW → TPMI readout |
| 22022421454 | Report frequency reduction reason | FW → PLR/MSR thermal reason bits |

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421444](https://hsdes.intel.com/appstore/article-one/#/22022421444) | [ACP] Verify Configuration of Core's Temperature Target | Runnable_On_N-1 |
| [22022421445](https://hsdes.intel.com/appstore/article-one/#/22022421445) | [ACP] Verify Core Cross Throttle | Runnable_On_N-1 |
| [22022421452](https://hsdes.intel.com/appstore/article-one/#/22022421452) | [ACP] Verify Core EMTTM Disable | Runnable_On_N-1 |
| [22022421453](https://hsdes.intel.com/appstore/article-one/#/22022421453) | [ACP] Verify Core Thermal Information | Runnable_On_N-1 |
| [22022421454](https://hsdes.intel.com/appstore/article-one/#/22022421454) | [ACP] Verify Report out of Frequency Reduction Reason | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Path | Purpose |
|-----------|------|---------|
| **TPMI PLR** | `sv.socket0.cbbN.base.tpmi.plr_die_level` | Performance Limit Reason -- TC 22022421454 |
| **Core temp target** | MSR `0x1A2` (`IA32_TEMPERATURE_TARGET`) | TCONTROL/TCC offset -- TC 22022421444 |
| **Core thermal status** | MSR `0x19C` (`IA32_THERM_STATUS`) | Thermal status bits, DTS reading -- TC 22022421453 |
| **Core throttle MSR** | MSR `0x1A0` (`IA32_MISC_ENABLES`) | EMTTM enable/disable -- TC 22022421452 |
| TPMI | `sv.socket0.cbbN.base.tpmi.*` | Thermal status and throttle registers |
| PMSB | `sv.socket0.cbbN.compute*.pma*.gpsb` | PMA-level thermal telemetry |
| HPM | CBB ↔ IMH HPM messages | Cross-die thermal limit propagation |
| GPIO | IMH GPIO bumps | VR Hot / PROCHOT external inputs |

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

All 5 TCs in this TCD validate different aspects of this chain for the **ACP (Autonomous Core Perimeter)** scenario.

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| Core temperature target misconfigured | ACP reflects programmed target or reverts to safe default; validate readback |
| EMTTM disabled while other thermal protections active | Safety-critical protections (Thermtrip, VR Hot) remain active; only autonomous throttling changes |
| Multiple cross-throttle initiators (CCF + Inf + Core) simultaneously | Most restrictive limit wins; PLR identifies all contributing sources |
| Cross-throttle event from outside local core domain | ACP still reports appropriate PLR; limit propagated correctly |
| PLR reason changes faster than software sampling rate | PLR bits may reflect transient causes; snapshot at relevant time |
| EMTTM disabled but TCC threshold exceeded | TCC-based protection still fires independently of EMTTM state |

---

## Section 7: Security / Safety / Policy

- TCC thresholds may be BIOS-locked before OS handoff
- VR Hot and Prochot are safety-critical paths; test injection requires privileged access
- Thermal MSR overrides require OS privilege level

---

## Section 8: References

- [DMR CBB Thermal Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/thermal_management/thermal_management.html) -- Core Thermal Management (ACP); EMTTM; cross-throttle initiators (CCF/Inf/D2D/Core); VR Hot; Thermal Reporting
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP SoC Thermal scope; ACP feature applicability
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features) -- NWP ACP/thermal feature list
- [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html) -- Cross-die thermal coordination; SoC thermal response chain
