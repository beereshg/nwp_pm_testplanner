# NWP PM Feature Knowledge Base

> **Status**: Enriched — 101 articles enriched with architecture summaries, register tables, execution flows, NWP deltas, and collateral links (May–June 2026)
>
> Each feature folder maps 1:1 to a Test Plan (TP) feature. Each folder has a `*_main.md` overview
> and per-subflow `.md` files matching TP sub-features. See `nwp_architecture/` for NWP-specific
> spec summaries and the `nwp_has_impact_on_pm_fv.md` TC impact analysis.

## Features

> TC counts from TP metadata (`nwp_pm_fv/data/metadata/`). NWP Supported = feature is active on NWP silicon.

| Feature | Folder | TP TCs | Subflows | Enriched | NWP Supported |
|---------|--------|--------|----------|----------|---------------|
| [Core C-States](core_c_states/core_c_states_main.md) | `core_c_states/` | 54 | 10 | 10/10 ✅ | ✅ (C0/C1/C1e/C6; PkgC6 ZBB) |
| [Fabric DVFS](fabric_dvfs/fabric_dvfs_main.md) | `fabric_dvfs/` | 7 | 1 | 1/1 ✅ | ❌ ZBB (mesh fixed 2 GHz) |
| [Memory Thermal Management](memory_thermal/memory_thermal_main.md) | `memory_thermal/` | 18 | 5 | 5/5 ✅ | ✅ (LPDDR6/MR4; MEMHOT/MEMTRIP) |
| [OSPL](ospl/ospl_main.md) | `ospl/` | 2 | 2 | 2/2 ✅ | ✅ |
| [Platform PM Interface](platform_pm_interface/platform_pm_interface_main.md) | `platform_pm_interface/` | 11 | 3+1 | 4/4 ✅ | ✅ |
| [PM Cross Products + Sideband](pm_cross_products/pm_cross_products_main.md) | `pm_cross_products/` | 4 | 5 | 5/5 ✅ | ✅ (AIPM: active-link ZBB, no-device+IP-disable kept) |
| [Power/RAPL](power_rapl/power_rapl_main.md) | `power_rapl/` | 117¹ | 10 | 10/10 ✅ | ✅ (Socket RAPL only; DRAM/Platform ZBB) |
| [Pstate Stack](pstate_stack/pstate_stack_main.md) | `pstate_stack/` | 85 | 14 | 14/14 ✅ | ✅ (HWP/P0n/P1/Pn; DCM ZBB) |
| [SoC Thermal Management](soc_thermal/soc_thermal_main.md) | `soc_thermal/` | 89 | 15 | 15/15 ✅ | ✅ |
| [SST](sst/sst_main.md) | `sst/` | 70 | 12 | 12/12 ✅ | ✅ (PCT/SST-TF only; SST-PP/HGS ZBB) |
| [Thermal](thermal/thermal_main.md) | `thermal/` | 10 | 4 | 4/4 ✅ | ✅ |
| [CBB CCF PM](cbb_ccf_pm/cbb_ccf_pm_main.md) | `cbb_ccf_pm/` | — | — | T6 lineage | ✅ (no NWP delta) |

> ¹ Power/RAPL folder covers multiple TP feature labels: **Power/RAPL** (60 TCs), **Socket RAPL** (30 TCs),
> **PMAX** (14 TCs), **SIMPL/IccMax** (8 TCs), **SVID** (5 TCs) — all architecturally coupled in PCode/PrimeCode.

## NWP Architecture Reference

> NWP-specific spec summaries extracted from HAS/MAS/PAS. Use as ground-truth before modifying
> or writing TCs that touch NWP-specific behaviour (new rails, ZBB features, memory, IO stack).

| Document | Description |
|----------|-------------|
| [NWP HAS Overview](nwp_architecture/nwp_has_overview.md) | Top-level die topology, cores, memory, PCIe/CXL, GRS/C2C, SKU table, RAS/security deltas from DMR |
| [NWP PM MAS](nwp_architecture/nwp_nio_pm_mas.md) | NIO PM MAS — RC topology (5 lnpv RCs), FIVR inventory, power domains, ZBB table, SVID rail map |
| [NWP MIO Stack](nwp_architecture/nwp_mio_stack.md) | 6 MIO stacks — PM Q/P-channels, FIVR per-stack, PrimeCode-controlled FIVR_MIO_3/4, HAP/TDX |
| [NWP Memory IO Stack](nwp_architecture/nwp_memory_io_stack.md) | LPDDR6 CDS PHY, VCCDDRDIG MBVR, buttress APB, ISA_MC spare bits (PHY freq handshake), DTS |
| [NWP PM Telemetry](nwp_architecture/nwp_nio_pm_telemetry.md) | NIO PM telemetry delta — 5 RCs, NUM_TELE_INDEXES, MR4_TEMP entries vs DMR |
| [NWP NIO SCF Architecture](nwp_architecture/nwp_nio_scf_overview.md) | NIO die SCF topology (I/O Mesh, Mem Mesh, CAB), 423 SubIPs, 435 SBEPs, clocks, MCA bank IDs |
| [NWP PAS Reference](nwp_architecture/nwp_pas_reference.md) | Platform Architecture Spec — VR table (13 MBVRs/SVID addresses), power states, reset/boot, RAS |
| [NWP PM FV Impact Analysis](nwp_architecture/nwp_has_impact_on_pm_fv.md) | Full TC-level impact of NWP HAS on PM FV test plan: REJECT/UPDATE/NEW classification for all 442 TCs |
| [Voltage Regulation Architecture](nwp_architecture/voltage_regulation_architecture.md) | Cross-generational FIVR/DLVR/MBVR reference (GNR→DMR→NWP): per-core vs shared domains, FIVR inventory, platform VR table, validation implications |

## Cross-Cutting Infrastructure

| Document | Description |
|----------|-------------|
| [TPMI Infrastructure Reference](platform_pm_interface/tpmi_infrastructure.md) | Common TPMI architecture: VSEC/PFS/LUT, access control, TPMI_ID encoding, DMR PFS tables, interface transition, validation starting points |
| [Emulation Environment Guide](emulation_environment.md) | HSLE/CTH/Netbatch setup, NWP Simics/VP bringup, PythonSV namednodes, tracker usage, DTS injection, known issues |

## Cross-Cutting References

### NWP Specifications
| Type | Link | Scope |
|------|------|-------|
| HAS | [NWP HAS Overview](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html) | NWP top-level |
| HAS | [NWP HAS - PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features) | PM feature list & NWP deltas |
| HAS | [NWP HAS - Ingredients](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#nwp-ingredients) | NIO, CAB, IMH die composition |
| HAS | [NWP HAS - Platform Configurations](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#platform-configurations) | Socket/package configs |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | Master PM MAS for NWP |
| MAS | [NWP PM MAS - Introduction](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/NWP_IMH_SOC_PM_MAS.html#introduction) | NIO PM IPs overview |
| MAS | [NWP PM MAS - NIO PM IPs and Interfaces](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/NWP_IMH_SOC_PM_MAS.html#nio-pm-ips-and-interfaces) | IP interface details |
| MAS | [NWP PM MAS - NIO PM Telemetry](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/NWP_IMH_SOC_PM_MAS.html#nio-pm-telemetry) | Telemetry architecture |
| PAS | [NWP Platform Architecture Spec (PAS)](https://docs.intel.com/documents/custom-xeon/newport-docs/platform/pas/nwppas.html) | Platform/board level |

### NWP CBB Specifications
> **Note**: NWP reuses the DMR CBB silicon (CAB die). These are the NWP-specific overrides/deltas to CBB HAS documents.

| Type | Link | Scope |
|------|------|-------|
| HAS | [NWP CBB CCF (Converged Coherent Fabric) HAS](https://docs.intel.com/documents/clientsilicon/dmr_cbb/global/ccf/nwp_ccf.html) | NWP-specific CCF deltas from DMR CBB |
| HAS | [NWP CBB NCU (Non-Coherent Unit) HAS](https://docs.intel.com/documents/clientsilicon/dmr_cbb/global/ncu/nwp_ncu.html) | NWP-specific NCU deltas; also links CBB Address Map || HAS | [NWP CBB HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/cbb/nwp_cbb.html) | NWP CBB overview — 48 cores/CBB (1 chiplet disabled vs DMR), UCIe D2D 32 GT/s, no PM flow changes || HAS | [NWP CBB Telemetry Aggregator HAS](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/has/nwp_cbb_telemetry/telemetryaggregator_cbb_nwp.html) | NWP CBB telemetry aggregation — PM-relevant for RAPL/PEM/PLR counters |
| HAS | [DMR CBB Address Map](https://docs.intel.com/documents/ClientSilicon/DMR_CBB/global/NCU/CBBAddressMap.html) | CBB register address map (DMR baseline; NWP uses same map per NCU HAS) |

### DMR Specifications (Baseline)
| Type | Link | Scope |
|------|------|-------|
| HAS | [DMR Overview HAS](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/DMR_Overview_HAS.html) | DMR top-level |
| HAS | [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html) | SoC PM master HAS |
| HAS | [OKS Product Architecture Spec](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/OKS-Product-Architecture-Spec/OKS-Product-Architecture-Spec.html) | Platform architecture |
| HAS | [DMR Firmware Architecture Overview](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/FirmwareArch.html) | FW architecture |
| HAS | [DMR FW-to-FW Interaction Inventory](https://docs.intel.com/documents/Soc-fw-arch/FW-to-FW/DMR/fw-fw.html) | Cross-FW interfaces |

### NWP Block Diagrams
| Diagram | Link |
|---------|------|
| [NWP NIO Block Diagram](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/assets/NIO-diag.jpg) | NIO die |
| [NWP CAB Block Diagram (1x)](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/auto/CAB-blk-diag.vsdx_1x_28efd.png) | 1-socket 1x |
| [NWP CAB Block Diagram (2x)](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/auto/CAB-blk-diag.vsdx_2x_28efd.png) | 1-socket 2x |
| [NWP CAB Block Diagram (2S2x)](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/auto/CAB-blk-diag.vsdx_2S2x_28efd.png) | 2-socket 2x |
| [NWP CAB Block Diagram (2S4x)](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/auto/CAB-blk-diag.vsdx_2S4x_28efd.png) | 2-socket 4x |
| [NWP CAB C2C Diagram](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/auto/CAB-blk-diag.vsdx_CAB_C2C_28efd.png) | C2C connectivity |
| [NWP CAB Die-Package Diagram](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/auto/CAB-blk-diag.vsdx_die-pkg_28efd.png) | Die-to-package |

## How to Use

1. **Review a test case**: Find the feature -> subflow -> read architecture + collateral links
2. **Debug a sighting**: Find the feature -> read FW architecture -> trace to source code
3. **Refine test steps**: Read execution flow -> compare with HAS -> update test case
4. **Query via Copilot**: Ask about a feature/subflow and this KB provides grounded context
