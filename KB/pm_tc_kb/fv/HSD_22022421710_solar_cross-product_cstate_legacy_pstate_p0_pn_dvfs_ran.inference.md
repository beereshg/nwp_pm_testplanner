# TC 22022421710: [Solar Cross-Product] cstate_legacy_pstate_p0_pn_dvfs_random_exercise

**TCD:** 22022420633 — Solar Cross Products
**TPF:** 22022562325 — PM Integration Testing
**Val Environment:** silicon,virtual_platform
**Test Commands:** solar.sh /cfg Solar/Cross_Products/<xml> [--exercise]

## Section A: NWP Delta

[Solar] Solar XML-driven stress test — invoked via solar.sh.
**NWP Adaptation:** NWP uses 2 CBBs (vs DMR up to 4). PkgC6 is ZBB on NWP. IMH path replaces iMCH.

### Test Case Intent
Solar cross-product exercise: C-state + legacy P-state P0/Pn + DVFS random exercise.

### Pre-Conditions
Item Requirement Feature [Solar Cross-Product] Cross_Products-Allcross-cstate_legacy_pstate_p0_pn_pstate_dvfs_random_exercise Platform NWP validation target (silicon or emulation) with PM integration features enabled. Automation command /usr/bin/solar/solar.sh /cfg /usr/local/python/diamondrapids/pm/Solar/Cross_Products/Allcross/cstate_legacy_pstate_p0_pn_pstate_dvfs_random_exercise.xml /logpath .

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
- **TCD:** Solar Cross Products
- **Scope:** [Solar Cross-Product] cstate_legacy_pstate_p0_pn_dvfs_random_exercise

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
