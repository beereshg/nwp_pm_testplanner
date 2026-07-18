# TCD 16031169308 -- PCT - Negative / Boundary Validation

| Field | Value |
|-------|-------|
| **TCD ID** | [16031169308](https://hsdes.intel.com/appstore/article-one/#/16031169308) |
| **Title** | PCT - Negative / Boundary Validation |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030762939 -- NWP PM PCT](https://hsdes.intel.com/appstore/article-one/#/16030762939) |
| **Child TCs** | *(none yet -- TC TBD)* |
| **Source** | Co-Design T1 coverage gap audit, 2026-07-18 |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Architecture / Micro-architecture and Functionality

This TCD validates that PCT **rejects or clamps invalid configurations** at BIOS, TPMI, and CLOS boundaries. PCT uses SST-TF CLOS-based frequency partitioning; this TCD exercises the error paths and boundary conditions that positive-path TCDs (BIOS Enabling, Functionality) do not cover.

> **Architecture overview:** See [TPF 16030762939](https://hsdes.intel.com/appstore/article-one/#/16030762939) for full-stack PCT architecture.

### Co-Design Spec Refs (Gap findings #1--#4)

| Finding | Spec Ref |
|---------|----------|
| Invalid partition count > supported HP-core bucket count | SST_TF_INFO_8.NUM_CORE_* — Intel SST HAS |
| Out-of-range SST_CLOS_ASSOC_* programming | SST_CLOS_ASSOC_* — Intel SST HAS |
| Invalid SST_CLOS_CONFIG_[0..3] (illegal min/max, reserved fields) | SST_CLOS_CONFIG_[0..3] — Intel SST HAS |
| Conflicting HP module positions / duplicate placement | CLOS association model — Intel SST HAS |

---

## Section 2: Interfaces and Protocols

| Interface | Register | Boundary Under Test |
|-----------|----------|-------------------|
| BIOS knob | PCT HP Partition Count | Value > SST_TF_INFO_8.NUM_CORE_0 / MAX_LPIDS |
| TPMI | SST_CLOS_ASSOC_* | Core index > max valid; duplicate CLOS assignment |
| TPMI | SST_CLOS_CONFIG_[0..3].min/max | min > max; reserved field writes |
| BIOS knob | PCT Core Selection | Position > valid range for partition |

---

## Section 3: Reset / Power / Clocking

- Invalid BIOS configurations must be rejected/clamped at CPL3 — before TPMI programming.
- Invalid TPMI writes at OS runtime must be silently ignored or produce SST_CP_STATUS.ERROR_TYPE.

---

## Section 4: Programming Model

| Scenario | Input | Expected Rejection |
|----------|-------|--------------------|
| Partition count overflow | Count = NUM_CORE_0 + 1 | BIOS clamps to NUM_CORE_0; no TPMI change |
| CLOS_ASSOC out of range | Core N assigned CLOS[5] (only 0--3 valid) | Write ignored; prior assignment retained |
| CLOS_CONFIG min > max | CONFIG[0].min = 0x30, CONFIG[0].max = 0x20 | Write rejected or clamped to min=max |
| Conflicting HP positions | Two partitions claim same core as HP | BIOS rejects; default HP selection applied |

---

## Section 5: Operational Behavior

| Scenario | Expected | TC |
|----------|----------|----|
| Partition count overflow rejected | BIOS clamps; feature disabled or at max valid | *(TC TBD)* |
| OOR CLOS_ASSOC write ignored | No TPMI state change; frequency unaffected | *(TC TBD)* |
| Invalid CLOS_CONFIG min/max rejected | Config reverts to prior valid state | *(TC TBD)* |
| Conflicting HP module positions rejected | Default HP assignment applied | *(TC TBD)* |

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| **All scenarios above** | This TCD IS the negative/boundary coverage | *(TC TBD for all)* | Author TCs after TCD review |

---

## Section 7: Security / Safety / Policy

- Invalid TPMI writes must not corrupt valid CLOS state or create undefined frequency behavior.
- BIOS knob validation must prevent out-of-range values from reaching TPMI programming.

---

## Section 8: References

- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST_CLOS_ASSOC, SST_CLOS_CONFIG, SST_TF_INFO_8
- [NWP PM MAS -- PCT](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- Co-Design T1 findings #1--#4 (2026-07-18)
