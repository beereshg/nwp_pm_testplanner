# Deep Analysis: Socket RAPL x PROCHOT

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422013 |
| **Title** | Socket rapl x Prochot |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | RAPL cross-product with PROCHOT — simultaneous RAPL + PROCHOT throttle |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **Socket RAPL interaction with PROCHOT** per Wave 3 Common HAS. Both RAPL and PROCHOT can simultaneously throttle the processor; the test verifies the combined behavior. Tags: `plc.feature.p2`, `pm.xproducts.pm`, `PMSS_NWP_READINESS_CHECK`.

On NWP: PROCHOT via `sv.socket0.imh0.punit.prochot_trigger`; RAPL via TPMI `socket_rapl_pl1_control`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run cpu_rapl PMx | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| 2 | Set RAPL PL1 to constrain power | Active RAPL throttle |
| 3 | Inject PROCHOT | `sv.socket0.imh0.punit.prochot_trigger.write(1)` |
| 4 | Verify both RAPL and PROCHOT active simultaneously | `perf_limit_reasons`: both power and PROCHOT bits set |
| 5 | Verify frequency limited by stricter of RAPL vs PROCHOT | Min frequency wins |
| 6 | Release PROCHOT | `prochot_trigger.write(0)` → only RAPL active |
| 7 | Verify RAPL still enforced after PROCHOT release | No RAPL bypass after PROCHOT |

### NWP Key Notes
- PROCHOT inject: `sv.socket0.imh0.punit.prochot_trigger.write(1)`
- RAPL × PROCHOT arbitration: PROCHOT overrides frequency to Pm; RAPL controls power budget
- Both throttle limits can be simultaneously active; Wave 3 HAS defines interaction
- `runPmx.py -x nwp.xml` (not `dmr.xml`)

### Pass Criteria
- PROCHOT + RAPL simultaneously active: perf_limit_reasons shows both reasons
- PROCHOT overrides frequency; RAPL enforces power budget
- After PROCHOT release: RAPL throttle resumes as sole limiter
- No crash or unexpected MCA

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; NWP PROCHOT inject via `imh0.punit.prochot_trigger`**

1. `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3`
2. Inject PROCHOT via `sv.socket0.imh0.punit.prochot_trigger.write(1)`
3. Verify simultaneous RAPL + PROCHOT arbitration per Wave 3 Common HAS

**Priority**: Medium — `plc.feature.p2`; RAPL × PROCHOT interaction validates critical combined throttle path
