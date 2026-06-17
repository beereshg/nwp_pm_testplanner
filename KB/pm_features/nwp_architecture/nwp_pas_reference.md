# NWP Platform Architecture Specification (PAS) — PM-Relevant Reference

> **Source**: [NWP PAS v0.8](https://docs.intel.com/documents/custom-xeon/newport-docs/platform/pas/NwpPAS.html) (Shekoufeh Qawami, Mahesh Natu, Reza Daftari, Dan Stuart, Tiffany Kasanicky, Anand Enamandram, Przemyslaw Tusk, Marian Alvarez Perez — May 2026, EC milestone)
> **Scope**: Key NWP platform architecture details relevant to PM validation — SoC construction, power delivery, memory, thermal, reset, RAS, and platform constraints.

---

## NWP Platform Overview

NWP (Newport) is a custom SoC derived from **DMR (Diamond Rapids)** for a single customer (codename **Nimbus**). The platform goal is to reuse Oak Stream AP as much as possible, remove unnecessary features, and add Nimbus-specific requirements.

### Key Specs
- **Socket TDP**: 450W
- **Package**: BGA 76×88.5mm, ~12000 pins (0.75/0.8/0.84mm ball pitch)
- **Sockets**: 1S and 2S (connected via midplane, no cables)
- **Form factor**: uMGX (210mm × 360mm per 1S module)

### SoC Construction (vs DMR)

| | DMR-AP | NWP |
|---|--------|-----|
| **CBBs** | 4 | **2** |
| **IMH dies** | 2 (IMH1 or IMH2) | **1 NIO** (derived from IMH2) |
| **Memory** | 16ch DDR5/MRDIMM | **32ch LPDDR6** (8 SOCAMM2 modules) |
| **Integrated accelerators** | DSA, IAA, QAT | **None** |
| **Custom accelerator port** | N/A | **2× GRS/CHI** (x14 CHI per accelerator) |
| **PCIe lanes** | 128L Gen6 | **80L Gen6 + 4L Gen4** |
| **UPI** | Up to 6 ports | **1×8L (P3) fused + optional P6** |
| **Self-boot** | 2nd gen | Same |

### Die ID Assignment
- CBBs: 0–1 (2–7 reserved)
- NIO: 8 (9–15 reserved)

---

## Power Delivery

### VR Table (13 MBVRs)

| Rail | Vnom (V) | ICCmax.max (A) | ITDC (A) | SVID | Address | Notes |
|------|----------|----------------|----------|------|---------|-------|
| **PVCCIN_EHV0** | 1.83 | 728 | 290 | Yes | 01h | Input to FIVRs |
| **PVCCANA0** | 0.9 | 35.4 | 36 | Yes | 02h | Analog for PCIe G6 |
| **PVCCINF** | 0.85 | 42 | 42 | Yes | 03h | Infrastructure |
| **PVCC_HV** | 1.25 | 7.9 | 8 | No | — | |
| **PVCCNN** | 1.0 | 10 | 10 | No | — | |
| **VCCFA_EHV** | 1.8 | 2.3 | 4 | No | — | 1.8V quiet rail |
| **PVCCC2C** | 0.875 | 86 | 86 | Yes | 05h | C2C VCC |
| **PVDD0** | 0.77 | 64 | 64 | Yes | TBD | LPDDR6 VDD0 |
| **PVDD1** | 0.77 | 64 | 64 | Yes | TBD | LPDDR6 VDD1 |
| **PVCCDQ** | 0.5 | 2.5 | 2.5 | No | — | LV supply for DDR |
| **PVCCQXC** | 1.025 | 1.5 | 1.5 | No | — | DDR PHY analog |
| **PVCCQXD** | 0.9 | 3.5 | 3.5 | No | — | DDR PHY analog |
| **PVCC3P3_AUX** | 3.3 | 0.5 | 0.5 | Yes | 0Dh | Psys sensor (VCCIN0) |

**Key SVID deltas from DMR-AP**: VCC_EHV dropped from SVID; new rails VCCC2C, PVDD0, PVDD1 added. Memory power sensor at SVID address 1Bh (for memory RAPL).

### Platform Power States
- Supported: **G3, S0, S5** (S4 indistinguishable from S5)
- **S3 not POR**
- **Pre-S5** mode supported for system inventory/manageability (3.3V on, CPU reads PIROM, then 3.3V off)
- **ADR flows not supported** on NWP

---

## Memory Architecture

### LPDDR6 SOCAMM2
- **32 channels**, 48b/channel, x192 per SOCAMM module
- 8 SOCAMM modules maximum (options for 6 and 4 SOCAMM configs)
- 4 LP6 packages per SOCAMM, each x48 (4 sub-channels × x12, two x6 DRAM)
- 2 PMICs per SOCAMM module (PMIC6300, JEDEC JESD336-1)
- External LP6 PHY with integrated controller for memory training (replaces MMC/Zcode)
- LP6 PHY FW signed by Intel, stored in BIOS flash, loaded by BIOS via S3M/ACTM

### Speed Rates
| Ranks | 10700 MT/s | 9600 MT/s | 7500 MT/s |
|-------|-----------|-----------|-----------|
| 1R/2R | **Supported** | Fallback | — |
| 4R | — | **Supported** | Fallback |

### Configurations
| Config | Channels | SOCAMMs | Notes |
|--------|----------|---------|-------|
| 32ch | 32 | 8 | Full config |
| 28ch | 28 | 8 | 4 spare channels (boot-time sparing) |
| 24ch | 24 | 6 | Reduced |
| 16ch | 16 | 4 | Reduced |
| 8ch | 8 | — | Boot-time failover from 16ch |
| 2ch | 2 | 1 (half) | Debug only (MC8 & MC9) |

### Memory RAPL
> **⚠️ DRAM RAPL is FUSED OFF on NWP** per [NWP PM MAS §3](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/NWP_IMH_SOC_PM_MAS.html#major-changes-from-dmr-product) and [HSD 14025012732](https://hsdes.intel.com/appstore/article-one/#/article/14025012732).

The PAS reference below describes the memory power *measurement* path, which feeds **Socket RAPL** (aggregate SoC power), NOT a standalone DRAM RAPL domain:
- RAPL via 12V rail sensor → e-fuse on 5V rail → PCODE reads for memory RAPL calculation
- Flow leveraged from [DMR DRAM RAPL](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/DMR_DDR5_MCR.html#dram-running-average-power-limit-rapl)

### Memory PM ZBB
> Per [HSD 22021155412](https://hsdes.intel.com/appstore/article/#/22021155412): **No APD/PPD, No LPM1/LPM2/LPM3, No SSR, No DSREF** on NWP.
- MC only issues self-refresh without clock stop prior to warm reset assertion (ensures command/data flushed)
- Memory subsystem removes FSAs outside memtop to allow SD MI
- LPDDR6 PHY integration with built-in MCU (replaces MMC)
- Dedicated MCPLL per memstack (no PHY PLL sourcing)
- Subchannel flip removed: MC_Ch(0,1,4,5) ↔ MSE_Ch(0,1,4,5) → HAMVF_Ch(0,1,4,5) — straight connectivity
  - Related: [Feature HSD](https://hsdes.intel.com/appstore/article/#/14018814652), [BIOS coding change](https://hsdes.intel.com/appstore/article/#/15014127427), [RTL connectivity flip](https://hsdes.intel.com/appstore/article/#/14019341279)
- MSE MKTME keys reduced 2048 → 1028
- Reference: [IMH2 vs NWP topology delta](https://intel.sharepoint.com/:u:/r/sites/nwp/_layouts/15/Doc.aspx?sourcedoc=%7B8F0147DC-58D0-4181-A061-B4082BCB4CD1%7D&file=imh2_vs_nwp_par_delta.vsdx), [IMH2 vs NWP partition delta](https://intel.sharepoint.com/:x:/r/sites/nwp/_layouts/15/Doc.aspx?sourcedoc=%7BDC3C353E-BE11-4D85-AD44-F6CFBDE8021C%7D&file=imh2_vs_nwp_par_delta.xlsx)

### Thermal Management
- **CLTT** via MR4 register (refresh rate multipliers, not direct temperature)
  - 0.7x multiplier (01010b) → switch 1x→2x refresh (~85°C equivalent)
  - 0.5x multiplier (01011b) → start throttling (~90–95°C equivalent)
- **No TSOD polling** over SPD bus (unlike DDR5)
- MR109 temperature register available but not planned for SoC harvesting
- PMIC has integrated thermal sensor/protection (shutdown if critical; 125°C limit vs DRAM 95°C)
- **MEMHOT pin** supported for reporting

### CXL Memory
- CXL Type 3 volatile memory expansion (HDM-H only)
- Up to 4 x16 ports (or 4 x8) — all must be same width
- No CXL Type 1/2, no Flat MM, no PMEM
- CXL hot-plug supported
- Host Based Encryption supported if devices support TSP/IDE + MK-TME

### SPD Bus (I3C_SPD)
- 4 I3C_SPD controller instances (same count as DMR)
- Each I3C_SPD instance maps to 8 memory controllers
- I3C_SPD-to-MC mapping: see [NWP Global ID Excel, "I3C MC Mapping" sheet](https://intel.sharepoint.com/:x:/r/sites/nwp/_layouts/15/Doc.aspx?sourcedoc=%7B1E76F6F8-6F29-4046-9169-9BC8737E5E42%7D&file=nwp_imh_global_id.xlsx&action=default&mobileredirect=true)
- I3C Basic (I2C also supported on SOCAMM)
- **Purpose**: Used by BIOS during system initialization/boot for memory discovery and configuration — DIMM/SOCAMM type, speed, timing, and other config parameters for memory initialization and training
- **Key NWP delta vs DMR**: No TSOD polling for temperature, no error recovery flow for I3C_SPD bus ([NWP PAS - SPD Bus](https://docs.intel.com/documents/custom-xeon/newport-docs/platform/pas/NwpPAS.html#spd-bus), [NWP HAS - Memory Feature List Delta](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#nwp-memory-feature-list-delta))
- For LPDDR6 memory technology, DRAM refresh rates are conveyed via **MR4** (for CLTT), and **MR109** for temperature reading — replacing the DDR5 TSOD polling mechanism

---

## Reset and Boot

### Reset Types
| Type | Description | C2C Links |
|------|-------------|-----------|
| Cold Boot (G3→S0) | Full power up | L3→L0 |
| Cold Reset (S5→S0) | Main power cycle | Reset |
| Warm Reset (S0) | No power cycle | Reset (L2 only) |
| FLR | Accelerator function reset | Re-init by OS |
| CXL Reset | Accelerator CXL reset | Re-init by OS |
| Thermtrip | Thermal emergency power down | L0→L3 |

### Key NWP Boot Deltas
- **No PFR T-1 flow** — customer-defined
- **1–2 Nimbus accelerators** per socket via GRS (PCIe control path + C2C data path)
- **LPDDR6 full training on every reset** (including warm — no fast training advantage)
- **No ADR flows**
- **No multi-socket CBB ID remapping** needed (identical CBB IDs on both sockets)
- **C2C MBVR (VCCC2C)** must power down before FIVRs on cold reset entry
- C2C FW loaded by ACTM, link trained by BIOS DXE driver (ported from Nimbus)

### Boot Time KPIs (to EFI Shell)
| Config | First Cold Boot | Fast Cold Reset | Warm Reset |
|--------|----------------|-----------------|------------|
| 1S | 140s | 120s | 60s |
| 2S | 160s | 130s | 70s |
| PPV | 135s | 105s | N/A |

---

## RAS Architecture

### Key RAS Deltas from DMR

**Not supported on NWP:**
- Error Cloaking (CSR and MCA Bank)
- MSMI (disabled to avoid interference with C2C isolation recovery)
- Viral Mode
- IOMCA error reporting
- PCIe Surprise Hot Plug, PCIe NTB link disable
- UXI Dynamic Link Width Reduction
- Memory SDDC, x8 HDC, DDDC, PFD, Memory Mirroring, MAGIC-RH, MRT, MMC-based RAS
- SCI generation (mutually exclusive with BMC RAS offload — BMC offload chosen)
- Socket Partitioning, MCA 2.0 Recovery, Runtime SLSM

**Supported/Changed:**
- **Custom 32b ECC** for LPDDR6 (replaces DDR5 SDDC/x8 coverage)
- **BMC RAS Offload** — firmware-first mode with BMC handling top 3 recurring CE events
- **Single MCA domain** (one NIO die)
- **MCA bank merging** — 32 MCs fit in 8 MCA bank allocations
- **CAB MCA banks** — new bank IDs for CAB-NBA and CAB-NBH
- **Channel Sparing** — 28ch mode with 4 spare channels (7 failover configs from 8 SOCAMM)
- **Channel Failover** — boot-time, pairs (left+right symmetry). Sparing and failover mutually exclusive

### C2C Error Handling
- All C2C errors logged in proprietary registers (no standard CXL RAS Capability Structure)
- Containment errors → ERR_COR to RCEC → ERR0 pin to BMC
- Uncorrectable errors → broadcast SMI → NMI to OS with CPER
- C2C isolation modeled after CXL Error/Timeout/Isolation
- **MSMI disabled** across all MCA banks; relies on "Crashlog on MCERR" instead
- Recovery: offline accelerator HDM → WBINVD → CXL reset → bring link out of isolation → hot-add

---

## Nimbus Accelerator Architecture

- Up to **2 accelerators per socket** via GRS (Ground Reference Signaling)
- **PCIe control path** (P5 port) + **C2C data path** (CHI protocol + proprietary extensions)
- SW abstraction: appears as CXL Type 2 device with deviations (not fully CXL compliant)
- Accelerator FW stored on device side (not in CPU flash)
- **C2C FW** signed by Intel, stored in BIOS flash, loaded by ACTM (in TDX TCB)
- GRS PHY FW not runtime-patchable (requires reboot)
- Port configurations: 1S1A, 1S2A, 2S2A, 2S4A
- No accelerator failover (1S2A→1S1A not POR)
- C2C link training failure does not halt boot

---

## Telemetry and Manageability

- Inband + out-of-band PMT supported
- All DMR-AP telemetry sources carried forward (where IP exists)
- No new telemetry for LP6 or C2C IPs
- **Trusted telemetry NOT required** (customer confirmed)
- BMC connection: eSPI, I2C_RTC, PCIe, I3C_MNG/I3C_DBG via MCU→USB bridge
- Node Manager basic functionality + PMT (PLDM format preferred)

---

## Security

- **SGX**: Not supported
- **TDX**: Supported (TDX-IO extended for Nimbus accelerators and LPDDR6; SVM model)
- **TME/MK-TME**: Standalone MK-TME not supported; upper PA bits exclusively for TDX KeyIDs
- **BootGuard/TXT (CBnT)**: Supported (same as OKS)
- **Host-Based Encryption**: Supported for CXL Type 3 memory; accelerator memory encrypted by device

---

## PM-Relevant Opens from PAS

| Open | Impact Area |
|------|-------------|
| Power management requirements still being defined | All PM features |
| SVID address for PVDD0/1 | SVID/RAPL |
| Power team needs to verify e-fuse works on 5V for memory RAPL | Memory RAPL |
| HSF allocation programming by SCF IPSD | HSF PM |
| C2C MBVR sequencing — shared VR between SoC and accelerator being evaluated | Reset/power sequencing |
| Thermal limits — lidded package vs bare die decision pending | SoC thermal |
| Unused MC/DDRIO disable for power savings — requirement removed but may revisit | Memory idle power |
| Accelerator clock signal requirement | Accelerator PM |

---

## Collateral Links

| Type | Link | Notes |
|------|------|-------|
| PAS | [NWP PAS v0.8](https://docs.intel.com/documents/custom-xeon/newport-docs/platform/pas/NwpPAS.html) | Full NWP Platform Architecture Spec |
| PAS data | [NWP PAS spreadsheet](https://docs.intel.com/documents/custom-xeon/newport-docs/platform/pas/assets/nwp_pas.xlsx) | VR table, platform configs |
| PAS data | [NWP Memory data](https://docs.intel.com/documents/custom-xeon/newport-docs/platform/pas/assets/Memory/NwpMem.xlsx) | Configs, BW, failover, signal connectivity |
| PAS data | [NWP Reset data](https://docs.intel.com/documents/custom-xeon/newport-docs/platform/pas/assets/Reset/NWP_Reset.xlsx) | Reset types, boot time, platform config |
| PAS data | [NWP RAS delta](https://docs.intel.com/documents/custom-xeon/newport-docs/platform/pas/assets/DMR_vs_NWP_RAS_Features.xlsx) | Feature-by-feature DMR vs NWP RAS comparison |
| PAS data | [NWP UXI ports](https://docs.intel.com/documents/custom-xeon/newport-docs/platform/pas/assets/UXI/NWP_UXI_Ports.xlsx) | UXI topology port connections |
| PAS data | [NWP TAD rule allocation](https://docs.intel.com/documents/custom-xeon/newport-docs/platform/pas/assets/Memory/NWP_TAD_Rule_Allocation.xlsx) | Coherent decoder rules |
| HAS | [NWP HAS Overview](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html) | NWP top-level HAS |
| HAS | [NWP HAS - IP Change List](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#ip-change-list) | DMR→NWP IP deltas |
| HAS | [NWP Global ID HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Global_IDs/NWP_Global_ID_HAS.html) | Die IDs, CAPID |
| HAS | [NWP RAS HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/RAS/NWP_RAS_HAS.html) | MCA banks, C2C isolation |
| HAS | [NWP Security HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Security/NWP_Security_HAS.html) | C2C FW auth |
| HAS | [NWP MCHECK/ACTM HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/MCHECK/NWP_MCHECK_ACTM_HAS.html) | FW_LOAD function |
| MAS | [NWP MIO MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/MIO/NWP_NIO_MIO.html) | MIO stack details |
| MAS | [BIOS Memory Domain FAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/BIOS/Domain/Memory-Domain-FAS/MemoryPhyHostInterfaceSpec.html) | LP6 PHY↔BIOS interface |
| IP HAS | [Gen6 LPDDR6 MC IP HAS](https://docs.intel.com/documents/iparch/mc/HAS/Gen6/Releases/LPDDR6/lpddr6.html) | LP6 memory controller |
| Platform | [OKS PAS](https://docs.intel.com/documents/server-platform-arch/Oakstream/pas/OksPAS.html) | Baseline platform (OKS-AP) |
| Platform | [OKS PSAS](https://docs.intel.com/documents/server-platform-arch/Oakstream/psas/OksPSAS.html) | Baseline platform SW |
| PM HAS | [PM doc Index](https://docs.intel.com/documents/pm_doc/src/server/index.html) | Server PM HAS collection |
| FR | [14024623287](https://hsdes.intel.com/appstore/article-one/#/article/14024623287) | Newport memory requirements |
| FR | [22021754517](https://hsdes.intel.com/appstore/article-one/#/article/22021754517) | Newport memory configurations |
| FR | [22021754562](https://hsdes.intel.com/appstore/article-one/#/article/22021754562) | Newport memory speeds |
| Global ID | [NWP Global ID spreadsheet](https://intel.sharepoint.com/:x:/r/sites/nwp/_layouts/15/Doc.aspx?sourcedoc=%7B1E76F6F8-6F29-4046-9169-9BC8737E5E42%7D&file=nwp_imh_global_id.xlsx) | MC/SPD/HID mapping |
