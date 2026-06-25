# Deep Analysis: CBB CCF GV PEGA Injection

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422851](https://hsdes.intel.com/appstore/article-one/#/22022422851) |
| **Title** | CBB CCF GV PEGA Injection |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | Fabric DVFS / CBB CCF GV -- PEGA-driven transitions |
| **Parent TCD** | [22022421168](https://hsdes.intel.com/appstore/article-one/#/22022421168) |
| **KB last updated** | 2026-06-25 |

---

## Test Case Intent

**Objective:** Verify that CBB CCF ring frequency responds correctly to synthetic PEGA (Power Engine Generic Agent) mailbox injections. PEGA injects P-state requests for fabric domains (meshgv, iagv, memgv, iogv) directly into PCode via the B2P mailbox, bypassing the normal bandwidth-heuristic slow loop. This validates the GVFSM (GV Finite State Machine) end-to-end path: mailbox reception, GVFSM state transition, PLL settling, and status reporting via TPMI UFS_STATUS.CURRENT_RATIO.

**PEGA API:** `pega_mailbox.pega_pstate(iagv, meshgv, memgv, iogv, rearm, act2)` where `meshgv=0` requests P0 (max CCF, ~2.2 GHz) and `meshgv="rand"` injects a stress/random GV request. Implemented in `pm/pss/pega/pega_fabric_gv.py`.

### Pre-Conditions

| Pre-Condition | Expected State | Failure Indication |
|---------------|---------------|-------------------|
| System booted to XOS/SVOS | BIOS CPL4 complete; PCode running CCF GVFSM | System not booted or hangs |
| BIOS: ProcessorHWPMEnable = 1 | HWP initialized (required for PEGA mailbox) | PEGA injection fails at B2P |
| TPMI accessible per CBB | `sv.socket0.cbbN.base.tpmi.ufs_status.current_ratio` readable | TPMI path not valid |
| PEGA mailbox available | `pega_mailbox.pega_pstate()` reachable | Module import error |
| CBB CCF GV enabled | `UFS_HEADER.AUTONOMOUS_UFS_DISABLED = 0` on each CBB | CCF GV disabled -- BIOS config issue |
| System at idle CCF baseline | Initial CURRENT_RATIO readable and non-zero | CCF not running |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Read baseline `UFS_STATUS.CURRENT_RATIO` on cbb0 and cbb1 | Non-zero ratios on both CBBs; note values as baseline | Zero ratio -- GVFSM not running |
| 2 | Inject PEGA stress request: `pega_pstate(meshgv="rand", iagv="rand", memgv="rand", iogv="rand")` | Command accepted (no B2P error); wait 30M cycles | B2P NAK or mailbox error |
| 3 | Read `UFS_STATUS.CURRENT_RATIO` on all CBBs after PEGA stress injection | At least one CBB shows ratio change from baseline | No ratio change -- GVFSM not responding to PEGA |
| 4 | Inject PEGA low request: `pega_pstate(meshgv=0, iagv=0, memgv=0, iogv=0)` (requests P0/max) | Command accepted; wait 30M cycles | B2P error or mailbox unresponsive |
| 5 | Read `UFS_STATUS.CURRENT_RATIO` on all CBBs after P0 injection | Ratios increase toward max (NWP CCF P0 = 22, 2.2 GHz); each CBB reflects the P0 request | Ratio unchanged or wrong direction -- GVFSM not honoring mailbox |
| 6 | Release PEGA: `pega_pstate(rearm=0)` and wait 2s for autonomous recovery | Ratios return to bandwidth-heuristic-driven value; no stuck GVFSM | Ratios stuck at injected value -- GVFSM hung after release |
| 7 | Verify `PLR_DIE_LEVEL` on each CBB = 0x0 | No spurious Performance Limit Reason from PEGA transition | PLR non-zero -- unexpected throttle event during GV transition |
| 8 | Verify `UFS_STATUS` GVFSM busy/done flags clear (not stuck) | GVFSM `busy` bit = 0 after transition settled | Busy bit stuck -- GVFSM hung state |

### Pass / Fail Criteria

**PASS:** PEGA mailbox accepted without error; at least one CBB shows ratio change after stress injection; P0 injection drives ratio toward 2.2 GHz; autonomous CCF ratio recovery after PEGA release; PLR_DIE_LEVEL = 0x0; GVFSM not stuck.

**FAIL:** B2P mailbox rejects PEGA command; no ratio change after injection; GVFSM stuck (busy bit set); ratio does not recover after release; PLR non-zero indicating throttle during GV transition.

### Post-Process

Save: UFS_STATUS.CURRENT_RATIO snapshots (baseline, after stress, after P0, after release), B2P mailbox status, PLR_DIE_LEVEL values, GVFSM busy/done register state for both CBBs.

### Reference Documents

- [CBB PEGA HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html) -- CBB Power Event Generation Architecture, B2P mailbox injection flow
- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#switching-between-fast-gv-drainless-gv) -- GVFSM states, V-first/F-first transitions
- [DMR CBB TPMI Support](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_TPMI/cbb_tpmi.html) -- UFS_STATUS.CURRENT_RATIO, GVFSM busy/done fields
- [PEGA Architecture Rev 0.75](https://wiki.ith.intel.com/display/ServerPcode/PEGA) -- PEGA mailbox command format, rearm behavior
- [Uncore Frequency Scaling HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/Hierarchical%20UFS/HPM_UFS.html#bios-control) -- UFS BIOS control, AUTONOMOUS_UFS_DISABLED
- [Fabric DVFS KB](../../../pm_features/fabric_dvfs/fabric_dvfs_main.md) -- CBB CCF ring DVFS context, GVFSM description
- Test script: `pm/pss/pega/pega_fabric_gv.py` (implements this TC flow)

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable -- CBB CCF GV and PEGA both present on NWP**

CBB PCode GVFSM and PEGA mailbox are inherited from DMR CBB shared source. NWP has 2 CBBs (cbb0, cbb1); both must be validated. NWP CCF P0 = 2.2 GHz (ratio = 22). PEGA `meshgv=0` requests P0 for CCF ring.

The existing test script `pm/pss/pega/pega_fabric_gv.py` implements this TC flow and follows the verified emulation pattern (PM_INFO:: prefix, cli stabilization).

Tags: `CBB CCF`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### Key Namednodes Paths (NWP)

| Register | NWP Path | Purpose |
|----------|----------|---------|
| UFS_STATUS.CURRENT_RATIO | `sv.socket0.cbbN.base.tpmi.ufs_status.current_ratio` | Observed CCF ring ratio after GVFSM settles |
| PLR_DIE_LEVEL | `sv.socket0.cbbN.base.tpmi.plr_die_level` | Perf Limit Reason per CBB |
| ACP_PERF_LIMIT | `sv.socket0.cbbN.base.punit_regs.punit_pmsb.pmsb_pcu.acp_perf_limit` | ACP power limit post-GV |
| UFS_ADV_CONTROL_1 | `sv.socket0.cbbN.base.tpmi.ufs_adv_control_1` | CCF RAPL line slope (should be unchanged) |

### PEGA Injection API

```python
from diamondrapids.pm.pss.mailbox import pega_mailbox
# Stress injection (provoke random GV change)
pega_mailbox.pega_pstate(iagv="rand", meshgv="rand", memgv="rand", iogv="rand")
# P0 request (drive CCF to max, ~2.2 GHz)
pega_mailbox.pega_pstate(iagv=0, meshgv=0, memgv=0, iogv=0)
# Release
pega_mailbox.pega_pstate(rearm=0)
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run existing script | `python pm/pss/pega/pega_fabric_gv.py` |
| 2 | Iterate both CBBs | `for cbb in sv.sockets.cbbs:` |
| 3 | Check baseline ratio | `cbb.base.tpmi.ufs_status.current_ratio.read()` |
| 4 | Inject PEGA | `pega_mailbox.pega_pstate(meshgv="rand")` |
| 5 | Wait (emulation) | `cli.run_command("emu.engine.wait-for-cycle -relative 10000000")` x3 |
| 6 | Verify ratio changed | Assert at least one CBB ratio != baseline |

### Pass Criteria

PEGA injection accepted; ratio changes per injection; PLR = 0x0; autonomous recovery after release; GVFSM not stuck.
