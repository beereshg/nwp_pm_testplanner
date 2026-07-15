# CBB CCF Distress Signal

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422894](https://hsdes.intel.com/appstore/article-one/#/22022422894) |
| **Title** | CBB CCF Distress signal |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | Ring Scalability / Distress Signal / PCode Algorithm Inputs |
| **Parent TCD** | [22022421192](https://hsdes.intel.com/appstore/article-one/#/22022421192) |
| **KB last updated** | 2026-07-08 |

---

## Test Case Intent

Verify that all PCode algorithm inputs for ring scalability distress processing are available and valid. The CCF PMA sends a distress message to PCode via PMSB (CR_WR opcode to address 0x1C8 = PUNIT_CR_RING_DISTRESS_STATUS) containing `ia_distress[3:0]` (0-15 IA stress level) and `snoop_level[11:8]` (0-15 snoop stress level). PCode translates distress level to `ia_ring_factor` and computes the ring frequency via slow loop and fast-path triggers. This TC verifies the distress signal path is functional.

**Distress signal (from HAS):**
- `ring_distress_status.ia_distress` [3:0] — IA main grade (0-15)
- `ring_distress_status.snoop_level` [11:8] — Snoop grade (0-15)
- `ring_distress_status.ia_distress_invalid` [4] — validity flag (0 = valid)
- `ring_distress_status.snoop_level_invalid` [12] — validity flag (0 = valid)
- Ring scalability enable: MSR POWER_CTL 0x1FC bit[25] `disable_ring_ee` = 0 (enabled)

**Flow:**

- Verify ring scalability is enabled: MSR 0x1FC `disable_ring_ee=0` on all cores per CBB
- Verify distress status register is accessible and returning valid data (`ia_distress_invalid=0`, `snoop_level_invalid=0`)
- Verify distress levels are non-zero under CCF activity (ring scalability events occurring)
- Match PCode interpretation: `ring_distress_status` reflects current CCF load

**Test scripts:**
- `pmx_ccf_cbo.py --test_ccf_distress_to_punit` → `cbb_ccf_distress_to_punit_test()` — checks MSR 0x1FC `disable_ring_ee=0`
- `pmx_ccf_cbo.py --test_ccf_pcode_to_distress_input` → `cbb_ccf_pcode_to_distress_input_test()` — reads `ring_distress_status.ia_distress` before/after sleep (partially implemented — no pass/fail comparison)

---

## Pre-Conditions

| Pre-Condition | Requirement |
|---|---|
| System booted to OS | BIOS CPL4 complete; PCode running ring scalability |
| Ring scalability enabled | MSR POWER_CTL 0x1FC bit[25] `disable_ring_ee=0` on all cores |
| `ring_distress_status` accessible | `cbb.base.punit_regs.punit_pmsb.pmsb_pcu.ring_distress_status` readable |
| PEGA released | `pega.release(1)` called before test to clear any PEGA overrides |

---

## Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Check MSR POWER_CTL 0x1FC `disable_ring_ee` bit[25] per core per CBB: `cbb_ccf_distress_to_punit_test(skt, 'cbbs')` | `disable_ring_ee=0` on all cores — ring scalability (distress source) enabled | Any core shows `disable_ring_ee=1` — ring scalability disabled, no distress to PCode |
| 2 | Read `ring_distress_status` validity: check `ia_distress_invalid=0` and `snoop_level_invalid=0` per CBB | Both validity flags = 0 (valid data) per CBB | Any invalid flag = 1 — distress signal not initialized |
| 3 | Read baseline `ring_distress_status.ia_distress` and `snoop_level` per CBB: `cbb_ccf_pcode_to_distress_input_test(skt, 'cbbs')` | Both fields readable; note baseline values | Read error — PMSB register not accessible |
| 4 | Apply CCF activity (idle OS or PEGA P-state injection). Re-read `ring_distress_status.ia_distress` | `ia_distress` is non-zero or changes from baseline — distress path is active | `ia_distress` always 0 — no distress reaching PCode; CCF not sending distress |
| 5 | Verify hysteresis chicken bit accessible: read `ring_distress_status.group` field and any hysteresis override register | Chicken bit register readable/writable | Register not accessible — CB not implemented |

---

## Pass / Fail Criteria

**PASS:** MSR 0x1FC `disable_ring_ee=0` on all cores; `ia_distress_invalid=0` and `snoop_level_invalid=0` per CBB; `ia_distress` and `snoop_level` fields accessible and non-zero under CCF load; all PCode algorithm inputs (ia_distress, snoop_level, validity flags) available.

**FAIL:** `disable_ring_ee=1` on any core (ring scalability disabled); invalid flags set; `ring_distress_status` inaccessible; all distress fields zero regardless of system load.

---

## Post-Process

Save: MSR 0x1FC per core, `ring_distress_status` (ia_distress, snoop_level, both invalid flags) per CBB before/after CCF activity.

---

## References

- [CBB CCF Power Management HAS (Ring Scalability)](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#cbb-ring-frequency-scalability)
- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#ccf-gv)
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details)
- [CBB CCF Power Management HAS index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html)
- [pCode Home](https://wiki.ith.intel.com/display/ServerPcode/Server+Pcode+Home)
- [CBB Power Event Generation Architecture (PEGA)](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html)
