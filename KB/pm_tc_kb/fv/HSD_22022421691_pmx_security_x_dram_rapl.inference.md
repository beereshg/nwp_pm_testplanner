# TC 22022421691: pmx Security x DRAM RAPL

**TCD:** 16031172977 - PMX Security cross product
**TPF:** 22022562325 - PM Integration Testing
**Val Environment:** silicon
**Test Commands:** pmx security cross-product test

## Section A: NWP Delta

**NWP Adaptation:** DRAM RAPL may be fused off on NWP. This TC requires verification that the DRAM RAPL feature is enabled before execution. If fused off, TC should be marked not-applicable.

### Test Case Intent
Validates that DRAM RAPL enforcement remains correct when security energy filtering (MSR 0xBC) is active. Energy fuzzing must not interfere with DRAM power limiting.

### Pre-Conditions
| Item | Requirement |
|------|-------------|
| Feature | pmx Security x DRAM RAPL |
| Platform | NWP validation target with DRAM RAPL enabled (verify fuse state) |
| BIOS | Energy filtering capable; DRAM RAPL limits programmed |
| NWP Note | **DRAM RAPL may be fused off on NWP - verify before execution** |

### Test Steps
| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Verify DRAM RAPL fuse state | DRAM RAPL enabled (not fused off) | Feature disabled - skip TC |
| 2 | Program DRAM RAPL PL1 to throttle-inducing level | Limit accepted | Limit rejected |
| 3 | Enable energy filtering (MSR 0xBC.bit0=1) | Filtering active | Write fails |
| 4 | Apply memory-intensive workload | DRAM power throttled to PL1 | No throttling observed |
| 5 | Verify DRAM ENERGY_STATUS reflects fuzzing | Fuzzed values reported | Unfuzzed values |
| 6 | Verify DRAM RAPL enforcement persists | Power stays at/below PL1 | Power exceeds limit |

### Pass / Fail Criteria
- **PASS:** DRAM RAPL correctly enforced with energy fuzzing active; no MCA; no hang
- **FAIL:** DRAM RAPL enforcement fails; MCA; hang; or feature fused off (N/A)

## Section B: Interactions

### Swimlane Data
| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | Test | Check DRAM RAPL fuse | Fuse register |
| 2 | Test | Program DRAM PL1 | TPMI |
| 3 | Test | Enable energy fuzzing | MSR 0xBC |
| 4 | Workload | Generate memory traffic | DRAM |
| 5 | Test | Read ENERGY_STATUS | TPMI |
| 6 | Test | Verify enforcement | TPMI PERF_STATUS |

## Section C: Coverage

- **Feature:** PM Security Cross-product
- **TCD:** PMX Security cross product
- **Scope:** DRAM RAPL x Security energy filtering

## Section D: Spec Refs

| Register / Log | Field/Offset | Pass/Fail Criteria |
|----------------|-------------|-------------------|
| MSR 0xBC | bit0 | 1 = energy filtering enabled |
| TPMI DRAM_PL1 | power limit | Configured to throttle level |
| TPMI DRAM_ENERGY_STATUS | energy counter | Reflects fuzzing |
| Test log | exit code | 0 = pass |

## Section E: Risk Assessment

| Risk / Open Item | Likelihood | Severity | Mitigation |
|-----------------|-----------|---------|-----------|
| DRAM RAPL fused off on NWP | High | High | Verify fuse before execution; mark N/A if disabled |
