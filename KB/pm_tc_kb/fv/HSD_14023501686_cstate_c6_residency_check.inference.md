# Deep Analysis: CState C6 Residency Check

| Field | Value |
|-------|-------|
| **HSD ID** | 14023501686 |
| **Title** | CState C6 residency check |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Core C-States |
| **Sub-Feature** | C6 residency check across all C6 flavors (C6A, C6S, C6S-P) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test checks **C6 residency** in all C6 flavors: C6A (Autonomous C6), C6S (C6 with cache flush), C6S-P (C6S Predictive). All are functional on NWP.

Requires NGA default flow working first. Tags: `DMR_PO`, `NGA_MAIN`, `plc.feature.p1`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Ensure NGA default flow working | Flexcon checks pass with `NWPSV.ini` |
| 2 | Run cstates PMx | `python runPmx.py -x nwp.xml -p cstates -H 1 -M 5` |
| 3 | OR standalone | `python /usr/lib/python3/dist-packages/newport/pm/Idle_PM/cstates/ccx_residency_test.py` |
| 4 | Idle system (run with light workload to promote idle) | Allow all 96 cores to enter C6 |
| 5 | Read C6 residency counters for each flavor | Per core; check all 96 cores have C6 residency |

### C6 Residency Counter Paths (NWP)

```python
# NWP C6 residency check (example for cbb0, first module)
# Exact paths depend on NWP PythonSV hierarchy
for cbb in range(2):
    for module in sv.socket0.getbypath(f"cbb{cbb}").computes:
        for core_pma in module.pmas:
            residency = core_pma.pmsb.<c6_residency_counter>.read()
            print(f"cbb{cbb} {module.target_info.name}: C6 residency = {residency}")
```

### Pass Criteria
- C6A residency counter > 0 for all 96 cores during idle
- C6S residency counter > 0 (with cache flush)
- C6S-P residency counter > 0 (predictive)
- No hung cores (zero residency after sufficient idle time indicates issue)

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; standalone script `diamondrapids` → `newport`; verify all 96 cores (2 CBBs × 48) show C6 residency**

**Priority**: High — `NGA_MAIN`, `plc.feature.p1`; C6 residency is the primary idle power efficiency metric for NWP server deployment
