# TPF 16031170066 — ITD Compensation

| Field | Value |
|-------|-------|
| **TPF ID** | [16031170066](https://hsdes.intel.com/appstore/article-one/#/16031170066) |
| **Title** | [NWP PM] ITD Compensation |
| **Parent TP** | [16030763137 — NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Split from** | [16030763139 — Socket Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763139) |
| **KB last updated** | 2026-07-20 |
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

| TCD ID | Title | TCs | Action |
|---|---|---|---|
| [16031170072](https://hsdes.intel.com/appstore/article-one/#/16031170072) | [ITD] Core/Ring Rail ITD | 22022421522, 22022421524 | Split from 22022420603 |
| [16031170073](https://hsdes.intel.com/appstore/article-one/#/16031170073) | [ITD] Fabric/IO Rail ITD | 22022421535, 22022421536, 22022421546, 22022421538, 22022421542, 22022458470 | Split from 22022420603 |
| [16031170074](https://hsdes.intel.com/appstore/article-one/#/16031170074) | [ITD] Memory/CFC Rail ITD | 22022421525, 22022421540 | Split from 22022420603 |
| [16031170075](https://hsdes.intel.com/appstore/article-one/#/16031170075) | [ITD] ITD Common Controls | 22022421521, 22022421528, 22022421534 | Split from 22022420603 |

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

### ITD Compensation Block Diagram

```
  DTS / Thermal Diodes
  (per-domain temperature sources)
         |  thermal inputs
         v
  ITD Controller (PCode / Primecode / Acode per domain)
         |  <--- ITD Fuse / Config Inputs:
         |        ITD_SLOPE / SLOPE2, ITD_CUTOFF_Vx
         |        ITD_CUTOFF_TJ, MIN_ACCURATE_TEMP
         |        ITD_MIN_OVERRIDE_TEMP, TRUE_TD_ENABLE
         |  <--- Reset / Init Control:
         |        Boot phase: worst-case ITD
         |        UCIe MB training: real-time ITD (one-time correction)
         |        Post-training: safe boot ITD until reset complete
         |
         v  voltage compensation per domain
  Voltage Domains:
    VccCore (ACP)  -- Acode autonomous         [TCD 16031170072]
    VccRing (CCF)  -- CBB PCode                [TCD 16031170072]
    VccInf  (Inf)  -- Primecode                [TCD 16031170073]
    VCCC2IA (UCIe) -- boot-ITD + runtime       [TCD 16031170073]
    VCCUCIEA       -- UCIe A-side              [TCD 16031170073]
    VCCCFCIO       -- IO fabric                [TCD 16031170073]
    VCCCFCMEM      -- Memory fabric            [TCD 16031170074]
    VCCFIXDIG      -- Fixed digital            [TCD 16031170073]
    VCCFCFCAB/VCCCAB -- CAB domain (NWP new)   [TCD 16031170073]
    VCC MLC SSA    -- Core MLC SSA             [TCD 16031170074]
         |
         v  compensated domain behavior
  Consumer blocks:
    ACP / CCF / INF / UCIe / MLC SSA / CAB

  ITD Controller --> TPMI / MSR / PMSB (status + debug)
                 --> IMH / NIO Root Die (root-die compensation)
                 --> CBB0 / CBB1 (per-die compensation path)
```

### Supported ITD Domains (NWP) — Domain→TCD→TC Map

| Domain | Rail | FW Owner | TCD | TC ID |
|--------|------|----------|-----|-------|
| ACP | VccCore | Acode autonomous | 16031170072 | [22022421522](https://hsdes.intel.com/appstore/article-one/#/22022421522) |
| CCF | VccRing | CBB PCode | 16031170072 | [22022421524](https://hsdes.intel.com/appstore/article-one/#/22022421524) |
| Core MLC SSA | VCC MLC SSA | PCode | 16031170074 | [22022421525](https://hsdes.intel.com/appstore/article-one/#/22022421525) |
| Inf | VccInf | Primecode | 16031170073 | [22022421535](https://hsdes.intel.com/appstore/article-one/#/22022421535) |
| UCIe | VCCC2IA | PCode + boot-ITD | 16031170073 | [22022421536](https://hsdes.intel.com/appstore/article-one/#/22022421536) |
| UCIe-A | VCCUCIEA | PCode | 16031170073 | [22022421546](https://hsdes.intel.com/appstore/article-one/#/22022421546) |
| IO Fabric | VCCCFCIO | Primecode | 16031170073 | [22022421538](https://hsdes.intel.com/appstore/article-one/#/22022421538) |
| Mem Fabric | VCCCFCMEM | Primecode | 16031170074 | [22022421540](https://hsdes.intel.com/appstore/article-one/#/22022421540) |
| Fixed Digital | VCCFIXDIG | Primecode | 16031170073 | [22022421542](https://hsdes.intel.com/appstore/article-one/#/22022421542) |
| CAB (NWP new) | VCCFCFCAB / VCCCAB | Primecode | 16031170073 | [22022458470](https://hsdes.intel.com/appstore/article-one/#/22022458470) |

### Interface & Register Matrix

| Register / Interface | Field | Domain | Feature Effect | TCD |
|---|---|---|---|---|
| `IMH_DOMAIN_ITD_SLOPE` | Fuse | All | Slope coefficient for linear compensation | 16031170075 (checkout) |
| `ITD_CUTOFF_TJ` | Fuse | All | Temperature cutoff above which ITD is clipped | 16031170075 |
| `TRUE_TD_ENABLE` | Fuse | All | Master enable for ITD per domain | 16031170075 |
| `MIN_ACCURATE_TEMP` | Fuse | All | Below this temp, DTS readings unreliable → override | 16031170075 |
| `ITD_MIN_OVERRIDE_TEMP` | Fuse | All | Override temp used when below MIN_ACCURATE_TEMP | 16031170075 |
| DTS per-core thermal diode | Sensor | VccCore | Per-core temperature input for Acode | 16031170072 |
| CCF FIVR domain DTS | Sensor | VccRing | Per-FIVR temperature for PCode min/max calc | 16031170072 |
| TPMI ITD status | Readback | All | Per-domain ITD compensation readback | All |
| HPM message (temp delivery) | Cross-die | VccInf | IMH temperature delivery for Inf ITD | 16031170073 |
| VID / FIVR voltage | Output | All | Compensated voltage target | All |

### SKU / Config Distinctions

| SKU / Config | Distinction | TCDs Affected |
|---|---|---|
| NWP new domains (VCCCAB, VCCC2CDIG) | No DMR N-1 baseline; fresh validation required | 16031170073 |
| PkgC6 disabled (ZBB on NWP) | All PkgC6-related ITD scenarios removed | 16031170075 |
| Fuse coefficients per-SKU | ITD_SLOPE/cutoff may vary by SKU; checkout must use SKU-specific expected values | 16031170075 |

### Microarch→Scenario Coverage Matrix

| # | Element (from §2) | Category | Implied WHAT | Realized as TCD | TC(s) | Tier | Status |
|---|---|---|---|---|---|---|---|
| 1 | VccCore Acode autonomous compensation | Layer 3a | Acode periodic temp→VID correction | 16031170072 | 22022421522 | FV, HSLE | ✓ |
| 2 | VccRing PCode min/max CCF FIVR temp | Layer 3b | PCode CCF domain compensation | 16031170072 | 22022421524 | FV, HSLE | ✓ |
| 3 | VccInf Primecode compensation | Layer 3c | Primecode Inf domain ITD | 16031170073 | 22022421535 | FV, HSLE | ✓ |
| 4 | VCCC2IA boot-time + runtime ITD | Layer 2+3c | UCIe boot-time one-time correction + runtime | 16031170073 | 22022421536 | FV, HSLE | ✓ |
| 5 | VCCUCIEA PCode compensation | Layer 3c | UCIe-A domain ITD | 16031170073 | 22022421546 | FV, HSLE | ✓ |
| 6 | VCCCFCIO Primecode compensation | Layer 3c | IO fabric domain ITD | 16031170073 | 22022421538 | FV, HSLE | ✓ |
| 7 | VCCCFCMEM Primecode compensation | Layer 3c | Memory fabric domain ITD | 16031170074 | 22022421540 | FV, HSLE | ✓ |
| 8 | VCCFIXDIG Primecode compensation | Layer 3c | Fixed digital domain ITD | 16031170073 | 22022421542 | FV, HSLE | ✓ |
| 9 | VCCFCFCAB / VCCCAB (NWP new) | Layer 3c | CAB domain ITD — NWP new, no N-1 | 16031170073 | 22022458470 | FV | ✓ |
| 10 | Core MLC SSA PCode compensation | Layer 3b | MLC SSA domain ITD | 16031170074 | 22022421525 | FV, HSLE | ✓ |
| 11 | ITD fuse coefficient readback | Layer 4 | Fuse values match expected | 16031170075 | 22022421521 | FV, HSLE, VP | ✓ |
| 12 | ITD global disable path | Layer 3 | Disable → no compensation all domains | 16031170075 | 22022421528 | FV, HSLE | ✓ |
| 13 | Reset-time worst-case/safe ITD | Layer 2 | Boot-phase safe ITD → MB training real-time → safe | 16031170075 | 22022421534 | FV, HSLE, VP | ✓ |
| 14 | MIN_ACCURATE_TEMP guard | Layer 3 | Below threshold → override temp used | 16031170075 | GAP (within 22022421521?) | FV, HSLE | ⚠️ PARTIAL |
| 15 | VCCC2CDIG (NWP new domain) | Layer 3c | NWP-specific new domain compensation | 16031170073 | GAP | FV | ⚠️ GAP |
| 16 | ITD re-enable after disable | Layer 3 | Voltage returns to compensated value | 16031170075 | GAP (within 22022421528?) | FV, HSLE | ⚠️ PARTIAL |
| 17 | Rapid temp change during loop | Layer 3 | No stale voltage; updates per loop rate | ALL | GAP | FV | ⚠️ GAP |

---

## Section 3: Validation Strategy

ITD validation requires temperature injection (DTS override or thermal stimulus) to verify voltage compensation tracks temperature. Each domain group is tested independently because FW owners differ.

### Tier Rationale

| Tier | What it validates | Why needed |
|---|---|---|
| PSS (VP) | Fuse readout, disable path, reset-time state machine logic | Safe negative testing; can inject invalid fuse values without silicon risk |
| PSS (HSLE) | Within-die PCode/Primecode ITD computation, FIVR domain compensation | RTL-accurate voltage computation; validates slope×temp math |
| PSS (XOS) | Cross-die HPM temp delivery for VccInf ITD | Only env with both IMH+CBB RTL — mandatory for cross-die protocol |
| FV | All domains: real DTS temp → real FIVR voltage compensation | Gold standard — real silicon behavior, real power/thermal response |
| PV | indirect (OS sees stable frequency/voltage) | No direct PV TC planned — ITD is transparent to OS |

### Domain-Group Test Strategy

- **Core/Ring (16031170072):** Inject per-core DTS temp, verify VccCore VID change (Acode); inject CCF FIVR temps, verify VccRing VID (PCode)
- **Fabric/IO (16031170073):** Per-domain temp injection → per-domain FIVR VID verification; NWP-new domains (VCCCAB, VCCC2CDIG) require fresh validation without N-1 reference
- **Memory/CFC (16031170074):** VccCFCMEM and MLC SSA temp→VID; memory-intensive workload thermal stress as stimulus
- **Common Controls (16031170075):** Fuse checkout (all domains), disable path (global ITD off), reset-time behavior (boot phases), MIN_ACCURATE_TEMP guard

---

## Section 4: Tier Coverage

| TCD | FV | PSS (VP) | PSS (HSLE) | PSS (XOS) | PV |
|---|---|---|---|---|---|
| 16031170072 — Core/Ring Rail | ✅ (2 TCs) | planned | planned | planned (VccRing cross-die) | indirect |
| 16031170073 — Fabric/IO Rail | ✅ (6 TCs) | planned | planned | planned (VccInf HPM) | indirect |
| 16031170074 — Memory/CFC Rail | ✅ (2 TCs) | planned | planned | ❌ | indirect |
| 16031170075 — Common Controls | ✅ (3 TCs) | planned | planned | ❌ | indirect |
| **Total** | **13 TCs** | 0 | 0 | 0 | 0 |

---

## Section 5: Risks & Dependencies

### Active Risks

- **NWP new domains (VCCCAB, VCCC2CDIG) have no DMR N-1 baseline** — require fresh validation; fuse coefficient expected values unconfirmed
- **Temperature injection fidelity varies by environment** — Simics DTS override is model-limited; HSLE is RTL-accurate; FV uses real DTS
- **VCCC2CDIG has no TC yet** — gap identified in coverage matrix (row 15)
- **Cross-die HPM temp delivery (VccInf)** — only testable in XOS env; no XOS TCs exist yet

### Accepted Coverage Limitations

| Gap ID | Description | Coverage Today | Accepted Rationale |
|--------|-------------|----------------|-------------------|
| G-1 | PkgC6 ITD interaction | None (ZBB on NWP) | NWP does not support PkgC6 — feature is architecturally absent |
| G-2 | PV-tier ITD validation | Indirect only | ITD is transparent to OS; no user-visible interface to validate directly from PV |
| G-3 | Silicon HW layer (Layer 1) analog behavior | FV only | DTS diode accuracy is HW-intrinsic; only real silicon validates analog behavior |

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

| TCD ID | Title | Status | TC Count | Key TCs |
|---|---|---|---|---|
| [16031170072](https://hsdes.intel.com/appstore/article-one/#/16031170072) | [ITD] Core/Ring Rail ITD | draft | 2 | 22022421522, 22022421524 |
| [16031170073](https://hsdes.intel.com/appstore/article-one/#/16031170073) | [ITD] Fabric/IO Rail ITD | draft | 6 | 22022421535, 22022421536, 22022421546, 22022421538, 22022421542, 22022458470 |
| [16031170074](https://hsdes.intel.com/appstore/article-one/#/16031170074) | [ITD] Memory/CFC Rail ITD | draft | 2 | 22022421525, 22022421540 |
| [16031170075](https://hsdes.intel.com/appstore/article-one/#/16031170075) | [ITD] ITD Common Controls | draft | 3 | 22022421521, 22022421528, 22022421534 |

**Total: 4 TCDs, 13 TCs (all FV), 0 PSS TCs (planned)**

### Original TCD (superseded)

| TCD ID | Title | Status | Disposition |
|---|---|---|---|
| [22022420603](https://hsdes.intel.com/appstore/article-one/#/22022420603) | [SoC Thermal Management] ITD | open | Superseded — all 13 TCs redistributed to child TCDs above |

### References

- [NWP PM MAS — ITD section](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [DMR CBB ITD HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/ITD/ITD.html)
- [DMR Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/thermals/dmr_thermal.html)
- [D2D PM HAS — UCIe boot-time ITD](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/D2D_PM/D2D_PM.html)
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features)
- [Primecode FHAS Index](https://docs.intel.com/documents/primecode/fhas/index.html)

### Coverage Gaps (from Microarch→Scenario Matrix)

| # | Gap | Priority | Recommended Action |
|---|---|---|---|
| 15 | VCCC2CDIG (NWP new domain) — no TC | High | Create TC under TCD 16031170073; NWP-new domain has no N-1 baseline |
| 14 | MIN_ACCURATE_TEMP guard — partial (within fuse checkout TC) | Medium | Verify 22022421521 explicitly tests below-threshold scenario; else split TC |
| 16 | ITD re-enable after disable — partial (within disable TC) | Low | Verify 22022421528 covers re-enable transition; else add scenario |
| 17 | Rapid temp change during loop — no TC | Low | Consider soak/stress TC injection scenario |
