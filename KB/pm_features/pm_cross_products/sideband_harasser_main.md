# Sideband Harasser — Main Flow

> **Status**: Enriched — rollup from enriched [pm_sideband_harasser.md](pm_sideband_harasser.md) + Primecode source (May 2026)
> **Generated**: 2026-05-23 from nwp_pm_test_cases.json (2 TCs)

## NWP Spec Context
| Field | Value |
|-------|-------|
| HAS ref | NWP HAS: PM Sideband stress flows |
| MAS ref | NWP PM MAS: Sideband harasser supported |
| NWP delta | Carried from DMR — NIO reuses same Primecode `sb_harasser/v1_0` |
| NWP supported | True |

## Architecture Summary

The **Sideband Harasser** is a configurable IOSF sideband stress generator running on the IMH Punit (Primecode). It issues periodic register-access transactions (read, write, or read-modify-write) against any target IP on either GPSB or PMSB fabric. The feature is used exclusively for **firmware verification and hardware validation** — it enables endpoint sweep and cross-product stress testing without hardcoding IP-specific access patterns.

```
  SA_BULK_CR_DATA[0-4]              Primecode SidebandHarasser
  (PCU IO @ 0xfb180)                     (IMH Punit)
         │                                    │
         │  SB_HARASSER_CFG event              │
         ├───────────────────────────────────►│
         │                                    │  Parse config:
         │                                    │  • target die + port
         │                                    │  • GPSB or PMSB
         │                                    │  • access type
         │                                    │  • repeat count
         │                                    │  • timer period
         │                                    │
         │                    ┌────────────────┤  Arm timer
         │                    │  Timer fires   │  (default 250 µs)
         │                    │  every period  │
         │                    ▼                │
         │              ┌─────────────┐        │
         │              │ IOSF Access │        │
         │              │ CRRd/CRWr   │        │
         │              │ CfgRd/CfgWr │        │
         │              │ MRd/MWr/RMW │        │
         │              └──────┬──────┘        │
         │                     │               │
         │                     ▼               │
         │          ┌──────────────────┐        │
         │          │ GPSB / PMSB      │        │
         │          │ Sideband Fabric   │        │
         │          │ → Target IP       │        │
         │          └──────────────────┘        │
```

### Feature Purpose

- **EndPoint Sweep**: Iterate across all reachable sideband endpoints to validate routing, responsiveness, and correct register access
- **Cross Products**: Run harasser concurrently with PkgC transitions, RAPL throttling, and reset flows to detect sideband contention or deadlocks

## FW Agents
- **Agents**: Primecode (IMH Punit)
- **Interfaces**: IOSF sideband (GPSB, PMSB), SA_BULK_CR_DATA[0-4] configuration registers
- **HW Blocks**: GPSB port, PMSB port, PCU IO memory region
- **Sub-features**: EndPoint Sweep, Cross Products

## Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR Firmware Architecture Overview](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/FirmwareArch.html) | GPSB sideband topology |
| HAS | [DMR FW-to-FW Interaction Inventory](https://docs.intel.com/documents/Soc-fw-arch/FW-to-FW/DMR/fw-fw.html) | FW-to-FW sideband messaging inventory |
| HAS | [HPM Message Specification](https://docs.intel.com/documents/primecode/has/DMR/Hierarchical%20PM/HPM_Message_Specification.html) | HPM sideband protocol |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM MAS — sideband harasser scope |
| MAS | [NWP PM MAS - NIO PM IPs and Interfaces](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/NWP_IMH_SOC_PM_MAS.html#nio-pm-ips-and-interfaces) | NIO PM sideband interfaces |
| Primecode src | `src/flow/sb_harasser/v1_0/sb_harasser.hpp` | Class definition, register field extraction |
| Primecode src | `src/flow/sb_harasser/v1_0/sb_harasser.cpp` | Algorithm, IOSF message dispatch |
| Unit tests | `tests/flow/sb_harasser/v1_0/sb_harasser_ut.cpp` | Configuration and access path tests |
| KB sibling | [power_rapl/sideband.md](../power_rapl/sideband.md) | Detailed register spec (SA_BULK_CR_DATA fields) |

## Related Sightings

No known sightings specific to sideband harasser. Failures typically manifest as sideband timeout MCAs in target IPs.

## Subflows (1)

| # | Subflow | Status | TCs | Segment | Notes |
|---|---------|--------|-----|---------|-------|
| 1 | [PM Sideband Harasser](pm_sideband_harasser.md) | Enriched | 2 | FV | EndPoint Sweep + Cross Products |
| | **Total** | 1/1 enriched | **2** | | |
