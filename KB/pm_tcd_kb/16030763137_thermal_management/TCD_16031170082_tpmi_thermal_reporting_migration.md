# TCD: [Thermal Reporting] TPMI Thermal Reporting Migration

| Field | Value |
|-------|-------|
| **TCD ID** | [16031170082](https://hsdes.intel.com/appstore/article-one/#/16031170082) |
| **Title** | [Thermal Reporting] TPMI Thermal Reporting Migration |
| **Status** | draft |
| **Parent TPF** | [16031170068 — Thermal Status/Reporting Interfaces](https://hsdes.intel.com/appstore/article-one/#/16031170068) |
| **Feature** | Thermal Reporting |
| **Sub-Feature** | MSR → TPMI migration for thermal status/control registers |
| **NWP Disposition** | New |
| **KB last updated** | 2026-07-19 |
| **Co-Design ref** | Ingest tracker N3; Co-Design TPMI thermal migration query 2026-07-19 |
| **Spec refs** | NWP TPMI HAS/LUT tables; DMR/GNR MSR deprecation guidance |

---

## Section 1: Architecture / Micro-architecture and Functionality

**TPMI Thermal Reporting Migration** validates that NWP thermal status and reporting registers have correctly migrated from legacy MSRs to TPMI MMIO equivalents, and that deprecated MSR paths behave as specified (reads return 0, writes ignored).

> **Architecture overview:** See TPF — Thermal Status/Reporting Interfaces §Design Details.

### Deprecated MSRs and TPMI Replacements (from Co-Design spec query)

| Deprecated MSR | Address | TPMI Replacement | Read behavior |
|---|---|---|---|
| IA32_THERM_STATUS | 0x19C | TPMI_THERM_STATUS | Returns 0 |
| IA32_THERM_INTERRUPT | 0x19B | TPMI_THERM_INTERRUPT | Returns 0 |
| IA32_THERM_CONTROL | 0x19A | IA32_CLOCK_MODULATION (renamed) | Returns 0 |
| TEMPERATURE_TARGET | 0x1A2 | TPMI_TEMPERATURE_TARGET | Returns 0 |
| PACKAGE_THERM_STATUS | 0x1B1 | TPMI_PACKAGE_THERM_STATUS | Returns 0 |
| PACKAGE_THERM_INTERRUPT | 0x1B2 | TPMI_PACKAGE_THERM_INTERRUPT | Returns 0 |
| MCP_THERMAL_REPORT_1 | 0x1A3 | TPMI_MCP_THERMAL_REPORT_1 | Returns 0 |
| MCP_THERMAL_REPORT_2 | 0x1A5 | TPMI_MCP_THERMAL_REPORT_2 | Returns 0 |

### Key Facts

- **Deprecated MSR reads return 0** (not #GP) — architectural guidance to avoid OS driver crashes
- **Deprecated MSR writes are ignored** — no effect
- **NWP adds TPMI-only fields:** DLCP PCT SST_TF_INFO registers, PMT telemetry aggregators (iMH PUNIT, D2D ULA & IO-CA)
- **PMT thermal counters:** NWP-specific PMT objects for thermal telemetry

---

## Section 2: Functional Requirements / Spec Refs

| FR ID | Requirement | Spec ref |
|---|---|---|
| FR1 | TPMI thermal registers return correct thermal status matching silicon state | NWP TPMI HAS/LUT |
| FR2 | Deprecated MSR reads return 0 (not #GP) | DMR/GNR MSR deprecation guidance |
| FR3 | Deprecated MSR writes are ignored (no effect) | DMR/GNR MSR deprecation guidance |
| FR4 | TPMI-only fields (DLCP PCT, PMT aggregators) are functional | NWP TPMI HAS |
| FR5 | PMT thermal counters increment correctly | NWP PMT spec |

---

## Section 5: Pass/Fail Bar

| Bar | Measurable criterion | Spec ref |
|---|---|---|
| TPMI functional | TPMI_THERM_STATUS reflects current thermal state (temp, threshold status); matches DTS reading | NWP TPMI HAS |
| TPMI write-read | Write to TPMI thermal threshold → read back matches → interrupt fires on threshold crossing | NWP TPMI HAS |
| Deprecated MSR read | Read IA32_THERM_STATUS (0x19C) → returns 0x0 (no #GP) | MSR deprecation guidance |
| Deprecated MSR write | Write to 0x19C → no effect; TPMI register unchanged | MSR deprecation guidance |
| TPMI-only fields | SST_TF_INFO TPMI registers readable with valid data | NWP TPMI HAS |
| PMT counters | PMT thermal telemetry counters increment under thermal load | NWP PMT spec |

---

## Section 6: Corner Cases / Coverage

| Scenario | TC ID | Env | Verdict |
|---|---|---|---|
| TPMI_THERM_STATUS readback vs DTS | TBD | FV, VP | |
| TPMI threshold write + interrupt delivery | TBD | FV | |
| Deprecated MSR 0x19C read → 0 | TBD | FV, VP | |
| Deprecated MSR 0x19C write → no effect | TBD | FV, VP | |
| All 8 deprecated MSRs return 0 | TBD | FV | |
| TPMI-only DLCP PCT registers readable | TBD | FV | |
| PMT thermal counter increment under load | TBD | FV | |
| TPMI register access during thermal event | TBD | FV | |

---

## Section 8: Open Items

- Confirm exact TPMI register offsets from NWP TPMI LUT
- Verify OS thermal zone driver compatibility with TPMI path (PV scope?)
- Check if any deprecated MSR returns non-zero on specific steppings
