# Deep Analysis: Socket RAPL x Core Traffic x IO Traffic

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421998 |
| **Title** | Socket Rapl x Core Traffic x IO Traffic |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | RAPL cross-product with simultaneous CPU + IO traffic |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **Socket RAPL under combined CPU and IO traffic**. Reference PMx command from SPR: `runPmx.py -x spr.xml -p cpu_rapl -p cpu_traffic -p core_power`. NWP adapts to use `nwp.xml`. Tags: `DMR_PO`, `plc.feature.p2`, `pm.xproducts.traffic`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted PMx Command
```
python runPmx.py -x nwp.xml -p cpu_rapl -p cpu_traffic -p core_power -tM 6 -M 3
```

Add IO traffic plugin if available for NWP:
```
python runPmx.py -x nwp.xml -p cpu_rapl -p cpu_traffic -p io_traffic -p core_power -tM 6 -M 3
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Start combined CPU + IO traffic | `cpu_traffic` plugin + IO traffic on 96 cores (2 CBBs) |
| 2 | Apply RAPL PL1/PL2 limits | Via MSR 0x610 or TPMI `socket_rapl_pl1_control` |
| 3 | Verify RAPL enforced under traffic | Energy status converges to limits |
| 4 | Check perf limit reasons | Power bit set when throttling due to RAPL under traffic |
| 5 | Verify IO traffic doesn't break RAPL accounting | Energy status still accurate with IO traffic |

### NWP Notes
- 2 CBBs × 48 cores under CPU traffic; IO traffic from NWP IO die
- Single `imh0` aggregates power for RAPL
- `runPmx.py -x nwp.xml` (not `dmr.xml` or `spr.xml`)

### Pass Criteria
- RAPL enforced correctly under combined CPU + IO traffic
- Energy status accurate
- Perf limit reasons updated when throttled

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; add IO traffic plugin; verify 2 CBBs under combined load**

`python runPmx.py -x nwp.xml -p cpu_rapl -p cpu_traffic -p core_power -tM 6 -M 3`

**Priority**: Medium — `plc.feature.p2`; RAPL accuracy under mixed traffic validates real server workload RAPL behavior
