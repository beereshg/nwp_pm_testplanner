# Thermal — Main Flow

> **Status**: Enriched — rollup from enriched subflow articles + DMR Thermal HAS (May 2026)
> **Generated**: 2026-05-23 from nwp_pm_test_cases.json (10 TCs)

## NWP Spec Context
| Field | Value |
|-------|-------|
| HAS ref | NWP HAS: Thermal Protection (ProcHot, Thermtrip) |
| MAS ref | NWP PM MAS: Thermal flows supported |
| NWP delta | Derived from DMR — NIO monolithic removes D2D thermal propagation |
| NWP supported | True |

## Architecture Summary

**Thermal** encompasses all CPU thermal protection and reporting mechanisms: PROCHOT (platform-asserted throttling), TCC/EMTTM (temperature-based frequency throttling), THERMTRIP/CATTRIP (emergency HW shutdown), and thermal reporting (DTS → MSR pipeline).

```
  DTS Sensors          PCode (CBB)              Primecode (IMH)
  ┌──────────┐      ┌────────────────┐      ┌────────────────┐
  │ Core DTS │      │ Sampling       │      │ Reporting      │
  │ SOC DTS  ├─ADC►│ Aggregation    ├─HPM►│ Package status │
  │ IO DTS   │      │ EWMA filter    │      │ MSR update     │
  └──────────┘      └───────┬────────┘      └────────────────┘
                        │
                 ┌───────┴────────┐
                 │ Protection      │
                 │ • PROCHOT (ext) │
                 │ • TCC/EMTTM     │
                 │ • THERMTRIP (HW)│
                 └────────────────┘
```

### Thermal Protection Hierarchy

| Level | Mechanism | Trigger | Response | Latency |
|-------|-----------|---------|----------|---------|
| 1 | **TCC/EMTTM** | Tj ≥ TCC activation | Frequency throttle (P-state clip) | ~ms |
| 2 | **PROCHOT** | Platform GPIO asserted | Fast_throttle + power ceiling | ~250 ns |
| 3 | **Early throttle** | Tj near thermtrip margin | Emergency frequency clamp (FW) | ~ms |
| 4 | **THERMTRIP** | Tj > absolute max (fused) | HW shutdown (PLL gate → FIVR off) | ~30-100 ns |

## FW Agents

- **PCode (CBB Punit)**: DTS sampling, EWMA filter, per-CCP thermal status, PROCHOT response, SOCKET_THERMAL HPM
- **Primecode (IMH Punit)**: Package thermal reporting, early throttle before thermtrip, PROCHOT HPM routing
- **Acode (Core)**: TCC/EMTTM execution at core level, thermal monitor status updates
- **BIOS**: TCC offset, PROCHOT response power/lock, EWMA filter enable

## Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR SoC Thermal Management](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html) | Full thermal HAS |
| HAS | [DMR CBB ITD HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/ITD/ITD.html#itd-ttd-domains) | ITD/TTD domains |
| HAS | [Socket Thermal Management](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) | Socket thermal overview |
| HAS | [ITD HAS (Wave3 Common)](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/ITD/ITD_HAS.html) | Internal Temperature Distribution |
| HAS | [ACP PM HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Autonomous%20Core%20Perimeter/Autonomous%20Core%20Perimeter%20PM%20HAS.html) | ACP thermal (Acode) |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM MAS |
| PCode src | `source/pcode/flows/thermals/thermal_report.cpp` | Thermal reporting + PROCHOT |
| PCode src | `source/pcode/flows/thermals/thermal_sampling.cpp` | DTS readout |
| Primecode src | `src/flow/thermals/` | Thermal reporting + management |
| Primecode src | `src/flow/prochot/` | PROCHOT handling |

## Related Sightings

| HSD | Title | Relevance |
|-----|-------|----------|
| 22021682591 | xxTHERMTRIP_N rx disabled | DMR thermtrip GPIO output-only |

## Subflows (4)

| # | Subflow | Status | TCs | Segment | Notes |
|---|---------|--------|-----|---------|-------|
| 1 | [PROCHOT](prochot.md) | Enriched | 4 | PV | Platform-asserted fast throttle |
| 2 | [TCC (Thermal Control Circuit)](tcc_thermal_control_circuit.md) | Enriched | 2 | PV | EMTTM throttle + TCC offset |
| 3 | [THERMTRIP/CATTRIP](thermtrip_cattrip.md) | Enriched | 1 | PV | HW emergency shutdown |
| 4 | [Thermal Reporting](thermal_reporting.md) | Enriched | 3 | PV | DTS → MSR reporting pipeline |
| | **Total** | 4/4 enriched | **10** | | |
