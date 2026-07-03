# TC 22022423123: iMH GPSB end point sweep

**TCD:** 22022421311 — EndPoint Sweep
**TPF:** 22022562325 — PM Integration Testing
**Val Environment:** silicon,virtual_platform
**Test Commands:** pm/pmutils/pega.py + pm/pss/mailbox/pega_mailbox.py (GPSB/PMSB endpoint sweep)

## Section A: NWP Delta


**NWP Adaptation:** NWP uses 2 CBBs (vs DMR up to 4). PkgC6 is ZBB on NWP. IMH path replaces iMCH.

### Test Case Intent
Intent Verification Strategy * How will TC logic be checked out prior to testing on silicon (e. Feature tag: SB Harasser . HAS Ref — GPSB/PMSB Endpoint Sweep: Systematic access to all registered GPSB (General Purpose Sideband) and PMSB (Power Management Sideband) endpoints on CBB and iMH. Validation: each endpoint responds to read/write transactions; no timeout, no unreachable endpoint; register v

### Pre-Conditions
Item Requirement Feature iMH GPSB end point sweep Platform NWP validation target (silicon or emulation) with PM integration features enabled. Automation command echo manual_execution Category / note Active PM

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
- **TCD:** EndPoint Sweep
- **Scope:** iMH GPSB end point sweep

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
