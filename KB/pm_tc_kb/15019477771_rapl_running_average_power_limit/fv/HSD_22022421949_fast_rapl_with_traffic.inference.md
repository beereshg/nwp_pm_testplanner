# Deep Analysis: Fast RAPL with Traffic

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421949 |
| **Title** | Fast RAPL with traffic |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | Fast RAPL algorithm correctness under CPU traffic (with and without PROCHOT) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **Fast RAPL algorithm under CPU traffic** in two sub-tests:
1. Fast RAPL with traffic, **without** PROCHOT
2. Fast RAPL with traffic, **with** PROCHOT

Fast RAPL is the high-speed RAPL control loop that responds faster than the standard RAPL PID. On NWP: same Fast RAPL mechanism; 2 CBBs × 48 cores = 96 cores under traffic. `plc.feature.p2` priority; `PMSS_NWP_READINESS_CHECK` confirmed.

---

## Section B: NWP-Specific Test Procedure

### Sub-test 1: Fast RAPL + Traffic (no PROCHOT)

```bash
python runPmx.py -x nwp.xml -p base -p fast_rapl -p core_power -p cpu_traffic -tM 6 -M 3
```

### Sub-test 2: Fast RAPL + Traffic + PROCHOT

```bash
python runPmx.py -x nwp.xml -p base -p fast_rapl -p core_power -p cpu_traffic -p prochot -tM 6 -M 3
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run Fast RAPL with CPU traffic (no PROCHOT) | Sub-test 1 command above |
| 2 | Verify Fast RAPL algorithm responds correctly under traffic | Energy status tracks PL1/PL2; fast response |
| 3 | Run Fast RAPL with CPU traffic + PROCHOT | Sub-test 2 command above |
| 4 | Verify Fast RAPL algorithm correct while PROCHOT active | Both PROCHOT and RAPL limits enforced |
| 5 | Check RAPL energy reporting accuracy | Energy status MSRs update at expected rate |

### NWP Key Notes
- NWP: 2 CBBs; traffic (`cpu_traffic` plugin) covers all 96 cores
- `p base` sets baseline RAPL configuration for NWP
- Fast RAPL bit verification: check FAST_RAPL_BIT in RAPL HPM message (see TC 22022421955)
- PROCHOT inject via `sv.socket0.imh0.punit.prochot_trigger` on NWP

### Pass Criteria
- Fast RAPL responds to power transients within fast-loop latency window
- RAPL energy stays within PL1/PL2 limits under CPU traffic
- Both sub-tests (with and without PROCHOT) pass

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; 2 CBBs (96 cores) under traffic; run both PROCHOT variants**

1. Sub-test 1: `python runPmx.py -x nwp.xml -p base -p fast_rapl -p core_power -p cpu_traffic -tM 6 -M 3`
2. Sub-test 2: `python runPmx.py -x nwp.xml -p base -p fast_rapl -p core_power -p cpu_traffic -p prochot -tM 6 -M 3`
3. NWP: single `imh0`; 2 CBBs; 48 cores/CBB

**Priority**: Medium — `plc.feature.p2`; Fast RAPL stability under traffic is critical for NWP server workload RAPL control accuracy
