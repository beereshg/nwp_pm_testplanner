# Voltage Regulation Architecture — Cross-Generational Reference (GNR / DMR / NWP)

**Sources**:
- [GNR Compute Die SoC MAS — FIVR placement & inventory](https://docs.intel.com/documents/arch_datacenter/gnr_mas/soc/compute%20die%20soc%20mas.html)
- [Server FIVR HAS](https://docs.intel.com/documents/pm_doc/src/server/wave3_common/power%20delivery/fivr%20has.html)
- [Converged Core Perimeter PM HAS](https://docs.intel.com/documents/pm_doc/src/server/wave3_common/ccp/converged%20core%20perimeter%20pm%20has.html)
- [GNR-D SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/GNRD/gnrd_soc_pm_has.html)
- [GRR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/grr/grr_soc_pm_has.html)
- [NWP IMH SOC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/NWP_IMH_SOC_PM_MAS.html)
- [NWP PAS](https://docs.intel.com/documents/custom-xeon/newport-docs/platform/pas/NwpPAS.html)

**Date**: 2026-07-20

---

## 1. Generational Summary — Server Voltage Regulation

| Generation | Regulation Technology | Core Voltage Granularity | Notes |
|---|---|---|---|
| **Haswell / Broadwell** (2013–2015) | FIVR (package inductors) | Per-core | First gen; inductors integrated into package substrate |
| **Skylake-SP → Ice Lake-SP** (2017–2021) | External VRM only | Shared (platform VR) | FIVR removed; package thinning made inductors infeasible |
| **Sapphire Rapids** (2023) | FIVR returns | Per-core | FIVR brought back to server for per-core DVFS |
| **Granite Rapids / GNR** (2024) | FIVR (Gen4) | **Per-core** (1 FIVR per core) | Explicit: `VCCCORE[X:0]`, "FIVR per core" |
| **Diamond Rapids / DMR** (2025) | FIVR (Gen4) | Per-core P-states (PCPS) + Per-tile P-states (PTPS) | CBB-based; terminology confirms both PCPS and PTPS |
| **Newport / NWP** (2026) | FIVR (Gen4) + MBVR | CBB inherits DMR per-core | NIO has only uncore/fabric FIVRs; CBB PM is 100% DMR |

> **Key insight**: DLVR (Digital Linear Voltage Regulator) was a **client-only** experiment (Raptor Lake die, fused off in shipping). Server retained FIVR once it returned on SPR.

---

## 2. Granite Rapids (GNR) — Detailed Architecture

### 2.1 Core Voltage: Per-Core FIVR

The GNR Compute Die SoC MAS is explicit:

> "Internal Voltage Rails — Derived from per core FIVRs — `VCCCORE[X:0]` … FIVR per core."

Each core has a **dedicated FIVR** residing in its CPU tile, enabling independent per-core DVFS.

**FIVR inventory by topology:**
| Topology | Core FIVRs | Cores |
|---|---|---|
| 10×5 | 44 | 44 |
| 10×6 | 50 | 50 |
| 6×5 | 20 | 20 |

### 2.2 Shared / Uncore Domains (Centralized FIVRs)

| FIVR Type | Count | Domain | Organization |
|---|---|---|---|
| Core FIVR | 1 per core | `VCCCORE` | Per-core; L2/MLC also on VCCCore for RWC |
| CFC FIVR | 2 | `VCCCFC` | One per vertical die-half; powers LLC/SF + mesh/fabric |
| HDC FIVR | 2 | `VCCHDC` / `VCCRAM` | One per vertical die-half; powers SRAM/cache |
| DDRA FIVR | ~4 | `VCCDDRA` | Per adjacent DDR tile; DDR analog |
| DDRD FIVR | ~4 | `VCCDDRD` | Per adjacent DDR tile; DDR digital |

### 2.3 External Rails Feeding FIVRs

| Rail | Voltage | Purpose |
|---|---|---|
| `VCCIN_EHV` | 1.55–1.9 V | Main input to centralized FIVRs |
| `VCCINF` | ~0.7 V | Infrastructure / always-on |
| `VNN` | ~1.0 V | GPIO |
| `VCCFA_EHV` | ~1.8 V | CGU and PUNIT |

### 2.4 Voltage Domain Isolation

- RWC: L2 on `VCCCore`, LLC on `VCCHDC`
- Isolation cells at CFC ↔ HDC domain crossings
- Platform VRs controlled by PCU over SVID

---

## 3. Diamond Rapids (DMR) — Known Architecture

### 3.1 Confirmed

- **FIVR-based power delivery** for multiple internal rails
- Terminology explicitly includes: **FIVR**, **FCM**, **MBVR**, **PCPS (per-core P-states)**, **PTPS (per-tile P-states)**
- Shared FIVR-fed uncore/fabric rails confirmed:
  - `VCCCFN_HCT` / `VCCCFN`
  - `VCCCFCX`, `VCCCFC0`, `VCCCFC1`
  - Mesh/CMS/B2 and related logic on these rails
- Some rails remain external VR (not FIVR-generated):
  - `VCCINF`, `VCCVNN`, `VCCVNN_NAC`, `VCCFA_EHV`

### 3.2 Unconfirmed (from available excerpts)

- Exact `VCCCORE` topology (1 FIVR per core, as GNR, vs tile-grouped)
- Exact core FIVR count per CBB
- Whether DLVR exists anywhere in DMR (strong absence of evidence — FIVR dominates)

### 3.3 PM Terminology

| Term | Meaning |
|---|---|
| **PCPS** | Per-Core P-States — individual core frequency/voltage control |
| **PTPS** | Per-Tile P-States — tile-level frequency/voltage management |
| **FCM** | FIVR Control Module |
| **MBVR** | Motherboard Voltage Regulator (platform-delivered, SVID-controlled) |

---

## 4. Newport (NWP) — FIVR + MBVR Architecture

### 4.1 Key Principle

NWP CBB PM flows are **100% leveraged from DMR CBB** — no CBB PM changes. This means:
- Core voltage regulation in CBB is **identical to DMR** (per-core FIVR presumed)
- All NWP-specific FIVR content is on the **NIO die** (uncore/fabric/memory/IO)

### 4.2 NIO FIVR Inventory (Gen4.0, same IP as DMR IMH2)

| FIVR Global Name | Type | Rail | Domain |
|---|---|---|---|
| `fivr_vcccfcio_w` / `_e` | Stacked 80-bump | VCCCFCIO | IO mesh fabric |
| `fivr_vcccfcmem_w` / `_e` | Stacked 80-bump | VCCCFCMEM | Memory mesh fabric |
| `fivr_vcccfccab` | Inline 80-bump | VCCCFCCAB | CHI Accelerator Bridge |
| `fivr_vccfixdig_w` / `_e` | 48-bump inline | VCCFIXDIG | MC + LPDDR6 PHY digital |
| `fivr_vccfixdig_mio0..5` | 20-bump stacked (MIO2=16) | VCCFIXDIG_MIO | Per-MIO stack |
| `fivr_vccfixdig_ucie_nw` / `_ne` | 32-bump stacked | VCCFIXDIG_UCIE | D2D UCIe PHY |
| `fivr_vccc2cdig` | Inline 80-bump | **VCCC2CDIG** | **NEW** — C2C digital |

**Note:** FIVR_MIO_3 and FIVR_MIO_4 controlled directly by PrimeCode (RC NUM_VR=4 constraint).

### 4.3 NWP Platform VRs (13 MBVRs)

| Rail | Vnom (V) | ICCmax (A) | SVID | Notes |
|---|---|---|---|---|
| PVCCIN_EHV0 | 1.83 | 728 | Yes (01h) | Input to FIVRs |
| PVCCANA0 | 0.9 | 35.4 | Yes (02h) | PCIe G6 analog |
| PVCCINF | 0.85 | 42 | Yes (03h) | Infrastructure |
| PVCC_HV | 1.25 | 7.9 | No | — |
| PVCCNN | 1.0 | 10 | No | — |
| VCCFA_EHV | 1.8 | 2.3 | **No** | Removed from SVID (HSD 14027235624) |
| PVCCC2C | 0.875 | 86 | Yes (05h) | **NEW** C2C VCC |
| PVDD0 | 0.77 | 64 | Yes (TBD) | LPDDR6 VDD0 |
| PVDD1 | 0.77 | 64 | Yes (TBD) | LPDDR6 VDD1 |
| PVCCDQ | 0.5 | 2.5 | No | DDR LV supply |
| PVCCQXC | 1.025 | 1.5 | No | DDR PHY analog |
| PVCCQXD | 0.9 | 3.5 | No | DDR PHY analog |
| PVCC3P3_AUX | 3.3 | 0.5 | Yes (0Dh) | Psys sensor |

### 4.4 NWP-Specific Voltage Deltas from DMR

| Delta | Detail |
|---|---|
| `VCCFA_EHV` removed from SVID | HSD 14027235624 — quiet rail only |
| `VCCC2CDIG` FIVR **new** | 80-bump inline; C2C digital domain (HSD 22021977883) |
| `VCCC2C` platform rail **new** | SVID address 05h (HSD 14027373379) |
| `VCCDDRDIG` MBVR-delivered **new** | LPDDR6 PHY digital at 0.77V; no FIVR (HSD 14026585116) |
| `PVDD0` / `PVDD1` **new** | LPDDR6 DRAM supply (JEDEC PMIC6300 on SOCAMM) |
| Each MIO stack has **unique FIVR** | Delta from DMR where FIVRs shared across northcaps |

---

## 5. Validation Implications

### 5.1 Per-Core Voltage Independence (GNR/DMR/NWP-CBB)

Per-core FIVR enables:
- Independent per-core DVFS (P-state transitions without neighbor impact)
- Per-core power gating in C6 (FIVR turns off → core domain de-energized)
- Fast turbo-to-idle switching (~1 μs VID change vs ~10 μs with platform VR)
- TC relevance: `verify_thermtrip_shuts_down_all_fivrs`, `pkgc_ensure_vcccore_fivr_is_turned_off`

### 5.2 NWP-Specific Test Considerations

- NIO FIVRs are **all uncore/fabric** — no per-core FIVRs on NIO die
- CBB per-core FIVR behavior must be tested via CBB flows (inherited from DMR)
- New `VCCC2CDIG` domain needs: power-up sequencing, thermal trip, telemetry TCs
- `VCCFA_EHV` loss of SVID control → static rail; verify no SVID commands sent
- `VCCDDRDIG` is MBVR-only → verify no FIVR WP programming attempted for this rail
- FIVR_MIO_3/4 PrimeCode-controlled → verify RC does not attempt to manage these

### 5.3 Cross-Generation FIVR Test Portability

| Test Category | GNR | DMR | NWP |
|---|---|---|---|
| Per-core VID transitions | ✅ Core FIVR | ✅ CBB FIVR | ✅ CBB FIVR (inherited) |
| Fabric DVFS via FIVR | ✅ CFC/HDC | ✅ VCCCFC* | ✅ VCCCFCIO/VCCCFCMEM (but UFS ZBB'd) |
| FIVR shutdown in PkgC6 | ✅ | ✅ | ❌ PkgC6 ZBB'd |
| Memory domain FIVR | ✅ DDRA/DDRD | ✅ | ✅ VCCFIXDIG (MC); VCCDDRDIG is MBVR |
| New C2C domain FIVR | N/A | N/A | ✅ VCCC2CDIG (new TC needed) |

---

## 6. Glossary

| Term | Expansion | Notes |
|---|---|---|
| FIVR | Fully Integrated Voltage Regulator | Buck converter with package inductors; Gen4 on GNR/DMR/NWP |
| DLVR | Digital Linear Voltage Regulator | Client-only (Raptor Lake, fused off); no inductors needed |
| IVR | Integrated Voltage Regulator | Generic term; in Intel server context = FIVR |
| MBVR | Motherboard Voltage Regulator | Platform-delivered rail, SVID-controlled |
| PCPS | Per-Core P-States | Individual core voltage/frequency |
| PTPS | Per-Tile P-States | Tile-level voltage/frequency management |
| FCM | FIVR Control Module | Hardware block managing FIVR operation |
| SVID | Serial Voltage ID | Intel protocol for CPU ↔ platform VR communication |
| WP | Working Point | FIVR operating point (voltage/frequency pair) |
| BGR | Bandgap Reference | Voltage reference used by FIVRs and PMAXs |
