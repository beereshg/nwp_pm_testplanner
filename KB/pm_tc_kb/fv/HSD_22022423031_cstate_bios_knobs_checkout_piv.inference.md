# Deep Analysis: CState Bios_knobs checkout PIV

| Field | Value |
|-------|-------|
| **HSD ID** | 22022423031 |
| **Title** | CState Bios_knobs checkout PIV |
| **Date** | 2026-07-03 |
| **Target Program** | NWP (Newport) |
| **Segment** | FV |
| **TPF** | Core C1/C6 (Entry/Exit/Residency) |
| **TCD** | CState C6 basic functionality |
| **Status** | open |
| **Val Environment** | emulation.hsle |
| **Owner Team** | pss.val |
| **Automation** |  |

---

## Test Case Intent

Verify that C-state BIOS knobs propagate correctly from BIOS configuration into NWP PCode and hardware registers. BIOS knobs control C-state policy: C6Enable, C1AutoDemotion, C1AutoUnDemotion, MonitorMWait, ProcessorC1eEnable. Each must take effect in the correct hardware register on all 96 NWP cores.

---

## Section A: NWP Disposition

**Disposition: Runnable_On_NWP**

Core C-states are fully supported on NWP (PantherCove PNC). NWP has 2 CBBs × 48 cores (96 total) vs DMR up to 4 CBBs × 64 cores. PkgC6 is ZBB on NWP — any test must verify PC6 residency stays at 0. Key NWP CBB loop adaptation: `range(4)→range(2)`, core loops: `range(64)→range(48)`. Register paths prefix: `sv.socket0.cbb{0,1}.*`.

---

## Section B: NWP Test Procedure

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP silicon or VP; BIOS with C-state knobs exposed. |
| Knobs to test | C6Enable, C1AutoDemotion, C1AutoUnDemotion, MonitorMWait, ProcessorC1eEnable. |
| PythonSV | `sv.socket0.cbb{i}.core[c].CLOCK_CST_CONFIG_CONTROL` per-core accessible on sv.socket0.cbb{0,1}.*. |
| BIOS tool | XmlCli or UEFI knob programming interface. |

### Test Steps

| Step | Action | Expected Result (PASS) | Failure Indication |
|------|--------|----------------------|-------------------|
| 1 | Set C6Enable=1; reboot. Read CLOCK_CST_CONFIG_CONTROL.c6_state_enable across all 96 cores. | All cores: c6_state_enable=1. | Any core showing c6_state_enable=0. |
| 2 | Set C1AutoDemotion=1; verify c1_state_auto_demotion_enable bit per-core. | All 96 cores: demotion bit=1. | Bit mismatch on any core. |
| 3 | Set C1AutoUnDemotion=1; verify enc1undemotion bit. | enc1undemotion=1 on all cores. | enc1undemotion=0 on any core. |
| 4 | Set MonitorMWait=0; verify MISC_ENABLES.enable_monitor_fsm=0 (MSR 0x1A0 bit[18]). | enable_monitor_fsm=0 on all cores. | Bit still set after knob change. |
| 5 | Set ProcessorC1eEnable=1; verify POWER_CTL1.C1E_ENABLE (MSR 0x1FC bit[1]). | C1E_ENABLE=1 (package scope). | C1E_ENABLE=0 after enable. |
| 6 | NWP-specific: Set C6Enable=ON; verify PkgC6 NOT entered (PC6 residency = 0). | MSR 0x3F9 = 0 throughout test. | MSR 0x3F9 > 0 — PkgC6 ZBB violated. |

### Health Checks

- No MCA or boot hang after each BIOS knob change.
- All 96 cores reflect correct register state for each knob.
- PC6 residency (MSR 0x3F9) = 0 confirming ZBB.
- PkgC6 ZBB: when C6Enable=ON, PC6 not entered (NWP delta vs DMR).

### Pass / Fail Criteria

- **PASS**: All BIOS knobs reflected in hardware registers across 96 cores; no MCA; PC6 residency=0.

- **FAIL**: Any register mismatch; MCA; boot hang; PC6 residency>0.

---

## Section C: NWP Delta Impact

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBB count | Up to 4 | **2** | Loop: `range(4)→range(2)` |
| Cores per CBB | 64 | **48** | Loop: `range(64)→range(48)` |
| Total cores | 256 | **96** | Adjust all-core workload scale |
| PkgC6 | Supported | **ZBB** | PC6 residency must stay 0 |
| Register prefix | `cbb{0..3}` | **`cbb{0,1}`** | 2-CBB namespace |

---

## Section D: Spec Refs

- [Core C-state HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_C_States/Core_C_States_HAS.html)
- [ACP PM HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Autonomous%20Core%20Perimeter/Autonomous%20Core%20Perimeter%20PM%20HAS.html)
- Intel SDM — MSR 0x3F9 (PkgC6 residency), MSR 0x660-0x669 (core residency)
- HSD TC: https://hsdes.intel.com/appstore/article-one/#/22022423031