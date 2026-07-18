# TCD 16031169297 — PCT - TPMI Runtime Control

| Field | Value |
|-------|-------|
| **TCD ID** | [16031169297](https://hsdes.intel.com/appstore/article-one/#/16031169297) |
| **Title** | PCT - TPMI Runtime Control |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030762939 — NWP PM PCT (Priority Core Turbo)](https://hsdes.intel.com/appstore/article-one/#/16030762939) |
| **Sibling TCDs** | [22022420855](https://hsdes.intel.com/appstore/article-one/#/22022420855) — PCT - BIOS Enabling |
| | [22022420858](https://hsdes.intel.com/appstore/article-one/#/22022420858) — PCT - Functionality |
| | [16031169298](https://hsdes.intel.com/appstore/article-one/#/16031169298) — PCT - DQ Rules |
| | [16031169308](https://hsdes.intel.com/appstore/article-one/#/16031169308) — PCT - Negative / Boundary Validation |
| | [16030982802](https://hsdes.intel.com/appstore/article-one/#/16030982802) — PCT - DLCP (Die Level Cherry Picking) |
| | [16031169309](https://hsdes.intel.com/appstore/article-one/#/16031169309) — PCT × C-states (HP C6 mixed workload) |
| | [16031169310](https://hsdes.intel.com/appstore/article-one/#/16031169310) — PCT × RAPL × C-states × thermal |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Architecture / Micro-architecture and Functionality

This TCD validates the **TPMI runtime control path** for PCT — that SST registers are correctly programmed after boot and that PCT can be dynamically enabled/disabled via `SST_PP_CONTROL.feature_state[1]` with correct PCode response. PCT uses SST-TF CLOS partitioning: HP cores (CLOS[0]) get P0max ceiling while LP cores (CLOS[3]) are clipped to ~P1. This TCD owns **register correctness** and **runtime toggle lifecycle** — distinct from BIOS enabling (TCD 22022420855) and frequency enforcement (TCD 22022420858).

> **Architecture overview:** See [TPF 16030762939 — NWP PM PCT](https://hsdes.intel.com/appstore/article-one/#/16030762939) §2 Design Details for full-stack PCT architecture, CLOS mechanism, ordered throttle, and frequency hierarchy.

### NWP-Specific Deltas

- **2 CBBs**: NWP has 2 CBBs × 48 cores = 96 total (DMR: 4 CBBs × 32 cores). CLOS_ASSOC covers more cores per dielet
- **Single NIO**: TPMI registers accessed via `sv.socket0.nio.punit.sst.*` (DMR: `sv.socket0.imh0/imh1.punit.sst.*`)
- **8 HP cores default**: 4 partitions × 2 HP cores; HP TRL target ~4.4 GHz; LP clip ~P1 ~2.3 GHz
- **SST-BF ZBB'd**: No mutual exclusion test needed for SST-BF (only SST-PP × PCT check relevant via DQ Rules TCD)

### TC Coverage Map

| TC | Scope | Environment |
|----|-------|-------------|
| [22022422103](https://hsdes.intel.com/appstore/article-one/#/22022422103) — PCT - TPMI register check | Verify SST_CLOS registers correctly programmed at boot (register-level, no workload) | FV (silicon/emulation) |
| [16030715690](https://hsdes.intel.com/appstore/article-one/#/16030715690) — [PSS]PCT - TPMI register check (FlexconPM) | Same register verification on VP/HSLE via FlexconPM | PSS (VP/HSLE) |
| [16030715694](https://hsdes.intel.com/appstore/article-one/#/16030715694) — [PSS]PCT - enable/disable | Runtime enable/disable via SST_CP_CONTROL on PSS model | PSS (VP/HSLE) |
| [16030768620](https://hsdes.intel.com/appstore/article-one/#/16030768620) — PCT - TPMI runtime enable/disable | Runtime toggle via SST_PP_CONTROL.feature_state[1] on silicon | FV (silicon) |

---

## Section 2: Interfaces and Protocols

### TPMI Registers (Primary — this TCD's scope)

| Register | Access | Description | Expected Value (PCT Enabled) |
|----------|--------|-------------|------------------------------|
| `SST_PP_CONTROL.feature_state[1]` | RW | SST-TF enable/disable bit; bit 1 controls SST-TF (which PCT uses) | 1 (enabled) |
| `SST_PP_STATUS.feature_state[1]` | RO | Reflects current SST-TF feature state after PCode processes CONTROL write | 1 (after enable acknowledged) |
| `SST_PP_STATUS.FEATURE_ERROR_TYPE` | RO | Error code: 0 = OK; nonzero = feature not supported by fuses or invalid transition | 0 |
| `SST_CP_CONTROL.sst_cp_enable` | RW | Enables CLOS-based prioritization (CP); BIOS sets = 1 when PCT active | 1 |
| `SST_CP_CONTROL.SST_CP_PRIORITY_TYPE` | RW | Throttle mode: 1 = Ordered Throttling (LP first, HP maintained) | 1 |
| `SST_CLOS_CONFIG[0].max` | RW | HP TRL ceiling per CDYN; set to `SST_TF_INFO_2.RATIO_0` | HP TRL (~4.4 GHz ratio) |
| `SST_CLOS_CONFIG[0].min` | RW | HP floor; typically P1 | P1 ratio |
| `SST_CLOS_CONFIG[3].max` | RW | LP clip ceiling; set to `SST_TF_INFO_0.LP_CLIP_RATIO_0` | LP clip (~P1 ratio) |
| `SST_CLOS_CONFIG[3].min` | RW | LP floor; typically Pn | Pn ratio |
| `SST_CLOS_ASSOC_0..3[core]` | RW | Core → CLOS mapping; 4 bits/core, 16 cores/register; HP → CLOS[0], LP → CLOS[3] | HP cores = 0x0, LP cores = 0x3 |

### Read-Only Info Registers (verified for correctness, not toggled)

| Register | Access | Description |
|----------|--------|-------------|
| `SST_TF_INFO_0` | RO | LP clip ratios per CDYN bucket; populated by PrimeCode Phase 5 from fuses |
| `SST_TF_INFO_2` | RO | HP TRL ratios per CDYN bucket (SSE/AVX2/AVX3/AMX); populated from fuses |
| `SST_TF_INFO_8` | RO | Core counts: NUM_CORE_0, MAX_LPIDS; bounds max partitions |
| `SST_TF_INFO_10` | RO | DLCP module mask (if applicable); fixed HP core positions from fuse |

### NWP Register Paths

| DMR Path | NWP Path |
|----------|----------|
| `sv.socket0.imh0.punit.sst.*` | `sv.socket0.nio.punit.sst.*` |
| `sv.socket0.imh1.punit.sst.*` | N/A (single NIO) |

---

## Section 3: Reset / Power / Clocking

- **Phase 5 (PrimeCode)**: Reads SST_TF fuses → populates SST_TF_INFO_0/2/8/10 TPMI registers. These RO registers define the bounds for HP TRL, LP clip, and max partitions. This TCD verifies they are populated correctly
- **CPL3 (BIOS)**: Reads BIOS knobs → programs SST_CLOS_CONFIG, SST_CLOS_ASSOC, SST_CP_CONTROL, SST_PP_CONTROL. This TCD verifies the resulting register state
- **Runtime (OS/tool)**: After BIOS handoff, SW can toggle `SST_PP_CONTROL.feature_state[1]` to enable/disable SST-TF at runtime. PCode processes the change within 2 slow-loop cycles (~2ms). This TCD's runtime toggle TCs exercise this path
- **Warm reset**: TPMI state re-initialized from NVRAM/fuses on every boot. Stale CLOS_ASSOC from a previous boot must not persist — verified by register check TCs after reboot

---

## Section 4: Programming Model

### Boot-Time Register Programming (verified by register check TCs)

BIOS programs TPMI SST registers at CPL3 when PCT Partition Count > 0:

| Step | Register Written | Value Source | Observable State |
|------|-----------------|--------------|-----------------|
| 1 | `SST_PP_CONTROL.feature_state[1]` | BIOS sets = 1 (SST-TF active) | SST_PP_STATUS.feature_state[1] = 1 |
| 2 | `SST_CP_CONTROL.sst_cp_enable` | BIOS sets = 1 | CP prioritization active |
| 3 | `SST_CP_CONTROL.SST_CP_PRIORITY_TYPE` | BIOS sets = 1 (Ordered) | LP throttled before HP |
| 4 | `SST_CLOS_CONFIG[0].max` | SST_TF_INFO_2.RATIO_0 (HP TRL) | HP cores ceiling = ~4.4 GHz ratio |
| 5 | `SST_CLOS_CONFIG[3].max` | SST_TF_INFO_0.LP_CLIP_RATIO_0 (LP clip) | LP cores ceiling = ~P1 ratio |
| 6 | `SST_CLOS_ASSOC_0..3[core]` | HP cores → 0x0, LP cores → 0x3 | 4 bits/core, 16 cores/register |
| 7 | `MSR 0x1AD` | SST_TF_INFO_2.RATIO_0 | Must not be 0xFF ([HSD 14025997048](https://hsdes.intel.com/appstore/article-one/#/14025997048)) |

### Runtime Toggle (verified by enable/disable TCs)

When SW writes `SST_PP_CONTROL.feature_state[1]`:

| Operation | CONTROL Write | PCode Response | Observable After |
|-----------|--------------|----------------|-----------------|
| **Disable SST-TF** | feature_state[1] = 0 | PCode processes within 2 slow loops; CLOS enforcement suspended; all cores revert to standard TRL | SST_PP_STATUS.feature_state[1] = 0; SST_CP_CONTROL.sst_cp_enable unchanged (BIOS-programmed) |
| **Re-enable SST-TF** | feature_state[1] = 1 | PCode re-applies CLOS ceilings from existing CLOS_CONFIG/CLOS_ASSOC state | SST_PP_STATUS.feature_state[1] = 1; HP cores resume PCT TRL |
| **Invalid (fuse-blocked)** | feature_state[1] = 1 on non-capable part | PCode rejects; STATUS.FEATURE_ERROR_TYPE ≠ 0 | ERROR_TYPE reflects rejection reason |

### Register Verification Strategy

The register check TCs (22022422103, 16030715690) validate the **full register state** after boot:
1. Read SST_TF_INFO_0/2/8 → extract expected HP TRL, LP clip, core counts
2. Read SST_CLOS_CONFIG[0].max → compare against SST_TF_INFO_2.RATIO_0
3. Read SST_CLOS_CONFIG[3].max → compare against SST_TF_INFO_0.LP_CLIP_RATIO_0
4. Read SST_CLOS_ASSOC per core → verify HP cores mapped to CLOS[0], LP to CLOS[3]
5. Read SST_CP_CONTROL → verify sst_cp_enable = 1, PRIORITY_TYPE = 1
6. Read SST_PP_STATUS → verify feature_state[1] = 1

---

## Section 5: Operational Behavior

| Scenario | Expected Outcome | Verification | TC Link |
|----------|-----------------|--------------|---------|
| Boot with PCT enabled (Partition Count > 0) | All SST_CLOS registers correctly programmed; CLOS_CONFIG[0].max = HP TRL; CLOS_ASSOC maps HP → CLOS[0] | Register read + compare against SST_TF_INFO values | [22022422103](https://hsdes.intel.com/appstore/article-one/#/22022422103), [16030715690](https://hsdes.intel.com/appstore/article-one/#/16030715690) |
| Runtime disable via feature_state[1] = 0 | SST_PP_STATUS.feature_state[1] transitions to 0 within 2 slow loops; CLOS enforcement suspended | Read STATUS after write; confirm transition | [16030768620](https://hsdes.intel.com/appstore/article-one/#/16030768620), [16030715694](https://hsdes.intel.com/appstore/article-one/#/16030715694) |
| Runtime re-enable via feature_state[1] = 1 | SST_PP_STATUS.feature_state[1] transitions back to 1; CLOS ceilings resume; HP cores return to PCT TRL | Read STATUS + CLOS_CONFIG after re-enable | [16030768620](https://hsdes.intel.com/appstore/article-one/#/16030768620), [16030715694](https://hsdes.intel.com/appstore/article-one/#/16030715694) |
| Register correctness on PSS VP/HSLE model | Same register expectations as silicon; validates PrimeCode + PCode fuse→register path pre-silicon | FlexconPM automated register read on VP | [16030715690](https://hsdes.intel.com/appstore/article-one/#/16030715690) |

### Pass/Fail Bar

- **Register check pass criteria**: Every SST_CLOS register field must match the expected value derived from SST_TF_INFO fuse-populated registers. Specifically: `SST_CLOS_CONFIG[0].max == SST_TF_INFO_2.RATIO_0`, `SST_CLOS_CONFIG[3].max == SST_TF_INFO_0.LP_CLIP_RATIO_0`, `SST_CP_CONTROL.sst_cp_enable == 1`, `SST_CP_CONTROL.SST_CP_PRIORITY_TYPE == 1`, and every core's CLOS_ASSOC assignment matches the HP/LP partition algorithm
- **Runtime toggle pass criteria**: `SST_PP_STATUS.feature_state[1]` must reflect the written value within 2 PCode slow-loop cycles (~2ms). `SST_PP_STATUS.FEATURE_ERROR_TYPE` must be 0 on a valid transition. After re-enable, CLOS_CONFIG values must be unchanged from the pre-disable state
- **Failure indicators**: Any register mismatch between expected and actual value; STATUS.FEATURE_ERROR_TYPE ≠ 0 on a valid toggle; CLOS_ASSOC corruption after enable/disable cycle

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| **Stale CLOS_ASSOC after disable→re-enable** | After SST-TF is disabled and re-enabled, CLOS_ASSOC must still correctly map HP/LP cores; stale or zero ASSOC would mismatch | ⚠️ Partial — TC 16030768620 toggles but may not re-read ASSOC after re-enable | Add explicit CLOS_ASSOC re-read after re-enable as pass criterion in TC 16030768620 |
| **Rapid toggle (enable→disable→enable)** | Rapid successive writes to feature_state[1] before PCode acknowledges prior write | ❌ Not covered | New TC or scenario extension — verify STATUS settles correctly after rapid toggle |
| **Warm reset with PCT enabled** | After warm reset, TPMI registers must be re-programmed from NVRAM/fuses; stale state from prior boot must not persist | ⚠️ Verification criterion — add warm-reset register re-read to TC 22022422103 | Add warm-reset boot cycle to TC 22022422103 register check |
| **CLOS_CONFIG consistency across dielets** | On NWP with 2 CBBs, each dielet's CLOS_CONFIG must match; divergent HP TRL across dielets indicates BIOS programming bug | ⚠️ Verification criterion — TC 22022422103 should compare both dielets | Add cross-dielet comparison to register check |
| **Lock bit prevents runtime toggle** | If SST_PP_CONTROL lock bit is set by BIOS, runtime writes to feature_state should be rejected | ❌ Not covered — belongs in negative TCD 16031169308 | Confirm sibling TCD 16031169308 covers lock-bit rejection |
| **Feature not fuse-supported** | Writing feature_state[1] = 1 on a part without SST-TF fuse capability should set FEATURE_ERROR_TYPE | ❌ Not covered — negative path | Sibling TCD 16031169308 scope |

---

## Section 7: Security / Safety / Policy

- **TPMI access control**: SST TPMI registers are protected by `IO_TPMI_REG_LOCK_x` bits set by PCode. After lock, runtime SW cannot modify CLOS_CONFIG/CLOS_ASSOC. Only SST_PP_CONTROL.feature_state remains writable for runtime toggle
- **RACL**: NWP has single NIO + single VCCIN — RACL is ZBB'd. No per-domain access control validation needed
- **No OS driver path in this TCD**: TC 22022422103 uses PythonSV/namednodes for direct TPMI access, not the OS `intel-speed-select` driver. OS driver validation is in PV TCD 16031169214

---

## Section 8: References

| Source | Link |
|--------|------|
| PCT HAS | [docs.intel.com — PCT](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) |
| SST HAS | [docs.intel.com — Intel SST](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| DMR Turbo HAS | [docs.intel.com — DMR Turbo](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html) |
| CPUPM BIOS Knobs Gen 3 | [docs.intel.com — BIOS Knobs](https://docs.intel.com/documents/System-firmware-bios/Domain/ServerCpuPm/Index/CPUPM%20BIOS%20Knobs/BiosKnobs.html) |
| NWP PM MAS | [docs.intel.com — NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |
| NWP PCT CCB | [HSD 14026595435](https://hsdes.intel.com/appstore/article-one/#/14026595435) |
| MSR 0x1AD bug | [HSD 14025997048](https://hsdes.intel.com/appstore/article-one/#/14025997048) |
| KB article — PCT | [KB/pm_features/sst/pct.md](../../pm_features/sst/pct.md) |
| TPF KB — PCT | [TPF_16030762939](../../pm_tpf_kb/16030762839_sst_speed_select_technology/TPF_16030762939_nwp_pm_pct_priority_core_turbo.md) |