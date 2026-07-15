# CBB CCF GV BIOS Configuration

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422850](https://hsdes.intel.com/appstore/article-one/#/22022422850) |
| **Title** | CBB CCF GV BIOS Configuration |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | Fabric DVFS / CBB CCF GV |
| **Parent TCD** | [22022421165](https://hsdes.intel.com/appstore/article-one/#/22022421165) |
| **KB last updated** | 2026-07-08 |

---

## Test Case Intent

Verify that BIOS correctly configures CBB CCF GV via the two knobs `UncoreFreqCtrlCbb` (maps to `UFS_THROTTLE_MODE`: 0=auto, 1=clamp) and `UncoreFreqRatioCbb` (maps to `MAX_RATIO = MIN_RATIO` when > 0, dynamic when 0). Confirm PCode enforces the programmed values per CBB. Validated using Python-SV register reads and FlexCon (`flexconPM.py`).

**Flow:**

- BIOS CBB CCF GV enabling — verify `UncoreFreqCtrlCbb` knob enables CCF GV per CBB (`UFS_CONTROL.UFS_THROTTLE_MODE`)
- BIOS CBB CCF GV configurations available — `UncoreFreqCtrlCbb` (0=auto, 1=clamp) and `UncoreFreqRatioCbb` (0=dynamic, N=fixed ratio) accessible and writable in BIOS Setup
- Match pCode interpretation — verify `UFS_CONTROL` fields per CBB reflect the BIOS knob values after boot; use FlexCon (`flexconPM.py`) to confirm
- Override — change BIOS CCF GV knobs via BIOS Setup or xmlcli if required; verify TPMI updated after reboot

**BIOS Knobs (resolves original Open #1):** `UncoreFreqCtrlCbb` → `UFS_THROTTLE_MODE`; `UncoreFreqRatioCbb` → `MAX_RATIO = MIN_RATIO` (fixed) or dynamic when 0.

**Test tool:** Python-SV + FlexCon (`flexconPM.py`). Verified on DMR silicon and Simics (see [22611874742](https://hsdes.intel.com/appstore/article-one/#/22611874742)).

---

## Pre-Conditions

| Pre-Condition | Requirement |
|---|---|
| System booted to OS | BIOS CPL4 complete; PCode initialized |
| TPMI accessible per CBB | `sv.sockets.cbbs.base.tpmi.ufs_control` readable |
| Python-SV available | `import namednodes; sv = namednodes.sv` succeeds |
| BIOS knobs override tool available | BIOS Setup menu or xmlcli accessible |

---

## Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Boot with default BIOS knobs. Read `UFS_CONTROL` per CBB and run `flexconPM.py` | `UFS_THROTTLE_MODE=1` (Clamp default); dynamic ratio range; FlexCon confirms | FlexCon/register mismatch |
| 2 | Set `UncoreFreqCtrlCbb=1, UncoreFreqRatioCbb=N` (e.g. 15, 28, 3). Reboot. Read `UFS_CONTROL` per CBB and run `flexconPM.py` | `UFS_THROTTLE_MODE=1`; `MAX_RATIO=MIN_RATIO=N` (clipped to fused P0/Pm if out of range) | Ratio not reflected; no clipping at fused boundary |
| 3 | Set `UncoreFreqCtrlCbb=0, UncoreFreqRatioCbb=0`. Reboot. Read and run `flexconPM.py` | `UFS_THROTTLE_MODE=0` (autonomous); dynamic ratio range | Mode not 0 |
| 4 | Set `UncoreFreqCtrlCbb=0, UncoreFreqRatioCbb=N` (e.g. 16, 27). Reboot. Verify | `UFS_THROTTLE_MODE=0`; `MAX_RATIO=MIN_RATIO=N` | Mode/ratio not applied |

---

## Pass / Fail Criteria

**PASS:** All BIOS knobs for CCF GV in each CBB available and writable. PCode interpretation matches: `UncoreFreqCtrlCbb` → `UFS_THROTTLE_MODE`; `UncoreFreqRatioCbb` → `MAX_RATIO=MIN_RATIO`. FlexCon (`flexconPM.py`) confirms register values.

**FAIL:** Any knob not reflected in `UFS_CONTROL`; FlexCon disagrees with direct register read; ratio not clipped to fused P0/Pm range.

---

## Post-Process

Save `UFS_CONTROL` dump per CBB for each scenario, FlexCon output log, fused P0/Pm ratios from `sst_pp_info_11`.

---

## References

- [BIOS CPU P-State Knobs (UncoreFreqCtrlCbb, UncoreFreqRatioCbb)](https://docs.intel.com/documents/System-firmware-bios/Domain/ServerCpuPm/Index/CPU%20&%20PM%20BIOS%20Knobs/BiosKnobs.html#figure-cpu-p-state-control)
- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#ccf-gv)
- [DMR CBB TPMI Support](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_TPMI/cbb_tpmi.html)
- [Architectural UFS TPMI Interface](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html#dmr-family)
- [Uncore Frequency Scaling in a Hierarchical SoC](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/Hierarchical%20UFS/HPM_UFS.html#bios-control)
- [CBB CCF Power Management HAS index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html)
- [CBB Telemetry Aggregator](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html)
- [Execution Evidence HSD 22611874742](https://hsdes.intel.com/appstore/article-one/#/22611874742) — jenyaohs, 2024-11-08
