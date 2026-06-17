# Deep Analysis: [PV] PMSS - SST PCT Disable

| Field | Value |
|-------|-------|
| **HSD ID** | 16030717719 |
| **Title** | [PV] PMSS - SST PCT Disable |
| **Date** | 2026-06-09 |
| **Target Program** | NWP (Newport) |
| **Feature** | SST |
| **Sub-Feature** | PCT (Priority Core Turbo) |
| **Validation Layer** | **OS Software Stack** — validates OS correctly enforces disabled state via sysfs |
| **Feature Classification** | **Silicon-heavy** (disable writes SST_CP_ENABLE=0 to HW; silicon stops HP/LP TRL differentiation) with firmware/driver orchestration |
| **NWP Disposition** | **Runnable_As-Is** |

---

## Duplication Analysis vs FV

### FV Counterparts
- [16030715684](https://hsdes.intel.com/appstore/article-one/#/16030715684) [PSS] PCT - Default Disabled
- [16030715694](https://hsdes.intel.com/appstore/article-one/#/16030715694) [PSS] PCT - enable/disable
- [16030768620](https://hsdes.intel.com/appstore/article-one/#/16030768620) PCT - TPMI runtime enable/disable

### Assessment: **Complementary — NOT a duplicate**

**Validation layer differentiation:**

| FV TCs 16030715684 / 16030768620 | This PV TC 16030717719 |
|-----------------------------------|------------------------|
| Reads `PCT_CONTROL.enable` TPMI register directly | Calls `sst perf-profile disable` CLI; reads sysfs |
| Validates: hardware register reflects disabled state | Validates: driver + sysfs correctly report and enforce disabled state |
| Does NOT test OS scheduler awareness | Tests that OS scheduler is notified (kernel HWP hint via driver) |
| Does NOT exercise `intel-speed-select` disable path | Explicitly exercises driver's `disable` codepath |

**Unique bugs caught by this PV TC:**
- Driver `disable` codepath fails silently (no TPMI write, but returns success)
- sysfs `feature_state` not updated to "disabled" after `sst perf-profile disable`
- OS scheduler continues pinning to HP cores after PCT disabled (HWP hint not cleared)
- `sst perf-profile info` shows "enabled" after disable (stale driver cache)

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_As-Is**

PCT disable via OS stack fully applicable on NWP:
- When partition count = 0 (BIOS default on NWP): all cores in same CLOS → conventional turbo
- `sst perf-profile disable` must write `SST_CP_CONTROL.SST_CP_ENABLE = 0` via driver
- NWP: verify both CBBs correctly updated when PCT is disabled

---

## Section B: Test Procedure

### Preconditions
- Linux booted with `intel-speed-select` driver and PCT enabled (partition count > 0)
- Baseline: HP cores receiving higher turbo than LP cores (verified via turbostat)

### Test Steps
1. Confirm PCT active: `sst perf-profile info` → feature_state = enabled; HP cores identified
2. Disable PCT: `sst perf-profile disable` (partition count = 0 via BIOS or runtime)
3. Verify driver reports disabled: `sst perf-profile info` → feature_state = disabled
4. Verify sysfs: all cores in same CLOS (no HP/LP distinction)
5. Verify hardware (optional PythonSV): `SST_CP_CONTROL.SST_CP_ENABLE = 0` per CBB
6. Run workload: all cores must achieve same TRL (no HP/LP differential)
7. Verify no stale HP core hints in `/proc/cpuinfo` or kernel scheduler logs

### Pass Criteria
- `sst perf-profile disable` exits 0; dmesg clean
- sysfs shows all cores as LP (or no HP designation)
- `turbostat` shows uniform TRL across all cores under load
- No dmesg errors; no hung tasks or scheduler warnings

---

## Section C: Coverage Assessment

| Category | Status | Notes |
|----------|--------|-------|
| Architecture / Functionality | ✅ Covered | PCT disable path via OS stack |
| Interface and Protocols | ✅ Covered | `intel-speed-select` driver disable codepath, sysfs |
| Reset, Power, and Clocking | ⚠️ Partial | Does not test that disable state persists across warm reset |
| Programming Model | ✅ Covered | BIOS default=disabled + runtime disable via SST tool |
| Operational Behavior | ✅ Covered | No HP/LP differential when disabled; uniform turbo |
| Corner Cases & Error Handling | ⚠️ Partial | Does not test disable when HP cores are active in workload |
| Security / Safety / Policy | ❌ Not Covered | |
| References | ✅ Covered | NWP HAS SST-TF |

---

## Section D: Spec References

- NWP HAS PM Features: https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html#pm-features
- KB Article: KB/pm_features/sst/sst_main.md
- FV TC (hardware layer): [16030715684](https://hsdes.intel.com/appstore/article-one/#/16030715684), [16030768620](https://hsdes.intel.com/appstore/article-one/#/16030768620)

---

## Section E: Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Driver disable path skips one CBB on NWP dual-CBB topology | Medium | High — one CBB still in PCT mode | Verify both CBBs show `SST_CP_ENABLE=0` via PythonSV |
| OS scheduler retains stale HP core affinity after disable | Low | Medium | Check scheduler via `/proc/cpuinfo` APERFMPERF flags post-disable |

---

## Section F: Recommendations

1. **[NWP-specific]** Explicitly check both CBBs (cbb0 and cbb1) for `SST_CP_CONTROL.SST_CP_ENABLE = 0` after disable.
2. **[Regression]** Re-enable PCT after disable to confirm round-trip (disable → enable → disable) works.
3. **[HAS Reference]** Link NWP SST-TF HAS section explicitly in TC description.
