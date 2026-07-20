# TCD: [ITD] Common Controls

| Field | Value |
|-------|-------|
| **TCD ID** | [16031170075](https://hsdes.intel.com/appstore/article-one/#/16031170075) |
| **Title** | [ITD] Common Controls |
| **Status** | draft |
| **Parent TPF** | [16031170066 — ITD Compensation](https://hsdes.intel.com/appstore/article-one/#/16031170066) |
| **Split from** | [22022420603 — ITD](https://hsdes.intel.com/appstore/article-one/#/22022420603) |
| **Feature** | ITD Compensation |
| **Sub-Feature** | Common Controls (fuse checkout, enable/disable, reset-time, MIN_ACCURATE_TEMP) |
| **NWP Disposition** | Needs_Adaptation (PkgC6 TCs → ZBB on NWP) |
| **KB last updated** | 2026-07-19 |
| **Co-Design T2 ref** | Ingest tracker §3B row S7 |
| **Spec refs** | DMR thermal / ITD: Common control + reset-time behavior |

---

## Section 1: Architecture / Micro-architecture and Functionality

**ITD Common Controls** validates the cross-domain ITD control mechanisms: fuse coefficient checkout, global ITD enable/disable path, reset-time behavior (worst-case ITD during MB training), and the MIN_ACCURATE_TEMP guard condition. These are the shared control/safety mechanisms that apply across ALL ITD-capable domains.

> **Architecture overview:** See TPF — ITD Compensation §Design Details.

### Key Behavioral Facts

- **Fuse checkout:** `IMH_DOMAIN_ITD_SLOPE`, `ITD_CUTOFF_TJ`, `TRUE_TD_ENABLE`, `MIN_ACCURATE_TEMP` readable and match expected values
- **Disable path:** ITD disable → compensation zeroed across all domains
- **Reset-time behavior:** Before MB training = worst-case/safe ITD; during training = real-time ITD; after training = safe again until reset complete
- **MIN_ACCURATE_TEMP:** Guard — ITD compensation not applied below this temperature (unreliable DTS readings)

### NWP Delta — ZBB Items

- **PkgC6 interaction:** NWP has no PkgC6 (ZBB) — all PkgC6-related ITD TCs must be removed or marked ZBB_N/A

---

## Section 2: Functional Requirements / Spec Refs

| FR ID | Requirement | Spec ref |
|---|---|---|
| FR1 | Fuse coefficients readable and match expected values | DMR thermal / ITD fuse |
| FR2 | ITD disable → compensation zeroed across all domains | DMR thermal / ITD |
| FR3 | Reset-time: worst-case ITD before MB training | DMR thermal / ITD reset behavior |
| FR4 | Reset-time: real-time ITD during MB training | DMR thermal / ITD reset behavior |
| FR5 | MIN_ACCURATE_TEMP guard: no compensation below threshold | DMR thermal / ITD |
| FR6 | PkgC6 interaction | **ZBB on NWP — not applicable** |

---

## Section 5: Pass/Fail Bar

| Bar | Measurable criterion | Spec ref |
|---|---|---|
| Fuse checkout | All ITD fuse fields readable; values match platform-expected coefficients | DMR thermal / ITD fuse |
| Disable path | ITD disabled → no voltage compensation on any domain (VID at baseline) | DMR thermal / ITD |
| Reset-time worst-case | During boot before MB training: ITD at worst-case/safe values (not real-time) | DMR thermal / ITD |
| MIN_ACCURATE_TEMP | Below MIN_ACCURATE_TEMP: ITD compensation not applied; above: normal operation | DMR thermal / ITD |

---

## Section 6: Corner Cases / Coverage

| Scenario | TC ID | Env | Verdict |
|---|---|---|---|
| Fuse coefficient checkout (all domains) | TBD | FV, HSLE, VP | |
| ITD global disable → re-enable | TBD | FV, HSLE | |
| Reset-time: worst-case ITD during early boot | TBD | FV, HSLE, VP | |
| Reset-time: MB training exit → real-time ITD | TBD | FV, HSLE | |
| MIN_ACCURATE_TEMP boundary (at/below/above) | TBD | FV, HSLE | |
| ~~PkgC6 → ITD interaction~~ | ~~N/A~~ | ~~ZBB~~ | **ZBB on NWP** |

---

## Section 8: Open Items

- Map existing TCs from parent ITD TCD (22022420603) to this split
- Identify and tag PkgC6-related TCs for ZBB removal
- Confirm MIN_ACCURATE_TEMP threshold value for NWP
