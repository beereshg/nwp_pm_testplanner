# Deep Analysis: Throttling Below Pm

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421978 |
| **Title** | Throttling below Pm |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | RAPL throttling below Pm (minimum operating frequency) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **RAPL throttling below Pm** (the minimum supported operating frequency). From Wave 3 Common HAS: when RAPL power limit forces the operating point below Pm, the hardware behavior (clock gating, voltage reduction, or halt) must match the specification.

Test steps reference GNR TC (16014287020) using `pm.pmutils.cpu_rapl` functions:
1. Import `cpu_rapl` from pmutils
2. Set RAPL limit below minimum (low enough to force below-Pm operation)
3. Verify behavior matches spec (throttle action below Pm)

Tags: `DMR_PO`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`

---

## Section B: NWP-Specific Test Procedure

### NWP Pm (Minimum Ratio)

| Parameter | NWP Path |
|-----------|----------|
| Pm ratio | `sv.socket0.imh0.fuses.punit.<pm_ratio_fuse>` or MSR `IA32_PLATFORM_INFO` [55:48] |
| Pm frequency | Pm ratio × 100 MHz |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Import cpu_rapl and read Pm | `import pm.pmutils.cpu_rapl as rapl; pm = rapl.get_pm_ratio()` |
| 2 | Start workload | Ensure system is active (RAPL active) |
| 3 | Set PL1 limit low enough to force below Pm | Very low power budget (below idle×2) |
| 4 | Verify throttle behavior at or below Pm | Core clock gating or halt; check `perf_limit_reasons.power` |
| 5 | Verify system stability during below-Pm throttle | No hang, no MCA |
| 6 | Restore PL1 to TDP; verify recovery | System returns to normal operation |

### PMx Command
```
python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3
```

### NWP Notes
- NWP Pm is the minimum guaranteed frequency; below-Pm behavior defined in HAS Wave 3 Common
- 2 CBBs × 48 cores; below-Pm throttle applies to all cores globally
- `runPmx.py -x nwp.xml` (not `dmr.xml`)
- Wave 3 Common HAS: https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html#throttling-below-pm-spr-onwards

### Pass Criteria
- When RAPL forces operation below Pm: defined throttle behavior (per HAS spec)
- `perf_limit_reasons.power` bit set during RAPL throttle
- System stable (no hang or MCA) during below-Pm RAPL throttle
- Recovery to normal frequency when PL1 restored

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; read NWP Pm from fuse/MSR; below-Pm behavior per Wave 3 HAS**

1. `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3`
2. Read NWP Pm from `IA32_PLATFORM_INFO` [55:48] or fuse
3. Set PL1 to force below-Pm; verify throttle behavior and system stability
4. Reference: Wave 3 Common HAS §throttling-below-pm-spr-onwards

**Priority**: Medium — `plc.feature.p2`; below-Pm RAPL throttle validates an extreme boundary condition of the power management control loop
