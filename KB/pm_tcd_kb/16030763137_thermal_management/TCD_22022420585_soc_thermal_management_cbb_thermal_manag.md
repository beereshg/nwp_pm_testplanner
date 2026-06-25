# TCD: [SoC Thermal Management] CBB Thermal Management

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420585](https://hsdes.intel.com/appstore/article-one/#/22022420585) |
| **Title** | [SoC Thermal Management] CBB Thermal Management |
| **Status** | open |
| **Parent TP** | [16030763137 -- NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Feature** | SoC Thermal |
| **Sub-Feature** | SoC Thermal |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**CBB Thermal Management** covers the **CBB-autonomous EMTTM (Enhanced Multi-Throttle Thermal Management)** engine that controls CCF ring and core frequencies under thermal pressure. CBB EMTTM runs **four transactions per slow loop** — `sampler_tx`, `calc_limit_tx`, `calc_ccp_limit_tx`, `commit_tx` — treating CCF/Ring, Inf, D2D, and Core as possible **cross-throttle initiators**.

**Key architectural facts (from DMR CBB Thermal HAS):**
- CBB runs EMTTM to control **CCF**; cross-throttle initiators: Inf, D2D, Core
- `sampler_tx`: samples DTS temp, cross-throttle requests, computes effective Tjmax
- `calc_limit_tx`: PID error vs target → thermal ratio limit with hysteresis
- `calc_ccp_limit_tx`: ring-to-core throttle mapping; core cross-throttle due to ring/CBB thermal
- `commit_tx`: writes slow thermal limits; asserts OOS indication after ~20 ms sustained throttle
- **Ring → Core cross-throttle:** when ring throttles, pCode lowers core freq to match ring bandwidth
- **Core → Core cross-throttle:** overheating core CCP → pCode throttles all cores/DCMs + Ring

### Block Diagram

```
  CBB DTS / Diode Topology
         |  thermal sensing
         v
  CBB EMTTM / Thermal Management Engine
  [sampler_tx]   <--- Cross-Throttle Initiators (Core/CCF/Inf/D2D)
                 <--- Temperature Target Handling (Tjmax + BIOS)
  [calc_limit_tx] : PID(temp_error, target) -> ratio limit + hysteresis
  [calc_ccp_limit_tx] : ring -> core cross-throttle limits
  [commit_tx]    : write slow limits; OOS after ~20 ms sustained throttle
         |
         v  autonomous throttle decision
  Soft Throttle Actions (Core / CCF / Ring)
         |  applied thermal limits
         v
  PCode / Punit / Primecode Thermal Framework  <--- VR Hot / PROCHOT
         |
         +---- report -----> TPMI / MSR / PMSB (status + PLR + OOS)
         +---- coordinate --> CBB0 / CBB1
         +---- coordinate --> IMH / NIO Root Die
```

### Per-TC Architecture Mapping

| TC | Validates | EMTTM Path |
|----|-----------|-----------|
| 22022421475 | CBB EMTTM Disable | Disable EMTTM; verify no autonomous throttle from `calc_limit_tx` |
| 22022421476 | EMTTM Soft Throttle | Temp above target → `calc_limit_tx` → `commit_tx` |
| 22022421477 | EMTTM Soft Throttle | Alternate throttle condition (may test OOS/persistence) |
| 22022421478 | Temperature Target Handling | Verify effective Tjmax computation in `sampler_tx` |
| 22022421479 | Core Cross Throttle Due to Ring | Ring throttles → `calc_ccp_limit_tx` → core ratio limit |

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421475](https://hsdes.intel.com/appstore/article-one/#/22022421475) | [CBB Thermal Management] Verify CBB EMTTM Disable | Runnable_On_N-1 |
| [22022421476](https://hsdes.intel.com/appstore/article-one/#/22022421476) | [CBB Thermal Management] Verify CBB EMTTM Soft Throttle | Runnable_On_N-1 |
| [22022421477](https://hsdes.intel.com/appstore/article-one/#/22022421477) | [CBB Thermal Management] Verify CBB EMTTM Soft Throttle | Runnable_On_N-1 |
| [22022421478](https://hsdes.intel.com/appstore/article-one/#/22022421478) | [CBB Thermal Management] Verify CBB Temperature Target Handling | Runnable_On_N-1 |
| [22022421479](https://hsdes.intel.com/appstore/article-one/#/22022421479) | [CBB Thermal Management] Verify Core Cross Throttle Due to Ring | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Path | Purpose |
|-----------|------|--------|
| **TPMI PLR** | `sv.socket0.cbbN.base.tpmi.plr_die_level` | Performance Limit Reason -- throttle cause |
| **TPMI OOS** | `sv.socket0.cbbN.base.tpmi.therm_status` | Out-of-spec persistence indicator (~20 ms) |
| **MSR 0x19C** | `IA32_THERM_STATUS` per core | Thermal status bits, DTS reading |
| **MSR 0x1A2** | `IA32_TEMPERATURE_TARGET` | Effective Tjmax / temperature target |
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

All 5 TCs in this TCD validate different aspects of this chain for the **CBB Thermal Management** scenario.

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| EMTTM disabled | No autonomous CBB throttle from EMTTM; safety-critical paths (VR Hot, Thermtrip) remain |
| Temperature briefly above target | Soft throttle engages and exits cleanly via hysteresis |
| Temperature sustained above target (~20 ms) | OOS persistence flag raised; `commit_tx` asserts OOS indicator |
| Ring cross-throttle causes core limit | `calc_ccp_limit_tx` maps ring condition to core ratio limit; PLR identifies ring |
| Core CCP overheats (core cross-throttle) | pCode throttles all cores/DCMs + Ring until core CCP request deasserts |
| Multiple cross-throttle initiators active | Most restrictive limit applied; all contributing PLR bits visible |
| Temperature target misconfigured | EMTTM uses fallback/safe Tjmax; validate Tjmax computation in sampler_tx |

---

## Section 7: Security / Safety / Policy

- TCC thresholds may be BIOS-locked before OS handoff
- VR Hot and Prochot are safety-critical paths; test injection requires privileged access
- Thermal MSR overrides require OS privilege level

---

## Section 8: References

- [DMR CBB Thermal Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/thermal_management/thermal_management.html) -- EMTTM transactions (sampler/calc/commit); cross-throttle; OOS persistence; VR Hot; Thermtrip topology
- [DMR CBB Thermal Management FAS](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/fas/thermals/thermal_management_fas.html) -- EMTTM detailed flow; ring-to-core cross-throttle; core CCP cross-throttle
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP SoC thermal scope; CBB EMTTM applicability
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features) -- NWP CBB thermal feature list
- [Primecode Feature HAS Index](https://docs.intel.com/documents/primecode/fhas/index.html) -- CBB EMTTM as Primecode feature area
