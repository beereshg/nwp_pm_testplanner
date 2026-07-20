# TPF 16031170078 — [NWP PM] DDRIO Temperature Compensation

| Field | Value |
|-------|-------|
| **TPF ID** | [16031170078](https://hsdes.intel.com/appstore/article-one/#/16031170078) |
| **Title** | [NWP PM] DDRIO Temperature Compensation |
| **Parent TP** | [16030763137 — NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Split from** | [16030763140 — Memory Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763140) |
| **KB last updated** | 2026-07-19 |
| **Co-Design finding** | Architecturally separate from MTM (CLTT/Memhot/Memtrip). Owned by DDRIO PHY/Memory IO team. Fully independent CRI registers and RC firmware. |

---

## Section 1: Feature Classification & Introduction

**DDRIO Temperature Compensation** addresses the reliability concern that higher DDR speeds require ongoing temperature compensation for DDRIO analog circuits. These circuits are trained during MRC (Memory Reference Code) at boot, but temperature drift after training moves the link away from optimal settings. The platform uses an ongoing RC-driven mechanism to keep DDRIO settings aligned with thermal conditions without full link retraining.

**Classification:** Silicon-heavy (DDRIO PHY analog + RC firmware). Architecturally separate from Memory Thermal Management (CLTT/Memhot/Memtrip) — different spec owner (DDRIO PHY team), different registers (CRI temp-code registers), different firmware agent (RC, not PCode/Primecode thermal policy).

**Gating mechanism:**
- **RC strap:** Push rate is strap-configurable; RC pushes DDRIO temp at the same rate as DTS → PUnit
- **CRI registers:** 2 temp-code registers added on CRI to receive temperature code from RC
- **NWP delta:** Single thermal diode per CBB (replacing multiple diodes in DMR)

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| Memory technology | LPDDR6 PHY/MC | NWP SOC |
| Thermal diodes per CBB | 1 (NWP-specific; DMR has multiple) | NWP Memory IO Stack MAS |
| CRI temp-code registers | 2 per DDRIO | NWP DDRIO MAS |
| Push rate | Strap-configurable; same rate as DTS → PUnit | DDRIO MAS |
| Spec owner | DDRIO PHY / Memory IO team | Co-Design T2 finding |
| Spec section | NWP Memory IO (DDRIO) Stack MAS: DDRIO Comp registers | Co-Design |

### TCDs Under This TPF

| TCD ID | Title | Action |
|---|---|---|
| [22022420567](https://hsdes.intel.com/appstore/article-one/#/22022420567) | DDRIO Temperature Compensation | Reparent from 16030763140 |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:16px;font-family:Arial,sans-serif;max-width:640px">
  <div style="font-weight:700;font-size:13px;text-align:center;margin-bottom:12px;border-bottom:2px solid #333;padding-bottom:8px">DDRIO Temperature Compensation — Full-Stack Architecture</div>
  <div style="background:#4472C4;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 4: MRC Boot Training</strong> — Initial DDRIO analog calibration at boot time</div>
  <div style="background:#ED7D31;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 3: Thermal Diodes / DTS</strong> — DDRIO-associated thermal sources provide temperature code</div>
  <div style="background:#A020F0;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 2: RC (Rate Controller)</strong> — Periodic DTS pull via RA DTS path → push to CRI via RA PLL path</div>
  <div style="background:#70AD47;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 1: DDRIO CRI / Analog</strong> — CRI temp-code registers (x2) receive compensation; analog circuits apply drift correction</div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | Notes |
|---|---|---|---|---|---|---|
| Layer 4: MRC Boot Training | ✅ | ✅ | ✅ | ✅ | ✅ | All tiers boot |
| Layer 3: Thermal Diodes / DTS | ❌ | ✅ | ✅ | ✅ | ✅ | Analog diodes = silicon; HSLE: RTL readout |
| Layer 2: RC (Rate Controller) | ❌ | ✅ | ✅ | ✅ | indirect | RTL RC FSM |
| Layer 1: DDRIO CRI / Analog | ❌ | ✅ | ✅ | ✅ | indirect | RTL CRI registers; analog = silicon only |

---

## Section 3: Validation Strategy

Key strategy:
- **RC push mechanism:** HSLE validates RTL RC → CRI path; FV validates on silicon
- **Compensation accuracy:** Inject temperature change, verify CRI register update and analog drift correction
- **NWP single-diode behavior:** Validate single thermal diode per CBB (vs DMR multi-diode)

---

## Section 4: Tier Coverage

*To be populated after TCD enrichment.*

---

## Section 5: Risks & Dependencies

- Analog compensation accuracy is silicon-only — pre-Si covers digital path only
- NWP single-diode per CBB differs from DMR — adaptation required for multi-diode DMR tests
- No shared registers with CLTT/Memhot — fully independent failure modes

---

## Section 6: DFX Considerations

- TPMI / PMSB for DTS readings and compensation visibility
- CRI register readback for temperature code verification

---

## Section 7: Common Corner Cases

- Rapid temperature change after MRC training — RC push rate vs thermal transient
- Maximum/minimum temperature code at CRI boundaries
- Single thermal diode failure — compensation behavior on invalid reading

---

## Section 8: TCD Coverage Summary & References

| TCD ID | Title | Status | TC Count |
|---|---|---|---|
| 22022420567 | DDRIO Temperature Compensation | Reparented | 1 |
