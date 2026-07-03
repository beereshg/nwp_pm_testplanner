# Deep Analysis: [PV] PMSS - SST PCT Partition Custom Config

| Field | Value |
|-------|-------|
| **HSD ID** | 16030717717 |
| **Title** | [PV] PMSS - SST PCT Partition Custom Config |
| **Date** | 2026-06-09 |
| **Target Program** | NWP (Newport) |
| **Feature** | SST |
| **Sub-Feature** | PCT (Priority Core Turbo) |
| **Validation Layer** | **OS Software Stack** — distinct from FV hardware register layer |
| **Feature Classification** | **Silicon-heavy** (CAPID4.bit29 fuse-gated; HW enforces HP/LP TRL) with firmware orchestration (PCode/BIOS program CLOS config) |
| **NWP Disposition** | **Runnable_As-Is** |

---

## Duplication Analysis vs FV

### FV Counterpart
- [22022422105](https://hsdes.intel.com/appstore/article-one/#/22022422105) PCT - Default HP core selection (FV TCD 22022420858)
- [16030715686](https://hsdes.intel.com/appstore/article-one/#/16030715686) [PSS] PCT - Default HP core selection

### Assessment: **Complementary — NOT a duplicate**

**Validation layers differ fundamentally:**

| Aspect | FV TC 22022422105 | PV TC 16030717717 (this TC) |
|--------|-------------------|------------------------------|
| Interface | PythonSV → namednodes → TPMI MMIO direct | SST tool → `intel-speed-select` kernel driver → sysfs → TPMI |
| Bug class caught | Silicon/TPMI encoding, PCode handler errors | Kernel driver, SST tool, BIOS ACPI _DSM interface |
| OS required | No (bare metal PythonSV) | Yes (Linux with intel-speed-select driver loaded) |
| Validates | Hardware implements PCT correctly | Software stack correctly exposes PCT to OS |

**Unique coverage of this PV TC:**
- Validates `intel-speed-select` driver correctly programs `SST_CLOS_CONFIG` when BIOS selects a custom partition count
- Validates `sst perf-profile config` CLI correctly translates user partition count to TPMI writes
- Validates sysfs ABI exposes correct HP/LP core sets after custom partition configuration
- Catches driver bugs (e.g., off-by-one in partition→CLOS mapping)

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_As-Is**

PCT with custom partition configuration is supported on NWP:
- SST-TF active on NWP (not ZBB)
- 2 CBBs × 48 cores = 96 total cores; partition config applies per CBB
- `intel-speed-select` driver must correctly handle NWP's 2-CBB topology

NWP-specific consideration: verify `sst` tool enumerates both CBBs when setting custom partition count; driver must not assume 4 CBBs (DMR topology).

---

## Section B: Test Procedure

### Preconditions
- NWP-IMH system booted to Linux with `intel-speed-select` driver loaded
- Verify: `lsmod | grep intel_speed_select`
- SST-TF not ZBB: `sst turbofreq info` should show enabled

### Test Steps
1. Read current PCT config: `sst perf-profile info`
2. Set custom partition count (e.g., 4 HP cores/CBB): `sst perf-profile config --clos 0 --core-count 4`
3. Verify via sysfs: `cat /sys/bus/pci/.../intel_speed_select/clos_config`
4. Verify via PythonSV cross-check (optional): read `SST_CLOS_CONFIG[0]` via namednodes
5. Run workload and verify HP cores receive higher turbo frequency

### Pass Criteria
- `sst perf-profile config` exits 0; no driver errors in dmesg
- sysfs reports correct partition count matching configuration
- HP cores get higher TRL than LP cores under load
- No regression in non-PCT operation after reconfiguration

---

## Section C: Coverage Assessment

| Category | Status | Notes |
|----------|--------|-------|
| Architecture / Functionality | ✅ Covered | PCT partition via BIOS and SST tool path |
| Interface and Protocols | ✅ Covered | `intel-speed-select` driver, sysfs, TPMI CLOS config |
| Reset, Power, and Clocking | ⚠️ Partial | Post-reset partition config persistence not tested here |
| Programming Model | ✅ Covered | BIOS knob + SST tool custom config path |
| Operational Behavior | ✅ Covered | Custom partition active under workload |
| Corner Cases & Error Handling | ⚠️ Partial | Invalid partition counts not tested (see FV TC 16030768621) |
| Security / Safety / Policy | ❌ Not Covered | Privilege check for sst tool not tested |
| References | ✅ Covered | NWP HAS SST-TF, intel-speed-select driver docs |

---

## Section D: Spec References

- NWP HAS PM Features: https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features
- KB Article: KB/pm_features/sst/sst_main.md
- FV TC (hardware layer): [22022422105](https://hsdes.intel.com/appstore/article-one/#/22022422105)

---

## Section E: Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `intel-speed-select` driver assumes 4 CBBs (DMR) instead of 2 (NWP) | Medium | High — wrong HP core set assigned | Verify driver enumerates CBBs dynamically; check sysfs per-CBB entries |
| SST tool misreads NWP TPMI capability register | Medium | Medium — wrong max partition count reported | Cross-check with PythonSV direct TPMI read |
| Partition count config not persisted across S3 | Low | Low | Out of scope for this TC |

---

## Section F: Recommendations

1. **[NWP topology]** Add explicit check that `sst perf-profile info` shows 2 CBB instances (not 4) and correct per-CBB core count (48).
2. **[Cross-validation]** After setting custom partition via SST tool, add PythonSV readback of `SST_CLOS_CONFIG` to confirm HW matches SW view.
3. **[HAS Reference]** Link NWP SST-TF HAS section in TC description.
