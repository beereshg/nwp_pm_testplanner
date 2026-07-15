# TCD: PCT - DLCP (Die Level Cherry Picking)

| Field | Value |
|-------|-------|
| **TCD ID** | [16030982802](https://hsdes.intel.com/appstore/article-one/#/16030982802) |
| **Title** | PCT - DLCP (Die Level Cherry Picking) |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030762939](https://hsdes.intel.com/appstore/article-one/#/16030762939) |
| **Parent TP** | [16030762839 — NWP PM SST](https://hsdes.intel.com/appstore/article-one/#/16030762839) |
| **Child TCs** | [16030982833](https://hsdes.intel.com/appstore/article-one/#/16030982833) -- DLCP SST_TF_INFO_10 Fuse-to-Register Verification<br>[16030982837](https://hsdes.intel.com/appstore/article-one/#/16030982837) -- DLCP HP Core Position and HWP Capabilities Verification<br>[16030982844](https://hsdes.intel.com/appstore/article-one/#/16030982844) -- Per-SST-Instance Programming Completeness (NWP 2-CBB)<br>[16030982850](https://hsdes.intel.com/appstore/article-one/#/16030982850) -- NWP MADT Partition Algorithm Validation |
| **NWP Status** | Runnable_On_NWP — 4 TCs covering Scenario A (DLCP active) and Scenario B (DLCP absent) |
| **KB last updated** | 2026-07-15 |

---

## Section 1: Architecture / Micro-architecture and Functionality

DLCP (Die Level Cherry Picking) is a variant of PCT (Priority Core Turbo) where HP core positions are **fixed at manufacturing time** via the `PCT_Module_Mask` OTP fuse, rather than BIOS computing HP positions from APIC-ID / MADT order at boot. PrimeCode reads this fuse at Reset Phase 5 and populates the read-only `SST_TF_INFO_10` TPMI register per CBB dielet. BIOS reads `SST_TF_INFO_10` and **must honor** that mask when programming `SST_CLOS_ASSOC`. In DLCP mode, `IA32_HWP_CAPABILITIES.highest_perf` differs per core (HP = P0max; LP = LP_CLIP), enabling OS-level HP/LP discovery without TPMI enumeration.

### Feature Overview

DLCP is a super-set of standard PCT. The two operational scenarios are:

| Scenario | Condition | TC Impact |
|----------|-----------|-----------|
| A — DLCP Active | `PCT_Module_Mask` ≠ 0; `SST_TF_INFO_10` ≠ 0 | Full DLCP validation: TCs 1 + 2 + 3 + 4 |
| B — DLCP Absent | `PCT_Module_Mask` = 0; `SST_TF_INFO_10` = 0 | TC 1 as negative check; TC 2 skip; TCs 3 + 4 as NWP topology tests |

### Key Registers

| Register | Type | Description |
|----------|------|-------------|
| `PCT_Module_Mask` | OTP fuse | Manufacturing-fixed HP module mask per CBB dielet |
| `SST_TF_INFO_10` | RO TPMI | HP module mask exposed to BIOS/OS per CBB dielet |
| `SST_CLOS_ASSOC` | RW TPMI | CLOS assignment — must follow DLCP mask when non-zero |
| `IA32_HWP_CAPABILITIES.highest_perf` | MSR | HP = P0max; LP = LP_CLIP in DLCP mode |
| `SST_CP_CONTROL.sst_cp_enable` | RW TPMI | PCT globally enabled (1 = on) |
| `SST_CP_CONTROL.sst_cp_priority_type` | RW TPMI | Ordered throttle (1 = Ordered) |

### DLCP Boot Flow

<!-- raw-html -->
<div style="margin:14px 0;border:1px solid #bfcfe8;border-radius:8px;overflow:hidden;font-family:'Segoe UI',Arial,sans-serif;font-size:11.5px;max-width:860px;">
  <div style="background:#1e3a5f;color:#fff;padding:8px 16px;font-weight:700;font-size:12px;letter-spacing:.5px;text-align:center;">DLCP Boot Flow: OTP Fuse &rarr; TPMI &rarr; BIOS &rarr; OS Discovery</div>
  <div style="padding:14px 18px;background:#f8fafc;">
    <!-- Row 1: Manufacturing -->
    <div style="display:flex;gap:8px;align-items:stretch;margin-bottom:4px;">
      <div style="flex:1;background:#fff3e0;border:2px solid #e65100;border-radius:6px;padding:8px 12px;">
        <div style="font-weight:700;color:#c2410c;font-size:10.5px;margin-bottom:4px;">&#128295; Manufacturing (OTP Fuse)</div>
        <div style="font-size:10px;color:#333;line-height:1.8;">
          <strong>PCT_Module_Mask</strong> fuse per CBB dielet<br>
          Encodes which modules are HP (bit=1)<br>
          One fuse per CBB (cbb0, cbb1 on NWP)<br>
          <span style="color:#92400e;">Set once at sort — hardware-immutable</span>
        </div>
      </div>
    </div>
    <div style="text-align:center;font-size:10px;color:#64748b;padding:2px 0;">&#11015; Reset Phase 5</div>
    <!-- Row 2: PrimeCode PH5 -->
    <div style="display:flex;gap:8px;align-items:stretch;margin-bottom:4px;">
      <div style="flex:1;background:#ede9fe;border:2px solid #6d28d9;border-radius:6px;padding:8px 12px;">
        <div style="font-weight:700;color:#5b21b6;font-size:10.5px;margin-bottom:4px;">PrimeCode Phase 5 (per CBB)</div>
        <div style="font-size:10px;color:#333;line-height:1.8;">
          Reads PCT_Module_Mask fuse<br>
          Writes <strong>SST_TF_INFO_10</strong> TPMI register (RO)<br>
          cbb0: INFO_10 &larr; cbb0 PCT_Module_Mask<br>
          cbb1: INFO_10 &larr; cbb1 PCT_Module_Mask<br>
          <span style="color:#5b21b6;">Happens before BIOS CPL3 handoff</span>
        </div>
      </div>
    </div>
    <div style="text-align:center;font-size:10px;color:#64748b;padding:2px 0;">&#11015; CPL3 (BIOS reads SST_TF_INFO_10)</div>
    <!-- Row 3: BIOS CPL3 (two paths) -->
    <div style="display:flex;gap:8px;align-items:stretch;margin-bottom:4px;">
      <div style="flex:1;background:#dcfce7;border:2px solid #16a34a;border-radius:6px;padding:8px 12px;">
        <div style="font-weight:700;color:#15803d;font-size:10.5px;margin-bottom:4px;">&#10003; Scenario A: DLCP Active (INFO_10 &ne; 0)</div>
        <div style="font-size:10px;color:#333;line-height:1.8;">
          SST_CLOS_ASSOC[core] &larr; DLCP mask<br>
          Modules in mask &rarr; CLOS[0] (HP, ~4.4 GHz)<br>
          Modules not in mask &rarr; CLOS[3] (LP, ~P1)<br>
          <strong>MADT APIC-ID order ignored</strong> for HP selection
        </div>
      </div>
      <div style="flex:1;background:#f1f5f9;border:2px solid #94a3b8;border-radius:6px;padding:8px 12px;">
        <div style="font-weight:700;color:#475569;font-size:10.5px;margin-bottom:4px;">&#9711; Scenario B: DLCP Absent (INFO_10 = 0)</div>
        <div style="font-size:10px;color:#333;line-height:1.8;">
          SST_CLOS_ASSOC[core] &larr; MADT/APIC-ID order<br>
          First N modules per partition &rarr; HP<br>
          TC 16030982833 runs as <em>negative check</em><br>
          TC 16030982837 skipped (no DLCP mask to validate)
        </div>
      </div>
    </div>
    <div style="text-align:center;font-size:10px;color:#64748b;padding:2px 0;">&#11015; OS / PythonSV observability</div>
    <!-- Row 4: OS discovery -->
    <div style="display:flex;gap:8px;align-items:stretch;">
      <div style="flex:1;background:#e0f2fe;border:1px solid #7dd3fc;border-radius:6px;padding:8px 12px;font-size:10.5px;">
        <div style="font-weight:700;color:#0369a1;margin-bottom:4px;">IA32_HWP_CAPABILITIES (MSR 0x771) per-core</div>
        <div style="display:flex;gap:8px;">
          <div style="flex:1;background:#dcfce7;border:1px solid #16a34a;border-radius:4px;padding:5px 8px;font-size:10px;"><strong>HP cores:</strong><br>highest_perf = P0max<br>OS sees elevated ceiling</div>
          <div style="flex:1;background:#fff7ed;border:1px solid #ea580c;border-radius:4px;padding:5px 8px;font-size:10px;"><strong>LP cores:</strong><br>highest_perf = LP_CLIP<br>OS sees clipped ceiling</div>
        </div>
        <div style="margin-top:6px;font-size:9.5px;color:#0369a1;">OS/scheduler can discover HP/LP without TPMI query in DLCP mode</div>
      </div>
    </div>
  </div>
</div>
<!-- /raw-html -->

### NWP-Specific Deltas

- NWP has **2 CBBs** (cbb0, cbb1) — 8 HP cores total across 4 partitions (PctHpModuleCount = default)
- Each CBB has its own `PCT_Module_Mask` fuse and `SST_TF_INFO_10` register
- DLCP applicability on NWP **TBD** — depends on whether NWP SKU populates `PCT_Module_Mask`
- If `PCT_Module_Mask = 0` on all NWP SKUs, DLCP TCs run as negative/structural checks only
- Register access: `sv.socket0.cbbX.base.tpmi.sst_tf_info_10` (X = 0, 1)
- CAPID4.bit29 fuse must be 1 for PCT capability (verified via `sv.socket0.nio.punit.ptpcioregs.ptpcioregs.capid4.capid4_29`)

---

## Section 2: Interfaces and Protocols

- **TPMI** (primary in-band interface): `SST_TF_INFO_10` (RO), `SST_CLOS_ASSOC` (RW), `SST_CP_CONTROL` (RW)
- **OTP fuse** (manufacturing): `PCT_Module_Mask` — set once at sort; not software-writable
- **MSR** (OS-visible): `IA32_HWP_CAPABILITIES.highest_perf` — per-core HP/LP indication
- **BIOS**: Programs `SST_CLOS_ASSOC` at CPL3 using DLCP mask from `SST_TF_INFO_10`
- **PCode**: Reads fuse at reset; programs `SST_TF_INFO_10`; enforces HP/LP TRL separation at runtime

---

## Section 3: Reset, Power, and Clocking

- `PCT_Module_Mask` is read and `SST_TF_INFO_10` populated by PrimeCode at **Reset Phase 5**
- `SST_TF_INFO_10` is read-only after PrimeCode programs it — no SW override
- BIOS reads `SST_TF_INFO_10` during **CPL3** before OS handoff
- DLCP has no separate power/clock enable beyond the standard PCT enable (`sst_cp_enable = 1`)

---

## Section 4: Programming Model

**Step 1 — Verify DLCP capability:**
```python
# Check fuse — must be 1 for PCT capability
cap = sv.socket0.nio.punit.ptpcioregs.ptpcioregs.capid4.capid4_29.get_value()
assert cap == 1, 'PCT not fuse-capable on this SKU'

# Read DLCP mask per CBB
for cbb in sv.socket0.cbbs:
    mask = cbb.base.tpmi.sst_tf_info_10.get_value()
    print(f'{cbb.target_info["name"]}: SST_TF_INFO_10 = {hex(mask)}')
    # Non-zero -> DLCP Scenario A; zero -> Scenario B
```

**Step 2 — Verify CLOS assignment follows DLCP mask (Scenario A):**
```python
import diamondrapids.pm.Active_PM.SST.pct.pct_focus as pctd
pctd.generate_core_list()
for cbb in sv.socket0.cbbs:
    mask = cbb.base.tpmi.sst_tf_info_10.get_value()
    for module_idx in range(12):  # NWP: 12 modules per CBB
        clos = cbb.base.tpmi.sst_clos_assoc_0.get_value()  # per-module CLOS ID
        expected = 0 if (mask >> module_idx) & 1 else 3    # HP=CLOS[0], LP=CLOS[3]
        # assert actual_clos == expected
```

**Step 3 — Verify HWP capabilities reflect DLCP:**
```python
for core in pctd.HP_CORES:
    hwp_cap = pd.debug.access_to_msr(0x771, core=core)  # IA32_HWP_CAPABILITIES
    hp_perf = (hwp_cap >> 24) & 0xFF  # highest_perf field
    # HP cores: hp_perf should equal P0max encoding
for core in pctd.LP_CORES:
    hwp_cap = pd.debug.access_to_msr(0x771, core=core)
    hp_perf = (hwp_cap >> 24) & 0xFF
    # LP cores: hp_perf should equal LP_CLIP encoding
```

---

## Section 5: Operational Behavior

### TC Coverage Map

| TC ID | Title | NWP Disposition | Scenario |
|-------|-------|-----------------|----------|
| [16030982833](https://hsdes.intel.com/appstore/article-one/#/16030982833) | PCT - DLCP SST_TF_INFO_10 Fuse-to-Register Verification | Runnable_On_NWP | A + B |
| [16030982837](https://hsdes.intel.com/appstore/article-one/#/16030982837) | PCT - DLCP HP Core Position and HWP Capabilities Verification | Runnable_On_NWP | A only |
| [16030982844](https://hsdes.intel.com/appstore/article-one/#/16030982844) | PCT - Per-SST-Instance Programming Completeness (NWP 2-CBB) | Runnable_On_NWP | A + B |
| [16030982850](https://hsdes.intel.com/appstore/article-one/#/16030982850) | PCT - NWP MADT Partition Algorithm Validation | Runnable_On_NWP | A + B |

---

## Section 6: Corner Cases and Error Handling

- **`PCT_Module_Mask = 0` on NWP SKU**: DLCP TCs pivot to Scenario B (negative checks). Test must detect and branch.
- **DLCP mask conflicts with MADT BIOS algorithm**: BIOS override validation — `SST_CLOS_ASSOC` must match `SST_TF_INFO_10` mask, not MADT order.
- **`SST_TF_INFO_10` written by SW**: Should be read-only; test must verify write-protect (attempted write must not change value).
- **HP mask spanning CBB boundary**: Each CBB has its own `SST_TF_INFO_10` — cross-CBB mask consistency not guaranteed.

---

## Section 7: Security / Safety / Policy

- `PCT_Module_Mask` is an OTP fuse — hardware enforcement. No SW can override post-manufacturing.
- `SST_TF_INFO_10` is read-only to OS/BIOS — same hardware protection as other SST_TF_INFO registers.
- DLCP differentiates per-core `IA32_HWP_CAPABILITIES.highest_perf`, which is OS-visible — must match DLCP mask to avoid OS scheduling anomalies.

---

## Section 8: References

- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — `PCT_Module_Mask`; `SST_TF_INFO_10`; DLCP HP core discovery
- [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — `SST_CLOS_CONFIG` / `SST_CLOS_ASSOC` / `SST_CP_CONTROL`; Ordered Throttling
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PCT scope; DLCP confirmation pending
- CCB HSD 14026595435 — NWP PCT 8 HP cores, 4.4 GHz target
