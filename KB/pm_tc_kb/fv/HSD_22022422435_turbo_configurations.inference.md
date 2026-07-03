# Deep Analysis: Turbo Configurations

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422435 |
| **Title** | Turbo configurations |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | Turbo opportunistic boost — active core count, license level, power headroom, ICCMax |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the full **Turbo configuration and decision framework**:
- Turbo is opportunistic: granted when power/current/thermal headroom available
- Turbo ratio depends on: active core count, core license level, power headroom, OS/HWP request
- Turbo Ratio Limits: enforce ICCMax limitation (per-part variation management)

On NWP, the same Turbo opportunistic logic applies. NWP turbo ratio tables differ from DMR (48 cores/CBB vs 32).

**Key Justification:**
- `Ready_for_testing` + `DMR_PO` + `NGA_MAIN` + `plc.ti_gate.b0` + `plc.feature.p1` + `PMSS_NWP_READINESS_CHECK` tags
- Core turbo configuration test; applicable to NWP

---

## Section B: NWP-Specific Test Procedure

### NWP Turbo Configuration Factors

| Factor | DMR | NWP |
|--------|-----|-----|
| Cores/CBB | 32 | **48** |
| CBBs | 2 (base config) | **2** |
| Total cores | Up to 128 | **96** |
| Turbo ratio table | Per active core count | Per active core count (NWP-specific values) |
| Core License | LCC/MCC/HCC | NWP license levels |
| ICCMax | Per-SKU DMR fuse | Per-SKU NWP fuse |

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Read base turbo ratio from `IA32_TURBO_RATIO_LIMIT` (MSR 0x1AD) | NWP-specific values |
| 2 | Run turbo PMx | `python runPmx.py -x nwp.xml -p turbo -tM 60` |
| 3 | Verify 1-core turbo (max ratio when 1 active) | All other cores idle |
| 4 | Verify N-core turbo (ratio decreases with more active cores) | Scale from 1 to 96 |
| 5 | Force ICCMax limit; verify turbo clipped | Power limit PROCHOT |
| 6 | Verify turbo with EETurbo enabled/disabled | More/less aggressive |

### NWP Pass Criteria
- Turbo granted when power headroom available
- Turbo ratio matches `IA32_TURBO_RATIO_LIMIT` table per active core count
- ICCMax limit properly clips turbo (no over-current)
- Turbo ratio decreases monotonically as active core count increases

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; Turbo logic same; NWP ratio values differ**

Required adaptations:
1. `python runPmx.py -x nwp.xml -p turbo -tM 60`
2. Read NWP-specific `IA32_TURBO_RATIO_LIMIT` values (48 cores/CBB vs 32)
3. NWP 96 total cores — scale active core count sweep 1–96
4. Verify NWP ICCMax fuse values and license level configuration

**Priority**: High — `DMR_PO` + `NGA_MAIN` + `plc.feature.p1`; fundamental Turbo configuration validation
