# Deep Analysis: [Solar]_CStates-CStates_AnyCore--Verify

| Field | Value |
|-------|-------|
| **HSD ID** | 22022423113 |
| **Title** | [Solar]_CStates-CStates_AnyCore--Verify |
| **Date** | 2026-07-03 |
| **Target Program** | NWP (Newport) |
| **Segment** | FV |
| **TPF** | C-State Cross Products & PMX |
| **TCD** | Solar |
| **Status** | open |
| **Val Environment** | virtual_platform |
| **Owner Team** | soc.pm |
| **Automation** | /usr/bin/solar/solar.sh /cstate -scope 0:0:100 -states C1,C6 -mode v /logpath . /log_ip_disables |

---

## Test Case Intent

Solar stress test for C-states on NWP (PantherCove PNC). The Solar framework rapidly exercises C-state entry/exit sequences across all cores to detect stability issues, firmware hang conditions, and residency counter errors. Mode "e" = exercise (stress without verification). NWP adapts DMR Solar config by limiting to 2 CBBs × 48 cores.

---

## Section A: NWP Disposition

**Disposition: Runnable_On_NWP**

Core C-states are fully supported on NWP (PantherCove PNC). NWP has 2 CBBs × 48 cores (96 total) vs DMR up to 4 CBBs × 64 cores. PkgC6 is ZBB on NWP — any test must verify PC6 residency stays at 0. Key NWP CBB loop adaptation: `range(4)→range(2)`, core loops: `range(64)→range(48)`. Register paths prefix: `sv.socket0.cbb{0,1}.*`.

---

## Section B: NWP Test Procedure

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP silicon or virtual platform. SVOS booted with C-states enabled. |
| Solar | Solar framework installed at /usr/bin/solar/; NWP Solar XML config present. |
| C-states | C6A, C6S, C6S-P, MC6 enabled in BIOS (C6Enable=1, Module C-state policy set). |
| PythonSV | sv.socket0.* accessible for post-run register inspection. |
| Note | PkgC6 is ZBB on NWP — Solar must not attempt PC6; verify scope excludes PC6. |

### Test Steps

| Step | Action | Expected Result (PASS) | Failure Indication |
|------|--------|----------------------|-------------------|
| 1 | Boot to SVOS with C-states enabled. Verify no pending MCA. | System at S0, no errors. | Any MCA or boot hang. |
| 2 | Run Solar: `/usr/bin/solar/solar.sh /cstate -scope 0:0:100 -states C1,C6 -mode v /logpath . /log_ip_disables` | Solar exits with PASS; no timeout; no kernel panic. | Solar reports FAIL, hangs, or MCA during execution. |
| 3 | Check NWP C-state residency counters: `MSR 0x3F9 (pkg C6 residency) | core MSR 0x660-0x669 (per-core C6)` | Counters increment during test; no counter stuck at zero for active cores. | Counter stuck or frozen — indicates C-state not entered. |
| 4 | Check NLOG/SVOS console for error events. | No error-level events; no unexpected demotion events. | Any error-level PM events in log. |
| 5 | Verify system remains stable after Solar completion. | Normal OS operation resumes; no latent hangs. | OS becomes unresponsive post-Solar. |

### Health Checks

- No MCA or kernel panic during or after Solar.
- Solar PASS result in Solar log.
- C-state residency counters (MSR 0x3F9, per-core 0x660–0x669) non-zero.
- No PM error counters incremented: sv.socket0.nio0.punit.ptpcfsms.pm_err_cnt*.
- NWP-specific: PC6 residency (MSR 0x3F9) must remain 0 (ZBB).

### Pass / Fail Criteria

- **PASS**: Solar completes with PASS; all residency counters non-zero; no MCA.

- **FAIL**: Solar FAIL/timeout; MCA; PC6 residency > 0 (ZBB violation); kernel panic.

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
- HSD TC: https://hsdes.intel.com/appstore/article-one/#/22022423113