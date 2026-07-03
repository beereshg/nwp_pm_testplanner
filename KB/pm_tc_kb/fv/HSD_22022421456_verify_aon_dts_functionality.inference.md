# Deep Analysis: [CBB DTS & Telemetry] Verify AON DTS Functionality

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421456 |
| **Title** | [CBB DTS & Telemetry] Verify AON DTS Functionality |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | DTS — AON (Always-On) die thermal sensor |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **Always-On (AON) DTS** functionality:
1. Read DTS temperature from AON DTS sensor
2. Read the same temperature from PUNIT telemetry
3. Compare — values should match
4. Stress/change temperature and repeat

The AON DTS is a persistent thermal sensor active even in deep package C-states. NWP has AON DTS on compute dies. Tags: `New_content`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`

---

## Section B: NWP-Specific Test Procedure

### AON DTS Paths (NWP)

| Source | NWP Register Path |
|--------|-------------------|
| AON DTS direct | `sv.socket0.cbb[0-1].<aon_dts_path>.temperature` |
| PUNIT telemetry | `sv.socket0.imh0.punit.pkg_therm_status.*` or per-die telemetry register |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Read AON DTS temperature directly | `sv.socket0.cbb0.<aon_dts_reg>.temperature.read()` |
| 2 | Read PUNIT telemetry for same die | `sv.socket0.imh0.punit.<aon_telem_reg>.read()` |
| 3 | Compare — values should match | Delta within calibration tolerance |
| 4 | Stress die (run workload) to change temperature | Increase thermal activity |
| 5 | Repeat steps 1–3 under load | Verify telemetry tracks DTS in real-time |
| 6 | Repeat for cbb1 AON DTS | Verify both CBB AON sensors |

### PMx Command
```
python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2
```

### NWP: 2 CBBs
- Test AON DTS on cbb0 and cbb1 independently
- Single `imh0` aggregates telemetry from both CBBs
- AON DTS is always-on — accessible regardless of C-state

### Pass Criteria
- AON DTS temperature matches PUNIT telemetry (within tolerance)
- Telemetry tracks DTS changes under load
- Both cbb0 and cbb1 AON sensors functional

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; verify AON DTS on both CBBs; single iMH aggregates telemetry**

1. `python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2`
2. NWP: 2 CBBs — test cbb0 and cbb1 AON DTS independently
3. Compare DTS direct vs PUNIT telemetry for each die
4. Verify telemetry updates correctly under temperature change

**Priority**: Medium — `plc.feature.p1`; AON DTS is baseline thermal telemetry for always-on monitoring
