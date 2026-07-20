# TCD: CBB PM EndPoint Sweep

| Field | Value |
|-------|-------|
| **TCD ID** | [16031172974](https://hsdes.intel.com/appstore/article-one/#/16031172974) |
| **Title** | CBB PM EndPoint Sweep |
| **Status** | open |
| **Owner** | thangama |
| **Parent TPF** | [22022562325](https://hsdes.intel.com/appstore/article-one/#/22022562325) |
| **Parent TP** | [16030765631 - PM Cross Product](https://hsdes.intel.com/appstore/article-one/#/16030765631) |
| **KB last updated** | 2026-07-20 |
| **Feature** | Power / PM Sideband - CBB GPSB/PMSB endpoint accessibility |

## Section 1: Architecture / Micro-architecture and Functionality

Validates that all PM sideband endpoints on the CBB die are accessible and respond correctly. Exercises GPSB and PMSB endpoint sweeps on the CBB side, verifying correct port ID mapping and response for all CBB PM agents (PUNIT, compute modules, base components).

> **Architecture overview:** See [TPF 22022562325](https://hsdes.intel.com/appstore/article-one/#/22022562325) Section 2

### NWP-Specific Deltas

- NWP has 2 CBBs with same PantherCove (PNC) core as DMR-SP
- CBB sideband topology follows DMR-SP CBB HAS
- Each CBB has 4 compute clusters x 8 modules = 32 modules per CBB

### TC Coverage Map

| TC | Scope | Environment |
|----|-------|-------------|
| [22022423121](https://hsdes.intel.com/appstore/article-one/#/22022423121) | CBB GPSB end point sweep | FV (silicon) |
| [22022423122](https://hsdes.intel.com/appstore/article-one/#/22022423122) | CBB PMSB end point sweep | FV (silicon) |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Role |
|-----------|----------------|------|
| GPSB | Port ID remap table (CBB) | Endpoint addressing |
| PMSB | Port ID remap table (CBB) | PM message routing |
| CSR | CBB sideband config | Endpoint configuration |
| PUNIT | CBB PM agents | Endpoint consumers |

---

## Section 3: Reset, Power, and Clocking

- CBB endpoints accessible after platform boot
- GPSB/PMSB remap tables programmed by PCode during reset exit
- CBB has its own sideband domain separate from iMH

---

## Section 4: Programming Model

CBB sideband endpoints addressed via port IDs. Sweep iterates all valid GPSB and PMSB entries on CBB die. CBB sideband is independent of iMH sideband - separate remap tables and topology.

---

## Section 5: Operational Behavior

### Pass/Fail Bar

| Criterion | Measurable Threshold | Spec Basis |
|-----------|---------------------|-----------|
| All valid endpoints accessible | Every non-INVALID remap entry responds | CBB sideband architecture |
| No timeout | No endpoint read times out | Architecture invariant |
| No corruption | Response data matches expected state | Endpoint register spec |

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| INVALID remap entry | Should not respond | Covered by sweep | No action |
| Module in C6 during sweep | Endpoint may be clock-gated | Verify wakeup behavior | Low risk |

---

## Section 7: Security / Safety / Policy

- Only trusted agents access CBB PM endpoints
- Validation interface inherently privileged

---

## Section 8: References

- [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/has/cbb overview/dmr_cbb_power_management.html) - CBB sideband
- [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/soc_pm_has/dmr_soc_pm_has.html) - GPSB/PMSB
