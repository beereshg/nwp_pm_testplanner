# TCD: CBB CCF GV BIOS Configuration

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421165](https://hsdes.intel.com/appstore/article-one/#/22022421165) |
| **Title** | CBB CCF GV BIOS Configuration |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [22022420507 -- CBB CCF Active States](https://hsdes.intel.com/appstore/article-one/#/22022420507) |
| **Feature** | CBB CCF Active States -- GV management |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**CBB CCF GV BIOS Configuration** covers the boot-time initialization of CCF ring frequency boundaries by BIOS through the TPMI `UFS_CONTROL` register. During TPMI_INIT (PH1.x of the boot flow), BIOS writes the maximum and minimum allowed CCF ring ratios, ELC thresholds, and throttle mode. CBB PCode GVFSM then uses these as hard limits for all autonomous frequency decisions.

### Boot-Time Configuration Flow

```
Boot Time (BIOS CPL3)
  BIOS reads fused P0/Pm from UFS_HEADER
  BIOS writes UFS_CONTROL:
    MAX_RATIO [14:8]   = max allowed CCF freq (e.g. 0x16 = 2.2 GHz)
    MIN_RATIO [21:15]  = min allowed CCF freq (e.g. 0x08 = 800 MHz)
    ELC_LOW_RATIO      = ELC Low floor (e.g. 0x08 = 800 MHz)
    UFS_THROTTLE_MODE  = 0 (autonomous) or 1 (clamp)
    ELC thresholds
  BIOS completes CPL4 -> PCode takes control
  PCode GVFSM reads UFS_CONTROL -> starts autonomous CCF frequency management
  All CCF freq decisions bounded by [MIN_RATIO, MAX_RATIO]
```

### Key BIOS Knobs

| Knob | Controls | Default |
|------|---------|---------|
| CBB CCF GV Max Ratio | `UFS_CONTROL.MAX_RATIO` | P0 from fuse (2.2 GHz on NWP) |
| CBB CCF GV Min Ratio | `UFS_CONTROL.MIN_RATIO` | Pm from fuse (800 MHz) |
| CCF ELC Low Threshold | `UFS_CONTROL.ELC_LOW_THRESHOLD` | 10% C0 utilization |
| CCF ELC High Threshold | `UFS_CONTROL.ELC_HIGH_THRESHOLD` | 95% C0 utilization |
| CCF Throttle Mode | `UFS_CONTROL.UFS_THROTTLE_MODE` | 0 = autonomous |

### NWP-Specific Context

- NWP: 2 CBBs; each has independent UFS_CONTROL -- BIOS must program both
- NWP CCF P0 = 2.2 GHz (ratio 22 = 0x16); Pm = 800 MHz (ratio 8 = 0x08)
- `UFS_HEADER.AUTONOMOUS_UFS_DISABLED` must = 0 for autonomous GV

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422850 -- CBB CCF GV BIOS Configuration](https://hsdes.intel.com/appstore/article-one/#/22022422850) | TPMI UFS_CONTROL field accessibility, BIOS override, PCode enforcement of BIOS-programmed limits |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| TPMI UFS_HEADER | `sv.socket0.cbbN.base.tpmi.ufs_header` | Fused P0/Pm caps; AUTONOMOUS_UFS_DISABLED flag |
| TPMI UFS_CONTROL | `sv.socket0.cbbN.base.tpmi.ufs_control` | BIOS-programmed MAX/MIN/ELC/mode |
| TPMI UFS_STATUS | `sv.socket0.cbbN.base.tpmi.ufs_status` | CURRENT_RATIO -- PCode-observed freq |
| BIOS knob tool | xmlcli / xmlcli override tool | Runtime BIOS knob read/write |

---

## Section 3: Reset, Power, and Clocking

- CCF GV state resets on warm reset; BIOS re-programs UFS_CONTROL during TPMI_INIT at next boot
- RING PLL and FIVR initialize to boot ratio; PCode GVFSM takes control after PH6
- UFS_STATUS.CURRENT_RATIO reflects live PLL state; reads are always current (no caching)
- V-first for frequency increase; PLL-first for frequency decrease -- mandatory for stable operation

---

## Section 4: Programming Model

BIOS programs UFS_CONTROL during TPMI_INIT before handoff to OS. PCode then reads UFS_CONTROL at first slow-loop iteration to establish GV operating range. If BIOS does not program UFS_CONTROL, PCode may use fallback defaults (fuse values). BIOS override tool (`xmlcli`) can be used to change BIOS knobs post-boot for validation; requires reboot to take effect.

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
- [BIOS CPU P-State Knobs](https://docs.intel.com/documents/System-firmware-bios/Domain/ServerCpuPm/Index/CPU%20&%20PM%20BIOS%20Knobs/BiosKnobs.html#figure-cpu-p-state-control) -- CCF GV BIOS knob definitions
