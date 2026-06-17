# Deep Analysis: Verify Capability to Change RAPL Limits to Custom-Defined Ones

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421989 |
| **Title** | Verify capability to change rapl limits to custom-defined ones |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | RAPL limit programmability — decrease and increase PL1/PL2 from default |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that **RAPL limits (PL1, PL2) can be set to custom values** by software:
- Decrease PL1/PL2 from programmed value to less than TDP/1.2×TDP
- Increase PL1/PL2 beyond default values
- Verify RAPL enforces each custom-programmed limit correctly

This is a fundamental RAPL programmability test. Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Conditions to Test (NWP)

| Condition | NWP PL1/PL2 Value | Expected Behavior |
|-----------|-------------------|-------------------|
| Decrease PL1 | < TDP | Power throttled to new limit |
| Decrease PL2 | < 1.2×TDP | Burst power capped at new limit |
| Increase PL1 | Up to TDP | Default if platform enforces max |
| Increase PL2 | Up to 1.2×TDP | Burst allowed up to new limit |
| PL1 = 0 | 0W | Minimum power state |
| PL1 > TDP | > TDP (if allowed) | Platform max may clamp |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run cpu_rapl PMx | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| 2 | Read NWP default PL1/PL2 | MSR 0x610 PL1 field; MSR 0x610 PL2 field |
| 3 | Set PL1 to TDP/2 (50% of TDP) | Custom decrease; verify enforced |
| 4 | Set PL2 to 0.6×TDP (50% of default PL2) | Custom decrease; verify enforced |
| 5 | Restore to defaults | Verify system recovers to default limits |
| 6 | Set PL1 to 0.9×TDP, 0.7×TDP, 0.5×TDP | Sweep decreasing values; verify each |
| 7 | Verify platform max limits respected | NWP may have max PL1 cap from fuse |

### PMx Command
```
python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3
```

### Pass Criteria
- RAPL power consumption converges to each custom PL1/PL2 setting
- Decreases: power drops to new limit
- Increases: power allowed up to new limit
- Platform max cap honored if applicable on NWP

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; test custom PL1/PL2 on NWP; note NWP TDP and max cap from fuses**

1. `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3`
2. Read NWP TDP from `sv.socket0.imh0.fuses.punit.*`; use as baseline
3. Test decrease and increase scenarios; verify each custom limit enforced

**Priority**: Medium — `plc.feature.p2`; fundamental RAPL programmability validation — core to NWP power management correctness
