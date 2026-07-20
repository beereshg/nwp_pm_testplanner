# TPF NEW — Thermal Sensors & DTS Telemetry

| Field | Value |
|-------|-------|
| **TPF ID** | [16031170067](https://hsdes.intel.com/appstore/article-one/#/16031170067) |
| **Title** | [NWP PM] Thermal Sensors & DTS Telemetry |
| **Parent TP** | [16030763137 — NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Split from** | [16030763141 — Thermal Reporting/Telemetry](https://hsdes.intel.com/appstore/article-one/#/16030763141) |
| **KB last updated** | 2026-07-19 |
| **Co-Design T2 ref** | Ingest tracker §1C row C1 |

---

## Section 1: Feature Classification & Introduction

**Thermal Sensors & DTS Telemetry** covers the thermal sensor inventory, DTS (Digital Thermal Sensor) readings, and dielet telemetry exposure for both CBB and IMH dies on NWP. This is the **measurement infrastructure** — what temperatures are sensed, where, and how they are exposed as telemetry. Distinct from reporting interfaces (TPMI/MSR readback) which consume these readings.

**Classification:** Silicon-heavy. DTS sensors and thermal diodes are analog silicon; the readout path and telemetry aggregation involves firmware (Primecode/PCode).

**Sensor topology:**
- **CBB sensors:** AON (always-on), CBO cluster, CCP, Core, SOC DTS
- **IMH sensors:** Accelerator, CGU, D2D, IO, MIO, Mem DTS
- **DTS daisy-chain:** Cross-dielet propagation for package-level temperature

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| CBB DTS types | AON, CBO cluster, CCP, Core, SOC | NWP DTS spec |
| IMH DTS types | Accelerator, CGU, D2D, IO, MIO, Mem | NWP DTS spec |
| DTS daisy-chain | Cross-dielet propagation (IMH + CBB) | NWP IMH MAS |
| Spec backing | NWP DTS / thermal diode sections | Co-Design T2 |

### TCDs Under This TPF

| TCD ID | Title | Action |
|---|---|---|
| [22022420582](https://hsdes.intel.com/appstore/article-one/#/22022420582) | CBB DTS & Telemetry | Reparent from 16030763141 |
| [22022420593](https://hsdes.intel.com/appstore/article-one/#/22022420593) | IMH DTS & Telemetry | Reparent from 16030763141 |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:16px;font-family:Arial,sans-serif;max-width:640px">
  <div style="font-weight:700;font-size:13px;text-align:center;margin-bottom:12px;border-bottom:2px solid #333;padding-bottom:8px">Thermal Sensors & DTS Telemetry — Full-Stack Architecture</div>
  <div style="background:#4472C4;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 4: Telemetry Consumer</strong> — PMT, TPMI readback, Primecode/PCode temperature polling</div>
  <div style="background:#ED7D31;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 3: Aggregation</strong> — Package-level max-of-all-sensors, per-die max, DTS daisy-chain propagation</div>
  <div style="background:#A020F0;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 2: Per-Sensor Readout</strong> — ADC conversion, calibration/trim, digital readout register per DTS</div>
  <div style="background:#70AD47;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 1: Analog Sensors</strong> — Thermal diodes, DTS analog front-end, silicon temperature sensing elements</div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | Notes |
|---|---|---|---|---|---|---|
| Layer 4: Telemetry Consumer | ✅ | ✅ | ✅ | ✅ | ✅ | All tiers read telemetry |
| Layer 3: Aggregation | ❌ | Partial | ✅ | ✅ | indirect | HSLE: single-die only; XOS: cross-die chain |
| Layer 2: Per-Sensor Readout | ❌ | ✅ | ✅ | ✅ | indirect | RTL ADC behavior |
| Layer 1: Analog Sensors | ❌ | ❌ | ❌ | ✅ | ✅ | Real analog silicon only |

---

## Section 3: Validation Strategy

- **Sensor accuracy:** Silicon-only (analog behavior)
- **Readout path:** HSLE validates RTL ADC/digital readout
- **Cross-die aggregation:** XOS required for DTS daisy-chain
- **Telemetry exposure:** All tiers validate register readback

---

## Section 4: Tier Coverage

*To be populated after TCD enrichment.*

---

## Section 5: Risks & Dependencies

- Analog sensor accuracy is silicon-only — pre-Si coverage limited to digital readout path
- DTS daisy-chain cross-die propagation requires XOS for multi-die validation

---

## Section 6: DFX Considerations

- DTS readout registers for per-sensor temperature inspection
- PMT telemetry for aggregated temperature monitoring

---

## Section 7: Common Corner Cases

- Sensor failure / stuck reading — how does aggregation handle invalid input?
- All sensors at max temperature simultaneously
- Single sensor hot, others cold — max-of-all accuracy
- DTS daisy-chain latency during rapid temperature change

---

## Section 8: TCD Coverage Summary & References

| TCD ID | Title | Status | TC Count |
|---|---|---|---|
| 22022420582 | CBB DTS & Telemetry | Reparent pending | 7 |
| 22022420593 | IMH DTS & Telemetry | Reparent pending | 8 |
