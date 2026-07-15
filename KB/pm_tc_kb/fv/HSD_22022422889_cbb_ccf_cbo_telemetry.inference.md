# CBB CCF CBO Telemetry

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422889](https://hsdes.intel.com/appstore/article-one/#/22022422889) |
| **Title** | CBB CCF CBO Telemetry |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | Ring Scalability / CBO Telemetry / SBO Telemetry |
| **Parent TCD** | [22022421189](https://hsdes.intel.com/appstore/article-one/#/22022421189) |
| **KB last updated** | 2026-07-08 |

---

## Test Case Intent

Verify post-silicon extraction of CBB CCF ring scalability telemetry from CBO lookup counters and SBO snoop counters. Ring Scalability telemetry is the mechanism by which PCode measures IA traffic to decide CCF frequency (GV) changes per RSE (Ring Scalability Event, ~2k uclk cycles). Verify all CBO and SBO telemetry counters are accessible, can be enabled/disabled, and are non-zero during CCF activity.

**CBO telemetries (per cluster `i_ccf_env{N}`, per ingress `ingress_{NN}`):**
- Lookup counter — `cbb.base.i_ccf_env{N}.ingress_{NN}.cbo_lookup_counter.lookup_counter` (non-addressless transactions)
- Enable bit — `cbb.base.i_ccf_env{N}.ingress_{NN}.cbo_lookup_counter.lookup_counter_enable`
- Ingress-all register — enables/disables all counters within a cluster

**SBO telemetries (per cluster):**
- Snoop counter — `cbb.base.i_ccf_env{N}.sbo_misc_regs.sbo_snoop_counter.snoop_counter`
- Enable bit — `cbb.base.i_ccf_env{N}.sbo_misc_regs.sbo_snoop_counter.snoop_counter_enable`

**Flow:**

- Verify CBO and SBO telemetry counters are accessible per CBB per cluster
- Test enable/disable toggle via `lookup_counter_enable` and `snoop_counter_enable`
- Verify counters are non-zero when enabled under CCF activity (IA load or PEGA P-state injection)
- Verify disabled counters remain stable (freeze mechanism)

**Test scripts:** Two scripts map to this TC:
- `pmx_ccf_cbo.py --test_ccf_cbo_telemetry` → `ccf_cbo_telemetry_lookup_cntr_disable_test()` + `ccf_cbo_telemetry_lookup_cntr_enable_disable_all_test()`
- `pmx_ccf_cbo.py --test_ccf_sbo_telemetry` → `ccf_sbo_telemetry_snoop_cntr_disable_test()`

**Script vs TC note:** Both scripts test disable/freeze functionality (counters stay zero when disabled = PASS). The TC also requires verifying counters are NON-ZERO during activity — not covered by the existing scripts; needs workload + enable + verify non-zero.

---

## Pre-Conditions

| Pre-Condition | Requirement |
|---|---|
| System booted to OS | BIOS CPL4 complete; PCode running Ring Scalability |
| CBO counters accessible | `cbb.base.i_ccf_env0.ingress_00.cbo_lookup_counter` readable/writable |
| SBO counters accessible | `cbb.base.i_ccf_env0.sbo_misc_regs.sbo_snoop_counter` readable/writable |
| IA activity available | System running workload (idle OS or Supercollider) to drive CBO lookups |

---

## Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Enable all CBO lookup counters per CBB: set `lookup_counter_enable=1` for all `i_ccf_env{0-3}.ingress_{NN}`. Let run 15s. Read `lookup_counter` | At least one `lookup_counter > 0` per CBB under idle OS activity | All counters zero — CBO lookup counting not functional |
| 2 | Test CBO counter disable: `ccf_cbo_telemetry_lookup_cntr_disable_test(skt, 'cbbs', 'i_ccf_envs', 'ingresss', rtime=100)` | PASS (diff==0) — disabled counters stable; freeze mechanism works | FAIL — disabled counters changed; disable mechanism broken |
| 3 | Test CBO ingress-all enable/disable toggle: `ccf_cbo_telemetry_lookup_cntr_enable_disable_all_test(skt, 'cbbs', 'i_ccf_envs', iter_num=10)` | All toggles accepted; `lookup_counter_enable` reflects written value | Any toggle fails — ingress-all register not controlling all ingresss |
| 4 | Enable all SBO snoop counters: set `snoop_counter_enable=1` for all `i_ccf_env{0-3}`. Let run 15s. Read `snoop_counter` | At least one `snoop_counter > 0` per CBB (snoop traffic present) | All zero — SBO snoop counting not functional |
| 5 | Test SBO counter disable: `ccf_sbo_telemetry_snoop_cntr_disable_test(skt, 'cbbs', 'i_ccf_envs', rtime=100)` | PASS (diff==0) — disabled snoop counters stable | FAIL — disabled snoop counters changed |

---

## Pass / Fail Criteria

**PASS:** All CBO lookup and SBO snoop counters accessible per CBB; enable/disable toggle works for both; at least one counter > 0 per CBB when enabled under system activity; disabled counters remain stable.

**FAIL:** Any counter inaccessible; enable/disable toggle fails; all counters remain zero when enabled; disabled counters change.

---

## Post-Process

Save: CBO `lookup_counter` values for all `i_ccf_env{N}.ingress_{NN}` per CBB (enabled state); SBO `snoop_counter` values; enable/disable toggle pass/fail counts.

---

## References

- [CBB Ring frequency scalability](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#cbb-ring-frequency-scalability)
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details)
- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#ccf-gv)
- [CBB CCF Power Management HAS index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html)
- [pCode Home](https://wiki.ith.intel.com/display/ServerPcode/Server+Pcode+Home)
