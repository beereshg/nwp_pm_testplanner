# Deep Analysis: [Prochot Flow] Verify Prochot IMH Entry and Exit Flow

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421553 |
| **Title** | [Prochot Flow] Verify Prochot IMH Entry and Exit Flow |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | PROCHOT entry/exit for IMH — UFS ratio control and PROCHOT throttle |
| **NWP Disposition** | **Runnable_On_N-1** |

---


## Test Case Intent

Validates the IMH PROCHOT entry and exit flow with fabric freq clamp/recovery scenario defined in [TCD 22022420609 -- Prochot Flow](https://hsdes.intel.com/appstore/article-one/#/22022420609) S5. Environment: NWP post-silicon, FV.

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **PROCHOT flow through IMH**:
1. Use IMH `ufs_control.min_ratio` to set ratio above Pm (≥ 800 MHz)
2. Verify via `ufs_status.current_ratio`
3. Inject PROCHOT
4. Verify IMH ratio drops
5. Remove PROCHOT and verify recovery

On NWP (single iMH — `imh0`): same flow with NWP register paths. DMR Simics paths adapt to NWP silicon PythonSV.

**Key Justification:**
- `Ready_for_testing` + `plc.feature.p1` + `PMSS_NWP_READINESS_CHECK` tags
- IMH PROCHOT flow directly applicable on NWP (single iMH)

---

## Section B: NWP-Specific Test Procedure

### NWP IMH Register Paths

| Register | NWP Path |
|----------|----------|
| `ufs_control.min_ratio` | `sv.socket0.imh0.punit.ufs_control.min_ratio` |
| `ufs_status.current_ratio` | `sv.socket0.imh0.punit.ufs_status.current_ratio` |
| PROCHOT inject | `sv.socket0.imh0.punit.prochot_trigger` |

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Set IMH min_ratio above Pm | `sv.socket0.imh0.punit.ufs_control.min_ratio.write(N)` where N > Pm ratio |
| 2 | Run prochot_thermal PMx | `python runPmx.py -x nwp.xml -p prochot_thermal -tM 20 -M 5` |
| 3 | Verify ufs_status.current_ratio > Pm (≥ 800 MHz ratio) | Pre-PROCHOT state |
| 4 | Inject PROCHOT | `sv.socket0.imh0.punit.prochot_trigger.write(1)` |
| 5 | Verify IMH ratio drops (ufs_status.current_ratio = Pm) | PROCHOT active |
| 6 | Release PROCHOT; verify ratio recovery | `prochot_trigger.write(0)` → ratio recovers |

### NWP Single iMH Note
DMR has imh0 (root primary) and optionally imh1. NWP has single `imh0` only. No secondary iMH PROCHOT path needed.

### NWP Pass Criteria
- IMH current_ratio above Pm before PROCHOT
- IMH current_ratio drops to Pm on PROCHOT injection
- IMH current_ratio recovers on PROCHOT release
- No iMH stability issues during PROCHOT flow

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; IMH PROCHOT flow same; NWP single iMH**

1. `python runPmx.py -x nwp.xml -p prochot_thermal -tM 20 -M 5`
2. NWP: `sv.socket0.imh0.*` (no imh1)
3. Adapt OakStream Simics PROCHOT inject to NWP silicon PythonSV register path

**Priority**: Medium — `plc.feature.p1`; IMH PROCHOT throttle entry/exit verification
