# Deep Analysis: [PSS]C6 Residency Counter

| Field | Value |
|-------|-------|
| **HSD ID** | 16030715587 |
| **Title** | [PSS]C6 Residency Counter |
| **Date** | 2026-07-03 |
| **Target Program** | NWP (Newport) |
| **Segment** | FV |
| **TPF** | Core C1/C6 (Entry/Exit/Residency) |
| **TCD** | CState Entry Actions |
| **Status** | open |
| **Val Environment** |  |
| **Owner Team** | soc.pm |
| **Automation** |  |

---

## Test Case Intent

Verify C-state residency counters on NWP. When cores idle in C6, hardware residency counters must increment proportionally to idle time. Correct counter behavior is critical for power management telemetry, OS power governor decisions, and RAPL energy accounting.

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
| Idle workload | Script that drives cores to idle for a measured duration. |
| PythonSV | `MSR 0x3F9 (pkg C6 residency) | core MSR 0x660-0x669 (per-core C6)` and per-core MSRs 0x660–0x669 readable. |

### Test Steps

| Step | Action | Expected Result (PASS) | Failure Indication |
|------|--------|----------------------|-------------------|
| 1 | Read baseline residency counters before idle period. | Counters readable; note baseline value. | Counter not accessible; read error. |
| 2 | Drive cores to idle in C6 for N seconds (e.g. 10s). | Cores in {cs}; idle workload confirming no spurious wake. | Cores not entering {cs}; residency stays flat. |
| 3 | Read residency counters after idle period; compute delta. | Delta ≈ N × core_count × TSC_frequency (within 5% tolerance). | Delta too small (cores not in C-state) or too large (counter overflow). |
| 4 | Verify counters across all 96 cores (2 CBBs × 48 cores). | All core counters show proportional increase; no stuck counter. | Any core counter stuck at 0 or not incrementing. |

### Health Checks

- No MCA during residency test.
- Residency counter delta proportional to idle time within ±5%.
- NWP: per-core MSRs 0x660-0x669 readable for all 96 cores (2 CBBs × 48).
- PC6 residency (MSR 0x3F9) = 0 (ZBB).

### Pass / Fail Criteria

- **PASS**: Residency counters increment proportionally; no stuck counter; no MCA.

- **FAIL**: Counter stuck at 0; delta < 50% expected; MCA; PC6 counter > 0.

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
- HSD TC: https://hsdes.intel.com/appstore/article-one/#/16030715587