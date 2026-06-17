# NWP HAS Impact on PM FV Test Plan — TPF/TCD/TC Analysis

**Date**: 2026-05-30
**Sources**: NWP HAS Overview, NWP NIO PM MAS, NWP MIO Stack MAS, NWP Memory IO Stack MAS
**Test Plan**: NWP PM FV (442 TCs total)

---

## Impact Legend

| Impact | Meaning |
|--------|---------|
| **REJECT** | Feature ZBB'd on NWP — reject all TCD/TCs under this TPF |
| **UPDATE** | Feature exists but changed — TCD/TC descriptions need updating |
| **NEW** | New NWP-specific feature — may need new TCD/TCs |
| **NO CHANGE** | Leveraged from DMR as-is |

---

## 1. ZBB'd Features — REJECT Candidates

These features are fused off or explicitly ZBB'd on NWP. All related TCD/TCs should be rejected.

### 1.1 PkgC6 (HSD 22021155362)
**Status**: REJECT — fused off (`FUSE_PKG_C_STATE=0`, `PKG_C_STATE_LIMIT_REQ=0`), Pchannel PUNIT↔RC removed
**Affected TCs** (from `pkgc_tpf_inventory.txt`):
- TCD 22022421039 (Clock Actions): TC 22022422450 (COREPLL/FLL), TC 22022422455 (RINGPLL)
- TCD 22022421044 (Link/Fabric/Mem State): TC 22022422468 (All Cores in C6)
- TCD 22022421048 (Voltage Actions): TC 22022422475 (VccCORE FIVR off), TC 22022422482 (VccR Vmin)
- TCD 22022421051 (BIOS Programming): TC 22022422489/496/499/501/502 (5 TCs)
- TCD 22022421054 (Fuse Checkout): TC 22022422504/512/521/523/525/549 (6 TCs)
- TCs: 22022422550 (Multi-socket PC6), 22022422552 (PkgC x OS offlines), 22022422555 (PkgC x UFS), 22022422556 (PMX PkgC residency), 22022422558 (No PC6 after emon), 22022422559 (PkgC x ADR), 22022422560 (PkgC x ITD emu), 22022422561 (PkgC x ITD), 22022422562 (PkgC x MC SSR), 22022422568 (UCIe L1 latency), 22022422572 (OPC PkgC entry), 22022422580 (PkgC x PMAX neg), 22022422584 (PkgC x probe mode), 22022422589 (PkgC x RAS), 22022422593 (PkgC x surprise reset), 22022422596 (PkgC x SPD I3C), 22022422603 (PkgC x TPMI), 22022422613 (PkgC Solar)
- **Note**: "PKGC ZBB Negative Checks" TC should be **KEPT** — validates PkgC cannot be entered

### 1.2 UFS — Uncore Frequency Scaling (HSD 14024876702)
**Status**: REJECT — NIO mesh & CAB fixed at 2 GHz
**Affected TCs**:
- "UFS x RAPL" — REJECT
- "TPMI-driven FabricGV" — REJECT (if NIO-specific; CBB DVFS still supported)
- "PEGA-driven FabricGV" — REJECT (if NIO-specific)
- "BIOS Configurations of DVFS settings" — UPDATE (CBB still supports, NIO does not)
- "AshTree PRT_Solar CStates/PStates/DVFS" — UPDATE (remove NIO DVFS expectations)

### 1.3 Memory PM (HSD 22021155412)
**Status**: REJECT — APD, PPD, LPM, SSR, SR all ZBB'd
**Affected TCs**:
- "Memory PM ZBB Negative Checks" — **KEEP** (validates memory PM cannot be entered)
- Any TCs referencing MC self-refresh, APD, PPD entry/exit — REJECT

### 1.4 DRAM RAPL (HSD 14025012732)
**Status**: REJECT — fused off
**Affected TCs**:
- "DRAM RAPL ZBB Negative Checks" — **KEEP** (validates DRAM RAPL reads 0)
- Any DRAM RAPL energy counters, limits, throttling TCs — REJECT

### 1.5 Platform RAPL / Psys (HSD 22021155415)
**Status**: REJECT
**Affected TCs**:
- "Platform RAPL / PSYS ZBB Negative Checks" — **KEEP**

### 1.6 SST-PP / BF / CP
**Status**: REJECT — only SST-TF (PCT) supported
**Affected TCs**:
- "SST-PP Dynamic Fuse checks" (22022422188) — REJECT
- "SST-PP Static Boot flow with OSPL" (22022422194) — REJECT
- "SST-PP Static Boot flow_silicon" (22022422195) — REJECT
- "SST-PP/CP/BF ZBB Negative Checks" — **KEEP**
- "HGS Enabling and Discovery" (22022422197) — REJECT (HGS requires SST-PP)
- "HGS Functionality_silicon" (22022422198) — REJECT
- "Power Management – Intel SST – PP TDP Test" — REJECT
- "Power Management – Intel SST – TRL Sweep" — UPDATE (verify SST-TF only)
- "Socket rapl x SST" — UPDATE (scope to SST-TF only)
- "PCT - SST-PP x PCT Basic Checks" (22022422110) — REJECT

### 1.7 DCM (Dual-Chip Module)
**Status**: REJECT — NWP is 1S or 2S only, no DCM
**Affected TCs**:
- "DCM FIT" (22022422273) — REJECT

### 1.8 ADR (HSD 22021155420)
**Status**: REJECT
**Affected TCs**:
- "PkgC x ADR" — already rejected with PkgC6

### 1.9 PCIe L1 / HSIO L0p / UXI L1/L0p
**Status**: REJECT
**Affected TCs**: Any PCIe L1 entry/exit, HSIO L0p, UXI link PM TCs

### 1.10 Favored Core
**Status**: REJECT
**Affected TCs**: Any favored core selection, HW feedback favored core TCs

---

## 2. Changed Features — UPDATE Required

### 2.1 SVID
**Impact**: VCCFA_EHV **removed from SVID** (HSD 14027235624); VCCC2C **new SVID rail** (HSD 14027373379)
**Affected TCs**:
- "SVID Basic commands functionality" (22022421917) — UPDATE: remove VCCFA_EHV, add VCCC2C
- "SVID Registers Verification" (22022421920) — UPDATE: new rail map
- "SVID Addressing Verification" (22022421922) — UPDATE: VCCC2C at SVID0/05h
- "SVID Imon telemetry" (22022421924) — UPDATE: add VCCC2C telemetry
- "SVID Pmon Telemetry" (22022421926) — UPDATE: add VCCC2C

### 2.2 ITD (Isochronous Thermal Domain)
**Impact**: New VCCFCFCAB digital domain for ITD
**Affected TCs**:
- "Verify VCCFCFCAB ITD" (22022458470) — **KEEP/EXISTS**: already in test plan
- "Verify ITD disable" (22022421528) — UPDATE: include VCCFCFCAB in disable check
- "Verify ITD during reset" (22022421534) — UPDATE: include VCCFCFCAB
- All other ITD rail TCs — NO CHANGE (ACP, CCF, Core MLC SSA, Inf, UCIe, CFCIO, CFCMEM, FIXDIG, UCIEA)

### 2.3 Telemetry
**Impact**: NUM_TELE_INDEXES increased across all 5 RCs; new DTS sensors (C2C, MIO, memory MC ×16)
**Affected TCs**:
- "Verify CCP Thermal Telemetry" (22022421461) — UPDATE: new telemetry table sizes
- "CBB DTS Thermal Telemetry" — UPDATE (CBB unchanged but NIO telemetry is larger)
- "IMH DTS Thermal Telemetry" — UPDATE: NIO has more DTS entries
- Already covered in [nwp_nio_pm_telemetry.md](../KB/nwp_nio_pm_telemetry.md)

### 2.4 DTS Sensors
**Impact**: Significantly more DTS types on NIO — new C2C, MIO infra, memory MC, center infra DTS
**Affected TCs (all need UPDATE for NWP NIO DTS topology)**:
- "Verify AON DTS Functionality" (22022421456) — UPDATE
- "Verify CBO Cluster DTS Functionality" (22022421458) — NO CHANGE (CBB)
- "Verify CGU DTS Functionality" (22022421498) — UPDATE: NIO CGU DTS
- "Verify Core DTS Functionality" (22022421465) — NO CHANGE (CBB core tile)
- "Verify D2D DTS Functionality" (22022421501) — UPDATE: NIO has DTS_D2D{NE,NW}
- "Verify IO Fabric DTS Functionality" (22022421504) — UPDATE: NIO MIO infra DTS
- "Verify Memory DTS Functionality" (22022421508) — UPDATE: 16 memstack DTS (new pardfi partition)
- "Verify Memory Fabric DTS Functionality" (22022421515) — UPDATE: NIO CFCMEM DTS
- "Verify MIO DTS Functionality" (22022421506) — UPDATE: DTS moved outside MIO stack
- "Verify SOC DTS Functionality" (22022421469) — UPDATE: NIO center infra DTS
- "Verify Accelerator DTS Functionality" (22022421487) — REJECT or UPDATE (QAT/DSA/IAA/DLB removed; accelerator now external via C2C)

### 2.5 Thermal Management
**Impact**: Same signals (THERMTRIP, PROCHOT, MEMHOT, EMTTM, VR_HOT) but NIO topology differs
**Affected TCs**:
- "Verify Thermtrip shuts down all FIVRs and MBVRs" (22022421671) — UPDATE: new VCCC2CDIG, VCCDDRDIG MBVRs
- "Verify IMH VR Hot Actions" (22022421674) — UPDATE: NIO has different VR topology (FIVR_MIO_3/4 PrimeCode-controlled)
- "Verify CBB VR Hot Actions" (22022421673) — NO CHANGE
- Pin assertion TCs (MEMHOT, MEMTRIP, PROCHOT, THERMTRIP) — NO CHANGE in behavior, UPDATE pin mapping if NIO-specific

### 2.6 RAPL
**Impact**: Socket RAPL unchanged; DRAM RAPL fused off; Platform RAPL/Psys ZBB'd
**Affected TCs**:
- Socket RAPL TCs — NO CHANGE (PL1 1s TW, PL2 12ms TW same)
- "RAPL IMON Addressing and Telemetry" (22022422042) — UPDATE: new VCCC2C on SVID
- "RAPL Energy status reporting" (22022422023) — UPDATE: only socket energy, no DRAM/platform
- "Fast RAPL" TCs — NO CHANGE (PEM/PLR mechanism same)

### 2.7 FIVR / Power Delivery
**Impact**: New VCCC2CDIG FIVR, FIVR_MIO_3/4 PrimeCode-controlled (not RC), new VCCDDRDIG MBVR
**Affected TCs**:
- "Fuse Values Propagation Checks" — UPDATE: new FIVR straps
- "Fuse Values Sanity Checks" — UPDATE: new FIVR fuse values
- Power delivery / SIMPL TCs — UPDATE: new voltage rails in SIMPL model

### 2.8 Memory (LPDDR6)
**Impact**: Completely new memory subsystem — LPDDR6 CDS PHY, VCCDDRDIG MBVR, ISA_MC spare bits for PHY handshake
**Affected TCs**:
- DIMM thermal TCs (MR4, MEMHOT, MEMTRIP) — UPDATE: LPDDR6 MR4 differs from DDR5
- "Verify DIMM temp" TCs — UPDATE: CDS PHY has its own DTS
- "MR4 based" / "MR4 Verify Memhot" TCs — UPDATE: LPDDR6 MR4 protocol changes
- "Temperature compensation" (22022421409) — UPDATE for LPDDR6

### 2.9 MIO Stack Architecture
**Impact**: 6 MIO stacks (5 UIO_A + 1 UIO_E), HAP integration, DTS moved outside stack
**Affected TCs**:
- "Verify MIO DTS Functionality" — UPDATE: DTS now outside MIO stack
- IO-related thermal/PM TCs — UPDATE: new stack topology

---

## 3. New NWP-Specific Features — NEW TCD/TC Candidates

### 3.1 C2C / GRS
- **No existing TCs** for C2C power management
- Consider: C2C LJPLL behavior, VCCC2CDIG FIVR telemetry, C2C DTS, GRS link PM (if any)

### 3.2 CAB (Custom Accelerator Bridge)
- VCCCFCCAB is a new FIVR domain
- "Verify VCCFCFCAB ITD" already exists — covers ITD aspect
- Consider: CAB power domain telemetry, CAB clock gating behavior

### 3.3 LPDDR6 PHY Frequency Change Flow
- ISA_MC spare bits for `freq_change_req`/`freq_change_ack` — new PCode flow
- Consider: PHY PLL lock during frequency change, ADOP disable/enable sequence

### 3.4 VCCDDRDIG MBVR
- New platform-delivered rail (not FIVR, not on RA)
- Consider: MBVR telemetry, voltage level verification

### 3.5 VCCC2C SVID Rail
- New SVID address (SVID0/05h)
- Consider: C2C SVID read/write commands, IMON/PMON telemetry

### 3.6 PrimeCode-Controlled FIVRs
- FIVR_MIO_3 and FIVR_MIO_4 bypass RC, controlled directly by PrimeCode
- Consider: Verify PrimeCode direct FIVR control, WP programming for these FIVRs

---

## 4. Summary — Impact Statistics

| Category | Count | Action |
|----------|-------|--------|
| PkgC6 TCs | ~30+ | REJECT (keep ZBB neg check) |
| UFS TCs | ~3–5 | REJECT or UPDATE |
| Memory PM TCs | ~2–3 | REJECT (keep neg check) |
| DRAM RAPL TCs | ~1–2 | REJECT (keep neg check) |
| Platform RAPL TCs | ~1 | REJECT (keep neg check) |
| SST-PP/BF/CP/HGS TCs | ~6–8 | REJECT (keep neg check) |
| DCM TCs | 1 | REJECT |
| SVID TCs | 5 | UPDATE |
| ITD TCs | 2–3 | UPDATE |
| DTS TCs | ~12 | UPDATE |
| Thermal TCs | ~5 | UPDATE |
| Memory/LPDDR6 TCs | ~10 | UPDATE |
| RAPL TCs | ~3 | UPDATE |
| FIVR/Power TCs | ~3 | UPDATE |
| New NWP TCs needed | ~6–10 | NEW |
| **Unchanged TCs** | **~350** | **NO CHANGE** |
