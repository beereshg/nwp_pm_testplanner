# TC 22022423116: PEGA C states x SB Harasser traffic

**TCD:** 22022421309 — Cross Products
**TPF:** 22022562325 — PM Integration Testing
**Val Environment:** silicon,virtual_platform
**Test Commands:** pm/pmutils/dvfs_utils.py + pm/pss/mailbox/* + Solar/* (harasser + feature script)

## Section A: NWP Delta


**NWP Adaptation:** NWP uses 2 CBBs (vs DMR up to 4). PkgC6 is ZBB on NWP. IMH path replaces iMCH.

### Test Case Intent
Intent Verification Strategy * How will TC logic be checked out prior to testing on silicon (e. Feature tag: SB Harasser . HAS Ref — Sideband Harasser Traffic: The Sideband (SB) Harasser generates continuous GPSB/PMSB traffic to stress the PM sideband fabric while other PM features run concurrently. Covered cross-products: CBB DVFS × SB harasser, DRAM RAPL × SB harasser, PEGA/Solar C-states × SB h

### Pre-Conditions
Item Requirement Feature PEGA C states x SB Harasser traffic Platform NWP validation target (silicon or emulation) with PM integration features enabled. Automation command echo manual_execution Category / note Active PM

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
- **Scope:** PEGA C states x SB Harasser traffic

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
