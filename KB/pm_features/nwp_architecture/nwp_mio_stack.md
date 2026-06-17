# NWP MIO Stack — Architecture Summary

**Source**: [NWP NIO MIO MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/MIO/NWP_NIO_MIO.html)
**Date**: 2026-05-30

---

## 1. Overview

- **MIO = Multiple System Input-Output Stack**, leveraged from DMR IMH2 UIO_A stack
- **7 IO stacks total**: ACC0 + 6 MIO stacks (MIO1–MIO6)
  - **5 × UIO_A** (MIO1, MIO2, MIO4, MIO5, MIO6) — full-featured: x16 PCIe/CXL Gen6 or x16 UXI or flex x8+x8
  - **1 × UIO_E** (MIO3 / P3) — x8 UXI-only (area-constrained)
- **IPs per UIO_A**: IOMMU, HAP, HIOP (CPC/ITC/OTC), HIOP ASF, IOMMU ASF, CXL ASF, FBLP, CXL, UXI/ULA, PCIe Gen6 (8-port), CEE, UFI static mux, avephy buttress, 2× x8 avephy
- **IPs in UIO_E (reduced)**: UXI/ULA, FBLP, CEE, CXL ASF, avephy buttress, 2× x4 avephy, 2× CMLBUF. **Removed**: IOMMU, HIOP, PCIe, CXL, HAP
- Each stack has its own **unique FIVR** (delta from DMR where FIVRs were shared across northcaps)

## 2. PM-Relevant Features

- **Q-channel interfaces** for clock gating managed by RC:
  - `qaggr_mio_lfclk` — LFCLK quiesce
  - `qaggr_mio_uclk_io` — uclk IO quiesce (aggregates CXL, IOMMU, HIOP ASFs)
  - `qaggr_mio_lfclk_dvp` — DVP q-channel
- **P-channel** for UXI/ULA: 3-bit pstate
- **ISA (IP State Aggregator)**: drives `o_safemode` per IP for clock-gate wake
- **DTS moved outside the MIO stack** for NWP — DTS RA PMSB endpoint removed
- **Power domains**: VCCINF, VCCFIXDIG, VCCCFCIO; VCCFCMEM clocks removed
- **ZBB'd PM features**: PkgC6, UXI L0p, PCIe L0p, PCIe L1, UPI Dynamic Link Width Reduction, ADR, QPI Quiesce

## 3. GPSB/PMSB Sideband

- **GPSB per UIO_A**: HIOP, IOMMU, CXLCM, PCIE, ULA, CEE, FLEXBUS LOGPHY, Buttress, MIO ISA, HAP
- **PMSB per UIO_A**: LFCLK PLL RA (DTS RA removed for NWP)
- **UIO_E**: reduced set (ULA, CEE, FBLP, Buttress, ISA on GPSB; LFCLK PLL RA on PMSB)
- Sideband IPs at **500 MHz** on VCCFIXDIG; infra at **400 MHz**
- FSAs moved outside stack (can't be MI'd)
- **Global ID mapping**: MIO1=C4, MIO2=C5, MIO3=C6, MIO4=C7, MIO5=C8, MIO6=C9

## 4. PCIe/CXL

- **80 lanes total** Gen6 across 5 UIO_A stacks (x16 configurable as x8+x8 or x16)
- **8 root ports per UIO_A stack**
- **UIO_E (P3)**: x8 UXI only, no PCIe/CXL
- **VMD 3.0 ZBB'd**; **NTB ZBB'd**
- CXPSMB: single instance for all 6 stacks (NPEM removed)

## 5. UXI/D2D

- UXI/ULA present in all stacks
- **UIO_E (P3)**: x8 UXI only — `ula_link_ctrl.full_link_width = 4'b010`
- D2D UFI repeaters from DMR **removed**
- **UXI L0p ZBB'd**; UPI link hot-plug ZBB'd; UPI PhyL0Sync ZBB'd

## 6. Delta from DMR IOH/MIO

| Change | Detail |
|--------|--------|
| **IMH count** | DMR: 2× IMH. NWP: single NIO die with 6 MIO stacks |
| **New UIO_E (P3)** | x8 UXI-only; removes IOMMU, HIOP, PCIe, CXL, HAP |
| **HAP/TDX integration** | New HAP IP in each UIO_A for TDX Connect |
| **DTS moved outside stack** | DTS RA PMSB endpoint removed |
| **Unique FIVR per stack** | DMR shared FIVRs; NWP each stack has own FIVR |
| **D2D UFI repeaters removed** | No UFI pass-through for D2D stack |
| **VCCFCMEM clocks removed** | `uclk_mem_in` and mem repeater clocks removed |
| **FBLP pipeline stages added** | 2GHz+1GHz repeaters on RX, 1GHz on TX |
| **io_demand** | One per stack (DMR aggregated stacks 0+2) |
| **ZBB'd features** | PkgC6, UXI L0p, PCIe L0p, PCIe L1, UPI Dynamic LW, VMD, NTB, ADR |

## 7. Key Registers

- `ula_link_ctrl.full_link_width` — x8 for P3 stack
- `FBLP.BIFCTL0` — port bifurcation (program `0x24` for P3)
- `IC_OUTBOUND_DECODE_CTRL_i` — HAP decode control
- `ATS_EXT_ACC_0/1` — HAP accelerator port registers
- `CAPID` — 4-bit per stack: `0110`=UIO_A, `0100`=UIO_E

## 8. RC Mapping

- RC → `qaggr_mio_lfclk` → LFCLK domain IPs
- RC → `qaggr_mio_uclk_io` → uclk IO domain IPs (CXL, IOMMU, HIOP ASFs)
- RC → `qaggr_mio_lfclk_dvp` → DVP IPs
- P-channel: RC → ISA → UXI/ULA
- PMSB RAs: LFCLK PLL RA (present); DTS RA (**removed**)
