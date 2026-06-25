# TCD: CBB CCF GV PEGA

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421168](https://hsdes.intel.com/appstore/article-one/#/22022421168) |
| **Title** | CBB CCF GV PEGA |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [22022420507 -- CBB CCF Active States](https://hsdes.intel.com/appstore/article-one/#/22022420507) |
| **Feature** | CBB CCF Active States -- GV management |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**CBB CCF GV PEGA** validates the PEGA mailbox path to the CBB CCF GVFSM. PEGA (Power Engine Generic Agent) injects synthetic P-state requests directly into CBB PCode via the B2P mailbox, bypassing the normal bandwidth-heuristic slow loop. This is the primary method for pre-silicon validation of the GVFSM end-to-end path.

### PEGA Injection Flow

```
PEGA Tool / pmutil
  pega_pstate(iagv, meshgv, memgv, iogv, rearm)
         |
         v  B2P Mailbox
  CBB PCode receives P-state request
         |
         v
  GVFSM processes new target ratio
         |  V-first (freq up) / PLL-first (freq down)
         v
  CCF Ring PLL settles at new ratio
         |
         v
  UFS_STATUS.CURRENT_RATIO updated
         |
         v
  HPM 0x1b UPSTREAM_CCF_DESIRED_RATIO updated -> IMH Primecode
```

### PEGA Encoding for CCF (meshgv)

| meshgv value | CCF ring target |
|-------------|----------------|
| 0 | P0 (max freq, 2.2 GHz on NWP) |
| "rand" | Random stress ratio (GVFSM stress test) |
| N > 0 | Specific ratio floor |

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422851 -- CBB CCF GV PEGA Injection](https://hsdes.intel.com/appstore/article-one/#/22022422851) | PEGA mailbox injection, GVFSM ratio change, PLR clean, autonomous recovery |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| B2P Mailbox | `pega_mailbox.pega_pstate(meshgv=...)` | PEGA injection API |
| TPMI UFS_STATUS | `sv.socket0.cbbN.base.tpmi.ufs_status.current_ratio` | Observed CCF ratio after GVFSM settles |
| HPM 0x1b | `UPSTREAM_CCF_DESIRED_RATIO` | CCF desired ratio sent to Primecode |
| TPMI PLR_DIE_LEVEL | `sv.socket0.cbbN.base.tpmi.plr_die_level` | Perf Limit Reason (must = 0x0) |

---

## Section 3: Reset, Power, and Clocking

- CCF GV state resets on warm reset; BIOS re-programs UFS_CONTROL during TPMI_INIT at next boot
- RING PLL and FIVR initialize to boot ratio; PCode GVFSM takes control after PH6
- UFS_STATUS.CURRENT_RATIO reflects live PLL state; reads are always current (no caching)
- V-first for frequency increase; PLL-first for frequency decrease -- mandatory for stable operation

---

## Section 4: Programming Model

PEGA injection requires `ProcessorHWPMEnable=1` BIOS knob (HWP init) for the B2P mailbox to be operational. The `pega_mailbox.pega_pstate()` API from `diamondrapids.pm.pss.mailbox.pega_mailbox` is the recommended injection method. On emulation, use `cli.run_command('emu.engine.wait-for-cycle -relative 10000000')` × 3 for GVFSM convergence.

---

## Section 5: Operational Behavior

The CBB CCF GVFSM runs autonomously each slow-loop (~1 ms) when in autonomous mode (MAX_RATIO > MIN_RATIO). The GVFSM:
1. Reads BW telemetry (CBO/SBO) and RAPL/RACL line from Primecode
2. Computes new CCF frequency target
3. Clamps to [MIN_RATIO, MAX_RATIO] from UFS_CONTROL
4. Executes V-first or PLL-first GV transition via FIVR + PLL
5. Updates UFS_STATUS.CURRENT_RATIO and CURRENT_VOLTAGE
6. Sends updated ratio to Primecode via HPM 0x1b

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| BIOS programs MAX < MIN | PCode reverts to fuse defaults; no GVFSM operation |
| Ratio request above P0 cap | Silently clamped to UFS_HEADER.MAX_RATIO_CAP |
| Ratio request below Pm floor | Silently clamped to UFS_HEADER.MIN_RATIO_CAP |
| GVFSM stuck (busy bit set) | System hang risk; detect via UFS_STATUS GVFSM status bits |
| PEGA injection with HWP disabled | B2P mailbox rejects -- requires BIOS HWP enable |

---

## Section 7: Security / Safety / Policy

- TPMI UFS_CONTROL may be locked by BIOS before OS handoff; runtime modifications require BIOS unlock
- PEGA injection requires privilege level; restricted in production OS environments
- VF curves are fused at manufacturing; no runtime override is permitted for customer SKUs

---

## Section 8: References

- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html) -- GVFSM, GV execution flow, V-first/F-first
- [DMR CBB TPMI Support](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_TPMI/cbb_tpmi.html) -- UFS_CONTROL, UFS_STATUS, UFS_HEADER field definitions
- [CBB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html) -- CBB PM feature index
- [Architectural TPMI Interface](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html#dmr-family) -- TPMI cluster layout
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP CCF ring scope
- [CBB PEGA HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html) -- PEGA mailbox command format, rearm behavior
- [PEGA Architecture Wiki](https://wiki.ith.intel.com/display/ServerPcode/PEGA) -- PEGA P-state request encoding
