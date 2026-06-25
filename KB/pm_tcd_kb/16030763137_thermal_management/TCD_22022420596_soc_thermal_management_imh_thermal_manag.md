# TCD: [SoC Thermal Management] IMH Thermal Management

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420596](https://hsdes.intel.com/appstore/article-one/#/22022420596) |
| **Title** | [SoC Thermal Management] IMH Thermal Management |
| **Status** | open |
| **Parent TP** | [16030763137 -- NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Feature** | SoC Thermal |
| **Sub-Feature** | SoC Thermal |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**IMH Thermal Management** covers the **uncore thermal control** of the NIO/IMH root die. IMH thermal management uses a **PID-style throttle loop for local-die thermal excursions** and a **cold action ramp** to gradually relax throttle when the die cools. IMH thermal control is scoped to **IMH-local thermal conditions and fabric/mesh frequency limits** — not core thermal management (which is ACP).

**Key architectural facts (from DMR IMH Thermal + Primecode Thermal Docs):**
- IMH thermal management = limited to IMH die; actions to **fabric/uncore frequencies**
- If `die_max_temp >= trip_point + max_offset`: uncore limit drops directly to **minimum throttle ratio** (emergency)
- If `die_max_temp >= trip_point` and throttle already active: **hot action** (PID + strike counter)
- Otherwise: **cold action** — raise limit by 1 tick; reset strikes
- Result published as `global_thermal_uncore_ratio_limit`
- **OOS persistence:** `thermal_oos_counter` / `global_thermal_outofspec_timer_expired` after sustained throttle
- **Disable controls:** `PCODE_SYSTEM_MODES_CONTROL` bit 6 OR `FIRM_CONFIG` bit 4 cleared → throttle disabled; **risk: overheat critical condition**
- VR Hot path: if VR reaches thermal threshold → pCode receives `VR_THERM_ALERT` via HPM `DNS_EVENT_DELIVERY` → throttle CCPs/ring to P1 → if VR does not cool: `xxPROCHOT` asserted → more aggressive throttle

### Block Diagram

```
  IMH DTS / Thermal Sensors
         |  thermal sensing
         v
  IMH Thermal Controller (Uncore PID / cold action)
  +-- if temp >= trip + max_offset: EMERGENCY (drop to min throttle ratio)
  |-- if temp >= trip + throttle active: HOT ACTION (PID + strikes)
  |-- otherwise: COLD ACTION (raise limit 1 tick; reset strikes)
  |-- OOS counter if sustained throttle
  +-- DISABLE path:
      PCODE_SYSTEM_MODES_CTRL bit6 OR FIRM_CONFIG bit4 -> no throttle
         |  <--- Temperature Targets / Thermal Knobs (BIOS-programmed)
         |
         v  uncore throttle decision
  Uncore Throttle Actions (Fabric / mesh / IMH limits)
  global_thermal_uncore_ratio_limit
         |  applied thermal limits
         v
  PCode / Primecode / Punit Thermal Framework  <--- VR Hot / PROCHOT
         |  (VR alert: DNS_EVENT_DELIVERY VR_THERM_ALERT via HPM)
         |
         +---- thermal status / reasons ----> TPMI / MSR / PMSB
         +---- root-die coordination -------> IMH / NIO Root Die
         +---- cross-die coordination ------> CBB0 / CBB1
```

### Per-TC Behavior

| TC | Validates | IMH Thermal Path |
|----|-----------|-----------------|
| 22022421518 | Cold Action | Temp < trip point → limit raised 1 tick per loop; strike count reset |
| 22022421519 | Disable Uncore Throttling | `PCODE_SYSTEM_MODES_CTRL` bit 6 or `FIRM_CONFIG` bit 4 → throttle loop bypassed |
| 22022421520 | Uncore Throttling (PID) | Temp at/above trip → hot action PID → uncore ratio limited; verify `global_thermal_uncore_ratio_limit` |

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421518](https://hsdes.intel.com/appstore/article-one/#/22022421518) | [IMH Thermal Management] Verify Cold Action | Runnable_On_N-1 |
| [22022421519](https://hsdes.intel.com/appstore/article-one/#/22022421519) | [IMH Thermal Management] Verify Disabling Uncore Thermal Throttling | Runnable_On_N-1 |
| [22022421520](https://hsdes.intel.com/appstore/article-one/#/22022421520) | [IMH Thermal Management] Verify Uncore Throttling (PID) | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Path | Purpose |
|-----------|------|---------|
| **`global_thermal_uncore_ratio_limit`** | Primecode internal | Published uncore ratio limit from PID/cold-action output |
| **`PCODE_SYSTEM_MODES_CONTROL` bit 6** | Firmware CSR | Disable uncore thermal throttling (TC 22022421519) |
| **`FIRM_CONFIG` bit 4** | Firmware CSR | Alternate disable path for uncore throttling |
| TPMI | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.*` | Thermal status and throttle registers |
| MSR | Per-core/die MSRs (0x19C, 0x1A2, 0x1A3, 0x664, etc.) | Thermal status bits, DTS readings |
| PMSB | `sv.socket0.imh0.compute*.pma*.gpsb` | PMA-level thermal telemetry |
| HPM | `DNS_EVENT_DELIVERY` (VR_THERM_ALERT) | VR thermal alert delivery to pCode |
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

All 3 TCs in this TCD validate different aspects of this chain for the **IMH Thermal Management** scenario.

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| Throttling disabled, temperature rises above trip | No throttle from uncore path; safety-critical THERMTRIP still fires if catastrophic |
| Disable causes overheat | **Documentation warns: disabling EMTTM may result in overheat critical condition** |
| Temperature drops after hot-action throttle | Cold action engages; limit raised 1 tick/loop; strikes reset toward non-throttled state |
| Temperature at trip + max_offset | Emergency action: limit drops directly to minimum (no PID); fastest thermal protection |
| OOS counter reaches limit | `global_thermal_outofspec_timer_expired` asserts; report out-of-spec condition |
| VR thermal alert escalates to PROCHOT | pCode receives `VR_THERM_ALERT` via HPM; if VR doesn't cool: `xxPROCHOT` → more aggressive throttle |

---

## Section 7: Security / Safety / Policy

- TCC thresholds may be BIOS-locked before OS handoff
- VR Hot and Prochot are safety-critical paths; test injection requires privileged access
- Thermal MSR overrides require OS privilege level

---

## Section 8: References

- [DMR IMH Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/thermals/dmr_thermal.html) -- IMH thermal management scope; PID throttle; cold action; uncore frequency limits
- [Primecode Thermal Docs](https://docs.intel.com/documents/primecode/primecode_two/firmware_architecture/ip_drivers_and_libraries/thermals_page.html) -- UncoreThermalManagement class; disable controls; OOS timer; thermal vars
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP NIO DTS/thermtrip; IMH thermal scope; PROCHOT input behavior
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features) -- NWP IMH thermal feature applicability
- [Newport GPIO HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/gpio/newport_nio_gpio_has.html) -- PROCHOT_N input; VR_THERM_ALERT / DNS_EVENT_DELIVERY via HPM
