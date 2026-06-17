# NWP NIO PM Architecture — MAS Summary

**Source**: [NWP IMH SOC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/NWP_IMH_SOC_PM_MAS.html)
**Author**: Steven S Chang, May 19, 2026
**Date**: 2026-05-30

---

## 1. Overview
- **Newport (NWP)** consists of two 48-core NWP CBBs and one NIO (Newport IMH) SOC die
- NIO derived from **DMR IMH2** with major changes: LPDDR6, new SCF/mesh topology, CAB + GRS/C2C, 6 MIO stacks
- Only **1 NIO per package** (unlike DMR IMH1+IMH2+IOH); supports 1S or 2S
- NWP CBB PM flows are **100% leveraged from DMR CBB** — no CBB PM changes
- PrimeCode FW runs on same **Gen4 PUNIT**; firmware leveraged from DMR with ZBB'd flows disabled
- NIO on **Intel 3 process** (same as DMR IMH2)
- **Max TDP: 450W, Nominal TDP: 350W**

## 2. RC (Resource Controller) Topology

All 5 RCs use the **lnpv** Gen4 RC variant.

| RC | Variant | Manages |
|---|---|---|
| **RC_MEM_W** | lnpv | West MC[0-7], VCCFIXDIG_W FIVR, 8 MC LJPLLs, ISA_MC[7:0], LPDDR6 PHY digital (west) |
| **RC_MEM_E** | lnpv | East MC[8-15], VCCFIXDIG_E FIVR, 8 MC LJPLLs, ISA_MC[15:8], LPDDR6 PHY digital (east) |
| **RC_MIO** | lnpv | MIO1-6 controllers & PHYs, 6 VCCFIXDIG_MIO FIVRs, 6 LF_CLK LJPLLs, Gen4 Legacy controller, ISA_UIO[1-6], ISA_MISCC |
| **RC_CFCIO** | lnpv | IO Fabric (W+E), CA/LLC, VCCCFCIO_{W,E} FIVRs, UCLK_IO LJPLL, ISA_LLC{W,E}, ISA_SCF{IO,P2P,PWP} |
| **RC_CFCMEM_EW** | lnpv | MEM Fabric (W+E), MSE, HAMVF, D2D UCIe, CAB, C2C; VCCCFCMEM_{W,E}, VCCCFCCAB, VCCFIXDIG_UCIE_{NW,NE}, VCCC2CDIG FIVRs; UCLK_MEM LJPLL, 4 UCIe PHY IOCLKs, C2C LJPLL |

**Key delta from DMR:** No Pchannel connectivity between PUNIT and RCs (NIO does not support PkgC6 or MBVR actions).

## 3. FIVR Inventory

All Gen4.0 FIVRs, same IP as DMR IMH2:

| FIVR Global Name | Type | Rail |
|---|---|---|
| fivr_vcccfcio_w / _e | Stacked 80-bump | VCCCFCIO (IO mesh) |
| fivr_vcccfcmem_w / _e | Stacked 80-bump | VCCCFCMEM (MEM mesh) |
| fivr_vcccfccab | Inline 80-bump | VCCCFCCAB (CAB domain) |
| fivr_vccfixdig_w / _e | 48-bump inline | VCCFIXDIG (MC) |
| fivr_vccfixdig_mio0..5 | 20-bump stacked (MIO2=16-bump) | VCCFIXDIG_MIO |
| fivr_vccfixdig_ucie_nw / _ne | 32-bump stacked | VCCFIXDIG_UCIE (D2D PHY) |
| fivr_vccc2cdig | Inline 80-bump | **VCCC2CDIG (NEW — C2C digital)** |

**Note:** FIVR_MIO_3 and FIVR_MIO_4 must be controlled **directly by PrimeCode** (RC NUM_VR=4 constraint). HSF0/HSF1 PLLs are **not** controlled by RC.

## 4. Power Domains

| Domain | Scope |
|---|---|
| VCCCFCIO_{W,E} | IO mesh fabric |
| VCCCFCMEM_{W,E} | Memory mesh fabric |
| VCCCFCCAB | CHI Accelerator Bridge |
| VCCC2CDIG | **NEW** — C2C digital SIP |
| VCCFIXDIG_{W,E} | MC + LPDDR6 PHY digital |
| VCCFIXDIG_MIO[0-5] | Per-MIO stack |
| VCCFIXDIG_UCIE_{NW,NE} | UCIe D2D PHY |
| VCCDDRDIG | **NEW** — LPDDR6 PHY digital (MBVR 0.77V) |
| VCCINF | OOBMSM, HIOP, NPK, TAM |

## 5. Supported PM Features

- **P-states:** HWP, Pn → P1 → P0n → P04 range
- **Core C-states:** C0, C1, C1e, C6
- **Package states:** PkgS0, PkgS5 (no PkgC6)
- **Socket RAPL:** PL1 (1s TW), PL2 (12ms TW)
- **Thermal protection:** ProcHot, Thermtrip, Memtrip, Memhot
- **SST-TF:** Priority Core Turbo (PCT) profile
- **ITD:** On VCCFCFCAB (new) + existing DMR rails
- **SVID:** Active for most rails
- **Telemetry:** Per-RC telemetry via Gen4 RC (up to 160 indexes)
- **DTS:** Comprehensive coverage

## 6. ZBB (Not Supported) Features

| Feature | Status | HSD |
|---|---|---|
| **UFS** | ZBB — Mesh & CAB fixed at 2 GHz | 14024876702 |
| **PkgC6** | ZBB — fused off | 22021155362 |
| **Idle Power** | No requirements | 22021155185 |
| **PCIe L1** | ZBB | 22021155368 |
| **HSIO L0p** | ZBB | — |
| **UXI L1/L0p** | ZBB | — |
| **Memory PM** (APD/PPD/LPM/SSR/SR) | ZBB | 22021155412 |
| **DRAM RAPL** | Fused off | 14025012732 |
| **Platform RAPL / Psys** | Not supported | 22021155415 |
| **ADR** | Not supported | 22021155420 |
| **SST-PP/BF/CP** | Not supported | — |
| **Favored Core** | Not supported | — |
| **DCM** | Not supported | — |

## 7. PrimeCode Flow

- **Post-boot Active WP:** PrimeCode reads RA CURRENT_VRCI/CURRENT_CLKI → programs RC CR_VR_WP_ACTIVE[0] and CR_CLK_WP_ACTIVE[0] → sets FORCE_ACTIVE_TV_CV_COPY → enables QVFS
- **IP Disable:** If RA returns CMPL_STATUS=2 (IP held in reset), PrimeCode skips WP programming
- **UFS ZBB:** NIO keeps IO mesh and MEM mesh at fixed 2 GHz. UFS still used internally as control knob for PL1/thermal throttling safety
- **PkgC ZBB:** PkgC6 fused off; no idle WP entry/exit flow. NIO removes Pchannel PUNIT↔RC connectivity entirely

## 8. Telemetry

| RC | NUM_TELE_INDEXES |
|---|---|
| RC_MEM_W | **160** |
| RC_MEM_E | **160** |
| RC_MIO | **64** |
| RC_CFCIO | **128** |
| RC_CFCMEM_EW | **160** |

All increased from DMR due to more MR4_TEMP entries, larger mesh, and additional DTS sensors.

## 9. DTS Sensors

- **Memory MC DTS:** DTS_MEM_{NW,NE,SW,SE}[0-3] — 16 total
- **D2D DTS:** DTS_D2D{NE,NW} — D2D_1, D2D_3 (NE), D2D_0, D2D_2 (NW)
- **MIO Infrastructure DTS:** DTS_MIOINF{1W,3W,3E}
- **C2C DTS:** DTS_C2C0 (ch 0-5), DTS_C2C1 (ch 8-13)
- **CGU/Always-On DTS:** DTS_AO (final in thermtrip daisy chain)
- **Center Infrastructure DTS:** DTS_CINF0
- **TSRD:** Horizontal diodes at multiple locations

## 10. Thermal Management

Same as DMR: XX_THERMTRIP_N, XX_MEMTRIP_N, XX_MEMHOT_{IN/OUT}_N, XX_PROCHOT_N, EMTTM, VR_HOT

## 11. SVID Rails

| Rail | SVID Address | Notes |
|---|---|---|
| VCCIN | SVID0/01h | No change |
| VCCINF | SVID0/02h | No change |
| VCCANA | SVID0/03h | No change |
| **VCCFA_EHV** | **N/A** | **Removed from SVID** (HSD 14027235624) |
| **VCCC2C** | SVID0/05h | **NEW** (HSD 14027373379) |

## 12. New NWP-Specific Items

- **LPDDR6 CDS PHY:** New memory stack replacing DDR5; PHY digital on VCCDDRDIG via MBVR
- **Buttress APB access:** For TDX HAP integration in MIO
- **ISA_MC spare bits:** LPDDR6 MC Pstate power table integration
- **TQ voltage crossing:** New domain boundaries (VCCC2CDIG, VCCCFCCAB)
- **MBVR for VCCDDRDIG:** No FIVR, power from platform (HSD 14026585116)
- **VCCC2CDIG FIVR:** New 80-bump inline (HSD 22021977883)
- **C2C LJPLL:** New PLL for UCLK_C2CSIP

## 13. Key Deltas from DMR

| Area | DMR | NWP NIO |
|---|---|---|
| **SOC die** | IMH1 + IMH2 + IOH (3 dies) | Single NIO die |
| **Memory** | DDR5 | LPDDR6 only (new MC + PHY) |
| **Memory PM** | APD/PPD/LPM/SSR/SR supported | All ZBB'd |
| **Mesh frequency** | DVFS via UFS | Fixed 2 GHz (UFS ZBB) |
| **PkgC6** | Supported (MBVR ZBB'd late) | Fused off; Pchannel removed |
| **PCIe L1** | Supported | ZBB'd |
| **UXI L1/L0p** | Supported | ZBB'd |
| **DRAM RAPL** | Supported | Fused off |
| **Platform RAPL/Psys** | Supported | ZBB'd |
| **ADR** | Supported | ZBB'd |
| **SST** | PP/BF/CP/TF | Only SST-TF (PCT) |
| **VCCFA_EHV** | On SVID | Removed from SVID |
| **VCCC2CDIG** | N/A | New FIVR + SVID rail |
| **VCCDDRDIG** | N/A | New MBVR-delivered rail |
| **UCIe D2D** | 24 GT/s | 32 GT/s |
| **ITD** | Existing rails | Added VCCFCFCAB |
| **Telemetry** | Smaller per-RC | Increased sizes |
| **FIVR_MIO_3/4** | RC-controlled | PrimeCode-controlled |
