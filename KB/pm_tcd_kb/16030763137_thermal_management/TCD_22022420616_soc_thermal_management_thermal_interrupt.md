# TCD: [SoC Thermal Management] Thermal Interrupts

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420616](https://hsdes.intel.com/appstore/article-one/#/22022420616) |
| **Title** | [SoC Thermal Management] Thermal Interrupts |
| **Status** | open |
| **Parent TP** | [16030763137 -- NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Feature** | SoC Thermal |
| **Sub-Feature** | IA32_HWP_INTERRUPT (Core MSR 0x773) — interrupt enable bits verification |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**Thermal Interrupts** cover the hardware/firmware mechanisms by which temperature-state transitions generate processor interrupts observable by OS/BIOS. On NWP there are **no changes to DMR thermal interrupt handling compared to legacy**. The interrupt architecture is split into a **core-scoped path** (`IA32_THERM_INTERRUPT`, MSR 0x19B) and a **package-scoped path** (`IA32_PACKAGE_THERM_INTERRUPT` / `PACKAGE_THERM_INTERRUPT`), plus a **HW feedback notification** interrupt that fires when the hardware power/thermal limits change hardware feedback values.

Six interrupt conditions are covered:
- **HIGH_TEMP** — temperature rises above TCC threshold
- **LOW_TEMP** — temperature falls below TCC threshold (hysteresis exit)
- **PROCHOT** — external PROCHOT_N assertion detected
- **OUT_OF_SPEC** — operating temperature exceeds spec limit
- **THRESHOLD_1 / THRESHOLD_2** — programmable relative-temperature threshold crossings

Each condition has a corresponding enable bit in both `IA32_THERM_INTERRUPT` (core-scoped) and `IA32_PACKAGE_THERM_INTERRUPT` (package-scoped). If the enable bit is clear, no interrupt is pended. If the APIC thermal LVT is not enabled, the interrupt will not reach software even if the thermal source fires.

### Block Diagram

```
  DTS / Thermal Sensors
  (temperature / state transitions)
         |
         v
  PCode / Primecode Thermal Monitoring
  (event classification: high/low/OOS/prochot/threshold crossings)
         |
         v
  Interrupt Generation Logic
  (checks interrupt-enable bits per source)
         |               |               |
         v               v               v
  Core MSR Path    Package MSR Path   HW_FEEDBACK_NOTIFICATION
  IA32_THERM_      IA32_PACKAGE_      Package-scoped; fires when
  INTERRUPT        THERM_INTERRUPT    HW feedback changes due to
  (MSR 0x19B)      + IO/PCU CR views  thermal/power limits
  - HIGH_TEMP      - HIGH_TEMP
  - LOW_TEMP       - LOW_TEMP
  - PROCHOT        - PROCHOT
  - OUT_OF_SPEC    - OUT_OF_SPEC
  - THRESHOLD_1    - THRESHOLD_1
  - THRESHOLD_2    - THRESHOLD_2
                   - POWER_INT
                   - HW_FEEDBACK_NOTIF
         |
         v
  TPMI / PMSB / Telemetry (status + observability)
  IMH root-die / CBB0 / CBB1 (package topology)
```

### Per-TC Coverage

| TC | Interrupt Source | Path |
|----|-----------------|------|
| 22022421588 | HW_FEEDBACK_NOTIFICATION | Package MSR (`PACKAGE_THERM_INTERRUPT`) |
| 22022421595 | HIGH_TEMP | Core + Package |
| 22022421610 | IA32_PACKAGE_THERM_INTERRUPT | Package MSR (full register validation) |
| 22022421614 | IA32_THERM_INTERRUPT | Core MSR 0x19B (full register validation) |
| 22022421618 | LOW_TEMP | Core + Package |
| 22022421620 | OUT_OF_SPEC | Core + Package |
| 22022421627 | PROCHOT Interrupt | Core + Package |
| 22022421629 | THRESHOLD_1 | Core + Package |
| 22022421633 | THRESHOLD_2 | Core + Package |

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421588](https://hsdes.intel.com/appstore/article-one/#/22022421588) | [Thermal Interrupts] HW_FEEDBACK_NOTIFICATION interrupt | Runnable_On_N-1 |
| [22022421595](https://hsdes.intel.com/appstore/article-one/#/22022421595) | [Thermal Interrupts] Verify HIGH_TEMP Interrupt | Runnable_On_N-1 |
| [22022421610](https://hsdes.intel.com/appstore/article-one/#/22022421610) | [Thermal Interrupts] Verify IA32_PACKAGE_THERM_INTERRUPT (Pk | Runnable_On_N-1 |
| [22022421614](https://hsdes.intel.com/appstore/article-one/#/22022421614) | [Thermal Interrupts] Verify IA32_THERM_INTERRUPT (Core MSR 0 | Runnable_On_N-1 |
| [22022421618](https://hsdes.intel.com/appstore/article-one/#/22022421618) | [Thermal Interrupts] Verify LOW_TEMP Interrupt | Runnable_On_N-1 |
| [22022421620](https://hsdes.intel.com/appstore/article-one/#/22022421620) | [Thermal Interrupts] Verify OUT_OF_SPEC Interrupt | Runnable_On_N-1 |
| [22022421627](https://hsdes.intel.com/appstore/article-one/#/22022421627) | [Thermal Interrupts] Verify PROCHOT Interrupt | Runnable_On_N-1 |
| [22022421629](https://hsdes.intel.com/appstore/article-one/#/22022421629) | [Thermal Interrupts] Verify THRESHOLD_1 Interrupt | Runnable_On_N-1 |
| [22022421633](https://hsdes.intel.com/appstore/article-one/#/22022421633) | [Thermal Interrupts] Verify THRESHOLD_2 Interrupt | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Path | Purpose |
|-----------|------|---------|
| **`IA32_THERM_INTERRUPT`** | MSR 0x19B (per-core) | Core thermal interrupt enable: HIGH_TEMP, LOW_TEMP, PROCHOT, OUT_OF_SPEC, THRESHOLD_1, THRESHOLD_2 |
| **`IA32_PACKAGE_THERM_INTERRUPT`** | Package MSR / IO/PCU CR views | Package thermal interrupt enable: same sources + POWER_INT + HW_FEEDBACK_NOTIFICATION_ENABLE |
| **`IA32_THERM_STATUS`** | MSR 0x19C (per-core) | Core thermal status: interrupt-status sticky bits, digital readout |
| **`IA32_PACKAGE_THERM_STATUS`** | Package MSR | Package thermal status sticky bits |
| **APIC Thermal LVT** | Local APIC register | Must be enabled for interrupt to reach software |
| TPMI | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.*` | Thermal status and throttle observability |
| PMSB | `sv.socket0.imh0.compute*.pma*.gpsb` | PMA-level thermal telemetry |
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

The thermal interrupt flow (distinct from the throttle response flow):

1. A thermal-state transition occurs (temperature crosses a threshold, PROCHOT asserted, out-of-spec, feedback change)
2. Thermal monitor / Punit logic evaluates the corresponding interrupt-enable bit in `IA32_THERM_INTERRUPT` (core) or `IA32_PACKAGE_THERM_INTERRUPT` (package)
3. If the enable bit is **set**: a thermal interrupt is generated and the corresponding **status sticky bit** is set in `IA32_THERM_STATUS` / `IA32_PACKAGE_THERM_STATUS`
4. If the APIC thermal LVT is enabled, the interrupt is delivered to software; otherwise the status bit is set but no IRQ is pended
5. Software (OS/BIOS) reads status bits to identify the interrupt source; clears sticky bits by writing 0
6. HW_FEEDBACK_NOTIFICATION: fires when hardware feedback values change due to thermal/power limits; uses `HW_FEEDBACK_NOTIFICATION_ENABLE` bit in `IA32_PACKAGE_THERM_INTERRUPT`

**Key distinction:** this TCD validates **interrupt generation and delivery** (enable bits, status bits, APIC delivery) — not the throttle/frequency response, which is covered by separate Prochot/TCC TCDs.

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| Thermal transition with interrupt enable bit cleared | No interrupt generated; status bit may still set |
| Interrupt enable bit set but no actual crossing event | No interrupt; status bit remains clear |
| THRESHOLD value programmed near TjMax | Interrupt fires only on defined relative-temperature crossing |
| PROCHOT asserted while already thermally throttling | PROCHOT interrupt still generated per enable bit; independent of throttle state |
| APIC thermal LVT not enabled | Thermal source may fire; no IRQ delivered to OS |
| Multiple thermal events close together | Separate status sticky bits remain distinguishable per source |
| Package and core thresholds crossed at different times | Core and package interrupt paths trigger independently per their own scopes |
| HIGH_TEMP then LOW_TEMP in quick succession | Both status bits should be observable; LOW_TEMP clears HIGH_TEMP sticky on threshold exit |

---

## Section 7: Security / Safety / Policy

- TCC thresholds may be BIOS-locked before OS handoff
- VR Hot and Prochot are safety-critical paths; test injection requires privileged access
- Thermal MSR overrides require OS privilege level

---

## Section 8: References

- [DMR Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/thermals/dmr_thermal.html) -- no changes to DMR thermal interrupt handling vs legacy; interrupt register overview
- [DMR CBB Thermal HAS](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/has/thermal/thermal_management/thermal_management.html) -- `IA32_THERM_INTERRUPT` core fields: HIGH_TEMP, LOW_TEMP, PROCHOT, OUT_OF_SPEC, THRESHOLD_1/2
- [Punit Registers -- Thermal Interrupt](https://docs.intel.com/documents/sysip_pm/punit/assets/punit_registers.html) -- `IA32_PACKAGE_THERM_INTERRUPT` package fields including HW_FEEDBACK_NOTIFICATION_ENABLE and POWER_INT
- [Punit TRM](https://docs.intel.com/documents/sysip_pm/punit/trm/trm.html) -- APIC thermal LVT interaction; interrupt delivery conditions
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP SoC Thermal; interrupt scope
