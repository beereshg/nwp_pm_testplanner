# TC 22022421697: pmx Security x Platform RAPL

**TCD:** 16031172977 - PMX Security cross product
**TPF:** 22022562325 - PM Integration Testing
**Val Environment:** silicon
**Test Commands:** pmx security cross-product test

## Section A: NWP Delta

**NWP Adaptation:** Platform RAPL (Psys) has reduced scope on NWP single-NIO topology. Only single-package platform power limiting is applicable.

### Test Case Intent
Validates that Platform RAPL (Psys) enforcement remains correct when security energy filtering (MSR 0xBC) is active. Energy fuzzing must not interfere with platform-level power limiting.

### Pre-Conditions
| Item | Requirement |
|------|-------------|
| Feature | pmx Security x Platform RAPL |
| Platform | NWP validation target with Platform RAPL enabled |
| BIOS | Energy filtering capable; Platform RAPL limits programmed |
| NWP Note | Single-NIO topology - reduced Psys scope vs multi-socket |

### Test Steps
| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Program Platform RAPL PL1 to throttle-inducing level | Limit accepted | Limit rejected |
| 2 | Enable energy filtering (MSR 0xBC.bit0=1) | Filtering active | Write fails |
| 3 | Apply mixed compute+IO workload | Platform power throttled | No throttling |
| 4 | Verify platform ENERGY_STATUS reflects fuzzing | Fuzzed values | Unfuzzed values |
| 5 | Verify Platform RAPL enforcement persists | Total power at/below PL1 | Power exceeds |

### Pass / Fail Criteria
- **PASS:** Platform RAPL correctly enforced with energy fuzzing active; no MCA; no hang
- **FAIL:** Platform RAPL enforcement fails; MCA; hang

## Section B: Interactions

### Swimlane Data
| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | Test | Program Platform PL1 | TPMI |
| 2 | Test | Enable energy fuzzing | MSR 0xBC |
| 3 | Workload | Generate mixed load | CPU + IO |
| 4 | Test | Read platform ENERGY_STATUS | TPMI |
| 5 | Test | Verify enforcement | TPMI PERF_STATUS |

## Section C: Coverage

- **Feature:** PM Security Cross-product
- **TCD:** PMX Security cross product
- **Scope:** Platform RAPL x Security energy filtering

## Section D: Spec Refs

| Register / Log | Field/Offset | Pass/Fail Criteria |
|----------------|-------------|-------------------|
| MSR 0xBC | bit0 | 1 = energy filtering enabled |
| TPMI Platform_PL1 | power limit | Configured to throttle |
| TPMI Platform_ENERGY_STATUS | energy counter | Reflects fuzzing |
| Test log | exit code | 0 = pass |

## Section E: Risk Assessment

| Risk / Open Item | Likelihood | Severity | Mitigation |
|-----------------|-----------|---------|-----------|
| Single-NIO reduced scope | Low | Low | Test covers applicable single-package Psys path |
