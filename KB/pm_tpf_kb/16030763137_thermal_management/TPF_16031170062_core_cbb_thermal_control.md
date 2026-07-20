# TPF NEW — Core/CBB Thermal Control

| Field | Value |
|-------|-------|
| **TPF ID** | [16031170062](https://hsdes.intel.com/appstore/article-one/#/16031170062) |
| **Title** | [NWP PM] Core/CBB Thermal Control |
| **Parent TP** | [16030763137 — NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Split from** | [16030763139 — Socket Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763139) |
| **KB last updated** | 2026-07-19 |
| **Co-Design T2 ref** | Ingest tracker §1A row A1 |

---

## Section 1: Feature Classification & Introduction

**Core/CBB Thermal Control** covers the socket-side thermal throttling algorithms for cores (ACP/EMTTM) and uncore/ring/CBB domains. This is the primary frequency-reduction mechanism activated when die temperature exceeds the Thermal Control Circuit (TCC) activation threshold. The feature is **firmware-heavy** — CBB PCode drives the PID throttle loop for CBB-level EMTTM, while Acode drives the per-core ACP (Autonomous Core Perimeter) thermal response.

**Classification:** Firmware-heavy (CBB PCode + Acode thermal control loops). Silicon provides DTS temperature sensors and FIVR frequency/voltage enforcement; firmware implements the PID algorithm and cross-core/cross-CBB throttle policy.

**Gating mechanism:** EMTTM is always enabled at boot (POR default). Feature control via:
- **Fuses:** TCC activation offset, per-domain temperature targets
- **BIOS knobs:** EMTTM enable/disable, temperature target offset (TPMI)
- **Runtime TPMI:** Dynamic temperature target adjustment

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| CBBs per socket | 2 (cbb0, cbb1) | NWP SOC topology |
| Cores per CBB | 48 (PantherCove) | NWP SOC topology |
| PID throttle owner — core | Acode (ACP autonomous) | DMR thermal flows |
| PID throttle owner — CBB/ring | CBB PCode (self + cross-throttle) | DMR thermal flows |
| Spec backing | DMR thermal flows / core EMTTM feature family | Co-Design T2 |

### TCDs Under This TPF

| TCD ID | Title | Action |
|---|---|---|
| [22022420579](https://hsdes.intel.com/appstore/article-one/#/22022420579) | ACP (Autonomous Core Perimeter) | Reparent from 16030763139 |
| [22022420585](https://hsdes.intel.com/appstore/article-one/#/22022420585) | CBB Thermal Management | Reparent from 16030763139 |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:16px;font-family:Arial,sans-serif;max-width:640px">
  <div style="font-weight:700;font-size:13px;text-align:center;margin-bottom:12px;border-bottom:2px solid #333;padding-bottom:8px">Core/CBB Thermal Control — Full-Stack Architecture</div>
  <div style="background:#4472C4;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 4: OS / Tool</strong> — TPMI read/write, PythonSV PEGA injection, thermal status MSR readback</div>
  <div style="background:#ED7D31;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 3: BIOS / Init</strong> — Temperature target programming, EMTTM enable/disable via TPMI_INIT</div>
  <div style="background:#A020F0;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 2: Firmware (PCode + Acode)</strong> — CBB PCode: PID throttle loop (self + cross-CBB); Acode: per-core ACP thermal response</div>
  <div style="background:#70AD47;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 1: Silicon HW</strong> — DTS thermal diodes, TCC activation comparator, FIVR frequency/voltage enforcement</div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | Notes |
|---|---|---|---|---|---|---|
| Layer 4: OS / Tool | ❌ | ❌ | ❌ | ✅ | ✅ | Requires booted OS or PythonSV |
| Layer 3: BIOS / Init | ✅ | ❌ | ❌ | ✅ | ✅ | VP validates TPMI programming |
| Layer 2: Firmware (PCode + Acode) | ✅ | ✅ | ✅ | ✅ | indirect | VP: PID logic; HSLE: single-CBB; XOS: cross-CBB |
| Layer 1: Silicon HW | ❌ | ✅ | ✅ | ✅ | indirect | RTL-level DTS/TCC behavior |

---

## Section 3: Validation Strategy

Layer coverage is mapped in §2 — Validation-Tier Layer Claim table identifies which tier validates each stack layer and flags any unclaimed layers as accepted gaps.

Key strategy:
- **ACP (core-level):** Acode autonomous — FV injects temperature via PythonSV, observes per-core frequency reduction
- **CBB EMTTM (uncore):** PCode PID loop — PSS VP validates algorithm, FV validates enforcement on silicon
- **Cross-CBB throttle:** Requires XOS (both CBBs present) for cross-die thermal propagation

---

## Section 4: Tier Coverage

*To be populated after TCD enrichment.*

---

## Section 5: Risks & Dependencies

- Dependency on DTS sensor accuracy (covered by Thermal Sensors & DTS Telemetry TPF)
- Cross-CBB throttle messaging depends on D2D/HPM transport (covered separately)

---

## Section 6: DFX Considerations

- TPMI thermal status registers for runtime observability
- PCode debug trace for PID loop inspection

---

## Section 7: Common Corner Cases

- Both CBBs at TCC simultaneously — verify PID loops don't oscillate
- Single CBB hot, other cold — cross-throttle propagation correctness
- EMTTM disable path — verify thermal protection fallback

---

## Section 8: TCD Coverage Summary & References

| TCD ID | Title | Status | TC Count |
|---|---|---|---|
| 22022420579 | ACP (Autonomous Core Perimeter) | Reparent pending | 6 |
| 22022420585 | CBB Thermal Management | Reparent pending | 7 |
