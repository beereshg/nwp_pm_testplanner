# CBB CCF Snoop Scalability/Distress

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422895](https://hsdes.intel.com/appstore/article-one/#/22022422895) |
| **Title** | CBB CCF Snoop Scalability/Distress |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | Ring Scalability / Snoop Distress / SBO Telemetry |
| **Parent TCD** | [22022421195](https://hsdes.intel.com/appstore/article-one/#/22022421195) |
| **KB last updated** | 2026-07-08 |

---

## Test Case Intent

Verify the **Snoop** scalability/distress path — the snoop grade field in the distress message sent from CCF PMA to PCode. The same distress register (PUNIT_CR_RING_DISTRESS_STATUS, address 0x1C8) carries `snoop_level[11:8]` (0-15 snoop stress level) alongside `ia_distress[3:0]`. This TC focuses specifically on the snoop side: SBO snoop counters → snoop grade → PCode snoop distress input.

**Differentiator from TC 22022422894 (IA Distress):**
- 22022422894 covers `ia_distress[3:0]` (IA Main Grade — driven by CBO lookup counters)
- This TC covers `snoop_level[11:8]` (Snoop Grade — driven by SBO snoop counters)
- Both share the same distress message register and PCode algorithm framework

**Distress message (snoop fields):**
- `ring_distress_status.snoop_level` [11:8] — 0-15 snoop stress level
- `ring_distress_status.snoop_level_invalid` [12] — 0 = valid, 1 = invalid/uninitialized
- `ring_distress_status.group` [31] — 0=Main, 1=Snoop message type
- SBO source: `cbb.base.i_ccf_env{N}.sbo_misc_regs.sbo_snoop_counter`

**Flow:**

- Verify snoop grade inputs are available: `ring_distress_status.snoop_level_invalid=0` per CBB
- Verify SBO snoop counters are accessible and can be enabled per cluster
- Verify `snoop_level` changes under snoop traffic (system active with coherent workload)
- Match PCode interpretation: snoop distress drives ring frequency via same algorithm as IA distress

**Test scripts:** Same distress scripts as TC 22022422894, plus SBO telemetry:
- `--test_ccf_distress_to_punit` — ring scalability enabled (prerequisite for both IA and snoop distress)
- `--test_ccf_sbo_telemetry` → `ccf_sbo_telemetry_snoop_cntr_disable_test()` — SBO snoop counter (source of snoop grade) freeze validation

---

## Pre-Conditions

| Pre-Condition | Requirement |
|---|---|
| System booted to OS | BIOS CPL4 complete; PCode running ring scalability |
| Ring scalability enabled | MSR POWER_CTL 0x1FC bit[25] `disable_ring_ee=0` |
| `ring_distress_status` accessible | `cbb.base.punit_regs.punit_pmsb.pmsb_pcu.ring_distress_status` readable |
| SBO snoop counters accessible | `cbb.base.i_ccf_env0.sbo_misc_regs.sbo_snoop_counter` readable/writable |

---

## Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Read `ring_distress_status.snoop_level_invalid` per CBB | `snoop_level_invalid=0` (valid snoop data) on all CBBs | `snoop_level_invalid=1` — snoop grade not initialized |
| 2 | Read `ring_distress_status.snoop_level` per CBB at idle | Non-garbage value in [11:8]; note baseline | Read error — distress register not accessible |
| 3 | Enable SBO snoop counters: `ccf_sbo_telemetry_snoop_cntr_disable_test(skt, 'cbbs', 'i_ccf_envs', rtime=100)` | PASS (diff==0) — disabled SBO counters stable; enable/disable mechanism works | FAIL — disabled counters changed; SBO disable broken |
| 4 | Enable SBO snoop counting; apply coherent workload (idle OS sufficient). Re-read `ring_distress_status.snoop_level` | `snoop_level` changes or is non-zero under snoop activity — snoop distress path active | `snoop_level` always 0 regardless of load — snoop grade not reaching PCode |
| 5 | Verify `ring_distress_status.group` field toggles: PCode receives both Main (group=0) and Snoop (group=1) messages | Both group values observed in register across sampling interval | Only one group type observed — snoop message not being sent |

---

## Pass / Fail Criteria

**PASS:** `snoop_level_invalid=0` per CBB; `snoop_level` accessible and reflects snoop load; SBO snoop counter disable mechanism works; both Group=0 (IA) and Group=1 (Snoop) messages visible in `ring_distress_status`; all snoop distress PCode inputs available.

**FAIL:** `snoop_level_invalid=1`; `snoop_level` always 0 regardless of system load; SBO disable mechanism broken; only Group=0 messages (snoop messages not sent).

---

## Post-Process

Save: `ring_distress_status` (snoop_level, snoop_level_invalid, group field) per CBB across multiple samples; SBO snoop counter values per cluster.

---

## References

- [CBB CCF Power Management HAS (Ring Scalability)](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#cbb-ring-frequency-scalability)
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details)
- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#ccf-gv)
- [CBB CCF Power Management HAS index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html)
- [pCode Home](https://wiki.ith.intel.com/display/ServerPcode/Server+Pcode+Home)
- [Related TC 22022422894 - IA Distress](https://hsdes.intel.com/appstore/article-one/#/22022422894)
