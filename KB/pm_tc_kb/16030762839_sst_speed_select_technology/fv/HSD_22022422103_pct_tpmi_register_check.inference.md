# Deep Analysis: PCT - TPMI Register Check

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422103 |
| **Title** | PCT - TPMI register check |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SST |
| **Sub-Feature** | PCT (Performance Core Tuning) — SST-TF-based HP/LP core frequency segmentation |
| **Feature Classification** | **Silicon-heavy** (CAPID4.bit29 fuse-gated; HW enforces HP/LP TRL) with firmware orchestration (PCode/BIOS/PrimeCode/Acode) |
| **NWP Disposition** | **Runnable_On_N-1** |

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
