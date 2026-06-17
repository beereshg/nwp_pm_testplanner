# Deep Analysis: RAPL Cold TDP Checkout

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421962 |
| **Title** | RAPL Cold TDP checkout |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | Cold TDP — fused temperature threshold adds offset to PL1 below threshold |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **Cold TDP behavior**:
- Pcode tracks a temperature threshold (fused per SKU by binsplit)
- If the die temperature is **below** the fused threshold → Pcode adds a fused offset to PL1 limit (higher power budget at cold)
- Verify the delta is correctly applied as temperature crosses the fused threshold in both directions

This is a standard RAPL fused-parameter feature applicable on NWP. Tags: `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Cold TDP Fuse Paths (NWP)

| Fuse | NWP Path |
|------|----------|
| Cold TDP temperature threshold | `sv.socket0.imh0.fuses.punit.<cold_tdp_temp_thresh>` |
| Cold TDP PL1 offset | `sv.socket0.imh0.fuses.punit.<cold_tdp_pl1_offset>` |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Read Cold TDP fuses | Temperature threshold + PL1 offset from `imh0.fuses.punit.*` |
| 2 | Run cpu_rapl PMx | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| 3 | At cold temperature (below fused threshold) | Verify PL1 = nominal_PL1 + cold_offset |
| 4 | Warm system to above fused threshold | Platform thermal conditioning |
| 5 | Verify PL1 drops back to nominal (offset removed) | Cold offset only applied below threshold |
| 6 | Cross threshold in both directions | Verify hysteresis if any |

### NWP Notes
- Cold TDP fuse values differ per NWP SKU (set by binsplit)
- NWP: single `imh0`; temperature aggregated from 2 CBBs
- `runPmx.py -x nwp.xml` (not `dmr.xml`)

### Pass Criteria
- PL1 = nominal + cold_offset when die temperature < threshold
- PL1 = nominal when die temperature ≥ threshold
- Transition is clean when temperature crosses threshold

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; read NWP cold TDP fuses from `imh0.fuses.punit.*`**

1. `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3`
2. Read NWP cold TDP threshold fuse at `sv.socket0.imh0.fuses.punit.*`
3. Verify PL1 offset applied when below threshold; removed above threshold
4. Test both cold→warm and warm→cold temperature transitions

**Priority**: Medium — `plc.feature.p2`; Cold TDP is a SKU-specific power budget optimization; validates correct fuse application on NWP
