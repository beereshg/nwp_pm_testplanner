# NWP HAS Overview — Architecture Summary

**Source**: [NWP HAS Overview](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html)
**Date**: 2026-05-30

---

## 1. Overview
- **Newport (NWP)** is a custom Xeon processor for Nimbus customer; DMR derivative on OKS-AP derivative platform
- Design philosophy: change only what is necessary to maximize HW/SW/validation leverage from DMR
- Supports same features as DMR unless otherwise stated
- **CPUID**: Family 0x4F (same as DMR), **Model 0x5** (DMR is 0x1)

## 2. Die Topology
- **2x 48-core NWP CBBs** (48 printed per CBB, 96 total printed) + **1 NIO SOC die**
- Core tile: re-used from DMR unchanged
- CBB base: leveraged from DMR with doubled die-to-die write BW (UCIe: 16GT 2W/4R → 32GT 3W/3R)
- NIO: new die with new UCIe (matching CBB), new CAB, new C2C, leveraged HA/HSF/Ubox/SPK
- Accelerators QAT, IAA, DSA, DLB are **removed** from NIO (only x4 gen4, OOB, NPK, S3M, TAM kept)
- Package: BGA 75mm × 77.5mm (updated to 76×88.5), 0.8mm hex pitch, ~11500 pins

## 3. CHI Interface
- **14 CHI links** connecting CPU to accelerator(s) via AMBA CHI protocol
- Each link: one set of Tx/Rx interfaces per channel (REQ, RSP, DATA, SNP)
- Addresses hashed and **interleaved at 256B per CHI port**
- Max raw BW: 32B/cycle/dir/port → **896 GB/s/dir raw**, expected peak ~700–770 GB/s/dir (C2C limited)
- 1 PAG (Port Aggregation Group) = 14 ports; 2 PAGs = 7 ports each
- Data width: 256b; Address width: 52b; NodeID width: 11b

## 4. Core / Compute
- **92 active cores, 96 printed** (2 × 48-core CBBs, 2 spares per CBB)
- Core freq: **P0n 3.3 GHz**, 8 cores capable of **4.4 GHz via PCT** (Priority Core Turbo)
- LLC: **2 × 320 MB** (2 × 32 slices × 10 MB per slice)
- L2: 2 MB per core (re-used DMR core tile)

## 5. Memory
- **LPDDR6** via SOCAMM — exclusive memory interface (no DDR5, LP5x, MRDIMM)
- **32 × 48-bit channels** at 10,667 MT/s (1R/2R), 9,600 MT/s (4R); 16 east + 16 west on NIO
- **Supported configurations**: 32ch, 28ch (failover), 24ch, 16ch, 8ch (failover), 2ch (debug only)
- **Failover**: boot-time sparing — 32→28ch, 24→16ch, 16→8ch (pairs between left/right for balance)
- **Max capacity**: up to **4 TB** (4R × 32Gb × x6 devices, 32ch) per socket
- **ECC**: single 32-bit ECC mode only (on-die ECC disabled, host gathers 32b ECC per 512b data)
- No 2LM support; no SDDC; no ADDDC; no full mirroring
- **Address range (partial) mirroring**: supported (5% option), no mirror failover
- DRAM RAPL: **not supported**; only socket RAPL
- Peak BW: ~1.4–1.5 TB/s per socket

## 6. PCIe / CXL
- **80 lanes Gen6 PCIe/CXL** on north of NIO + **8 lanes UPI** + **4 lanes Gen4 PCIe**
- Configs: 1S: 5×16 + 1×8 Gen6 + 1×4 Gen4; 2S: 5×16 + 1×8 Gen6 + 1×4 Gen4
- UPI topology: 1×8, 2×8, or 1×8+1×16 UPI at 56 GT/s
- P5 does **not** support CXL (enables single-insertion PPV)
- Only 2 Type-2 CXL devices per socket (HDM-DB only)
- CXL hot plug: supported; surprise hot plug: **not supported**
- NTB, VMD, L0p: **not supported**

## 7. CAB / AMA / HMA / CIT Architecture
- **CAB (Custom Accelerator Bridge)**: new NIO sub-IP connecting accelerator(s) to NIO mesh
  - 8 rows of SCF on left/right, 14 columns of CHI
  - Does not support RDT monitoring/enforcement
- **NBA (Newport Bridge Accelerator Agent)**: BRIDGE + AMA
  - **AMA (Accelerator Memory Agent)**: handles CXL.mem requests, includes **PWB** ~21 MB baseline
- **NBH (Newport Bridge Host Agent)**: HMA + CIT
  - **HMA (Host Memory Agent)**: tracks host lines owned by device(s), 24 MB SF per HMA
  - **CIT (CHI-IDI Translator)**: translates CHI→IDI for CXL.cache requests
- **SCA LLC**: 8 MB across 32 slices (256K/slice)

## 8. GRS / C2C
- **2 × 7 GRS ports** on south of package (1 or 2 accelerators)
- Each GRS connection = 1 PAG; 1 accelerator per PAG, up to 7 GRS ports each
- GRS BW limits: ~1365 GB/s (1r1w accel→CPU mem), ~770 GB/s (100R), ~730 GB/s (100W)
- Configs: 1S1A, 1S2A, 2S2A, 2S4A

## 9. SKU Details
- **Single Nimbus SKU** — fully featured
- **TDP: 450W** (PL1 controlled by Nimbus SW for power steering)
- **Tcase: 75°C max**

## 10. PM Features
- **Not supported**: FACT, PkgC6, Soft SKU, DRAM RAPL, platform RAPL
- **Supported**: Socket RAPL, PCT (8 cores at 4.4 GHz), P-states (P0n 3.3 GHz), thermal throttling (CLTT via MR4, OLTT)
- Memory PM: CKE, PPD/APD, OSR (opportunistic self refresh), SREF no clock stop (shallow self refresh)
- **Not supported**: SREF with clock stop (deep self refresh), DVFS, WCK clock stop

## 11. RAS Features — Delta from DMR
- **Removed**: SDDC, HDC (x8), ADDDC, full memory mirroring, mirror failover, PFD, runtime sPPR, mBIST PPR, MAGIC row hammer, error cloaking, viral mode, MCA 2.0 recovery, PCIe surprise hot plug, IOMCA reporting, SCI generation, UXI dynamic link width reduction, socket lockstep, DDR write CRC
- **Added**: Custom 32b ECC mode, address range (partial) mirroring, boot-time sPPR/hPPR, boot-time channel sparing (28ch from 32ch), PRAC + DRFM for row hammer

## 12. Security Features — Delta from DMR
- **Not supported**: SGX-TEM, MK-TME, PFR, VAB, KPT, Secure Telemetry, encrypted debug
- **Changed**: Total keys 1024 (down from 2048), TDX attestation S3M-based only
- **Added**: TDX-Connect with ATS, TDX-Connect with SVM, TDX-Connect with HAC

## 13. Key Deltas from DMR — Summary

| Area | Delta |
|------|-------|
| **Die composition** | 2 CBBs + NIO (vs DMR's 2 CBBs + 2 IMH SOC dies) |
| **Accelerators** | QAT/DSA/IAA/DLB removed; new CAB/AMA/HMA/CIT + C2C/GRS |
| **Memory** | LPDDR6 SOCAMM (not DDR5 DIMM); 32×48b channels; single 32b ECC mode |
| **D2D** | UCIe doubled write BW (32GT 3W/3R) |
| **CHI** | 14-port CHI interface to accelerator, 256B interleave |
| **GRS** | 2×7 GRS ports at 56 GT/s |
| **Cores** | 92 active / 96 printed (same tile as DMR) |
| **LLC** | 2 × 320 MB (same as DMR CBB) |
| **IO** | 80 lanes Gen6 PCIe/CXL; no NTB/VMD/L0p; P5 no CXL |
| **PM** | No FACT, PkgC6, DRAM RAPL, Soft SKU |
| **RAS** | Reduced memory RAS; PRAC for row hammer |
| **Security** | No SGX, 1024 keys; adds TDX-Connect |
| **CPUID model** | 0x5 (DMR is 0x1) |
| **Package** | BGA 76×88.5mm, ~11500 pins |
