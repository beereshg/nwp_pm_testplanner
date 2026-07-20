# TCD: [Memory Thermal Management] CLTT TSOD based

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420563](https://hsdes.intel.com/appstore/article-one/#/22022420563) |
| **Title** | [Memory Thermal Management] CLTT TSOD based |
| **Status** | open |
| **Parent TP** | [16030763140 -- NWP PM Memory Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763140) |
| **Feature** | Memory Thermal -- CLTT TSOD |
| **Sub-Feature** | TSOD (Thermal Sensor On DIMM) via SPD Controller |
| **NWP Disposition** | ⚠️ **ZBB_N/A** — TSOD not POR for NWP LPDDR6/SOCAMM (was: Runnable_On_N-1) |
| **KB last updated** | 2026-07-19 |
| **Co-Design T2 action** | ⚠️ REMOVE / mark ZBB_N/A — NWP PAS confirms TSOD not planned for LP6/SOCAMM CLTT/system usage. See `codesign_T2_ingest_thermal_mgmt.md` §4. |
| **Spec refs (T2)** | NWP PAS (nwppas.html): TSOD not available for CLTT/system usage on LPDDR6/SOCAMM |

## Section 1: Architecture / Micro-architecture and Functionality

**CLTT TSOD (Closed-Loop Thermal Throttling via Thermal Sensor On DIMM)** uses a dedicated hardware temperature sensor on each DIMM module that communicates temperature via the **SPD (Serial Presence Detect)** bus. Unlike MR4-based CLTT (which uses DDR protocol reads) or PECI-based CLTT (which uses Intel's platform interface), TSOD provides a direct, independent temperature reading path through the SPD controller hardware.

**Key distinction:** DIMM temperature in `dimm_tsod_temp` registers is populated **autonomously by hardware** (SPD Controller) -- firmware reads the result rather than issuing DDR commands.

### Block Diagram

```
  DIMMs / DDR5 Modules
    |  TSOD sensor (on DIMM)
    |  reports via SPD bus
    v
  SPD Controller (HW autonomous)
  (polls TSOD; populates dimm_tsod_temp registers)
         |  DIMM temp registers updated
         v
  Memory Controller (MC)
    dimm_tsod_temp[DIMM0..N]    -- TSOD reading per DIMM
    dimm_temp_thresh[low/mid/high/memtrip/2xrefresh]  -- thresholds
    dimm_therm_thr_lvl[low/mid/high]  -- throttle levels
         |  threshold comparison
         v
  BIOS / PCode thermal firmware
    BIOS knob: thermalthrottlingsupport = TSOD mode
    PCode: evaluates dimm_tsod_temp vs dimm_temp_thresh
         |  throttle decision
         v
  IMH Root Die / CBB thermal agents
    Cross-die HPM: propagate throttle limits
    TPMI status updated
         |
         v
  TPMI / MSR observability
  (temperature, throttle status, threshold registers)
```

### TSOD vs Other CLTT Modes

| Feature | TSOD | MR4-based | PECI-based |
|---------|------|----------|-----------|
| Sensor bus | SPD (I2C-like) | DDR protocol MR4 | Platform PECI |
| HW autonomous | Yes -- SPD Controller polls | Partial | No -- platform driven |
| Register | `dimm_tsod_temp` | `dimm_mr4_temp` | Via PECI path |
| BIOS knob | `thermalthrottlingsupport = TSOD` | `= MR4` | `= PECI` |
| Primary use | DDR4/DDR5 with TSOD sensor populated | DDR5 native MR4 | Platform-controlled |

### Key Registers

| Register | Fields | Purpose |
|----------|--------|---------|
| `dimm_tsod_temp` | TSOD temp per DIMM; `tsod_temp_sensor_valid` | DIMM temperature + validity |
| `dimm_temp_thresh` | `dimm_temp_low_maxthreshold[7:0]`, `dimm_temp_mid_maxthreshold[7:0]`, high, memtrip, 2xrefresh | CLTT threshold levels |
| `dimm_therm_thr_lvl` | `dimm_throttle_therm_low_level[7:0]`, mid, high | Max transactions per throttle region |

### TC Coverage Map

| TC ID | Title | Val Env | Disposition |
|-------|-------|---------|------------|
| [22022421376](https://hsdes.intel.com/appstore/article-one/#/22022421376) | [TSOD] Verify CLTT TSOD end to end functionality | virtual_platform | Runnable_On_N-1 |
| [22022421387](https://hsdes.intel.com/appstore/article-one/#/22022421387) | [TSOD] Verify DIMM Thresholds match with default values | silicon, VP | Runnable_On_N-1 |
| [22022421391](https://hsdes.intel.com/appstore/article-one/#/22022421391) | [TSOD] Verify DIMM Thresholds match with default values | emulation | Runnable_On_N-1 |
| [22022421394](https://hsdes.intel.com/appstore/article-one/#/22022421394) | [TSOD] Verify DIMM temp in MC updated by SPD controller | silicon, VP | Runnable_On_N-1 |
| [22022421400](https://hsdes.intel.com/appstore/article-one/#/22022421400) | [TSOD] Verify DIMM temp in MC updated by SPD controller | silicon, VP | Runnable_On_N-1 |
| [22022421405](https://hsdes.intel.com/appstore/article-one/#/22022421405) | [TSOD] Verify DIMM temp in MC updated by SPD controller | emulation | Runnable_On_N-1 |
| [22022421407](https://hsdes.intel.com/appstore/article-one/#/22022421407) | [TSOD] Verify DIMM throttle levels match default values | silicon, VP | Runnable_On_N-1 |
| [22022421408](https://hsdes.intel.com/appstore/article-one/#/22022421408) | [TSOD] Verify DIMM throttle levels match default values | emulation | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| SPD bus | Hardware-autonomous; SPD Controller | TSOD temperature polling from DIMM |
| `dimm_tsod_temp` | MC CSR | DIMM temperature + `tsod_temp_sensor_valid` bit |
| `dimm_temp_thresh` | MC CSR | CLTT thresholds: low, mid, high, memtrip, 2xrefresh |
| `dimm_therm_thr_lvl` | MC CSR | Per-throttle-region transaction limits |
| BIOS knob | `thermalthrottlingsupport` | Select TSOD mode (vs MR4 or PECI) |
| TPMI | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.*` | Thermal status and throttle visibility |

---

## Section 3: Reset, Power, and Clocking

- SPD Controller begins TSOD polling after DRAM initialization; `tsod_temp_sensor_valid` asserts when sensor is present
- BIOS programs `dimm_temp_thresh` and `dimm_therm_thr_lvl` during CPL3 before OS handoff
- BIOS selects TSOD mode via `thermalthrottlingsupport` BIOS knob
- Thermal state persists across warm reset; cold reset re-initializes all thresholds and SPD polling

---

## Section 4: Programming Model

1. **BIOS**: Sets `thermalthrottlingsupport = TSOD` and programs `dimm_temp_thresh` (3 levels + memtrip + 2xrefresh) and `dimm_therm_thr_lvl` (low/mid/high throttle levels)
2. **SPD Controller (HW)**: Autonomously polls each DIMM TSOD sensor; writes temperature to `dimm_tsod_temp`; asserts `tsod_temp_sensor_valid` when DIMM is populated
3. **PCode**: Periodically reads `dimm_tsod_temp`; compares to thresholds; applies throttling via `dimm_therm_thr_lvl` settings
4. **Validation**: Read-back CSR registers to verify defaults; monitor throttle status under temperature injection

---

## Section 5: Operational Behavior

1. SPD Controller autonomously polls DIMM TSOD sensors; `dimm_tsod_temp` updated per slot
2. `tsod_temp_sensor_valid[N]` = 1 for populated slots; 0 for empty slots
3. PCode compares `dimm_tsod_temp[N]` against `dimm_temp_thresh` thresholds each slow-loop
4. If `dimm_tsod_temp > dimm_temp_low_maxthreshold`: throttle at THRT_LO level (`dimm_throttle_therm_low_level`)
5. If `dimm_tsod_temp > dimm_temp_mid_maxthreshold`: throttle at THRT_MID level
6. If `dimm_tsod_temp > dimm_temp_high_maxthreshold`: throttle at THRT_HI level (emergency)
7. If `dimm_tsod_temp > memtrip_threshold`: assert MEMTRIP (critical thermal event)
8. On temperature drop: remove throttle per hysteresis; restore normal BW

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| DIMM slot not populated | `tsod_temp_sensor_valid = 0`; MC ignores that slot's temp |
| TSOD sensor not present on DIMM | `tsod_temp_sensor_valid = 0`; TSOD CLTT disabled for that slot |
| Threshold below current temp at boot | Throttle fires immediately; check BIOS default values |
| All three thresholds exceeded simultaneously | THRT_HI applied (most restrictive); verify priority |
| Temperature drops below low threshold | Throttle exits cleanly via hysteresis; BW restored |
| BIOS selects wrong CLTT mode | `thermalthrottlingsupport != TSOD`; TSOD registers may not be populated |

---

## Section 7: Security / Safety / Policy

- TSOD threshold registers (`dimm_temp_thresh`, `dimm_therm_thr_lvl`) may be BIOS-locked after CPL3
- MEMTRIP is a safety-critical path; `dimm_temp_thresh.memtrip` must be set below DIMM max-safe temperature
- SPD Controller autonomous operation means TSOD readings are always live -- no firmware action needed to get temperature

---

## Section 8: References

- [NWP PM MAS -- Memory Thermal](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- CLTT TSOD scope, NWP memory thermal
- [DMR DDR5/MCR HAS -- TSOD CLTT](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/DMR_DDR5_MCR.html) -- TSOD-based CLTT, SPD Controller, dimm_tsod_temp registers
- [Primecode Feature HAS Index](https://docs.intel.com/documents/primecode/fhas/index.html) -- TSOD-based memory thermal management as Primecode feature
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features) -- NWP memory thermal feature applicability
- [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html) -- Cross-die thermal limit propagation
