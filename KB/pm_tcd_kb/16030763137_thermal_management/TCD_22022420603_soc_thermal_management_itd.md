# TCD: [SoC Thermal Management] ITD

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420603](https://hsdes.intel.com/appstore/article-one/#/22022420603) |
| **Title** | [SoC Thermal Management] ITD |
| **Status** | open |
| **Parent TP** | [16030763137 -- NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Feature** | SoC Thermal |
| **Sub-Feature** | SoC Thermal |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-07-19 |
| **Co-Design T2 action** | ⚠️ SPLIT into 4 TCDs: Core/Ring Rail ITD, Fabric/IO Rail ITD, Memory/CFC Rail ITD, ITD Common Controls. PkgC6 TCs → ZBB on NWP. See `codesign_T2_ingest_thermal_mgmt.md` §3B. |
| **Spec refs (T2)** | DMR thermal flows / ITD compensation; NWP CCRD spec (ITD-capable domains); NWP PM MAS + DMR CBB ITD HAS |

## Section 1: Architecture / Micro-architecture and Functionality

**ITD (Inverse Temperature Dependence)** is a **temperature-dependent voltage compensation** mechanism — not a frequency-throttle mechanism. As silicon heats up, MOSFET threshold voltage changes; ITD corrects the voltage targets per domain to track these temperature-dependent changes. ITD is fundamentally a **reliability and margin preservation** feature.

**Key architectural facts (from NWP PM MAS + DMR CBB ITD HAS):**
- NWP explicitly supports ITD; rails documented in NWP CCRD spec
- NWP adds **two new ITD-capable domains: `VCCCAB` and `VCCC2CDIG`** vs DMR
- ITD uses fuse-programmed slope/cutoff coefficients per domain: `IMH_DOMAIN_ITD_SLOPE`, `ITD_CUTOFF_TJ`, `TRUE_TD_ENABLE`, `MIN_ACCURATE_TEMP`, etc.
- **ACP/VccCore ITD:** autonomous in Acode; periodic temperature readout + voltage correction in WP recalculation
- **CCF/VccRing ITD:** CBB PCode computes per-FIVR domain using min/max temp of CCF FIVR domains
- **UCIe boot-time ITD:** one-time correction at MB training exit; CBB uses worst-case ITD during training; real-time ITD resumes post-training
- **Reset-time behavior:** before MB training = safe/worst-case ITD; during training = real-time ITD; after training = safe again until reset sequence complete

### Block Diagram

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
    VccCore (ACP)  -- Acode autonomous
    VccRing (CCF)  -- CBB PCode
    VccInf  (Inf)  -- Primecode
    VCCC2IA (UCIe) -- boot-ITD + runtime
    VCCUCIEA       -- UCIe A-side
    VCCCFCIO       -- IO fabric
    VCCCFCMEM      -- Memory fabric
    VCCFIXDIG      -- Fixed digital
    VCCFCFCAB/VCCCAB -- CAB domain (NWP new)
         |
         v  compensated domain behavior
  Consumer blocks:
    ACP / CCF / INF / UCIe / MLC SSA / CAB

  ITD Controller --> TPMI / MSR / PMSB (status + debug)
                 --> IMH / NIO Root Die (root-die compensation)
                 --> CBB0 / CBB1 (per-die compensation path)
```

### Supported ITD Domains (NWP)

| Domain | Rail | Implementation | TC |
|--------|------|----------------|----|
| ACP | VccCore | Acode autonomous | 22022421522 |
| CCF | VccRing | CBB PCode | 22022421524 |
| Core MLC SSA | VCC MLC SSA | PCode | 22022421525 |
| Inf | VccInf | Primecode | 22022421535 |
| UCIe | VCCC2IA | PCode + boot-ITD | 22022421536 |
| UCIe-A | VCCUCIEA | PCode | 22022421546 |
| IO Fabric | VCCCFCIO | Primecode | 22022421538 |
| Mem Fabric | VCCCFCMEM | Primecode | 22022421540 |
| Fixed Digital | VCCFIXDIG | Primecode | 22022421542 |
| CAB | VCCFCFCAB / VCCCAB | Primecode (NWP new) | 22022458470 |
| Fuse checkout | All | Fuse readback | 22022421521 |
| ITD disable | All | Disable path | 22022421528 |
| ITD during reset | UCIe / all | Boot/reset phase | 22022421534 |

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421521](https://hsdes.intel.com/appstore/article-one/#/22022421521) | [ITD] Fuse checkout | Runnable_On_N-1 |
| [22022421522](https://hsdes.intel.com/appstore/article-one/#/22022421522) | [ITD] Verify ACP (VccCore) ITD | Runnable_On_N-1 |
| [22022421524](https://hsdes.intel.com/appstore/article-one/#/22022421524) | [ITD] Verify CCF (VccRing) ITD | Runnable_On_N-1 |
| [22022421525](https://hsdes.intel.com/appstore/article-one/#/22022421525) | [ITD] Verify Core MLC SSA (VCC MLC SSA) ITD | Runnable_On_N-1 |
| [22022421528](https://hsdes.intel.com/appstore/article-one/#/22022421528) | [ITD] Verify ITD disable | Runnable_On_N-1 |
| [22022421534](https://hsdes.intel.com/appstore/article-one/#/22022421534) | [ITD] Verify ITD during reset | Runnable_On_N-1 |
| [22022421535](https://hsdes.intel.com/appstore/article-one/#/22022421535) | [ITD] Verify Inf (VccInf) ITD | Runnable_On_N-1 |
| [22022421536](https://hsdes.intel.com/appstore/article-one/#/22022421536) | [ITD] Verify UCIe (VCCC2IA) ITD | Runnable_On_N-1 |
| [22022421538](https://hsdes.intel.com/appstore/article-one/#/22022421538) | [ITD] Verify VCCCFCIO ITD | Runnable_On_N-1 |
| [22022421540](https://hsdes.intel.com/appstore/article-one/#/22022421540) | [ITD] Verify VCCCFCMEM ITD | Runnable_On_N-1 |
| [22022421542](https://hsdes.intel.com/appstore/article-one/#/22022421542) | [ITD] Verify VCCFIXDIG ITD | Runnable_On_N-1 |
| [22022421546](https://hsdes.intel.com/appstore/article-one/#/22022421546) | [ITD] Verify VCCUCIEA ITD | Runnable_On_N-1 |
| [22022458470](https://hsdes.intel.com/appstore/article-one/#/22022458470) | [ITD] Verify VCCFCFCAB ITD | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Path | Purpose |
|-----------|------|---------|
| **ITD fuses** | `sv.socket0.imh0.fuses.punit.*itd*` | Slope, cutoff, cutoff_tj, min_accurate_temp, true_td_enable |
| **DTS / thermal diode** | Per-domain DTS paths | Temperature input for ITD computation |
| TPMI | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.*` | Thermal status and ITD visibility |
| MSR | Per-core/die MSRs | Thermal status bits |
| PMSB | `sv.socket0.imh0.compute*.pma*.gpsb` | PMA telemetry |
| HPM | CBB ↔ IMH HPM messages | VccInf temperature delivery for Inf ITD |

---

## Section 3: Reset, Power, and Clocking

- Thermal DTS sensors initialize during PH1 (BIOS TPMI init); readings valid after PH6
- TCC threshold programmed by BIOS; runtime update via TPMI
- VR Hot and Prochot signals are asynchronous; PCode responds within 1 slow-loop (~1 ms)
- Thermal state persists across warm reset; cold reset re-initializes all thresholds

---

## Section 4: Programming Model

- BIOS programs TCC thresholds and thermal knobs during CPL3
- PCode slow-loop (~1 ms) polls thermal telemetry and applies throttle decisions
- OS reads thermal data via MSRs and TPMI; writes to override registers require privilege
- Test methodology: PMx `prochot_thermal` / `thermal_mgt` plugin or direct register injection

---

## Section 5: Operational Behavior

Thermal events trigger a response chain:
1. Hardware sensor (DTS / VR Hot / Prochot) asserts
2. PCode detects via PMSB poll or interrupt within 1 slow-loop
3. PCode applies throttle: reduce core/mesh frequency toward P1 or Pm
4. PCode reports via TPMI status registers and MSR thermal bits
5. On event clear: PCode ramps frequency back to autonomous level

All 13 TCs in this TCD validate different aspects of this chain for the **ITD** scenario.

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| ITD fuse values invalid or zero | Domain falls back to safe/default compensation; fuse readback fails validation |
| DTS below `MIN_ACCURATE_TEMP` | `ITD_MIN_OVERRIDE_TEMP` used instead of raw temperature; verify override path |
| ITD disabled | No voltage correction applied; domain at safe boot voltage regardless of temperature |
| UCIe reset during boot-ITD window | Boot-phase rules apply: safe/worst-case until training completes |
| Temperature above `ITD_CUTOFF_TJ` | ITD above-cutoff behavior; True TD disabled = no further correction |
| Multiple CCF FIVR domains at different temperatures | Each domain computes separate ITD result using domain-local temperature |
| NWP-new domain `VCCCAB` / `VCCC2CDIG` | ITD applies as with other domains; verify NWP-specific domain readback |
| Rapid temperature change during compensation loop | Compensation updates per loop rate; no stale voltage applied |

---

## Section 7: Security / Safety / Policy

- TCC thresholds may be BIOS-locked before OS handoff
- VR Hot and Prochot are safety-critical paths; test injection requires privileged access
- Thermal MSR overrides require OS privilege level

---

## Section 8: References

- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP supports ITD; new domains VCCCAB and VCCC2CDIG; NWP ITD scope
- [DMR CBB ITD HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/ITD/ITD.html) -- CCF ITD; per-FIVR compensation; slope/cutoff fuse model
- [DMR Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/thermals/dmr_thermal.html) -- ACP/VccCore ITD autonomous; CCF ITD; Inf ITD delivery via HPM
- [D2D PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/D2D_PM/D2D_PM.html) -- UCIe boot-time ITD behavior; reset-phase safe vs real-time ITD
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features) -- NWP ITD feature applicability
- [Primecode FHAS Index](https://docs.intel.com/documents/primecode/fhas/index.html) -- ITD as Primecode feature area
