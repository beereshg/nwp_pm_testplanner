# Power/RAPL > Sideband Harasser

> **Status**: Restructured — NWP delta enriched from MCP HAS/MAS query
> **Parent**: [Power / RAPL](power_rapl_main.md)

## Baseline (DMR)

The **Sideband Harasser** is a periodic register-access stress generator running on the IMH Punit (Primecode). It issues configurable IOSF sideband read/write/modify transactions against any target IP on either GPSB (general-purpose) or PMSB (power management) fabric, at a programmable timer interval. The feature is used for **firmware verification and hardware validation** — it torture-tests sideband message handling, coherency, and error handling without hardcoding specific IP access patterns.

## HW Touchpoints

<!-- TODO: Extract from Legacy content or enrich via MCP HAS query -->
| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| | | | | |

## FW Touchpoints

<!-- TODO: Extract from Legacy content or enrich via MCP HAS query -->
| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| | | | | |

## OS Interfaces

<!-- TODO: Extract from Legacy content or enrich via MCP HAS query -->
| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| | | | | |

## NWP Delta

**Sideband power communication is supported on NWP** with limitations.

### Changes
- VR and PMIC telemetry sideband flows are supported
- **Memory-related sideband flows are removed** (no DRAM RAPL, no Memory PM)
- SPD controller sideband for DIMM power data — N/A

### Validation Impact
- Verify VR telemetry sideband communication
- Skip memory-related sideband test cases

## Legacy (Human-Curated Reference)

### Architecture Summary

The **Sideband Harasser** is a periodic register-access stress generator running on the IMH Punit (Primecode). It issues configurable IOSF sideband read/write/modify transactions against any target IP on either GPSB (general-purpose) or PMSB (power management) fabric, at a programmable timer interval. The feature is used for **firmware verification and hardware validation** — it torture-tests sideband message handling, coherency, and error handling without hardcoding specific IP access patterns.

#### Configuration-Driven Stress Engine

```
                    SA_BULK_CR_DATA[0-4]
                    (PCU IO @ 0xfb180)
                           │
                  ┌────────▼────────┐
                  │  eventConfig()  │  ← Triggered by SB_HARASSER_CFG event
                  │  Parse fields:  │
                  │  • target die   │
                  │  • port ID      │
                  │  • fabric       │
                  │  • access type  │
                  │  • repeat count │
                  └────────┬────────┘
                           │ Arms timer
                  ┌────────▼────────┐
                  │  timerEvent()   │  ← Fires every timer_period µs (default 250 µs)
                  │  if enabled:    │
                  │  repeat N times │
                  └────────┬────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         sendRead     sendWrite    sendModify
         Access()     Access()     Access()
              │            │            │
              ▼            ▼            ▼
         ┌───────────────────────────────┐
         │     IOSF Sideband Fabric      │
         │   GPSB (fabric_select=0)      │
         │   PMSB (fabric_select=1)      │
         └───────────────────────────────┘
```

#### Access Types

| `access_type` | Read Opcode | Write Opcode | Description |
|---------------|-------------|--------------|-------------|
| 0 | CRRd | CRWr | Configuration register read/write |
| 1 | CfgRd | CfgWr | PCI configuration space read/write |
| 2 | MRd | MWr | Memory-mapped read/write |

#### Read-Modify-Write (RMW) Operation

When `read_modify_write = 2`, the harasser performs an atomic RMW:

```
read_data = IOSF_Read(target, offset)
write_data = (read_data | (write_payload & modify_mask)) & ~(~write_payload & modify_mask)
IOSF_Write(target, offset, write_data)
```

This allows targeted bit-flipping with arbitrary masks for stress variation.

### Execution Flow

1. **BIOS / FW configuration**: External agent writes `SA_BULK_CR_DATA[0-4]` registers with target parameters (die ID, port ID, fabric, access type, repeat count, timer period)
2. **Config event fires**: `SB_HARASSER_CFG` event triggers `eventConfig()` which parses all 5 data registers and extracts the access pattern
3. **Enable check**: If `ENABLED` bit (CR_DATA[0][31]) is set, the timer is armed at the configured period; if cleared, the timer is disarmed
4. **Timer fires**: Every `timer_period` µs (default 250 µs if configured as 0), `timerEvent()` calls `runSidebandHarasser()`
5. **Message generation**: `runSidebandHarasser()` dispatches to the appropriate access function (read/write/modify) based on configuration
6. **Repeat loop**: The access is issued `repeat_count` times per timer event, tracking `num_repeats_successful`
7. **Continuous**: Timer re-arms after each event until the feature is disabled via a new config event

### Key Registers & Interfaces

| Register | Offset | Description | Source |
|----------|--------|-------------|--------|
| `SA_BULK_CR_DATA[0]` | `0xfb180` | Control: DIE_ID[7:0], ACCESS_TYPE[26:25], POSTED[27], GPSB_PMSB[28], RMW[30:29], ENABLED[31] | Primecode source |
| `SA_BULK_CR_DATA[1]` | `0xfb184` | Target: LOCAL_PORT_ID[15:0], REGISTER_OFFSET[31:16] | Primecode source |
| `SA_BULK_CR_DATA[2]` | `0xfb188` | Timing: REPEAT_PERIOD[15:0] (µs, 0→250), REPEAT_COUNT[31:16] | Primecode source |
| `SA_BULK_CR_DATA[3]` | `0xfb18c` | Write data: WRITE_PAYLOAD[31:0] | Primecode source |
| `SA_BULK_CR_DATA[4]` | `0xfb190` | Modify mask: MODIFY_MASK[31:0] (for RMW operations) | Primecode source |

#### FW Integration Points

| Item | Identifier | Description |
|------|------------|-------------|
| Timer ID | `TimerID::SB_HARASSER` | Periodic timer for access generation |
| Event ID | `event_id::SB_HARASSER_CFG` | Configuration change event |
| Reset Seq | `reset_seq::FW_INIT_RUNTIME` | Init handler during runtime FW init |
| Namespace | `SidebandHarasserFlow` | Flow namespace in Primecode |
| Singleton | `SidebandHarasser` | Main class (singleton pattern) |

### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR FW Architecture Overview](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/FirmwareArch.html) | GPSB sideband topology |
| HAS | [DMR FW-to-FW Interaction Inventory](https://docs.intel.com/documents/Soc-fw-arch/FW-to-FW/DMR/fw-fw.html) | Sideband messaging inventory |
| HAS | [HPM Message Specification](https://docs.intel.com/documents/primecode/has/DMR/Hierarchical%20PM/HPM_Message_Specification.html) | HPM sideband protocol details |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM MAS — sideband harasser scope |
| Primecode src | `src/flow/sb_harasser/v1_0/sb_harasser.hpp` | Class definition, register field extraction |
| Primecode src | `src/flow/sb_harasser/v1_0/sb_harasser.cpp` | Algorithm implementation, IOSF message dispatch |
| Unit tests | `tests/flow/sb_harasser/v1_0/sb_harasser_ut.cpp` | Configure0/1/2, Read/Write/Modify access tests |

### Related Sightings

No known sightings specific to the sideband harasser feature at this time. The feature is a stress/debug utility and failures typically manifest as sideband timeout MCAs in the target IP rather than in the harasser itself.

### NWP Delta

| Area | DMR (N-1) | NWP | Notes |
|------|----------|-----|-------|
| Sideband harasser | Fully supported — GPSB + PMSB | Same expected | NWP reuses DMR Primecode `sb_harasser/v1_0` |
| Fabric targets | GPSB + PMSB endpoints | Same expected | NIO die has same sideband fabric topology |
| SA_BULK_CR_DATA | PCU IO base `0xfb180` | Same expected | ⚠ Confirm NWP PCU IO base address unchanged |
