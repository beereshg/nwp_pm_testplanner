# Deep Analysis: [Prochot Flow] Verify Operation of Prochot Response Power

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421557 |
| **Title** | [Prochot Flow] Verify operation of Prochot Response Power |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | PROCHOT response power — per-domain power ceiling during PROCHOT |
| **NWP Disposition** | **Runnable_On_N-1** |

---


## Test Case Intent

Validates the PROCHOT response power behavior and throttle policy scenario defined in [TCD 22022420609 -- Prochot Flow](https://hsdes.intel.com/appstore/article-one/#/22022420609) S5. Environment: NWP post-silicon, FV.

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test extends the PROCHOT CBB/IMH entry/exit flows (22022421548, 22022421553) by also validating that **PROCHOT Response Power** can be programmed to constrain the power ceiling Pcode selects for each domain during PROCHOT throttle. The revised WW46 2025 flow:
1. Get PF curves for each GV domain
2. Set each domain to the highest ratio in the curve (ensures throttling at any power/cDyn point)
3. Get response power fuses to set response power ceiling
4. Inject PROCHOT and verify each domain is throttled accordingly

On NWP (single iMH, 2 CBBs × 48 cores):
- Same PROCHOT entry/exit mechanism (SVID PROCHOT line or PythonSV inject)
- NWP PF curves use `nwp.xml` targets
- `plc.feature.p1` + `PMSS_NWP_READINESS_CHECK` tags confirm portability

---

## Section B: NWP-Specific Test Procedure

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Read PF curves for each GV domain | `python runPmx.py -x nwp.xml -p prochot_thermal -tM 20 -M 5` |
| 2 | Set each domain to highest ratio | Per-domain; CBBs = 2; iMH = imh0 |
| 3 | Read PROCHOT response power fuses | `sv.socket0.imh0.fuses.punit.*` response power fields |
| 4 | Inject PROCHOT | `sv.socket0.imh0.punit.prochot_trigger.write(1)` |
| 5 | Verify per-domain power ceiling honored | Check telemetry; each domain at or below response power ceiling |
| 6 | Release PROCHOT | `sv.socket0.imh0.punit.prochot_trigger.write(0)` → domains recover |

### NWP Key Differences
- 2 CBBs (not 4): loops `for cbb in range(2):`
- 96 total cores (48/CBB)
- Single iMH (`imh0`)
- `runPmx.py -x nwp.xml` (not `dmr.xml`)

### Pass Criteria
- Each GV domain power-limited to PROCHOT response power ceiling while PROCHOT active
- All domains recover to normal operation after PROCHOT release
- No system hang or unrecoverable error during PROCHOT injection

---

## Section F: Recommendation

**Recommendation: ADOPT — Extend CBB/IMH PROCHOT tests with response power ceiling validation**

1. `python runPmx.py -x nwp.xml -p prochot_thermal -tM 20 -M 5`
2. NWP: 2 CBBs, 48 cores/CBB, single `imh0`
3. PROCHOT inject via `sv.socket0.imh0.punit.prochot_trigger`
4. Response power fuses at `sv.socket0.imh0.fuses.punit.*`

**Priority**: Medium — `plc.feature.p1`; completes PROCHOT flow test coverage
