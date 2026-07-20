# TPF NEW — Thermal Status/Reporting Interfaces

| Field | Value |
|-------|-------|
| **TPF ID** | [16031170068](https://hsdes.intel.com/appstore/article-one/#/16031170068) |
| **Title** | [NWP PM] Thermal Status / Reporting Interfaces |
| **Parent TP** | [16030763137 — NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Split from** | [16030763141 — Thermal Reporting/Telemetry](https://hsdes.intel.com/appstore/article-one/#/16030763141) |
| **KB last updated** | 2026-07-19 |
| **Co-Design T2 ref** | Ingest tracker §1C row C2 |

---

## Section 1: Feature Classification & Introduction

**Thermal Status / Reporting Interfaces** covers the architectural thermal status readback, threshold programming, thermal interrupts, and TPMI/PMT reporting interfaces on NWP. This is the **consumer/interface layer** — how thermal state is exposed to OS, tools, and firmware for monitoring and event notification. Distinct from the sensor/telemetry infrastructure (what is measured) and from thermal control (what action is taken).

**Classification:** Firmware + Architecture interface. Register/MSR/TPMI definitions are architectural; interrupt delivery and threshold comparison are firmware-configured with hardware enforcement.

**Key NWP delta:** TPMI replaces deprecated MSRs for several thermal reporting paths. Validate that NWP TPMI paths are functional and that deprecated MSR paths behave correctly (expected values or #GP).

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| Reporting interfaces | TPMI, MSR (legacy/compat), PMT | NWP HAS + TPMI transition refs |
| Thermal interrupts | Per-core threshold crossing, package-level | DMR thermal spec |
| MCA on invalid temp | DIE TOO HOT (>135C) | DMR thermal flows |
| TPMI migration | Replaces deprecated MSRs for thermal status | NWP HAS |
| Spec backing | DMR thermal interrupt/reporting + TPMI transition refs | Co-Design T2 |

### TCDs Under This TPF

| TCD ID | Title | Action |
|---|---|---|
| [22022420619](https://hsdes.intel.com/appstore/article-one/#/22022420619) | Thermal Reporting | Keep (reparent from 16030763141) |
| [22022420616](https://hsdes.intel.com/appstore/article-one/#/22022420616) | Thermal Interrupts | Reparent from 16030763139 |
| [22022420606](https://hsdes.intel.com/appstore/article-one/#/22022420606) | MCAs | Reparent from 16030763139 |
| NEW | TPMI Thermal Reporting Migration | New TCD (Co-Design N3) |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:16px;font-family:Arial,sans-serif;max-width:640px">
  <div style="font-weight:700;font-size:13px;text-align:center;margin-bottom:12px;border-bottom:2px solid #333;padding-bottom:8px">Thermal Status / Reporting Interfaces — Full-Stack Architecture</div>
  <div style="background:#4472C4;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 5: OS / Driver</strong> — Thermal zone driver, APCI thermal, sysfs thermal readback, perf counters</div>
  <div style="background:#2F5496;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 4: TPMI / MSR Interface</strong> — TPMI thermal status registers, legacy MSR compatibility, PMT counters</div>
  <div style="background:#ED7D31;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 3: Threshold / Interrupt Logic</strong> — Per-core threshold crossing detection, interrupt delivery, package thermal status</div>
  <div style="background:#A020F0;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 2: Firmware MCA</strong> — DIE TOO HOT MCA on invalid temperature (>135C), reason bit encoding</div>
  <div style="background:#70AD47;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 1: HW Status</strong> — Tcontrol margin, thermal monitor filtering, constrained-time counters</div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | Notes |
|---|---|---|---|---|---|---|
| Layer 5: OS / Driver | ❌ | ❌ | ❌ | ❌ | ✅ | Requires booted OS |
| Layer 4: TPMI / MSR Interface | ✅ | ✅ | ✅ | ✅ | ✅ | All tiers validate register access |
| Layer 3: Threshold / Interrupt Logic | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Layer 2: Firmware MCA | ✅ | ✅ | ✅ | ✅ | ❌ | MCA is destructive on PV |
| Layer 1: HW Status | ❌ | ✅ | ✅ | ✅ | indirect | |

---

## Section 3: Validation Strategy

- **TPMI migration:** Validate new TPMI paths + deprecated MSR behavior
- **Thermal interrupts:** Inject threshold crossing, verify interrupt delivery to OS/handler
- **MCA:** Inject invalid temperature (>135C), verify DIE TOO HOT MCA fires
- **Reporting accuracy:** Compare reported values vs injected/known temperatures

---

## Section 4: Tier Coverage

*To be populated after TCD enrichment.*

---

## Section 5: Risks & Dependencies

- TPMI migration may leave deprecated MSR paths partially functional — need explicit coverage
- Thermal interrupt delivery depends on APIC/OS configuration
- DIE TOO HOT MCA is destructive — requires controlled test environment

---

## Section 6: DFX Considerations

- TPMI thermal registers for status readback
- MCA bank dump for DIE TOO HOT decode
- Thermal interrupt log for delivery verification

---

## Section 7: Common Corner Cases

- TPMI read vs deprecated MSR read — same temperature, different paths
- Multiple threshold crossings in rapid succession — interrupt coalescing
- MCA at exactly 135C boundary — edge case for trip condition
- Constrained-time counter overflow handling

---

## Section 8: TCD Coverage Summary & References

| TCD ID | Title | Status | TC Count |
|---|---|---|---|
| 22022420619 | Thermal Reporting | Reparent pending | 11 |
| 22022420616 | Thermal Interrupts | Reparent pending | 9 |
| 22022420606 | MCAs | Reparent pending | 1 |
| NEW | TPMI Thermal Reporting Migration | Scaffold pending | TBD |
