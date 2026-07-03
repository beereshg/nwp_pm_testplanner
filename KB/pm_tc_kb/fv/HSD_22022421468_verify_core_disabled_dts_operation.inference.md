# Deep Analysis: [CBB DTS & Telemetry] Verify Core Disabled DTS Operation

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421468 |
| **Title** | [CBB DTS & Telemetry] Verify Core Disabled DTS operation |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | DTS — disabled core DTS isolation (fused-off core temperature excluded from telemetry) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies behavior when a **core DTS is bad or the core is fused off**:
- Configure the specific core & DTS to be disabled
- Verify the disabled core's DTS temperature is **not used** in thermal management
- Assumption: no need for disabled core temperature in any other flow (e.g., thermtrip, perf limit)

In DMR: DCM (Dual Core Module) — disabling one core means both cores in the DCM may be affected (module-level disable). In NWP: single-core modules (no SMT, no DCM pairing). Disabling a core isolates only that core's DTS.

Tags: `DMR_PO`, `NGA_MAIN`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`

---

## Section B: NWP-Specific Test Procedure

### Core Disable DTS Architecture (NWP)

| Aspect | DMR | NWP |
|--------|-----|-----|
| Module | DCM (2 cores) — disabling affects module pair | Single core per module — only that core disabled |
| Fuse disable | Per-DCM fuse | Per-core fuse on NWP |
| DTS isolation | Disabled core DTS excluded from telemetry | Same principle, single-core granularity |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run core_dts_disable PMx | `python runPmx.py -x nwp.xml -p core_dts_disable -tM 60 --retry_count 2` |
| 2 | Identify a core to disable (use fused-off or test override) | Select a non-critical core on cbb0 or cbb1 |
| 3 | Configure core as disabled (fuse/register override) | Set disable bit for target core DTS |
| 4 | Verify disabled core DTS temperature **not included** in PUNIT telemetry | Telemetry should reflect remaining active cores only |
| 5 | Stress active cores | Disabled core DTS should not affect perf limit or thermal decision |
| 6 | Verify system stability with disabled core DTS | No false thermtrip, no perf limit from disabled DTS |
| 7 | Re-enable and verify DTS resumes contribution | Restore; telemetry includes all cores again |

### NWP Adaptation Notes
- NWP: no DCM pairing — disabling 1 core affects only that core (not a paired core)
- `cbb0` and `cbb1` each have 48 cores; test on one core from each CBB
- `runPmx.py -x nwp.xml` (not `dmr.xml`)
- Single `imh0` Punit processes telemetry from both CBBs

### Pass Criteria
- Disabled core DTS temperature excluded from PUNIT telemetry
- No false perf limit, thermtrip, or MCA from disabled DTS
- Re-enabled core DTS resumes proper temperature reporting
- Behavior correct for both cbb0 and cbb1 cores

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; NWP single-core disable (no DCM pairing)**

1. `python runPmx.py -x nwp.xml -p core_dts_disable -tM 60 --retry_count 2`
2. NWP: per-core disable (not per-DCM); test a core on cbb0 and cbb1
3. Verify disabled DTS excluded from telemetry without affecting active core management

**Priority**: Medium — `plc.feature.p1`; important for fused-off core scenarios on NWP silicon
