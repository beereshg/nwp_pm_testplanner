# TCD: [SoC Thermal Management] TPMI/PMT

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420612](https://hsdes.intel.com/appstore/article-one/#/22022420612) |
| **Title** | [SoC Thermal Management] TPMI/PMT |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030767555 -- NWP PM PMT](https://hsdes.intel.com/appstore/article-one/#/16030767555) |
| **Parent TP** | [16030765561 -- NWP PM Interfaces (OS2P/TPMI/PECI/PMT)](https://hsdes.intel.com/appstore/article-one/#/16030765561) |
| **KB last updated** | 2026-07-20 |
| **Feature** | PM Interfaces -- TPMI/PMT Thermal Registers |

## Section 1: Architecture / Micro-architecture and Functionality

**TPMI PMT Thermal** validates the thermal-specific subset of the TPMI (Topology Aware Register and PM Capsule Interface) and PMT (Platform Monitoring Technology) infrastructure. This TCD verifies that OOB and inband thermal status, temperature monitoring, margin telemetry, and thermal filtering registers are correctly populated, accessible, and reflect real-time thermal state.

> **Architecture overview:** See [TPF 16030767555 -- NWP PM PMT](https://hsdes.intel.com/appstore/article-one/#/16030767555) Section 2 Design Details for TPMI/PMT architecture, PFS discovery, and OOBMSM path.

### NWP-Specific Deltas

- NWP reuses DMR IMH2 TPMI/PMT architecture unchanged
- Single NIO die -- one set of TPMI/PMT instances (vs dual-IMH on DMR)
- OOBMSM VSEC BAR, PFS structure, and TPMI SRAM layout identical to DMR
- PMT telemetry update rate: ~1ms (PrimeCode slow-loop)

### TC Coverage Map

| TC | Scope | Environment |
|----|-------|-------------|
| [22022421578 -- Verify Package Thermal Status TPMI Register](https://hsdes.intel.com/appstore/article-one/#/22022421578) | OPC_PKG_THERM_STATUS (TPMI_ID 0x0F, idx 2) read/verify | FV |
| [22022421583 -- Verify Thermal Constrained Time PMT Register](https://hsdes.intel.com/appstore/article-one/#/22022421583) | THERMAL_CONSTRAINED_TIME PMT counter verification | FV |
| [22022421581 -- Verify Temperature Target PMT Register](https://hsdes.intel.com/appstore/article-one/#/22022421581) | TEMPERATURE_TARGET PMT entry verification | FV |
| [22022421558 -- Verify Aggregate Margin to Tcontrol PMT Register](https://hsdes.intel.com/appstore/article-one/#/22022421558) | MARGIN_TO_TCONTROL (S8.8 format) PMT entry verification | FV |
| [22022421576 -- Verify Package Temperature PMT Register](https://hsdes.intel.com/appstore/article-one/#/22022421576) | PACKAGE_TEMPERATURE PMT entry verification (+64C offset) | FV |
| [22022421585 -- Verify Thermal Monitor Filtering TPMI Register](https://hsdes.intel.com/appstore/article-one/#/22022421585) | OPC_THERMAL_MONITOR EWMA decay factor configuration | FV |

---

## Section 2: Interfaces and Protocols

| Interface | Path / Address | Access | Description |
|-----------|---------------|--------|-------------|
| TPMI SRAM (OPC_PKG_THERM_STATUS) | OOBMSM BAR + PFS offset (TPMI_ID 0x0F, idx 2) | RW (BMC) / RO (OS) | Package thermal status/log bits -- mirrors IA32_PACKAGE_THERM_STATUS with independent OOB log bits |
| TPMI SRAM (OPC_PKG_THERM_STATUS_LOG_CLEAR) | TPMI_ID 0x0F, idx 3 | RW/1C | Write-1-to-clear OOB thermal log bits |
| TPMI SRAM (OPC_THERMAL_MONITOR) | TPMI_ID 0x0F, idx 4 | RW | EWMA decay factor (DECAY_FACTOR[6:0]), ENABLE_EWMA[7], INBAND_LOCK[30] |
| PMT (PACKAGE_TEMPERATURE) | PMT telemetry entry | RO stream | Package temperature with +64C offset encoding |
| PMT (MARGIN_TO_TCONTROL) | PMT telemetry entry | RO stream | Signed 8.8 format -- margin to TCC activation |
| PMT (TEMPERATURE_TARGET) | PMT telemetry entry | RO stream | TCC activation temperature target |
| PMT (THERMAL_CONSTRAINED_TIME) | PMT telemetry entry | RO stream | Cumulative time spent thermally constrained |
| PECI Rd/WrEndpointCfg | OOB (BMC) | RW | OOB access to TPMI SRAM thermal registers |
| IA32_PACKAGE_THERM_STATUS | MSR 0x1B1 | RO (OS) | Inband MSR thermal status -- independent log bits from OOB TPMI view |

---

## Section 3: Reset, Power, and Clocking

- **Cold reset**: TPMI SRAM zeroed by Punit MBIST; PrimeCode reinitializes thermal registers at PH2.x (CPL3)
- **Warm reset**: PrimeCode clears SRAM at ResetSeq::CLEAR_HPM_SRAM (~834us); thermal registers re-populated
- **Boot activation**: BIOS locks TPMI features via TPMI_SET_STATE(LOCK=1) before OS boot
- **Runtime**: PrimeCode updates OPC_PKG_THERM_STATUS and PMT entries each slow-loop (~1ms)

---

## Section 4: Programming Model

PrimeCode populates OPC_PKG_THERM_STATUS each slow-loop iteration by reading internal thermal sensor data and writing the formatted status/log bits to TPMI SRAM. The independent OOB log bits allow BMC to clear its view without affecting the OS MSR 0x1B1 log bits.

OPC_THERMAL_MONITOR configures the EWMA thermal filtering window. BMC writes DECAY_FACTOR[6:0] to set the time constant (2.3 x 2^N ms). PCode reads the new config within one slow-loop via IO_FASTPATH_TPMI_LINEMASK notification.

PMT entries (PACKAGE_TEMPERATURE, MARGIN_TO_TCONTROL, TEMPERATURE_TARGET, THERMAL_CONSTRAINED_TIME) are telemetry registers updated by PrimeCode each slow-loop. They are read-only from the BMC perspective via PMT watcher API.

### Key Register Fields

**OPC_PKG_THERM_STATUS (TPMI_ID 0x0F, idx 2):**
| Bit | Field | Description |
|-----|-------|-------------|
| 0 | THERMAL_MONITOR_STATUS | Package thermal monitor currently tripped |
| 1 | THERMAL_MONITOR_LOG | Sticky -- thermal event since last clear |
| 2 | PROCHOT_STATUS | xxPROCHOT# currently asserted |
| 3 | PROCHOT_LOG | Sticky -- PROCHOT since last clear |
| 4 | OUT_OF_SPEC_STATUS | Operating out of thermal spec |
| 5 | OUT_OF_SPEC_LOG | Sticky -- out-of-spec since last clear |
| 6 | THRESHOLD1_STATUS | Temp >= Threshold1 |
| 7 | THRESHOLD1_LOG | Sticky -- Threshold1 transition |
| 8 | THRESHOLD2_STATUS | Temp >= Threshold2 |
| 9 | THRESHOLD2_LOG | Sticky -- Threshold2 transition |
| 10 | POWER_LIMITATION_STATUS | P-state limited by power |
| 11 | POWER_LIMITATION_LOG | Sticky -- power limitation |
| 12 | PMAX_STATUS | PMAX detector asserted |
| 13 | PMAX_LOG | Sticky -- PMAX assertion |

**OPC_THERMAL_MONITOR (TPMI_ID 0x0F, idx 4):**
| Bit | Field | Description |
|-----|-------|-------------|
| 6:0 | DECAY_FACTOR | Time window: 2.3 x 2^N ms (N=0..127) |
| 7 | ENABLE_EWMA | Enable EWMA thermal filtering |
| 30 | INBAND_LOCK | Block inband writes when set |

---

## Section 5: Operational Behavior

> **WHAT:** TPMI PMT thermal registers correctly reflect real-time thermal state and are accessible via both inband MMIO and OOB PECI paths.

| Scenario | Expected Outcome | TC Link |
|----------|-----------------|---------|
| Read OPC_PKG_THERM_STATUS via TPMI | Status bits reflect current thermal state; log bits accumulate events | [22022421578](https://hsdes.intel.com/appstore/article-one/#/22022421578) |
| Read PACKAGE_TEMPERATURE via PMT | Value = actual die temp + 64C offset; updates each slow-loop | [22022421576](https://hsdes.intel.com/appstore/article-one/#/22022421576) |
| Read MARGIN_TO_TCONTROL via PMT | Signed 8.8 value; positive = margin below TCC; negative = above TCC | [22022421558](https://hsdes.intel.com/appstore/article-one/#/22022421558) |
| Read TEMPERATURE_TARGET via PMT | Returns TCC activation temperature programmed by BIOS | [22022421581](https://hsdes.intel.com/appstore/article-one/#/22022421581) |
| Read THERMAL_CONSTRAINED_TIME via PMT | Counter increments while thermally constrained | [22022421583](https://hsdes.intel.com/appstore/article-one/#/22022421583) |
| Configure OPC_THERMAL_MONITOR EWMA | DECAY_FACTOR accepted; filtering behavior changes within 1 slow-loop | [22022421585](https://hsdes.intel.com/appstore/article-one/#/22022421585) |

**Pass/fail bar:**
- OPC_PKG_THERM_STATUS status bits match current thermal state (cross-validated with MSR 0x1B1)
- PMT PACKAGE_TEMPERATURE within +/- 2C of DTS sensor reading (accounting for +64C offset)
- PMT MARGIN_TO_TCONTROL = TEMPERATURE_TARGET - PACKAGE_TEMPERATURE (within +/- 1 unit)
- THERMAL_CONSTRAINED_TIME counter monotonically non-decreasing during thermal event
- OPC_THERMAL_MONITOR DECAY_FACTOR write takes effect within 2 slow-loops (~2ms)
- OOB log bits clearable independently from inband MSR 0x1B1 log bits

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| **OOB vs inband log independence** | BMC clears OPC_PKG_THERM_STATUS_LOG_CLEAR; MSR 0x1B1 log bits unaffected | ⚠️ Verification criterion -- add as check in TC 22022421578 | Add dual-read assertion |
| **EWMA lock contention** | OOB sets INBAND_LOCK=1 on OPC_THERMAL_MONITOR; OS write attempt rejected | ⚠️ Verification criterion -- add as check in TC 22022421585 | Add lock scenario |
| **PMT during thermal throttle** | PACKAGE_TEMPERATURE, MARGIN_TO_TCONTROL update correctly during active throttle | ✅ Implicit in TC 22022421576/22022421558 if run under thermal stress | No action |
| **Post-warm-reset re-init** | All TPMI thermal registers re-populated after warm reset | ❌ Not covered | New TC needed -- read-after-reset verification |
| **DECAY_FACTOR boundary** | N=0 (2.3ms window) and N=127 (max window) behave correctly | ⚠️ Verification criterion -- add boundary values in TC 22022421585 | Add boundary sweep |

---

## Section 7: Security / Safety / Policy

- BIOS locks TPMI features via TPMI_SET_STATE(LOCK=1) before OS handoff
- OOB access authenticated via BMC platform security policy
- IB_WRITE_BLOCK=1 on OOB_PKG_CTLS prevents OS tampering with OOB-exclusive registers
- PMT entries are read-only -- no write path from any SW agent

---

## Section 8: References

- [TPMI Common Feature HAS v2.50](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html) -- Architecture specification
- [DMR TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/TPMI/DMR_TPMI.html) -- DMR-specific TPMI
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/NWP_IMH_SOC_PM_MAS.html) -- NWP PM specification
- KB: [soc_thermal/tpmi_pmt.md](../../pm_features/soc_thermal/tpmi_pmt.md) -- Feature KB reference
- KB: [platform_pm_interface/tpmi_infrastructure.md](../../pm_features/platform_pm_interface/tpmi_infrastructure.md) -- TPMI infrastructure reference
