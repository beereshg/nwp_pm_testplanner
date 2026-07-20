# TPF NEW — Thermal GPIO & External Events

| Field | Value |
|-------|-------|
| **TPF ID** | [16031170064](https://hsdes.intel.com/appstore/article-one/#/16031170064) |
| **Title** | [NWP PM] Thermal GPIO & External Events |
| **Parent TP** | [16030763137 — NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Split from** | [16030763139 — Socket Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763139) |
| **KB last updated** | 2026-07-19 |
| **Co-Design T2 ref** | Ingest tracker §1A row A3 |

---

## Section 1: Feature Classification & Introduction

**Thermal GPIO & External Events** covers the externally visible thermal signal semantics and event-driven throttle responses on NWP. These are the platform boundary signals — PROCHOT_N, MEMHOT_IN/OUT, MEMTRIP_N, THERMTRIP_N — that bridge internal thermal detection to external platform actions. Each signal has distinct direction, latency requirements, and fuse-gated enable behavior per the Newport NIO GPIO HAS.

**Classification:** Silicon-heavy with firmware response. GPIO bump hardware is silicon; PCode/Primecode implements the thermal response policy upon signal assertion/deassertion.

**Gating mechanism:**
- **Fuses:** `PTPCFSMS_GPIO_BUMP_ENABLES_ENABLE_XX*_FUSE` per signal
- **PCode:** Frequency clamp on PROCHOT assertion; MC throttle on MEMHOT_IN
- **Hardware:** Wire-OR for THERMTRIP, bidirectional for cross-die sensing

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| PROCHOT_N direction | Input only (output mode removed on NWP) | NWP GPIO HAS |
| MEMHOT_IN throttle latency | Within 100 us | NWP GPIO HAS |
| THERMTRIP_N | Bidirectional, wire-OR across dice | NWP GPIO HAS |
| Bump fuse control | Per-signal enable/disable via PTPCFSMS | NWP GPIO HAS |
| Spec backing | NWP GPIO thermal signal sections + IMH thermal behavior table | Co-Design T2 |

### TCDs Under This TPF

| TCD ID | Title | Action |
|---|---|---|
| NEW | PROCHOT_N Interface | Split from 22022420589 GPIO Interface |
| NEW | MEMHOT IN/OUT Interface | Split from 22022420589 GPIO Interface |
| NEW | MEMTRIP/THERMTRIP Package Signaling | Split from 22022420589 GPIO Interface |
| [22022420609](https://hsdes.intel.com/appstore/article-one/#/22022420609) | Prochot Flow | Reparent from 16030763139 |
| [22022420628](https://hsdes.intel.com/appstore/article-one/#/22022420628) | VR Hot | Reparent from 16030763139 |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:16px;font-family:Arial,sans-serif;max-width:640px">
  <div style="font-weight:700;font-size:13px;text-align:center;margin-bottom:12px;border-bottom:2px solid #333;padding-bottom:8px">Thermal GPIO & External Events — Full-Stack Architecture</div>
  <div style="background:#4472C4;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 5: Platform / BMC</strong> — External thermal event sources: VR, PCIe card, DIMM, BMC fan control</div>
  <div style="background:#2F5496;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 4: GPIO Bump HW</strong> — NIO GPIO pads, bump fuse enables (PTPCFSMS), direction control, wire-OR logic</div>
  <div style="background:#ED7D31;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 3: PCode / Primecode Response</strong> — PROCHOT freq clamp, MEMHOT MC throttle, VR_HOT PLR, THERMTRIP HWRS</div>
  <div style="background:#A020F0;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 2: Thermal Status</strong> — TPMI/MSR status bits reflecting active thermal events</div>
  <div style="background:#70AD47;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 1: Recovery / Deassertion</strong> — Signal deassertion detection, recovery path, hysteresis</div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | Notes |
|---|---|---|---|---|---|---|
| Layer 5: Platform / BMC | ❌ | ❌ | ❌ | ✅ | ✅ | Real platform signals; FV via PythonSV GPIO injection |
| Layer 4: GPIO Bump HW | ❌ | ✅ | ✅ | ✅ | indirect | RTL bump logic |
| Layer 3: PCode / Primecode Response | ✅ | ✅ | ✅ | ✅ | indirect | VP: firmware policy; HSLE/XOS: enforcement |
| Layer 2: Thermal Status | ✅ | ✅ | ✅ | ✅ | ✅ | All tiers read status |
| Layer 1: Recovery / Deassertion | ❌ | ✅ | ✅ | ✅ | ✅ | Timing-sensitive recovery paths |

---

## Section 3: Validation Strategy

GPIO signal injection requires FV or HSLE with pin-level control. VP (Simics) can model firmware response to injected events but not real GPIO electrical behavior.

Key strategy:
- **Signal assertion/deassertion timing:** Silicon-only (absolute timing) or HSLE (relative ordering)
- **Firmware response correctness:** VP validates policy, FV validates enforcement
- **Fuse gating:** FV/HSLE validates bump enable/disable

---

## Section 4: Tier Coverage

*To be populated after TCD enrichment.*

---

## Section 5: Risks & Dependencies

- PROCHOT_N is input-only on NWP (output mode removed) — DMR tests using PROCHOT output need adaptation
- GPIO bump fuse enables must be set before signal testing
- THERMTRIP wire-OR requires multi-die topology (XOS or silicon)

---

## Section 6: DFX Considerations

- GPIO thermal status via TPMI / PLR registers
- PythonSV GPIO injection for FV-tier signal assertion

---

## Section 7: Common Corner Cases

- PROCHOT + VR_HOT asserted simultaneously — verify priority/stacking
- MEMHOT_IN during RAPL PL1 active — verify lower bound wins
- THERMTRIP assertion during active workload — clean shutdown sequence
- Fuse-disabled signal assertion — verify no response

---

## Section 8: TCD Coverage Summary & References

| TCD ID | Title | Status | TC Count |
|---|---|---|---|
| NEW | PROCHOT_N Interface | Scaffold pending (split from 22022420589) | TBD |
| NEW | MEMHOT IN/OUT Interface | Scaffold pending (split from 22022420589) | TBD |
| NEW | MEMTRIP/THERMTRIP Package Signaling | Scaffold pending (split from 22022420589) | TBD |
| 22022420609 | Prochot Flow | Reparent pending | 5 |
| 22022420628 | VR Hot | Reparent pending | 5 |
