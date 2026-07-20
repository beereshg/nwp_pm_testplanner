# TCD: iMH PM EndPoint Sweep

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421311](https://hsdes.intel.com/appstore/article-one/#/22022421311) |
| **Title** | iMH PM EndPoint Sweep |
| **Status** | open |
| **Owner** | thangama |
| **Parent TPF** | [22022562325](https://hsdes.intel.com/appstore/article-one/#/22022562325) |
| **Parent TP** | [16030765631 - PM Cross Product](https://hsdes.intel.com/appstore/article-one/#/16030765631) |
| **KB last updated** | 2026-07-20 |
| **Feature** | Power / PM Sideband - iMH GPSB/PMSB endpoint accessibility |

## Section 1: Architecture / Micro-architecture and Functionality

Validates that all PM sideband endpoints on the iMH (IMH2) die are accessible and respond correctly. GPSB (General Purpose Sideband) and PMSB (Power Management Sideband) are two sideband fabrics used for PM control messaging. Endpoint sweeps read/write all configured endpoints to verify connectivity, correct port ID mapping, and response during normal operation.

> **Architecture overview:** See [TPF 22022562325](https://hsdes.intel.com/appstore/article-one/#/22022562325) Section 2

### NWP-Specific Deltas

- NWP IMH2 has different remap table entries than DMR IMH1
- NWP GPSB: 24 entries (vs DMR 32); PMSB: 8 entries (vs DMR 16)
- Two additional GPSB endpoints added for extra ULA instances on NWP
- Many remap entries marked INVALID due to NWP die topology changes
- All SB endpoints use 16-bit port IDs

### TC Coverage Map

| TC | Scope | Environment |
|----|-------|-------------|
| [22022423123](https://hsdes.intel.com/appstore/article-one/#/22022423123) | iMH GPSB end point sweep | FV (silicon) |
| [22022423125](https://hsdes.intel.com/appstore/article-one/#/22022423125) | iMH PMSB end point sweep | FV (silicon) |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Role |
|-----------|----------------|------|
| GPSB | Port ID remap table (iMH) | Endpoint addressing |
| PMSB | Port ID remap table (iMH) | PM message routing |
| CSR | Sideband config registers | Endpoint configuration |
| PUNIT | HWRS, RC, RA agents | PM endpoint consumers |

---

## Section 3: Reset, Power, and Clocking

- Endpoints must be accessible after platform boot (post-BIOS init)
- GPSB/PMSB remap tables programmed during reset exit by PCode
- Invalid entries must not respond (no spurious completions)

---

## Section 4: Programming Model

Sideband endpoints are addressed via 16-bit port IDs mapped through remap tables. The sweep iterates all valid GPSB and PMSB entries on the iMH die, issuing read transactions to each endpoint. Valid endpoints must respond; INVALID-marked entries must not respond.

---

## Section 5: Operational Behavior

### Pass/Fail Bar

| Criterion | Measurable Threshold | Spec Basis |
|-----------|---------------------|-----------|
| All valid endpoints accessible | Every non-INVALID remap entry responds to read | NWP sideband architecture |
| No timeout | No endpoint read times out | Architecture invariant |
| No corruption | Response data matches expected reset values or configured state | Endpoint register spec |
| Invalid entries silent | INVALID remap entries produce no response | NWP remap table spec |

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| INVALID remap entry accessed | Should produce no response | Covered by sweep | No action |
| Endpoint in reset state | May return default values | Covered by sweep | No action |
| Concurrent PM traffic during sweep | Other PM messages in flight | Not explicitly stressed | Low risk |

---

## Section 7: Security / Safety / Policy

- Only trusted HW agents and authenticated firmware access PM sideband endpoints
- Sweep uses PythonSV/validation interface (inherently privileged)

---

## Section 8: References

- [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) - sideband topology
- [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/soc_pm_has/dmr_soc_pm_has.html) - GPSB/PMSB architecture
