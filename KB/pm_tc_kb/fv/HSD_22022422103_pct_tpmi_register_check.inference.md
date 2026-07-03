# Deep Analysis: PCT - TPMI Register Check

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422103](https://hsdes.intel.com/appstore/article-one/#/22022422103) |
| **Title** | PCT - TPMI Register Check |
| **Date** | 2026-06-23 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SST |
| **Sub-Feature** | PCT (Priority Core Turbo) — SST-TF TPMI CLOS register boot-time validation |
| **Parent TCD** | [22022420855 — PCT - Enabling & Discovery](https://hsdes.intel.com/appstore/article-one/#/22022420855) |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Val Environment** | virtual_platform |
| **Framework** | os-svos |
| **Owner** | mps |
| **Tags** | plc.feature.p1, PMSS_NWP_READINESS_CHECK |

## Version History
- v1 (2025-07-24): Initial — sections A, B, F only
- v2 (2026-06-23): Full enrichment — all sections A-G, NWP register paths, PSS grading

---

## Test Case Intent

Verify that TPMI SST_CLOS registers are **correctly programmed by PCode at boot** to reflect the
BIOS-configured HP core count. This is a register-level boot validation — no runtime workload needed.
Environment: NWP silicon or emulation (PythonSV/namednodes direct TPMI access, not OS driver).

**Key distinction from PV TC 16030717720 (Discovery)**: This TC reads raw TPMI registers directly;
PV exercises the `sst` tool + `intel-speed-select` driver path.

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP silicon or emulation with PCT enabled |
| BIOS knobs | `PctHpModuleCount` set to non-zero (multiples of 4); `PctCapableSystem` enabled |
| FW stack | PCode, PrimeCode, PythonSV, namednodes installed |
| CAPID4 | `sv.socket0.nio.punit.ptpcioregs.ptpcioregs.capid4.capid4_29` = 1 (PCT fuse enabled) |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Read `CAPID4.bit29` from NWP CAPID path | = 1 (PCT capability fuse set) | = 0 → PCT not fused, TC cannot run |
| 2 | Read `nvram.PctHpModuleCount.getValue()` | Non-zero; multiple of 4 | Zero or invalid |
| 3 | For each CBB (cbb0, cbb1): read `SST_CLOS_ASSOC_0.clos_id_module[N]` for first M modules | First `PctHpModuleCount/2` modules per CBB → CLOS 0 (HP); rest → CLOS 2/3 (LP) | CLOS assignment mismatch |
| 4 | Read `SST_CP_CONTROL.sst_cp_enable` per CBB | = 1 (PCT globally enabled) | = 0 |
| 5 | Read `SST_CP_CONTROL.sst_cp_priority_type` per CBB | = 1 (Ordered Throttling mode) | ≠ 1 |
| 6 | Read `SST_TF_INFO_1.num_core_0` per CBB | ≥ configured HP module count | < configured value |
| 7 | **[DLCP check]** Read `SST_TF_INFO_10` from both CBBs. `for cbb in [0,1]: info10=sv.socket0.cbb[cbb].base.tpmi.sst_tf_info_10.read(); print(f'CBB{cbb} SST_TF_INFO_10=0x{info10:08X}')` | **Scenario A (DLCP active):** non-zero value matching `PCT_Module_Mask` fuse on both CBBs. **Scenario B (non-DLCP):** = 0 on both CBBs and MADT-order CLOS assignment governs | Fuse \u2260 register — PrimeCode Phase 5 init failure |
| 8 | **[DLCP check]** Verify `SST_TF_INFO_10` is RO: attempt write; read back to confirm unchanged. | Value unchanged after write attempt | Value changed — register incorrectly writable |

### Pass / Fail Criteria

- **PASS**: CAPID4.bit29=1; CLOS assignments match BIOS HP count; `sst_cp_enable`=1; `sst_cp_priority_type`=1; num_core_0 ≥ HP count
- **FAIL**: Any register mismatch; CAPID4.bit29=0; CLOS assignment incorrect; PCT globally disabled

---

## Section A: NWP Delta

**Disposition: Runnable_On_N-1** — PCT relies on SST-TF infrastructure which is functional on NWP.

| Aspect | DMR | NWP | Adaptation Required |
|--------|-----|-----|---------------------|
| Number of CBBs | 4 | **2** | Loop `range(2)` not `range(4)` |
| Cores per CBB | 64 | **48** | Adjust module count calculations |
| Total cores | 256 | **96** (2×48) | Update HP count validation |
| CAPID4 namednodes path | `sv.socket0.imh0.punit.ptpcioregs.capid4_29` | **`sv.socket0.nio.punit.ptpcioregs.ptpcioregs.capid4.capid4_29`** | Path changed: `imh0` → `nio` |
| SST TPMI path | `sv.socket0.imhX.base.tpmi.sst_*` | **`sv.socket0.cbbX.base.tpmi.sst_*`** | CBB path (same as DMR CBB) |
| Automation config | `dmr.xml` | **`nwp.xml`** | Config swap |
| SST python package | `diamondrapids` | **`newport`** | Package update |

**NWP-specific critical note**: `CAPID4.bit29` is at `sv.socket0.nio.punit.ptpcioregs.ptpcioregs.capid4.capid4_29` (NIO Punit, not IMH Punit).

---

## Section B: Interactions

### Key Registers (NWP Namednodes Paths)

| Register | NWP Namednodes Path | Purpose |
|----------|--------------------|----|
| `CAPID4.bit29` | `sv.socket0.nio.punit.ptpcioregs.ptpcioregs.capid4.capid4_29` | Fuse: PCT capability enable |
| `PctHpModuleCount` | `nvram.PctHpModuleCount.getValue()` | BIOS: HP module count (multiples of 4) |
| `SST_CLOS_ASSOC_0.clos_id_module{N}` | `sv.socket0.cbb{X}.base.tpmi.sst_clos_assoc_0.clos_id_module{N}` | Module CLOS assignment (0/1=HP, 2/3=LP) |
| `SST_CP_CONTROL.sst_cp_enable` | `sv.socket0.cbb{X}.base.tpmi.sst_cp_control.sst_cp_enable` | PCT globally enabled (1=on) |
| `SST_CP_CONTROL.sst_cp_priority_type` | `sv.socket0.cbb{X}.base.tpmi.sst_cp_control.sst_cp_priority_type` | Throttling mode (1=Ordered) |
| `SST_TF_INFO_1.num_core_0` | `sv.socket0.cbb{X}.base.tpmi.sst_tf_info_1.num_core_0` | Max HP modules supported by silicon |
| `MSR 0x774 IA32_HWP_REQUEST` | `pd.debug.access_to_msr(0x774, core=core)` | HWP desired ratio (HP cores: request P0) |
| `MSR 0x198 IA32_PERF_STATUS` | `pd.debug.access_to_msr(0x198, core=core)` | Current operating ratio |

### PythonSV Validation Sketch

```python
# NWP PCT TPMI register check (2 CBBs × 48 cores)
import sv

# Step 1: Check CAPID4.bit29 (NIO path on NWP)
capid4_pct = sv.socket0.nio.punit.ptpcioregs.ptpcioregs.capid4.capid4_29.read()
print(f"CAPID4.bit29 (PCT fuse) = {capid4_pct}  (expect 1)")
assert capid4_pct == 1, "PCT fuse not set — TC cannot run"

# Step 2: Read BIOS HP module count
hp_count = nvram.PctHpModuleCount.getValue()
print(f"PctHpModuleCount = {hp_count}  (expect non-zero, multiple of 4)")
assert hp_count > 0 and hp_count % 4 == 0

# Step 3: Verify CLOS assignment per CBB
for cbb_idx in range(2):   # NWP: 2 CBBs
    cbb = sv.socket0.getbypath(f"cbb{cbb_idx}")
    hp_per_cbb = hp_count // 2  # HP modules split evenly across 2 CBBs
    for mod in range(48 // 2):  # 24 modules per CBB (2 cores/module)
        clos = cbb.base.tpmi.sst_clos_assoc_0.getbypath(f"clos_id_module{mod}").read()
        expected = 0 if mod < hp_per_cbb else 2  # HP=CLOS0, LP=CLOS2
        print(f"CBB{cbb_idx} mod{mod}: CLOS={clos}  (expect {expected})")
        assert clos == expected, f"CLOS mismatch CBB{cbb_idx} mod{mod}: got {clos} expected {expected}"

    # Step 4-5: PCT control registers
    cp_en = cbb.base.tpmi.sst_cp_control.sst_cp_enable.read()
    cp_type = cbb.base.tpmi.sst_cp_control.sst_cp_priority_type.read()
    num_core = cbb.base.tpmi.sst_tf_info_1.num_core_0.read()
    print(f"CBB{cbb_idx}: cp_enable={cp_en} priority_type={cp_type} num_core_0={num_core}")
    assert cp_en == 1, f"PCT not enabled on CBB{cbb_idx}"
    assert cp_type == 1, f"Priority type != Ordered on CBB{cbb_idx}"
    assert num_core >= hp_per_cbb, f"num_core_0 < HP count on CBB{cbb_idx}"

print("PASS: PCT TPMI registers correctly programmed")
```

---

## Section C: Coverage

| Coverage Area | DMR Coverage | NWP Adaptation | Gap |
|--------------|-------------|----------------|-----|
| CAPID4.bit29 fuse check | ✅ | ✅ Path changed to NIO | None after path fix |
| CLOS assignment per module | ✅ 4 CBBs | ✅ 2 CBBs | CBB loop bounds |
| `sst_cp_enable` per CBB | ✅ | ✅ | None |
| `sst_cp_priority_type` per CBB | ✅ | ✅ | None |
| `sst_tf_info_1.num_core_0` | ✅ | ✅ | None |
| HP count validation math | 4 CBBs÷4 = 1×HP | **2 CBBs÷2 = hp_count/2 per CBB** | Must recalculate |
| VP/HSLE environment | Limited | ✅ `virtual_platform` env | Run on VP |

---

## Section D: Spec Refs

| Reference | Link |
|-----------|------|
| SST HAS — PCT registers | [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| NWP PM MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |
| PCT KB article | [KB/pm_features/sst/pct.md](../../../pm_features/sst/pct.md) |
| Parent TCD 22022420855 | [PCT Enabling & Discovery](https://hsdes.intel.com/appstore/article-one/#/22022420855) |

---

## Section E: Risk Assessment

| # | Risk | Severity | Notes |
|---|------|----------|-------|
| 1 | CAPID4 path change (`imh0` → `nio`) missed | High | Must use `sv.socket0.nio.punit.ptpcioregs.*` not IMH path |
| 2 | HP module count math — CBB count changed (4→2) | Medium | `hp_per_cbb = hp_count // 2` (not // 4) |
| 3 | Automation still uses `dmr.xml` | Medium | Must change to `nwp.xml` |
| 4 | SST python package (`diamondrapids` → `newport`) | Low | Package name update needed |

---

## Section F: Recommendations

**Adopt with adaptation.** PCT/SST-TF functional on NWP.

Required changes:
1. `CAPID4.bit29` path: `sv.socket0.imh0.punit.*` → `sv.socket0.nio.punit.ptpcioregs.ptpcioregs.capid4.capid4_29`
2. CBB loop: `range(4)` → `range(2)` 
3. HP count per CBB: `hp_count // 4` → `hp_count // 2`
4. Automation: `dmr.xml` → `nwp.xml`
5. SST package: `diamondrapids` → `newport`

---

## Section G: PSS Grading

| Sl No | Dimension | Value | Rationale |
|-------|-----------|-------|-----------|
| 1 | NWP Delta | Yes | 2 CBBs (not 4); CAPID4 path change; HP count math update |
| 2 | Applicable NWP | **Yes** | SST-TF/PCT functional on NWP; register check is direct TPMI read |
| 3 | PSS Environment | ✅ Virtual Platform | VP can run TPMI register checks; `virtual_platform` env tagged |
| 4 | Silicon Only | No | VP feasible for register-level boot validation |
| 5 | Test Content | DMR_L | Low adaptation: path fix + CBB count; test intent unchanged |
| 6 | OS | sv-os | PythonSV namednodes (no OS driver needed) |

### Verdict

**Runnable_On_N-1** — direct TPMI register read after boot; VP-capable; low adaptation overhead.
Key adaptation: CAPID4 NIO path + 2-CBB loop + HP count math correction.

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

PCT (Performance Core Tuning) partitions cores into High Priority (HP) and Low Priority (LP) groups, allowing HP cores to run at a higher turbo frequency when power allows. PCT relies on SST-TF infrastructure (TPMI-based CLOS configuration), and SST-TF is **functional on NWP** (not ZBB).

Test verifies TPMI registers after boot:
- `SST_CLOS_CONFIG[0]`: HP cores — min=P1, max=SST_TF turbo ratio
- `SST_CLOS_CONFIG[3]`: LP cores — min=Pn, max=LP clip ratio
- `SST_CP_CONTROL.SST_CP_PRIORITY_TYPE = 1` (Ordered Throttling)
- `SST_PP_CONTROL.feature_state[1] = 1` (SST-TF enabled)

NWP topology: 2 CBBs × 48 cores = 96 total cores; `sst_pp_control` per CBB.

Tags: `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p pct -tM 60 -M 10 --retry_count 2
```

### NWP CLOS Configuration Check
```python
# NWP: verify PCT CLOS config per CBB (2 CBBs, 48 cores each)
for cbb_idx in range(2):
    cbb = sv.socket0.cbb[cbb_idx]
    # Check CLOS config for HP (CLOS[0]) and LP (CLOS[3])
    # cbb.punit.sst_clos_config[0]  -- HP config
    # cbb.punit.sst_clos_config[3]  -- LP config
    # cbb.punit.sst_cp_control.sst_cp_priority_type  -- expect = 1
```

### Pass Criteria
- `SST_CLOS_CONFIG[0]` and `[3]` match BIOS settings
- `SST_CP_CONTROL.SST_CP_PRIORITY_TYPE = 1` (Ordered Throttling)
- `SST_PP_CONTROL.feature_state[1] = 1` per CBB
- HP cores subscribed to CLOS[0], LP cores to CLOS[3]
- `pct` PMx plugin passes for NWP

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; 2 CBBs × 48 cores; PCT/SST-TF functional on NWP; SST python package: `diamondrapids` → `newport`**

**Priority**: High — `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`; PCT TPMI register baseline is foundation for all PCT functional tests

---

## Feature Classification: Silicon-Heavy with Firmware Orchestration

> **PCT is primarily a silicon-heavy feature with moderate firmware orchestration.**
> Firmware/BIOS/PCode are important for discovery, programming, and policy — but the
> feature is fundamentally rooted in hardware capability and hardware behavior.

### Silicon-Heavy Evidence
- `CAPID4.bit29 = PCT_ENABLE`: feature is fuse-gated — silicon capability, not a firmware construct
- Core frequency/TRL enforcement happens in hardware (Acode + CBB PCode at RTL level)
- Topology (HP/LP core assignment) implemented in silicon CLOS hardware
- Key scenarios (C6 interaction, TDP convergence, real power/frequency) require real silicon
- PSS model gaps exist: VP cannot model exact Acode behavior; HSLE cannot model cross-die HPM

### Firmware Orchestration Responsibilities
| Firmware Agent | PCT Role |
|----------------|---------|
| BIOS | Capability check (CAPID4.bit29); knob exposure; TPMI/MSR programming order |
| PCode (CBB) | Dereferences SST_CLOS_CONFIG; applies HP/LP TRL to cores |
| PrimeCode (NIO/IMH) | Sends HPM RAPL_PERF_LIMIT messages with PCT-adjusted limits |
| Acode (core uCode) | Applies derating ratio to HP vs LP cores at execution level |

### Implication for This TC (FV — TPMI Register Check)
This TC is **directly in the silicon-heavy domain**: it validates that the hardware TPMI
registers (SST_CLOS_CONFIG, SST_CP_CONTROL, SST_PP_CONTROL) contain the correct values
after BIOS/PCode programming. A failure here most likely indicates:
1. **Silicon bug** — hardware ignores or misroutes the TPMI write
2. **PCode bug** — firmware writes wrong value to register
3. **BIOS bug** — BIOS programs wrong partition count or CLOS assignment

This TC is the **FV ground truth** — if it passes, silicon implements PCT registers correctly.
PSS (pre-silicon) catches firmware/model bugs; PV catches driver/tool stack bugs.

### Risk Prioritization
| Risk Owner | Risk | Likelihood |
|-----------|------|-----------|
| Silicon | TPMI CLOS config write silently ignored | Low |
| PCode | Wrong CLOS priority type written (ordered vs proportional) | Medium |
| BIOS | HP core count off-by-one for NWP 2-CBB topology | Medium |
| PCode | SST_CP_CONTROL not updated after BIOS knob change | Low |

---

## Appendix: PCT Validation — Three-Tier Architecture Reference

> This appendix is referenced by all PCT cache files. It captures the authoritative
> justification for why FV, PSS, and PV coverage is complementary, not duplicate.

### Validation Architecture

```
PRE-SILICON                    POST-SILICON
─────────────────────          ────────────────────────────────────────
PSS (Model Validation)         FV (Hardware Truth)    PV (System Behavior)
  VP (Simics)                    Silicon                Silicon
  HSLE (CBB or IMH RTL)          PythonSV→TPMI          sst→driver→sysfs→TPMI
  HSLE XOS (IMH+CBB RTL)
```

### PSS Sub-Environment RTL Fidelity

| PSS Env | RTL Fidelity | What it validates | Cannot validate |
|---------|-------------|-------------------|----------------|
| VP (Simics) | Simulated core — Acode/core RTL **not** exact | Firmware flows: PCode/PrimeCode TPMI writes, HPM messages, PCode state machine | Core µarch response, exact Acode execution, real power/frequency |
| HSLE | Full RTL — one die at a time | HW signal flows within one die; TPMI register behavior at gate level | Cross-die IMH↔CBB HPM protocol; full-system power flows |
| HSLE XOS | Full RTL — **both IMH and CBB** | End-to-end HW flows: HPM passing IMH↔CBB, TPMI→core response, PCode+PrimeCode co-execution | OS stack (no Linux), real power/voltage |

### Bug Coverage Matrix

| Bug Category | VP | HSLE | HSLE XOS | FV | PV |
|-------------|:--:|:----:|:--------:|:--:|:--:|
| PCode TPMI write logic | ✅ | ⚠️ | ✅ | ✅ | ✅ indirect |
| PrimeCode HPM message to CBB | ✅ | ❌ | ✅ | ✅ | ✅ indirect |
| CBB PCode misreads CLOS config | ❌ | ✅ | ✅ | ✅ | ✅ indirect |
| Acode applies wrong ratio to HP cores | ❌ | ✅ | ✅ | ✅ | ✅ indirect |
| IMH↔CBB HPM protocol bug | ❌ | ❌ | ✅ | ✅ | ✅ indirect |
| Silicon TPMI decoder HW bug | ❌ | ❌ | ❌ | ✅ | ✅ indirect |
| Real fuse gating PCT wrong | ❌ | ❌ | ❌ | ✅ | ✅ indirect |
| `intel-speed-select` driver bug | ❌ | ❌ | ❌ | ❌ | ✅ |
| `sst` tool misparse capability | ❌ | ❌ | ❌ | ❌ | ✅ |
| NWP 2-CBB topology in driver | ❌ | ❌ | ❌ | ❌ | ✅ |
| TDP convergence (real power) | ❌ | ❌ | ❌ | ✅ | ✅ |
| BIOS negative knob validation | ✅ safe | ❌ | ❌ | ❌ risky | ❌ |

### Why PSS ≠ FV (Time axis, not content axis)

```
Firmware bug in PCode TPMI write:
  PSS → FAIL ✅  (catches it 6+ months before silicon)
  FV  → FAIL ✅  (confirms on real silicon)

Silicon TPMI decoder hardware bug:
  PSS → PASS ❌  (RTL model may not have same layout bug)
  FV  → FAIL ✅  (ground truth — only FV catches it)

Model gap (missing TPMI field in VP):
  PSS → PASS ❌  (model doesn't implement that field)
  FV  → ground truth behavior ✅
```

PSS = **early detection**; FV = **ground truth**. Neither replaces the other.

### Why PSS ≠ PV (Interface axis)

PSS environments (VP/HSLE/XOS) run minimal boot — **no Linux OS, no `intel-speed-select` driver, no sysfs, no `sst` tool**. PV cannot run pre-silicon. Zero content overlap.

### Scenario Ownership Summary

| Scenario | PSS | FV | PV | Notes |
|----------|:---:|:--:|:--:|-------|
| Discovery / TPMI Check | ✅ | ✅ | ✅ | All required — different layers |
| Default HP Core / Config | ✅ | ✅ | ✅ | 3-layer validation |
| Enable / Disable | ✅ | ✅ | ✅ | Same feature, different layer |
| C6 Interaction | ✅ | ✅ | ❌ | HW-level; no OS needed |
| Partition Sweep | ❌ | ❌ | ✅ | Requires full driver stack |
| TDP Convergence | ❌ | ✅ | ✅ | Needs real silicon power |
| BIOS Negative Validation | ✅ | ❌ risky | ❌ | Safe only in emulation |

### Final Verdict

> **✅ Keep ALL tiers. Reject NO PCT TCs as duplicates.**
> PCT validation = 3-layer system: PSS (early) → FV (hardware truth) → PV (system behavior)
> These layers are complementary, not redundant.
>
> Feature classification: **Silicon-heavy** (CAPID4 fuse, HW TRL enforcement, Acode derating)
> with **moderate firmware orchestration** (BIOS knobs, PCode CLOS programming, PrimeCode HPM).
