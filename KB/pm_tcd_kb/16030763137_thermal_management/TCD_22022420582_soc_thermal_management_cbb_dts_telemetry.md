# TCD: [SoC Thermal Management] CBB DTS & Telemetry

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420582](https://hsdes.intel.com/appstore/article-one/#/22022420582) |
| **Title** | [SoC Thermal Management] CBB DTS & Telemetry |
| **Status** | open |
| **Parent TP** | [16030763137 -- NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Feature** | SoC Thermal |
| **Sub-Feature** | DTS — AON (Always-On) die thermal sensor |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**CBB DTS & Telemetry** covers the thermal sensing topology, sensor validity, and telemetry reporting paths on the CBB die — not active throttling. NWP CBB is based on **DMR-CBB** (48 active PNC-ST cores, 32 CBOs); DMR CBB thermal topology is the correct baseline unless NWP-specific deltas override it.

The CBB sensing architecture includes five distinct thermal source types validated by this TCD:

| Source | Description |
|--------|-------------|
| **AON DTS** | Always-On DTS in CGU; no power gating; single diode; thermtrip chain terminus; remains available independent of ordinary FIVR power state |
| **Core DTS** | 2 DTS per DCM module (1 per core); rich per-core diode connectivity; managed by Core PMA push telemetry |
| **CBO Cluster DTS** | CCF/CBO-adjacent thermal sensing; max/min domain reporting to pCode |
| **SoC DTS** | Base/SoC die thermal sensing; reported via Thermal Puller (Punit) / pCode IO push |
| **CCP Thermal Telemetry** | Core PMA push path; min/max reporting for DCM core and MLCSSA domains via short telemetry |

DTS behavior is controlled by **fuse/config**: `oneshotmodeen`, `sleeptimer`, `catfilteren`, `active_diode_mask`, and per-domain calibration masks. Disabled DTS instances are controlled via active diode mask exclusion; the thermal flow ignores suppressed sources.

### Block Diagram

```
  CBB Die Thermal Sources
  +-----------+-----------+-----------+-----------+-----------+
  | AON DTS   | Core DTS  | CBO       | SoC DTS   | CCP       |
  | (always-  | (2/module,| Cluster   | (base die)| Telemetry |
  | on, CGU)  | Core PMA) | DTS       | Thermal   | (PMA push)|
  +-----------+-----------+ (CCF/CBO) | Puller    +-----------+
                          +-----------+-----------+
         |
  Disabled DTS Mask / Fuse / Config
  (active_diode_mask, oneshotmodeen, sleeptimer, catfilteren)
         |
         v
  CBB DTS Aggregation / Thermal Reporting
  (domain max/min; pCode IO push; short telemetry)
         |
         v
  PCode / Primecode Telemetry Consumer
  (thermal status, interrupt feeds, throttle inputs)
         |
         v
  TPMI / MSR / PMSB (software-visible telemetry)
  + IMH / root-die cross-die reporting context
```

### Per-TC Sensor Mapping

| TC | Sensor / Path |
|----|---------------|
| 22022421456 | AON DTS — always-on, no power gating, single diode, thermtrip anchor |
| 22022421458 | CBO Cluster DTS — 32 CBOs; CCF/CBO-adjacent sensing; max/min domain reporting |
| 22022421461 | CCP Thermal Telemetry — Core PMA push; DCM core + MLCSSA min/max via short telemetry |
| 22022421465 | Core DTS — 2 DTS per DCM module; per-core diode connectivity |
| 22022421468 | Core Disabled DTS — active_diode_mask exclusion; suppressed source handling |
| 22022421469 | SoC DTS — base/SoC die sensing; Thermal Puller / pCode IO push reporting |

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421456](https://hsdes.intel.com/appstore/article-one/#/22022421456) | [CBB DTS & Telemetry] Verify AON DTS Functionality | Runnable_On_N-1 |
| [22022421458](https://hsdes.intel.com/appstore/article-one/#/22022421458) | [CBB DTS & Telemetry] Verify CBO Cluster DTS Functionality | Runnable_On_N-1 |
| [22022421461](https://hsdes.intel.com/appstore/article-one/#/22022421461) | [CBB DTS & Telemetry] Verify CCP Thermal Telemetry | Runnable_On_N-1 |
| [22022421465](https://hsdes.intel.com/appstore/article-one/#/22022421465) | [CBB DTS & Telemetry] Verify Core DTS Functionality | Runnable_On_N-1 |
| [22022421468](https://hsdes.intel.com/appstore/article-one/#/22022421468) | [CBB DTS & Telemetry] Verify Core Disabled DTS operation | Runnable_On_N-1 |
| [22022421469](https://hsdes.intel.com/appstore/article-one/#/22022421469) | [CBB DTS & Telemetry] Verify SOC DTS Functionality | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Path | Purpose |
|-----------|------|---------|
| **AON DTS** | CGU always-on sensor | Single-diode; thermtrip anchor; independent of FIVR power state |
| **Core DTS / Core PMA push** | Per-DCM (2 DTS/module); short telemetry path | Min/max core and MLCSSA domain temperatures pushed to pCode |
| **CBO Cluster DTS** | CCF/CBO-adjacent sensing | Max/min domain reporting for 32-CBO topology |
| **SoC/Base DTS** | Thermal Puller (Punit) / pCode IO | Base/SoC die temperature pushed to pCode per-diode |
| **CCP Telemetry** | Core PMA short telemetry | DCM core + MLCSSA min/max telemetry stream |
| **DTS fuse/config** | `active_diode_mask`, `oneshotmodeen`, `sleeptimer`, `catfilteren` | Per-instance DTS mode, enabled diode set, sleep cadence, filter controls |
| MSR `IA32_THERM_STATUS` | 0x19C per-core | Per-core DTS digital readout and status bits |
| TPMI | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.*` | Aggregate thermal status and throttle observability |
| PMSB | `sv.socket0.imh0.compute*.pma*.gpsb` | PMA-level telemetry path |

---

## Section 3: Reset, Power, and Clocking

- **AON DTS** is always available — no power gating, no diode toggling; remains functional independent of ordinary FIVR power state; thermtrip chain terminates here
- Non-AON DTS instances (Core, CBO, SoC) depend on fuse/config, power/clock state, `active_diode_mask`, and `sleeptimer` settings to determine availability
- DTS readings are only valid after sensor bring-up, fuse configuration, and per-instance operating mode initialization
- Warm reset preserves DTS fuse configuration; cold reset re-initializes DTS operational state
- Core PMA push telemetry (CCP) is only valid after PMA bring-up and Core PM initialization

---

## Section 4: Programming Model

DTS/telemetry programming is primarily fuse/config-driven:

- **AON DTS**: configured separately; `oneshotmodeen`, `sleeptimer`, `catfilteren` — no ordinary diode toggling; always-on operation
- **Core DTS**: per-module; `active_diode_mask` selects enabled diodes; core vs MLCSSA domain calibration masks; `sleeptimer` / `sleeptimer1` control reporting cadence
- **CBO Cluster DTS**: CCF/CBO cluster domain; max/min DTS reporting configured via thermal domain masks
- **SoC/Base DTS**: Thermal Puller push programming; per-diode temperature reporting to pCode IO
- **CCP Telemetry**: Core PMA short-telemetry configuration; min/max push for DCM core and MLCSSA domains
- **Disabled DTS**: `active_diode_mask` exclusion; when a core/module is fused off, corresponding DTS contribution is excluded from thermal aggregate
- BIOS / Primecode initialize DTS fuse fields and operating modes during early boot; OS reads DTS telemetry read-only via MSR 0x19C and TPMI

---

## Section 5: Operational Behavior

This TCD validates **sensor presence, valid temperature reporting, correct aggregation path, and disabled-sensor handling** — not the downstream throttle loop.

1. DTS instances sample temperature from local/remote diodes per configured mode (`oneshotmodeen`, `sleeptimer`, `active_diode_mask`)
2. Each domain reports through its designated path:
   - **AON / SoC/Base DTS** → Thermal Puller (Punit) / pCode IO per-diode push
   - **CBO Cluster DTS** → CCF/CBO max/min domain reporting to pCode
   - **Core DTS / CCP** → Core PMA push short telemetry (min/max DCM core + MLCSSA)
3. pCode / Primecode thermal consumers aggregate reported values for thermal status, interrupt feeds, and throttle inputs
4. Disabled DTS instances (`active_diode_mask` exclusion) are silently suppressed; the thermal flow must not erroneously include fused-off sensor values
5. TPMI / MSR / PMSB provide software-visible observability of reported temperatures and telemetry

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| DTS not yet valid after reset | Telemetry must not be consumed as valid thermal state |
| AON DTS active while other DTS instances unavailable (power-gated) | AON path remains functional and observable |
| Core DTS disabled / masked via `active_diode_mask` | Corresponding thermal contribution excluded from aggregate; no false temperature reporting |
| Active diode mask excludes certain diodes | Reported temperature reflects only enabled diode set |
| Core/MLCSSA domain temperatures differ | PMA telemetry must preserve separate min/max domain reporting |
| CBO cluster hotspot vs core hotspot | Domain-specific telemetry path reflects correct source |
| Sleep/oneshot configuration differs between DTS instances | Reporting cadence/availability changes per instance config |

---

## Section 7: Security / Safety / Policy

- Thermal telemetry configuration and debug access are privileged (BIOS/firmware controlled)
- DTS fuse/config programming is platform-controlled; OS reads telemetry read-only
- Validation that overrides DTS values, active masks, or disabled-DTS behavior requires controlled test access
- Because DTS telemetry feeds protection mechanisms (thermtrip, TCC), test injection must avoid unintentionally triggering catastrophic thermal actions

---

## Section 8: References

- [NWP CBB HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/cbb/nwp_cbb.html) -- NWP CBB baseline; 48 cores, 32 CBOs; DMR-CBB inheritance
- [DMR CBB Thermal Integration HAS](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/has/thermal/dmr_cbb_thermal_integration_has/dmr_cbb_thermal_integration_has.html) -- DTS topology; AON DTS; core/CBO/SoC DTS architecture; diode connectivity
- [DMR CBB Thermal Management HAS](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/has/thermal/thermal_management/thermal_management.html) -- Thermal Puller push; CCP telemetry; Core PMA push; DTS reporting domains
- [DMR CBB Thermal MAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Power_Delivery_MAS/Thermal_MAS/Thermal_MAS/Thermal_MAS.html) -- DTS fuse/config: active_diode_mask, oneshotmodeen, sleeptimer, catfilteren
- [DMR Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/thermals/dmr_thermal.html) -- DMR thermal feature summary; DTS/reporting context
- [NWP Telemetry and Manageability HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/manageability_and_telemetry/telemetry_and_manageability_has.html) -- NWP telemetry inheritance from DMR
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP SoC Thermal; CBB telemetry scope
