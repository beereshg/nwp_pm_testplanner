# TCD: ITD-SCENARIO-001 - ITD and PkgC6 Interaction [ZBB]

| Field | Value |
|-------|-------|
| **TCD ID** | [16031179491](https://hsdes.intel.com/appstore/article-one/#/16031179491) |
| **Title** | ITD-SCENARIO-001 - ITD and PkgC6 Interaction [ZBB] |
| **Status** | rejected |
| **Parent TPF** | [16031170066 — ITD Compensation](https://hsdes.intel.com/appstore/article-one/#/16031170066) |
| **Feature** | ITD Compensation |
| **Sub-Feature** | PkgC6 Interaction |
| **NWP Disposition** | ZBB — PkgC6 is ZBB on NWP |
| **KB last updated** | 2026-07-21 |
| **Spec refs** | Wave3_common Socket Thermal Mgmt HAS (PkgC x ITD) |

---

## Definition Block

- **Layer:** 3 (Scenario)
- **Sentence:** ITD is inactive during PkgC6; exit voltages are programmed correctly for wake; no hang on ITD request during PkgC entry.
- **Gate:** ITD-CONTRACT-002 (Core/Ring Domain Compensation)
- **Suspect:** PkgC entry FSM ITD quiesce; PkgC exit voltage restore
- **Setup:** ITD enabled on core/ring domains. PkgC6 entry conditions met.
- **Check:** Enter PkgC6 → verify ITD inactive. Exit PkgC6 → verify ITD resumes with correct voltage.
- **Invariant:** During PkgC6: ITD compensation = 0. On exit: voltage matches ITD algorithm for current temp within 1 RAPL cycle. No hang during PkgC entry when ITD request is in flight.

---

## Section 1: Architecture / Micro-architecture and Functionality

**ITD and PkgC6 Interaction** validates that ITD compensation is correctly quiesced during PkgC6 and restored on exit. This is a cross-domain coordination scenario between the PkgC FSM and the ITD compensation engine.

> **Architecture overview:** See TPF — ITD Compensation §Design Details.

**ZBB on NWP:** PkgC6 is Zero Bug Bounce on NWP. This TCD and all child TCs are rejected. Retained for lineage tracking and future un-ZBB.

### Key Behavioral Facts (from DMR/GNR spec)

- ITD should be inactive during PkgC6 (all domains powered down)
- Exit workpoint voltages must include ITD compensation for safe wake
- GNR sighting: Fabric ITD request while entering PkgC caused hang when UCIe PHY in Qstop state
- PkgC exit must resume ITD with correct temperature-based compensation

---

## Section 2: Functional Requirements / Spec Refs

| FR ID | Requirement | Spec ref |
|---|---|---|
| FR1 | ITD inactive during PkgC6 | Wave3_common Socket Thermal Mgmt HAS |
| FR2 | PkgC6 exit voltages include ITD compensation | Wave3_common Socket Thermal Mgmt HAS |
| FR3 | No hang on ITD request during PkgC entry | GNR sighting (bug push) |

---

## Section 5: Pass/Fail Bar

| Bar | Measurable criterion | Spec ref |
|---|---|---|
| PkgC6 ITD inactive | During PkgC6: ITD compensation = 0 across all domains | Wave3_common |
| PkgC6 exit restore | On PkgC6 exit: VID reflects ITD for current temp within 1 RAPL cycle | Wave3_common |
| No hang | PkgC entry with active ITD request: no system hang | GNR sighting |

**Status: ALL BARS ZBB on NWP — PkgC6 is not POR.**

---

## Section 6: Corner Cases / Coverage

| Scenario | TC ID | Env | Verdict |
|---|---|---|---|
| ~~PkgC6 entry with active ITD~~ | ~~[22022421526](https://hsdes.intel.com/appstore/article-one/#/22022421526)~~ | ~~FV~~ | **ZBB — rejected** |
| ~~PkgC6 entry ITD (emulation)~~ | ~~[22022421527](https://hsdes.intel.com/appstore/article-one/#/22022421527)~~ | ~~HSLE~~ | **ZBB — rejected** |

---

## Section 8: Open Items

- If PkgC6 is un-ZBB'd on NWP, reactivate this TCD and child TCs
- Review GNR sighting for applicability to NWP UCIe PHY topology
