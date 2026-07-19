# TCD: CBB CCF Ring Scalability Telemetry & Distress Generation

<!-- NEW 2026-07-19: Split from TCD 22022421197 (CBB CCF Distress Signal Path).
     Co-Design T2 ingest: HW signal generation (silicon) has a different bar
     from FW algorithm correctness (PCode). This TCD covers the silicon side.
     HSD TCD creation pending — replace NEW with actual HSD ID when created. -->

| Field | Value |
|-------|-------|
| **TCD ID** | *(HSD creation pending)* |
| **Title** | CBB CCF Ring Scalability Telemetry & Distress Generation |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [22022420514 — CBB CCF Ring Scalability](https://hsdes.intel.com/appstore/article-one/#/22022420514) |
| **Validation Phase** | **Alpha / Beta / PRQ** — Volume functional validation (multi-milestone) |
| **Feature** | CBB CCF Ring Frequency Scalability — HW Telemetry & Distress Signal Generation |
| **Child TCs** | [22022422894](https://hsdes.intel.com/appstore/article-one/#/22022422894) — Distress Signal to PUnit<br>[22022422895](https://hsdes.intel.com/appstore/article-one/#/22022422895) — Snoop Scalability/Distress |
| **Split from** | [22022421197](https://hsdes.intel.com/appstore/article-one/#/22022421197) — CBB CCF Distress Signal Path |
| **KB last updated** | 2026-07-19 |

---

## Section 1: Architecture / Micro-architecture and Functionality

> **Architecture overview:** See [TPF 22022420514 — CBB CCF Ring Scalability](https://hsdes.intel.com/appstore/article-one/#/22022420514) §2 Design Details
> for full-stack cross-layer diagram, dual-path architecture, and Interface & Register Matrix.

**CBB CCF Ring Scalability Telemetry & Distress Generation** validates the **silicon-side** of the ring scalability feature: CBO and SBO telemetry counter behavior, SBO grade computation, and CCF PMA distress message delivery to PUnit.

The scope covers:
1. **CBO Bandwidth telemetry** — 48 CBO mesh RD/WR counters accumulate per-cycle; sampled per RSE (~2k uclk cycles); feed BW threshold LUT walk in PCode.
2. **SBO Snoop distress** — SBO snoop back-pressure occupancy counters feed the ring-scalability logic; when TOR occupancy + WCil exceed HIGH threshold, CCF PMA generates IA_DISTRESS.
3. **Distress message delivery** — CCF PMA sends distress message to CBB-local PUNIT via PMSB (CR_WR opcode to address 0x1C8 = `PUNIT_CR_RING_DISTRESS_STATUS`) containing `ia_distress[3:0]` and `snoop_level[11:8]`.

This TCD does **NOT** cover the PCode algorithm that consumes the distress signal — that is validated by the sibling TCD "CBB PCode Ring-Distress Consumption Algorithm".

### Data Flow

```
CBO mesh (48 per CBB)          SBO (per cluster)
  RD/WR transaction counters     snoop back-pressure occupancy
  accumulate per-cycle           TOR occ + WCil counters
         |                              |
         v  (per RSE ~2k uclk)          v  (per RSE)
  BW telemetry to PCode         Ring-scalability logic
  (CBO pipe traffic)            7-threshold logistic regression
                                        |
                                        v
                                SBO grade output (0-15)
                                        |
                                        v
                                CCF PMA collects grades
                                from all clusters
                                        |
                                        v
                                PMSB CR_WR 0x1C8 →
                                PUNIT_CR_RING_DISTRESS_STATUS
                                  ia_distress[3:0]
                                  snoop_level[11:8]
                                  ia_distress_invalid[4]
                                  snoop_level_invalid[12]
```

### Spec Refs (from Co-Design T2)

- "The feature analyzes ring traffic telemetries implemented inside each of the cluster's CBOs and their corresponding SBO… SBO then outputs a 'Grade'… CCF PMA collects the grades… constructs and sends a 'Distress' message to Punit" — [ring_scalability_mas.html](https://docs.intel.com/documents/ccfdoc/src/cbb/ring_scalability/ring_scalability_mas.html)
- SBO/CBO detailed flow uses indication counters, regression, PMON, and SyncBus grade toward CCFPMA — [cbb_ccf_pm.0.5.html](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.0.5.html)

---

## Section 5: Pass/Fail Bar

Under injected or workload-driven BW/snoop stress:
- CBO and SBO telemetry counters/grades change from idle baseline
- SBO produces a non-idle cluster grade
- CCF PMA emits a corresponding distress indication to PUnit for the stressed cluster within the RSE-based telemetry update flow
- `ring_distress_status.ia_distress[3:0]` is non-zero under load
- `ring_distress_status.snoop_level[11:8]` tracks SBO occupancy
- `ia_distress_invalid` and `snoop_level_invalid` flags are 0 (valid)

**FAIL:** `ring_distress_status` always reads 0 regardless of load; invalid flags set; counters stuck at zero; no distress generated under sustained coherency stress.

---

## Section 6: TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422894 — CBB CCF Distress Signal to PUnit](https://hsdes.intel.com/appstore/article-one/#/22022422894) | Distress signal path: CCF PMA → PMSB → PCode receives `ia_distress[3:0]` + `snoop_level[11:8]`; checks `disable_ring_ee=0` per core | `cbb_ccf_distress_to_punit_test` |
| [22022422895 — CBB CCF Snoop Scalability/Distress](https://hsdes.intel.com/appstore/article-one/#/22022422895) | Snoop distress path: `snoop_level[11:8]` valid + responsive to snoop load; `group` field toggles (Group=0 IA / Group=1 Snoop) | `cbb_ccf_pcode_to_distress_input_test` (snoop side) |

---

## Section 8: References

| Reference | Link |
|-----------|------|
| Ring Scalability MAS | [ring_scalability_mas.html](https://docs.intel.com/documents/ccfdoc/src/cbb/ring_scalability/ring_scalability_mas.html) |
| CBB CCF PM HAS v0.5 | [cbb_ccf_pm.0.5.html](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.0.5.html) |
| CBB CCF PM HAS v1.0 | [cbb_ccf_pm.1.0.html](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.1.0.html) |
| Parent TPF | [TPF 22022420514 — CBB CCF Ring Scalability](https://hsdes.intel.com/appstore/article-one/#/22022420514) |
| Sibling TCD | TCD_NEW_pcode_ring_distress_algorithm.md — PCode consumption side |
| Split source | [TCD 22022421197 — CBB CCF Distress Signal Path](https://hsdes.intel.com/appstore/article-one/#/22022421197) |