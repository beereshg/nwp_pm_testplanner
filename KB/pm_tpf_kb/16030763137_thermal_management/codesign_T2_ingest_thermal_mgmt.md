# Co-Design T2 Ingest — Thermal Management (TP 16030763137)

> **Ingested:** 2026-07-19
> **Template:** T2 (Grouping / WHAT-boundary check) — extended to TPF level
> **Spec sources cited by Co-Design:**
> - DMR thermal flows — dmr_thermal.html
> - NWP IMH SoC PM MAS — 
wp_imh_soc_pm_mas.html
> - Newport NIO GPIO HAS — 
ewport nio gpio has.html
> - NWP PAS — 
wppas.html
> - Primecode FHAS index — index.html (SERVERPMFW-1021)
> - DMR overview HAS — dmr_overview_has.html
>
> **Status:** ALL ITEMS RESOLVED (2026-07-19)
> - 8 TPFs created (7 thermal splits + 1 DDRIO), 13 TCDs reparented, 10 new TCDs created, 21 TCs mapped
> - 2 TCDs marked ZBB_N/A (TSOD + CLTT PECI), 1 DDRIO separated to own TPF
> - 3 new-coverage TCDs created with spec-backed bars (cross-die, thermal×RAPL, TPMI migration)
> - **No remaining open items**
>
> ### HSD ID Map (created 2026-07-19)
>
> | Type | ID | Title |
> |---|---|---|
> | TPF | [16031170062](https://hsdes.intel.com/appstore/article-one/#/16031170062) | Core/CBB Thermal Control |
> | TPF | [16031170063](https://hsdes.intel.com/appstore/article-one/#/16031170063) | IMH Thermal Control |
> | TPF | [16031170064](https://hsdes.intel.com/appstore/article-one/#/16031170064) | Thermal GPIO & External Events |
> | TPF | [16031170065](https://hsdes.intel.com/appstore/article-one/#/16031170065) | Thermtrip / Catastrophic Shutdown |
> | TPF | [16031170066](https://hsdes.intel.com/appstore/article-one/#/16031170066) | ITD Compensation |
> | TPF | [16031170067](https://hsdes.intel.com/appstore/article-one/#/16031170067) | Thermal Sensors & DTS Telemetry |
> | TPF | [16031170068](https://hsdes.intel.com/appstore/article-one/#/16031170068) | Thermal Status / Reporting Interfaces |
> | TCD | [16031170069](https://hsdes.intel.com/appstore/article-one/#/16031170069) | PROCHOT_N Interface |
> | TCD | [16031170070](https://hsdes.intel.com/appstore/article-one/#/16031170070) | MEMHOT IN/OUT Interface |
> | TCD | [16031170071](https://hsdes.intel.com/appstore/article-one/#/16031170071) | MEMTRIP/THERMTRIP Package Signaling |
> | TCD | [16031170072](https://hsdes.intel.com/appstore/article-one/#/16031170072) | Core/Ring Rail ITD |
> | TCD | [16031170073](https://hsdes.intel.com/appstore/article-one/#/16031170073) | Fabric/IO Rail ITD |
> | TCD | [16031170074](https://hsdes.intel.com/appstore/article-one/#/16031170074) | Memory/CFC Rail ITD |
> | TCD | [16031170075](https://hsdes.intel.com/appstore/article-one/#/16031170075) | ITD Common Controls |

---

## 1. TPF-Level Structural Actions

### 1A. TPF 16030763139 "Socket Thermal Management" → SPLIT into 5 TPFs

| # | Proposed TPF | Scope | Spec section | TCDs to contain | Status |
|---|---|---|---|---|---|
| A1 | **Core/CBB Thermal Control** | Socket-side thermal throttling for cores, uncore, ring/CBB domains | DMR thermal flows / core EMTTM feature family | 22022420579 ACP; 22022420585 CBB Thermal Mgmt | `DONE` |
| A2 | **IMH Thermal Control** | IMH2-specific thermal control: IMH-die PID throttle and local thermal responses | NWP IMH thermal behavior (nwp_imh_soc_pm_mas) | 22022420596 IMH Thermal Mgmt; NEW cross-die propagation | `DONE` |
| A3 | **Thermal GPIO & External Events** | Externally visible thermal signal semantics and event-driven throttle responses | NWP GPIO thermal signal sections (newport nio gpio has) + IMH thermal behavior table | split-GPIO TCDs; 22022420609 Prochot Flow; 22022420628 VR Hot | `DONE` |
| A4 | **Thermtrip/Catastrophic Shutdown** | Catastrophic thermal detection, DTS chain propagation, shutdown behavior | NWP IMH MAS 6.6 + NWP GPIO THERMTRIP | 22022420625 Thermtrip | `DONE` |
| A5 | **ITD Compensation** | Voltage-temperature compensation behavior and common ITD controls per rail group | DMR thermal flows / ITD compensation open items | split-22022420603 ITD TCDs | `DONE` |

**Local validation gate:** Each proposed TPF must represent a genuinely distinct spec subsystem with a different IP owner or throttle mechanism. The 5-way split passes this gate: EMTTM (CBB PCode), IMH PID (IMH firmware), GPIO signals (NIO/platform boundary), catastrophic chain (HWRS/DTS), and ITD compensation (FIVR/voltage) are all architecturally distinct.

### 1B. TPF 16030763140 "Memory Thermal Management" → KEEP (with TSOD removal)

- Remove/ZBB TCD 22022420563 (CLTT TSOD) — not POR for NWP LPDDR6/SOCAMM
- Flag TCD 22022420554 (CLTT PECI) for spec-basis confirmation
- Status: `DONE`

### 1C. TPF 16030763141 "Thermal Reporting/Telemetry" → SPLIT into 2 TPFs

| # | Proposed TPF | Scope | Spec section | TCDs to contain | Status |
|---|---|---|---|---|---|
| C1 | **Thermal Sensors & DTS Telemetry** | Thermal sensor inventory, readings, dielet telemetry for CBB and IMH | NWP DTS/thermal diode sections | 22022420582 CBB DTS; 22022420593 IMH DTS | `DONE` |
| C2 | **Thermal Status/Reporting Interfaces** | Architectural thermal status, threshold programming, interrupts, TPMI/PMT reporting | DMR thermal interrupt/reporting + TPMI transition refs | 22022420619 Thermal Reporting; 22022420616 Thermal Interrupts; 22022420606 MCAs | `DONE` |

---

## 2. TCD Reparenting Actions

| TCD ID | Title | Current TPF | Target TPF | Spec justification | Status |
|---|---|---|---|---|---|
| 22022420596 | IMH Thermal Management | 16030763139 | NEW **IMH Thermal Control** | IMH2-specific PID throttle is architecturally separate from CBB EMTTM | `DONE` |
| 22022420606 | MCAs | 16030763139 | NEW **Thermal Status/Reporting Interfaces** | Error reporting, not thermal control; belongs with reporting/status | `DONE` |
| 22022420609 | Prochot Flow | 16030763139 | NEW **Thermal GPIO & External Events** | External event response flow, distinct from internal thermal control | `DONE` |
| 22022420616 | Thermal Interrupts | 16030763139 | NEW **Thermal Status/Reporting Interfaces** | Package thermal interrupt register semantics = reporting/status | `DONE` |
| 22022420625 | Thermtrip | 16030763139 | NEW **Thermtrip/Catastrophic Shutdown** | Catastrophic shutdown chain = distinct spec subsystem | `DONE` |
| 22022420628 | VR Hot | 16030763139 | NEW **Thermal GPIO & External Events** | External thermal/power event response, not general socket thermal | `DONE` |
| 22022420567 | DDRIO Temp Compensation | 16030763140 | NEW **Memory PHY Thermal Compensation** OR keep in 16030763140 | PHY/temp comp different mechanism from CLTT/memhot; keep if same owner | `RESOLVED — TPF 16031170078` |

---

## 3. TCD Split Actions

### 3A. TCD 22022420589 "GPIO Interface" → SPLIT into 3 TCDs

**Rationale:** Clubs PROCHOT_N, MEMHOT IN/OUT, MEMTRIP/THERMTRIP — each with distinct spec semantics, direction, and platform behavior per Newport NIO GPIO HAS.

| # | Proposed TCD | WHAT | Spec section | Bar sketch | Status |
|---|---|---|---|---|---|
| S1 | **PROCHOT_N Interface** | PROCHOT_N input pin assertion → External_PROCHOT set → TCC active → deassert recovery | NWP GPIO HAS: PROCHOT_N section | PROCHOT_N asserted → TCC active in spec'd latency; deassert → recovery within spec'd window; fuse enable/disable respected | `DONE` |
| S2 | **MEMHOT IN/OUT Interface** | MEMHOT_IN external request → memory throttle within 100µs; MEMHOT_OUT on dimm temp threshold crossing | NWP GPIO HAS: MEMHOT_IN_N / MEMHOT_OUT_N sections | MEMHOT_IN → MC throttle within 100µs; MEMHOT_OUT driven when MH_TEMP_STAT crosses DIMM_TEMP_EV_OFST; bump fuse gating | `DONE` |
| S3 | **MEMTRIP/THERMTRIP Package Signaling** | MEMTRIP_N/THERMTRIP_N catastrophic signal assertion, cross-die wire-OR, fuse gating | NWP GPIO HAS: MEMTRIP_N / THERMTRIP_N sections | MEMTRIP_N asserted on catastrophic memory temp; THERMTRIP_N wire-OR'd across dice; ignore until fuses downloaded + first measurement valid | `DONE` |

**Local validation:** Bars are distinct — latency/throttle (PROCHOT), threshold crossing (MEMHOT), catastrophic chain (MEMTRIP/THERMTRIP). Split passes.

### 3B. TCD 22022420603 "ITD" → SPLIT into 4 TCDs

**Rationale:** 16 TCs covering 10+ voltage domains plus fuse/disable/reset/PkgC6. Multiple WHATs with different pass/fail bars per domain group.

| # | Proposed TCD | WHAT | Spec section | Bar sketch | Status |
|---|---|---|---|---|---|
| S4 | **Core/Ring Rail ITD** | VccCore (ACP/Acode) + VccRing (CCF/PCode) temperature-dependent voltage compensation | DMR thermal / ITD: VccCore + VccRing domains | ITD slope applied per fuse coefficients; voltage tracks temperature within spec'd tolerance; Acode autonomous for VccCore, PCode for VccRing | `DONE` |
| S5 | **Fabric/IO Rail ITD** | VccInf, VccCFCIO, VccFIXDIG, VccUCIEA, VccC2IA, VccFCFCAB/VccCAB compensation | DMR thermal / ITD: Fabric/IO domains + NWP new VCCCAB | ITD fuse coefficients applied per domain; NWP new domains (VCCCAB, VCCC2CDIG) compensated correctly | `DONE` |
| S6 | **Memory/CFC Rail ITD** | VccCFCMEM + MLC SSA domain ITD compensation | DMR thermal / ITD: Memory fabric domains | Memory fabric ITD slope/cutoff applied; MLC SSA compensation functional | `DONE` |
| S7 | **ITD Common Controls** | Fuse checkout, global enable/disable, reset-time behavior (worst-case ITD during MB training), MIN_ACCURATE_TEMP | DMR thermal / ITD: Common control + reset-time behavior | Fuse-programmed coefficients match expectations; disable path zeroes compensation; reset-time worst-case ITD applied during MB training; PkgC6 interaction **ZBB on NWP — remove** | `DONE` |

**Local validation:** Domain groups have different FW owners (Acode vs PCode vs Primecode), different fuse sets, and different bar thresholds. Split passes. PkgC6-related TCs in S7 are ZBB on NWP and must be removed/skipped.

---

## 4. ZBB/Removal Actions

| TCD ID | Title | Finding | Action | Status |
|---|---|---|---|---|
| 22022420563 | CLTT TSOD based | Not POR for NWP LPDDR6/SOCAMM; TSOD not available for CLTT/system usage per NWP PAS | Mark disposition = `ZBB_N/A`; skip all TCs | `DONE` |
| 22022420603 (part) | ITD — PkgC6 interaction TCs | NWP has no PkgC6 (ZBB); PkgC6-related TCs within ITD are not applicable | Remove PkgC6 TCs from split TCDs or mark `ZBB_N/A` | `DONE` |

---

## 5. Spec-Basis Confirmation Needed

| TCD ID | Title | Issue | Action | Status |
|---|---|---|---|---|
| 22022420554 | CLTT PECI based | Co-Design confirmed: PECI-based CLTT is DDR5/DDR4 with TSOD only. NWP LPDDR6 uses MR4 exclusively. No BIOS knob for PECI CLTT on LP6. | **Mark ZBB_N/A.** KB updated. | `RESOLVED — ZBB_N/A` |
| 22022420567 | DDRIO Temp Compensation | Co-Design confirmed: separate spec subsystem owned by DDRIO PHY/Memory IO team. Fully independent CRI registers and RC firmware. | **Created TPF [16031170078](https://hsdes.intel.com/appstore/article-one/#/16031170078).** TCD reparented, KB + HSD pushed. | `RESOLVED — separate TPF` |

---

## 6. Missing Coverage — New TCD/TPF Candidates

| # | Finding | Spec ref | Proposed home | Bar sketch | Status |
|---|---|---|---|---|---|
| N1 | **Cross-die / broadcast thermal propagation** | NWP IMH SoC PM MAS: cross-die thermal; HPM DNS/UPS_EVENT_DELIVERY[cross_die_throttle] | TCD [16031170080](https://hsdes.intel.com/appstore/article-one/#/16031170080) under **IMH Thermal Control** (16031170063) | IMH→CBB: DNS_EVENT_DELIVERY → CBB overrides temp to TJMax → EMTTM throttle; CBB→IMH: UPS_EVENT_DELIVERY → IMH fabric = P1; FAST_THROTTLE_IN_0 wire <1ns | `RESOLVED — created + pushed` |
| N2 | **Thermal × RAPL / FastRAPL / PMAX interaction** | DMR thermal flows: limiter arbitration; PCode PID design | TCD [16031170081](https://hsdes.intel.com/appstore/article-one/#/16031170081) under **Core/CBB Thermal Control** (16031170062) | Both active → min(F_thermal, F_rapl) wins; status bits per limiter; no oscillation (PID design); PMAX Health Indicator | `RESOLVED — created + pushed` |
| N3 | **NWP TPMI-only thermal reporting migration** | NWP TPMI HAS/LUT; DMR/GNR MSR deprecation guidance | TCD [16031170082](https://hsdes.intel.com/appstore/article-one/#/16031170082) under **Thermal Status/Reporting** (16031170068) | 8 MSRs deprecated (return 0, writes ignored); TPMI replacements functional; TPMI-only fields (DLCP PCT, PMT aggregators) working | `RESOLVED — created + pushed` |

**Hard rule check:** N1 and N2 have bar sketches (pass). N3 has a bar sketch (pass). All are candidates for scaffolding via `nwp-tcd-description` after human confirmation.

---

## 7. KB §2 Spec-Ref Captures

Spec refs from Co-Design response to be captured in each TCD KB file's §2 (Functional Requirements / FR linkage):

| TCD ID | Spec ref to add to §2 |
|---|---|
| 22022420579 ACP | DMR thermal flows / core EMTTM feature family |
| 22022420585 CBB Thermal Mgmt | DMR thermal flows / CBB EMTTM; DMR CBB HAS |
| 22022420589 GPIO Interface (or splits) | NWP GPIO HAS: PROCHOT_N / MEMHOT_IN_N / MEMHOT_OUT_N / MEMTRIP_N / THERMTRIP_N sections |
| 22022420596 IMH Thermal Mgmt | NWP IMH SoC PM MAS: IMH thermal behavior |
| 22022420603 ITD (or splits) | DMR thermal flows / ITD compensation; NWP CCRD spec (ITD-capable domains) |
| 22022420606 MCAs | DMR thermal flows: DIE TOO HOT MCA |
| 22022420609 Prochot Flow | NWP GPIO HAS: PROCHOT_N + NWP PM MAS: inbound PROCHOT response |
| 22022420616 Thermal Interrupts | DMR thermal interrupt/reporting register semantics |
| 22022420619 Thermal Reporting | DMR thermal status + TPMI transition feature refs |
| 22022420625 Thermtrip | NWP IMH MAS 6.6 + NWP GPIO HAS: THERMTRIP_N |
| 22022420628 VR Hot | DMR thermal flows: VR Hot delivery + feature index |
| 22022420548 CLTT MR4 | NWP PM MAS: MR4-based CLTT for LP6 |
| 22022420570 Memhot | NWP GPIO HAS: MEMHOT IN/OUT + MC throttle consequences |
| 22022420575 Memtrip | NWP PM MAS: MEMTRIP generation + distinction from THERMTRIP |
| 22022420582 CBB DTS | NWP DTS / thermal diode sections |
| 22022420593 IMH DTS | NWP IMH DTS topology / chaining |

---

## Summary Statistics

| Category | Count |
|---|---|
| TPF splits | 2 (16030763139 → 5; 16030763141 → 2) |
| TPF keeps | 1 (16030763140) |
| TCD reparents | 11 (7 original + DDRIO + 3 reporting) |
| TCD splits | 2 (GPIO → 3; ITD → 4) |
| ZBB/remove | 4 (TSOD + CLTT PECI + ITD PkgC6 TCs) |
| Needs investigation | 0 (both resolved) |
| New coverage (TCD/TPF) | 3 (all created + pushed) |
| Spec refs to capture | 16 TCDs |
| **Total action items** | **35 (all RESOLVED)** |
