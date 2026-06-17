# Deep Analysis: PCT - Default HP Core Selection

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422105](https://hsdes.intel.com/appstore/article/#/22022422105) |
| **Title** | PCT - Default HP core selection |
| **Date** | 2026-06-17 |
| **Version** | v3 (owner fix, segment/framework added, NWP register paths + test code from live HSD) |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SST |
| **Sub-Feature** | PCT — default HP core selection algorithm |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Owner** | mps |
| **Status** | open |
| **Val Environment** | virtual_platform |
| **Framework** | os-svos |
| **Automation** | yes |
| **Tags** | `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK` |
| **DMR Command** | `runPmx.py -x dmr.xml -p pct -tM 60 -M 10 --retry_count 2` |

---

## Test Case Intent

SW divides all available "processors" into N partitions (default N=4). The first processor in each partition is configured as the PCT HP (High Priority) core. This test verifies the default HP core selection algorithm produces the correct set of HP cores and CLOS assignments on NWP's 96-core topology.

### Pre-Conditions

- PCT enabled via BIOS knob (PCT Partition Count ≥ 1; default = 4)
- SST-TF active (`SST_PP_CONTROL.feature_state[1] = 1`)
- All cores online (no BIST failures, no OS offlines)

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Boot with PCT Partition Count = 4 (default) | System boots with SST-TF/PCT active |
| 2 | Read total available logical processors | 96 (NWP: 2 CBBs × 48, no SMT) |
| 3 | Compute expected partitions: 96 ÷ 4 = 24 cores/partition | 4 partitions of 24 cores each |
| 4 | Identify expected HP cores: first core of each partition | Cores at indices 0, 24, 48, 72 (or 2 per partition = 8 total per CCB 14026595435) |
| 5 | Read `SST_CLOS_ASSOC` for each logical processor | HP cores → CLOS[0], LP cores → CLOS[3] |
| 6 | Verify HP core CLOS config | `SST_CLOS_CONFIG[0].max = SST_TF_INFO_2.RATIO_0` (HP TRL) |
| 7 | Verify LP core CLOS config | `SST_CLOS_CONFIG[3].max = SST_TF_INFO_0.LP_CLIP_RATIO_0` (~P1) |
| 8 | Read MSR 0x1AD on HP cores | Overridden with HP TRL ratio |

### Pass / Fail Criteria

- **PASS**: Correct number of HP cores selected per partition; CLOS assignments match HP/LP segmentation; HP cores report elevated TRL
- **FAIL**: Wrong HP core count, incorrect CLOS mapping, or LP cores not clipped

---

## Section A: NWP Architecture Delta

**Disposition: Runnable_On_N-1**

PCT is one of only 2 SST features supported on NWP (SST-TF and PCT). All other SST features (SST-BF, SST-PP, SST-CP, HGS) are ZBB'd. The PCT flow uses SST-TF CLOS infrastructure which is fully functional on NWP.

### DMR → NWP Delta Table

| Aspect | DMR | NWP | Impact on Test |
|--------|-----|-----|----------------|
| **CBB count** | 4 CBBs | 2 CBBs | Partition-to-die mapping changes; fewer die boundaries to cross |
| **Cores per CBB** | 32 (8 modules × 4 cores) | 48 (24 DCMs × 2 PNC cores) | Partition size = 24 (NWP) vs 32 (DMR) |
| **Total cores** | 128 | 96 | Different partition math: 96÷4=24 vs 128÷4=32 |
| **HP cores per partition** | 1-2 | 2 (8 total per CCB 14026595435) | Verify 2 HP cores per partition on NWP |
| **SMT** | 2 threads/core | None (single-threaded) | Logical processor = physical core on NWP |
| **PCT frequency target** | ~4.6 GHz | 4.4 GHz (POR-1, trending) | Different TRL ratio values |
| **DLCP support** | Yes (PCT_Module_Mask fuse) | TBD — confirm if NWP uses DLCP or legacy | Open item |
| **SST-PP interaction** | SST-PP active, cross-product possible | SST-PP ZBB'd — no cross-product | Simplifies PCT testing |
| **PCT Enable knob** | Integrated into PCT Partition Count | Same as DMR+ | No standalone PCT Enable knob |
| **MADT ordering** | 2 IMH + 4 CBBs | NIO + 2 CBBs | Different APIC topology affects partition → core mapping |
| **Test config** | `dmr.xml` | `nwp.xml` | Config file swap required |

### NWP PCT Configuration (from CCB [HSD 14026595435](https://hsdes.intel.com/appstore/article/#/14026595435))

| Parameter | NWP Value |
|-----------|-----------|
| HP core count | 8 (2 per partition × 4 partitions) |
| PCT frequency target | 4.4 GHz (POR-1) |
| Total cores | 96 (2 CBBs × 48) |
| Default partitions | 4 → 24 cores/partition |
| HP cores per partition | 2 |

---

## Section B: Interactions — Swimlane & Sequence

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | BIOS | Read PCT Partition Count knob (default=4) | BIOS Setup |
| 2 | BIOS | Discover 96 available cores via CPUID 0x1F | CPUID |
| 3 | BIOS | Divide 96 cores into 4 partitions of 24 | |
| 4 | BIOS | Select 2 HP cores per partition (8 total) | |
| 5 | PrimeCode (NIO) | Read SST_TF fuses + PCT_Module_Mask at reset Phase 5 | Fuse ctrl |
| 6 | PrimeCode (NIO) | Populate SST_TF_INFO_0..10 TPMI registers | TPMI MMIO |
| 7 | BIOS | Program SST_CLOS_CONFIG[0]: min=P1, max=HP TRL | TPMI MMIO |
| 8 | BIOS | Program SST_CLOS_CONFIG[3]: min=Pn, max=LP_CLIP | TPMI MMIO |
| 9 | BIOS | Program SST_CLOS_ASSOC: HP=CLOS[0], LP=CLOS[3] | TPMI MMIO |
| 10 | BIOS | Set SST_PP_CONTROL.feature_state[1]=1 | TPMI MMIO |
| 11 | BIOS | Override MSR 0x1AD with HP TRL ratio | MSR |
| 12 | PCode (CBB×2) | Enforce CLOS limits at runtime: HP=P0max, LP=LP_CLIP | HW wire |
| 13 | OS/Test | Query SST_CLOS_ASSOC per logical processor | TPMI MMIO |
| 14 | OS/Test | Verify 8 HP cores at expected indices | |
| 15 | OS/Test | Read SST_CLOS_CONFIG[0].max — verify HP TRL | TPMI MMIO |
| 16 | OS/Test | Read SST_CLOS_CONFIG[3].max — verify LP clip ratio | TPMI MMIO |

### Sequence Data

| # | From | To | Message | Interface |
|---|------|----|---------|-----------|
| 1 | BIOS | TPMI SRAM | Read PCT capability (partition count) | [TPMI MMIO] |
| 2 | PrimeCode | Fuse Controller | Read SST_TF_CONFIG fuse arrays + PCT_Module_Mask | [Internal] |
| 3 | PrimeCode | TPMI SRAM | Write SST_TF_INFO_0 (LP_CLIP_RATIO), SST_TF_INFO_2 (HP TRL) | [TPMI MMIO] |
| 4 | BIOS | TPMI SRAM | Write SST_CLOS_CONFIG[0] (HP: max=TRL ratio) | [TPMI MMIO] |
| 5 | BIOS | TPMI SRAM | Write SST_CLOS_CONFIG[3] (LP: max=LP_CLIP) | [TPMI MMIO] |
| 6 | BIOS | TPMI SRAM | Write SST_CLOS_ASSOC[core] for all 96 cores | [TPMI MMIO] |
| 7 | BIOS | Core | Write MSR 0x1AD (PRIMARY_TURBO_RATIO_LIMIT) = HP TRL | [MSR] |
| 8 | BIOS | PCode | Set SST_PP_CONTROL.feature_state[1]=1 | [TPMI MMIO] |
| 9 | PCode | Core FIVR/PLL | Enforce CLOS-based frequency: HP→P0max, LP→LP_CLIP | [HW wire] |
| 10 | Test | TPMI SRAM | Read SST_CLOS_ASSOC per core — verify HP/LP mapping | [TPMI MMIO] |
| 11 | Test | Core | Read IA32_HWP_CAPABILITIES (0x771) — HP reports P0max | [MSR] |

---

## Section C: Interface Coverage Assessment

| Interface | Type | Register / Address | Covered by TC? | Notes |
|-----------|------|--------------------|-----------------|-------|
| SST_CLOS_ASSOC | TPMI | Per-core CLOS assignment | **Yes** | Primary check: HP → CLOS[0], LP → CLOS[3] |
| SST_CLOS_CONFIG[0] | TPMI | HP CLOS config (min/max ratio) | **Yes** | Verify max = SST_TF_INFO_2.RATIO_0 |
| SST_CLOS_CONFIG[3] | TPMI | LP CLOS config (min/max ratio) | **Yes** | Verify max = LP_CLIP_RATIO_0 |
| SST_TF_INFO_0 | TPMI | LP clip ratio array | Partial | Implicitly checked via CLOS_CONFIG |
| SST_TF_INFO_2 | TPMI | HP TRL ratio array | Partial | Implicitly checked via CLOS_CONFIG |
| SST_TF_INFO_10 | TPMI | PCT_Module_Mask (DLCP) | **No** | DLCP on NWP TBD — gap if DLCP active |
| SST_PP_CONTROL | TPMI | feature_state[1] SST-TF enable | Partial | Implicitly required for PCT to function |
| MSR 0x1AD | MSR | PRIMARY_TURBO_RATIO_LIMIT | **Should add** | Verify HP TRL override |
| MSR 0x771 | MSR | IA32_HWP_CAPABILITIES | **Should add** | HP cores report P0max, LP report LP_CLIP |
| SST_CP_CONTROL | TPMI | SST_CP_PRIORITY_TYPE = 1 (Ordered) | **No** | Not covered — add negative check |
| PCT Partition Count BIOS knob | BIOS | BIOS setup variable | **Yes** | Default N=4 is the test target |

---

## Section D: NWP Specification References

### Key NWP Namednodes Register Paths (from TC description)

| Register | NWP Namednodes Path | Purpose |
|----------|--------------------|---------|
| CAPID4.bit29 | `sv.socket0.nio.punit.ptpcioregs.ptpcioregs.capid4.capid4_29` | Fuse: PCT capability enable (must be 1) |
| PctHpModuleCount | `nvram.PctHpModuleCount.getValue()` | BIOS: HP module count (multiples of 4) |
| SST_CLOS_ASSOC_0.clos_id_module{N} | `sv.socket0.cbb{X}.base.tpmi.sst_clos_assoc_0.clos_id_moduleN` | Module CLOS assignment (0/1=HP, 2/3=LP) |
| SST_CP_CONTROL.sst_cp_enable | `sv.socket0.cbb{X}.base.tpmi.sst_cp_control.sst_cp_enable` | PCT globally enabled (1=on) |
| SST_CP_CONTROL.sst_cp_priority_type | `sv.socket0.cbb{X}.base.tpmi.sst_cp_control.sst_cp_priority_type` | Throttling mode (1=Ordered) |
| SST_TF_INFO_1.num_core_0 | `sv.socket0.cbb{X}.base.tpmi.sst_tf_info_1.num_core_0` | Max HP modules supported by silicon |
| MSR 0x774 IA32_HWP_REQUEST | `pd.debug.access_to_msr(0x774, core=core)` | HWP desired ratio (HP cores: request P0) |
| MSR 0x198 IA32_PERF_STATUS | `pd.debug.access_to_msr(0x198, core=core)` | Current operating ratio |
| MSR 0x199 IA32_PERF_CTL | `pd.debug.access_to_msr(0x199, core=core)` | Legacy P-state request (if HWP off) |

> Note: `nio.punit.*` register names and field definitions are identical to DMR `imh0.punit.*`; path prefix swap only.

### Test Implementation (from TC description)

```python
from pysvtools.xmlcli import nvram
import diamondrapids.pm.Active_PM.SST.pct.pct_focus as pctd  # adapt to NWP equivalent

ram = nvram.getNVRAM(); ram.pull()
hp_mod_count = ram.PctHpModuleCount.getValue()
print(f'BIOS PctHpModuleCount = {hp_mod_count}')

# Generate HP/LP list from TPMI
pctd.generate_core_list()

# Verify first core is HP (BSP requirement)
first_core = sv.socket0.cbb0.computes[0].modules[0].cores[0]
assert first_core in pctd.HP_CORES, 'First core must be HP!'

# Verify HP count matches BIOS knob
actual_hp_mods = len(pctd.HP_CORES) // pctd.COUNT
assert actual_hp_mods == hp_mod_count, f'Mismatch: BIOS={hp_mod_count}, TPMI={actual_hp_mods}'

# Dump full CLOS assignment table (NWP: 2 CBBs)
for cbb in sv.sockets.cbbs:  # cbb0, cbb1
    print(f'\n--- CBB{cbb.instance} ---')
    for compute in cbb.computes:
        for mod in compute.modules:
            n = mod.instance % 0x20
            grp = 0 if compute.instance in [0, 1] else 1
            clos = cbb.base.tpmi.getbypath(f'sst_clos_assoc_{grp}.clos_id_module{n}').get_value()
            print(f'  Compute{compute.instance} Module{n}: CLOS={clos} ({"HP" if clos in [0,1] else "LP"})')
```

**HP Selection Rule (PctHpModuleCount):**
- CBB0 compute0: modules 0..(PctHpModuleCount/2 - 1) → CLOS[0] (HP)
- CBB0 compute1: modules 0..(PctHpModuleCount/2 - 1) → CLOS[1] (HP)
- Remaining modules → CLOS[2] or CLOS[3] (LP)
- `PctHpModuleCount` must be a multiple of 4 (2 computes × 2 modules minimum)
- **BSP rule**: First core of socket (CBB0, compute0, module0, core0) must always be HP

### Reference Documents

| Document | Link | Relevance |
|----------|------|-----------|
| PCT HAS | [PCT Architecture Spec](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) | Primary: PCT algorithm, CLOS mapping, DLCP, HP selection |
| Intel SST HAS | [SST Architecture Spec](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) | SST-TF CLOS infrastructure used by PCT |
| NWP PM MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP-specific PCT scope and configuration |
| DMR Overview HAS | [DMR Overview — CBB Feature List](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/DMR_Overview_HAS.html) | PCT as separate feature item (HSD 14023051596) |
| NWP PCT CCB | [HSD 14026595435](https://hsdes.intel.com/appstore/article/#/14026595435) | NWP PCT core count (8 HP), frequency target (4.4 GHz), POR-1 status |
| NWP SST ZBB | [HSD 22021155414](https://hsdes.intel.com/appstore/article/#/22021155414) | SST-PP/BF/CP/HGS ZBB'd on NWP |
| PrimeCode SST-TF Init | `src/flow/sst/sst_tpmi_general.cpp::sstTfInfoInit()` | Firmware: SST_TF_INFO register population at reset Phase 5 |
| PCode SST Manager | `source/pcode/sst_manager.cpp::update_cfgs()` | PCode: CLOS-based frequency enforcement |

---

## Section E: NWP Risk Assessment

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|------------|--------|------------|
| 1 | **HP core count mismatch**: NWP CCB specifies 8 HP cores (2/partition) but TC description says "first processor" (singular) per partition | Medium | High | Clarify: NWP uses 2 HP cores per partition (8 total), not 1. Update TC to expect 8 HP cores on NWP |
| 2 | **Partition math with 96 cores**: 96 ÷ 4 = 24 is clean, but APIC topology (NIO + 2 CBBs) may produce non-contiguous APIC IDs affecting partition boundaries | Medium | Medium | Verify partition algorithm uses logical processor numbering from MADT, not physical die IDs |
| 3 | **DLCP vs legacy core selection**: If NWP uses DLCP (PCT_Module_Mask fuse), HP core positions are fixed by fuse, not by partition algorithm. TC assumes partition-based selection | Low-Medium | High | Check SST_TF_INFO_10 for PCT_Module_Mask; if non-zero, DLCP is active and test logic must adapt |
| 4 | **Vrel risk**: CCB 14026595435 notes Vrel risk — if it materializes, PCT falls back to legacy SST-TF with reduced frequency target | Low | Medium | Track CCB status; if Vrel materializes, update expected HP frequency from 4.4 GHz |
| 5 | **Config file**: DMR command uses `dmr.xml`; NWP requires `nwp.xml` which may not exist yet | High | Medium | Ensure `nwp.xml` runPmx config file is created with correct NWP topology parameters |
| 6 | **No SMT**: NWP has no SMT, so logical processor = physical core. DMR tests may assume 2 threads per core for CLOS_ASSOC | Low | Low | Verify test does not multiply core count by 2 for thread-level CLOS assignment |

---

## Section F: Recommendations

1. **ADOPT with adaptation** — Change config from `dmr.xml` → `nwp.xml`; update expected HP core count from 4 to 8 (2 per partition per CCB 14026595435)
2. **Update expected partition math** — NWP: 96 cores ÷ 4 partitions = 24 cores/partition, with 2 HP cores per partition (indices depend on MADT ordering)
3. **Add DLCP check** — Read SST_TF_INFO_10 to determine if DLCP is active; if so, HP core positions come from PCT_Module_Mask fuse, not partition algorithm
4. **Add MSR verification** — Read MSR 0x1AD (TRL) and MSR 0x771 (HWP_CAPABILITIES) on HP vs LP cores to confirm frequency differentiation
5. **Add SST_CP_CONTROL check** — Verify `SST_CP_PRIORITY_TYPE = 1` (Ordered Throttling) is set
6. **Priority**: Medium — tagged `plc.feature.p1`; default HP selection is the foundation for all PCT test cases

### Adapted NWP Command
```bash
python runPmx.py -x nwp.xml -p pct -tM 60 -M 10 --retry_count 2
```

### NWP Default HP Core Calculation
```python
# NWP: 96 cores total, N=4 default partitions, 2 HP cores per partition
total_cores = 96    # 2 CBBs × 48 cores
n_partitions = 4    # default PCT partition count
partition_size = total_cores // n_partitions  # = 24 cores/partition
hp_per_partition = 2  # per CCB 14026595435

# Expected HP core indices (first 2 of each partition)
hp_cores = []
for p in range(n_partitions):
    base = p * partition_size
    hp_cores.extend([base, base + 1])
# hp_cores = [0, 1, 24, 25, 48, 49, 72, 73]
print(f"Expected {len(hp_cores)} HP cores: {hp_cores}")
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1 | 2025-07-24 | Initial enrichment |
| v2 | 2026-05-29 | Full pipeline re-enrichment: fresh HSD metadata, Co-Design MCP query, expanded sections A-F, swimlane/sequence diagrams, risk assessment, 8 HP cores per CCB 14026595435 |
| v3 | 2026-06-17 | Owner corrected (mmaltese→mps); Segment/Framework added; NWP namednodes register paths + pctd test code injected from live HSD TC description |

## User Notes

_(none)_
