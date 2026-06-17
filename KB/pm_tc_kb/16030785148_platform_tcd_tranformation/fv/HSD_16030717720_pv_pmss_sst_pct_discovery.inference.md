# Deep Analysis: [PV] PMSS - SST PCT Discovery

| Field | Value |
|-------|-------|
| **HSD ID** | 16030717720 |
| **Title** | [PV] PMSS - SST PCT Discovery |
| **Date** | 2026-06-09 |
| **Target Program** | NWP (Newport) |
| **Feature** | SST |
| **Sub-Feature** | PCT (Priority Core Turbo) |
| **Validation Layer** | **OS Software Stack** — exercises `sst` tool enumeration and `intel-speed-select` driver discovery path |
| **Feature Classification** | **Silicon-heavy** (CAPID4.bit29 fuse gates capability; SST_TF_CAPABILITY is a HW register) with firmware/BIOS/driver discovery chain |
| **NWP Disposition** | **Runnable_As-Is** |

---

## Duplication Analysis vs FV

### FV Counterparts
- [22022422103](https://hsdes.intel.com/appstore/article-one/#/22022422103) PCT - TPMI register check
- [16030715690](https://hsdes.intel.com/appstore/article-one/#/16030715690) [PSS] PCT - TPMI register check (FlexconPM)

### Assessment: **Complementary — NOT a duplicate**

**Why this is the most clearly differentiated PV TC:**

The FV "TPMI register check" reads raw TPMI register bits via PythonSV/namednodes. This PV "Discovery" TC explicitly exercises the `sst` tool's discovery path and the `intel-speed-select` driver's capability enumeration:

```
sst perf-profile info
    ↓ ioctl to intel-speed-select driver
    ↓ driver reads SST_TF_CAPABILITY via TPMI MMIO
    ↓ driver parses capability fields
    ↓ returns to userspace
    ↓ sst tool formats and displays
```

**Unique bug classes caught:**
- `sst` tool displays wrong max HP core count (misparse of `SST_TF_INFO_1.NUM_CORE_0`)
- Driver ioctl interface returns stale/cached capability after hot-plug or reset
- `sst perf-profile info` shows PCT as "not supported" on NWP despite TPMI capability bit set
- Driver enumerates wrong number of CBBs or cores per CBB (topology mismatch)
- BIOS ACPI _DSM interface (used by driver for discovery) returns wrong PCT capability

**FV TC 22022422103 catches:** TPMI register bits are set correctly by PCode/BIOS.  
**This PV TC catches:** the software stack correctly reads, parses, and reports those bits.  
Both are needed — a silicon that passes FV but fails PV means a driver/tool bug, not a HW bug.

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_As-Is**

PCT discovery via SST tool fully applicable on NWP:
- `SST_TF_CAPABILITY` present in NWP TPMI (SST-TF not ZBB)
- `SST_TF_INFO_1.NUM_CORE_0`: reports max HP cores supportable per CBB
- NWP: 2 CBBs × 48 cores; discovery must enumerate both CBBs correctly
- `intel-speed-select` driver must report NWP topology (not assume DMR's 4 CBBs)

---

## Section B: Test Procedure

### Preconditions
- Linux booted with `intel-speed-select` driver loaded
- PythonSV accessible for cross-validation (optional)

### Test Steps
1. Run SST discovery: `sst perf-profile info`
2. Verify output contains:
   - `feature_state: enabled` (PCT supported and active)
   - `num-hp-cores-supported: <N>` matches TPMI `SST_TF_INFO_1.NUM_CORE_0`
   - Socket/CBB topology: 2 CBBs enumerated (not 4)
   - Per-CBB HP/LP core count consistent with 48 cores/CBB
3. Cross-validate: read `SST_TF_CAPABILITY` via PythonSV namednodes; compare with `sst perf-profile info` output
4. Check sysfs: `ls /sys/bus/pci/.../intel_speed_select/` — verify all expected PCT sysfs entries present
5. Run `sst` with JSON output: `sst -j perf-profile info` — verify parseable output with correct fields

### Pass Criteria
- `sst perf-profile info` exits 0; no errors
- Reported `num-hp-cores-supported` matches TPMI value
- 2 CBBs enumerated (NWP topology)
- All mandatory sysfs entries present (`clos_config`, `feature_state`, `hp_count`)
- JSON output parseable and fields match non-JSON output

---

## Section C: Coverage Assessment

| Category | Status | Notes |
|----------|--------|-------|
| Architecture / Functionality | ✅ Covered | PCT capability discovery via full SW stack |
| Interface and Protocols | ✅ Covered | `intel-speed-select` ioctl, ACPI _DSM, sysfs, TPMI |
| Reset, Power, and Clocking | ⚠️ Partial | Discovery after reset not tested here |
| Programming Model | ✅ Covered | BIOS programs capability; driver reads; tool reports |
| Operational Behavior | ✅ Covered | Discovery accuracy; topology correctness |
| Corner Cases & Error Handling | ⚠️ Partial | Discovery with SST-TF disabled not tested |
| Security / Safety / Policy | ❌ Not Covered | |
| References | ✅ Covered | NWP HAS SST-TF, intel-speed-select driver docs |

---

## Section D: Spec References

- NWP HAS PM Features: https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features
- KB Article: KB/pm_features/sst/sst_main.md
- FV TC (hardware layer): [22022422103](https://hsdes.intel.com/appstore/article-one/#/22022422103)
- `intel-speed-select` driver: kernel.org/doc/html/latest/admin-guide/pm/intel-speed-select.html

---

## Section E: Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Driver assumes DMR topology (4 CBBs) instead of NWP (2 CBBs) | Medium | High — wrong HP count reported | Verify driver uses dynamic TPMI enumeration |
| `sst perf-profile info` reports PCT "not supported" despite TPMI capability set | Medium | High — discovery failure | Cross-check TPMI directly via PythonSV |
| ACPI _DSM method for PCT returns wrong capability on NWP BIOS | Low | Medium | Check BIOS ACPI table for PCT DSM method |
| Kernel driver version incompatible with NWP TPMI layout changes | Low | High | Verify driver version vs NWP TPMI spec revision |

---

## Section F: Recommendations

1. **[NWP critical]** Explicitly assert `sst perf-profile info` enumerates exactly 2 CBBs and 48 cores/CBB — add this as explicit pass criterion in TC description.
2. **[Cross-validation]** Add mandatory PythonSV cross-check of `SST_TF_CAPABILITY.hp_cores` vs `sst perf-profile info` output.
3. **[JSON output]** Use `sst -j perf-profile info` for automated pass/fail parsing in PEGA/PMSS execution.
4. **[Duplication note]** This TC is explicitly complementary to FV [22022422103] — both must pass: FV confirms HW, PV confirms SW stack. Neither replaces the other.
