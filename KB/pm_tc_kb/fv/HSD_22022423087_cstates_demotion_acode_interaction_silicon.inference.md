# Deep Analysis: CStates: Demotion: Acode interaction_silicon

| Field | Value |
|-------|-------|
| **HSD ID** | 22022423087 |
| **Title** | CStates: Demotion: Acode interaction_silicon |
| **Date** | 2026-07-03 |
| **Target Program** | NWP (Newport) |
| **Segment** | FV |
| **TPF** | C-State Demotion/Undemotion |
| **TCD** | CStates: C6/C1 Demotion/Undemotion Configuration |
| **Status** | open |
| **Val Environment** | virtual_platform |
| **Owner Team** | soc.pm |
| **Automation** | pm\focus\cstate_focus.py |

---

## Test Case Intent

Verify C-state demotion/undemotion policy on NWP. When a core requests a deep C-state (C6A/C6S) but pCode determines conditions are not met (e.g. pending interrupts, short idle prediction), it demotes to a shallower state (C1 or C3). Undemotion re-enables deeper C-states when conditions improve. This TC validates the demotion policy gates and register state.

---

## Section A: NWP Disposition

**Disposition: Runnable_On_NWP**

Core C-states are fully supported on NWP (PantherCove PNC). NWP has 2 CBBs × 48 cores (96 total) vs DMR up to 4 CBBs × 64 cores. PkgC6 is ZBB on NWP — any test must verify PC6 residency stays at 0. Key NWP CBB loop adaptation: `range(4)→range(2)`, core loops: `range(64)→range(48)`. Register paths prefix: `sv.socket0.cbb{0,1}.*`.

---

## Section B: NWP Test Procedure

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP silicon or VP; SVOS booted. |
| BIOS | C1AutoDemotion=1; C1AutoUnDemotion=1 (demotion enabled). |
| PythonSV | `sv.socket0.cbb{i}.core[c].CLOCK_CST_CONFIG_CONTROL` and demotion policy registers accessible. |
| Workload | Short-burst interrupt pattern to trigger demotion; sustained idle to trigger undemotion. |

### Test Steps

| Step | Action | Expected Result (PASS) | Failure Indication |
|------|--------|----------------------|-------------------|
| 1 | Enable C1 auto-demotion (BIOS knob or MSR). Confirm CLOCK_CST_CONFIG_CONTROL.c1_state_auto_demotion_enable=1 on all 96 cores. | Demotion bit set across 2 CBBs × 48 cores. | Bit not set on any core. |
| 2 | Apply short-burst interrupt pattern; observe that cores are demoted to C1 instead of C6. | Cores land in C1; C6 residency counter flat; C1 residency incrementing. | Cores entering C6 despite demotion policy — demotion not applied. |
| 3 | Stop interrupt pattern (sustained idle); verify undemotion re-enables C6. | Cores begin entering C6; C6 residency counter starts incrementing. | C6 not re-enabled after sustained idle — undemotion stuck. |
| 4 | Test C6A, C6S, C6S-P demotion separately. | Each variant demotes to C1 correctly; residency counters confirm. | Any variant not demoting or not undemoting. |

### Health Checks

- No MCA during demotion/undemotion transitions.
- CLOCK_CST_CONFIG_CONTROL.c1_state_auto_demotion_enable=1 on all 96 cores.
- C1 residency increases during demotion period; C6 flat.
- C6 residency resumes after undemotion; no stuck-at-C1 scenario.
- PC6 residency (MSR 0x3F9) = 0 (ZBB).

### Pass / Fail Criteria

- **PASS**: Demotion demotes to C1 when triggered; undemotion re-enables C6 when idle; no MCA.

- **FAIL**: Demotion not applying; undemotion stuck; MCA; PC6>0.

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
- HSD TC: https://hsdes.intel.com/appstore/article-one/#/22022423087