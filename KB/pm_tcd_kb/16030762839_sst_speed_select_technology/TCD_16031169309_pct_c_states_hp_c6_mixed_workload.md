# TCD 16031169309 — PCT × C-states (HP C6 mixed workload)

| Field | Value |
|-------|-------|
| **TCD ID** | [16031169309](https://hsdes.intel.com/appstore/article-one/#/16031169309) |
| **Title** | PCT × C-states (HP C6 mixed workload) |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030762939 — NWP PM PCT (Priority Core Turbo)](https://hsdes.intel.com/appstore/article-one/#/16030762939) |
| **Sibling TCDs** | [22022420855](https://hsdes.intel.com/appstore/article-one/#/22022420855) — PCT - BIOS Enabling |
| | [22022420858](https://hsdes.intel.com/appstore/article-one/#/22022420858) — PCT - Functionality |
| | [16031169297](https://hsdes.intel.com/appstore/article-one/#/16031169297) — PCT - TPMI Runtime Control |
| | [16031169298](https://hsdes.intel.com/appstore/article-one/#/16031169298) — PCT - DQ Rules |
| | [16031169310](https://hsdes.intel.com/appstore/article-one/#/16031169310) — PCT × RAPL × C-states × thermal |
| | [16031169376](https://hsdes.intel.com/appstore/article-one/#/16031169376) — PCT × Thermal (throttle escalation) |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Architecture / Micro-architecture and Functionality

This TCD validates the **cross-product interaction between PCT (SST-TF CLOS partitioning) and core C6 power states** — specifically that when all HP cores (CLOS[0]) enter C6, LP cores (CLOS[3]) remain clipped to `LP_CLIP_RATIO` and do not gain access to the HP turbo budget. CLOS assignment is static per core, not dynamic per C-state. PCode does not recalculate the HP/LP TRL bucket when HP cores idle — LP clip is maintained regardless.

> **Architecture overview:** See [TPF 16030762939 — NWP PM PCT](https://hsdes.intel.com/appstore/article-one/#/16030762939) §2 Design Details for full-stack PCT architecture, CLOS mechanism, ordered throttle, and frequency hierarchy.

### NWP-Specific Deltas

- **2 CBBs × 48 cores = 96 total**: 8 HP cores across 4 partitions; when all 8 HP cores enter C6, 88 LP cores remain active
- **No MC6 blocking by PCT**: MC6 (module C6) entry depends on all cores in the module being C6-eligible; PCT does not add blocking conditions
- **Single NIO**: TPMI SST registers at `sv.socket0.nio.punit.sst.*`; C-state registers at `sv.socket0.cbb[0-1].compute[*].module[*].*`

### TC Coverage Map

| TC | Scope | Environment |
|----|-------|-------------|
| [22022422104](https://hsdes.intel.com/appstore/article-one/#/22022422104) — PCT - All HP cores in C6 | Place all HP cores in C6 via HWP; verify LP cores remain clipped to LP_CLIP_RATIO; runtime functional validation | FV (silicon) |
| [16030715676](https://hsdes.intel.com/appstore/article-one/#/16030715676) — [PSS]PCT - All HP cores in C6 | Same scenario on HSLE XOS; validates cross-die HPM protocol handles HP-idle state; MC6 not blocked by PCT | PSS (HSLE XOS) |

---

## Section 2: Interfaces and Protocols

### Registers — PCT CLOS State (verified under C6 conditions)

| Register | Access | Role in This TCD |
|----------|--------|-----------------|
| `SST_CLOS_CONFIG[0].max` | RW | HP TRL ceiling — must remain programmed even when all HP cores in C6 |
| `SST_CLOS_CONFIG[3].max` | RW | LP clip ceiling — **must be enforced** while HP cores idle |
| `SST_CLOS_ASSOC_0..3[core]` | RW | HP → CLOS[0], LP → CLOS[3] — static; not modified by C-state transitions |
| `SST_CP_CONTROL.sst_cp_enable` | RW | CP prioritization stays enabled regardless of HP C-state |
| `SST_CP_CONTROL.SST_CP_PRIORITY_TYPE` | RW | Ordered throttle = 1; ordering logic active even when HP idle |

### Registers — C-state Observation

| Register / MSR | Access | Role in This TCD |
|----------------|--------|-----------------|
| `IA32_HWP_REQUEST (MSR 0x774)` | RW | Per-core HWP desired/min/max; TC sets max-freq request to force LP to attempt turbo |
| `IA32_HWP_CAPABILITIES (MSR 0x771)` | RO | `highest_perf`: LP cores should report LP clip (not P0max) under PCT |
| `IA32_MPERF / IA32_APERF (MSR 0xE7/0xE8)` | RO | Effective frequency measurement — LP must not exceed LP_CLIP_RATIO |
| `cpuinfo_max_freq` (sysfs) | RO | OS-visible max freq per core — LP cores show LP clip value |
| C6 residency counters (`MSR 0x3FD` / `IA32_MC6_STATUS`) | RO | Confirm HP cores are actually resident in C6 |

### NWP Register Paths

| Component | Path |
|-----------|------|
| TPMI SST | `sv.socket0.nio.punit.sst.*` |
| Compute module | `sv.socket0.cbb[0-1].compute[0-3].module[0-7].*` |

---

## Section 3: Reset / Power / Clocking

- **Boot**: PCT state established at CPL3 (BIOS programs CLOS_CONFIG, CLOS_ASSOC, CP_CONTROL). C6 capability independently enabled by BIOS via `MSR 0xE2` (IA32_POWER_CTL) and package C-state configuration
- **Runtime**: After boot, HP cores may enter C6 via MWAIT or autonomous C-state promotion. CLOS assignments do not change on C6 entry/exit — they are static until next BIOS reprogramming
- **C6 entry/exit**: When an HP core enters C6, PCode updates the active-core-count for legacy TRL recalculation, but **FACT/SST-TF (PCT) does not recalculate HP/LP TRL buckets** based on C-state — LP clip is maintained unconditionally
- **MC6 (module C6)**: All cores in a module must be C6-eligible for MC6 entry. PCT does not add blocking conditions. If both HP and LP cores in the same module are in C6, MC6 proceeds

---

## Section 4: Programming Model

### Key Architectural Invariant

PCT CLOS enforcement is **C-state-independent**:

| HP Core State | LP Core Behavior | Reason |
|---------------|-----------------|--------|
| All HP in C0 (active) | LP clipped to LP_CLIP_RATIO | Standard PCT enforcement |
| All HP in C6 (idle) | LP **still clipped** to LP_CLIP_RATIO | CLOS assignment is static; PCode does not recalculate FACT/SST-TF TRL on C-state change |
| Mixed (some HP C0, some HP C6) | LP clipped to LP_CLIP_RATIO | Same — CLOS-based, not active-count-based |
| HP exits C6 → C0 | LP remains clipped; HP resumes at HP TRL | No transient where LP gets HP turbo budget |

### Why LP Cores Don't Get HP Turbo When HP Sleeps

In legacy (non-PCT) TRL, fewer active cores → higher per-core turbo ratio. Under PCT/SST-TF, this legacy recalculation **does not override the CLOS-based LP clip**:

1. PCode maintains two separate frequency ceilings: WP4_HP (from CLOS_CONFIG[0].max) and WP4_LP (from CLOS_CONFIG[3].max)
2. Even when HP active count = 0, PCode broadcasts WP4_LP = LP_CLIP_RATIO to LP cores
3. LP cores cannot exceed their CLOS ceiling regardless of how many cores are active system-wide
4. This is by design: PCT guarantees deterministic LP clipping to prevent workload interference

### Verification Strategy

1. Boot with PCT enabled (Partition Count > 0, 8 HP cores)
2. Verify initial state: HP cores at HP TRL, LP cores at LP clip
3. Force all HP cores into C6 (via `idle` injection or MWAIT on HP core set)
4. Confirm HP cores show C6 residency (MSR 0x3FD or residency counters)
5. On LP cores: request max frequency via HWP (`IA32_HWP_REQUEST.desired = 0xFF`)
6. Measure LP effective frequency via APERF/MPERF — must not exceed LP_CLIP_RATIO
7. Wake HP cores from C6 → verify they resume at HP TRL; LP remains clipped

---

## Section 5: Operational Behavior

| Scenario | Expected Outcome | Verification | TC Link |
|----------|-----------------|--------------|---------|
| All HP cores in C6, LP cores active requesting max freq | LP effective frequency ≤ LP_CLIP_RATIO; LP does not gain HP turbo budget | APERF/MPERF ratio on LP cores; cpuinfo_max_freq | [22022422104](https://hsdes.intel.com/appstore/article-one/#/22022422104) |
| HP cores in C6, MC6 entry eligible | MC6 proceeds without PCT-related blocking; SST_CP_STATUS HP mask consistent | MC6 residency counter increments; no NLOG assertion | [16030715676](https://hsdes.intel.com/appstore/article-one/#/16030715676) |
| HP cores wake from C6 | HP cores resume at HP TRL ceiling; LP remains clipped; no transient frequency spike on LP | HP effective freq = HP TRL after wake; LP unchanged | [22022422104](https://hsdes.intel.com/appstore/article-one/#/22022422104) |
| HSLE XOS: cross-die HPM with HP idle | IMH-CBB HPM message delivered correctly on HSLE; no model assertion | SST_CP_STATUS consistent; no NLOG | [16030715676](https://hsdes.intel.com/appstore/article-one/#/16030715676) |

### Pass/Fail Bar

- **LP clip invariant**: LP core effective frequency (APERF/MPERF ratio) must not exceed `SST_TF_INFO_0.LP_CLIP_RATIO_0` at any point while HP cores are in C6. A single LP core exceeding LP_CLIP_RATIO by more than 1 ratio bin (measurement noise margin) is a FAIL
- **C6 residency confirmation**: HP cores must show >90% C6 residency during the measurement window (via residency counters or MSR 0x3FD). If HP cores are not actually in C6, the test is invalid, not a pass
- **MC6 non-blocking**: If all cores in a module (both HP and LP) are C6, MC6 residency counter must increment. If MC6 is blocked while PCT is active with all-core-C6, that is a FAIL
- **No NLOG/assertion**: Zero NLOG errors or model assertions during the HP C6 → LP active scenario on HSLE XOS
- **HP wake recovery**: After HP cores exit C6, HP effective frequency must return to HP TRL within 100 μs (PCode workpoint recalculation latency). LP frequency must remain at LP_CLIP_RATIO throughout

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| **All HP cores in C6 simultaneously** | Primary scenario — all 8 HP cores idle while 88 LP cores run max workload | ✅ Covered by TC 22022422104 and TC 16030715676 | No action |
| **Partial HP C6 (some HP active, some C6)** | Mixed HP C-state; LP clip must persist regardless of how many HP cores are idle | ⚠️ Verification criterion — TC 22022422104 focuses on all-HP-C6; add mixed scenario as variant | Extend TC 22022422104 or add scenario variant |
| **HP C6 exit during LP measurement** | Race condition: HP waking from C6 while LP frequency is being measured; LP must not get transient HP turbo | ⚠️ Verification criterion — add timing check around HP wake event | Add C6 exit timing verification to TC 22022422104 |
| **MC6 entry with mixed HP/LP in same module** | Module has both HP (CLOS[0]) and LP (CLOS[3]) cores; MC6 requires all cores in module to be C6-eligible | ✅ Covered by TC 16030715676 (HSLE XOS validates MC6 non-blocking) | No action |
| **PCT disabled while HP in C6** | Runtime disable of SST-TF while HP cores are in deep C-state; CLOS enforcement should cleanly release | ❌ Not covered — cross-product with TPMI runtime control (TCD 16031169297) | Consider new TC or extend TCD 16031169297 |
| **RAPL PL1 throttle with HP in C6** | Ordered throttle active (LP throttled first) while HP cores are idle; throttle logic must handle zero-active-HP correctly | ❌ Not covered — cross-product with RAPL (TCD 16031169310 scope) | Sibling TCD 16031169310 |

---

## Section 7: Security / Safety / Policy

- **Deterministic LP clipping**: The C-state-independent LP clip prevents a scenario where an attacker could infer HP core C-state by observing LP core frequency changes. LP frequency is constant regardless of HP activity
- **No covert channel**: Because CLOS assignments are static and LP clip does not change with HP C-state, there is no side-channel between HP and LP frequency domains
- **TPMI access**: SST registers are protected by IO_TPMI_REG_LOCK after BIOS handoff; no runtime modification of CLOS assignments possible without reset

---

## Section 8: References

| Source | Link |
|--------|------|
| PCT HAS | [docs.intel.com — PCT](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |
| SST HAS | [docs.intel.com — Intel SST](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| NWP PM MAS | [docs.intel.com — NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |
| NWP PCT CCB | [HSD 14026595435](https://hsdes.intel.com/appstore/article-one/#/14026595435) |
| KB article — PCT | [KB/pm_features/sst/pct.md](../../pm_features/sst/pct.md) |
| TPF KB — PCT | [TPF_16030762939](../../pm_tpf_kb/16030762839_sst_speed_select_technology/TPF_16030762939_nwp_pm_pct_priority_core_turbo.md) |
| Sibling TCD — TPMI Runtime Control | [TCD 16031169297](https://hsdes.intel.com/appstore/article-one/#/16031169297) |
| Sibling TCD — RAPL × C-states × thermal | [TCD 16031169310](https://hsdes.intel.com/appstore/article-one/#/16031169310) |
| Co-Design MCP spec query | FACT/SST-TF C-state interaction, 2026-07-18 |