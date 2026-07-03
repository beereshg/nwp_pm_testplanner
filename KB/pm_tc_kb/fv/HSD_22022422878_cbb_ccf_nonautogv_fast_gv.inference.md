# Deep Analysis: CBB CCF NonAutoGV Mode - Fast GV

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422878](https://hsdes.intel.com/appstore/article-one/#/22022422878) |
| **Title** | CBB CCF NonAutoGV Mode - Fast GV |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | CBB CCF -- Non-Autonomous GV mode with drainless Fast GV transitions |
| **Parent TCD** | [22022421183](https://hsdes.intel.com/appstore/article-one/#/22022421183) |
| **KB last updated** | 2026-06-25 |

---

## Test Case Intent

**Objective:** Validate CBB CCF Non-Autonomous GV (NonAutoGV) mode and **Fast GV** (drainless frequency transition). In NonAutoGV mode, the TPMI `UFS_CONTROL` is programmed with `UFS_THROTTLE_MODE=0` and `MIN_RATIO=MAX_RATIO=target`, disabling the autonomous BW-heuristic algorithm. The GVFSM continues to run but uses only the RAPL proportional throttle line — no bandwidth-driven adjustments. **Fast GV** is a drainless frequency transition: the CCF ring ratio changes without waiting for outstanding transactions to drain, achieving <1 ms latency versus the normal drain-GV sequence.

**Mode comparison:**

| Mode | UFS_THROTTLE_MODE | MIN/MAX | BW Heuristics | RAPL Line | GV Type | Latency |
|------|------------------|---------|---------------|-----------|---------|---------|
| Autonomous | Any | MIN < MAX | Active | Active | Drain-GV | ~5-10 ms |
| NonAutoGV (pin) | 0 | MIN = MAX | Disabled | Active | Fast GV | <1 ms |
| Clamp | 1 | MIN < MAX | Active | Active | Drain-GV | ~5-10 ms |

### Pre-Conditions

| Pre-Condition | Expected State | Failure Indication |
|---------------|---------------|-------------------|
| System booted to XOS/SVOS | BIOS CPL4; PCode GVFSM running | System not booted |
| TPMI UFS_CONTROL writable | `ufs_control` writes reflected on readback | TPMI write-protected |
| Baseline CCF ratio known | `UFS_STATUS.CURRENT_RATIO` non-zero; GVFSM in autonomous mode | GVFSM not running |
| No active RAPL throttle | RAPL PL1 not constraining CCF below test ratios | RAPL overrides NonAutoGV pin |
| Timing measurement available | `time.time()` or emulation cycle counter for latency check | Cannot measure transition latency |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Read and save baseline `UFS_CONTROL` and `UFS_STATUS.CURRENT_RATIO` on both CBBs | Baseline recorded; autonomous mode (MIN < MAX) confirmed | MIN >= MAX -- already non-autonomous |
| 2 | Enable NonAutoGV on cbb0: write `UFS_THROTTLE_MODE=0`, `MIN_RATIO=MAX_RATIO=0x16` (2.2 GHz pin) | Write accepted; readback matches; `UFS_CONTROL.MIN==MAX=0x16` | Write rejected or mismatch |
| 3 | Wait 50ms and verify `UFS_STATUS.CURRENT_RATIO = 0x16` | GVFSM pins CCF at 2.2 GHz; no BW-heuristic changes | Ratio drifts from 0x16 -- NonAutoGV pin not holding |
| 4 | **Fast GV test:** write new pin `MIN_RATIO=MAX_RATIO=0x10` (1.6 GHz); start timer | Ratio changes from 0x16 to 0x10 in <10 ms (drainless = no transaction drain wait) | Latency >10 ms -- Fast GV not engaged; normal drain-GV used instead |
| 5 | Poll `UFS_STATUS.CURRENT_RATIO` until settled; record transition latency | `CURRENT_RATIO = 0x10` within <10 ms; no intermediate values stuck | Ratio stuck at 0x16 -- GVFSM did not honor new pin |
| 6 | Repeat Fast GV upward: write `MIN_RATIO=MAX_RATIO=0x16` (2.2 GHz); measure latency | Ratio transitions back to 0x16 in <10 ms (V-first still applies on up-transition) | Ratio does not recover -- up-transition Fast GV broken |
| 7 | Repeat steps 2-6 on cbb1 independently | cbb1 pins and transitions independently of cbb0 | cbb1 affected by cbb0 -- inter-CBB coupling in NonAutoGV |
| 8 | **Boundary test:** pin below Pm (write 0x01) | GVFSM clamps to `min_ratio_cap` from UFS_HEADER fuse | No clamping -- below-Pm operation |
| 9 | **Boundary test:** pin above P0 (write 0xFF) | GVFSM clamps to `max_ratio_cap` from UFS_HEADER | No clamping -- above-P0 operation |
| 10 | Restore autonomous mode: write original `UFS_CONTROL` (MIN < MAX); wait 100ms | `CURRENT_RATIO` returns to BW-heuristic-driven value; autonomous DVFS resumes | Ratio stuck at last NonAutoGV pin -- GVFSM stuck in NonAutoGV |
| 11 | Verify `PLR_DIE_LEVEL = 0x0` after all mode transitions | No spurious Performance Limit Reason from NonAutoGV/Fast GV transitions | PLR non-zero -- unexpected throttle during mode switch |

### Pass / Fail Criteria

**PASS:** NonAutoGV pin holds `CURRENT_RATIO` at programmed value; Fast GV transitions (both down and up) complete in <10 ms; boundary clamping to P0/Pm caps correct; per-CBB independence confirmed; autonomous mode restores cleanly; PLR = 0x0 throughout.

**FAIL:** Pin does not hold (ratio drifts); Fast GV latency >10 ms; boundary not clamped; cbb1 affected by cbb0; autonomous mode does not restore; PLR non-zero.

### Post-Process

Save: UFS_CONTROL baseline and each programmed value, UFS_STATUS.CURRENT_RATIO at each step, Fast GV transition latencies (ms), PLR_DIE_LEVEL for both CBBs, UFS_HEADER cap values.

### Reference Documents

- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#switching-between-fast-gv-drainless-gv) -- NonAutoGV mode, Fast GV (drainless) vs drain-GV, UFS_THROTTLE_MODE encoding
- [DMR CBB TPMI Support](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_TPMI/cbb_tpmi.html) -- UFS_CONTROL.UFS_THROTTLE_MODE [1:0], MIN_RATIO, MAX_RATIO fields
- [Architectural TPMI Interface](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html#dmr-family) -- TPMI cluster register layout
- [CBB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html) -- CBB PM feature index
- [Fabric DVFS KB](../../../pm_features/fabric_dvfs/fabric_dvfs_main.md) -- CCF ring DVFS context, GVFSM description

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable -- NonAutoGV and Fast GV present on NWP**

CBB PCode GVFSM supports NonAutoGV mode on NWP via the same TPMI UFS_CONTROL mechanism. NWP: 2 CBBs; each independent. CCF P0 = 0x16 (2.2 GHz). Test ratios: 0x16 (P0), 0x10 (P1-ish), 0x08 (Pm).

Tags: `CBB CCF`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### UFS_CONTROL NonAutoGV Encoding (NWP)

| Field | Bits | NonAutoGV Value | Purpose |
|-------|------|----------------|---------|
| UFS_THROTTLE_MODE | [1:0] | 0 | Disable autonomous BW heuristics |
| MAX_RATIO | [14:8] | target | Pin upper bound |
| MIN_RATIO | [21:15] | = MAX_RATIO | Pin lower bound (MIN=MAX disables DVFS range) |

### Namednodes Paths (NWP)

| Register | NWP Path | Purpose |
|----------|----------|---------|
| UFS_CONTROL | `sv.socket0.cbbN.base.tpmi.ufs_control` | NonAutoGV mode + ratio pin |
| UFS_STATUS | `sv.socket0.cbbN.base.tpmi.ufs_status` | CURRENT_RATIO readback |
| PLR_DIE_LEVEL | `sv.socket0.cbbN.base.tpmi.plr_die_level` | Perf Limit Reason |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Enable NonAutoGV pin | `ufs_control.ufs_throttle_mode.write(0); ufs_control.max_ratio.write(0x16); ufs_control.min_ratio.write(0x16)` |
| 2 | Fast GV down | Write new pin `0x10`; poll `ufs_status.current_ratio` until = 0x10 |
| 3 | Measure latency | `time.time()` delta; expect <10 ms |
| 4 | Iterate both CBBs | `for cbb in sv.sockets.cbbs:` |
| 5 | Restore | Write original UFS_CONTROL value |

### Pass Criteria

NonAutoGV pin holds; Fast GV <10 ms both directions; clamping to P0/Pm; autonomous restores; PLR = 0x0.
