# Sideband Harasser > PM Sideband Harasser

> **Status**: Enriched from Primecode `src/flow/sb_harasser/v1_0/` source analysis (May 2026)
> **Parent**: [Sideband Harasser](sideband_harasser_main.md)
> **Source Confidence**: High — Primecode source code primary reference. Cross-ref [power_rapl/sideband.md](../power_rapl/sideband.md) for detailed register spec.

## Architecture Summary

The PM Sideband Harasser generates periodic IOSF sideband transactions against configurable target IPs on GPSB or PMSB fabric. It is a **stress/validation utility** running on the IMH Punit (Primecode) that enables endpoint sweep and cross-product testing without hardcoding access patterns.

### EndPoint Sweep

The **EndPoint Sweep** test (14022603906) exercises the harasser across all reachable IOSF sideband endpoints:

```
For each target_port_id in GPSB/PMSB port list:
    Configure SA_BULK_CR_DATA[0-4] with target port, CRRd opcode
    Fire SB_HARASSER_CFG event
    Verify harasser successfully reads from endpoint
    Check: no sideband timeout MCA, no GPSB/PMSB error
```

This validates that all sideband endpoints respond correctly to firmware-initiated register reads, catching dead ports, misconfigured routing, and timeout issues.

### Cross Products

The **Cross Products** test (14022603910) exercises the harasser concurrently with other PM features:
- Sideband harasser + PkgC entry/exit — verify sideband transactions don't block or get blocked during package C-state transitions
- Sideband harasser + RAPL throttling — verify sideband traffic doesn't interfere with power limit enforcement
- Sideband harasser + reset flows — verify harasser disarms cleanly during reset entry

## Execution Flow

1. **Test script configures**: SA_BULK_CR_DATA[0-4] registers specify target die, port ID, fabric (GPSB/PMSB), access type, and repeat count
2. **Config event fires**: `SB_HARASSER_CFG` event triggers Primecode to parse configuration
3. **Timer arms**: Periodic timer fires every `timer_period` µs (default 250 µs)
4. **Access dispatch**: Each timer event issues `repeat_count` × access (CRRd/CRWr/CfgRd/CfgWr/MRd/MWr)
5. **Endpoint response**: Target IP responds on IOSF fabric; harasser tracks `num_repeats_successful`
6. **Validation**: Test script verifies no MCAs, no timeouts, correct response data

## Key Registers & Interfaces

See [power_rapl/sideband.md](../power_rapl/sideband.md) for full register field breakdown.

| Register | Description |
|----------|-------------|
| `SA_BULK_CR_DATA[0]` | Control: DIE_ID, ACCESS_TYPE, POSTED, GPSB_PMSB, RMW, ENABLED |
| `SA_BULK_CR_DATA[1]` | Target: LOCAL_PORT_ID, REGISTER_OFFSET |
| `SA_BULK_CR_DATA[2]` | Timing: REPEAT_PERIOD (µs), REPEAT_COUNT |
| `SA_BULK_CR_DATA[3]` | WRITE_PAYLOAD for write/modify operations |
| `SA_BULK_CR_DATA[4]` | MODIFY_MASK for RMW operations |

## Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR FW Architecture Overview](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/FirmwareArch.html) | GPSB/PMSB sideband topology |
| HAS | [HPM Message Specification](https://docs.intel.com/documents/primecode/has/DMR/Hierarchical%20PM/HPM_Message_Specification.html) | HPM sideband protocol |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM MAS — sideband harasser scope |
| Primecode src | `src/flow/sb_harasser/v1_0/sb_harasser.hpp` | Class definition, field extraction |
| Primecode src | `src/flow/sb_harasser/v1_0/sb_harasser.cpp` | Algorithm, IOSF dispatch |
| Unit tests | `tests/flow/sb_harasser/v1_0/sb_harasser_ut.cpp` | Configure + access path tests |
| KB sibling | [power_rapl/sideband.md](../power_rapl/sideband.md) | Detailed register spec and algorithm |

| HSD ID | Title | Segment | NWP Scope |
|--------|-------|---------|-----------|  
| 14022603906 | EndPoint Sweep | FV | Runnable_On_N-1 |
| 14022603910 | Cross Products | FV | Runnable_On_N-1 |

## Related Sightings

No known sightings specific to sideband harasser. Failures typically manifest as sideband timeout MCAs in target IPs rather than in the harasser itself.

## NWP Delta

| Area | DMR (N-1) | NWP | Notes |
|------|----------|-----|-------|
| Sideband harasser | Fully supported | Same expected | NWP reuses Primecode `sb_harasser/v1_0` |
| GPSB endpoints | DMR IMH port topology | NIO port topology | ⚠ EndPoint Sweep port list may differ |
| PMSB endpoints | DMR PMSB ports | NIO PMSB ports | ⚠ Verify NIO PMSB port IDs |
| Cross products | PkgC + RAPL + Reset | Same expected | |
