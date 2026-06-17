# NWP Memory IO Stack — MAS Summary

**Source**: [NWP Memory IO (DDRIO) Stack MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/MC/Memory_IO_Stack_MAS.html)
**Author**: Howard Chang, Rev 0.5, May 19, 2026
**Date**: 2026-05-30

---

## 1. Overview
- NWP memory system uses **LPDDR6** (LP6) — first Intel server platform with LPDDR6
- Each MC channel paired with a **CDS LP6 x48 PHY** (Cadence IP)
- Aggregate BW: **2.04 TB/s** (63.84 GB/s × 32 channels) at **10640 MT/s**
- memstack contains: LP6 PHY, LP6 MC (Gen6), MSE, MCCMI wrappers, RAT, Buttress, DTS, TQ, global infrastructure

## 2. Memory Stack Topology
- **16 memstacks** total per NWP IMH
- Each memstack: **2 MC channels** with 2 CDS LP6 x48 PHY → **32 MC channels** total
- Depopulation modes: 24, 16, and 4 channel configurations
- One **RAT** block shared per 2 channels within a memstack

## 3. LPDDR6 PHY (CDS)
- **Cadence (CDS) LPDDR6 x48 PHY** — 2 per memstack (1 per MC channel)
- Data width: **x48** (32 data + 7b ECC)
- Max data rate: **10640 MT/s**
- PHY has **built-in microcontroller** (Tensilica) with external **iRAM/dRAM** (64K×39b each, 7-bit ECC)
- Firmware download via Buttress APB indirect access
- Training: PHY handles PLL lock, calibration, DRAM training internally; reports via `dfi_init_complete`
- Frequency change: `freq_change_req` + `freq_change_type` (2 requests during boot)

## 4. Power Domains

| Domain | Voltage | Source | Supplies |
|--------|---------|--------|----------|
| **VCCDDRDIG** | **0.77V** | **MBVR** | LP6 PHY digital |
| **VCCFIXDIG** | 0.9V | On-die FIVR | MC, MCPLL, ASF |
| **VCCCFCMEM** | 0.5–0.85V | On-die FIVR | MSE, ASF, MISC |
| **VCCINF** | 0.7V | MBVR | Infrastructure |
| **VCCFA_EHV** | 1.8V | MBVR | MCPLL, MISC analog |
| **VCCDDQC** | 1.0V | MBVR | PHY I/O |
| **VCCDDQD** | 0.875V | MBVR | PHY I/O |
| **VCCDDQ** | 0.5V | MBVR | PHY I/O |

- **Key change**: Split voltage MC (VCCFIXDIG 0.9V) / PHY (VCCDDRDIG 0.77V MBVR) — TQ for voltage crossing on DFI

## 5. Buttress
- **PIC9 AIC Buttress IP** — bridges IOSF sideband to 2 x48 PHY APB slaves
- Supports **S3M firmware patch flow** (IOSF handshake for iRAM/dRAM loading)
- PHY register space: **1 MB APB range** (paddr[19:0]) — DMR was 64KB
- SOC maps **32 MB total** across all 32 LP6 PHYs

## 6. ISA_MC Spare Bits — PHY freq_change_req/ack

`ip_isa_spare_strapcfg` bus:
- **[0]**: PHY0 `sys_interrupt` (calibration done)
- **[8]**: PHY0 `freq_change_req`
- **[15:10]**: PHY0 `freq_change_type`
- **[16]**: PHY1 `sys_interrupt`
- **[24]**: PHY1 `freq_change_req`

`isa_ip_spare_strapcfg`:
- **[1][4]**: PHY0 `freq_change_ack`
- **[1][5]**: PHY1 `freq_change_ack`
- **[1][0]**: `phy_clk_div4_sel` (clock mux)
- **[1][10]**: `mc2xclk_adop_disable` (PLL relock gate)

**Flow**: PCode polls ISA for `freq_change_req` → disables MCPLL ADOP → reprograms RA → reconfigures dividers/mux → waits for lock → re-enables ADOP → writes `freq_change_ack`

## 7. DTS
- **New DTS HIP** in memstack `pardfi` partition (new vs DMR)
- Collects `parmemsram` TSDIODE and nearby SOC `parscfmemfivr` TSDIODE
- Dedicated RSTW, FPC_CRI, and RA for DTS
- 1 TSDIODE + 1 DTS per memstack
- RA on **PMSB** (`DTS_RA_IOSF`)

## 8. PM Features
- **PkgC6: DISABLED**
- **SSR (Shallow Self Refresh): DISABLED**
- **DSREF (Deep Self Refresh): DISABLED**
- **APD / PPD: DISABLED** (HSD 22021155412)
- MC issues **Self Refresh without clock stop** prior to Warm Reset only
- **P-Channel Distributor**: 2 P-channel targets (mcsched0/1 common wrappers) → ISA_MC
  - P-state encoding: `3'h5` = PkgS3/S4/S5/WR, `3'h6` = ADR
- **Q-channel clock gating**: per-IP aggregators for dficlk, uclk_mem domains
- Clock gating via ADOP/PDOP/RDOP throughout

## 9. Sideband Topology

| Endpoint | Bus | Instances |
|----------|-----|-----------|
| RAT_IOSF | GPSB | 1 |
| MCTRK_IOSF | GPSB | 2 |
| MSE_IOSF | GPSB | 2 |
| MCCMI_UPSTR/DNSTR_IOSF | GPSB | 2+2 |
| ISA_MC_IOSF | GPSB | 1 |
| PHY_BTRS_IOSF | GPSB | 1 |
| MCPLL_RA_IOSF | PMSB | 1 |
| DTS_RA_IOSF | PMSB | 1 |

Total: **13 SB endpoints** per memstack. LP6 PHY via **4 APB endpoints** through buttress.

## 10. Key Deltas from DMR

| Area | Delta |
|------|-------|
| **Memory type** | LPDDR6 replaces LPDDR5X — CDS PHY with built-in MCU |
| **Split power domains** | MC on VCCFIXDIG (0.9V), PHY on new VCCDDRDIG (0.77V MBVR) + TQ crossing |
| **Dedicated MCPLL** | Per memstack (replaces PHY PLL sourcing) |
| **New `pardfi` partition** | DFI bus repeaters, SB repeaters, DFD patrace, DFT |
| **New DTS** | Inside memstack (parmemsram + parscfmemfivr TSDIODEs) |
| **Two ISA_MC P-channels** | mcsched0_common + mcsched1_common (new) |
| **Removed** | HAMVF-to-MC subchannel flip, MMC (replaced by LP6 MCU) |
| **Reduced MSE MKTME keys** | 2048 → 1028 |
| **Disabled PM** | PkgC6, SSR, DSREF, APD, PPD |
| **PHY register space** | 64KB → 1MB per PHY |

## 11. Key Registers

| Register | Purpose |
|----------|---------|
| `ip_isa_spare_strapcfg[0]` | PHY0 sys_interrupt |
| `ip_isa_spare_strapcfg[8]` | PHY0 freq_change_req |
| `ip_isa_spare_strapcfg[15:10]` | PHY0 freq_change_type |
| `isa_ip_spare_strapcfg[1][4:5]` | PHY0/1 freq_change_ack |
| `isa_ip_spare_strapcfg[1][0]` | phy_clk_div4_sel |
| `isa_ip_spare_strapcfg[1][10]` | mc2xclk_adop_disable |
| `TARGET_CLKI.PLL_MODE/.RATIO` | MCPLL configuration |
| `PLL_OVRD_CTRL.PLL_BYPASS_OVRD_*` | PLL bypass override |
| `ucctrlreg→uccore_csr0/1/2` | PHY FW download control |
| `phycmnreg→phy_glb_errsts_csr*` | PHY error status |
