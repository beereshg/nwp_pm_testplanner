# TCD 22022420855 -- PCT - BIOS Enabling

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420855](https://hsdes.intel.com/appstore/article-one/#/22022420855) |
| **Title** | PCT - BIOS Enabling |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030762939 -- NWP PM PCT (Priority Core Turbo)](https://hsdes.intel.com/appstore/article-one/#/16030762939) |
| **Child TCs** | [22022422100](https://hsdes.intel.com/appstore/article-one/#/22022422100) -- PCT - BIOS Menu (FV)<br>[16030768619](https://hsdes.intel.com/appstore/article-one/#/16030768619) -- PCT - Default Enabled (FV)<br>[16030715678](https://hsdes.intel.com/appstore/article-one/#/16030715678) -- [PSS]PCT - BIOS Menu<br>[16030715684](https://hsdes.intel.com/appstore/article-one/#/16030715684) -- [PSS]PCT - Default Disabled |
| **Sibling TCDs** | [16031169297](https://hsdes.intel.com/appstore/article-one/#/16031169297) -- PCT - TPMI Runtime Control<br>[16031169298](https://hsdes.intel.com/appstore/article-one/#/16031169298) -- PCT - DQ Rules & Negative Validation<br>[22022420858](https://hsdes.intel.com/appstore/article-one/#/22022420858) -- PCT - Functionality<br>[16030982802](https://hsdes.intel.com/appstore/article-one/#/16030982802) -- PCT - DLCP (Die Level Cherry Picking) |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Architecture / Micro-architecture and Functionality

This TCD validates the **BIOS Setup interface** for PCT (Priority Core Turbo) -- specifically that PCT knobs are visible with correct defaults, and that enabling/disabling PCT via BIOS produces the expected NVRAM and hardware state. PCT is built on SST-TF CLOS-based frequency partitioning: a subset of HP cores runs at elevated turbo (~P0max, ~4.4 GHz on NWP) while LP cores are clipped to ~P1.

> **Architecture overview:** See [TPF 16030762939 -- NWP PM PCT](https://hsdes.intel.com/appstore/article-one/#/16030762939) §2 Design Details for full-stack PCT architecture, frequency hierarchy, CLOS mechanism, and standard vs DLCP distinction.

### NWP-Specific Deltas

- **Default disabled**: PCT Partition Count defaults to Auto = 0 on NWP/DMR (GNR: enabled if fused)
- **No PCT-enable fuse**: All NWP SKUs can opt-in via BIOS knob (GNR: gated by CAPID4.bit29)
- **2 CBBs**: NWP has 2 CBBs x 48 cores = 96 total; max partitions bounded by `SST_TF_INFO_8.NUM_CORE_0 / MAX_LPIDS`
- **PCT Enable knob eliminated**: On DMR/NWP, the standalone "PCT Enable" knob is integrated into PCT Partition Count (Auto = 0 = disabled)

### TC Coverage Map

| TC | Scope | Tier |
|----|-------|------|
| [22022422100](https://hsdes.intel.com/appstore/article-one/#/22022422100) -- PCT - BIOS Menu | Verify knob visible, correct options, correct default | FV |
| [16030768619](https://hsdes.intel.com/appstore/article-one/#/16030768619) -- PCT - Default Enabled | Verify boot with Partition Count > 0 produces valid PCT state | FV |
| [16030715678](https://hsdes.intel.com/appstore/article-one/#/16030715678) -- [PSS]PCT - BIOS Menu | BIOS knob visibility/defaults in Simics/VP | PSS |
| [16030715684](https://hsdes.intel.com/appstore/article-one/#/16030715684) -- [PSS]PCT - Default Disabled | Default boot with Partition Count = 0 produces no PCT state | PSS |

---

## Section 2: Interfaces and Protocols

### BIOS Knobs (Primary -- this TCD's scope)

| BIOS Knob | Options | Default | Notes |
|-----------|---------|---------|-------|
| PCT Partition Count | Auto / Manual (1..16) | **Auto (= 0, disabled)** | When Auto: BIOS skips PCT init. Manual: distributes HP modules into N partitions. Max = `SST_TF_INFO_8.NUM_CORE_0 / MAX_LPIDS` |
| High Priority Core Module Selection | Auto / Manual (0..255) | **Auto (= 0, first core)** | Starting core offset within partition for HP selection (MADT order). Auto = lowest APIC ID per partition |

### Enablement Dependencies (FlexconPM DQ Rules -- enforced at BIOS level)

| Rule | Enforcement | Sibling TCD |
|------|-------------|-------------|
| PCT requires SST-TF | If PCT Partition Count > 0, BIOS must set `SSTTF_ENABLE = Enabled` | — |
| PCT + SST-BF mutually exclusive | FlexconPM blocks enabling both simultaneously | [16031169298](https://hsdes.intel.com/appstore/article-one/#/16031169298) |
| PCT + FCT mutually exclusive | FlexconPM blocks enabling both simultaneously | [16031169298](https://hsdes.intel.com/appstore/article-one/#/16031169298) |

### Downstream Registers (programmed by BIOS when PCT enabled)

These registers are **not the primary validation target** of this TCD -- see sibling TCD [16031169297](https://hsdes.intel.com/appstore/article-one/#/16031169297) for TPMI register correctness. Listed here for reference only:

| Register | Direction | Programmed When |
|----------|-----------|-----------------|
| SST_CP_CONTROL.sst_cp_enable | RW | BIOS sets =1 when Partition Count > 0 |
| SST_CP_CONTROL.SST_CP_PRIORITY_TYPE | RW | BIOS sets =1 (Ordered Throttling) |
| SST_CLOS_CONFIG[0].max | RW | BIOS sets = HP TRL (SST_TF_INFO_2.RATIO_0) |
| SST_CLOS_CONFIG[3].max | RW | BIOS sets = LP clip (SST_TF_INFO_0.LP_CLIP_RATIO_0) |
| SST_CLOS_ASSOC_0..3[core] | RW | BIOS assigns HP cores → CLOS[0], LP cores → CLOS[3]; 4 bits/core, 16 cores/register |
| SST_PP_CONTROL.feature_state[1] | RW | BIOS sets =1 (SST-TF active) |
| MSR 0x1AD PRIMARY_TURBO_RATIO_LIMIT | RW | BIOS writes = SST_TF_INFO_2.RATIO_0; must not be 0xFF ([HSD 14025997048](https://hsdes.intel.com/appstore/article-one/#/14025997048)) |

---

## Section 3: Reset / Power / Clocking

- **Phase 5 (PrimeCode)**: Populates SST_TF_INFO_0/2/8/10 from fuses before BIOS CPL3 handoff. These RO registers bound what BIOS can configure.
- **CPL3 (BIOS)**: Reads PCT BIOS knobs from NVRAM. FlexconPM enforces DQ rules (PCT vs SST-BF/FCT mutual exclusion). If Partition Count > 0, programs CLOS, ASSOC, CP_CONTROL, PP_CONTROL, and MSR 0x1AD per dielet. If Partition Count = 0 (Auto), leaves SST-TF inactive.
- **Post-boot invariant**: After BIOS hands off to OS, PCT state reflects the BIOS knob configuration. No further BIOS involvement until next reboot.
- **Warm reset**: PCT state must be re-established from NVRAM on every boot. Stale CLOS/ASSOC state from previous boot must not persist.

---

## Section 4: Programming Model

### BIOS PCT Enabling Logic (WHAT is configured)

| Condition | BIOS Action | Observable State |
|-----------|-------------|-----------------|
| Partition Count = Auto/0 (default) | Skip all PCT programming | SST_CP_CONTROL.sst_cp_enable = 0; MSR 0x1AD = 0xFF or legacy TRL |
| Partition Count = N (1..16) | Program CLOS, ASSOC, CP_CONTROL, PP_CONTROL, MSR 0x1AD | SST_CP_CONTROL.sst_cp_enable = 1; CLOS_CONFIG[0].max = HP TRL |
| Partition Count > NUM_CORE_0/MAX_LPIDS | BIOS clamps to max | Knob range limited; no overallocation |

### HP Core Selection Algorithm (BIOS logic -- observable by TCs)

1. BIOS enumerates all enabled physical cores in APIC ID order (MADT: P-cores first, then compute Atoms, then SoC Atoms)
2. Cores divided evenly into N partitions (NWP default: 4 partitions of 24 cores)
3. Default HP core = lowest APIC ID in each partition (offset 0)
4. `High Priority Core Module Selection` knob shifts the offset for manual override
5. HP cores → CLOS[0]; all others → CLOS[3]

### BIOS Knob Visibility Rules

| Condition | Knob Visible? | Notes |
|-----------|--------------|-------|
| Standard SKU | Yes | All NWP SKUs can opt-in |
| DLCP SKU | Yes (partition count may be fuse-constrained) | HP Core Module Selection knob may be hidden or overridden by fuse mask |
| PCT not capable (GNR legacy gate) | N/A on NWP | NWP has no PCT gate fuse (CAPID4.bit29 not used) |

---

## Section 5: Operational Behavior

### Pass/Fail Bar

TCs under this TCD validate that BIOS knobs are **visible with correct defaults** and that enabling/disabling PCT via BIOS produces the expected observable state:

- **Enabled**: SST_CP_CONTROL.sst_cp_enable = 1; CLOS_CONFIG[0].max = SST_TF_INFO_2.RATIO_0; CLOS_ASSOC maps HP → CLOS[0], LP → CLOS[3]; MSR 0x1AD = HP TRL (not 0xFF)
- **Disabled (default)**: SST_CP_CONTROL.sst_cp_enable = 0; CLOS_ASSOC = default; MSR 0x1AD = legacy TRL or 0xFF

### Scenario Table

| Scenario | Expected Outcome | TC Link |
|----------|-----------------|---------|
| Default boot (Partition Count = Auto/0) | All cores at legacy TRL; SST_CP_CONTROL.sst_cp_enable = 0; no HP/LP split | [16030715684](https://hsdes.intel.com/appstore/article-one/#/16030715684) |
| Enable PCT (Partition Count = N) | BIOS programs CLOS/ASSOC/CP_CONTROL; N HP cores at P0max, rest at LP_clip | [16030768619](https://hsdes.intel.com/appstore/article-one/#/16030768619) |
| BIOS menu visibility | PCT Partition Count and HP Core Module Selection knobs visible with correct defaults | [22022422100](https://hsdes.intel.com/appstore/article-one/#/22022422100), [16030715678](https://hsdes.intel.com/appstore/article-one/#/16030715678) |
| Partition Count knob range | Upper bound = SST_TF_INFO_8.NUM_CORE_0 / MAX_LPIDS; cannot exceed max partitions | [22022422100](https://hsdes.intel.com/appstore/article-one/#/22022422100) |
| BIOS re-enable after disable | Previous PCT state fully cleared; new config applied cleanly | [16030768619](https://hsdes.intel.com/appstore/article-one/#/16030768619) |

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| **Partition Count knob range** | BIOS knob range must be bounded by SST_TF_INFO_8.NUM_CORE_0/MAX_LPIDS; values above max should not appear as selectable options | ⚠️ Verification criterion | Add as bound-check in TC [22022422100](https://hsdes.intel.com/appstore/article-one/#/22022422100) |
| **Warm reset state persistence** | Boot with Partition Count = 0 after a previous boot with PCT enabled must show clean disabled state (no stale CLOS/ASSOC) | ⚠️ Verification criterion | Add as check in TC [16030715684](https://hsdes.intel.com/appstore/article-one/#/16030715684): enable PCT, reboot with Count=0, verify SST_CP_CONTROL.sst_cp_enable = 0 |
| **HP Core Module Selection knob default** | When set to Auto, BIOS selects offset 0 (lowest APIC ID per partition); knob should not expose invalid offsets beyond partition size | ⚠️ Verification criterion | Add as default-value check in TC [22022422100](https://hsdes.intel.com/appstore/article-one/#/22022422100) |
| **Knob hidden when PCT not capable** | On a hypothetical SKU where PCT is not available, knobs must not be visible | ❌ Not applicable on NWP (all SKUs support PCT) | No action — NWP has no PCT gate fuse |

---

## Section 7: Security / Safety / Policy

- BIOS knobs are protected by Setup password. No ring-0 OS path to change NVRAM PCT configuration.
- BIOS knob validation must occur before programming hardware registers -- out-of-range values must be clamped, not passed through.
- FlexconPM enforces DQ rules at BIOS level; conflicting configurations are rejected before any registers are programmed.
- On DLCP SKUs, the BIOS Partition Count knob controls HP count but not HP core positions (fuse-fixed via PCT_Module_Mask).

---

## Section 8: References

- [PCT (Priority Core Turbo) HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html)
- [CPUPM BIOS Knobs Reference Gen 3](https://docs.intel.com/documents/System-firmware-bios/Domain/ServerCpuPm/Index/CPUPM%20BIOS%20Knobs/BiosKnobs.html)
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html)
- [NWP PM MAS -- PCT section](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [DMR Turbo HAS -- PCT section](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html)
- [HSD 14025997048](https://hsdes.intel.com/appstore/article-one/#/14025997048) -- MSR 0x1AD must not be 0xFF
- [HSD 14026595435](https://hsdes.intel.com/appstore/article-one/#/14026595435) -- NWP PCT CCB: 8 HP cores, 4.4 GHz target
- Sibling TCD: [16031169297 -- PCT - TPMI Runtime Control](https://hsdes.intel.com/appstore/article-one/#/16031169297)
- Sibling TCD: [16031169298 -- PCT - DQ Rules & Negative Validation](https://hsdes.intel.com/appstore/article-one/#/16031169298)
- Sibling TCD: [22022420858 -- PCT - Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420858)
- Sibling TCD: [16030982802 -- PCT - DLCP](https://hsdes.intel.com/appstore/article-one/#/16030982802)
- KB: KB/pm_features/sst/pct.md
