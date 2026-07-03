# Deep Analysis: CState Fast C1E: Exit flow_silicon

| Field | Value |
|-------|-------|
| **HSD ID** | 22022423096 |
| **Title** | CState Fast C1E: Exit flow_silicon |
| **Date** | 2026-07-03 |
| **Target Program** | NWP (Newport) |
| **Segment** | FV |
| **TPF** | Fast C1E |
| **TCD** | CState Fast C1E: C1E start/end flow |
| **Status** | open |
| **Val Environment** | silicon,virtual_platform |
| **Owner Team** | soc.pm |
| **Automation** | runPmx.py -x dmr.xml -p cstates -H 1 -M 5 |

---

## Test Case Intent

Verify the C-state exit flow for C1E on NWP. When a core receives a wake event (interrupt, IPI, or timer), pCode/Acode executes the C1E exit sequence: restore frequency/voltage, ungating clocks, re-enabling caches, and transitioning back to C0. This TC confirms exit actions complete correctly.

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
| C-state BIOS | Target C-state enabled; cores can enter {cs}. |
| PythonSV | `sv.socket0.cbb{i}.core[c].CLOCK_CST_CONFIG_CONTROL` and exit latency measurement accessible. |
| Wake source | Timer interrupt or IPI to trigger exit from {cs}. |

### Test Steps

| Step | Action | Expected Result (PASS) | Failure Indication |
|------|--------|----------------------|-------------------|
| 1 | Drive cores into C1E (via MWAIT or idle); confirm entry. | Cores in {cs} state; residency counter incrementing. | Entry fails; cannot test exit. |
| 2 | Trigger wake event (IPI or timer); measure exit latency. | All cores return to C0 within spec; `{reg_c6}` shows C0 state. | Exit latency exceeds spec; core not waking. |
| 3 | Read post-exit registers: voltage/frequency restored, cache re-enabled. | All per-core registers reflect C0 state post-exit. | Any register showing stale {cs} state post-exit. |
| 4 | Repeat entry/exit cycle 100+ times; check for accumulating errors. | No MCA or stability degradation across repeated cycles. | MCA or increasing error count with repeated cycling. |

### Health Checks

- No MCA during C1E exit.
- Exit latency within spec for 2 CBBs × 48 cores.
- Post-exit: `sv.socket0.cbb{i}.core[c].CLOCK_CST_CONFIG_CONTROL` = C0 for all cores.
- No residual C1E state bit set after full exit.

### Pass / Fail Criteria

- **PASS**: All cores exit C1E within spec latency; return to C0 cleanly; no MCA.

- **FAIL**: Exit timeout; core stuck in C1E post-wake; MCA.

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
- HSD TC: https://hsdes.intel.com/appstore/article-one/#/22022423096