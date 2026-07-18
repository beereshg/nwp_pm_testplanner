# TCD 16031169308 — PCT - Negative / Boundary Validation

| Field | Value |
|-------|-------|
| **TCD ID** | [16031169308](https://hsdes.intel.com/appstore/article-one/#/16031169308) |
| **Title** | PCT - Negative / Boundary Validation |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030762939 — [NWP PM] PCT (Priority Core Turbo)](https://hsdes.intel.com/appstore/article-one/#/16030762939) |
| **Parent TP** | [16030762839 — NWP PM SST](https://hsdes.intel.com/appstore/article-one/#/16030762839) |
| **Sibling TCDs** | [22022420855](https://hsdes.intel.com/appstore/article-one/#/22022420855) — PCT - BIOS Enabling |
| | [16031169297](https://hsdes.intel.com/appstore/article-one/#/16031169297) — PCT - TPMI Runtime Control |
| | [22022420858](https://hsdes.intel.com/appstore/article-one/#/22022420858) — PCT - Functionality |
| | [16031169298](https://hsdes.intel.com/appstore/article-one/#/16031169298) — PCT - DQ Rules |
| | [16030982802](https://hsdes.intel.com/appstore/article-one/#/16030982802) — PCT - DLCP (Die Level Cherry Picking) |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Architecture / Micro-architecture and Functionality

This TCD validates that PCT **rejects or clamps invalid configurations** at BIOS knob, TPMI runtime, and CLOS boundaries. PCT uses SST-TF CLOS-based frequency partitioning to elevate HP cores; this TCD exercises the error paths and boundary conditions that positive-path TCDs (BIOS Enabling, Functionality) do not cover. Invalid inputs must never reach PCode or corrupt CLOS state.

> **Architecture overview:** See [TPF 16030762939 — PCT](https://hsdes.intel.com/appstore/article-one/#/16030762939) Section 2 Design Details for full-stack PCT architecture, CLOS mechanism, ordered throttle, and frequency hierarchy.

### NWP-Specific Deltas

- **2 CBBs x 48 cores = 96 total** (DMR: 4 CBBs x 32). Partition algorithm divides across fewer, larger dies — boundary conditions at partition edges differ from DMR.
- **PCT Partition Count knob (0 = disabled)**: standalone PCT Enable eliminated on DMR/NWP; partition count = 0 means disabled.
- **MAX_LPIDS**: NWP max valid HP count = SST_TF_INFO_8.NUM_CORE_0 / MAX_LPIDS; on NWP with 4 partitions x 2 HP = 8 max. Values > 8 or non-multiples of 4 are invalid.
- **CAPID4.bit29 not used on NWP** (GNR-only). All NWP parts can run PCT or non-PCT.
- **SST-PP ZBB d**: cross-product PCT x SST-PP switching is eliminated. Negative tests for PP-level conflicts are N/A.

### TC Coverage Map

| TC | Title | Scope | Environment |
|----|-------|-------|-------------|
| [16030715680](https://hsdes.intel.com/appstore/article-one/#/16030715680) | [PSS] PCT - BIOS Negative Validation | BIOS knob rejection: non-multiple-of-4, out-of-range HP count; NVRAM integrity after invalid injection | PSS (VP/Simics) |
| [16030768621](https://hsdes.intel.com/appstore/article-one/#/16030768621) | PCT - TPMI runtime negative validation | PCode rejection of invalid TPMI writes: HP count not multiple of 4, HP < 4, HP > NUM_CORE_0; no MCA/hang | FV (silicon, VP) |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Knob | NWP namednodes Path | Boundary Under Test |
|-----------|----------------|---------------------|---------------------|
| BIOS knob | PctHpModuleCount | nvram.PctHpModuleCount.getValue() | Value not multiple of 4; value > 0x20 (MAX_MODULES_PER_CBB); value = 0 (disable path) |
| BIOS knob | PctCapableSystem | — | Knob hidden when fuse not set; reject attempts to force-enable |
| TPMI | SST_CLOS_ASSOC_0.clos_id_module{N} | sv.socket0.cbbX.base.tpmi.sst_clos_assoc_0.clos_id_moduleN | Module index > max valid; duplicate CLOS assignment across partitions |
| TPMI | SST_CLOS_CONFIG_[0..3].min/max | sv.socket0.cbbX.base.tpmi.sst_clos_config_N | min > max inversion; reserved field writes; values outside fused ratio range |
| TPMI | SST_CP_CONTROL.sst_cp_enable | sv.socket0.cbbX.base.tpmi.sst_cp_control.sst_cp_enable | Enable toggle while invalid CLOS state is loaded |
| TPMI | SST_TF_INFO_1.num_core_0 | sv.socket0.cbbX.base.tpmi.sst_tf_info_1.num_core_0 | Reference: max HP modules supported by silicon (read-only boundary) |
| Fuse | CAPID4.bit29 | sv.socket0.nio.punit.ptpcioregs.ptpcioregs.capid4.capid4_29 | PCT fuse gate — must be 1 for PCT to be usable |

---

## Section 3: Reset / Power / Clocking

- **BIOS boundary (CPL3)**: Invalid BIOS knob values must be rejected or clamped before TPMI programming. NVRAM must retain last valid value; invalid values must not propagate to PCode.
- **TPMI runtime boundary**: Invalid TPMI writes at OS runtime must be silently ignored by PCode or produce a deterministic error state. No MCA, no system hang, no corruption of valid CLOS state.
- **Warm reset**: PCT Partition Count changes require warm reset. Invalid values set before reset must not persist through the reset into TPMI state.
- **No power/clocking dependency**: Negative validation scenarios are static configuration checks — no C-state, P-state, or clock gating interactions.

---

## Section 4: Programming Model

### BIOS Knob Boundary Scenarios

| Scenario | Input | Expected Rejection | Register to Verify |
|----------|-------|--------------------|-------------------|
| Non-multiple of 4 | PctHpModuleCount = 3 | BIOS rejects; NVRAM retains previous valid value | nvram.PctHpModuleCount unchanged |
| Exceeds MAX_MODULES_PER_CBB | PctHpModuleCount = 0x24 (36 > 32 max per CBB) | BIOS rejects; NVRAM retains previous valid value | nvram.PctHpModuleCount unchanged |
| Zero (disable path) | PctHpModuleCount = 0 | Deterministic behavior: either accepted as disabled or rejected per policy; no crash | sst_cp_control.sst_cp_enable = 0 |
| Core selection overflow | PCT Core Select > partition size (> 23 on NWP with 24-core partitions) | BIOS clamps to valid range or wraps to offset 0 | sst_clos_assoc_0 HP assignment |

### TPMI Runtime Boundary Scenarios

| Scenario | Input | Expected Rejection | Register to Verify |
|----------|-------|--------------------|-------------------|
| HP count not multiple of 4 via TPMI | Write odd HP count to TPMI | PCode rejects write; prior CLOS state retained | sst_clos_assoc_0 unchanged |
| HP count < 4 (below minimum partition) | HP = 2 via TPMI | PCode rejects; maintains last valid config | sst_cp_control state unchanged |
| HP count > NUM_CORE_0 | HP = NUM_CORE_0 + 4 | PCode rejects; maintains last valid config | sst_tf_info_1.num_core_0 as ceiling |
| CLOS_CONFIG min > max | CONFIG[0].min = 0x30, max = 0x20 | Write rejected or clamped to min = max | sst_clos_config_0 unchanged |
| CLOS_ASSOC invalid CLOS ID | Module N assigned CLOS[5] (only 0-3 valid) | Write ignored; prior assignment retained | sst_clos_assoc_0.clos_id_moduleN |
| Duplicate HP module across partitions | Two partitions claim same module as HP | BIOS rejects; default HP selection applied | CLOS assignment table |

---

## Section 5: Operational Behavior

**Pass/Fail Bar:**

| Scenario | Pass Criterion | Fail Indicator |
|----------|---------------|----------------|
| BIOS non-multiple-of-4 rejected | NVRAM retains last valid PctHpModuleCount; no TPMI programming change | Invalid value accepted into NVRAM; PCode receives corrupt HP count |
| BIOS out-of-range rejected | NVRAM retains last valid value; no model crash/assertion | Out-of-range value in NVRAM after injection |
| TPMI invalid HP count rejected | PCode maintains last valid CLOS state; no MCA; no system hang | MCA, hang, or CLOS state corruption |
| CLOS_CONFIG min > max rejected | Config field unchanged or clamped to min = max; frequency behavior unaffected | Inverted min/max accepted; undefined frequency behavior |
| CLOS_ASSOC invalid CLOS ID ignored | Prior CLOS assignment retained; no frequency disruption | Invalid CLOS ID written successfully; core runs at undefined ratio |
| Core selection overflow clamped | HP selection wraps or clamps; no crash | Out-of-bounds module selected; potential null dereference in partition logic |

---

## Section 6: Corner Cases and Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| **BIOS non-multiple-of-4** | PctHpModuleCount = 3, 5, 7 — values that do not divide evenly into partitions | Covered by TC [16030715680](https://hsdes.intel.com/appstore/article-one/#/16030715680) Step 1 | No action |
| **BIOS out-of-range (> MAX)** | PctHpModuleCount = 0x24 — exceeds MAX_MODULES_PER_CBB | Covered by TC [16030715680](https://hsdes.intel.com/appstore/article-one/#/16030715680) Step 2 | No action |
| **BIOS zero (disable)** | PctHpModuleCount = 0 — disable path determinism | Covered by TC [16030715680](https://hsdes.intel.com/appstore/article-one/#/16030715680) Step 4 | No action |
| **TPMI non-multiple-of-4** | PCode writes odd HP count via TPMI path | Covered by TC [16030768621](https://hsdes.intel.com/appstore/article-one/#/16030768621) | No action |
| **TPMI HP < minimum** | HP = 2 (below 4-core minimum partition) | Covered by TC [16030768621](https://hsdes.intel.com/appstore/article-one/#/16030768621) | No action |
| **TPMI HP > NUM_CORE_0** | HP count exceeds silicon max from SST_TF_INFO_1 | Covered by TC [16030768621](https://hsdes.intel.com/appstore/article-one/#/16030768621) | No action |
| **CLOS_CONFIG min > max inversion** | CLOS_CONFIG[0].min = 0x30, max = 0x20 | Gap: not covered | New TC or add as test step to TC 16030768621 |
| **CLOS_ASSOC invalid CLOS ID** | Module assigned CLOS[5] (only 0-3 valid) | Gap: not covered | New TC or add as test step to TC 16030768621 |
| **Core selection overflow** | PCT Core Select > partition size (> 23) | Verification criterion only | Add boundary check to BIOS enabling TC 22022420855 |
| **Duplicate HP module** | Two partitions claim same module as HP | Gap: not covered | New TC needed — BIOS partition conflict scenario |
| **NVRAM corruption after invalid injection** | Verify NVRAM snapshot integrity after each negative test | Covered by TC [16030715680](https://hsdes.intel.com/appstore/article-one/#/16030715680) Step 3 | No action |

---

## Section 7: Security / Safety / Policy

- Invalid TPMI writes must not corrupt valid CLOS state or create undefined frequency behavior. PCode must treat invalid writes as no-ops.
- BIOS knob validation must prevent out-of-range values from reaching TPMI programming — defense-in-depth at the NVRAM layer.
- No MCA or system hang on any invalid input — graceful rejection is mandatory for all boundary conditions.
- Invalid configurations must not leak through warm reset: TPMI state after reset must reflect only the last valid BIOS configuration.

---

## Section 8: References

- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST_CLOS_ASSOC, SST_CLOS_CONFIG, SST_TF_INFO_8
- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — PCT partition model, CLOS boundary rules, DQ assertions
- [NWP PM MAS — PCT](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP-specific PCT configuration
- [CPUPM BIOS Knobs Gen 3](https://docs.intel.com/documents/System-firmware-bios/Domain/ServerCpuPm/Index/CPUPM%20BIOS%20Knobs/BiosKnobs.html) — PctHpModuleCount, PctCapableSystem knob spec
- [DMR Turbo HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html) — DMR/NWP PCT changes vs GNR
- Co-Design T1 findings 1-4 (2026-07-18)
