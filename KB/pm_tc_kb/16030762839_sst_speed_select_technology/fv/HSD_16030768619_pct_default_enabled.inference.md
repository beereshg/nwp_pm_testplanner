# Deep Analysis: PCT - Default Enabled

| Field | Value |
|-------|-------|
| **HSD ID** | [16030768619](https://hsdes.intel.com/appstore/article-one/#/16030768619) |
| **Title** | PCT - Default Enabled |
| **Date** | 2026-06-23 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SST |
| **Sub-Feature** | PCT — Automatic boot-time enablement when CAPID4.bit29=1 |
| **Parent TCD** | [22022420858 — PCT - Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420858) |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Status** | open |
| **Owner** | mps |

## Version History
- v1 (2026-06-23): New — co-design MCP + HSD description enrichment

---

## Test Case Intent

Verify that the system boots with PCT **automatically enabled** when the silicon capability fuse
is set (`CAPID4.bit29=1`) and BIOS defaults are in effect. No explicit user configuration is
required — this is a **power-on default state verification**.

**Boot default flow** (co-design confirmed):
1. BIOS reads `CAPID4.bit29` at PEI phase; if=1 → feature qualified for PCT
2. BIOS reads `SST_TF_INFO-8.NUM_CORE_0` and `SST_TF_INFO-101.QUALIFIED_MODULE_MASK` to determine default HP module count
3. BIOS programs default `PctHpModuleCount` (SKU-dependent from fuse/BIOS table) at CPL3
4. BIOS programs `SST_CLOS_CONFIG`, `SST_CLOS_ASSOC`, `SST_CP_CONTROL`, `SST_PP_CONTROL.feature_state[1]=1`
5. PCode activates SST-TF enforcement at S0 entry

**Key distinction from other PCT TCs:**
- TC 22022422103 (TPMI register check): boot validation with explicit BIOS knob set
- TC 16030768620 (TPMI runtime enable/disable): validates toggle without reboot
- **This TC**: validates *automatic* default enablement — no user action, default BIOS settings

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP silicon or emulation; CAPID4.bit29=1 (PCT fuse set) |
| BIOS | **Default settings** — no PCT-specific knob changes; BIOS auto-determines HP count |
| FW stack | PCode, PrimeCode, PythonSV installed |
| SST-TF | SST-TF fuses programmed (LP_CLIP, TRL ratios in SST_TF_INFO registers) |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Boot platform with **default BIOS settings** (no PCT knob changes) | Clean boot; no hang/MCA during PCode SST-TF initialization | Boot hang, MCA, or instability |
| 2 | Read `CAPID4.bit29`: `sv.socket0.nio.punit.ptpcioregs.ptpcioregs.capid4.capid4_29` | = 1 (PCT capability fuse set) | = 0 → TC cannot run on this platform |
| 3 | Read `SST_PP_CONTROL.feature_state[1]` per CBB | = 1 (PCT/SST-TF **automatically** activated by BIOS default) | = 0 → PCT not auto-enabled |
| 4 | Read `SST_CP_CONTROL.sst_cp_enable` per CBB (cbb0, cbb1) | = 1 (PCT globally enabled) | = 0 |
| 5 | Read `SST_CP_CONTROL.sst_cp_priority_type` per CBB | = 1 (Ordered Throttling — BIOS default) | ≠ 1 |
| 6 | Read `SST_TF_INFO_1.num_core_0` per CBB; compare to default HP count | num_core_0 ≥ default `PctHpModuleCount` programmed by BIOS | Mismatch |
| 7 | Read `SST_CLOS_ASSOC_0.clos_id_module{N}` per CBB for all modules | First `PctHpModuleCount/2` modules per CBB = CLOS 0 (HP); rest = CLOS 2/3 (LP) | CLOS assignment mismatch |
| 8 | Verify `MSR 0x1AD` = `SST_TF_INFO_2.RATIO_0` (HP TRL, not 0xFF) | MSR 0x1AD = HP TRL ratio (~4.4 GHz on NWP) | = 0xFF or ≠ RATIO_0 ([HSD 14025997048](https://hsdes.intel.com/appstore/article-one/#/14025997048)) |

### Pass / Fail Criteria

- **PASS**: CAPID4.bit29=1; `feature_state[1]`=1 automatically at default boot; CLOS assignments match default HP count; `sst_cp_enable`=1; `sst_cp_priority_type`=1; `MSR 0x1AD` = `RATIO_0`; no hang/MCA
- **FAIL**: PCT not auto-enabled at default boot (`feature_state[1]`=0); CLOS mismatch; `MSR 0x1AD`=0xFF; boot hang/MCA

---

## Section A: NWP Delta

**Disposition: Runnable_On_N-1** — PCT default enablement is functional on NWP.

| Aspect | DMR | NWP | Adaptation |
|--------|-----|-----|-----------|
| CAPID4.bit29 path | `sv.socket0.imh0.punit.*` | **`sv.socket0.nio.punit.ptpcioregs.ptpcioregs.capid4.capid4_29`** | Path change: IMH → NIO |
| CBBs | 4 | **2** (cbb0, cbb1) | Loop `range(2)` |
| Cores per CBB | 32 | **48** | 24 modules/CBB |
| Default HP count | 4–8 (SKU dependent) | **8** (2/partition × 4 partitions on 96-core NWP) | Different default |
| SST-BF/PP active | May conflict | **ZBB'd** — no interference | Simplifies test |

### NWP Default PctHpModuleCount
Per co-design MCP query (2026-06-23): determined from `SST_TF_INFO-8.NUM_CORE_0` and `SST_TF_INFO-101.QUALIFIED_MODULE_MASK` at runtime. On 96-core NWP: **8 HP cores** (2 per partition × 4 partitions).

---

## Section B: Interactions

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | BIOS PEI | Read `CAPID4.bit29`; if=1 → PCT qualified | CAPID MMIO |
| 2 | BIOS PEI | Read `SST_TF_INFO-8.NUM_CORE_0` + `SST_TF_INFO-101.QUALIFIED_MODULE_MASK` → default HP count | TPMI |
| 3 | BIOS CPL3 | Program `SST_CLOS_CONFIG[0/3]`, `SST_CLOS_ASSOC`, `SST_CP_CONTROL` | TPMI MMIO |
| 4 | BIOS CPL3 | Set `SST_PP_CONTROL.feature_state[1]=1` → PCT active | TPMI MMIO |
| 5 | BIOS CPL3 | Override `MSR 0x1AD` = `SST_TF_INFO_2.RATIO_0` | MSR |
| 6 | PCode | SstManager detects SST-TF enable; loads TRL tables; activates WP4 enforcement | Internal |
| 7 | Test | Read TPMI/MSR registers to verify auto-enabled state | PythonSV |

---

## Section D: NWP Register Paths

| Register | NWP Namednodes Path | Expected Default |
|----------|--------------------|----|
| `CAPID4.bit29` | `sv.socket0.nio.punit.ptpcioregs.ptpcioregs.capid4.capid4_29` | 1 |
| `SST_PP_CONTROL.feature_state[1]` | `sv.socket0.cbb{X}.base.tpmi.sst_pp_control.feature_state` bit 1 | 1 (auto-enabled) |
| `SST_CP_CONTROL.sst_cp_enable` | `sv.socket0.cbb{X}.base.tpmi.sst_cp_control.sst_cp_enable` | 1 |
| `SST_CP_CONTROL.sst_cp_priority_type` | `sv.socket0.cbb{X}.base.tpmi.sst_cp_control.sst_cp_priority_type` | 1 (Ordered) |
| `SST_TF_INFO_1.num_core_0` | `sv.socket0.cbb{X}.base.tpmi.sst_tf_info_1.num_core_0` | ≥ default HP count |
| `SST_CLOS_ASSOC_0` | `sv.socket0.cbb{X}.base.tpmi.sst_clos_assoc_0.clos_id_module{N}` | HP modules = CLOS 0 |
| `MSR 0x1AD` | `pd.debug.access_to_msr(0x1AD, core=0)` | = `SST_TF_INFO_2.RATIO_0` |

---

## Section E: Risk Assessment

| # | Risk | Severity | Notes |
|---|------|----------|-------|
| 1 | CAPID4 path must use NIO (`nio.punit`) not IMH | High | NWP path changed |
| 2 | MSR 0x1AD=0xFF causes issues ([HSD 14025997048](https://hsdes.intel.com/appstore/article-one/#/14025997048)) | High | BIOS must write `RATIO_0` not 0xFF |
| 3 | Default HP count differs from DMR | Medium | NWP: 8 HP cores (2/partition × 4 partitions) |

---

## Section F: Recommendations

**Runnable_On_N-1.** Single adaptation: CAPID4 path (`imh0` → `nio`). CBB loop `range(2)`.
Validate MSR 0x1AD ≠ 0xFF explicitly. No workload needed — pure register checkout of default auto-enabled state.

---

## Section G: PSS Grading

| Sl No | Dimension | Value | Rationale |
|-------|-----------|-------|-----------|
| 1 | NWP Delta | Yes (minor) | CAPID4 path change; 2 CBBs; default HP count differs |
| 2 | Applicable NWP | **Yes** | PCT default enablement functional on NWP |
| 3 | PSS Environment | ✅ VP | Register-level boot validation; VP capable |
| 4 | Silicon Only | No | VP feasible for default boot register checkout |
| 5 | Test Content | DMR_L | Low adaptation: path fix + CBB count; intent unchanged |
| 6 | OS | sv-os | PythonSV namednodes reads |

### References
- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — Default enablement, BIOS programming
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST-TF CLOS, feature_state
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [HSD 14025997048](https://hsdes.intel.com/appstore/article-one/#/14025997048) — MSR 0x1AD 0xFF invalid
- [KB/pm_features/sst/pct.md](../../../pm_features/sst/pct.md)
