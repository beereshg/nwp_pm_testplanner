# CBB CCF CBO Telemetry

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422889](https://hsdes.intel.com/appstore/article-one/#/22022422889) |
| **Title** | CBB CCF CBO Telemetry |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | Ring Scalability / CBO Lookup Telemetry |
| **Parent TCD** | [22022421189](https://hsdes.intel.com/appstore/article-one/#/22022421189) |
| **KB last updated** | 2026-07-08 |

---

## Test Case Intent

Verify post-silicon extraction of CBB CCF ring scalability telemetry from **CBO lookup counters**. Ring Scalability telemetry is the mechanism by which PCode measures IA traffic to decide CCF frequency (GV) changes per RSE (Ring Scalability Event, ~2k uclk cycles). This TC focuses on CBO (Cache Box) lookup counters — the IA traffic side of ring scalability telemetry. SBO snoop counters are covered separately by TC [22022422900](https://hsdes.intel.com/appstore/article-one/#/22022422900) under TCD "CBB CCF SBO Snoop Telemetry".

**CBO telemetries (per cluster `i_ccf_env{N}`, per ingress `ingress_{NN}`):**
- Lookup counter — `cbb.base.i_ccf_env{N}.ingress_{NN}.cbo_lookup_counter.lookup_counter` (non-addressless transactions)
- Enable bit — `cbb.base.i_ccf_env{N}.ingress_{NN}.cbo_lookup_counter.lookup_counter_enable`
- Ingress-all register — enables/disables all counters within a cluster

**Flow:**

- Verify CBO lookup counters are accessible per CBB per cluster
- Test enable/disable toggle via `lookup_counter_enable`
- Verify counters are non-zero when enabled under CCF activity (IA load or PEGA P-state injection)
- Verify disabled counters remain stable (freeze mechanism)

**Test script:**
- `pmx_ccf_cbo.py --test_ccf_cbo_telemetry` → `ccf_cbo_telemetry_lookup_cntr_disable_test()` + `ccf_cbo_telemetry_lookup_cntr_enable_disable_all_test()`

**Script vs TC note:** The script tests disable/freeze functionality (counters stay zero when disabled = PASS). The TC also requires verifying counters are NON-ZERO during activity — not covered by the existing script; needs workload + enable + verify non-zero.

---

## Pre-Conditions

| Pre-Condition | Requirement |
|---|---|
| System booted to OS | BIOS CPL4 complete; PCode running Ring Scalability |
| CBO counters accessible | `cbb.base.i_ccf_env0.ingress_00.cbo_lookup_counter` readable/writable |
| IA activity available | System running workload (idle OS or Supercollider) to drive CBO lookups |

---

## Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Enable all CBO lookup counters per CBB: set `lookup_counter_enable=1` for all `i_ccf_env{0-3}.ingress_{NN}`. Let run 15s. Read `lookup_counter` | At least one `lookup_counter > 0` per CBB under idle OS activity | All counters zero — CBO lookup counting not functional |
| 2 | Test CBO counter disable: `ccf_cbo_telemetry_lookup_cntr_disable_test(skt, 'cbbs', 'i_ccf_envs', 'ingresss', rtime=100)` | PASS (diff==0) — disabled counters stable; freeze mechanism works | FAIL — disabled counters changed; disable mechanism broken |
| 3 | Test CBO ingress-all enable/disable toggle: `ccf_cbo_telemetry_lookup_cntr_enable_disable_all_test(skt, 'cbbs', 'i_ccf_envs', iter_num=10)` | All toggles accepted; `lookup_counter_enable` reflects written value | Any toggle fails — ingress-all register not controlling all ingresss |

---

## Pass / Fail Criteria

**PASS:** All CBO lookup counters accessible per CBB per cluster; enable/disable toggle works; at least one `lookup_counter > 0` per CBB when enabled under system activity; disabled counters remain stable (freeze mechanism works).

**FAIL:** Any CBO counter inaccessible; enable/disable toggle fails; all counters remain zero when enabled; disabled counters change.

---

## Post-Process

Save: CBO `lookup_counter` values for all `i_ccf_env{N}.ingress_{NN}` per CBB (enabled state); enable/disable toggle pass/fail counts.

---

## References

- [CBB Ring frequency scalability](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#cbb-ring-frequency-scalability)
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details)
- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#ccf-gv)
- [CBB CCF Power Management HAS index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html)
- [pCode Home](https://wiki.ith.intel.com/display/ServerPcode/Server+Pcode+Home)
