# TCD 16031169217 — PCT - PV BIOS Disable

| Field | Value |
|-------|-------|
| **TCD ID** | [16031169217](https://hsdes.intel.com/appstore/article-one/#/16031169217) |
| **Title** | PCT - PV BIOS Disable |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030762939 — NWP PM PCT (Priority Core Turbo)](https://hsdes.intel.com/appstore/article-one/#/16030762939) |
| **Siblings** | [22022420862 — PCT - PV BIOS Configuration](https://hsdes.intel.com/appstore/article-one/#/22022420862) · [16031169214 — PCT - PV Discovery](https://hsdes.intel.com/appstore/article-one/#/16031169214) |
| **Feature** | Power / SST — PCT PV: BIOS partition count = 0 → conventional turbo, no HP/LP split |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Architecture / Micro-architecture and Functionality

**PCT - PV BIOS Disable** validates that PCT is correctly disabled when the BIOS PCT Partition Count knob is set to 0. When disabled, all cores must operate in conventional turbo behavior with no HP/LP frequency differentiation visible from the Ubuntu OS. This is a distinct scenario from PCT configuration (positive path) — it tests the disable/default state and clean removal of any prior HP/LP split.

**Scope:** partition count = 0 → no CLOS differentiation → all cores at conventional TRL as observed from `intel-speed-select` and `cpufreq`. Sibling TCD [22022420862 — PCT - PV BIOS Configuration](https://hsdes.intel.com/appstore/article-one/#/22022420862) covers the positive-path partition count configuration.

> **Architecture overview:** See [TPF 16030762939 — NWP PM PCT](https://hsdes.intel.com/appstore/article-one/#/16030762939) §2 Design Details for boot flow, CLOS mechanism, and frequency hierarchy.

### TC Coverage Map

| TC | Title | Scope |
|----|-------|-------|
| [16030717719](https://hsdes.intel.com/appstore/article-one/#/16030717719) | [PV] SST PCT Disable | Partition count = 0 → no HP/LP split; conventional turbo from OS view; prior-enabled state required as baseline |

### NWP-Specific Deltas

- Default state on NWP: PCT is **disabled by default** (partition count = 0, unlike GNR where CAPID4.bit29 auto-enables)
- Test must start from a prior-enabled state (partition count > 0) to validate clean removal of HP/LP differentiation
- After disable: all 96 cores must show the same `cpuinfo_max_freq`; MSR 0x1AD must not carry HP TRL override

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Direction | Role |
|-----------|----------------|-----------|------|
| BIOS Setup | PCT Partition Count knob = 0 | RW (user) | Disables PCT; BIOS skips CLOS programming |
| `intel-speed-select` | `isst perf-profile info` | RO | Must report PCT disabled / no HP modules active |
| Linux sysfs | `/sys/bus/cpu/devices/cpuN/cpufreq/cpuinfo_max_freq` | RO | Must be uniform across all 96 cores |
| MSR | 0x1AD PRIMARY_TURBO_RATIO_LIMIT | RO | Must not carry HP TRL override — should be conventional TRL |
| TPMI | `SST_PP_CONTROL.feature_state[1]` | RO | Must = 0 when PCT disabled |

---

## Section 3: Reset, Power, and Clocking

- **Precondition**: System must boot once with PCT enabled (partition count > 0) to establish a valid prior-enabled baseline — this is the starting state for the disable test
- **Disable boot**: Set partition count = 0 in BIOS; warm reset; BIOS CPL3 skips CLOS programming
- **Post-disable state**: `SST_CLOS_ASSOC` entries may persist in TPMI SRAM but `SST_CP_ENABLE = 0`; OS must not see HP/LP differentiation

---

## Section 4: Programming Model

When PCT Partition Count = 0, BIOS does NOT program SST-TF CLOS registers. The invariants that must hold from the OS perspective:

| Invariant | Expected value | Verification |
|-----------|---------------|-------------|
| All cores at same frequency ceiling | Uniform `cpuinfo_max_freq` | Read per-core sysfs |
| `intel-speed-select` reports no HP modules | HP module count = 0 | `isst perf-profile info` |
| MSR 0x1AD not overridden | Conventional TRL across all cores | Read from OS |
| `SST_PP_CONTROL.feature_state[1]` = 0 | SST-TF inactive | `isst` or TPMI read |

---

## Section 5: Operational Behavior

| Scenario | Expected Behavior | TC | Pass/Fail Bar |
|----------|-------------------|----|---------------|
| PCT disabled (partition count = 0) | No HP/LP frequency split; all 96 cores uniform `cpuinfo_max_freq`; `intel-speed-select` reports no HP modules | [16030717719](https://hsdes.intel.com/appstore/article-one/#/16030717719) | All `cpuinfo_max_freq` values equal; `isst` HP count = 0 |
| Prior-enabled → disable transition | Prior HP/LP differentiation cleanly removed; stale `CLOS_ASSOC` in TPMI does not cause misreporting | [16030717719](https://hsdes.intel.com/appstore/article-one/#/16030717719) | No HP/LP split visible from OS despite stale TPMI entries |

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action |
|-------------|-------------|-----------------|--------|
| **Stale CLOS_ASSOC after disable** | `CLOS_ASSOC` persists in TPMI SRAM; `SST_CP_ENABLE = 0` — OS tools must show no differentiation | TC 16030717719 covers the positive-path disable check; stale-state negative assertion not explicit (G8) | Extend TC 16030717719 to add stale-state negative assertion |
| **Re-enable after disable** | Re-enable (partition count > 0) must produce fresh HP/LP differentiation; stale state must not reactivate incorrectly (G9) | Not in TC 16030717719 | Add as step 4 in TC 16030717719 or new TC |

---

## Section 7: Security / Safety / Policy

- BIOS Setup access is pre-OS only; no runtime escalation risk.
- Disable state is the default NWP configuration (no PCT partition count specified).

---

## Section 8: References

- [PCT (Priority Core Turbo) HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html)
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html)
- [NWP PM MAS — PCT section](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [PCT - PV BIOS Configuration TCD 22022420862](https://hsdes.intel.com/appstore/article-one/#/22022420862)
- [PCT - PV Discovery TCD 16031169214](https://hsdes.intel.com/appstore/article-one/#/16031169214)
- KB: KB/pm_features/sst/pct.md
