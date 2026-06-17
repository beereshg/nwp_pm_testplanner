# NWP NIO PM Telemetry — Delta Analysis from DMR

**Source**: [NWP IMH SOC PM MAS §8](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/NWP_IMH_SOC_PM_MAS.html#nio-pm-telemetry)
**Telemetry spreadsheet**: [NWP_IMH_Telemetry.xlsx](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/assets/NWP_IMH_Telemetry.xlsx)
**DMR reference**: [DMR Telemetry HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Telemetry.html)
**MAS version**: 0.73 (2026-05-18)
**TPF**: [22022420495 — IMH PM Telemetry](https://hsdes.intel.com/appstore/article/#/22022420495)
**Date**: 2026-05-30

---

## 1. Architecture: Same 5 RCs, Increased NUM_TELE_INDEXES

NWP keeps the same 5 RC topology as DMR IMH1/IMH2, but every RC's NUM_TELE_INDEXES has grown:

| RC | NWP NUM_TELE_INDEXES | Indexes Used | Content Summary |
|---|---|---|---|
| **RC_MC_E** | 160 | 128 | MR4_TEMP for MC_8 through MC_15 (east memory stacks) |
| **RC_MC_W** | 160 | 128 | MR4_TEMP for MC_0 through MC_7 (west memory stacks) |
| **RC_MIO_EW** | 64 | 64 | UXI BW, SVID accumulators, DTS sensors |
| **RC_CFCIO** | 128 | 126 | CFC mesh traffic (CRS), UBR BW (HIOP/IOMMU/CXL) |
| **RC_CFCMEM_EW** | 160 | 152 | CFC mesh traffic (CRS/CMS/CAB), UBR D2D BW, DTS, VCCC2C |

**Total**: 598 telemetry entries across all 5 RCs (all status = Ready).

---

## 2. RC_MC_E and RC_MC_W — MR4_TEMP Expansion

Each MC RC now covers **16 sub-channels** (vs DMR's lower count), with **4 MR4_TEMP entries per sub-channel**, split into LO/HI = 128 entries per RC.

### MC-to-subch mapping:
| Sub-channel [n] | RC_MC_E Pull IP | RC_MC_W Pull IP |
|---|---|---|
| [0]-[1] | MCTRK_COMMON_0/1_MC_8 | MCTRK_COMMON_0/1_MC_0 |
| [2]-[3] | MCTRK_COMMON_0/1_MC_9 | MCTRK_COMMON_0/1_MC_1 |
| [4]-[5] | MCTRK_COMMON_0/1_MC_10 | MCTRK_COMMON_0/1_MC_2 |
| [6]-[7] | MCTRK_COMMON_0/1_MC_11 | MCTRK_COMMON_0/1_MC_3 |
| [8]-[9] | MCTRK_COMMON_0/1_MC_12 | MCTRK_COMMON_0/1_MC_4 |
| [10]-[11] | MCTRK_COMMON_0/1_MC_13 | MCTRK_COMMON_0/1_MC_5 |
| [12]-[13] | MCTRK_COMMON_0/1_MC_14 | MCTRK_COMMON_0/1_MC_6 |
| [14]-[15] | MCTRK_COMMON_0/1_MC_15 | MCTRK_COMMON_0/1_MC_7 |

- All entries are 4-byte Mem Rd via `mc_iosfsb` at offsets 0x1700-0x171C
- Push via PUNIT PMSB, pull via MCTRK sideband
- **tele_ignore_quiesce = 0** (pulled during PC6), **accumulate = 0**, **enable mask = 1/1** for both IMH1/IMH2

---

## 3. RC_MIO_EW — UXI BW, SVID, DTS

64 entries organized as:

### 3.1 UXI BW Counters (Indexes 0-23)
- **6 UXI links** (MIO_1 through MIO_6) — unchanged from DMR
- TX counters (LO/HI, 8 bytes each, accumulated) at offset 0x300/0x304
- RX counters (LO/HI, 8 bytes each, accumulated) at offset 0x308/0x30C
- **tele_ignore_quiesce = 0, accumulate = 1** — these are bandwidth counters

### 3.2 SVID Accumulators (Indexes 24-37)
| Index | Rail | Type | SVID Slot | Notes |
|---|---|---|---|---|
| 24-25 | VCCFIXDIG_E | I_OUT | [0] | East die fixed digital |
| 26-27 | VCCIN | I_OUT | [1] | Main input voltage |
| 28-29 | VCCANA | I_OUT | [2] | Analog rail |
| 30-31 | VCCINF | I_OUT | [3] | Infrastructure rail |
| 32-33 | PSYS_EHV | P_IN_ENERGY | [13] | Platform system power |
| 34-35 | VCCFIXDIG_W | I_OUT | [4] | West die fixed digital |
| 36-37 | VCCFIXDIG_W | P_IN_ENERGY | [4] | **Enable mask = 0/0** (disabled by default) |

**Key delta**: 
- **VCCFC_EHV rail removed** — "no more telemetry reads for VCCFC_EHV rail"
- **VCCC2C not in RC_MIO_EW** — moved to RC_CFCMEM_EW
- VCCFIXDIG_W P_IN has **enable mask 0/0** — disabled for both die variants

### 3.3 DTS Sensors (Indexes 38-63)
| Indexes | DTS Location | Count |
|---|---|---|
| 38-39 | D2D NW (D2D_0, D2D_2) | 2 |
| 40-41 | D2D NE (D2D_1, D2D_3) | 2 |
| 42-43 | MIOINF3W (P1, P2) | 2 |
| 44-45 | MIOINF1W (P34, P5) | 2 |
| 46-47 | MIOINF3E (P6, P7) | 2 |
| 48-63 | Memory DTS (NW 0-3, SW 0-3, NE 0-3, SE 0-3) | 16 |

- All 26 DTS entries read DFVFReg1/DFVFReg2 via RA_DTS_* resource adapters
- **tele_ignore_quiesce = 1, accumulate = 0** — temperature snapshots, not accumulated

---

## 4. RC_CFCIO — Mesh IO Traffic + UBR BW

128 entries (126 used):

### 4.1 CFC CRS Mesh Traffic (Indexes 0-29)
- 30 CRS nodes from CRS_40 through CRS_69 (IO mesh fabric)
- Reading `ufsMMcounter` (Max_Traffic_Count) — 8 bytes each, accumulated
- Covers columns 7-12 (c7r0 through c12r8)
- **Enable mask varies**: indexes 23-29 have **IMH1=0** (only present on IMH2/NIO-E die variant)

### 4.2 UBR BW Counters (Indexes 30-125)
96 UBR bandwidth counters organized by IP group:

| IP Group | HIOP Stacks | UBR Instances | Counters Per Stack |
|---|---|---|---|
| **HIOP** | 0(Type2), 1, 2, 5, 6, 7 | UBR_18-24 | A2F_REQ, A2F_NON_P2P, A2F_P2P, F2A_REQ, F2A_NON_P2P, F2A_P2P |
| **IOMMU** | 0(Type2), 1, 2, 5, 6, 7 | UBR_18-24 | Same 6 counter types (different offsets) |
| **UXI/CXL** | 1, 2, 3, 5, 6, 7 | UBR_18-24 | Same 6 counter types |

- **Missing HIOP 3,4 and IOMMU 3,4** — these stacks don't exist on NWP
- **UXI/CXL uses UBR_20** for stack 3 (unlike HIOP/IOMMU which skip it)
- Enable masks: HIOP_2, IOMMU_2, HIOP_7 → **IMH1=0** (east-only stacks)

---

## 5. RC_CFCMEM_EW — Mesh Memory + D2D + New Rails

160 entries (152 used), the most complex RC:

### 5.1 CFC Mesh Traffic (Indexes 0-111)
112 entries covering CRS and CMS fabric nodes:
- **CRS nodes**: c0, c1, c3, c16, c18, c19 (SCRS_IOSF_SBAgent)
- **CMS nodes**: c2, c4, c6, c13, c15, c17 (SCMS_IOSF_SBAgent)
- **CAB nodes**: c0(r9-r16), c3(r9-r16), c4(r9-r16), c15(r9-r16), c16(r9-r16), c19(r9-r16) — 48 entries for cross-column bandwidth

### 5.2 UBR D2D BW (Indexes 112-143)
32 UBR D2D bandwidth counters for 8 D2D links (D2D_0 through D2D_7):
- Counter types: F2A_NON_P2P_DATA, F2A_REQ, A2F_NON_P2P_DATA, A2F_REQ
- Uses UBR_0, UBR_9, UBR_33, UBR_34

### 5.3 DTS — C2C and Center Infrastructure (Indexes 148-149)
| Index | Name | RA Pull Path |
|---|---|---|
| 148 | DTS_C2C1_C111213 | RA_DTS_C2C1 (DFVFReg2) |
| 149 | DTS_CINF0 | RA_DTS_CINF0 (DFVFReg1) |

### 5.4 VCCC2C SVID (Indexes 150-151)
| Index | Name | SVID Slot | Notes |
|---|---|---|---|
| 150 | VCCC2C_I_OUT_ACCUMULATOR | [5] | **NEW rail for NWP** (HSD 14027373379) |
| 151 | VCCC2C_I_OUT_NUM_SAMPLES_SNAPSHOT | [5] | |

---

## 6. SVID Rail Mapping — NWP vs DMR

| Rail | DMR | NWP | RC Location | Notes |
|---|---|---|---|---|
| VCCFIXDIG_E | Supported | Supported | RC_MIO_EW [24-25] | Unchanged |
| VCCIN | Supported | Supported | RC_MIO_EW [26-27] | Unchanged |
| VCCANA | Supported | Supported | RC_MIO_EW [28-29] | Unchanged |
| VCCINF | Supported | Supported | RC_MIO_EW [30-31] | Unchanged |
| VCCFIXDIG_W | Supported | Supported | RC_MIO_EW [34-37] | P_IN disabled by default |
| PSYS_EHV | Supported | Supported | RC_MIO_EW [32-33] | P_IN energy only |
| VCCFC_EHV | Supported | **REMOVED** | — | "No more telemetry reads" |
| VCCC2C | N/A | **NEW** | RC_CFCMEM_EW [150-151] | New C2C rail, HSD 14027373379 |
| VCCFA_EHV | Supported | **Off-SVID** | — | HSD 14027235624 |

---

## 7. Test Coverage Gaps for TPF 22022420495

The existing 2 TCDs in the IMH PM Telemetry TPF need augmentation:

### Must-have TCDs:
1. **MR4_TEMP pull correctness** — verify all 256 entries (128 E + 128 W) across 16 MCs, validate LO/HI pairing, cross-check with actual DRAM thermal sensor values
2. **SVID rail telemetry** — verify I_OUT accumulator/snapshot for all active rails (VCCFIXDIG_E/W, VCCIN, VCCANA, VCCINF, VCCC2C), verify PSYS_EHV P_IN, verify VCCFC_EHV is truly removed
3. **VCCC2C new rail** — dedicated TCD for the new C2C rail telemetry (end-to-end: SVID controller → RC_CFCMEM_EW push → PUNIT scratchpad)
4. **UXI BW accumulation** — verify 6-link TX/RX counters accumulate correctly under traffic, reset on read
5. **DTS thermal telemetry** — verify all 28 DTS entries (26 in MIO + 2 in CFCMEM) read correct temperatures from DFVFReg1/DFVFReg2
6. **CFC mesh traffic counters** — verify CFCIO (30 CRS) and CFCMEM (112 CRS/CMS/CAB) ufsMMcounter reads under fabric load
7. **UBR BW counters** — verify HIOP, IOMMU, CXL, and D2D bandwidth counters across all active stacks
8. **Enable mask correctness** — validate that IMH1-only vs IMH2-only entries (e.g., CFCIO idx 23-29, CFCMEM die-variant entries) are correctly masked per die variant
9. **PC6 quiesce behavior** — verify tele_ignore_quiesce=1 entries (DTS, SVID) are correctly skipped during PC6, while quiesce=0 entries (MR4, UXI, CFC) continue polling

### DMR-bug-informed TCDs:
10. **Telemetry push offset contiguity** — verify no push offset collisions or gaps in the 0x2000-0x2D88 range across all 5 RCs
11. **SbPortId resolution** — verify PMSB port ID lookup for all 598 entries resolves to correct IP instances (MCTRK, UXI_MIO, PMUSVID, CRS, CMS, UBR, RA_DTS)

---

## 8. Key HSDs Referenced in Telemetry Spec

| HSD | Topic |
|---|---|
| 14027235624 | VCCFA_EHV no longer on SVID |
| 14027373379 | VCCC2C new SVID rail control |
| 14027181891 | NWP DTS global names and partition |
| 14027343287 | PMAX changes |
