# TPF NEW — IMH Thermal Control

| Field | Value |
|-------|-------|
| **TPF ID** | [16031170063](https://hsdes.intel.com/appstore/article-one/#/16031170063) |
| **Title** | [NWP PM] IMH Thermal Control |
| **Parent TP** | [16030763137 — NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Split from** | [16030763139 — Socket Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763139) |
| **KB last updated** | 2026-07-19 |
| **Co-Design T2 ref** | Ingest tracker §1A row A2 |

---

## Section 1: Feature Classification & Introduction

**IMH Thermal Control** covers the IMH2-specific thermal control behavior on NWP, including the IMH-die PID throttle, cold action path, and IMH thermal disable. This is architecturally separate from CBB-side EMTTM because IMH2 runs its own firmware (Primecode) with independent thermal policy, different temperature sensors (IMH DTS), and a different throttle mechanism targeting memory/IO fabric domains.

**Classification:** Firmware-heavy (IMH Primecode thermal policy). IMH2 is NWP-specific — use NWP IMH2 HAS/MAS for all IMH-side thermal content, not DMR IMH1.

**Gating mechanism:** IMH thermal management is always enabled. Controlled by:
- **Fuses:** IMH temperature target, thermal action thresholds
- **Primecode:** PID throttle loop for IMH-die uncore domains
- **Cross-die messaging:** HPM thermal propagation between IMH and CBB

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| IMH count per socket | 1 (imh0 only) | NWP SOC topology — single IMH |
| IMH type | IMH2 (NWP-specific) | NWP HAS |
| Thermal FW owner | Primecode (IMH firmware) | NWP IMH SoC PM MAS |
| Cross-die transport | HPM thermal messages | NWP IMH SoC PM MAS |
| Spec backing | NWP IMH thermal behavior (nwp_imh_soc_pm_mas) | Co-Design T2 |

### TCDs Under This TPF

| TCD ID | Title | Action |
|---|---|---|
| [22022420596](https://hsdes.intel.com/appstore/article-one/#/22022420596) | IMH Thermal Management | Reparent from 16030763139 |
| NEW | Cross-Die Thermal Propagation | New TCD (Co-Design N1) |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:16px;font-family:Arial,sans-serif;max-width:640px">
  <div style="font-weight:700;font-size:13px;text-align:center;margin-bottom:12px;border-bottom:2px solid #333;padding-bottom:8px">IMH Thermal Control — Full-Stack Architecture</div>
  <div style="background:#4472C4;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 4: OS / Tool</strong> — TPMI read, PythonSV thermal register inspection</div>
  <div style="background:#ED7D31;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 3: BIOS / Init</strong> — IMH temperature target, thermal action threshold programming</div>
  <div style="background:#A020F0;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 2: IMH Primecode</strong> — PID throttle loop, cold action, disable path, cross-die HPM thermal messages</div>
  <div style="background:#70AD47;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 1: Silicon HW</strong> — IMH DTS sensors, FIVR enforcement, D2D UCIe PHY (HPM transport)</div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | Notes |
|---|---|---|---|---|---|---|
| Layer 4: OS / Tool | ❌ | ❌ | ❌ | ✅ | ✅ | |
| Layer 3: BIOS / Init | ✅ | ❌ | ❌ | ✅ | ✅ | |
| Layer 2: IMH Primecode | ✅ | ✅ | ✅ | ✅ | indirect | HSLE: IMH-only; XOS: cross-die HPM |
| Layer 1: Silicon HW | ❌ | ✅ | ✅ | ✅ | indirect | |

---

## Section 3: Validation Strategy

Cross-die thermal propagation (IMH↔CBB HPM messages) requires **XOS** environment — single-die HSLE is insufficient.
IMH-local PID throttle can be validated on single-die HSLE (IMH2 alone).

---

## Section 4: Tier Coverage

*To be populated after TCD enrichment.*

---

## Section 5: Risks & Dependencies

- NWP single-IMH topology (imh0 only) — no multi-IMH corner cases needed
- Cross-die HPM thermal message latency depends on D2D UCIe link state
- IMH2 is NWP-specific — DMR IMH1 thermal behavior does NOT apply

---

## Section 6: DFX Considerations

- IMH thermal status via TPMI/Primecode debug trace
- Cross-die HPM message logging for thermal propagation debug

---

## Section 7: Common Corner Cases

- IMH PID throttle + CBB PID throttle active simultaneously
- Cold action path — IMH below minimum operating temperature
- Cross-die thermal message lost during D2D link transition

---

## Section 8: TCD Coverage Summary & References

| TCD ID | Title | Status | TC Count |
|---|---|---|---|
| 22022420596 | IMH Thermal Management | Reparent pending | 3 |
| NEW | Cross-Die Thermal Propagation | Scaffold pending | TBD |
