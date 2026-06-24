# Deep Analysis: PCT - TPMI Runtime Enable/Disable

| Field | Value |
|-------|-------|
| **HSD ID** | [16030768620](https://hsdes.intel.com/appstore/article-one/#/16030768620) |
| **Title** | PCT - TPMI runtime enable/disable |
| **Date** | 2026-06-24 |
| **Target Program** | NWP (Newport) |
| **Segment** | FV |
| **Feature** | SST |
| **Sub-Feature** | PCT — SST-TF runtime enable/disable via TPMI SST_PP_CONTROL |
| **Parent TCD** | [22022420858 — PCT - Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420858) |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Val Environment** | silicon, virtual_platform |
| **Owner** | mps |

## Test Case Intent

Verify that PCT can be dynamically enabled and disabled at runtime via TPMI write to `SST_PP_CONTROL.feature_state[bit 1]`, and that the system correctly reflects the enable/disable state in TPMI status registers. This validates the **TPMI runtime control path** for PCT.

**Distinction from other PCT TCs**:

> TC 22022422103 (TPMI register check): validates boot-time register state

> TC 16030768619 (PCT Default Enabled): validates auto-enablement at boot

> **This TC**: validates **runtime toggle** of PCT via TPMI write

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP silicon or emulation with SST-TF/PCT capable |
| PCT at boot | PCT enabled at boot (TPMI SST_PP_CONTROL.feature_state[1] = 1) |
| FW stack | PCode, PrimeCode, PythonSV installed |
| NWP CBBs | Both CBBs (cbb0, cbb1) accessible |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Confirm PCT enabled at boot: read `SST_PP_CONTROL.feature_state[1]` per CBB | = 1 on both CBBs | = 0 or inaccessible |
| 2 | Record baseline: `SST_CP_CONTROL.sst_cp_enable`, `SST_CLOS_ASSOC`, `SST_CLOS_CONFIG` per CBB | Baseline captured | Read failure |
| 3 | Disable PCT: write `SST_PP_CONTROL.feature_state[bit 1] = 0` on both CBBs | Write accepted; no hang/MCA | Write failure or instability |
| 4 | Verify disabled: read `SST_PP_CONTROL.feature_state[1]` per CBB | = 0 on both CBBs | Still = 1 |
| 5 | Verify `SST_CP_CONTROL.sst_cp_enable = 0` after disable | PCT globally disabled | = 1 or mismatched |
| 6 | Re-enable PCT: write `SST_PP_CONTROL.feature_state[bit 1] = 1` on both CBBs | Write accepted | Write failure |
| 7 | Verify re-enabled: read `SST_PP_CONTROL.feature_state[1]` per CBB | = 1 on both CBBs | = 0 |
| 8 | Verify CLOS config restored: `SST_CLOS_ASSOC`, `SST_CLOS_CONFIG` match baseline | Consistent with pre-disable snapshot | Configuration drift |

### Pass / Fail Criteria

**PASS**: PCT dynamically toggles via TPMI write; `SST_PP_CONTROL.feature_state` reflects state; CLOS config consistent; no hang/MCA; re-enable restores expected state.

**FAIL**: TPMI write failure; `feature_state` doesn't reflect write; hang/MCA; CLOS corrupted after re-enable.

---

## Section A: NWP Delta

| Aspect | DMR | NWP | Notes |
|--------|-----|-----|-------|
| `SST_PP_CONTROL` path | `sv.socket0.imhX.base.tpmi.sst_pp_control` | `sv.socket0.cbbX.base.tpmi.sst_pp_control` | CBB path on NWP |
| CBB count | 4 | 2 (cbb0, cbb1) | Iterate both |
| PCT runtime toggle | Functional | Functional | Same mechanism |

### NWP Register Paths

| Register | NWP Namednodes Path |
|----------|---------------------|
| `SST_PP_CONTROL.feature_state` | `sv.socket0.cbb{X}.base.tpmi.sst_pp_control.feature_state` |
| `SST_CP_CONTROL.sst_cp_enable` | `sv.socket0.cbb{X}.base.tpmi.sst_cp_control.sst_cp_enable` |

### PythonSV Sketch

```python
# PCT TPMI runtime enable/disable (NWP) -- 2 CBBs
for cbb_idx in range(2):
    cbb = sv.socket0.getbypath(f"cbb{cbb_idx}")
    state = cbb.base.tpmi.sst_pp_control.feature_state.read()
    print(f"CBB{cbb_idx} feature_state = {hex(state)}")

    # Disable: clear bit 1
    cbb.base.tpmi.sst_pp_control.feature_state.write(state & 0xFD)
    assert (cbb.base.tpmi.sst_pp_control.feature_state.read() & 0x2) == 0

    # Re-enable: set bit 1
    cbb.base.tpmi.sst_pp_control.feature_state.write(state | 0x2)
    assert (cbb.base.tpmi.sst_pp_control.feature_state.read() & 0x2) != 0
    print(f"CBB{cbb_idx}: disable/re-enable PASS")
```

---

## Section F: Recommendations

**Runnable_On_N-1.** Same TPMI mechanism as DMR. Key adaptation: iterate both CBBs; use CBB TPMI path.

---

## Section G: PSS Grading

| Sl No | Dimension | Value | Rationale |
|-------|-----------|-------|-----------|
| 1 | NWP Delta | Yes (minor) | CBB path; 2 CBBs |
| 2 | Applicable NWP | Yes | PCT runtime toggle functional |
| 3 | PSS Environment | VP | TPMI toggle; VP feasible |
| 4 | Silicon Only | No | VP feasible |
| 5 | Test Content | DMR_L | Low adaptation |
| 6 | OS | sv-os | PythonSV |

### References

- [PCT KB — pct.md](../../../pm_features/sst/pct.md)
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html)
