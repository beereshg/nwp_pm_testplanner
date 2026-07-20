# Deep Analysis: [Prochot Flow] Verify Prochot CBB Entry and Exit Flow

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421548 |
| **Title** | [Prochot Flow] Verify Prochot CBB Entry and Exit Flow |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | PROCHOT entry/exit for CBB — frequency drops to Pm, restores on removal |
| **NWP Disposition** | **Runnable_On_N-1** |

---


## Test Case Intent

Validates the CBB PROCHOT entry and exit flow with frequency clamp/recovery scenario defined in [TCD 22022420609 -- Prochot Flow](https://hsdes.intel.com/appstore/article-one/#/22022420609) S5. Environment: NWP post-silicon, FV.

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **PROCHOT flow through CBB**:
1. Confirm core frequency NOT at Pm before injection (MSR 0x198 bits [15:8])
2. Inject PROCHOT
3. Verify frequency drops to Pm (800–500 MHz range)
4. Remove PROCHOT
5. Verify frequency recovers

DMR steps reference OakStream Simics path for PROCHOT injection. On NWP silicon, use PythonSV PROCHOT trigger register.

**Key Justification:**
- `Ready_for_testing` + `plc.feature.p1` + `PMSS_NWP_READINESS_CHECK` tags
- PROCHOT CBB entry/exit directly applicable on NWP

---

## Section B: NWP-Specific Test Procedure

### NWP PROCHOT Injection (Adapted from OakStream Simics)

DMR Simics path: `oakstream.mb.mcp0.imh_die0.punit.punit[0]->prochot_trigger`
NWP silicon path: `sv.socket0.imh0.punit.<prochot_trigger register>`

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run prochot_thermal PMx | `python runPmx.py -x nwp.xml -p prochot_thermal -tM 20 -M 5` |
| 2 | Confirm core not at Pm: read MSR 0x198 [15:8] | Expected: ratio > Pm |
| 3 | Inject PROCHOT via NWP PythonSV | `sv.socket0.imh0.punit.prochot_trigger.write(1)` |
| 4 | Read MSR 0x198 [15:8]; verify at Pm (800–500 MHz) | PROCHOT throttle active |
| 5 | Remove PROCHOT: `sv.socket0.imh0.punit.prochot_trigger.write(0)` | Release |
| 6 | Verify frequency recovers above Pm | MSR 0x198 shows normal ratio |

### NWP Pass Criteria
- Pre-PROCHOT: core ratio above Pm
- Post-PROCHOT-inject: core ratio = Pm (Pn/minimum)
- Post-PROCHOT-release: core ratio recovers to pre-PROCHOT level
- Both CBBs respond to PROCHOT (CBB0 and CBB1)

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; PROCHOT CBB flow same; NWP PythonSV inject path**

1. `python runPmx.py -x nwp.xml -p prochot_thermal -tM 20 -M 5`
2. Adapt PROCHOT injection from OakStream Simics to NWP silicon PythonSV register write
3. Verify `sv.socket0.imh0.punit.prochot_trigger` register name on NWP

**Priority**: Medium — `plc.feature.p1`; PROCHOT CBB throttle entry/exit verification
