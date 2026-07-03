# Deep Analysis: [PV] PMSS - SST PCT Partition Sweep

| Field | Value |
|-------|-------|
| **HSD ID** | 16030717718 |
| **Title** | [PV] PMSS - SST PCT Partition Sweep |
| **Date** | 2026-06-09 |
| **Target Program** | NWP (Newport) |
| **Feature** | SST |
| **Sub-Feature** | PCT (Priority Core Turbo) |
| **Validation Layer** | **OS Software Stack** — stresses `intel-speed-select` driver across all valid partition counts |
| **Feature Classification** | **Silicon-heavy** (HW enforces HP/LP TRL; core frequency derating in Acode/CBB RTL) with firmware orchestration |
| **NWP Disposition** | **Runnable_As-Is** |

---

## Duplication Analysis vs FV

### FV Counterparts
- [22022422105](https://hsdes.intel.com/appstore/article-one/#/22022422105) PCT - Default HP core selection
- [16030715686](https://hsdes.intel.com/appstore/article-one/#/16030715686) [PSS] PCT - Default HP core selection

### Assessment: **Complementary — NOT a duplicate**

**Why this is additive, not redundant:**

The FV TCs validate that the *hardware correctly implements* a given partition configuration. This PV TC exercises the *OS driver's ability to handle all valid partition counts* without errors — a fundamentally different validation scope:

| Bug class | FV catches? | This PV TC catches? |
|-----------|:-----------:|:-------------------:|
| Silicon implements wrong TRL per partition | ✅ | ✅ (indirectly via frequency check) |
| Driver fails at partition count boundary (0, max) | ❌ | ✅ |
| Driver loses state between partition changes | ❌ | ✅ |
| Sysfs entry missing for certain partition counts | ❌ | ✅ |
| `sst` tool crashes or returns error for odd partition values | ❌ | ✅ |

**Key unique coverage:** systematically sweeping 0 → max partition count stresses the driver's loop/state management in ways a single-point FV test cannot.

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_As-Is**

NWP supports PCT via SST-TF. The sweep must cover:
- Partition count = 0 (PCT disabled, all cores LP)
- Partition count = 1..max_supported (verify max from `SST_TF_INFO_1.NUM_CORE_0` via TPMI)
- NWP: 48 cores/CBB; valid PCT partition counts depend on module granularity (4 cores/module = 12 modules/CBB → max partition count = 12 per CBB)

---

## Section B: Test Procedure

### Preconditions
- Linux booted with `intel-speed-select` driver
- SST-TF enabled (not ZBB on NWP)

### Test Steps
1. Read max partition count: `sst turbofreq info` → note `num-hp-cores-supported`
2. For each partition count N in [0, 4, 8, 12, ..., max]:
   a. `sst perf-profile config --clos 0 --core-count N`
   b. Verify dmesg: no errors, no WARNING or BUG
   c. Verify sysfs: HP core count reflects N
   d. Run 30s workload: verify HP cores at higher TRL than LP cores
   e. `sst perf-profile config --clos 0 --core-count 0` (reset to disabled)
3. Verify final state: PCT disabled, all cores at same TRL

### Pass Criteria
- All partition counts accepted without driver error
- Sysfs consistently reflects configured partition count
- HP/LP frequency differential observed under load for N > 0
- Clean reset to disabled state after sweep

---

## Section C: Coverage Assessment

| Category | Status | Notes |
|----------|--------|-------|
| Architecture / Functionality | ✅ Covered | Full partition count range via OS stack |
| Interface and Protocols | ✅ Covered | `intel-speed-select` driver, sysfs, TPMI sweep |
| Reset, Power, and Clocking | ⚠️ Partial | Reset between partition changes not a reset event (warm/cold) |
| Programming Model | ✅ Covered | Iterative BIOS/SST tool config changes |
| Operational Behavior | ✅ Covered | Frequency differential verified at each partition count |
| Corner Cases & Error Handling | ✅ Covered | Boundary values (0, max) explicitly tested |
| Security / Safety / Policy | ❌ Not Covered | Privilege enforcement not tested |
| References | ✅ Covered | NWP HAS SST-TF |

---

## Section D: Spec References

- NWP HAS PM Features: https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features
- KB Article: KB/pm_features/sst/sst_main.md
- FV TC (hardware layer): [22022422105](https://hsdes.intel.com/appstore/article-one/#/22022422105)

---

## Section E: Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Driver has hardcoded max partition count from DMR (not NWP) | Medium | High — sweep fails at NWP-valid counts | Check driver against NWP TPMI capability register |
| Partition count granularity differs between CBBs on NWP | Low | Medium | Verify both CBBs updated consistently |
| Frequency differential not observable on emulation platform | High (emulation) | Low — skip on emulation | Mark as silicon-required in val_environment |

---

## Section F: Recommendations

1. **[NWP topology]** Verify sweep covers NWP-specific max (based on 48 cores/CBB, 4-core module granularity = 12 modules → max 12 HP partitions per CBB).
2. **[Driver stress]** Log dmesg before/after each partition change to catch any silent driver errors.
3. **[Cross-validation]** Add optional PythonSV cross-check at partition count 4 and max to confirm TPMI `SST_CLOS_CONFIG` matches sysfs.
