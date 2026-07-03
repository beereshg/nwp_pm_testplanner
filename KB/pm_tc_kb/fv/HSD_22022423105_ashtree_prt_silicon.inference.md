# Deep Analysis: AshTree PRT_silicon

| Field | Value |
|-------|-------|
| **HSD ID** | 22022423105 |
| **Title** | AshTree PRT_silicon |
| **Date** | 2026-07-03 |
| **Target Program** | NWP (Newport) |
| **Segment** | FV |
| **TPF** | C-State Cross Products & PMX |
| **TCD** | AshTree PRT |
| **Status** | open |
| **Val Environment** | silicon |
| **Owner Team** | soc.pm |
| **Automation** |  |

---

## Test Case Intent

Validate AshTree PRT_silicon on NWP (PantherCove PNC). This TC covers AshTree PRT functionality within the NWP C-state validation suite. NWP uses 2 CBBs × 48 cores (vs DMR up to 4 CBBs × 64 cores); PkgC6 is ZBB.

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
| C-states | Target C-state enabled in BIOS. |
| PythonSV | sv.socket0.* accessible. |
| Automation | N/A |

### Test Steps

| Step | Action | Expected Result (PASS) | Failure Indication |
|------|--------|----------------------|-------------------|
| 1 | Boot to SVOS; verify no pending MCA. | System at S0, no errors. | MCA or boot failure. |
| 2 | Execute test procedure per TC description. | Test completes with PASS. | Test FAIL or timeout. |
| 3 | Read C-state registers across 2 CBBs × 48 cores. | All registers reflect expected state. | Any register mismatch. |
| 4 | Verify no MCA or hang post-test. | System stable post-test. | MCA or hang post-test. |

### Health Checks

- No MCA during test.
- C-state residency counters non-zero where expected.
- PC6 residency (MSR 0x3F9) = 0 (ZBB).
- Post-test system stable.

### Pass / Fail Criteria

- **PASS**: Test PASS; no MCA; registers as expected.

- **FAIL**: Test FAIL; MCA; register mismatch.

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
- HSD TC: https://hsdes.intel.com/appstore/article-one/#/22022423105