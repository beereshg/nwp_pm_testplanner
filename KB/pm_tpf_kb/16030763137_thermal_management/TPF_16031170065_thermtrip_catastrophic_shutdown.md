# TPF NEW — Thermtrip/Catastrophic Shutdown

| Field | Value |
|-------|-------|
| **TPF ID** | [16031170065](https://hsdes.intel.com/appstore/article-one/#/16031170065) |
| **Title** | [NWP PM] Thermtrip / Catastrophic Shutdown |
| **Parent TP** | [16030763137 — NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Split from** | [16030763139 — Socket Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763139) |
| **KB last updated** | 2026-07-19 |
| **Co-Design T2 ref** | Ingest tracker §1A row A4 |

---

## Section 1: Feature Classification & Introduction

**Thermtrip / Catastrophic Shutdown** covers the last-resort thermal protection: hardware thermtrip chain detection, DTS daisy-chain propagation across dice, and catastrophic shutdown behavior. This is architecturally distinct from normal thermal throttling — thermtrip is a **non-recoverable** safety mechanism that triggers platform shutdown when temperature exceeds the absolute maximum safe operating limit.

**Classification:** Silicon-heavy. The thermtrip chain is hardware-driven (HWRS logic); firmware's role is limited to initial fuse configuration and monitoring. The DTS daisy-chain and THERMTRIP_N wire-OR are physical layer behaviors.

**Gating mechanism:**
- **Fuses:** Thermtrip enable, per-die trip thresholds
- **Hardware:** DTS daisy-chain across dielets, THERMTRIP_N wire-OR
- **Guard:** THERMTRIP_N assertion ignored until fuses downloaded AND first measurement valid

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| THERMTRIP_N direction | Bidirectional (wire-OR across dice) | NWP GPIO HAS |
| Guard condition | Ignore until fuses downloaded + first valid measurement | NWP GPIO HAS |
| DTS chain | Daisy-chain across IMH + CBB dielets | NWP IMH MAS 6.6 |
| Shutdown mechanism | HWRS catastrophic shutdown | NWP IMH MAS |
| Spec backing | NWP IMH MAS 6.6 + NWP GPIO THERMTRIP | Co-Design T2 |

### TCDs Under This TPF

| TCD ID | Title | Action |
|---|---|---|
| [22022420625](https://hsdes.intel.com/appstore/article-one/#/22022420625) | Thermtrip | Reparent from 16030763139 |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:16px;font-family:Arial,sans-serif;max-width:640px">
  <div style="font-weight:700;font-size:13px;text-align:center;margin-bottom:12px;border-bottom:2px solid #333;padding-bottom:8px">Thermtrip / Catastrophic Shutdown — Full-Stack Architecture</div>
  <div style="background:#c62828;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 4: Platform Response</strong> — BMC/VR shutdown sequence on THERMTRIP_N assertion</div>
  <div style="background:#ED7D31;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 3: HWRS Logic</strong> — Hardware Reset Sequence: catastrophic shutdown trigger, power sequencing</div>
  <div style="background:#A020F0;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 2: DTS Daisy-Chain</strong> — Temperature sensor chain across IMH + CBB dielets; propagation to THERMTRIP comparator</div>
  <div style="background:#70AD47;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 1: GPIO / Package</strong> — THERMTRIP_N wire-OR pad, fuse-gated trip enable, bidirectional cross-die sensing</div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | Notes |
|---|---|---|---|---|---|---|
| Layer 4: Platform Response | ❌ | ❌ | ❌ | ❌ | ✅ | Real platform power-down; destructive test |
| Layer 3: HWRS Logic | ❌ | ✅ | ✅ | ✅ | indirect | RTL HWRS state machine |
| Layer 2: DTS Daisy-Chain | ❌ | Partial | ✅ | ✅ | indirect | HSLE: single-die chain; XOS: cross-die |
| Layer 1: GPIO / Package | ❌ | ✅ | ✅ | ✅ | ✅ | |

---

## Section 3: Validation Strategy

Catastrophic shutdown is destructive — FV/HSLE tests must inject temperature above trip threshold and verify shutdown sequence initiates without destroying the part.

- **DTS daisy-chain verification:** XOS required for cross-die chain propagation
- **Fuse-gated enable/disable:** FV/HSLE validates bump enable/disable
- **Guard condition timing:** Verify THERMTRIP ignored before fuse download and first valid measurement

---

## Section 4: Tier Coverage

*To be populated after TCD enrichment.*

---

## Section 5: Risks & Dependencies

- Destructive test — cannot verify full platform shutdown on pre-Si without risk model
- DTS chain accuracy depends on Thermal Sensors & DTS Telemetry TPF coverage

---

## Section 6: DFX Considerations

- Thermtrip assertion is logged in PLR/crashlog before shutdown
- Post-mortem analysis via BMC event log

---

## Section 7: Common Corner Cases

- Thermtrip during PkgC idle state (PkgC6 is ZBB on NWP)
- Multiple dice trip simultaneously — wire-OR correctness
- Fuse-disabled trip — verify no shutdown assertion

---

## Section 8: TCD Coverage Summary & References

| TCD ID | Title | Status | TC Count |
|---|---|---|---|
| 22022420625 | Thermtrip | Reparent pending | 3 |
