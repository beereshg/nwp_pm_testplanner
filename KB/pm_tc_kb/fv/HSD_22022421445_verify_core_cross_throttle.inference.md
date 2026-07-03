# Deep Analysis: [ACP] Verify Core Cross Throttle

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421445 |
| **Title** | [ACP] Verify Core Cross Throttle |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management > ACP (Autonomous Core Perimeter) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test case verifies that Pcode Core EMTTM triggers a Cross-Core Throttle Request when a core module overheats due to adjacent IP thermal load (also called `CROSS_CORE_THROTTLE_REQUEST`). When a hot core exceeds its self-throttle minimum ratio and is still overtemperature, it writes a virtual signal to Pcode, which applies a physically-aware frequency demotion to neighboring CCPs. On NWP, this ACP cross-core throttle mechanism is supported; the test requires script adaption from `dmr.xml` to `nwp.xml` and CBB loop changes (4→2 CBBs, 32→48 cores). The `DMR_PO` sub-feature tag indicates this was run at PO on DMR silicon — NWP silicon availability is required.

**Key Justification:**
- Core cross-throttle (`PMSB_PCU_CR_VIRTUAL_SIG[CROSS_CORE_THROTTLE_REQ]` bit 13) mechanism exists on NWP
- `runPmx.py -p emttm_thermal` is the test driver; adapting `-x dmr.xml` → `-x nwp.xml` is sufficient for topology config
- NWP CBB count is 2 (not 4) and has 48 cores per CBB — loop bounds in verification must change
- Silicon availability is required (DMR_PO tag confirms silicon-level test, not VP)

---

## Section B: NWP-Specific Test Procedure

### Pre-Conditions
- NWP silicon platform (not VP — cross-throttle is a live thermal event)
- `runPmx.py` with NWP-compatible `nwp.xml` config available
- PythonSv access to `sv.socket0.cbb{0,1}` PMSB registers

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Load EMTTM test module | Same — `import pm.Active_PM.Thermal_Management.CPU_Thermal_Management.EMTTM_pmx as emttm` |
| 2 | Run `emttm_test = emttm.EMTTM(); emttm_test.loopSetup()` | Same |
| 3 | Execute `emttm_test.mainTest()` | Change `-x dmr.xml` to `-x nwp.xml` in underlying command |
| 4 | Trigger thermal excursion on one core module | Same — use thermal stress workload |
| 5 | Verify `PMSB_PCU_CR_VIRTUAL_SIG[CROSS_CORE_THROTTLE_REQ]` (bit 13) set | Loop over `range(2)` CBBs (not 4) |
| 6 | Verify Pcode demotes neighboring CCPs' frequency ratios | Same acceptance — verify GPSS core ratio limits drop for neighbor CCPs |
| 7 | Verify recovery when thermal condition clears | Same acceptance criterion |

### Alternative via CLI
```bash
python runPmx.py -x nwp.xml -p emttm_thermal -tM 30 -M 6
```

### NWP Pass Criteria
- `CROSS_CORE_THROTTLE_REQUEST` asserts when self-throttle exhausted and core still overtemperature
- Neighboring CCP frequency demoted by physically-aware amount (larger demotion for near neighbors)
- Demotion clears after thermal condition resolves

---

## Section C: NWP Delta Impact Analysis

### Topology Changes

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBB count | 4 | 2 | Monitoring loop: `range(2)` |
| Cores per CBB | 32 | 48 | Inner verification scope: `range(48)` |
| Script XML | `dmr.xml` | `nwp.xml` | Direct config substitution |
| Physical neighbor mapping | DMR tile adjacency | NWP tile adjacency | Neighbor lookup table in test may need NWP layout |

### SST-PP / Ring C6 Note

| Feature | DMR | NWP | Impact |
|---------|-----|-----|--------|
| SST-PP eff_tj_max paths | Active | ZBB — not used | Cross-throttle trigger temp uses base TjMax only |
| Ring C6 | Active | ZBB | No impact — ring C-states ≠ ring thermal throttle |

---

## Section D: Key Registers & Validation Points

### Register Check Table (NWP)

| Category | Register | Field | Expected | Verify On |
|----------|----------|-------|----------|-----------|
| Cross-throttle signal | `PMSB_PCU_CR_VIRTUAL_SIG` | `CROSS_CORE_THROTTLE_REQ[13]` | 1 when hot core at min ratio | Per-CCP, both CBBs |
| Perf limit | `PERF_LIMIT_REASONS` | `THERMAL[4]` | 1 during throttle | Package TPMI |
| Core ratio limit | GPSS core ratio ceiling | — | Reduced for neighbor CCPs | Per-core |

### PythonSv Validation Commands (NWP)

```python
# Check CROSS_CORE_THROTTLE_REQUEST status across both CBBs
for cbb_idx in range(2):  # NWP has 2 CBBs
    cbb = sv.socket0.getbypath(f"cbb{cbb_idx}")
    for core_idx in range(48):  # NWP has 48 cores per CBB
        try:
            virt_sig = cbb.getbypath(
                f"compute{core_idx // 8}.module{core_idx % 8}.pmsb_pcu_cr_virtual_sig"
            ).cross_core_throttle_req.read()
            if virt_sig:
                print(f"CBB{cbb_idx} core{core_idx}: CROSS_CORE_THROTTLE_REQUEST asserted")
        except Exception:
            pass

# Package-level PLR check
plr = sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.perf_limit_reasons.read()
print(f"PLR value: 0x{plr:08X}")
```

---

## Section E: Risk Assessment & Open Items

| # | Risk/Open Item | Severity | Notes |
|---|----------------|----------|-------|
| 1 | **Silicon-only test** — cross-throttle requires real thermal events; VP simulation of thermal trips may not trigger the condition accurately | Medium | Mark VP environment as `Not Applicable`; run only on silicon |
| 2 | **NWP tile adjacency mapping** — the physically-aware cross-throttle demotion uses die floorplan; NWP neighbor map may differ from DMR | Medium | Validate with NWP PM HAS; test may need updated neighbor table |
| 3 | **PMSB path naming** — register path `PMSB_PCU_CR_VIRTUAL_SIG` needs NWP namednodes verification | Low | Validate during bring-up |

---

## Section F: Recommendation

**Recommendation: ADAPT — script config + topology loop adaptation required**

The cross-core throttle mechanism is architecturally identical on NWP. The primary changes are: (1) update test script XML from `dmr.xml` to `nwp.xml`, (2) update CBB/core loop bounds (4×32 → 2×48), and (3) verify the NWP tile adjacency table used for physically-aware demotion. This is a silicon-only test that cannot be run on VP.

Required adaptations:
1. Change `runPmx.py -x dmr.xml` → `runPmx.py -x nwp.xml`
2. Update verification loops: `range(2)` CBBs, `range(48)` cores
3. Confirm NWP PMSB VIRTUAL_SIG register path is accessible via namednodes
4. Review NWP physical neighbor adjacency for cross-throttle demotion amount

**Priority**: High — Core cross-throttle is a safety mechanism validated at PO
