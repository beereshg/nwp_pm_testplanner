# Deep Analysis: [CBB DTS & Telemetry] Verify Core DTS Functionality

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421465 |
| **Title** | [CBB DTS & Telemetry] Verify Core DTS Functionality |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | DTS — Core (per-core) thermal sensor, Core PMA push telemetry |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **Core DTS** functionality. From test steps:
- Core DTS: **2 DTS per module (1 per Core)**, **8 diodes per core** (including 1 in MLC = 16 total per DMR DCM)
- Thermal Telemetry: **Core PMA (Push)**, reporting min/max per DCM

On NWP:
- NWP is **single-threaded** (no SMT); no DCM (Dual Core Module) — 1 core per context
- NWP: 48 cores/CBB × 2 CBBs = 96 total cores; 1 DTS per core
- Core PMA push telemetry same mechanism; adapted to NWP core cluster organization
- Tags: `DMR_PO`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`

---

## Section B: NWP-Specific Test Procedure

### Core DTS Architecture (NWP)

| Parameter | DMR | NWP |
|-----------|-----|-----|
| Module | DCM (2 cores/module) | Single core (no SMT) |
| DTS per core | 1 (2 per DCM) | 1 per core |
| Diodes per core | 8 (incl. 1 in MLC) | 8 (same expected) |
| CBBs | 4 | 2 |
| Cores/CBB | 32 | 48 |
| Total cores | 128 | 96 |
| Telemetry push | Core PMA → min/max per DCM | Core PMA → min/max per core cluster |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run dts_telemetry PMx | `python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2` |
| 2 | Read Core DTS temperature per core | `sv.socket0.cbb[0-1].compute[0-3].module[0-7].<core_dts_reg>.temperature` |
| 3 | Read PUNIT telemetry for core temperature | `sv.socket0.imh0.punit.<core_telem_reg>` |
| 4 | Compare DTS direct vs PUNIT telemetry | Should match within calibration tolerance |
| 5 | Stress cores (workload) to increase temperature | Verify DTS and telemetry both update |
| 6 | Cool and verify DTS decreases | Telemetry tracks DTS |

### NWP Core Traversal
```python
# NWP core DTS traversal pattern
for cbb_idx in range(2):  # NWP: 2 CBBs
    for compute_idx in range(4):  # 4 compute tiles per CBB
        for module_idx in range(8):  # 8 modules per compute tile
            path = f"cbb{cbb_idx}.compute{compute_idx}.module{module_idx}"
            # Read core DTS temperature
```

### Pass Criteria
- Core DTS temperature matches PUNIT telemetry for each core
- Telemetry updates as core temperature changes
- All 96 cores (48/CBB × 2 CBBs) DTS functional

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; adapt for 96 NWP cores (no DCM); 2 CBBs × 48 cores**

1. `python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2`
2. NWP: no DCM; 1 DTS per core; 48 cores/CBB × 2 CBBs = 96 cores total
3. Core PMA push telemetry; verify min/max reporting per core cluster

**Priority**: High — `plc.feature.p1`; core DTS is the primary thermal monitoring for per-core power management
