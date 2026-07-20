# TPF 16030763141 — [NWP PM] Thermal Reporting/Telemetry (SPLIT)

| Field | Value |
|-------|-------|
| **TPF ID** | [16030763141](https://hsdes.intel.com/appstore/article-one/#/16030763141) |
| **Title** | [NWP PM] Thermal Reporting/Telemetry |
| **Parent TP** | [16030763137 — NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Status** | SPLIT — superseded by 2 child TPFs |
| **KB last updated** | 2026-07-19 |

---

## Section 1: Feature Classification & Introduction

**This TPF has been split** into 2 more focused TPFs during the Thermal Management T2 restructuring (2026-07-19). The split separates sensor/measurement infrastructure from architectural reporting interfaces.

**Do not add new TCDs to this TPF.** Use the target TPFs below.

### Successor TPFs

| TPF ID | Title | Scope | TCDs |
|---|---|---|---|
| [16031170067](https://hsdes.intel.com/appstore/article-one/#/16031170067) | Thermal Sensors & DTS Telemetry | DTS sensor inventory, readings, dielet telemetry (CBB + IMH) | 2 (CBB DTS, IMH DTS) |
| [16031170068](https://hsdes.intel.com/appstore/article-one/#/16031170068) | Thermal Status / Reporting Interfaces | Thermal status, interrupts, TPMI/PMT reporting, MCAs | 4 (Thermal Reporting, Interrupts, MCAs, TPMI Migration) |

---

## Section 2: Design Details

See successor TPFs for architecture diagrams and full-stack cross-layer views.

---

## Section 3: Validation Strategy

Validation is now distributed across the 2 successor TPFs. This TPF retains no active validation scope.

---

## Section 8: TCD Coverage Summary & References

All TCDs have been reparented to successor TPFs. No active children remain.
