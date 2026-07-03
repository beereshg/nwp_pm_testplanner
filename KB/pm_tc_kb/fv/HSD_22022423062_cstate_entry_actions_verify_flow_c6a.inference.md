# Deep Analysis: CState Entry Actions: Verify Flow C6A

| Field | Value |
|-------|-------|
| **HSD ID** | 22022423062 |
| **Title** | CState Entry Actions: Verify Flow C6A |
| **Date** | 2026-07-03 |
| **Target Program** | NWP (Newport) |
| **Segment** | FV |
| **TPF** | Core C1/C6 (Entry/Exit/Residency) |
| **TCD** | CState Entry Actions |
| **Status** | open |
| **Val Environment** | silicon,virtual_platform |
| **Owner Team** | soc.pm |
| **Automation** | runPmx.py -x dmr.xml -p cstates -H 1 -M 5 |

---

## Test Case Intent

Verify the C-state entry flow for C6A on NWP. When a core becomes idle, pCode/Acode executes the C6A entry sequence: voltage/frequency reduction, clock gate, firmware handshake, and state machine progression. This TC confirms the entry actions complete correctly with expected register state at the end of entry.

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
| C-state BIOS | C6Enable=1; ProcessorC1eEnable=1 (if C1E); all target C-state variants enabled. |
| PythonSV | `sv.socket0.cbb{i}.core[c].CLOCK_CST_CONFIG_CONTROL` and `MSR 0x3F9 (pkg C6 residency) | core MSR 0x660-0x669 (per-core C6)` accessible. |
| Idle mechanism | Workload that drives cores to idle (MWAIT or OS scheduler) to trigger C-state entry. |

### Test Steps

| Step | Action | Expected Result (PASS) | Failure Indication |
|------|--------|----------------------|-------------------|
| 1 | Set all cores idle (via MWAIT or sleep); observe C6A entry via PythonSV. | All cores enter target C-state; state machine registers show {cs} state. | Cores stuck in C1 or shallower state; entry timeout. |
| 2 | Read `sv.socket0.cbb{i}.core[c].CLOCK_CST_CONFIG_CONTROL` across 2 CBBs × 48 cores. | All cores in {cs} state; no core stuck in active state. | Any core not reaching {cs} within expected latency. |
| 3 | Check residency counters: MSR 0x3F9 (pkg C6 residency) | core MSR 0x660-0x669 (per-core C6). | Residency counter increments during idle period. | Counter stuck at 0 — C-state not entered. |
| 4 | Wake all cores; verify exit latency within spec. | All cores return to C0 within expected latency (<100μs typical). | Exit latency violation or core not waking. |

### Health Checks

- No MCA during C6A entry/exit.
- sv.socket0.cbb{i}.core[c].CLOCK_CST_CONFIG_CONTROL: entry bit set while idle.
- Residency counter: MSR 0x3F9 (pkg C6 residency) | core MSR 0x660-0x669 (per-core C6) non-zero.
- Exit from C6A < spec latency; core returns to C0 cleanly.
- NWP: PC6 residency = 0 (PkgC6 ZBB).

### Pass / Fail Criteria

- **PASS**: All cores enter C6A and counters increment; exit latency within spec; no MCA.

- **FAIL**: C6A not entered; counter stuck; exit timeout; MCA.

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
- HSD TC: https://hsdes.intel.com/appstore/article-one/#/22022423062