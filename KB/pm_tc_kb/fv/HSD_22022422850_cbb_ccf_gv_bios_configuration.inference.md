# Deep Analysis: CBB CCF GV BIOS Configuration

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422850](https://hsdes.intel.com/appstore/article-one/#/22022422850) |
| **Title** | CBB CCF GV BIOS Configuration |
| **Status** | open |
| **Owner** | bg3 |
| **Val Environment** | silicon, virtual_platform |
| **Feature** | Fabric DVFS / CBB CCF GV |
| **Parent TCD** | [22022421165](https://hsdes.intel.com/appstore/article-one/#/22022421165) |
| **KB last updated** | 2026-06-25 |

---

## Test Case Intent

**Objective:** Verify that BIOS correctly programs the CBB CCF (Converged Coherent Fabric) GV (working-point transition) TPMI control registers for each CBB die. Validate that all CCF GV BIOS knobs are accessible and writable, that the programmed values are within valid ranges, and that PCode interprets and enforces the BIOS-configured limits correctly at runtime.

**CBB CCF GV Context:** The CCF ring is the high-speed coherency fabric within each CBB die, operating at 800-2000 MHz. CBB PCode manages CCF frequency and voltage independently per CBB via the GVFSM (GV Finite State Machine). BIOS programs the CCF GV operating constraints (max/min ratios, ELC thresholds) into the TPMI UFS_CONTROL register before OS handoff. On NWP, CBB CCF Ring DVFS is **present and functional** (unlike IMH UFS which is ZBB'd for customer SKUs).

### Pre-Conditions

| Pre-Condition | Expected State | Failure Indication |
|---------------|---------------|-------------------|
| System booted to OS | BIOS CPL4 complete; PCode initialized | System hangs or resets |
| TPMI accessible per CBB | `sv.socketX.cbbN.base.tpmi.ufs_control` readable | TPMI not initialized by BIOS |
| CCF GV BIOS knobs configured | Non-default MAX_RATIO / MIN_RATIO set or defaults verified | BIOS did not program TPMI UFS_CONTROL |
| PCode running CCF GVFSM | `ufs_status.current_ratio` non-zero on each CBB | PCode not running CCF GV management |
| Python-SV available | `import namednodes; sv = namednodes.sv` succeeds | PythonSV not connected |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | For each CBB, read `UFS_HEADER` — verify `INTERFACE_VERSION=0x03` and `AUTONOMOUS_UFS_DISABLED=0` | Version=3; CCF GV enabled per CBB | `AUTONOMOUS_UFS_DISABLED=1` — CCF GV incorrectly disabled |
| 2 | Read `UFS_CONTROL.MAX_RATIO` per CBB | Non-zero value <= 20 (2000 MHz / 100 MHz steps) | Zero — BIOS did not program max ratio |
| 3 | Read `UFS_CONTROL.MIN_RATIO` per CBB | Non-zero value >= 8 (800 MHz floor); MIN < MAX | MIN=0 or MIN >= MAX — invalid range |
| 4 | Read `UFS_CONTROL.ELC_LOW_RATIO` per CBB | Non-zero; typically 8 (800 MHz) in low-power mode | Zero — ELC Low floor not configured |
| 5 | Read `UFS_CONTROL.UFS_THROTTLE_MODE` per CBB | 0=OFF (normal) or 1=Clamp; consistent with BIOS knob | Unexpected value — BIOS knob mismatch |
| 6 | Read `UFS_ADV_CONTROL_1.CCF_RAPL_LINE_SLOPE` per CBB | Non-zero slope programmed | Zero — RAPL line for CCF not configured |
| 7 | Write new MAX_RATIO via BIOS knob override tool and reboot; verify TPMI updated | New MAX_RATIO reflects BIOS knob value | TPMI not updated — BIOS override not working |
| 8 | Verify PCode enforces MAX_RATIO: apply CCF workload; check `UFS_STATUS.CURRENT_RATIO` <= MAX_RATIO | Current ratio stays at or below BIOS-configured max | CCF exceeds MAX_RATIO — PCode not enforcing |
| 9 | Verify PCode enforces MIN_RATIO: enter low-utilization state; check `UFS_STATUS.CURRENT_RATIO` >= MIN_RATIO | Current ratio stays at or above BIOS-configured min | CCF drops below MIN_RATIO — PCode not enforcing |

### Pass / Fail Criteria

**PASS:** All TPMI UFS_CONTROL fields accessible and non-zero per CBB; MAX_RATIO > MIN_RATIO; `AUTONOMOUS_UFS_DISABLED=0`; PCode-observed `CURRENT_RATIO` stays within [MIN_RATIO, MAX_RATIO]; BIOS knob override reflected after reboot.

**FAIL:** Any TPMI UFS_CONTROL field is zero or invalid; `AUTONOMOUS_UFS_DISABLED=1`; `CURRENT_RATIO` violates BIOS-configured range; BIOS override not reflected in TPMI.

### Post-Process

Save: UFS_CONTROL and UFS_STATUS register dumps for all CBBs (before/after BIOS override), PCode log showing GVFSM transitions, UFS_STATUS.CURRENT_RATIO samples under load.

### Reference Documents

- [CBB CCF Power Management HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html#ccf-gv) -- CCF GV execution flow, GVFSM, V-first/F-first transitions
- [DMR CBB TPMI Support](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_TPMI/cbb_tpmi.html) -- UFS_HEADER, UFS_STATUS, UFS_CONTROL, UFS_ADV_CONTROL definitions
- [Architectural TPMI Interface](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html#dmr-family) -- TPMI cluster layout and field encoding
- [BIOS CPU P-State Knobs](https://docs.intel.com/documents/System-firmware-bios/Domain/ServerCpuPm/Index/CPU%20&%20PM%20BIOS%20Knobs/BiosKnobs.html#figure-cpu-p-state-control) -- BIOS knob definitions for CCF GV
- [CBB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html) -- CBB PM feature index
- [Uncore Frequency Scaling HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/Hierarchical%20UFS/HPM_UFS.html#bios-control) -- BIOS control flow for hierarchical UFS
- [Fabric DVFS KB](../../../pm_features/fabric_dvfs/fabric_dvfs_main.md) -- CBB CCF ring context, NWP topology

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable — CBB CCF GV present on NWP**

CBB CCF Ring DVFS is **not ZBB'd** on NWP. The CBB PCode GVFSM runs independently per CBB and manages CCF frequency/voltage. BIOS must correctly initialize UFS_CONTROL before OS handoff. NWP has 2 CBBs (vs DMR's 4); iterate both cbb0 and cbb1.

NWP CCF target: **2.2 GHz** for full 460 GB/s fabric bandwidth.

Tags: `CBB CCF`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### Key TPMI Paths (NWP)

| Register | NWP namednodes path | Purpose |
|----------|---------------------|---------|
| UFS_HEADER | `sv.socket0.cbbN.base.tpmi.ufs_header` | CCF GV capability / disabled flag |
| UFS_STATUS | `sv.socket0.cbbN.base.tpmi.ufs_status` | Current CCF ratio + voltage |
| UFS_CONTROL | `sv.socket0.cbbN.base.tpmi.ufs_control` | BIOS-programmed limits |
| UFS_ADV_CONTROL_1 | `sv.socket0.cbbN.base.tpmi.ufs_adv_control_1` | RAPL line slopes for CCF |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Iterate both CBBs | `for cbb in sv.sockets.cbbs:` |
| 2 | Read TPMI UFS_CONTROL fields | `cbb.base.tpmi.ufs_control.max_ratio.read()` |
| 3 | Read UFS_STATUS current ratio | `cbb.base.tpmi.ufs_status.current_ratio.read()` |
| 4 | Apply PEGA workload and re-read | `pega.coreRatioSingleShot('all','all','all', p0_ratio)` |
| 5 | Verify BIOS override via xmlcli | `ram.CbbCcfGvMaxRatio.getValue()` (knob name TBC with BIOS team) |

### Pass Criteria

All TPMI UFS_CONTROL fields accessible and within spec range; CURRENT_RATIO bounded by [MIN_RATIO, MAX_RATIO]; BIOS knob override reflected post-reboot.
