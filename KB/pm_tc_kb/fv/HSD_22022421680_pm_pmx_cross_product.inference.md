# TC 22022421680: PM PMX Cross Product

**TCD:** 22022420631 — pmx cross products
**TPF:** 22022562325 — PM Integration Testing
**Val Environment:** silicon
**Test Commands:** runPmx.py -x dmr.xml -p pmx_security / pmx_cross

## Section A: NWP Delta


**NWP Adaptation:** NWP uses 2 CBBs (vs DMR up to 4). PkgC6 is ZBB on NWP. IMH path replaces iMCH.

### Test Case Intent
Intent Verification Strategy * PMX HW Requirements N/A SW Requirements AcodeFW, Pcode, Pstate driver, Cstate Driver, DMR SVOS, DMR python SV repository,PAtch23 and pythonSV installed. HAS Ref — PMX CPU/Core Power × Traffic Interaction: PMX cross-product with active CPU traffic validates that PM state transitions (C-states, P-states, DVFS) occur correctly under load. Key: core power draw with PMX-s

### Pre-Conditions
Item Requirement Feature PM PMX Cross Product Platform NWP validation target (silicon or emulation) with PM integration features enabled.

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
- **TCD:** pmx cross products
- **Scope:** PM PMX Cross Product

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
