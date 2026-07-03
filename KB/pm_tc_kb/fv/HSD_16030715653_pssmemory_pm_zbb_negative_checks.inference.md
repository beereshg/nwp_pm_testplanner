# TC 16030715653: [PSS]Memory PM ZBB Negative Checks

**TCD:** 22022421309 — Cross Products
**TPF:** 22022562325 — PM Integration Testing
**Val Environment:** os-svos,python-sv
**Test Commands:** pm/pmutils/dvfs_utils.py + pm/pss/mailbox/* + Solar/* (harasser + feature script)

## Section A: NWP Delta

[PSS] Pre-silicon simulation TC — runs on NWP Simics/emulation model.
**NWP Adaptation:** NWP Simics model; confirm PSS environment supports NWP topology.

### Test Case Intent
[PSS] Memory PM ZBB negative checks: verifies PC6/MC6 ZBB constraints hold under stress.

### Pre-Conditions
Item Requirement Feature [PSS]Memory PM ZBB Negative Checks Platform NWP validation target (silicon or emulation) with PM integration features enabled.

### Test Steps
# Action Expected Result (

### Pass / Fail Criteria
- **PASS:** No unexpected MCA, no hang, test completes without error
- **FAIL:** MCA, timeout, assertion failure, or unexpected register mismatch

## Section B: Interactions

### Swimlane Data
| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | Test script | Initialize PM environment | PythonSV / SVOS |
| 2 | PCode | Run feature under test | HW |
| 3 | Test script | Verify registers / counters | TPMI / MSR / PMSB |

### Sequence Data
| # | From | To | Message | Interface |
|---|------|----|---------|-----------|
| 1 | OS/Script | PCode | Feature trigger | TPMI / MSR |
| 2 | PCode | HW | Apply PM action | Internal |
| 3 | Script | Registers | Read result | MMIO / MSR |

## Section C: Coverage

- **Feature:** PM Integration / Cross-product
- **TCD:** Cross Products
- **Scope:** [PSS]Memory PM ZBB Negative Checks

## Section D: Spec Refs

| Register / Log | Field/Offset | Pass/Fail Criteria |
|----------------|-------------|-------------------|
| Test log / stdout | exit code | 0 = pass |
| MCA registers | any | Must be 0 |

## Section E: Risk Assessment

| Risk / Open Item | Likelihood | Severity | Mitigation |
|-----------------|-----------|---------|-----------|
| DMR→NWP port needed | Medium | Medium | Verify CBB count and PkgC6 ZBB adaptation |

## Section F: Recommendations

- Confirm NWP 2-CBB loop bounds (`range(2)`) replace DMR `range(4)` if applicable.
- PkgC6 ZBB: remove any PC6 residency assertions; assert PC6 NOT entered.
- For Solar TCs: verify Solar XML cross-product configs exist for NWP topology.
