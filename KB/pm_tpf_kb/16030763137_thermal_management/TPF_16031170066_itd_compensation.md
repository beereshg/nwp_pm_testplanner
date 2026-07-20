# TPF NEW — ITD Compensation

| Field | Value |
|-------|-------|
| **TPF ID** | [16031170066](https://hsdes.intel.com/appstore/article-one/#/16031170066) |
| **Title** | [NWP PM] ITD Compensation |
| **Parent TP** | [16030763137 — NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Split from** | [16030763139 — Socket Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763139) |
| **KB last updated** | 2026-07-19 |
| **Co-Design T2 ref** | Ingest tracker §1A row A5 |

---

## Section 1: Feature Classification & Introduction

**ITD (Inverse Temperature Dependence) Compensation** is a temperature-dependent voltage compensation mechanism — NOT a frequency-throttle mechanism. As silicon heats up, MOSFET threshold voltage changes; ITD corrects voltage targets per domain to track temperature-dependent changes. ITD is fundamentally a **reliability and margin preservation** feature.

**Classification:** Firmware-heavy (multi-owner). Different FW agents own different domain groups:
- **Acode:** VccCore (ACP autonomous)
- **CBB PCode:** VccRing (CCF domains)
- **IMH Primecode:** VccInf, fabric/IO/memory domains

**Gating mechanism:**
- **Fuses:** `IMH_DOMAIN_ITD_SLOPE`, `ITD_CUTOFF_TJ`, `TRUE_TD_ENABLE`, `MIN_ACCURATE_TEMP` per domain
- **NWP delta:** Two new ITD-capable domains vs DMR: `VCCCAB` and `VCCC2CDIG`
- **Reset-time behavior:** Worst-case ITD during MB training; real-time ITD post-training

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| ITD-capable domain count | 10+ (VccCore, VccRing, VccInf, VccCFCIO, VccCFCMEM, VccFIXDIG, VccUCIEA, VccC2IA, VccFCFCAB/VccCAB, MLC SSA) | DMR thermal + NWP CCRD |
| NWP new domains | VCCCAB, VCCC2CDIG | NWP CCRD spec |
| FW owner — VccCore | Acode (autonomous) | DMR thermal flows |
| FW owner — VccRing | CBB PCode | DMR thermal flows |
| FW owner — Fabric/IO/Mem | IMH Primecode | NWP PM MAS |
| PkgC6 ITD interaction | ZBB on NWP (no PkgC6) | NWP PM MAS |
| Spec backing | DMR thermal flows / ITD compensation; NWP CCRD spec | Co-Design T2 |

### TCDs Under This TPF

| TCD ID | Title | Action |
|---|---|---|
| NEW | Core/Ring Rail ITD | Split from 22022420603 |
| NEW | Fabric/IO Rail ITD | Split from 22022420603 |
| NEW | Memory/CFC Rail ITD | Split from 22022420603 |
| NEW | ITD Common Controls | Split from 22022420603 |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:16px;font-family:Arial,sans-serif;max-width:640px">
  <div style="font-weight:700;font-size:13px;text-align:center;margin-bottom:12px;border-bottom:2px solid #333;padding-bottom:8px">ITD Compensation — Full-Stack Architecture</div>
  <div style="background:#4472C4;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 5: TPMI / MSR / PMSB</strong> — ITD status readback, debug observability</div>
  <div style="background:#ED7D31;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 4: BIOS / Init</strong> — Fuse coefficient readout, ITD enable/disable programming</div>
  <div style="background:#A020F0;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 3a: Acode (VccCore)</strong> — Autonomous per-core ITD: periodic temp readout + voltage correction in WP recalculation</div>
  <div style="background:#9C27B0;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 3b: CBB PCode (VccRing)</strong> — CCF FIVR domain ITD: min/max temp computation across CCF domains</div>
  <div style="background:#6A1B9A;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 3c: IMH Primecode (Fabric/IO/Mem)</strong> — VccInf, VccCFCIO, VccCFCMEM, VccFIXDIG, VccUCIEA, VccCAB ITD</div>
  <div style="background:#70AD47;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 2: Reset-Time ITD</strong> — UCIe boot-time: worst-case ITD during MB training; one-time correction at exit</div>
  <div style="background:#FF0000;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 1: Silicon HW</strong> — DTS thermal diodes (per-domain temp source), FIVR voltage enforcement, fuse storage</div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | Notes |
|---|---|---|---|---|---|---|
| Layer 5: TPMI / MSR / PMSB | ✅ | ✅ | ✅ | ✅ | ✅ | All tiers read status |
| Layer 4: BIOS / Init | ✅ | ❌ | ❌ | ✅ | ✅ | VP validates fuse readout |
| Layer 3a: Acode (VccCore) | ✅ | ✅ | ✅ | ✅ | indirect | |
| Layer 3b: CBB PCode (VccRing) | ✅ | ✅ | ✅ | ✅ | indirect | |
| Layer 3c: IMH Primecode | ✅ | ✅ | ✅ | ✅ | indirect | HSLE: IMH-only |
| Layer 2: Reset-Time ITD | ✅ | ✅ | ✅ | ✅ | indirect | VP/HSLE: boot-time behavior |
| Layer 1: Silicon HW | ❌ | ✅ | ✅ | ✅ | indirect | |

---

## Section 3: Validation Strategy

ITD validation requires temperature injection (DTS override or thermal stimulus) to verify voltage compensation tracks temperature. Each domain group is tested independently because FW owners differ.

- **Core/Ring:** Acode/PCode — inject temp, verify voltage via VID readback
- **Fabric/IO/Mem:** Primecode — inject temp, verify FIVR domain voltage
- **Reset-time:** Observe ITD behavior across MB training phases
- **Common controls:** Fuse checkout, disable path, MIN_ACCURATE_TEMP guard

---

## Section 4: Tier Coverage

*To be populated after TCD enrichment.*

---

## Section 5: Risks & Dependencies

- PkgC6 ITD interaction is ZBB on NWP — all PkgC6 TCs must be removed/skipped
- NWP new domains (VCCCAB, VCCC2CDIG) have no DMR N-1 baseline — require fresh validation
- Temperature injection fidelity varies by environment (Simics vs HSLE vs silicon)

---

## Section 6: DFX Considerations

- TPMI ITD status for per-domain compensation readback
- PCode/Primecode debug trace for ITD slope/cutoff calculation inspection
- FIVR VID readback for voltage compensation verification

---

## Section 7: Common Corner Cases

- All domains at MIN_ACCURATE_TEMP boundary — verify guard condition
- ITD disable → re-enable transition — voltage returns to compensated value
- Reset-time: MB training exit → real-time ITD resumption — verify no voltage glitch
- NWP new domain (VCCCAB) at extreme temperature — fuse coefficient validation

---

## Section 8: TCD Coverage Summary & References

| TCD ID | Title | Status | TC Count |
|---|---|---|---|
| NEW | Core/Ring Rail ITD | Scaffold pending (split from 22022420603) | TBD |
| NEW | Fabric/IO Rail ITD | Scaffold pending (split from 22022420603) | TBD |
| NEW | Memory/CFC Rail ITD | Scaffold pending (split from 22022420603) | TBD |
| NEW | ITD Common Controls | Scaffold pending (split from 22022420603) | TBD |
