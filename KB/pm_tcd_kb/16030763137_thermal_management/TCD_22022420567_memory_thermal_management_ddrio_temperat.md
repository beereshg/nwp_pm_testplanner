# TCD: [Memory Thermal Management] DDRIO Temperature Compensation

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420567](https://hsdes.intel.com/appstore/article-one/#/22022420567) |
| **Title** | [Memory Thermal Management] DDRIO Temperature Compensation |
| **Status** | open |
| **Parent TP** | [16030763137 -- NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Feature** | Memory Thermal |
| **Sub-Feature** | DDRIO Temperature Compensation — RC pulls DTS temp via PMSB → DDRIO Resource Adapter (~10ms rate) |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**DDRIO Temperature Compensation** addresses a key memory reliability concern: **higher DDR speeds require temperature compensation for DDRIO analog circuits**. Those circuits are trained during MRC (Memory Reference Code), but temperature drift after training moves the link away from optimal settings. The platform uses an ongoing temperature-compensation mechanism driven by the RC (Rate Controller) to keep DDRIO settings aligned with thermal conditions — no full link retraining required.

**Architectural mechanism (from DMR/NWP DDRIO spec):**
- DDRIO has **thermal diodes** associated with circuits that require compensation
- SoC DTS collects temperature from those thermal sources
- RC is strapped to **periodically pull DDRIO temperature code from DTS** (via RA DTS path)
- RC **pushes that temperature code into DDRIO CRI temp-code registers** (via RA PLL path)
- **2 temp-code registers added on CRI** to receive the code from RC
- Push rate is strap-configurable; RC pushes DDRIO temp at the **same rate** as DTS → PUnit

On NWP: memory technology is **LPDDR6 PHY/MC**; NWP uses a **single thermal diode** per CBB (replacing multiple diodes in DMR). See NWP Memory IO Stack MAS for NWP-specific DDRIO compensation details.

### Block Diagram

```
  MRC Training (boot time)
  Initial DDRIO analog settings calibrated
         |
         v  (runtime -- periodic, strap-configurable rate)
  Thermal Diodes / DTS
  (DDRIO-associated thermal sources)
         |  temperature code
         v
  RC (Rate Controller) -- via RA DTS path
  Pulls DTS temperature code periodically
         |  via RA PLL path
         v
  DDRIO CRI Temperature Registers (x2)
  Receive updated temperature code from RC
         |
         v
  DDRIO Analog Circuits
  Apply temp code for drift compensation
  (no full link retraining needed)
         |
         v
  TPMI / PMSB observability
  (DTS readings, thermal status, compensation visibility)

  RC also: pushes DTS temp to PUnit at same rate
```

### Feature Scope

| Layer | Component | Role |
|-------|-----------|------|
| Initial calibration | MRC training | Establish baseline DDRIO analog settings |
| Thermal sensing | Thermal diodes + DTS | Sense DDRIO-relevant temperature |
| Compensation loop | RC (Rate Controller) | Pull DTS temp code; push to DDRIO CRI registers |
| Compensation target | DDRIO CRI temp registers (x2) | Receive periodic temp code updates |
| DDRIO analog | DDRIO circuits | Apply temp code for analog compensation |
| Observability | TPMI / PMSB | Thermal state visibility for validation |

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421409](https://hsdes.intel.com/appstore/article-one/#/22022421409) | [DDRIO Temperature Compensation] Temperature compensation | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Path | Purpose |
|-----------|------|---------|
| **DTS / thermal diode** | DDRIO-associated thermal source | Sense DDRIO temperature for compensation |
| **RC pull path (RA DTS)** | RC → DTS | Periodic pull of DDRIO temperature code |
| **RC push path (RA PLL)** | RC → DDRIO CRI registers | Push temperature code into DDRIO compensation registers |
| **DDRIO CRI temp registers** | 2 registers on CRI | Receive periodic temperature code from RC |
| TPMI | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.*` | Thermal status visibility |
| PMSB | `sv.socket0.cbb0.compute*.pma*.gpsb` | PMA-level thermal telemetry |
| MSR | Per-core/die MSRs (0x19C, 0x1A2, etc.) | Thermal status bits |
| GPIO | IMH GPIO bumps | External VR Hot / Prochot input signals |

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

All 1 TCs in this TCD validate different aspects of this chain for the **DDRIO Temperature Compensation** scenario.

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| Temperature changes after MRC training | Compensation updates keep DDRIO aligned; no full retraining needed |
| DTS / diode reading unavailable or stale | Previous valid compensation state retained; update skipped safely |
| RC pull succeeds but push to DDRIO CRI fails | CRI register stale; observable mismatch detectable via register read |
| Multiple RC pull indices map to same DTS source | No guarantee same data on corresponding push; validation must account for this |
| Strap-configured update cadence too slow | Compensation lags temperature drift; may degrade analog margin |
| Reset occurs during compensation loop | Compensation re-established after MRC training completes on next boot |
| NWP single diode vs DMR multi-diode | NWP uses single diode per CBB; fewer sources; verify single-diode path works |

---

## Section 7: Security / Safety / Policy

- TCC thresholds may be BIOS-locked before OS handoff
- VR Hot and Prochot are safety-critical paths; test injection requires privileged access
- Thermal MSR overrides require OS privilege level

---

## Section 8: References

- [NWP Memory IO Stack MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/mc/memory_io_stack_mas.html) -- NWP LPDDR6 PHY/MC DDRIO compensation, single-diode architecture
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP thermal scope
- [NWP CBB HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/cbb/nwp_cbb.html) -- NWP CBB single thermal diode (vs DMR multi-diode)
- [DMR DDR5/MCR HAS -- DDRIO Temp Comp](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/DMR_DDR5_MCR.html) -- DDRIO Temperature Compensation as memory thermal feature; RC pull/push mechanism
- [Primecode Feature HAS Index](https://docs.intel.com/documents/primecode/fhas/index.html) -- DDRIO Temperature Compensation as Primecode feature area
