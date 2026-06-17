# Deep Analysis: [CBB DTS & Telemetry] Verify CBO Cluster DTS Functionality

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421458 |
| **Title** | [CBB DTS & Telemetry] Verify CBO Cluster DTS Functionality |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | DTS — CBO Cluster die thermal sensor (2 DTS instances per CBO PMA) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **CBO Cluster DTS** functionality. From the test steps:
- CBO Cluster DTS: **2 DTS instances**, 1 per CBO PMA
- **12 diodes** total (6 diodes per DTS)
- Thermal Telemetry Managed by: **SA Thermal Puller (Punit)**
- Reporting Method: **min, max**

Flow:
1. Read DTS temperature in CBO Clusters
2. Read temperature in PUNIT telemetry
3. Compare — values should match
4. Increase/Decrease temperature and repeat

Tags: `New_content`, `DMR_PO`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`

NWP has CBO clusters per CBB (2 CBBs, each with CBO PMAs). Adapt register paths accordingly.

---

## Section B: NWP-Specific Test Procedure

### CBO Cluster DTS Architecture (NWP)

| Parameter | DMR | NWP |
|-----------|-----|-----|
| CBBs | 4 | 2 |
| DTS instances | 2 per CBO PMA | 2 per CBO PMA |
| Diodes per DTS | 6 | 6 |
| Telemetry manager | SA Thermal Puller (Punit) | SA Thermal Puller (imh0 Punit) |
| Reporting | min, max | min, max |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Read CBO Cluster DTS (min/max per PMA) | `sv.socket0.cbb[0-1].base.cbo.<cluster>.<dts_reg>.temperature` |
| 2 | Read PUNIT telemetry for CBO Cluster | `sv.socket0.imh0.punit.<cbo_telem_reg>.read()` |
| 3 | Compare min and max DTS readings vs telemetry | Both should match within tolerance |
| 4 | Change die temperature (stress workload or cooling) | Verify DTS and telemetry track together |
| 5 | Repeat for each CBO PMA on cbb0 and cbb1 | Full coverage |

### PMx Command
```
python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2
```

### NWP: 2 CBBs
- NWP has 2 CBBs (not 4 as in DMR)
- Each CBB has CBO PMAs with 2 DTS instances
- Loop: `for cbb_idx in range(2):`

### Pass Criteria
- CBO Cluster DTS min/max readings match PUNIT telemetry
- Telemetry updates as temperature changes (tracks DTS)
- All CBO PMAs on both cbb0 and cbb1 report correctly

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; 2 CBBs; verify all CBO PMAs on both dies**

1. `python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2`
2. NWP: 2 CBBs (not 4) — iterate over cbb0 and cbb1
3. Verify both min and max DTS reporting from each CBO PMA
4. SA Thermal Puller (imh0 Punit) aggregates from both CBBs

**Priority**: Medium — `plc.feature.p1`; CBO cluster DTS is key thermal monitoring for cache thermal management
