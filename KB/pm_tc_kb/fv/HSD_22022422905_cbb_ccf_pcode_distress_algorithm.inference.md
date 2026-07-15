# CBB CCF PCODE Algorithm for Distress Input

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422905](https://hsdes.intel.com/appstore/article-one/#/22022422905) |
| **Title** | CBB CCF PCODE algorithm for distress input |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | Ring Scalability / PCode Algorithm / ia_ring_factor / WP Calculation |
| **Parent TCD** | [22022421197 -- CBB CCF Ring Frequency Scalability](https://hsdes.intel.com/appstore/article-one/#/22022421197) |
| **KB last updated** | 2026-07-10 |

---

## Test Case Intent

Verify that PCode correctly processes the CCF distress input via the ring scalability algorithm and produces accurate ring GV frequency working points. The algorithm translates `ia_distress[3:0]` (0-15 grade) into `ia_ring_factor` (0..1), then computes:

`ia_promote_ring = (max{core_ratios} - ia_to_ring_downbin) × ia_ring_factor`

PCode initiates ring scalability via: slow loop, fast-path on distress change, and fast-path per DistressCycleUpdate (200µs). Verify all PCode algorithm inputs are accessible and that ring frequency responds correctly to distress input changes.

**⚠️ NOTE — Differentiation from related TCs using the same script:**
- **TC 22022422851** (CBB CCF GV PEGA Injection, TCD 22022421168, Active States TPF): Uses the same `--test_ccf_pega_pstate` script but validates the **PEGA-driven GV state machine output** (does CCF frequency reach the requested PEGA operating point?). Verifies `ufs_status.current_ratio` only.
- **THIS TC (22022422905)**: Validates the **PCode ring scalability algorithm internals** — specifically the distress-to-ring-factor conversion (`ia_distress → ia_ring_factor → ia_promote_ring`). Verifies `pcode.vars.ring.*`, `ia_distress`, `ia_ring_factor`. Uses PEGA as stimulus but checks algorithm correctness, not just GV state.
- **TC 22022422896** (CBB CCF Message to Punit): Validates the **sideband message DELIVERY** (`CR_WR` to `PUNIT_CR_RING_DISTRESS_STATUS`, 4-bit grade readability). THIS TC validates the PCode ALGORITHM that processes the already-delivered grade.

`ia_promote_ring = (max{core_ratios} - ia_to_ring_downbin) × ia_ring_factor`

PCode initiates ring scalability via: slow loop, fast-path on distress change, and fast-path per DistressCycleUpdate (200µs). Verify all PCode algorithm inputs are accessible and that ring frequency responds correctly to distress input changes.

**PCode algorithm inputs to verify (from original description):**
- `ia_distress[3:0]` — grade input (0-15), read from `ring_distress_status`
- Per-level parameters (7 levels): Min/Max Val, UpStep, DownStep, HighDisLevel
- RSE = 16K uclk, Wgrade = 1 (EMA), DistressCycleUpdate = 200µs
- `cbb.pcode.vars.ring.resolved_ratios.{max, guaranteed, min}` — resolved ring ratios after algorithm
- `cbb.base.ccf_pma.ccf_pmc_regs.ccf_wp[0].target_max_ratio` — final WP output

**Flow:**

- Verify distress input reaches PCode: `ring_distress_status.ia_distress` readable and valid
- Verify PCode resolved ring ratios are accessible: `pcode.vars.ring.resolved_ratios.*`
- Verify PCode WP output responds to injected distress: PEGA P-state injection → CCF_WP changes → `ufs_status.current_ratio` tracks
- Verify algorithm triggers: slow loop and fast path both update WP
- Verify post-reset persistence: algorithm parameters survive warm reset

**Test script (closest match):** `pmx_ccf_cbo.py --test_ccf_pega_pstate` → `ccfu.ccf_pegaPstate_test(sktNum, dieName, clrgv=ratio, chkstr='ccf_wp,ufs_status')` — exercises the PEGA P-state path which is the silicon-level simulation of distress-driven ring frequency change.

---

## Pre-Conditions

| Pre-Condition | Requirement |
|---|---|
| System booted to OS | BIOS CPL4 complete; PCode ring scalability running |
| Ring scalability enabled | MSR 0x1FC bit[25] `disable_ring_ee=0`; `ring_distress_status.ia_distress_invalid=0` |
| PCode vars accessible | `cbb.pcode.vars.ring.resolved_ratios` readable |
| PEGA available | `import diamondrapids.pm.pmutils.pega as pega` succeeds |

---

## Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Read distress input: `ring_distress_status.ia_distress` and verify validity flag; read `pcode.vars.ring.resolved_ratios.{max,guaranteed,min}` | `ia_distress_invalid=0`; resolved ratios non-zero and ordered max≥guaranteed≥min | Invalid flag set or zero ratios — algorithm inputs missing |
| 2 | Verify PCode WP responds to PEGA injection: `ccf_pegaPstate_test(skt, 'cbbs', clrgv=target, chkstr='ccf_wp,ufs_status')` across full fused [Pm..P0] range | Each injected ratio reflected in `ccf_wp[0].target_max_ratio` and `ufs_status.current_ratio` | Ratio mismatch — PCode WP calculation not following injected demand |
| 3 | Verify slow loop trigger: read `ring_distress_status.ia_distress` at 1s intervals (3 samples). Verify value changes under varying OS load | `ia_distress` varies — slow loop updating distress input and PCode responding | `ia_distress` stuck at one value — slow loop not triggering |
| 4 | Verify fast-path trigger: read `ccf_wp_status.ratio` before and immediately after PEGA injection | WP updates within 1 tick after injection — fast path active (distress change detected) | WP unchanged after injection — fast path not triggering |
| 5 | Verify PCode algorithm parameters accessible: check `pcode.vars.ring.resolved_ratios.min` equals fused Pm and `.max` equals fused P0 | Resolved ratios match `sst_pp_info_11.{pm_fabric_ratio, p0_fabric_ratio}` | Mismatch — PCode not initialized from fuses correctly |

---

## Pass / Fail Criteria

**PASS:** `ring_distress_status.ia_distress` readable with `ia_distress_invalid=0`; `pcode.vars.ring.resolved_ratios` accessible and fuse-consistent; CCF WP (`ccf_wp[0].target_max_ratio`, `ufs_status.current_ratio`) tracks PEGA-injected ring ratio across full [Pm..P0] range; distress value updates under load; fast-path WP update within 1 tick.

**FAIL:** Distress input invalid; resolved ratios inaccessible or zero; WP not tracking PEGA injection; distress value never changes under varying load.

---

## Post-Process

Save: `ring_distress_status` samples, `pcode.vars.ring.resolved_ratios`, `ccf_wp[0].target_max_ratio` and `ufs_status.current_ratio` per CBB for each injected ratio, MSR 0x1FC per core.

---

## References

- [CBB CCF Power Management HAS (Ring Scalability)](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#cbb-ring-frequency-scalability)
- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#ccf-gv)
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#punit-telemetry-space-details)
- [CBB CCF Power Management HAS index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html)
- [pCode Home](https://wiki.ith.intel.com/display/ServerPcode/Server+Pcode+Home)
- [Related TC 22022422894 - IA Distress Input](https://hsdes.intel.com/appstore/article-one/#/22022422894)
