# CBB CCF SBO Telemetry

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422900](https://hsdes.intel.com/appstore/article-one/#/22022422900) |
| **Title** | CBB CCF SBO Telemetry |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | Ring Scalability / SBO Telemetry / Snoop Counter |
| **Parent TCD** | [22022421201](https://hsdes.intel.com/appstore/article-one/#/22022421201) |
| **KB last updated** | 2026-07-08 |

---

## Test Case Intent

Verify post-silicon extraction of CBB CCF ring scalability telemetry from the **SBO (Snoop Box)** — specifically the SBO snoop counter per cluster. The SBO accumulates snoop traffic grades once per RSE and sends the result to PCode via the distress message. This TC focuses on the SBO side of ring scalability telemetry (complement to TC [22022422889](https://hsdes.intel.com/appstore/article-one/#/22022422889) which covers CBO telemetry).

**SBO telemetries (from original description):**
- ARAC count — cycles blocked by ARAC
- DPT count — DPT message count
- IFA occupancy — average IFA entries per RSE (sampled 8×)
- No credits to SAF — occurrences blocked toward SAF

**PythonSV path:** `cbb.base.i_ccf_env{N}.sbo_misc_regs.sbo_snoop_counter.{snoop_counter, snoop_counter_enable}`

**Note:** The `sbo_snoop_counter` in PythonSV is the primary accessible SBO telemetry register. The other SBO telemetries (ARAC, DPT, IFA, SAF) may require additional register paths not yet in the test script.

**Flow:**

- Verify SBO snoop counters are accessible per cluster per CBB
- Test enable/disable toggle via `snoop_counter_enable`
- Verify SBO counters are non-zero when enabled under snoop traffic
- Verify disabled counters remain stable (freeze mechanism)

**Test script:** `pmx_ccf_cbo.py --test_ccf_sbo_telemetry` → `ccf_sbo_telemetry_snoop_cntr_disable_test()`

**Note on script vs TC intent:** Same gap as TC 22022422889 — script tests FREEZE (diff==0 = PASS). TC requires counters NON-ZERO during activity. Both aspects needed.

---

## Pre-Conditions

| Pre-Condition | Requirement |
|---|---|
| System booted to OS | BIOS CPL4 complete; ring scalability running |
| SBO counters accessible | `cbb.base.i_ccf_env0.sbo_misc_regs.sbo_snoop_counter` readable/writable |
| Snoop traffic present | Coherent workload or idle OS to generate SBO snoop traffic |

---

## Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Enable all SBO snoop counters per CBB: set `snoop_counter_enable=1` for all `i_ccf_env{0-3}`. Let run 15s. Read `snoop_counter` | At least one `snoop_counter > 0` per CBB (snoop traffic counted) | All counters zero — SBO snoop counting not functional |
| 2 | Test SBO counter disable (freeze): `ccf_sbo_telemetry_snoop_cntr_disable_test(skt, 'cbbs', 'i_ccf_envs', rtime=100)` | PASS (diff==0) — disabled SBO counters stable across 100M cycles | FAIL — disabled counters changed; SBO freeze mechanism broken |
| 3 | Test SBO counter enable/disable toggle: `ccf_sbo_telemetry_snoop_cntr_chk(skt, 'cbbs', 'i_ccf_envs', 'enable')` then `'disable'` | Toggle accepted; `snoop_counter_enable` reflects written value per cluster | Toggle not accepted — SBO counter control not working |
| 4 | Verify per-cluster isolation: enable only `i_ccf_env0` snoop counter; verify other clusters (env1-3) stay zero | Only `i_ccf_env0` counts; others remain 0 — per-cluster scoping works | Other clusters count despite being disabled — isolation broken |
| 5 | Read SBO counter across multiple RSE periods under coherent OS load. Verify counter increments monotonically when enabled | Counter value grows over time — SBO accumulating snoop traffic per RSE | Counter stays zero or non-monotonic — SBO not accumulating correctly |

---

## Pass / Fail Criteria

**PASS:** SBO `snoop_counter` accessible per cluster per CBB; enable/disable toggle works per cluster; at least one cluster shows `snoop_counter > 0` under OS activity; disabled clusters remain stable.

**FAIL:** Any SBO counter inaccessible; enable/disable not working; all counters remain 0 when enabled with system activity; freeze mechanism broken.

---

## Post-Process

Save: `sbo_snoop_counter` values for all `i_ccf_env{0-3}` per CBB (enabled and disabled states); enable/disable toggle pass/fail counts.

---

## References

- [CBB Ring Frequency Scalability](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#cbb-ring-frequency-scalability)
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details)
- [CBB CCF Power Management HAS index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html)
- [Related TC 22022422889 - CBO Telemetry](https://hsdes.intel.com/appstore/article-one/#/22022422889)
- [pCode Home](https://wiki.ith.intel.com/display/ServerPcode/Server+Pcode+Home)
