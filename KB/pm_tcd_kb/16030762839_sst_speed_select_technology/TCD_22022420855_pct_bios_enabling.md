# TCD 22022420855 -- PCT - BIOS Enabling

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420855](https://hsdes.intel.com/appstore/article-one/#/22022420855) |
| **Title** | PCT - BIOS Enabling |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030762939 -- NWP PM PCT (Priority Core Turbo)](https://hsdes.intel.com/appstore/article-one/#/16030762939) |
| **Child TCs** | [22022422100](https://hsdes.intel.com/appstore/article-one/#/22022422100) -- PCT - BIOS Menu (FV)<br>[16030715678](https://hsdes.intel.com/appstore/article-one/#/16030715678) -- [PSS]PCT - BIOS Menu<br>[16030715684](https://hsdes.intel.com/appstore/article-one/#/16030715684) -- [PSS]PCT - Default Disabled<br>[16030768619](https://hsdes.intel.com/appstore/article-one/#/16030768619) -- PCT - Default Enabled (FV) |
| **Sibling TCDs** | [16031169297](https://hsdes.intel.com/appstore/article-one/#/16031169297) -- PCT - TPMI Runtime Control<br>[16031169298](https://hsdes.intel.com/appstore/article-one/#/16031169298) -- PCT - DQ Rules & Negative Validation<br>[22022420858](https://hsdes.intel.com/appstore/article-one/#/22022420858) -- PCT - Functionality |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Architecture / Micro-architecture and Functionality

This TCD validates the **BIOS Setup interface** for PCT (Priority Core Turbo) -- specifically that PCT knobs are visible with correct defaults, and that enabling/disabling PCT via BIOS produces the expected NVRAM and hardware state. PCT is built on SST-TF CLOS-based frequency partitioning: a subset of HP cores runs at elevated turbo (~P0max, ~4.4 GHz on NWP) while LP cores are clipped to ~P1.

> **Architecture overview:** See [TPF 16030762939 -- NWP PM PCT](https://hsdes.intel.com/appstore/article-one/#/16030762939) for full-stack PCT architecture diagram, frequency hierarchy, and standard vs DLCP distinction.

### Scope Boundary

This TCD owns **BIOS knob visibility and default state** only. Adjacent WHATs are covered by sibling TCDs:

| WHAT | TCD |
|------|-----|
| TPMI register correctness, runtime enable/disable via TPMI | [16031169297 -- PCT - TPMI Runtime Control](https://hsdes.intel.com/appstore/article-one/#/16031169297) |
| DQ rules (mutual exclusion), negative/invalid config | [16031169298 -- PCT - DQ Rules & Negative Validation](https://hsdes.intel.com/appstore/article-one/#/16031169298) |
| Runtime frequency enforcement, C6 resilience, TDP convergence | [22022420858 -- PCT - Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420858) |

### NWP-Specific Deltas

- **Default disabled**: PCT Partition Count defaults to 0 on NWP/DMR (GNR: enabled if fused)
- **No PCT-enable fuse**: All NWP SKUs can opt-in via BIOS knob (GNR: gated by CAPID4.bit29)
- **2 CBBs**: NWP has 2 CBBs x 48 cores = 96 total; BIOS knob range bounded by SST_TF_INFO_8.NUM_CORE_0

### TC Coverage Map

| TC | Scope | Tier |
|----|-------|------|
| [22022422100](https://hsdes.intel.com/appstore/article-one/#/22022422100) -- PCT - BIOS Menu | Verify knob visible, correct options, correct default | FV |
| [16030715678](https://hsdes.intel.com/appstore/article-one/#/16030715678) -- [PSS]PCT - BIOS Menu | Same -- PSS layer (Simics/VP) | PSS |
| [16030715684](https://hsdes.intel.com/appstore/article-one/#/16030715684) -- [PSS]PCT - Default Disabled | Verify default boot with Partition Count=0 produces no PCT state | PSS |
| [16030768619](https://hsdes.intel.com/appstore/article-one/#/16030768619) -- PCT - Default Enabled | Verify boot with Partition Count > 0 produces valid PCT state | FV |

---

## Section 2: Interfaces and Protocols

### BIOS Knobs (Primary -- this TCD's scope)

| BIOS Knob | Options | Default | Notes |
|-----------|---------|---------|-------|
| PCT HP Partition Count | 0 -- 16 | **0 (disabled)** | Controls HP core count per partition; 0 = PCT off |
| PCT Core Selection | 0 -- 255 | **0** | Starting core position within partition (MADT order) |

### NVRAM Variables (observable by TCs)

| Variable | Type | Purpose |
|----------|------|---------|
| PctHpModuleCount | UINT8 | HP module count from BIOS knob; 0 = disabled |

### Downstream Registers (programmed by BIOS when PCT enabled)

These registers are **not the primary validation target** of this TCD -- see sibling TCD [16031169297](https://hsdes.intel.com/appstore/article-one/#/16031169297) for TPMI register correctness. Listed here for reference only:

| Register | Direction | Programmed When |
|----------|-----------|-----------------|
| SST_CP_CONTROL.sst_cp_enable | RW | BIOS sets =1 when Partition Count > 0 |
| SST_CLOS_CONFIG[0].max | RW | BIOS sets = HP TRL |
| SST_CLOS_CONFIG[3].max | RW | BIOS sets = LP clip |
| SST_CLOS_ASSOC[core] | RW | BIOS assigns HP -> CLOS[0], LP -> CLOS[3] |
| SST_PP_CONTROL.feature_state[1] | RW | BIOS sets =1 (SST-TF active) |
| MSR 0x1AD PRIMARY_TURBO_RATIO_LIMIT | RO | BIOS writes = SST_TF_INFO_2.ratio_0 |

---

## Section 3: Reset / Power / Clocking

- **Phase 5 (PrimeCode)**: Populates SST_TF_INFO_0/2/8/10 from fuses before BIOS CPL3 handoff. These RO registers bound what BIOS can configure.
- **CPL3 (BIOS)**: Reads PCT BIOS knobs from NVRAM. If Partition Count > 0, programs CLOS, ASSOC, CP_CONTROL, PP_CONTROL, and MSR 0x1AD. If Partition Count = 0, leaves SST-TF inactive.
- **Post-boot invariant**: After BIOS hands off to OS, PCT state reflects the BIOS knob configuration. No further BIOS involvement until next reboot.
- **Warm reset**: PCT state must be re-established from NVRAM on every boot. Stale state from previous boot must not persist.

---

## Section 4: Programming Model

### BIOS PCT Enabling Logic (WHAT is configured)

| Condition | BIOS Action | Observable State |
|-----------|-------------|-----------------|
| Partition Count = 0 (default) | Skip all PCT programming | SST_CP_CONTROL.sst_cp_enable = 0; MSR 0x1AD = 0xFF or legacy TRL |
| Partition Count = N (1..16) | Program CLOS, ASSOC, CP_CONTROL, PP_CONTROL, MSR 0x1AD | SST_CP_CONTROL.sst_cp_enable = 1; CLOS_CONFIG[0].max = HP TRL |
| Partition Count > NUM_CORE_0 | BIOS should clamp to NUM_CORE_0 | Knob range limited; no overallocation |

### BIOS Knob Visibility Rules

| Condition | Knob Visible? | Notes |
|-----------|--------------|-------|
| Standard SKU | Yes | All NWP SKUs can opt-in |
| DLCP SKU | Yes (but partition count fixed by fuse) | Core Selection knob hidden or ignored |
| PCT fuse not present (GNR legacy) | N/A on NWP | NWP has no PCT gate fuse |

---

## Section 5: Operational Behavior

| Scenario | Expected Outcome | TC Link |
|----------|-----------------|---------|
| Default boot (Partition Count=0) | All cores at legacy TRL; SST_CP_CONTROL.sst_cp_enable=0; no HP/LP split | [16030715684](https://hsdes.intel.com/appstore/article-one/#/16030715684) |
| Enable PCT (Partition Count=N) | BIOS programs CLOS/ASSOC/CP_CONTROL; N HP cores at P0max, rest at LP_clip | [16030768619](https://hsdes.intel.com/appstore/article-one/#/16030768619) |
| BIOS menu visibility | PCT Partition Count and Core Selection knobs visible with correct defaults | [22022422100](https://hsdes.intel.com/appstore/article-one/#/22022422100), [16030715678](https://hsdes.intel.com/appstore/article-one/#/16030715678) |
| Partition Count knob range | Upper bound = SST_TF_INFO_8.NUM_CORE_0; cannot exceed max HP cores | [22022422100](https://hsdes.intel.com/appstore/article-one/#/22022422100) |
| BIOS re-enable after disable | Previous PCT state fully cleared; new config applied cleanly | [16030768619](https://hsdes.intel.com/appstore/article-one/#/16030768619) |

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| **Partition Count overflow** | BIOS knob set > SST_TF_INFO_8.NUM_CORE_0 | ⚠️ Verification criterion only | Add as bound-check in TC 22022422100 |
| **Warm reset state persistence** | PCT state from previous boot must not leak into a boot with Partition Count=0 | ⚠️ Verification criterion only | Add as check in TC 16030715684: enable PCT, reboot with Count=0, verify clean |
| **DLCP knob interaction** | On DLCP SKU, Partition Count knob effect is different (fuse-fixed positions) | ❌ Not covered | Gap -- needs DLCP-specific BIOS TC or cross-ref to DLCP TCD |
| **PCT + SST-BF knob conflict** | Both knobs enabled simultaneously in BIOS | Covered by sibling TCD [16031169298](https://hsdes.intel.com/appstore/article-one/#/16031169298) | No action (DQ Rules TCD) |
| **MSR 0x1AD = 0xFF** | BIOS fails to write MSR when enabling PCT | Covered by sibling TCD [16031169297](https://hsdes.intel.com/appstore/article-one/#/16031169297) | No action (TPMI TCD) |

---

## Section 7: Security / Safety / Policy

- BIOS knobs are protected by Setup password. No ring-0 OS path to change NVRAM PCT configuration.
- BIOS knob validation must occur before programming hardware registers -- out-of-range values must be clamped, not passed through.
- On DLCP SKUs, the BIOS Partition Count knob controls HP count but not HP core positions (fuse-fixed).

---

## Section 8: References

- [PCT (Priority Core Turbo) HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html)
- [CPUPM BIOS Knobs Reference Gen 3](https://docs.intel.com/documents/System-firmware-bios/Domain/ServerCpuPm/Index/CPUPM%20BIOS%20Knobs/BiosKnobs.html)
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html)
- [NWP PM MAS -- PCT section](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [HSD 14025997048](https://hsdes.intel.com/appstore/article-one/#/14025997048) -- MSR 0x1AD must not be 0xFF
- Sibling TCD: [16031169297 -- PCT - TPMI Runtime Control](https://hsdes.intel.com/appstore/article-one/#/16031169297)
- Sibling TCD: [16031169298 -- PCT - DQ Rules & Negative Validation](https://hsdes.intel.com/appstore/article-one/#/16031169298)
- Sibling TCD: [22022420858 -- PCT - Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420858)
- KB: KB/pm_features/sst/pct.md
