# TCD 16030785069 -- SST-TF (Turbo Frequency) E2E Functionality

| Field | Value |
|-------|-------|
| **TCD ID** | [16030785069](https://hsdes.intel.com/appstore/article-one/#/16030785069) |
| **Title** | SST-TF (Turbo Frequency) E2E Functionality |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030762937 -- NWP PM SST-TF (Turbo Frequency)](https://hsdes.intel.com/appstore/article-one/#/16030762937) |
| **Child TCs** | [16030717635](https://hsdes.intel.com/appstore/article-one/#/16030717635) -- SST-TF Operation LinuxTool AVX512 (PV)<br>[16030717650](https://hsdes.intel.com/appstore/article-one/#/16030717650) -- Validate HP-Core HWP Min/Max (PV)<br>[16030717713](https://hsdes.intel.com/appstore/article-one/#/16030717713) -- SST-TF Operation LinuxTool AVX2 (PV) |
| **KB last updated** | 2026-07-16 |

---

## Section 1: Architecture / Micro-architecture and Functionality

**SST-TF E2E Functionality** validates the end-to-end turbo frequency partitioning behavior under real workloads. Unlike the Enabling & Discovery TCD (which validates register programming), this TCD confirms that **HP cores achieve elevated TRL ratios** and **LP cores are frequency-clipped** under actual stress patterns (AVX2, AVX-512).

The E2E flow exercises the full stack: BIOS enables SST-TF at CPL3, PCode loads TRL tables via SstManager/TrlManager, OS subscribes to Intel SST via the Linux intel_speed_select tool, and workloads are pinned to HP/LP core groups to verify frequency differentiation.

### Key Scenarios

| Scenario | What is validated |
|----------|-------------------|
| HP cores under AVX-512 load | HP cores operate at HP TRL bucket ratio (CDYN5 = AVX-512 TRL from SST_TF_INFO_6) |
| HP cores under AVX2 load | HP cores operate at HP TRL bucket ratio (CDYN3 = AVX2 TRL from SST_TF_INFO_4) |
| LP cores under any load | LP cores clipped to LP_CLIP_RATIO for the corresponding CDYN level |
| HP cores in C6 | When all HP cores enter C6, LP cores remain clipped; system stable (no frequency spike on LP) |
| SST-CP + SST-TF interaction | CLOS-based HWP min/max enforcement operates correctly when both SST-CP and SST-TF are active |
| Dynamic enable/disable under load | Toggling feature_state[1] while workloads run causes TRL transition within 1+ slow-loop |

### NWP-Specific Deltas

- NWP uses **DLCP (Die-Level Cherry Picking)** -- HP cores are fuse-pinned, not user-selectable at runtime.
- NWP has **2 CBBs** -- E2E tests must validate both CBB0 and CBB1 HP/LP behavior independently.
- Intel speed_select tool must target NWP TPMI interface (not legacy MSR path).
- SST-CP interaction: NWP supports SST-CP for HWP min/max enforcement alongside SST-TF.
- AVX-512 TRL may differ from SSE TRL by 2-4 ratio bins on NWP SKUs.

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [16030717635 -- SST-TF Operation LinuxTool AVX512](https://hsdes.intel.com/appstore/article-one/#/16030717635) | E2E AVX-512 workload | Enable SST-TF + SST-CP via intel_speed_select; run AVX-512 stress on HP cores; verify TRL at CDYN5 bucket ratio |
| [16030717650 -- HP-Core HWP Min/Max Enforcement](https://hsdes.intel.com/appstore/article-one/#/16030717650) | SST-CP + SST-TF interaction | Verify SST-CP CLOS config for HP groups with SST-TF active; HWP min/max honored per CLOS group |
| [16030717713 -- SST-TF Operation LinuxTool AVX2](https://hsdes.intel.com/appstore/article-one/#/16030717713) | E2E AVX2 workload | Enable SST-TF + SST-CP via intel_speed_select; run AVX2 stress on HP cores; verify TRL at CDYN3 bucket ratio |
| ~~[16030717608 -- SST_TF_LP_Disable_UACT](https://hsdes.intel.com/appstore/article-one/#/16030717608)~~ | ~~LP disable~~ | ~~REJECTED -- superseded by DLCP fuse-based LP assignment~~ |
| ~~[16030717638 -- TRL Throttling SSE](https://hsdes.intel.com/appstore/article-one/#/16030717638)~~ | ~~TRL throttling SSE~~ | ~~REJECTED -- merged into Operation LinuxTool TCs~~ |
| ~~[16030717690 -- TRL Throttling AVX2](https://hsdes.intel.com/appstore/article-one/#/16030717690)~~ | ~~TRL throttling AVX2~~ | ~~REJECTED -- merged into Operation LinuxTool TCs~~ |
| ~~[16030717692 -- TRL Throttling AVX512](https://hsdes.intel.com/appstore/article-one/#/16030717692)~~ | ~~TRL throttling AVX512~~ | ~~REJECTED -- merged into Operation LinuxTool TCs~~ |
| ~~[16030717707 -- Discovery Turbo Disabled](https://hsdes.intel.com/appstore/article-one/#/16030717707)~~ | ~~Turbo disabled discovery~~ | ~~REJECTED -- covered by Enabling TCD ZBB checks~~ |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Direction | Description |
|-----------|----------------|-----------|-------------|
| TPMI SST | SST_PP_CONTROL.feature_state[1] | RW | SST-TF enable bit. Must be 1 for E2E functionality. |
| TPMI SST | SST_CP_CONTROL.feature_state | RW | SST-CP enable. Required for HWP min/max enforcement with TF. |
| TPMI SST | SST_TF_INFO_2..7 | RO | HP TRL ratios per CDYN level. E2E verifies frequency matches these. |
| TPMI SST | SST_TF_INFO_0.LP_CLIP_RATIO_0..5 | RO | LP clip ratios. E2E verifies LP cores do not exceed. |
| MSR | 0x1AD (PRIMARY_TURBO_RATIO_LIMIT) | RW | HP TRL reflected here when TF active. OS reads to verify. |
| MSR | 0x771 (HWP_REQUEST) | RW | OS/SST-CP writes min/max; PCode enforces within CLOS limits. |
| OS tool | intel_speed_select | CLI | Linux tool for SST control: enable/disable TF, query status. |
| PythonSV | sv.socket0.nio0.tpmi.sst_tf_info_2.hp_trl_ratio_0 | RO | HP TRL bucket 0 (SSE). |
| PythonSV | sv.socket0.cbbs.computes.modules.cores.threads.msr(0x198) | RO | IA32_PERF_STATUS -- actual operating frequency. |

---

## Section 3: Reset / Power / Clocking

- **Boot**: SST-TF + SST-CP enabled by BIOS at CPL3. TRL tables active before OS handoff.
- **C-state cycle**: HP/LP TRL assignment persists across core C-states. No re-enable needed.
- **Reset**: All SST state lost on warm/cold reset. BIOS must re-enable at CPL3.
- **Turbo disabled SKU**: If turbo is fuse-disabled, SST-TF has no effect (TRL = base frequency). E2E TC should detect and skip gracefully.

---

## Section 4: Programming Model

### E2E Test Flow (Linux-based PV)

`
# 1. Enable SST-TF via intel_speed_select tool
intel_speed_select -d 0 turbo-freq enable -a

# 2. Enable SST-CP for HWP enforcement
intel_speed_select -d 0 core-power enable -a

# 3. Pin AVX-512 workload to HP cores
taskset -c <HP_CORES> stress-ng --matrix 0 --timeout 60s

# 4. Read frequency on HP cores
rdmsr -a 0x198  # IA32_PERF_STATUS -- should show HP TRL for AVX-512

# 5. Read frequency on LP cores (running lighter workload)
# Should be clipped to LP_CLIP_RATIO for corresponding CDYN

# 6. Disable SST-TF
intel_speed_select -d 0 turbo-freq disable -a
# Verify TRL reverts to legacy within 1+ slow-loop
`

### PythonSV-based Verification

`python
import pm.pmutils.sst_validate as sst_val
# Check HP core frequency matches expected TRL
sst_val.check_core_max(socket=0, expected_hp_trl=hp_trl_ratio, cdyn_level=5)  # AVX-512
# Check LP core clipped
sst_val.check_lp_clip(socket=0, expected_lp_clip=lp_clip_ratio_5)
`

---

## Section 5: Operational Behavior

| Scenario | Expected Behavior |
|----------|-------------------|
| HP cores + AVX-512 stress | Frequency = SST_TF_INFO_6.hp_trl_ratio_0 (CDYN5 bucket) |
| HP cores + AVX2 stress | Frequency = SST_TF_INFO_4.hp_trl_ratio_0 (CDYN3 bucket) |
| LP cores + any stress | Frequency <= LP_CLIP_RATIO for active CDYN level |
| All HP cores in C6 | LP cores remain clipped; no frequency spike; system stable |
| SST-TF disabled mid-workload | TRL reverts to legacy within 1+ slow-loop; no hang/crash |
| SST-CP + TF both active | HWP min/max enforced per CLOS group; HP gets P0max range |

---

## Section 6: Corner Cases & Error Handling

- **All HP cores idle (C6)**: LP cores must NOT inherit HP TRL. System must remain stable.
- **AVX-512 downlevel**: If workload transitions from AVX-512 to SSE, TRL should adjust per CDYN level. PCode handles via turbo resolver.
- **DLCP mismatch**: If intel_speed_select reports different HP core list than DLCP fuse mask, test should flag as configuration error.
- **SST-CP disabled but TF active**: CLOS assignments still used for TRL differentiation even without SST-CP HWP enforcement.
- **Turbo disabled SKU**: E2E must detect FEATURE_SUPPORTED==0 or turbo-disabled fuse and exit gracefully.

---

## Section 7: Security / Safety / Policy

- SST-TF E2E tests run at OS ring-0 (via intel_speed_select or PythonSV). No user-space frequency control.
- TPMI writes are not locked post-CPL3 on NWP -- OS can toggle feature_state at runtime.
- E2E tests must restore SST-TF state to pre-test configuration on exit (cleanup).

---

## Section 8: References

- [SST Feature KB -- tf.md](../../../pm_features/sst/tf.md)
- [SST Intel HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html)
- [NWP PM MAS -- SST-TF section](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [Sibling TCD -- SST-TF Enabling & Discovery 22022420925](https://hsdes.intel.com/appstore/article-one/#/22022420925)
- [PCT KB -- TCD 22022420855](TCD_22022420855_pct_enabling_discovery.md)
- [Parent TCD HSD 16030785069](https://hsdes.intel.com/appstore/article-one/#/16030785069)
