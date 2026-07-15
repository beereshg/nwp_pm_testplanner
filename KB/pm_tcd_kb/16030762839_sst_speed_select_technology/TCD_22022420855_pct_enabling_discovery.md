# TCD 22022420855 -- PCT Enabling & Discovery

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420855](https://hsdes.intel.com/appstore/article-one/#/22022420855) |
| **Title** | PCT - Enabling & Discovery |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030762939 -- NWP PM PCT (Priority Core Turbo)](https://hsdes.intel.com/appstore/article-one/#/16030762939) |
| **Child TCs** | [22022422100](https://hsdes.intel.com/appstore/article-one/#/22022422100) -- BIOS Menu (silicon+VP)<br>[22022422103](https://hsdes.intel.com/appstore/article-one/#/22022422103) -- TPMI register check (VP)<br>[22022422118](https://hsdes.intel.com/appstore/article-one/#/22022422118) -- DQ Rules FlexconPM (silicon+VP)<br>[16030715678](https://hsdes.intel.com/appstore/article-one/#/16030715678) -- PSS BIOS Menu (silicon+VP)<br>[16030715682](https://hsdes.intel.com/appstore/article-one/#/16030715682) -- PSS DQ Rules FlexconPM (silicon+VP)<br>[16030715690](https://hsdes.intel.com/appstore/article-one/#/16030715690) -- PSS TPMI register check FlexconPM (silicon+VP)<br>[16030717720](https://hsdes.intel.com/appstore/article-one/#/16030717720) -- PV PMSS SST PCT Discovery |
| **KB last updated** | 2026-07-15 |

---

## Section 1: Architecture / Micro-architecture and Functionality

PCT (Priority Core Turbo) is a distinct Intel PM feature built on SST-TF CLOS-based frequency partitioning. A small subset of HP cores operates at elevated turbo (~P0max, ~4.4 GHz on NWP) while LP cores are clipped to ~P1 -- without requiring LP cores to sleep in C6. PCT is the **customer-facing policy** layer; SST-TF is the **enforcement mechanism** underneath.

<!-- raw-html -->
<div style="margin:16px 0;border:1px solid #bfcfe8;border-radius:8px;overflow:hidden;font-family:'Segoe UI',Arial,sans-serif;font-size:11.5px;max-width:900px;">
  <div style="background:#1e3a5f;color:#fff;padding:10px 18px;font-weight:700;font-size:12px;letter-spacing:.5px;text-align:center;">
    NWP PCT Architecture &mdash; Full Stack (PCT policy built on SST-TF enforcement)
  </div>

  <!-- Layer 1: SW/Policy -->
  <div style="background:#f1f5f9;border-bottom:1px solid #cbd5e1;padding:10px 16px;">
    <div style="font-weight:700;color:#374151;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">Software / Policy Layer</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;font-size:10.5px;color:#374151;">
      <div style="background:#fff;border:1px solid #cbd5e1;border-radius:4px;padding:5px 10px;">BIOS: PCT Partition Count knob (default=0, customer opt-in)</div>
      <div style="background:#fff;border:1px solid #cbd5e1;border-radius:4px;padding:5px 10px;">OS / Intel SST tool: enable/disable, reassign HP/LP at runtime</div>
      <div style="background:#fff;border:1px solid #cbd5e1;border-radius:4px;padding:5px 10px;">VMM: assign HP logical cores to specific VMs</div>
    </div>
  </div>
  <div style="text-align:center;background:#f8fafc;padding:3px 0;font-size:10px;color:#64748b;">&#11015; TPMI / control programming</div>

  <!-- Layer 2: TPMI -->
  <div style="background:#e0f2fe;border-bottom:1px solid #7dd3fc;padding:10px 16px;">
    <div style="font-weight:700;color:#0369a1;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">TPMI / Arch Discovery &amp; Control View (PCT-specific)</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:10.5px;">
      <div style="background:#fff;border:1px solid #bae6fd;border-radius:4px;padding:5px 9px;"><strong>SST_TF_INFO_0.LP_CLIP_RATIO_0</strong> &mdash; LP ceiling (~P1)</div>
      <div style="background:#fff;border:1px solid #bae6fd;border-radius:4px;padding:5px 9px;"><strong>SST_TF_INFO_2.RATIO_0</strong> &mdash; HP TRL ratio (~4.4 GHz)</div>
      <div style="background:#dbeafe;border:2px solid #3b82f6;border-radius:4px;padding:5px 9px;"><strong>SST_TF_INFO_10</strong> &mdash; DLCP PCT_Module_Mask (0=std, non-zero=DLCP)</div>
      <div style="background:#fff;border:1px solid #bae6fd;border-radius:4px;padding:5px 9px;"><strong>SST_CLOS_ASSOC_0..N</strong> &mdash; HP=CLOS[0/1], LP=CLOS[2/3]</div>
      <div style="background:#fff;border:1px solid #bae6fd;border-radius:4px;padding:5px 9px;"><strong>SST_CP_CONTROL.priority_type=1</strong> &mdash; Ordered throttle</div>
      <div style="background:#fff;border:1px solid #bae6fd;border-radius:4px;padding:5px 9px;"><strong>SST_TF_INFO_8.NUM_CORE_0</strong> &mdash; max HP cores (bounds BIOS knob)</div>
    </div>
  </div>
  <div style="text-align:center;background:#f8fafc;padding:3px 0;font-size:10px;color:#64748b;">&#11015; configuration / visibility</div>

  <!-- Layer 3: FW Policy -->
  <div style="background:#ede9fe;border-bottom:1px solid #c4b5fd;padding:10px 16px;">
    <div style="font-weight:700;color:#5b21b6;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">FW Policy / Resolution -- PCode / Punit</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <div style="flex:1;min-width:200px;background:#fff;border:1px solid #c4b5fd;border-radius:4px;padding:6px 10px;font-size:10px;line-height:1.8;">
        <strong>Phase 5 (PrimeCode):</strong><br>
        Reads SST-TF fuses &rarr; writes SST_TF_INFO_0/2/10<br>
        Populates DLCP mask if DLCP SKU
      </div>
      <div style="flex:1;min-width:200px;background:#fff;border:1px solid #c4b5fd;border-radius:4px;padding:6px 10px;font-size:10px;line-height:1.8;">
        <strong>CPL3 (BIOS):</strong><br>
        Programs CLOS_CONFIG[0/3] min/max<br>
        Sets CLOS_ASSOC per core (std) or defers to fuse (DLCP)<br>
        Sets SST_PP_CONTROL.feature_state[1]=1
      </div>
      <div style="flex:1;min-width:200px;background:#fff;border:1px solid #c4b5fd;border-radius:4px;padding:6px 10px;font-size:10px;line-height:1.8;">
        <strong>Runtime (PCode slow loop):</strong><br>
        Resolves HP bucket (active HP count)<br>
        Ordered throttle: LP throttled first (Phase A/B/C)
      </div>
    </div>
  </div>
  <div style="text-align:center;background:#f8fafc;padding:3px 0;font-size:10px;color:#64748b;">&#11015; resolved per-priority workpoints</div>

  <!-- Layer 4: WP4 -->
  <div style="background:#fdf4ff;border-bottom:1px solid #e879f9;padding:10px 16px;">
    <div style="font-weight:700;color:#86198f;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">WP4 Generation / PUNIT Delivery</div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;font-size:10.5px;">
      <div style="background:#fff;border:1px solid #f0abfc;border-radius:4px;padding:6px 10px;flex:1;min-width:160px;"><strong>MASK_HIGH/MASK_LOW</strong><br><span style="font-size:10px;color:#555;">Identifies HP vs LP cores<br>Std: from CLOS_ASSOC<br>DLCP: from PCT_Module_Mask fuse</span></div>
      <div style="background:#fff;border:1px solid #f0abfc;border-radius:4px;padding:6px 10px;flex:1;min-width:160px;"><strong>WP4_HP</strong><br><span style="font-size:10px;color:#555;">HP TRL ~4.4 GHz per CDYN<br>From SST_TF_INFO_2.RATIO_0</span></div>
      <div style="background:#fff;border:1px solid #f0abfc;border-radius:4px;padding:6px 10px;flex:1;min-width:160px;"><strong>WP4_LP</strong><br><span style="font-size:10px;color:#555;">LP clip ~P1 per CDYN<br>From SST_TF_INFO_0.LP_CLIP_RATIO_0</span></div>
      <div style="background:#fff;border:1px solid #f0abfc;border-radius:4px;padding:6px 10px;flex:1;min-width:160px;"><strong>GO command</strong><br><span style="font-size:10px;color:#555;">ACP must not apply WP4<br>until GO_* arrives</span></div>
    </div>
  </div>
  <div style="text-align:center;background:#f8fafc;padding:3px 0;font-size:10px;color:#64748b;">&#11015; masked WP4 writes + GO</div>

  <!-- Layer 5+6: ACP + Core Runtime (combined) -->
  <div style="background:#f0fdf4;border-bottom:1px solid #86efac;padding:10px 16px;">
    <div style="font-weight:700;color:#15803d;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">ACP/Acode Enforcement &rarr; Core Runtime</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <div style="flex:1;min-width:200px;background:#dcfce7;border:2px solid #16a34a;border-radius:5px;padding:8px 10px;font-size:10.5px;">
        <strong style="color:#15803d;">HP Cores (CLOS[0/1]) ~8 per NWP</strong><br>
        P0max turbo ceiling (~4.4 GHz)<br>HP bucket = f(active HP count)<br>
        DLCP: fuse-fixed positions<br>HWP_CAP.highest_perf = P0max
      </div>
      <div style="flex:1;min-width:200px;background:#fff7ed;border:2px solid #ea580c;border-radius:5px;padding:8px 10px;font-size:10.5px;">
        <strong style="color:#c2410c;">LP Cores (CLOS[2/3]) ~88 per NWP</strong><br>
        Clipped to LP_CLIP_RATIO (~P1)<br>Clipped even when HP cores in C6<br>
        Ordered throttle: LP throttled first<br>HWP_CAP.highest_perf = LP clip (DLCP)
      </div>
      <div style="flex:1;min-width:160px;background:#f0f9ff;border:1px solid #7dd3fc;border-radius:5px;padding:8px 10px;font-size:10px;color:#0369a1;">
        <strong>Observability:</strong><br>
        MSR 0x1AD / TURBO_RATIO_LIMIT<br>
        IA32_HWP_CAPABILITIES (per-core)<br>
        SST_TF_INFO_10 (DLCP mask)<br>
        Intel SST tool (OS)
      </div>
    </div>
  </div>

  <!-- Bottom: Key distinctions -->
  <div style="background:#1e3a5f;padding:10px 16px;">
    <div style="font-weight:700;color:#e2e8f0;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">Key Distinctions</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <div style="flex:1;min-width:180px;background:#0f4c81;border:1px solid #3b82f6;border-radius:5px;padding:8px 10px;font-size:10px;color:#e0f2fe;">
        <strong style="color:#93c5fd;">Standard SKU</strong><br>
        CLOS_ASSOC[] set by BIOS<br>Partition Count knob controls HP count<br>User can reassign via SST tool
      </div>
      <div style="flex:1;min-width:180px;background:#312e81;border:1px solid #818cf8;border-radius:5px;padding:8px 10px;font-size:10px;color:#e0e7ff;">
        <strong style="color:#a5b4fc;">DLCP SKU (fuse-fixed)</strong><br>
        PCT_Module_Mask fuse determines HP positions<br>CLOS_ASSOC[] IGNORED by PCode<br>Exposed via SST_TF_INFO_10 (non-zero)
      </div>
      <div style="flex:1;min-width:180px;background:#1e3a5f;border:1px solid #60a5fa;border-radius:5px;padding:8px 10px;font-size:10px;color:#93c5fd;">
        <strong>Ordered Throttle (SST_CP_PRIORITY_TYPE=1)</strong><br>
        Phase A: reduce LP first<br>Phase B: maintain HP while LP &gt; min<br>Phase C: reduce HP only when LP exhausted
      </div>
    </div>
  </div>
</div>
<!-- /raw-html -->

### Frequency Hierarchy

| Name | Description | NWP Example |
|------|-------------|-------------|
| P0max | Maximum turbo (HP ceiling) | ~4.4 GHz (fuse-set) |
| F3 | PCT HP core frequency | ~4.4 GHz |
| P0half | Half-core turbo (requires C6 on half cores) | ~3.9 GHz |
| P0n | All-core turbo | ~3.6 GHz |
| F2 / LP clip | LP core clip (SST_TF_INFO_0.LP_CLIP_RATIO_0) | ~P1 ~2.3 GHz |
| P1 | Guaranteed all-core frequency | -- |

### Key Design Points

- **No C6 requirement**: HP cores achieve P0max with LP cores fully active at ~P1
- **Default disabled (NWP/DMR)**: PCT Partition Count defaults to 0; customers must opt-in
- **HP selection**: MADT-ordered consecutive cores in each partition; 1st M cores per partition = HP
- **DLCP**: HP positions fuse-fixed via PCT_Module_Mask; CLOS_ASSOC[] ignored by PCode
- **DQ mutual exclusion**: PCT and SST-BF are mutually exclusive; PCT and FCT are mutually exclusive

### DMR vs NWP Delta

| Aspect | GNR | DMR / NWP |
|--------|-----|-----------|
| PCT enable fuse | CAPID4.bit29=1 | Not used -- all SKUs can opt-in |
| PCT default at boot | Enabled if fused | Disabled by default (Partition Count=0) |
| HP core count | CAPID4-gated | Available to all SKUs |
| NWP CBBs | N/A | 2 CBBs x 48 cores = 96 total; ~8 HP, ~88 LP |

---

## Section 2: Interfaces and Protocols

### BIOS Knobs

| BIOS Knob | Options | Default | Notes |
|-----------|---------|---------|-------|
| PCT HP Partition Count | 0 -- 16 | **0 (disabled)** | Controls HP core count; 0 = PCT off |
| PCT Core Selection | 0 -- 255 | **0** | Starting core position within partition |

### TPMI / MSR / NVRAM Registers

| Interface | Register | Direction | Purpose |
|-----------|----------|-----------|---------| 
| TPMI | SST_TF_INFO_0.lp_clip_ratio_0 | RO | LP ceiling (~P1); fuse-set by PrimeCode PH5 |
| TPMI | SST_TF_INFO_2.ratio_0 | RO | HP TRL ratio (~4.4 GHz); fuse-set by PrimeCode PH5 |
| TPMI | SST_TF_INFO_8.num_core_0 | RO | Max HP cores; bounds PCT Partition Count knob |
| TPMI | SST_TF_INFO_10 | RO | DLCP PCT_Module_Mask; 0=std SKU, non-zero=DLCP |
| TPMI | SST_CLOS_ASSOC_0..N | RW | Per-core CLOS assignment: HP=CLOS[0/1], LP=CLOS[2/3] |
| TPMI | SST_CLOS_CONFIG[0].max | RW | HP CLOS ceiling = SST_TF_INFO_2.ratio_0 |
| TPMI | SST_CLOS_CONFIG[3].max | RW | LP CLOS ceiling = SST_TF_INFO_0.lp_clip_ratio_0 |
| TPMI | SST_CP_CONTROL.sst_cp_enable | RW | PCT globally enabled bit |
| TPMI | SST_CP_CONTROL.priority_type | RW | 1 = Ordered throttle (LP first) |
| TPMI | SST_PP_CONTROL.feature_state[1] | RW | SST-TF active (set by BIOS at CPL3) |
| MSR | 0x1AD PRIMARY_TURBO_RATIO_LIMIT | RO | HP TRL broadcast; must = SST_TF_INFO_2.ratio_0 (not 0xFF) |
| MSR | IA32_HWP_CAPABILITIES (0x771) | RO | HP: highest_perf=P0max; LP: highest_perf=LP_clip (DLCP) |
| NVRAM | PctHpModuleCount | -- | Number of HP modules from BIOS knob; 0 = disabled |
| PythonSV | sv.socket0.nio0.tpmi.sst_tf_info_10 | RO | DLCP mask discovery |
| PythonSV | sv.socket0.nio0.tpmi.sst_cp_control | RW | Enable / priority type |

---

## Section 3: Reset / Power / Clocking

- **Phase 5 (PrimeCode)**: Reads SST-TF fuses; writes SST_TF_INFO_0.lp_clip_ratio, SST_TF_INFO_2.ratio, SST_TF_INFO_10 (DLCP mask). Happens before BIOS CPL3 handoff.
- **CPL3 (BIOS)**: Programs SST_CLOS_CONFIG[0/3], SST_CLOS_ASSOC, SST_CP_CONTROL.priority_type=1, SST_PP_CONTROL.feature_state[1]=1, MSR 0x1AD=SST_TF_INFO_2.ratio_0.
- **Runtime**: PCode slow loop detects feature_state changes and reloads TRL tables. Ordered throttle enforced on each workpoint update cycle.
- **C-state interaction**: LP clip enforced regardless of HP core C-state. HP cores in C6 do not remove LP clip.
- **OS runtime change**: Intel SST tool can toggle PCT via SST_CP_CONTROL at OS runtime; PCode reacts within 1 slow-loop cycle.

---

## Section 4: Programming Model

### Phase 5 and CPL3 Enabling Sequence

| Step | Actor | Register | Value |
|------|-------|----------|-------|
| 1 | PrimeCode PH5 | SST_TF_INFO_0.lp_clip_ratio_0 | LP ceiling from fuse |
| 2 | PrimeCode PH5 | SST_TF_INFO_2.ratio_0 | HP TRL from fuse (~4.4 GHz) |
| 3 | PrimeCode PH5 | SST_TF_INFO_10 | DLCP mask (0 if std SKU) |
| 4 | BIOS CPL3 | SST_CLOS_CONFIG[0].max | = SST_TF_INFO_2.ratio_0 |
| 5 | BIOS CPL3 | SST_CLOS_CONFIG[3].max | = SST_TF_INFO_0.lp_clip_ratio_0 |
| 6 | BIOS CPL3 | SST_CP_CONTROL.priority_type | = 1 (ordered throttle) |
| 7 | BIOS CPL3 | SST_CLOS_ASSOC[core] | HP -> CLOS[0]; LP -> CLOS[3] |
| 8 | BIOS CPL3 | SST_PP_CONTROL.feature_state[1] | = 1 (SST-TF active) |
| 9 | BIOS CPL3 | MSR 0x1AD | = SST_TF_INFO_2.ratio_0 (not 0xFF) |

### TC 22022422100/16030715678: BIOS Menu check

```python
# Verify BIOS NVRAM knobs visible and correct defaults
assert nvram.PctHpModuleCount == 0   # disabled by default on NWP/DMR
# After enabling PCT with N partitions
assert nvram.PctHpModuleCount == N
```

### TC 22022422103/16030715690: TPMI register check

```python
nio = sv.socket0.nio0
# LP clip ratio present
lp_clip = nio.tpmi.sst_tf_info_0.lp_clip_ratio_0
assert lp_clip > 0, "LP clip not populated"
# HP TRL ratio present
hp_trl = nio.tpmi.sst_tf_info_2.ratio_0
assert hp_trl > lp_clip, "HP TRL must exceed LP clip"
# DLCP check
dlcp_mask = nio.tpmi.sst_tf_info_10
print("DLCP mode:", "active" if dlcp_mask != 0 else "standard")
# CLOS assignments
assert nio.tpmi.sst_clos_assoc_0 in (0, 1)    # HP = CLOS 0 or 1
```

### TC 22022422118/16030715682: DQ Rules (FlexconPM)

```python
# FlexconPM validates DQ rules automatically
# Key rules checked:
# 1. PCT and SST-BF mutually exclusive
# 2. PCT and FCT mutually exclusive
# 3. SST_CP_CONTROL.priority_type == 1 when PCT enabled
# 4. MSR 0x1AD != 0xFF (must be SST_TF_INFO_2.ratio_0)
# 5. SST_TF_INFO_10 consistent with CLOS_ASSOC (std vs DLCP)
```

---

## Section 5: Operational Behavior

| Scenario | Expected |
|----------|----------|
| PCT disabled (Partition Count=0) | All cores at legacy TRL; SST_CP_CONTROL.sst_cp_enable=0 |
| PCT enabled, standard SKU | CLOS_ASSOC set by BIOS; HP at P0max; LP at LP_clip |
| PCT enabled, DLCP SKU | SST_TF_INFO_10 non-zero; HP positions fuse-fixed; CLOS_ASSOC ignored |
| BIOS menu visible | PCT Partition Count knob visible; default 0 |
| OS SST tool toggle | PCT enable/disable takes effect within 1 PCode slow-loop cycle |
| Power limit active | Ordered throttle: LP cores throttled first (Phase A), then HP (Phase C) |
| HP cores in C6 | LP cores remain at LP_clip; invariant not broken |
| DQ rules violated | FlexconPM DQ check fails; PCT+BF or PCT+FCT combination flagged |

---

## Section 6: Corner Cases & Error Handling

- **MSR 0x1AD = 0xFF**: Invalid on NWP/DMR per HSD 14025997048. MSR must be programmed to SST_TF_INFO_2.ratio_0 value. FlexconPM DQ check TC 22022422118 validates this.
- **DLCP vs standard**: If SST_TF_INFO_10 != 0, CLOS_ASSOC[] is irrelevant; HP positions are fuse-determined. TC 22022422103 must check INFO_10 first to branch between std vs DLCP validation paths.
- **Partition Count overflow**: PCT Partition Count is bounded by SST_TF_INFO_8.NUM_CORE_0 / MAX_LPIDS. BIOS must not exceed this; TC should verify knob range is correct.
- **PCT+BF mutual exclusion**: If SST-BF knob is also enabled, both features conflict. DQ rule enforces mutual exclusion. FlexconPM TC 22022422118 catches this.
- **PV discovery (TC 16030717720)**: Intel SST tool output should show PCT feature_state=1, HP partition count, HP/LP assignment. Validates end-to-end visibility from OS to hardware.

---

## Section 7: Security / Safety / Policy

- SST_CLOS_ASSOC is OS-writable (ring-0). Malicious reassignment of HP/LP roles possible. PCode does not validate CLOS assignments against fuse intent (except DLCP where fuse overrides SW).
- On DLCP SKUs, PCT_Module_Mask fuse provides hardware-enforced HP core selection that cannot be overridden by SW.
- MSR 0x1AD write by ring-0 is reconciled by PCode on next slow-loop cycle.

---

## Section 8: References

- [PCT (Priority Core Turbo) HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html)
- [Priority Core Turbo Technology White Paper](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/IC_PCT.html)
- [PRIMECODE-9334 PCT FHAS](https://docs.intel.com/documents/primecode/fhas/GNR/PCT/PRIMECODEF-9334-PCT.html)
- [DMR Turbo HAS -- PCT section](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html)
- [CPUPM BIOS Knobs Reference Gen 3](https://docs.intel.com/documents/System-firmware-bios/Domain/ServerCpuPm/Index/CPUPM%20BIOS%20Knobs/BiosKnobs.html)
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html)
- [NWP PM MAS -- PCT section](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [HSD 14025997048](https://hsdes.intel.com/appstore/article-one/#/14025997048) -- MSR 0x1AD must not be 0xFF
- [HSD 14026595435](https://hsdes.intel.com/appstore/article-one/#/14026595435) -- NWP 8 HP cores ~4.4 GHz PCT target
- [SST-TF Functionality TCD 22022420928](https://hsdes.intel.com/appstore/article-one/#/22022420928)
- [SST-TF Enabling TCD 22022420925](https://hsdes.intel.com/appstore/article-one/#/22022420925)
- KB: KB/pm_features/sst/pct.md
