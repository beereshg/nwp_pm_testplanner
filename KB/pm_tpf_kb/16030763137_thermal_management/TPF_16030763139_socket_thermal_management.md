# TPF 16030763139 — [NWP PM] Socket Thermal Management (SPLIT)

| Field | Value |
|-------|-------|
| **TPF ID** | [16030763139](https://hsdes.intel.com/appstore/article-one/#/16030763139) |
| **Title** | [NWP PM] Socket Thermal Management |
| **Parent TP** | [16030763137 — NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Status** | SPLIT — superseded by 5 child TPFs |
| **KB last updated** | 2026-07-19 |

---

## Section 1: Feature Classification & Introduction

**This TPF has been split** into 5 more focused TPFs during the Thermal Management T2 restructuring (2026-07-19). Each new TPF represents a distinct spec subsystem with a different IP owner or throttle mechanism.

**Do not add new TCDs to this TPF.** Use the target TPFs below.

### Successor TPFs

| TPF ID | Title | Scope | TCDs |
|---|---|---|---|
| [16031170062](https://hsdes.intel.com/appstore/article-one/#/16031170062) | Core/CBB Thermal Control | EMTTM core/CBB PID throttle (ACP + CBB) | 3 (ACP, CBB Thermal, Thermal x RAPL) |
| [16031170063](https://hsdes.intel.com/appstore/article-one/#/16031170063) | IMH Thermal Control | IMH2 PID throttle, cross-die propagation | 2 (IMH Thermal, Cross-Die) |
| [16031170064](https://hsdes.intel.com/appstore/article-one/#/16031170064) | Thermal GPIO & External Events | GPIO signals, PROCHOT, VR Hot | 5 (3 GPIO splits, Prochot, VR Hot) |
| [16031170065](https://hsdes.intel.com/appstore/article-one/#/16031170065) | Thermtrip / Catastrophic Shutdown | DTS chain, HWRS shutdown | 1 (Thermtrip) |
| [16031170066](https://hsdes.intel.com/appstore/article-one/#/16031170066) | ITD Compensation | Voltage-temp compensation per rail group | 4 (Core/Ring, Fabric/IO, Memory/CFC, Common) |

### Remaining Child

| TCD ID | Title | Notes |
|---|---|---|
| [22022420589](https://hsdes.intel.com/appstore/article-one/#/22022420589) | GPIO Interface | **Legacy stub** — 5 of 6 TCs moved to GPIO split TCDs under TPF 16031170064. 1 TC remains (fuse checkout spanning all signals). Consider moving to 16031170064 or closing. |

---

## Section 2: Design Details

See successor TPFs for architecture diagrams and full-stack cross-layer views.

---

## Section 3: Validation Strategy

Validation is now distributed across the 5 successor TPFs. This TPF retains no active validation scope.

---

## Section 8: TCD Coverage Summary & References

All active TCDs have been reparented to successor TPFs. Only the GPIO Interface legacy stub remains.
