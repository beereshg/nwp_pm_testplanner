# SoC Thermal > VR Hot

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SoC Thermal](soc_thermal_main.md)

## Baseline (DMR)

**What it does**: Two-tier VR thermal protection: **Thermal Alert** (~97% TEMP_MAX) → SOC throttles all domains to P1 via HPM; **VR_HOT** (100% TEMP_MAX) → VR asserts `VR_HOT#` ORed to `xxPROCHOT_N` → full PROCHOT fast_throttle flow.

**Topology**:
```
MBVR ──SVID STATUS1[ThermAlert] (polled)──> IMH PrimeCode
  └── HPM DNS_EVENT_DELIVERY[VR_THERM_ALERT] ─> CBB0..N + IMH1
       CBB PCode: VrThermalAlert::vr_thermal_alert_tx()
         └── slow_limits.set_ccp_limit(VR_THERMAL_ALERT_CCP_ID, P1)
         └── PLR HOT_VR (bit 26) + PLATFORM (bit 4)
MBVR ──VR_HOT# ──ORed──> XX_PROCHOT_N pkg bump ──> IMH GPIO ──> yy_prochot_n (D2D)
         └── CBB Punit fast_throttle (~20nS HW) → PCode PROCHOT flow
```

**Key operational principle**: CBB dies never directly poll VRs — all SVID communication goes through IMH PrimeCode which distributes via HPM. VR Hot does NOT wake from PkgC. Disable via `MSR_POWER_CTL[VR_THERM_ALERT_DISABLE]` (bit 24). SVID ThermAlert bit is sticky — clears only when VR cools below hysteresis threshold (~3% zone).

**Boot activation**: IMH PrimeCode SVID polling active from PH2.52 (SVID bus initialized). Fast_throttle path (VR_HOT → PROCHOT) active from power-on.

VR (Voltage Regulator) has layered thermal protection to prevent overheating: 1. **VR Hot / Thermal Alert (~97% TEMP_MAX)**: VR sets `SVID_STATUS[ThermAlert]` → SOC throttles to P1 2. **VR_HOT (100% / Prochot)**: VR asserts `VR_HOT#` → ORed to `xxPROCHOT_N` pin → full Prochot flow

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| MBVR (VCCIN_EHV0/1, VCCFA_EHV) | Platform | External VRs polled by IMH PrimeCode via SVID bus; `STATUS1[ThermAlert]` bit asserted at ~97% TEMP_MAX; `VR_HOT#` pin asserted at 100% | SVID bus; Alert# line; VR_HOT# GPIO | [VR14 Spec](http://goto/vr14spec) |
| SVID bus | IMH→MBVR | IMH PrimeCode polls all MBVRs for ThermAlert; CBB never polls directly (FIVR input VR only) | SVID `SVID_VR_STATUS` register | CBB Thermal Mgmt HAS |
| XX_PROCHOT_N package bump | IMH0 | VR_HOT# ORed to package PROCHOT input; triggers full PROCHOT fast_throttle flow | GPIO bump; `yy_prochot_n` D2D wire | DMR SoC Thermal HAS |
| CBB Punit fast_throttle | CBB Top Die | Asserted ~20nS on `yy_prochot_n` from PROCHOT/VR_HOT path | `fast_throttle` wire | CBB P-State Stack HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core PMA | No VR Hot role; receives fast_throttle from CBB Punit HW | — | — |
| PCode (CBB) | CBB Base Die | Receives HPM `DNS_EVENT_DELIVERY[VR_THERM_ALERT]` from IMH; runs `VrThermalAlert::vr_thermal_alert_tx()`; clamps CCP+Ring to P1 via slow_limits; sets PLR `HOT_VR` (bit 26) + `PLATFORM` (bit 4); de-asserts on HPM cleared | `VrThermalAlert::vr_thermal_alert_tx()`; `slow_limits.set_ccp_limit(VR_THERMAL_ALERT_CCP_ID, guaranteed)` | CBB Thermal Mgmt HAS |
| PrimeCode (IMH) | IMH die | Polls all MBVRs via SVID each slow-loop; detects ThermAlert; sends HPM `DNS_EVENT_DELIVERY[VR_THERM_ALERT]` to all CBBs + other IMH; limits fabric freq to P1; gates HPM on `MSR_POWER_CTL[VR_THERM_ALERT_DISABLE]` | `SVID_VR_STATUS`; HPM `DNS_EVENT_DELIVERY`; `hot_vr.cpp` | [DMR D2D Perimeter HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/D2D/DMR_D2D_Perimeter.html#vr-hot) |
| BIOS / UEFI | Platform | Programs `MSR_POWER_CTL[VR_THERM_ALERT_DISABLE]` if needed; no active VR Hot handling during runtime | Boot-time MSR config | Intel SDM |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `MSR_POWER_CTL` | 0x1FC | RW | [24] `VR_THERM_ALERT_DISABLE` — prevents IMH from sending VR_THERM_ALERT HPM | Intel SDM |
| MSR `CORE_PERF_LIMIT_REASONS` | 0x64F | RO/RWC | [4] `PLATFORM` (coarse PLR); [26] `HOT_VR` (fine-grain) — set during Thermal Alert P1 clamp | Intel SDM |
| PMT `PEM_STATUS` | 0x2E840 | RO | `PEM_HOT_VR` bit — current VR Hot excursion status | [NWP CBB Telemetry Aggregator HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/NWP_CBB_Telemetry/TelemetryAggregator_CBB_NWP.html) |
| PMT `PEM_COUNTER_*` | 0x2E848+ | RO | `PEM_HOT_VR` counter — accumulated VR Hot excursion events | NWP CBB Telemetry Aggregator HAS |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| SVID ThermAlert threshold | ~97 | % TEMP_MAX | VR14 Zone 6; hysteresis ~3% zone before de-assertion | [VR14 Spec](http://goto/vr14spec) |
| VR_HOT# assertion threshold | 100 | % TEMP_MAX | Tolerance ±4% (±4°C); optimized for 90–120°C range | [VR14 Spec](http://goto/vr14spec) |
| IMH SVID polling period | ~1 | mS | PrimeCode slow-loop; no SVID PM_EVENT notification (polling only) | Legacy Execution Flow |
| HPM propagation latency (ThermAlert) | ~1 | mS | IMH detects → `DNS_EVENT_DELIVERY` → CBB PCode acts | Legacy Execution Flow |
| VR_HOT → fast_throttle latency | ~20 | nS | VR_HOT# → PROCHOT pin → D2D GPIO → CBB Punit HW; no firmware in path | Legacy Architecture Summary |
| P1 clamping scope (Thermal Alert) | All CCPs + Ring + Fabric | — | IMH and CBB both clamp to guaranteed ratio (P1) | Legacy Execution Flow |
| SVID ThermAlert sticky | Until VR cools below hysteresis | — | Not cleared by `GetReg(Status1)` — only by temperature drop | Legacy Architecture Summary |

## NWP Delta

**VR thermal (VR HOT, VR alert) is supported on NWP** with platform changes per [NWP PAS](https://docs.intel.com/documents/custom-xeon/newport-docs/platform/pas/nwppas.html).

### Platform Changes
- **PMIC** (on-module VR controller) has its own integrated thermal sensor and protection
- PMIC does **not** have VR_HOT output visible to platform (unlike DDR4 MBVR)
- Platform thermal management FW must characterize **DIMM TSOD** data as proxy for PMIC and DRAM thermal events
- PMIC shutdown temperature (125°C) >> DRAM max temperature (95°C) → DRAM throttling expected before PMIC shutdown

### Functional Changes
- SVID VR thermal alert flow preserved: SVID STATUS1[THERMALERT] → PrimeCode HPM DNS_EVENT_DELIVERY
- VR_HOT/PROCHOT flow preserved at NIO level (single die)
- Each NIO has its own SVID_VR_STATUS instance (no dual-IMH coordination needed)

### Validation Impact
- VR HOT detection/assertion: verify NIO SVID_VR_STATUS handling (single die)
- PMIC thermal protection: platform-level test (not SoC FV scope, but document dependency)
- DIMM TSOD proxy validation: platform team responsibility
- No dual-IMH VR HOT coordination to test

## Legacy (Human-Curated Reference)

### Architecture Summary

VR (Voltage Regulator) has layered thermal protection to prevent overheating:
1. **VR Hot / Thermal Alert (~97% TEMP_MAX)**: VR sets `SVID_STATUS[ThermAlert]` → SOC throttles to P1
2. **VR_HOT (100% / Prochot)**: VR asserts `VR_HOT#` → ORed to `xxPROCHOT_N` pin → full Prochot flow

The VR Hot **action** does not change from GNR, but the **communication** across dies is different (HPM-based D2D messaging).

#### VR Internal Thermal Zones

Per the [VR14 Spec](http://goto/vr14spec), the SVID VR has progressive thermal protection:

```
 Temperature Zones (approximate)
 ┌─────────────────────────────────────────────┐
 │ Zone 0-5 : Operating (below ~94% TEMP_MAX)  │
 ├─────────────────────────────────────────────┤
 │ Zone 6 (Bit 6) : SVID Thermal Alert         │
 │   ~97% TEMP_MAX — STATUS1[ThermAlert]=1      │
 │   Alert# line asserted, stays sticky         │
 │   Hysteresis: ~3% or 1 temp zone tick        │
 ├─────────────────────────────────────────────┤
 │ VR_HOT# : 100% TEMP_MAX                     │
 │   VR_HOT# pin asserted → ORed to xxPROCHOT  │
 │   Tolerance: ±4% (±4°C, optimized 90-120°C)  │
 │   Hysteresis: ~3% or ~3°C from ThermAlert    │
 └─────────────────────────────────────────────┘
```

- The VR thermal sensor is **external to the PWM control IC** (located near heat-generating components)
- **Temperature Zone register**: Optional SVID register indicating proximity to VR_HOT# trip point, updated asynchronously with the SVID bus
- SVID ThermAlert bit is **not cleared** by a GetReg(Status1) command — it is a sticky bit that toggles only when VR temperature cools below the hysteresis threshold

#### CBB FIVR→MBVR Indirection

**CBB dies do not own SVID communication directly.** Core and Ring voltages are driven by in-die FIVRs, whose input voltage comes from `VCCIN_EHV0/1` MBVRs. Therefore:
- VR Hot for CBB is **never a direct CBB↔VR communication**
- CBB receives VR Hot indication **only through iMH HPM messages** (`DNS_EVENT_DELIVERY[VR_THERM_ALERT]`)
- The MBVRs that can trigger VR Hot are polled by iMH PrimeCode over the SVID bus, not by CBB PCode

**Key behaviors:**
- VR Hot actions are taken **across all dies in the socket** regardless of which VR asserts ThermAlert
- PkgC × VRHot: VR Hot does **not** cause a PkgC wake — in PkgC, cores are in C6 and fabric clock-gated, so throttling cannot help
- Can be disabled via `MSR_POWER_CTL[VR_THERM_ALERT_DISABLE]`

### Execution Flow

#### VR Hot Detection (Thermal Alert — ~97% TEMP_MAX)
1. **Polling**: Both IMH PrimeCodes poll their respective MBVR stack via `SVID_VR_STATUS` register for SVID ALERTs (periodic slow loop — not relying on SVID PM_EVENT notification)
2. **VR assertion**: When VR temperature exceeds ~97% of `TEMP_MAX`, MBVR sets `STATUS1[ThermAlert]` bit (bit 1) and asserts the Alert# line
3. **HPM propagation**: IMH PrimeCode detects VRHot → sends HPM `DNS_EVENT_DELIVERY` with `VR_THERM_ALERT` bit set to:
   - Its leaf CBB dies
   - The other IMH die
4. **Disable check**: PrimeCode will **not** send the `VR_THERM_ALERT` HPM if `MSR_POWER_CTL[VR_THERM_ALERT_DISABLE]` (bit 24) is set

#### VR Hot Action (Thermal Alert)
- **IMH die**: PrimeCode limits max fabric frequency to **P1** (guaranteed ratio); logs `MSR_CORE_PERF_LIMIT_REASONS[PLATFORM]` and `MSR_RING_PERF_LIMIT_REASONS[PLATFORM]` (not `[PROCHOT_STATUS]`)
- **CBB die**: PCode handler `VrThermalAlert::vr_thermal_alert_tx()` sets CCP+Ring to P1 via `slow_limits.set_ccp_limit(VR_THERMAL_ALERT_CCP_ID, guaranteed)`
- **PLR (Core)**: Sets `HOT_VR` (bit 26 fine-grain) and `PLATFORM` (bit 4 coarse) in `CORE_PERF_LIMIT_REASONS`
- **PLR (Ring)**: Sets corresponding bits in `RING_PERF_LIMIT_REASONS`
- **PLR (Die-level)**: CBB aggregates Core+Ring reasons into TPMI CRs `PLR_*` and HPM `LEAF_PERF_STATUS` for Root consumption

#### VR_HOT (Prochot — 100% TEMP_MAX)

If Thermal Alert actions didn't cool the VR, and temperature reaches 100% TEMP_MAX:
1. **VR asserts `VR_HOT#`** → ORed to `xxPROCHOT_N` on the platform
2. **iMH asserts `yyProchot` D2D wire** to all CBBs
3. **CBB HW fast_throttle**: Punit asserts fast_throttle wire → Core clock division + CCF serial debug mode (CCF data stalling, command each 3rd/5th/7th/.../15th cycle)
4. **PCode applies frequency limits**: Per `PROCHOT_POWER_LIMITED_FREQ_LIMIT` HPM message — Core fields: `CDYN_INDEX_*_LIMIT`; Ring field: `CBB_FABRIC_LIMIT`
5. **PCode masks fast_throttle** once the Core WP is applied

See also: [Prochot](prochot.md) for the full Prochot flow details.

#### VR Hot De-assertion
1. VR temperature cools → MBVR clears `STATUS1[ThermAlert]`
2. IMH PrimeCode detects status change → sends HPM `DNS_EVENT_DELIVERY` with `VR_THERM_ALERT` cleared
3. All CBB die PCode removes core+ring frequency ceiling due to VR Hot and clears `HOT_VR` / `PLATFORM` in PLR

### Key Registers & Interfaces

| Register / Interface | Scope | Key Fields | Purpose |
|---|---|---|---|
| `SVID STATUS1` | Per-VR | `ThermAlert` (bit 1), `VR Settled` (bit 0), `Icc-max Alert` (bit 2) | VR thermal/current alert status (polled via SVID bus) |
| `SVID Temperature Zone` | Per-VR | Zone bits [6:0] | Optional: indicates proximity to VR_HOT# (higher = hotter) |
| `MSR_POWER_CTL` (0x1FC) | Package | `VR_THERM_ALERT_DISABLE` (bit 24) | Disable VR Hot actions |
| `MSR_CORE_PERF_LIMIT_REASONS` | Package | `PLATFORM` (bit 4), `HOT_VR` (bit 26) | PLR reporting for VR Hot |
| `MSR_RING_PERF_LIMIT_REASONS` | Package | `PLATFORM` (bit 4) | Ring PLR reporting for VR Hot |
| HPM `DNS_EVENT_DELIVERY` | Root→All | `VR_THERM_ALERT` bit | Propagates VR Hot assertion/de-assertion across dies |
| HPM `LEAF_PERF_STATUS` | CBB→Root | Aggregated PLR bits | CBB reports aggregated core+ring limit reasons to Root |
| TPMI CRs `PLR_DIE_LEVEL` | Per-die | Die-level aggregated PLR | CBB die-level PLR (includes VR Hot bits) |
| PCode IO `IO_THROTTLE_INDICATIONS` | CBB Punit | PROCHOT cause | PCode reads to confirm Prochot source (VR_HOT vs external) |
| PCode IO `IO_FASTPATH_THERMAL` | CBB Punit | bit 0 | Fastpath interrupt on Prochot/VR_HOT fast_throttle |

#### PEM Telemetry for VR Hot Observability (CBB PMT)

The CBB Performance Excursion Monitor (PEM) tracks VR Hot excursion events via PMT registers:

| Register | SB Address | Description |
|----------|------------|-------------|
| `PEM_STATUS` | 0x2E840 | Current excursion status bits — includes `PEM_HOT_VR` |
| `PEM_COUNTER_*` | 0x2E848+ | Accumulated excursion counters per event type — `PEM_HOT_VR` counts VR thermal alert events |
| `PMAX_OVUV_HI_STATUS` | 0x2E870 | PMAX detector OV/UV fault counters — may indicate MBVR instability |
| `TOTAL_CBB_THROTTLED_TIME` | 0x2E890[63:32] | Time in ms below P1 due to thermal — non-zero during sustained VR Hot |

**Usage**: `PEM_HOT_VR` counter non-zero after a VR Hot event confirms CBB PCode received and acted on the `DNS_EVENT_DELIVERY[VR_THERM_ALERT]`. `TOTAL_CBB_THROTTLED_TIME` increasing during the event confirms P1 clamping was active.

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR SoC Thermal HAS — VR Hot](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html#vr-hot) | VR Hot flow section (iMH side) |
| HAS | [CBB Thermal HAS — VR HOT](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html#vr-hot-1) | CBB-side VR Hot overview, SVID zones |
| HAS | [CBB Thermal HAS — VR Thermal Alert](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html#vr-thermal-alert-therm_alert) | CBB-side PCode handler, PLR and frequency actions |
| HAS | [CBB Thermal HAS — VR_HOT (Prochot)](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html#vr_hot-prochot) | 100% TEMP_MAX → fast_throttle → Prochot flow |
| HAS | [DMR D2D Perimeter HAS — VR Hot](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/D2D/DMR_D2D_Perimeter.html#vr-hot) | Detailed iMH VR Hot flow |
| HAS | [NWP CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/NWP_CBB_Telemetry/TelemetryAggregator_CBB_NWP.html) | PEM_HOT_VR counters, PMAX_OVUV_HI_STATUS |
| HAS | [CBB PLR Resolving](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html#performance-limit-reasons-plr) | PLR bit definitions and CBB resolving logic |
| HAS | [CBB Pstate Stack — Prochot](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/P_State_Stack/p_state_stack.html#prochot) | Punit Prochot diagram (fast_throttle path) |
| Spec | [VR14 Spec](http://goto/vr14spec) | VR thermal zones, ThermAlert/VR_HOT# hysteresis, tolerance |
| MRF | [VR Hot flow MRF](https://hsdes-pre.intel.com/appstore/spark/mrf?id=1309637838&tenant=server_platf&family=1309245501) | Flow sequence diagram |
| FAS | [Pcode Thermal FAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/FAS/Thermals/Thermal%20Management_FAS.html) | PCode thermal management FAS (includes VR Hot) |
| PCode src | `source/pcode/flows/thermals/` | `VrThermalAlert::vr_thermal_alert_tx()` handler |
| Test scripts | TODO | |

#### Test Case Details

**22022421673 — Verify CBB VR Hot Actions**
- Trigger VR Hot via SVID status injection → verify CBB PCode sets core+fabric to P1 → verify PLR `HOT_VR` (bit 58) and `PLATFORM` (bit 4) set → de-assert → verify recovery

**22022421674 — Verify IMH VR Hot Actions**
- Trigger VR Hot → verify IMH PrimeCode limits fabric to P1 → verify HPM `DNS_EVENT_DELIVERY[VR_THERM_ALERT]` propagation to all dies → de-assert → verify recovery

**22022421676 — Verify VR_THERM_ALERT_DISABLE**
- Set `MSR_POWER_CTL[VR_THERM_ALERT_DISABLE]` → trigger VR Hot → verify NO throttling action taken → clear disable → re-trigger → verify throttle works

**22021969983 — [PSS] iMH North VR Hot Detection + PLR Bits**
- Trigger VR Hot on iMH North rail → verify PLR bit 58 (`HOT_VR`) set → verify frequency limited to P1 → de-assert → verify PLR clears and frequency recovers

### Related Sightings
<!-- TODO: Add sightings specific to this sub-feature -->

### NWP Delta

#### Feature Carry-Over
- **VR Hot Thermal Alert flow**: 100% PCode reuse — same `VrThermalAlert::vr_thermal_alert_tx()` handler, same HPM `DNS_EVENT_DELIVERY[VR_THERM_ALERT]` propagation
- **VR_HOT → Prochot escalation**: Same fast_throttle → PROCHOT_POWER_LIMITED_FREQ_LIMIT flow
- **PLR reporting**: Same bits — `HOT_VR` (bit 26), `PLATFORM` (bit 4) in Core and Ring PLR
- **PkgC × VRHot**: VR Hot does not cause PkgC wake — unchanged
- **PEM_HOT_VR telemetry**: Same PMT register structure for excursion counting

#### Topology Changes
- **Single NIO replaces dual IMH**: NIO PrimeCode is the sole SVID bus master polling all MBVRs. No IMH0↔IMH1 VR Hot HPM — NIO polls and distributes VR_THERM_ALERT to 2 CBBs.
- **LPDDR6 replaces DDR5**: LPDDR6 uses different MBVR topology — verify which MBVR stacks are polled and whether `SVID_VR_STATUS` addresses change.
- **Fewer CBB targets**: HPM `DNS_EVENT_DELIVERY` goes to 2 CBBs (vs DMR 4) — reduced fan-out.

#### NWP-Specific Risks
- NIO is a new die — SVID bus master routing, polling cadence, and HPM dispatch to CBBs must be validated.
- NWP removes accelerator IPs (DSA/IAA/QAT/DLB) — fewer MBVR domains; verify no stale VR polling addresses.
- `MSR_POWER_CTL[VR_THERM_ALERT_DISABLE]` behavior on NIO — must be validated (NIO is the only die processing this MSR for VR Hot).
- NWP CBB has 24 CCPs (vs DMR 32) — `VR_THERMAL_ALERT_CCP_ID` range in PCode may differ; verify P1 clamping applies to all 24 CCPs.
- PEM telemetry Product ID is NWP-specific (0x0AF) — ensure PEM_HOT_VR counter decode uses correct GUID.
