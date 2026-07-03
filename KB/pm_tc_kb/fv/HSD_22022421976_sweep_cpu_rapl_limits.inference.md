# Deep Analysis: Sweep CPU RAPL Limits

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421976 |
| **Title** | Sweep CPU RAPL limits |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | PL1/PL2 sweep from 0 to TDP under PTU TDP workload |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test **sweeps RAPL limits (PL1 and PL2) up and down** across the full range from 0 to TDP (and potentially above TDP) while running PTU TDP workload:
- Tests increasing and decreasing limit transitions
- Verifies RAPL correctly enforces each limit point across the sweep range
- Also tests limits below Pn (minimum operating frequency) for edge case behavior

On NWP: same RAPL sweep methodology. TDP from NWP fuses (`imh0.fuses.punit.*`). Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run cpu_rapl PMx | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| 2 | Read NWP TDP fuse | `sv.socket0.imh0.fuses.punit.<tdp_fuse>` |
| 3 | Start PTU TDP workload | `./ptu -ct 3` across all 96 cores |
| 4 | Sweep PL1: 0 → TDP in steps | For each PL1 value: set MSR, measure energy status, verify convergence |
| 5 | Sweep PL1: TDP → 0 in steps | Verify decreasing sweep also enforced correctly |
| 6 | Sweep PL2 similarly | Across range from 0 to 1.2×TDP |
| 7 | Test edge: PL1/PL2 at 0W | Verify behavior at extreme low (likely throttles to Pn) |

### NWP RAPL Range

| Parameter | Expected |
|-----------|---------|
| PL1 range | [0, TDP] W |
| PL2 range | [0, 1.2×TDP] W (typical) |
| TDP source | NWP fuse `sv.socket0.imh0.fuses.punit.*` |
| Sweep granularity | Recommend 5W steps or 10% TDP |

```python
# NWP RAPL sweep (example)
import pm.pmutils.cpu_rapl as rapl
tdp = <read from fuse>
for pl1_w in range(0, tdp+1, tdp//10):  # 10% steps
    rapl.set_pl1(pl1_w)
    # verify energy status tracks limit
```

### NWP Key Notes
- 2 CBBs × 48 cores = 96 cores under PTU workload
- `runPmx.py -x nwp.xml` (not `dmr.xml`)
- At PL1=0: may see minimum voltage/frequency operation or perf limit reason set

### Pass Criteria
- For each PL1/PL2 setting in sweep: consumed power converges to set limit
- Increasing sweep: limits enforced as power limit is raised
- Decreasing sweep: power drops to match lower limit
- No system hang or unexpected MCA during sweep

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; 2 CBBs under PTU; TDP from NWP fuse**

1. `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3`
2. Read NWP TDP from `sv.socket0.imh0.fuses.punit.*`
3. Sweep PL1/PL2 from 0→TDP and TDP→0 in steps; verify each limit point

**Priority**: Medium — `plc.feature.p2`; RAPL limit sweep validates the full range of power management enforcement accuracy
