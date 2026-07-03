# TCD: PCT - DLCP (Die Level Cherry Picking)

| Field | Value |
|-------|-------|
| **TCD ID** | [16030982802](https://hsdes.intel.com/appstore/article-one/#/16030982802) |
| **Title** | PCT - DLCP (Die Level Cherry Picking) |
| **Status** | open |
| **Owner** | mps |
| **Parent TPF** | [16030762939](https://hsdes.intel.com/appstore/article-one/#/16030762939) |
| **Parent TP** | [16030762839 — NWP PM SST](https://hsdes.intel.com/appstore/article-one/#/16030762839) |
| **NWP Status** | TBD — pending `PCT_Module_Mask` fuse confirmation on NWP SKU |
| **KB last updated** | 2026-07-03 |

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

```
Reset Phase 5 (PrimeCode)
  |
  +---> Read PCT_Module_Mask OTP fuse per CBB dielet
  |       cbb0: PCT_Module_Mask[7:0] -> SST_TF_INFO_10[7:0] (RO)
  |       cbb1: PCT_Module_Mask[7:0] -> SST_TF_INFO_10[7:0] (RO)
  |
BIOS CPL3
  |
  +---> Read SST_TF_INFO_10 per CBB dielet
  |       If non-zero -> DLCP mode: use mask for SST_CLOS_ASSOC programming
  |       If zero     -> standard PCT: BIOS derives HP cores from MADT order
  |
  +---> Program SST_CLOS_ASSOC per core to match DLCP mask
  |       Modules in mask -> CLOS[0] (HP, gets HP TRL ~4.4 GHz)
  |       Modules not in mask -> CLOS[3] (LP, clipped to LP_CLIP ~P1)
  |
  +---> SST_TF_INFO_10 populates IA32_HWP_CAPABILITIES:
          HP modules -> highest_perf = P0max
          LP modules -> highest_perf = LP_CLIP
          OS discovers HP/LP without TPMI query
```

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

| TC | Title | NWP Disposition | Scenario |
|----|-------|-----------------|---------|
| TBD | PCT - DLCP SST_TF_INFO_10 Fuse-to-Register Verification | Runnable_On_N-1 | A + B |
| TBD | PCT - DLCP HP Core Position and HWP Capabilities Verification | Runnable_On_N-1 | A only |
| TBD | PCT - Per-SST-Instance Programming Completeness (NWP 2-CBB) | Runnable_On_N-1 | A + B |
| TBD | PCT - NWP MADT Partition Algorithm Validation | Runnable_On_N-1 | A + B |

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
