# TCD 16031169310 -- PCT - Error Injection / Recovery

| Field | Value |
|-------|-------|
| **TCD ID** | [16031169310](https://hsdes.intel.com/appstore/article-one/#/16031169310) |
| **Title** | PCT - Error Injection / Recovery |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030762939 -- NWP PM PCT](https://hsdes.intel.com/appstore/article-one/#/16030762939) |
| **Child TCs** | *(none yet -- TC TBD)* |
| **Source** | Co-Design T1 coverage gap audit, 2026-07-18 |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Architecture / Micro-architecture and Functionality

This TCD validates PCT **error status reporting and recovery paths** defined in the SST HAS: SST_CP_STATUS.ERROR_TYPE for unsupported/conflicting feature control, and EXCURSION_TO_MIN reporting/clear for CLOS groups hitting minimum frequency floor.

> **Architecture overview:** See [TPF 16030762939](https://hsdes.intel.com/appstore/article-one/#/16030762939) for PCT architecture.

### Co-Design Spec Refs (Gap findings #8--#9)

| Finding | Spec Ref |
|---------|----------|
| ERROR_TYPE path for unsupported/conflicting enable | SST_CP_STATUS.ERROR_TYPE — Intel SST HAS |
| EXCURSION_TO_MIN set/clear behavior | SST_CP_STATUS.EXCURSION_TO_MIN, RESET_EXCURSION_TO_MIN — Intel SST HAS |

---

## Section 2: Interfaces and Protocols

| Interface | Register | Error/Recovery Role |
|-----------|----------|-------------------|
| TPMI | SST_CP_STATUS.ERROR_TYPE | Reports 
ot_supported and conflict errors |
| TPMI | SST_CP_STATUS.EXCURSION_TO_MIN | Per-CLOS-group flag: frequency hit minimum floor |
| TPMI | SST_CP_CONTROL.RESET_EXCURSION_TO_MIN | SW clears excursion flag |
| TPMI | SST_CP_CONTROL.HANDSHAKE | Error status read after handshake confirms write |

---

## Section 3: Reset / Power / Clocking

- ERROR_TYPE is set by PCode on control write rejection; persists until next successful control write.
- EXCURSION_TO_MIN is set by PCode during ordered throttle when a CLOS group reaches its minimum floor.
- Both are cleared by explicit SW action (new write or RESET_EXCURSION_TO_MIN).

---

## Section 4: Programming Model

| Scenario | Trigger | Expected Status |
|----------|---------|----------------|
| Unsupported feature enable | Enable PCT on unfused/unsupported SKU | ERROR_TYPE = not_supported |
| Conflicting feature enable | Enable PCT + SST-BF simultaneously | ERROR_TYPE = conflict |
| CLOS group at min floor | PL1 forces LP CLOS to minimum ratio | EXCURSION_TO_MIN[3] = 1 (LP CLOS) |
| Clear excursion flag | Write RESET_EXCURSION_TO_MIN = 1 | EXCURSION_TO_MIN[3] = 0 |
| Verify error clear on success | Valid PCT enable after error | ERROR_TYPE = 0 |

---

## Section 5: Operational Behavior

| Scenario | Expected | TC |
|----------|----------|----|
| ERROR_TYPE = not_supported on unsupported SKU | PCode rejects; feature remains disabled; error status readable | *(TC TBD)* |
| ERROR_TYPE = conflict on PCT + SST-BF | PCode rejects conflicting combo; original state preserved | *(TC TBD)* |
| EXCURSION_TO_MIN triggered under PL1 | Flag set when LP CLOS reaches floor; frequency at minimum | *(TC TBD)* |
| RESET_EXCURSION_TO_MIN clears flag | After SW clear, flag = 0; normal throttle resumes | *(TC TBD)* |

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| **All scenarios above** | This TCD IS the error/recovery coverage | *(TC TBD for all)* | Author TCs after TCD review |

---

## Section 7: Security / Safety / Policy

- ERROR_TYPE is read-only from OS; cannot be spoofed.
- EXCURSION_TO_MIN is read-only; only RESET_EXCURSION_TO_MIN is writable.

---

## Section 8: References

- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST_CP_STATUS, ERROR_TYPE, EXCURSION_TO_MIN
- [NWP PM MAS -- PCT](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- Co-Design T1 findings #8--#9 (2026-07-18)
