# TCD: [SoC Thermal Management] GPIO Interface

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420589](https://hsdes.intel.com/appstore/article-one/#/22022420589) |
| **Title** | [SoC Thermal Management] GPIO Interface |
| **Status** | open |
| **Parent TP** | [16030763137 -- NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Feature** | SoC Thermal |
| **Sub-Feature** | SoC Thermal |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**SoC Thermal GPIO Interface** covers the **package/platform-facing wire-level thermal signals** on NWP. These GPIO signals are the boundary between internal thermal detection/firmware policy and external platform protective actions. Each signal has distinct semantics, direction, and reset behavior (from Newport GPIO HAS + PM MAS).

### GPIO Thermal Signal Summary

| Signal | Direction | Purpose | Key Detail |
|--------|-----------|---------|-----------|
| `MEMHOT_IN_N` | **Input** | Platform requests memory throttle | Memory power must reduce within **100 µs**; overlaid on XTAL_MODE0 strap until GLOBAL_RESET_N |
| `MEMHOT_OUT_N` | **Output** | CPU indicates memory is hot | Driven when pCode writes hottest DIMM to `MH_TEMP_STAT` + MC compares vs `DIMM_TEMP_EV_OFST` |
| `MEMTRIP_N` | **Output** | Catastrophic memory temperature | OR'ed with `THERMTRIP_N`; separate pin to distinguish memory-origin vs CPU-origin trip |
| `PROCHOT_N` | **Input** | Platform triggers fast throttle | Sets `EXTERNAL_PROCHOT`; TCC active until deasserted; output mode removed on NWP (input only) |
| `THERMTRIP_N` | **Bi-directional** | Catastrophic CPU thermal | Wire-OR'd across dice; bidirectional so remote dielets sense assertion; must ignore until fuses downloaded + first measurement valid |
| GPIO bump fuses | — | Enable/disable each thermal bump | `PTPCFSMS_GPIO_BUMP_ENABLES_ENABLE_XX*_FUSE` per signal |

### Block Diagram

```
  GPIO Thermal Bump Enables (Fuses)
  PTPCFSMS_GPIO_BUMP_ENABLES_ENABLE_XXPROCHOT_N_FUSE
  PTPCFSMS_GPIO_BUMP_ENABLES_ENABLE_XXMEMHOT_IN/OUT_N_FUSE
  PTPCFSMS_GPIO_BUMP_ENABLES_ENABLE_XXMEMTRIP_N_FUSE
         |  bump enable configuration
         v
  Platform / BMC / VR / PCIe
         |                    |
  MEMHOT_IN_N (input)    PROCHOT_N (input)
         |                    |
         v                    v
  PCode / PMU / Punit Thermal Logic  <--- DTS / Thermal Diodes
         |  hottest DIMM / thermal policy
         v
  Memory Controller
         |                    |
  MEMHOT_OUT_N (output)  MEMTRIP_N (output)
         |                    |
         v                    v
  Platform                  Platform (+ OR'd with THERMTRIP)
  (fan ramp / cooling)      (memory-origin trip identification)

  PCode / PMU also:
         |  thermtrip request
         v
  THERMTRIP_N --> HWRS / Catastrophic Shutdown --> Platform

  PCode --> TPMI / MSR / PMSB (status / telemetry)
```

### Per-TC Signal Map

| TC | Signal | Validates |
|----|--------|-----------|
| 22022421480 | GPIO bump fuses | Fuse enables for MEMHOT_IN/OUT, MEMTRIP, PROCHOT bumps |
| 22022421481 | `MEMHOT_IN_N` | Platform asserts input; MC throttles DIMMs; 100 µs response |
| 22022421482 | `MEMHOT_OUT_N` | MH_TEMP_STAT + DIMM_TEMP_EV_OFST → MC asserts output; platform cooling |
| 22022421483 | `MEMTRIP_N` | Catastrophic DIMM temp → MEMTRIP asserts; OR'd with THERMTRIP |
| 22022421484 | `PROCHOT_N` | Platform asserts; EXTERNAL_PROCHOT set; TCC active until cleared |
| 22022421485 | `THERMTRIP_N` | DTS catastrophic → THERMTRIP propagates via wire-OR; HWRS action |

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421480](https://hsdes.intel.com/appstore/article-one/#/22022421480) | [GPIO Interface] Verify GPIO_BUMP Thermals fuses | Runnable_On_N-1 |
| [22022421481](https://hsdes.intel.com/appstore/article-one/#/22022421481) | [GPIO Interface] Verify XX_MEMHOT_IN_N input pin assertion | Runnable_On_N-1 |
| [22022421482](https://hsdes.intel.com/appstore/article-one/#/22022421482) | [GPIO Interface] Verify XX_MEMHOT_OUT_N output pin assertion | Runnable_On_N-1 |
| [22022421483](https://hsdes.intel.com/appstore/article-one/#/22022421483) | [GPIO Interface] Verify XX_MEMTRIP_N output pin assertion | Runnable_On_N-1 |
| [22022421484](https://hsdes.intel.com/appstore/article-one/#/22022421484) | [GPIO Interface] Verify XX_PROCHOT_N input pin assertion | Runnable_On_N-1 |
| [22022421485](https://hsdes.intel.com/appstore/article-one/#/22022421485) | [GPIO Interface] Verify XX_THERMTRIP_N input/output pin assertion | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Path | Purpose |
|-----------|------|---------|
| **GPIO bump fuses** | `sv.socket0.imh0.fuses.punit.ptpcfsms_gpio_bump_enables_enable_xx*` | Enable/disable per thermal GPIO bump |
| **MEMHOT_IN_N** | IMH package pin (input) | Platform → CPU: reduce memory power within 100 µs |
| **MEMHOT_OUT_N** | IMH package pin (output) | CPU → Platform: memory is hot (fan ramp) |
| **MEMTRIP_N** | IMH package pin (output) | CPU → Platform: catastrophic memory temp (OR'd with THERMTRIP) |
| **PROCHOT_N** | IMH package pin (input) | Platform → CPU: assert EXTERNAL_PROCHOT; TCC active |
| **THERMTRIP_N** | IMH package pin (bi-dir) | CPU ↔ Platform: catastrophic CPU temp; wire-OR; HWRS shutdown |
| TPMI | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.*` | Thermal status and throttle registers |
| MSR | Per-core/die MSRs (0x19C, 0x1A0, etc.) | Thermal status bits, PROCHOT indication |
| PMSB | `sv.socket0.imh0.compute*.pma*.gpsb` | PMA-level thermal telemetry |

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

All 6 TCs in this TCD validate different aspects of this chain for the **GPIO Interface** scenario.

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| `MEMHOT_IN_N` asserted during strap window | Pin behaves as XTAL_MODE0 until GLOBAL_RESET_N; Memhot only valid after reset |
| `THERMTRIP_N` observed before fuse download | Must be ignored until fuses loaded + first DTS measurement valid |
| `PROCHOT_N` held asserted | TCC remains active; no auto-deassert |
| GPIO bump fuse disabled for a signal | Corresponding signal path not expected to function |
| `MEMHOT_OUT_N` asserts with stale `MH_TEMP_STAT` | Should not assert based on stale hottest-DIMM data |
| Both `MEMTRIP_N` and `THERMTRIP_N` OR'd at platform | Platform cannot distinguish memory vs CPU trip via wire; MEMTRIP_N pin provides memory-origin identification |

---

## Section 7: Security / Safety / Policy

- These GPIO signals are **safety-critical platform interfaces** with hardware-driven semantics
- Input assertion (`MEMHOT_IN_N`, `PROCHOT_N`) may be asserted by external agents at any time; CPU must respond regardless of OS state
- Output signals (`MEMHOT_OUT_N`, `MEMTRIP_N`, `THERMTRIP_N`) are driven by hardware/firmware and indicate platform protection states
- GPIO bump fuse enables are one-time-programmable manufacturing controls; disabled bumps cannot be re-enabled at runtime
- Catastrophic paths (`THERMTRIP_N`, `MEMTRIP_N`) are not software-managed controls; platform protection is unconditional

---

## Section 8: References

- [Newport NIO GPIO HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/gpio/newport_nio_gpio_has.html) -- All 5 thermal GPIO signals; reset behavior; MEMHOT 100 µs requirement; THERMTRIP wire-OR; PROCHOT input-only on NWP
- [Punit Bump Enable Feature MAS](https://docs.intel.com/documents/sysip_pm/mas_wave4/feature_mas/punit_bump_enable_feature_mas/punit_bump_enable_feature_mas.html) -- PTPCFSMS_GPIO_BUMP_ENABLES_ENABLE_XX*_FUSE definitions (TC 22022421480)
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP thermal GPIO behavior; thermtrip chaining; MEMHOT/MEMTRIP/PROCHOT scope
- [DMR Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/thermals/dmr_thermal.html) -- DMR GPIO thermal interface context
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features) -- NWP thermal GPIO feature list
