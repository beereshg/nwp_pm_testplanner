# TCD 22022420862 — PCT - Ubuntu E2E Functional Test

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420862](https://hsdes.intel.com/appstore/article-one/#/22022420862) |
| **Title** | PCT - Ubuntu E2E Functional Test |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030762939 — NWP PM PCT (Priority Core Turbo)](https://hsdes.intel.com/appstore/article-one/#/16030762939) |
| **Siblings** | [22022420855 — PCT Enabling & Discovery](https://hsdes.intel.com/appstore/article-one/#/22022420855) · [22022420858 — PCT Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420858) |
| **Feature** | Power / SST — PCT end-to-end OS-level Platform Validation |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Architecture / Micro-architecture and Functionality

**PCT - Ubuntu E2E Functional Test** is the Platform Validation (PV) TCD that verifies Priority Core Turbo end-to-end on NWP from the Ubuntu Linux OS perspective. Where sibling TCD 22022420858 (Functionality) uses PythonSV to read TPMI/MSR registers directly, this TCD validates the same invariants via the OS-visible surface: BIOS knob configuration paths, the `intel-speed-select` user-space tool, and `cpufreq` / `ia32_hwp_capabilities` as seen from Linux. The automation framework is `kayak` with `kayak.plugins.sst.plugin`.

**Scope boundary:** BIOS programs PCT partition count and HP module assignments via BIOS Setup knobs; OS boots into the resulting HP/LP CLOS configuration; tests verify HP/LP frequency differentiation, partition correctness, and clean disable from OS.

### PCT Boot-to-OS Flow (NWP)

```
PrimeCode Phase 5
  Reads SST-TF fuses → writes SST_TF_INFO_0/2 (LP clip / HP TRL)

BIOS CPL3
  Reads PCT Partition Count knob
    (EDKII → Socket Config → Advanced PM Config → PCT Configuration)
  max_partitions = SST_TF_INFO_8.NUM_CORE_0 / MAX_LPIDS  [typically 4 on NWP]
  Divides 96 cores (2 CBBs × 48) into N partitions of 24
  Assigns first core per partition → CLOS[0] (HP); rest → CLOS[3] (LP)
  Programs SST_TF TPMI:
    SST_CLOS_CONFIG[0].max = SST_TF_INFO_2.ratio_0  [~4.4 GHz]
    SST_CLOS_CONFIG[3].max = SST_TF_INFO_0.lp_clip_ratio_0  [~P1 ~2.3 GHz]
    SST_CP_CONTROL.priority_type = 1  [Ordered Throttle]
    SST_PP_CONTROL.feature_state[1] = 1  [SST-TF active]
  Custom config path: user selects HP module positions explicitly via knob

Ubuntu OS boots
  intel-speed-select discovers PCT topology:
    Number of HP modules, APIC IDs per module, SST-TF feature flag
  cpufreq/cpuinfo_max_freq reflects HP vs LP ceiling per core
  ia32_hwp_capabilities.highest_performance: HP=P0max, LP=LP_clip
```

### TC Coverage Map

| TC | Title | Scope |
|----|-------|-------|
| [16030717717](https://hsdes.intel.com/appstore/article-one/#/16030717717) | [PV] SST PCT Partition Custom Config | Custom HP module selection via BIOS knob; CLOS programming verified from OS |
| [16030717718](https://hsdes.intel.com/appstore/article-one/#/16030717718) | [PV] SST PCT Partition Sweep | Sweep partition count 0 → max; uniform HP distribution for each count |
| [16030717719](https://hsdes.intel.com/appstore/article-one/#/16030717719) | [PV] SST PCT Disable | Partition count = 0 → no HP/LP split; conventional turbo from OS view |

### NWP-Specific Constants

| Parameter | Value | Source |
|-----------|-------|--------|
| Total cores | 96 (2 CBBs × 48) | NWP topology |
| Default HP count | 8 cores (2 per partition × 4 partitions) | HSD 14026595435 |
| HP TRL | ~4.4 GHz (SST_TF_INFO_2.ratio_0) | HSD 14026595435 |
| LP clip | ~P1 ~2.3 GHz (SST_TF_INFO_0.lp_clip_ratio_0) | PCT HAS |
| Max partitions | SST_TF_INFO_8.NUM_CORE_0 / MAX_LPIDS | PCT HAS |
| SST-BF | ZBB on NWP — no conflict | NWP MAS |
| Automation | `kayak -p kayak.plugins.sst.plugin ... sst_launcher.py --test SST_PCT_MODULE_*` | TC descriptions |
| BIOS knob path | EDKII → Socket Config → Advanced PM Config → PCT Configuration | TC 16030717717 |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Direction | Role in This TCD |
|-----------|----------------|-----------|-----------------|
| BIOS Setup | PCT Partition Count knob | RW (user) | Drives CLOS programming for all three TCs |
| BIOS Setup | PCT HP Module Select knob | RW (user) | Custom Config TC: overrides default first-per-partition rule |
| TPMI | SST_CLOS_CONFIG[0].max | RW (BIOS) | HP frequency ceiling — verified post-boot from OS |
| TPMI | SST_CLOS_CONFIG[3].max | RW (BIOS) | LP clip ceiling — verified post-boot from OS |
| TPMI | SST_PP_CONTROL.feature_state[1] | RW (BIOS) | SST-TF active; OS `intel-speed-select` reads this |
| TPMI | SST_TF_INFO_2.ratio_0 | RO | HP TRL source; BIOS reads for MSR 0x1AD override |
| TPMI | SST_TF_INFO_8.NUM_CORE_0 | RO | Max HP modules = max partition count |
| MSR | IA32_HWP_CAPABILITIES (0x771) | RO | Per-core: HP highest_perf=P0max, LP=LP_clip |
| MSR | IA32_PERF_STATUS (0x198) | RO | Current frequency ratio — HP vs LP differentiation at runtime |
| MSR | 0x1AD PRIMARY_TURBO_RATIO_LIMIT | RO | HP TRL visible to OS; must = SST_TF_INFO_2.ratio_0 |
| Linux sysfs | `/sys/bus/cpu/devices/cpuN/cpufreq/cpuinfo_max_freq` | RO | OS-visible HP vs LP frequency ceiling per core |
| `intel-speed-select` | `isst perf-profile info` | RO | SST topology: HP modules, APIC IDs, feature state |
| `kayak` | `sst_launcher.py --test SST_PCT_MODULE_*` | exec | Test automation framework for all three TCs |

---

## Section 3: Reset, Power, and Clocking

- **Phase 5 (PrimeCode)**: SST-TF fuses read; `SST_TF_INFO_0/1/2/8` populated. HP TRL and LP clip are immutable after this point.
- **BIOS CPL3**: PCT partition count knob read; CLOS_CONFIG[0/3], CLOS_ASSOC, SST_CP_CONTROL, SST_PP_CONTROL programmed. All TCs require a complete boot cycle for each BIOS knob change.
- **Warm reset between tests**: Each `kayak` test case that changes partition count requires a full warm reset to re-run BIOS CPL3 with the new value. These are not runtime-toggle tests.
- **Disable state (TC 16030717719)**: Partition count = 0 → BIOS does not program CLOS differentiation → all cores at conventional turbo. Prior-enabled state (partition > 0) must precede the disable test to confirm clean state removal.

---

## Section 4: Programming Model

### BIOS PCT Knob Effect on CLOS Register Programming

The PCT Partition Count BIOS knob is the single entry point that drives all SST-TF CLOS register state for this feature. BIOS CPL3 reads the knob value and executes the following sequence on each boot:

| Step | Actor | Register | Value / Rule |
|------|-------|----------|-------------|
| 1 | BIOS (reads fuse) | SST_TF_INFO_2.ratio_0 | HP TRL ratio — source of truth for HP frequency ceiling |
| 2 | BIOS (reads fuse) | SST_TF_INFO_0.lp_clip_ratio_0 | LP clip ratio — source of truth for LP frequency ceiling |
| 3 | BIOS (reads fuse) | SST_TF_INFO_8.NUM_CORE_0 | Max HP modules = max valid partition count |
| 4 | BIOS (knob) | PCT Partition Count N | 0 = disabled; 1..max = N partitions of (96/N) cores each |
| 5 | BIOS | SST_CLOS_CONFIG[0].max | = SST_TF_INFO_2.ratio_0 (HP TRL) |
| 6 | BIOS | SST_CLOS_CONFIG[3].max | = SST_TF_INFO_0.lp_clip_ratio_0 (LP clip) |
| 7 | BIOS | SST_CP_CONTROL.priority_type | = 1 (Ordered Throttle — LP throttled before HP) |
| 8 | BIOS | SST_CLOS_ASSOC[core] | HP cores (first per partition) → CLOS[0]; all others → CLOS[3] |
| 9 | BIOS | SST_PP_CONTROL.feature_state[1] | = 1 (SST-TF active) |
| 10 | BIOS | MSR 0x1AD (PRIMARY_TURBO_RATIO_LIMIT) | Overridden with SST_TF_INFO_2.ratio_0 for OS visibility |

When Partition Count = 0: steps 5–10 are skipped. All cores remain at conventional turbo; CLOS_ASSOC is not programmed; `SST_PP_CONTROL.feature_state[1]` stays 0.

### HP Core Selection Algorithm

The HP core assignment follows a deterministic partitioning rule based on APIC ID ordering (MADT order — P-cores first, then compute die atoms, then SoC atoms):

```
total_cores = 96  (2 CBBs × 48 per CBB on NWP)
partition_size = total_cores / N  (e.g. 24 cores per partition for N=4)

For each partition P (0 to N-1):
  HP core = core with index (P × partition_size) in APIC-sorted list
            = first (lowest APIC ID) core in that partition
  → assigned CLOS[0]
  All other cores in partition → CLOS[3] (LP)
```

**Custom Config mode** (TC 16030717717): The `PCT HP Module Select` knob overrides this default — the user specifies which physical module within each partition gets CLOS[0]. BIOS applies the user selection directly to `SST_CLOS_ASSOC` without the default first-per-partition rule.

### OS Discovery of PCT State

After BIOS programs CLOS registers, the OS discovers PCT topology through two paths:

**Path 1 — `intel-speed-select` tool (userspace):**
Reads TPMI `SST_CLOS_ASSOC` and `SST_PP_CONTROL` via `/dev/isst_interface` or ACPI. Reports: number of HP modules, which CPU IDs are HP, feature enabled/disabled state. Used for topology discovery and validation.

**Path 2 — Linux `cpufreq` / HWP:**
`IA32_HWP_CAPABILITIES.highest_performance` (MSR 0x771) is set per-core by hardware: HP cores = P0max, LP cores = LP_clip. The `intel_pstate` driver exposes this as `cpuinfo_max_freq` per CPU sysfs node. This is the OS-visible frequency ceiling that E2E tests observe.

### Disable State Invariants

When PCT Partition Count = 0, the following conditions must hold:
- `SST_PP_CONTROL.feature_state[1]` = 0 (SST-TF not active)
- All `SST_CLOS_ASSOC[core]` entries unset (no CLOS differentiation)
- All cores operate at conventional TRL (MSR 0x1AD not overridden)
- `cpuinfo_max_freq` uniform across all 96 cores
- `intel-speed-select` reports PCT as disabled / no HP modules active

---

## Section 5: Operational Behavior

| Scenario | Expected Behavior | TC |
|----------|-------------------|----|
| Custom HP module selection | BIOS programs CLOS[0] for user-specified positions; OS cpuinfo_max_freq reflects HP TRL on those cores | 16030717717 |
| Default HP (first-per-partition) | HP = lowest APIC-ID core per partition; `intel-speed-select` reports correct HP module list | 16030717717 (default path) |
| Partition sweep (1 → max) | HP count = partition_count × 2; uniform distribution; LP clip on all non-HP cores | 16030717718 |
| Partition count = 0 | No HP/LP split; all cores at conventional turbo; cpuinfo_max_freq uniform | 16030717719 |
| Prior-enabled → disable | Frequency differentiation removed cleanly; no stale CLOS visible from OS | 16030717719 |

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|-----------------|
| **Max partition count boundary** | Partition count above `SST_TF_INFO_8.NUM_CORE_0 / MAX_LPIDS` must be rejected by BIOS; default preserved | [16030717718](https://hsdes.intel.com/appstore/article-one/#/16030717718) sweeps valid range 1→max only — max+1 rejection path **not tested** | Extend TC 16030717718 to include a max+1 step, or file dedicated negative TC |
| **cpuinfo_max_freq vs HWP_CAP alignment** | `cpuinfo_max_freq` (sysfs) and `IA32_HWP_CAPABILITIES.highest_performance` (MSR 0x771) must agree per core; discrepancy = BIOS or `intel_pstate` driver bug | Not a standalone TC — this is a verification criterion that every positive-path TC should apply as a dual-read check | No new TC needed; add as explicit pass criterion in TC descriptions for 16030717717 and 16030717718 |
| **Stale CLOS on disable** | After PCT disabled (partition = 0), `CLOS_ASSOC` entries persist in TPMI but `SST_CP_ENABLE` = 0; OS tools must report no HP/LP differentiation | **Covered** — [16030717719](https://hsdes.intel.com/appstore/article-one/#/16030717719) explicitly starts from prior-enabled state then disables | No gap |
| **Driver prerequisite failure** | If `intel_pstate` not loaded or in passive mode, `cpuinfo_max_freq` reflects BIOS P-state table, not HWP — creates false-pass risk | Infrastructure/precondition check only — a setup failure, not a feature corner case | No new TC; add as precondition guard in kayak test setup |
| **Custom config — out-of-range HP position** | BIOS knob selects an HP module position beyond the valid range for the partition; BIOS must reject or clamp | **Not covered** — [16030717717](https://hsdes.intel.com/appstore/article-one/#/16030717717) tests positive custom config only; no negative-boundary path exists | **New TC needed** — negative custom config validation (analogous to [16030715680](https://hsdes.intel.com/appstore/article-one/#/16030715680) BIOS negative in TCD 22022420858) |

---

## Section 7: Security / Safety / Policy

- BIOS Setup knob access is pre-OS only — no runtime OS escalation risk in this TCD.
- `intel-speed-select` requires root (`CAP_SYS_ADMIN`). `kayak` runs as root on validation images.
- All TCs are positive-path or bounds-check validations — no security-model negative tests in this TCD.

---

## Section 8: References

- [PCT (Priority Core Turbo) HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html)
- [Priority Core Turbo Technology White Paper](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/IC_PCT.html)
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — CLOS config, SST_CP_CONTROL, ordered throttle
- [NWP PM MAS — PCT section](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [CCB HSD 14026595435](https://hsdes.intel.com/appstore/article-one/#/14026595435) — NWP 8 HP cores, 4.4 GHz PCT target
- [PCT Enabling & Discovery TCD 22022420855](https://hsdes.intel.com/appstore/article-one/#/22022420855)
- [PCT Functionality TCD 22022420858](https://hsdes.intel.com/appstore/article-one/#/22022420858)
- KB: KB/pm_features/sst/pct.md
