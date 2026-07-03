# Deep Analysis: CBB CCF GV TPMI Request

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422859](https://hsdes.intel.com/appstore/article-one/#/22022422859) |
| **Title** | CBB CCF GV TPMI Request |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | Fabric DVFS / CBB CCF GV -- TPMI-driven ratio locking |
| **Parent TCD** | [22022421171](https://hsdes.intel.com/appstore/article-one/#/22022421171) |
| **KB last updated** | 2026-06-25 |

---

## Test Case Intent

**Objective:** Verify that CBB CCF ring frequency (GV) can be controlled via direct TPMI `UFS_CONTROL` register writes. By programming `MAX_RATIO = MIN_RATIO = target`, the autonomous UFS bandwidth-heuristic algorithm is overridden and PCode GVFSM holds the CCF ring at the programmed fixed ratio. Tests: (1) ratio lock at mid-range; (2) `UFS_STATUS.CURRENT_RATIO` reflects the locked value; (3) autonomous mode restores when `MIN_RATIO < MAX_RATIO`; (4) boundary enforcement -- ratio clamped to fused P0/Pm limits.

**Mechanism:** Setting `UFS_CONTROL.MAX_RATIO = UFS_CONTROL.MIN_RATIO` collapses the allowed operating window to a single point, effectively pinning the GVFSM target. This is the standard way to force CCF to a known frequency for validation. Removing the pin (`MIN < MAX`) restores autonomous bandwidth-driven DVFS.

### Pre-Conditions

| Pre-Condition | Expected State | Failure Indication |
|---------------|---------------|-------------------|
| System booted to XOS/SVOS | BIOS CPL4 complete; PCode running CCF GVFSM | System not booted |
| TPMI UFS_CONTROL writable | `ufs_control` field writes reflected on readback | TPMI write-protected or BIOS locked |
| Baseline CCF ratio known | `UFS_STATUS.CURRENT_RATIO` non-zero on both CBBs | CCF GVFSM not running |
| `UFS_HEADER` fuse limits readable | `max_ratio_cap` and `min_ratio_cap` available | Fuse values not propagated at boot |
| No active RAPL throttle | RAPL PL1 not constraining CCF | RAPL throttle would override TPMI-locked ratio |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Read `UFS_HEADER` per CBB to get fused P0 cap and Pm floor | `max_ratio_cap` and `min_ratio_cap` non-zero; note as boundaries | Zero caps -- fuse not propagated |
| 2 | Read current `UFS_CONTROL.MAX_RATIO` and `MIN_RATIO` as baseline | Non-zero valid range; MAX > MIN | Invalid baseline -- BIOS did not program UFS_CONTROL |
| 3 | Lock ratio: write `UFS_CONTROL.MAX_RATIO = MIN_RATIO = 0x12` (1.8 GHz) on cbb0; wait 5M cycles | Write accepted (readback matches); GVFSM receives single-point target | Write rejected or readback mismatch |
| 4 | Read `UFS_STATUS.CURRENT_RATIO` on cbb0 | `CURRENT_RATIO = 0x12` (1.8 GHz); GVFSM settled at locked value | Ratio != 0x12 -- GVFSM not honoring TPMI pin |
| 5 | Repeat steps 3-4 on cbb1 (independently) | cbb1 CURRENT_RATIO = 0x12 independent of cbb0 | cbb1 not responding -- per-CBB independence broken |
| 6 | Boundary test: write `MAX_RATIO = MIN_RATIO = 0xFF` (above P0 cap) | GVFSM clamps to P0 cap value; CURRENT_RATIO = max_ratio_cap | No clamping -- GVFSM above fused P0 cap |
| 7 | Boundary test: write `MAX_RATIO = MIN_RATIO = 0x01` (below Pm) | GVFSM clamps to min_ratio_cap; CURRENT_RATIO = min_ratio_cap | No clamping -- GVFSM below Pm floor |
| 8 | Restore autonomous mode: write original `MAX_RATIO` and `MIN_RATIO` (MAX > MIN) per CBB; wait 5M cycles | CURRENT_RATIO returns to bandwidth-heuristic-driven value; no longer pinned | Ratio stays at locked value -- GVFSM stuck |
| 9 | Verify `PLR_DIE_LEVEL = 0x0` after all transitions | No spurious Performance Limit Reason from ratio transitions | PLR non-zero -- unexpected throttle during GV change |

### Pass / Fail Criteria

**PASS:** TPMI `UFS_CONTROL` writes accepted and reflected on readback; CURRENT_RATIO matches locked value within 1 convergence window (5M cycles); boundary clamping to P0/Pm caps correct; autonomous mode restores cleanly; PLR = 0x0 throughout.

**FAIL:** Write rejected or not reflected; CURRENT_RATIO does not match locked ratio; no boundary clamping; autonomous mode does not restore; PLR non-zero.

### Post-Process

Save: UFS_HEADER caps, UFS_CONTROL baseline, UFS_STATUS.CURRENT_RATIO snapshots at each step (lock mid, lock max, lock min, restore), PLR_DIE_LEVEL values for both CBBs.

### Reference Documents

- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#ccf-gv) -- GVFSM, ratio locking via UFS_CONTROL
- [DMR CBB TPMI Support](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_TPMI/cbb_tpmi.html) -- UFS_CONTROL MAX_RATIO/MIN_RATIO field encoding, UFS_STATUS.CURRENT_RATIO
- [Architectural TPMI Interface](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html#dmr-family) -- TPMI cluster layout
- [Uncore Frequency Scaling HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/Hierarchical%20UFS/HPM_UFS.html#bios-control) -- UFS_CONTROL pin-to-ratio mechanism
- [Fabric DVFS KB](../../../pm_features/fabric_dvfs/fabric_dvfs_main.md) -- CBB CCF ring context, GVFSM description
- [CBB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html) -- CBB PM feature index
- Related script: `pm/pss/dvfs/tpmi_fabric_gv.py` (implements TPMI-driven fabric GV)

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable -- CBB CCF GV TPMI control present on NWP**

CBB TPMI UFS_CONTROL register is accessible on NWP via `sv.socket0.cbbN.base.tpmi.ufs_control`. NWP has 2 CBBs (cbb0, cbb1), each managed independently. NWP CCF P0 cap = ratio 22 (2.2 GHz); Pm floor = ratio 8 (800 MHz). Lock test ratio = 0x12 = 18 (1.8 GHz).

Tags: `CBB CCF`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### UFS_CONTROL Bit Field Layout (NWP)

| Field | Bits | Encoding | Purpose |
|-------|------|----------|---------|
| MAX_RATIO | [14:8] | 7-bit, 100 MHz/step | Upper CCF freq limit |
| MIN_RATIO | [21:15] | 7-bit, 100 MHz/step | Lower CCF freq limit |
| ELC_LOW_RATIO | [28:22] | 7-bit | ELC Low floor |
| Pin mode | MAX = MIN | Both equal | Disables autonomous DVFS; GVFSM locked |
| Autonomous mode | MAX > MIN | Normal range | GVFSM driven by BW heuristics |

### Key Namednodes Paths (NWP)

| Register | NWP Path | Purpose |
|----------|----------|---------|
| UFS_HEADER | `sv.socket0.cbbN.base.tpmi.ufs_header` | Fused P0/Pm caps |
| UFS_CONTROL | `sv.socket0.cbbN.base.tpmi.ufs_control` | MAX_RATIO, MIN_RATIO write target |
| UFS_STATUS | `sv.socket0.cbbN.base.tpmi.ufs_status` | CURRENT_RATIO readback |
| PLR_DIE_LEVEL | `sv.socket0.cbbN.base.tpmi.plr_die_level` | Perf Limit Reason check |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Iterate both CBBs | `for cbb in sv.sockets.cbbs:` |
| 2 | Lock ratio | `cbb.base.tpmi.ufs_control.max_ratio.write(0x12); cbb.base.tpmi.ufs_control.min_ratio.write(0x12)` |
| 3 | Wait convergence | `cli.run_command("emu.engine.wait-for-cycle -relative 5000000")` |
| 4 | Read back | `cbb.base.tpmi.ufs_status.current_ratio.read()` -- expect 0x12 |
| 5 | Restore | Write original MAX/MIN from baseline values |

### Pass Criteria

TPMI writes reflected; CURRENT_RATIO = locked value after convergence; boundary clamped; autonomous restore clean; PLR = 0x0.
