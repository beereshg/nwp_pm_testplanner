# NWP NIO SCF Architecture — Technical Overview

> **Source**: [NWP SCF MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/scf/), [NWP HAS Overview](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html)
> **Scope**: NWP NIO die fabric architecture, topology, component inventory, clocks, reset/PM signals, fuses, RAS, DFD, and interface specs. Reference for PM validation, SCF debug, and topology understanding.

---

## NWP SoC Product Overview

Newport (NWP) is a custom Xeon processor derived from the baseline DMR architecture:
- **2 Compute dies (CBBs)**: each with 24 Dual Core Modules
- **1 NIO Die**: derived from DMR IMH2, built to support memory and BW requirements for the custom product

Product configurations: [NWP HAS - SoC Product Configurations](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#platform-configurations)

---

## NIO Die Architecture

NWP NIO die is derived from baseline DMR IMH2 with a substantial portion of the IPs/subsystems reused from IMH2. The scalable coherent fabric in NIO die has 3 main components:

| Fabric Domain | Description | Relationship to DMR |
|---------------|-------------|---------------------|
| **I/O Mesh** | Connections to universal bridges and I/O agents | Resembles DMR IMH2 I/O Die fabric |
| **Mem Mesh** | Revamped memory mesh — redesigned as I/O-like fabric | Redesigned for NWP BW KPIs |
| **CAB (C2C Accelerator Bridge)** | New fabric for NWP — coherent data flows between CPU and Nimbus accelerator | **New in NWP** |

Topology diagram: NWP NIO Die SCF MAS Topology with Global/Physical Instance IDs

---

## CAB Perimeter

The C2C Accelerator Bridge (CAB) portion of the SCF fabric:

### Interfaces
| Interface | Boundary | Protocol | Description |
|-----------|----------|----------|-------------|
| **Mem Mesh East/West** | B2CAB boundary | UFI | CAB ↔ Mem Mesh domain on East and West |
| **C2C IP (South)** | AMA/CIT boundary | ARM CHI-E | 2 Tx/Rx sets: accelerator as RN + CPU as HN |

C2C IP runs on a different clock from CAB fabric mesh → **asynchronous FIFO (ASF)** placed between CAB fabric and C2C IP.

### AMACIT Implementation
- Each AMACIT module (AMA01CIT): **2 AMA sub-slices** (operating at Uclk_Mem/2) + **1 CIT module**
- Each AMA sub-slice has an associated **PWB cache**
- **14 AMA01CIT instances** → 28 AMA + 14 CIT + 28 PWB physical instances
- Each AMA01CIT module: 3 Sideband EPs (2 AMA slices + 1 CIT module)

### AMA Slice ID to CHI Port Mapping

| AMA Slice ID (physical) | AMA Slice ID (Remapped) | CHI Port ID | CHI Link ID | Notes |
|--------------------------|-------------------------|-------------|-------------|-------|
| 0 | 0 | 0 | 6 | CHI Port ≤ 6: Link ID = (6 - Port ID) |
| 1 | 1 | 1 | 5 | |
| 2 | 2 | 2 | 4 | |
| 3 | 3 | 3 | 3 | |
| 4 | 4 | 4 | 2 | |
| 5 | 5 | 5 | 1 | |
| 6 | 6 | 6 | 0 | |
| 7 | 7 | — | — | Unused (UBR_HMA hash doesn't produce 7) |
| 8 | 8 | 7 | 7 | CHI Port > 6: Link ID = Port ID |
| 9 | 9 | 8 | 8 | |
| 10 | 10 | 9 | 9 | |
| 11 | **15** | 10 | 10 | Remapped per 14027485062 |
| 12 | 12 | 11 | 11 | |
| 13 | 13 | 12 | 12 | |
| 14 | 14 | 13 | 13 | |

> **Note**: AMA Slice ID 11 → 15 remapping addresses [14027485062](https://hsdes.intel.com/appstore/article-one/#/14027485062). PrimeCode sets up UBR_HMA default remapping table to map HA Slice ID 11 → 15.

---

## DMR IMH vs NWP NIO — Key Differences

### Non-CAB Fabric

| Component | DMR IMH | NWP NIO | Notes |
|-----------|---------|---------|-------|
| HAMVF/HSF instances | 16 | **32** | Single NIO = 2× DMR IMH |
| B2SCA | 8 | **16** | Single NIO = 2× DMR IMH |
| IOCA slices | 16 | **32** | Single NIO = 2× DMR IMH |
| UBR-UIO-Type1 (I/O Stacks) | 4 | **6** | |
| UBR-UIO-Type2 (Infra IPs) | 2 | **1** | No accelerator stack in NWP |
| I/O Mesh Rows | 4 | **8** | Increased for BW KPIs |
| Mem Mesh | CMS 2× layer Mesh | **New topology** | Redesigned for simultaneous traffic KPIs |
| B2D2D-CBB connections | 2 | **4** | |
| B2D2D-IMH | Present | **Removed** | Single NIO, no IMH-to-IMH D2D |
| I/O Voltage Domain | 1 | **2** | I/O fabric voltage domain split |
| TQ in I/O Fabric | Not present | **New** | |
| TQ from Mem E/W to CAB | Not present | **New** | |

### CAB Fabric (All New in NWP)

| Component | DMR | NWP NIO | Description |
|-----------|-----|---------|-------------|
| B2CAB-NIO | N/A | **New** | New UBR variant |
| B2CAB-HMA | N/A | **New** | New UBR variant |
| HMA (Home Memory Agent) | N/A | **New** | Developed from SCA baseline |
| HMA Snoop Filter | N/A | **New** | New IP (Cache team) |
| CRS (CAB) | N/A | **New instance** | Existing CRS IP |
| B2CHI | N/A | **New** | New UBR variant |
| AMA (Accelerator Memory Agent) | N/A | **New** | Developed from HAMVF baseline |
| CIT (CHI to IDI translator) | N/A | **New** | Completely new IP |
| PWB (Pre-allocated Write Buffer) | N/A | **New** | New IP (Cache team) |

---

## SCF SubIP Component Inventory

### Non-CAB Fabric (297 mesh SubIPs)

| Component | Count | Notes |
|-----------|-------|-------|
| CMS (Mem Mesh) | 16 | 8 per Mem Mesh Left + 8 Right |
| CMS (I/O Mesh) | 16 | 8 per Left IOCA + 8 per Right |
| CRS (Mem Mesh) | 48 | Complex formula across B2D2D, HA pairs, B2CAB |
| CRS (I/O Mesh) | 24 | 4 per B2UIO × 6 I/O stacks |
| P2P_CRS | 6 | 1 per I/O Stack |
| B2UIO | 7 | 6 for I/O Stacks + 1 for B2UIO_Infra |
| UBR_D2D_CBB | 4 | 2 per CBB × 2 CBBs |
| UBR_SCA | 16 | 8 + 8 |
| SCA (IOCA) | 32 | 2 per B2SCA |
| IOCA LLC | 32 | Cache IP associated with SCA |
| UBR_CAB | 16 | 8 + 8 |
| ASF | 16 | 8 + 8 |
| HAMVF | 32 | |
| HSF | 32 | Cache IP associated with HAMVF |

### CAB Fabric (126 mesh SubIPs)

| Component | Count | Notes |
|-----------|-------|-------|
| HMA | 16 | 8 + 8 |
| HMA Snoop Filter | 16 | 1 per HMA |
| UBR_HMA | 16 | 8 + 8 |
| CRS | 32 | 4 per Ring × 8 rings |
| UBR_AMACIT | 4 | Connects to AMA/CIT modules |
| AMA/CIT | 14 | 14 instances (2 AMA + 1 CIT per instance) |
| PWB | 28 | 2 per AMACIT module |

**Total SCF SubIPs**: 297 (Non-CAB) + 126 (CAB) = **423**

---

## Clocks

| Fabric Component | Clock | Notes |
|------------------|-------|-------|
| I/O Fabric | IO_UCLK | Same as DMR |
| I/O CA/LLC | IO_UCLK | Same as DMR |
| CAB Fabric | MEM_UCLK | New in NWP — runs on unified Mesh clock |
| Mem Fabric | MEM_UCLK | NWP unifies Mem+CAB onto single PLL (vs DMR separate clocks) |
| C2C Digital | C2C CLK | New in NWP — dedicated clock |
| CAB PWB | MEM_UCLK | New in NWP |
| CAB HMA-SF | MEM_UCLK | New in NWP |
| HSF SRAM | HSF PLL | Same as DMR |
| HAMVF | MEM_UCLK | Same as DMR |

> **Key delta**: In DMR, Mem Mesh and I/O Mesh had 2 different clocks. In NWP, the entire Mem Mesh + CAB Mesh is sourced by a single PLL (UclkMem). I/O Fabric remains on IO_UCLK.

---

## Reset & PM Signals (per SCF SubIP)

| Signal | Direction | Width | Description |
|--------|-----------|-------|-------------|
| Uclk | input | 1 | Uncore Mesh Clock — voltage domain specific |
| side_clk | input | 1 | Sideband EP clock — voltage domain specific |
| prim_rst_b | input | 1 | Primary/side reset for SCF — asserts/deasserts asynchronously |
| pwrgood_rst_b | input | 1 | Power-good reset indication — asserts/deasserts asynchronously |
| side_pok | output | 1 | Notifies sideband fabric of power-gate/reset — deasserted when prim_rst_b asserts |
| safe_mode | input | 1 | Disables clock gating during reset exit; must reassert for warm/surprise reset or Sx entry |
| config_done | input | 1 | Asserted after SOC completes IP config (LUT programming); latches configs, starts interface init |
| qActive | output | 1 | Activity indicator for PM |

### Q-Channel Exception (Cache IPs)
HSF, HMA-SF, PWB, and IOCA LLC support full Q-channel (qActive + qAccept_n + qreq_n) — requires a Q-channel aggregator at SoC level for each voltage domain's resource controller.

### ISA_SCF Instances (config_done/safe_mode routing)

| Instance | Count | Partition | SCF IPs Driven | Signal Count |
|----------|-------|-----------|----------------|--------------|
| ISA_SCF0 w/e | 2 | parscfmeminf3 w/e | 8 CRS_D2D + 2 UBR_D2D + 16 HSF + 2 CMS_DUMMY + 2 CRS_HA | 30 |
| ISA_SCF1 w/e | 2 | parscfmeminf1 w/e | 6 CRS_ha + 6 CMS_DUMMY + 16 HSF | 28 |
| ISA_SCF2 w/e | 2 | parcinffivrw/e | 8 CRS_CAB + 8 UBR_CAB + 1 bottom CATILE (14) | 30 |
| ISA_SCF3 w/e | 2 | parscfioinf0 w/e | 2 CATile lower (28) + lower 2 CRS_IO | 30 |
| ISA_SCF4 w/e | 2 | parscfioinf2 w/e | 1 CATile upper (14) + upper 2 CRS_IO + 3 UBR_MIO + 1 UBR_INFRA + 3 P2P_CRS | 23 |
| ISA_SCF5 w/e | 2 | parcabinf21 w/e | 8 HMA + 8 HMA-SF + 8 UBR-HMA | 24 |
| ISA_SCF6 | 1 | parcabmiscw | 8 CRS_RX_HMA + 8 CRS_TX_HMA + 4 b2amacit | 20 |
| ISA_SCF7 | 1 | parcabmisce | 8 CRS_RX_HMA + 8 CRS_TX_HMA | 16 |
| ISA_SCF8 | 1 | parcabinf01 | 14 AMACITs | 14 |
| ISA_SCF9 | 1 | parcabinf02 | 28 PWBs | 28 |
| **Total** | **16** | | | |

---

## Fuse Requirements

| IP | Fuse Name | Width | New from DMR | Notes |
|----|-----------|-------|--------------|-------|
| **TQ_IO_EW** | ptr_sep_east/west | 2+2 | Yes | TQ between VCCCFC_IO_E and VCCCFC_IO_W |
| **TQ_CAB_MEM_WEST** | ptr_sep_east/west | 2+2 | Yes | TQ between VCCCFC_CAB and VCCCFC_MEM_W |
| **TQ_CAB_MEM_EAST** | ptr_sep_east/west | 2+2 | Yes | TQ between VCCCFC_CAB and VCCCFC_MEM_E |
| **TQ_D2D** | ptr_sep_east/west | 2+2 | No | TQ for D2D on VCCCFC_MEM_W |
| **HSF** | HSF_DISABLE | 32 | No | |
| **HA** | HA_DISABLE | 32 | **Yes** | New — SCF IP team has NOT agreed to HAMVF disabled mode |
| **IOLLC** | IOLLC_DISABLE | 32 | No | Exists in DMR |
| **SCA** | SCA_DISABLE | 32 | No | Exists in DMR |
| **HMA-SF** | HMA_SF_DISABLE | 16 | **Yes** | New for NWP |
| **HMA** | HMA_DISABLE | 16 | **Yes** | New for NWP |
| **PWB** | PWB_DISABLE | 28 | **Yes** | New for NWP |
| **AMACIT** | AMACIT_DISABLE | 14 | **Yes** | New for NWP |

---

## Sideband Endpoints

### Non-CAB Fabric (281 SBEPs)

| Component | SBEPs | Sideband Type | IP Baseline |
|-----------|-------|---------------|-------------|
| CMS (Mem Mesh) | 16 | GPSB | CMS |
| CMS (I/O Mesh) | 16 | GPSB | CMS |
| CRS (Mem Mesh) | 48 | GPSB | CRS |
| CRS (I/O Mesh) | 24 | GPSB | CRS |
| P2P_CRS | 6 | GPSB | CRS |
| B2UIO | 7 | GPSB | UBR |
| UBR_B2D2D_CBB | 4 | GPSB | UBR |
| UBR_SCA | 16 | GPSB | UBR |
| SCA | 32 | GPSB | SCA |
| IOCA LLC | 32 | GPSB | IOCA LLC |
| UBR_CAB | 16 | GPSB | UBR |
| ASF | 0 | — | No SBEPs |
| HAMVF | 32 | GPSB | HAMVF |
| HSF | 32 | GPSB | HSF |

### CAB Fabric (154 SBEPs)

| Component | SBEPs | Sideband Type | IP Baseline |
|-----------|-------|---------------|-------------|
| HMA | 16 | GPSB | SCA baseline |
| HMA-SF | 16 | GPSB | HSF-like |
| UBR_HMA | 16 | GPSB | UBR |
| CRS | 32 | GPSB | CRS |
| UBR_AMACIT | 4 | GPSB | UBR |
| AMACIT (AMA×2 + CIT) | 42 | GPSB | HAMVF baseline (3 per instance × 14) |
| PWB | 28 | GPSB | IOLLC-like |

**Total SBEPs**: 281 + 154 = **435**

---

## Multicast Group Support

### Non-CAB (9 multicast port IDs)
SCA(32), IOCA LLC(32), HAMVF(32), HSF(32), UBR_SCA(16), UBR_UIO_TYPE1(1×6), UBR_UIO_TYPE2(1), UBR_D2D_CBB(4), CMS/CRS (all across CAB & Non-CAB)

### CAB (9 multicast port IDs)
UBR_CAB_NIMH(16), UBR_CAB_HMA(16), UBR_B2AMACIT(4), HMA(16), HMA-SF(16), AMACIT-AMA(28), AMACIT_CIT(14, separate from AMA since CIT is on Uclk and AMA on Uclk/2), PWB(28), Cache Flush Group(32 IOCA + 16 HMA + 28 AMA)

---

## MCA Bank IDs — NIO IPs

| Bank ID | DMR Location | NWP (NIO) Location | Merged Index | Notes |
|---------|-------------|---------------------|--------------|-------|
| 7 | D2D (0-3) | D2D (0-7) | Y | Increased from 4 to 8 |
| 9 | Spare | **CAB-PWB** (0-13) | Y | 14 PWB instances |
| 12 | HA/MVF (0-15) | HA/MVF (0-31) | Y | Increased 16→32 |
| 13 | HSF (0-15) | HSF (0-31) | Y | Increased 16→32 |
| 14 | SCA (0-15) | SCA (0-31) | Y | Increased 16→32 |
| 15 | D2D (0-11) | D2D (0-15) | Y | Increased 12→16 |
| 16 | MSE (0-15) | MSE (0-31) | Y | Increased 16→32 |
| 17 | IOCache (0-15) | IOCache (0-31) | Y | Increased 16→32 |
| 18 | UXI (0-3) | UXI (0-5) | Y | Increased 4→6 |
| 19-26 | MCCHAN0-7 / 8-15 | **MCCAMM0-7** (0-3 each) | Y | Merged 4 LPDDR6 ch per MCA bank |
| 29 | Spare | **CAB-CIT** (0-13) | Y | 14 CIT instances |
| 30 | Spare | **CAB-AMA (NBA)** (0-27) | Y | 28 AMA sub-slices |
| 31 | Spare | **CAB-HMA (NBH)** (0-15) | Y | 16 HMA instances |

---

## Key SCF Feature HSDs

| HSD | Description |
|-----|-------------|
| 14024794943 | SCA cache size reduction feasibility |
| 22021710923 | Map CPU from 1 RN/Socket to 4 RN/Socket |
| 14024641936 | CAB - CHI accelerator bridge flows & arch |
| 14024607636 | Address hashing changes for LPDDR channel failover |
| 14026009643 | Support for additional failover cfg, 1/2 CAMM cfg |
| 14024676755 | Support for 2 and 4 CAMM depop |
| 14024876702 | NIO Power Plane/Freq domain/PM DVFS strategy/anchors |
| 14024533647 | Memory & IO switch fabric changes |
| 22021494408 | IO-CA Domains update from 2 to 1 |
| 14024534253 | CAB - CHI accelerator bridge perimeter |
| 14024641935 | CAB Fabric Topology |
| 14024533673 | CAB - HSF changes for NWP CAB caching/coherence |
| 14024997060 | Clarification PWB Sizing |
| 14026033336 | Support for fewer than 14 GRS ports |
| 14026977215 | CCB Support for address range (partial) mirroring |
| 14024997124 | Device accessing Host MMIO |
| 14026543976 | Support for reduced light weight topology |
| 14024533594 | Buffer Size changes for NWP KPI |
| 15019143216 | HMA-SF STCV array increase by 2b of state |
| 14027485062 | AMA slice ID numbering - Bridge Mesh Stop ID/UFI port numbering |

---

## Interface Specs

| IP | Interface | Protocol | HAS Link |
|----|-----------|----------|----------|
| UBR_B2D2D_CBB | D2D Stack | UFI | [D2D CBB Bridge NWP](https://docs.intel.com/documents/iparch/scf/HAS/Gen4.1/HAS/BRIDGE/Latest/HAS/SCF_GEN4_LATEST_D2D_CBB_BRIDGE_NWP.html) |
| UBR_UIO_TYPE2 | MIO-A Stack | UFI | [UIO2 Bridge NWP](https://docs.intel.com/documents/iparch/scf/HAS/Gen4/HAS/BRIDGE/Latest/HAS/SCF_GEN4_LATEST_UIO2_BRIDGE_NWP.html) |
| UBR_UIO_TYPE1 | Accelerator Stack | UFI | [UIO1 Bridge NWP](https://docs.intel.com/documents/iparch/scf/HAS/Gen4/HAS/BRIDGE/Latest/HAS/SCF_GEN4_LATEST_UIO1_BRIDGE_NWP.html) |
| UBR_SCA | SCA (IOCA) | UFI | [SCA Bridge NWP](https://docs.intel.com/documents/iparch/scf/HAS/Gen4/HAS/BRIDGE/Latest/HAS/SCF_GEN4_LATEST_SCA_BRIDGE_NWP.html) |
| UBR_CAB | CAB ↔ Non-CAB | UFI | [CAB NIMH Bridge NWP](https://docs.intel.com/documents/iparch/scf/HAS/Gen4/HAS/BRIDGE/Latest/HAS/SCF_GEN4_LATEST_CAB_NIMH_BRIDGE_NWP.html) |
| UBR_CAB_HMA | HMA | — | [CAB HMA Bridge NWP](https://docs.intel.com/documents/iparch/scf/HAS/Gen4/HAS/BRIDGE/Latest/HAS/SCF_GEN4_LATEST_CAB_HMA_BRIDGE_NWP.html) |
| UBR_CAB_AMACIT | AMACIT | — | [AMACIT Bridge NWP](https://docs.intel.com/documents/iparch/scf/HAS/Gen4/HAS/BRIDGE/Latest/HAS/SCF_GEN4_LATEST_AMACIT_BRIDGE_NWP.html) |
| HAMVF | MC Stack | CMI | [HAMVF HAS](https://docs.intel.com/documents/iparch/scf/HAS/Gen4/HAS/HAMVF/R2204/HAS/SCF_GEN4_R2204_HAMVF_HAS.html#interfaces) |
| SCA | IOCA LLC | Cache Data/Tag | [SCA HAS](https://docs.intel.com/documents/iparch/scf/HAS/Gen4/HAS/SCA/Latest/HAS/SCF_GEN4_LATEST_SCA.html) |
| AMACIT | C2C Stack | CHI | [CAB AMACIT HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/CAB/SCF_GEN4.1_LATEST_CAB_AMACIT.html) |
| HMA | HMA-SF | Cache Data/Tag | [CAB HMA HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/CAB/HMA/HAS/SCF_GEN4.1_LATEST_CAB_HMA.html) |
| HSF | HAMVF | Cache Data/Tag | [SCF Cache HAS](https://docs.intel.com/documents/iparch/scfcache/HAS/Gen4/releases/R2204/HAS/SCFCACHE_HAS.html#interfaces) |
| IOCA | UBR_SCA | Cache Data/Tag | [SCF Cache HAS](https://docs.intel.com/documents/iparch/scfcache/HAS/Gen4/releases/R2204/HAS/SCFCACHE_HAS.html#interfaces) |
| PWB | AMA | Cache Data/Tag | [SCF Cache HAS](https://docs.intel.com/documents/iparch/scfcache/HAS/Gen4/releases/R2204/HAS/SCFCACHE_HAS.html#interfaces) |
| HMA-SF | HMA | Cache Data/Tag | [SCF Cache HAS](https://docs.intel.com/documents/iparch/scfcache/HAS/Gen4/releases/R2204/HAS/SCFCACHE_HAS.html#interfaces) |

---

## I3C_SPD Memory Controller Mapping

- **4 I3C_SPD controller instances** (same as DMR)
- Each instance maps to **8 memory controllers**
- I3C_SPD-to-MC mapping: [NWP Global ID Excel, "I3C MC Mapping" sheet](https://intel.sharepoint.com/:x:/r/sites/nwp/_layouts/15/Doc.aspx?sourcedoc=%7B1E76F6F8-6F29-4046-9169-9BC8737E5E42%7D&file=nwp_imh_global_id.xlsx&action=default&mobileredirect=true)
- Used by **BIOS during boot** for memory discovery: DIMM/SOCAMM type, speed, timing, config parameters for memory init and training
- **Key NWP delta**: No TSOD polling for temperature, no I3C_SPD error recovery flow
  - DRAM refresh rates via **MR4** (for CLTT)
  - Temperature reading via **MR109**
  - References: [NWP PAS - SPD Bus](https://docs.intel.com/documents/custom-xeon/newport-docs/platform/pas/NwpPAS.html#spd-bus), [NWP HAS - Memory Feature List Delta](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#nwp-memory-feature-list-delta)

---

## DFD Support

SCF SubIPs support:
- **VISA** — debug signal capture
- **Triggers** — debug event triggers

Each SCF SubIP interface HAS documents the specific debug interfaces. Full DFD fabric details in DFD MAS.

---

## PM-Relevant Observations

1. **I/O Voltage Domain split** (1→2 in NWP) affects PM domain management and DVFS strategy
2. **TQ instances** between voltage domains require fuse-controlled pointer separation — PM reset/safe_mode must handle these
3. **Single PLL (UclkMem)** for Mem+CAB fabric simplifies DVFS but changes frequency domain boundaries vs DMR
4. **qActive aggregation** for cache IPs (HSF, HMA-SF, PWB, IOCA LLC) requires full Q-channel at SoC level — impacts idle detection and power gating
5. **16 ISA_SCF instances** route config_done/safe_mode to all 423 SubIPs — any routing error blocks SCF from exiting reset
6. **CAB fabric power-gating** — C2C MBVR (VCCC2C) must power down before FIVRs on cold reset entry (per NWP PAS)
7. **NIO PM DVFS anchors**: [14024876702](https://hsdes.intel.com/appstore/article-one/#/14024876702) — Power Plane/Freq domain/PM DVFS strategy for NIO

---

## NIO PM Overview

> **Source**: [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/NWP_IMH_SOC_PM_MAS.html), [[NWP] NIO: Power Plane/Freq domain implementation](https://hsdes.intel.com/appstore/article-one/#/article/14024641958)

NIO has **significant changes** to Clock and Voltage Domains vs DMR IMH1/IMH2/IOH, driven by:

### Key Architectural Drivers
- **Strict customer KPIs** for Mesh and Memory domain performance
- Major **Mesh/SCF topology changes** (I/O Mesh, Mem Mesh redesign, new CAB fabric)
- **LPDDR6 memory** (replaces DMR DDR5/MR) — entirely new memory subsystem
- **CAB + GRS/C2C blocks** added (Nimbus accelerator connectivity)
- **6 MIO stacks** (replaces DMR's 4 I/O + 2 ACC stacks)
- IP **buffer and queue size increases** across many IPs to meet customer BW KPIs

### Voltage Domain Changes (vs DMR IMH)
- **I/O voltage domain split** from 1 → 2 domains (VCCCFC_IO_E and VCCCFC_IO_W)
- **New CAB voltage domain** (VCCCFC_CAB) — separate from Mem and I/O domains
- **New C2C voltage domain** with dedicated MBVR (PVCCC2C at SVID 05h)
- **New digital domain** VCCFCFCAB — ITD supported on this new domain
- TQ (Transfer Queue) instances at each voltage domain boundary require fuse-controlled pointer separation

### Frequency Domain Changes (vs DMR IMH)
- **No UFS (Uncore Frequency Scaling)** — Mesh (Mem + I/O) and CAB **fixed at 2 GHz** ([HSD 14024876702](https://hsdes.intel.com/appstore/article/#/14024876702))
  - *Actual freq for PRQ may deviate based on silicon performance*
- **Single PLL (UclkMem)** sources both Mem Mesh and CAB Mesh (DMR had separate clocks)
- **Dedicated MCPLL per memstack** — sources MC clock and DFI clock (replaces PHY PLL sourcing)
- **C2C has dedicated clock domain** (C2C CLK)
- I/O Fabric remains on IO_UCLK (unchanged from DMR)

### PM Feature Impact Summary

> **Source**: [NWP PRD](https://goto.intel.com/nwp.prd), [NWP PM MAS §3](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/NWP_IMH_SOC_PM_MAS.html#major-changes-from-dmr-product), [NWP HAS ZBB List](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#zbb-list)

#### NWP Supported PM Features (PRD Priority P0)

| Feature | PRD Priority | Same as DMR | Ownership | Notes |
|---------|-------------|-------------|-----------|-------|
| Core C6 | P0 | Yes | Core+SA+Uncore | Needed — customer wants some idle support |
| System state S0, S5 | P0 | Yes | Core+SA+Uncore | Required. No S3 (same as DMR) |
| HWP P-state limits via PCS | P0 | Yes | — | Limit min/max P-state bookends for HW-P via OOB (BMC) |
| Socket RAPL (PL1/PL2) | P0 | Yes | — | PL1 1s TW, PL2 12ms TW. No change from DMR |
| PCT (SST-TF profile) | P0 | Yes | — | Per MAS §3 |
| Thermal Protection | P0 | Yes | — | ProcHot, Thermtrip, Memtrip |
| ITD | P0 | — | — | On new digital domain VCCFCFCAB |

#### NWP ZBB Features (PRD: Not Required / TBD → ZBB'd)

| Feature | PRD Req | ZBB HSD | Customer Rationale |
|---------|---------|---------|-------------------|
| Core C3 | Remove | — | DMR does not support C3 either |
| PkgC6 | NR | [22021155362](https://hsdes.intel.com/appstore/article/#/22021155362) | Customer not sensitive to idle power; no customer requirement. Supporting would require extending flow to new IPs |
| PkgC6 exit latency | NR | [22021155185](https://hsdes.intel.com/appstore/article/#/22021155185) | Need to understand customer KPI for exit latency. Can we move to GPU-driver-hint model? |
| PCIe L1 (ASPM) | TBD→ZBB | [22021155368](https://hsdes.intel.com/appstore/article/#/22021155368) | Customer confirmation to ZBB |
| PCIe L0p | TBD→ZBB | [22021155360](https://hsdes.intel.com/appstore/article/#/22021155360) | Customer confirmation to ZBB |
| UXI L1/L0p | TBD→ZBB | [22021155419](https://hsdes.intel.com/appstore/article/#/22021155419) | Only x8 UXI — minimal power savings |
| Core C1e | TBD→ZBB | — | **⚠️ PRD says ZBB candidate, but MAS §3 lists C1e as supported (C0, C1, C1e, C6)** — needs reconciliation |
| Mem PM (APD/PPD/SSR/DSREF) | TBD→ZBB | [22021155412](https://hsdes.intel.com/appstore/article/#/22021155412) | Customer confirmation to ZBB |
| MemCLOS | TBD→ZBB | — | Customer has no prior history of using this feature |
| ADR | TBD→ZBB | [22021155420](https://hsdes.intel.com/appstore/article/#/22021155420) | Customer has no prior history; no PMEM use case |
| Platform RAPL / Psys | TBD→ZBB | [22021155415](https://hsdes.intel.com/appstore/article/#/22021155415) | Customer confirmation to ZBB |
| SST-PP/BF/CP | TBD→ZBB | [22021155414](https://hsdes.intel.com/appstore/article/#/22021155414) | Customer has no prior history of using this feature |
| DRAM RAPL | Fused off | [14025012732](https://hsdes.intel.com/appstore/article-one/#/article/14025012732) | No standalone DRAM power domain (LPDDR6) |
| Favored Core / DCM | ZBB | [22021155183](https://hsdes.intel.com/appstore/article/#/22021155183) | Not required |
| TMUL | ZBB | [22021155122](https://hsdes.intel.com/appstore/article/#/22021155122) | Not required |
| UFS (Mesh DVFS) | ZBB | [14024876702](https://hsdes.intel.com/appstore/article/#/14024876702) | Fixed 2 GHz — no frequency scaling |
| C2C link power savings | N/A | — | Not in customer datasheet |

### Power Plane / Freq Domain Details
Full implementation details: [[NWP] NIO: Power Plane/Freq domain implementation (HSD 14024641958)](https://hsdes.intel.com/appstore/article-one/#/article/14024641958)

---

*[val_agent] Created 2026-05-30 from NWP SCF MAS topology data*
