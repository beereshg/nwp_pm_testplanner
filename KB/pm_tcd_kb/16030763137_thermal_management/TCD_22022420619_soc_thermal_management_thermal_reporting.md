# TCD: [SoC Thermal Management] Thermal Reporting

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420619](https://hsdes.intel.com/appstore/article-one/#/22022420619) |
| **Title** | [SoC Thermal Management] Thermal Reporting |
| **Status** | open |
| **Parent TP** | [16030763137 -- NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Feature** | SoC Thermal |
| **Sub-Feature** | CORE_PERF_LIMIT_REASONS (MSR 0x64F) |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**Thermal Reporting** is the architectural layer that exposes thermal state, thresholds, margins, and thermal limitation reasons through core/package MSRs and PM telemetry structures. This TCD validates **thermal observability** — not throttling action itself.

The reporting architecture spans two scopes:
- **Core-scoped:** per-core status/log, temperature margin, perf-limit reasons
- **Package-scoped:** die-aggregate thermal state, package temperature margin, HW feedback notification

**Key registers validated by this TCD:**

| Register | MSR | Scope | Key Fields |
|----------|-----|-------|------------|
| `IA32_THERM_STATUS` | 0x19C | Core | Thermal monitor, PROCHOT, OOS, Threshold1/2, Power Limit status/log, temperature, valid |
| `IA32_PACKAGE_THERM_STATUS` | 0x1B1 | Package | Package thermal monitor, PROCHOT, OOS, Threshold1/2, HW feedback notification log, temperature, valid |
| `IA32_TEMPERATURE_TARGET` | 0x1A2 | Package | TjMax, TCC offset, Fan temp target |
| `IA32_PACKAGE_THERM_MARGIN` | — | Package | Margin to Tcontrol, margin to TJMax |
| `MCP_THERMAL_REPORT_1` | 0x1A3 | Package | PMT telemetry mirror |
| `MCP_THERMAL_REPORT_2` | 0x1A4 | Package | PMT telemetry mirror |
| `CORE_PERF_LIMIT_REASONS` | 0x64F | Core | Thermal/PROCHOT/VR-cause perf-limit bits |
| `POWER_CTL` | 0x1FC | Package | `DIS_PROCHOT_OUT`, `PROCHOT_RESPONSE`, `PROCHOT_LOCK`, thermal control bits |
| `IA32_MISC_ENABLES` | 0x1A0 | Thread | Thermal monitor enable (TM1/TM2), enhanced Intel SpeedStep enable |

Sticky log bits preserve event history until software clear; some out-of-spec conditions are reset-cleared only. A `VALID` bit in status registers must be set before temperature fields are meaningful.

### Block Diagram

```
  DTS / Thermal Monitor / PROCHOT / VR Hot / TCC events
         |
         v
  PCode / Primecode Thermal Reporting Logic
  (updates architectural MSR surfaces)
         |
    +----+----+----+----+----+----+
    |         |         |         |
    v         v         v         v
Core scope  Package   Thermal   Perf-limit
IA32_THERM  THERM_    control   reasons
_STATUS     STATUS    regs      CORE_PERF
(0x19C)     (0x1B1)   TEMP_     _LIMIT
PROCHOT     Margin    TARGET    _REASONS
OOS         MARGIN    POWER_CTL (0x64F)
Thresh1/2   HW_FEED   MISC_ENA
log bits    NOTIF log
    |
    v
MCP_THERMAL_REPORT_1 (0x1A3) -- PMT mirror
MCP_THERMAL_REPORT_2 (0x1A4) -- PMT mirror
    |
    v
TPMI / PMSB / PM Telemetry (software observability)
C6 / low-power state reporting context
```

### Per-TC Register Coverage

| TC | Register(s) | Scope |
|----|-------------|-------|
| 22022421640 | `CORE_PERF_LIMIT_REASONS` (0x64F) | Core |
| 22022421641 | `IA32_THERM_STATUS` temperature field + valid bit | Core |
| 22022421642 | `IA32_MISC_ENABLES` (0x1A0) — TM1/TM2 enable | Thread |
| 22022421643 | `IA32_PACKAGE_THERM_MARGIN` | Package |
| 22022421644 | `IA32_PACKAGE_THERM_STATUS` (0x1B1) | Package |
| 22022421646 | `IA32_TEMPERATURE_TARGET` (0x1A2) | Package |
| 22022421647 | `IA32_THERM_STATUS` (0x19C) — full field coverage | Core |
| 22022421649 | `MCP_THERMAL_REPORT_1` (0x1A3) | PMT mirror |
| 22022421650 | `MCP_THERMAL_REPORT_2` (0x1A4) | PMT mirror |
| 22022421660 | `POWER_CTL` (0x1FC) | Package |
| 22022421665 | Extended C6 — reporting in low-power state | C6 path |

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421640](https://hsdes.intel.com/appstore/article-one/#/22022421640) | [Thermal Reporting] Verify CORE_PERF_LIMIT_REASONS | Runnable_On_N-1 |
| [22022421641](https://hsdes.intel.com/appstore/article-one/#/22022421641) | [Thermal Reporting] Verify DTS temperature reporting during  | Runnable_On_N-1 |
| [22022421642](https://hsdes.intel.com/appstore/article-one/#/22022421642) | [Thermal Reporting] Verify IA32_MISC_ENABLES (Thread vMSR 0x | Runnable_On_N-1 |
| [22022421643](https://hsdes.intel.com/appstore/article-one/#/22022421643) | [Thermal Reporting] Verify IA32_PACKAGE_THERM_MARGIN | Runnable_On_N-1 |
| [22022421644](https://hsdes.intel.com/appstore/article-one/#/22022421644) | [Thermal Reporting] Verify IA32_PACKAGE_THERM_STATUS | Runnable_On_N-1 |
| [22022421646](https://hsdes.intel.com/appstore/article-one/#/22022421646) | [Thermal Reporting] Verify IA32_TEMPERATURE_TARGET | Runnable_On_N-1 |
| [22022421647](https://hsdes.intel.com/appstore/article-one/#/22022421647) | [Thermal Reporting] Verify IA32_THERM_STATUS (Core MSR 0x19c | Runnable_On_N-1 |
| [22022421649](https://hsdes.intel.com/appstore/article-one/#/22022421649) | [Thermal Reporting] Verify MSR 0x1A3 MCP_THERMAL_REPORT_1 | Runnable_On_N-1 |
| [22022421650](https://hsdes.intel.com/appstore/article-one/#/22022421650) | [Thermal Reporting] Verify MSR 0x1A4 MCP_THERMAL_REPORT_2 | Runnable_On_N-1 |
| [22022421660](https://hsdes.intel.com/appstore/article-one/#/22022421660) | [Thermal Reporting] Verify POWER_CTL | Runnable_On_N-1 |
| [22022421665](https://hsdes.intel.com/appstore/article-one/#/22022421665) | [Thermal Reporting][BEAT] Extended C6 validation for Thermal | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Path | Purpose |
|-----------|------|---------|
| **`IA32_THERM_STATUS`** | MSR 0x19C (per-core) | Core thermal status/log: Thermal Monitor, PROCHOT, OOS, Threshold1/2, Power Limit, temperature, valid |
| **`IA32_PACKAGE_THERM_STATUS`** | MSR 0x1B1 (package) | Package thermal status/log: same sources + HW Feedback Notification log, package temperature, valid |
| **`IA32_TEMPERATURE_TARGET`** | MSR 0x1A2 | TjMax, TCC offset, fan temp target; reference for margin calculation |
| **`IA32_PACKAGE_THERM_MARGIN`** | Package MSR | Margin to Tcontrol; margin to TJMax |
| **`MCP_THERMAL_REPORT_1`** | MSR 0x1A3 | PMT telemetry mirror — thermal report channel 1 |
| **`MCP_THERMAL_REPORT_2`** | MSR 0x1A4 | PMT telemetry mirror — thermal report channel 2 |
| **`CORE_PERF_LIMIT_REASONS`** | MSR 0x64F (per-core) | Thermal/PROCHOT/VR-source perf-limit cause bits |
| **`POWER_CTL`** | MSR 0x1FC | `DIS_PROCHOT_OUT`, `PROCHOT_RESPONSE`, `PROCHOT_LOCK`; thermal policy control |
| **`IA32_MISC_ENABLES`** | MSR 0x1A0 (thread) | TM1/TM2 thermal monitor enable; enhanced SpeedStep enable |
| TPMI | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.*` | Aggregate thermal status and telemetry observability |
| PMSB | `sv.socket0.imh0.compute*.pma*.gpsb` | PM telemetry bus; carries thermal report data |

---

## Section 3: Reset, Power, and Clocking

- Thermal reporting fields are meaningful only when the **`VALID`** bit in the respective status register is set
- **Sticky log bits** preserve event history across runtime until software clear (write 0 to clear)
- Some out-of-spec status conditions are **reset-cleared only** (not SW-clearable)
- Reporting becomes valid after thermal sensors, firmware reporting paths, and PM telemetry initialization complete
- `MCP_THERMAL_REPORT_1/2` (0x1A3/0x1A4) are PMT telemetry mirrors; valid after PMT initialization
- Warm reset preserves some sticky log bits; cold reset re-initializes all reporting state
- Extended C6 (TC 22022421665): reporting register accessibility and correctness must be verified in low-power C6 entry/exit context

---

## Section 4: Programming Model

**Core reporting (`IA32_THERM_STATUS` 0x19C):**
- `THERMAL_MONITOR_STATUS` / log, `PROCHOT_STATUS` / log, `OUT_OF_SPEC_STATUS` / log
- `THRESHOLD1_STATUS` / log, `THRESHOLD2_STATUS` / log, `POWER_LIMITATION_STATUS` / log
- Temperature (relative to TjMax), resolution, **valid** bit
- Log bits are SW-clearable; out-of-spec status is reset-cleared

**Package reporting (`IA32_PACKAGE_THERM_STATUS` 0x1B1):**
- Package Thermal Monitor, PROCHOT, OOS, Threshold1/2 status/log
- HW Feedback Notification log; package temperature relative to monitor trip; valid bit

**`IA32_TEMPERATURE_TARGET` (0x1A2):**
- TjMax (TCC activation temperature target); TCC offset; fan temp target
- `IA32_PACKAGE_THERM_MARGIN` reports margin-to-Tcontrol and margin-to-TJMax relative to this target

**`POWER_CTL` (0x1FC):**
- `DIS_PROCHOT_OUT`: disable PROCHOT output
- `PROCHOT_RESPONSE`: configure Primecode PROCHOT response power
- `PROCHOT_LOCK`: lock PROCHOT configuration

**`IA32_MISC_ENABLES` (0x1A0, thread):**
- Thermal Monitor 1 (TM1) enable; Thermal Monitor 2 (TM2) / enhanced SpeedStep enable
- Required for thermal monitor logic to be active

**`MCP_THERMAL_REPORT_1/2` (0x1A3/0x1A4):**
- PMT/PM telemetry mirrors of thermal report data; read via MSR by test

**`CORE_PERF_LIMIT_REASONS` (0x64F):**
- Per-core bits indicating reason for frequency limitation: thermal, PROCHOT, VR_THERMALERT, power, etc.
- Both current-state and log forms; SW-clearable log bits

---

## Section 5: Operational Behavior

This TCD validates **thermal observability** — that architectural MSR/PM telemetry surfaces correctly reflect thermal state, margins, and perf-limit causes.

1. DTS / thermal monitor / power-management logic detects current thermal state and threshold crossings
2. pCode / thermal-report logic updates architectural reporting surfaces:
   - Core `IA32_THERM_STATUS` (0x19C) — per-core status/log bits + temperature
   - Package `IA32_PACKAGE_THERM_STATUS` (0x1B1) — package-aggregate status/log + HW feedback notification
   - `IA32_PACKAGE_THERM_MARGIN` — package thermal margin to Tcontrol/TJMax
   - `MCP_THERMAL_REPORT_1/2` — PM telemetry mirror structures
   - `CORE_PERF_LIMIT_REASONS` — per-core thermal/PROCHOT/VR perf-limit cause bits
3. Software reads reporting registers; checks `VALID` bit before consuming temperature fields
4. Sticky log bits preserve event history after real-time condition clears; SW clears by writing 0
5. `POWER_CTL` and `IA32_MISC_ENABLES` control thermal policy and monitor enable; validated as part of the reporting programming model
6. Extended C6 (TC 22022421665): thermal reporting register behavior verified during/after C6 low-power transitions

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| Temperature field read when `VALID=0` | Software must treat reading as invalid; do not use temperature value |
| Real-time event clears before SW reads status | Sticky log bits still preserve event occurrence history |
| Out-of-spec asserted once | `OUT_OF_SPEC_STATUS` may remain set until reset (not SW-clearable) |
| Threshold crossing toggles around boundary | `THRESHOLD_STATUS` / log captures the transition correctly |
| Package and core temperatures disagree | Core (`0x19C`) and package (`0x1B1`) reporting remain independently scoped |
| PROCHOT asserted externally | `PROCHOT_STATUS` and `PROCHOT_LOG` update in both core and package registers |
| TM1/TM2 disabled in `IA32_MISC_ENABLES` | Thermal monitor logic inactive; thermal throttle response suppressed |
| Reporting read during C6 low-power transition | Some fields remain valid per C6 reporting architecture; Extended C6 TC validates boundary |
| `POWER_CTL.PROCHOT_LOCK=1` | PROCHOT policy fields locked; write attempts should be ignored |

---

## Section 7: Security / Safety / Policy

- Thermal reporting MSRs and PM telemetry are privileged architectural observability mechanisms; OS reads are ring-0
- Injecting or forcing thermal conditions to validate reporting requires controlled privileged access
- `POWER_CTL.PROCHOT_LOCK` is a one-way lock; test must validate lock behavior without permanently locking the system
- Because thermal reporting also reflects safety-critical conditions (PROCHOT, OOS), test injection must not confuse passive reporting validation with active protection behavior

---

## Section 8: References

- [DMR CBB Thermal Management HAS](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/has/thermal/thermal_management/thermal_management.html) -- `IA32_THERM_STATUS` (0x19C) core fields: Thermal Monitor, PROCHOT, OOS, Threshold1/2, Power Limit, temperature, valid
- [LNL Thermal Management HAS](https://docs.intel.com/documents/pm_doc/src/lnl/has/thermal/thermal_managment/thermal_mgnt.html) -- `IA32_PACKAGE_THERM_STATUS` (0x1B1) package fields; HW feedback notification log; package temperature/margin
- [LNL Prochot HAS](https://docs.intel.com/documents/pm_doc/src/LNL/HAS/Thermal/Prochot/Prochot.html) -- `POWER_CTL` (0x1FC): DIS_PROCHOT_OUT, PROCHOT_RESPONSE, PROCHOT_LOCK; CORE_PERF_LIMIT_REASONS thermal bits
- [Punit TRM Registers (GPSB)](https://docs.intel.com/documents/sysip_pm/drop_gen4/trm/trm_registers_h_gpsb_msg/trm_registers_h_gpsb_msg.html) -- MCP_THERMAL_REPORT_1 (0x1A3) / MCP_THERMAL_REPORT_2 (0x1A4) PM telemetry mirror mapping
- [DMR IMH PMT Telemetry](https://docs.intel.com/documents/primecode/has/PMT_Definitions/dmr_imh/pmt_telemetry.html) -- PACKAGE_TEMPERATURE: IA32_TEMPERATURE_TARGET; margin to Tcontrol and TJMax
