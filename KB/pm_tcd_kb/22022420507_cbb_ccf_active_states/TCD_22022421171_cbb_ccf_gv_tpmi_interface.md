# TCD: CBB CCF GV TPMI Interface

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421171](https://hsdes.intel.com/appstore/article-one/#/22022421171) |
| **Title** | CBB CCF GV TPMI Interface |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [22022420507 -- CBB CCF Active States](https://hsdes.intel.com/appstore/article-one/#/22022420507) |
| **Feature** | CBB CCF Active States -- GV management |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**CBB CCF GV TPMI Interface** covers runtime control of the CCF ring frequency via TPMI `UFS_CONTROL` register writes. The TPMI interface provides OS/validation visibility and control of CCF operating range. The key validation scenario is **ratio locking**: setting `MAX_RATIO = MIN_RATIO` collapses the GVFSM operating window to a single point, effectively pinning the CCF ring at a fixed frequency.

### Ratio Lock Mechanism

```
Normal Autonomous Mode:
  UFS_CONTROL.MAX_RATIO = 0x16 (2.2 GHz)
  UFS_CONTROL.MIN_RATIO = 0x08 (800 MHz)
  GVFSM freely selects within [MIN, MAX] based on BW heuristics

Ratio Lock (pin) Mode:
  UFS_CONTROL.MAX_RATIO = 0x12  (1.8 GHz -- test ratio)
  UFS_CONTROL.MIN_RATIO = 0x12  (same value)
  GVFSM has single-point window -> holds CCF at 1.8 GHz
  UFS_STATUS.CURRENT_RATIO -> 0x12 after convergence (~5M cycles)

Restore Autonomous:
  Write back original MAX > MIN values
  GVFSM resumes BW-heuristic-driven frequency
```

### UFS_CONTROL Field Encoding

| Field | Bits | Encoding |
|-------|------|---------|
| MAX_RATIO | [14:8] | 7-bit, 100 MHz/step; pin = set equal to MIN |
| MIN_RATIO | [21:15] | 7-bit, 100 MHz/step; pin = set equal to MAX |
| UFS_THROTTLE_MODE | [1:0] | 0=autonomous, 1=clamp |

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422859 -- CBB CCF GV TPMI Request](https://hsdes.intel.com/appstore/article-one/#/22022422859) | TPMI ratio lock (MAX=MIN), GVFSM pin behavior, boundary clamping, autonomous restore |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| TPMI UFS_CONTROL | `sv.socket0.cbbN.base.tpmi.ufs_control` | MAX_RATIO, MIN_RATIO write target |
| TPMI UFS_STATUS | `sv.socket0.cbbN.base.tpmi.ufs_status` | CURRENT_RATIO readback after pin |
| TPMI UFS_HEADER | `sv.socket0.cbbN.base.tpmi.ufs_header` | Fused P0/Pm caps (boundary check) |
| TPMI PLR_DIE_LEVEL | `sv.socket0.cbbN.base.tpmi.plr_die_level` | Perf Limit Reason (= 0x0 expected) |

---

## Section 3: Reset, Power, and Clocking

- CCF GV state resets on warm reset; BIOS re-programs UFS_CONTROL during TPMI_INIT at next boot
- RING PLL and FIVR initialize to boot ratio; PCode GVFSM takes control after PH6
- UFS_STATUS.CURRENT_RATIO reflects live PLL state; reads are always current (no caching)
- V-first for frequency increase; PLL-first for frequency decrease -- mandatory for stable operation

---

## Section 4: Programming Model

TPMI writes to UFS_CONTROL take effect at the next GVFSM slow-loop iteration (~1 ms latency). For emulation convergence, wait 5M cycles after write before reading back UFS_STATUS. Writes that violate fused boundaries (above P0 cap or below Pm floor) are silently clamped by PCode to the fused limit.

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
- [Uncore Frequency Scaling HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/Hierarchical%20UFS/HPM_UFS.html#bios-control) -- UFS_CONTROL pin-to-ratio mechanism
