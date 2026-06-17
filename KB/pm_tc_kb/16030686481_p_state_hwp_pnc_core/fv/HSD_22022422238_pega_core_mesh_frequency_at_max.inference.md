# Deep Analysis: PEGA Core/Mesh Frequency at Max/Min Combinations With Traffic

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422238 |
| **Title** | PEGA Core/Mesh frequency at max/min combinations w/ traffic |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | Core vs Mesh frequency cross-combination stress |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies the **stress condition of core frequency at minimum while mesh (uncore) at maximum, and vice versa**, with concurrent IDI traffic (Supercollider/Memicals). This exercises the cross-domain dependency between core and ring/mesh clocks.

Related GNR risk HSD 14014839301 motivates this cross-combination test. On NWP, the same core vs mesh/ring frequency interaction exists. Primary adaptation: `dmr.xml` → `nwp.xml`.

**Key Justification:**
- Core/ring frequency cross-combination applicable on NWP
- `pm.xproducts.traffic` cross-product required (IDI traffic)
- `DMR_PO` + `NGA_MAIN`: primary CI coverage
- Identified risk from GNR pre-silicon — important to validate on NWP silicon

---

## Section B: NWP-Specific Test Procedure

### Test Scenarios

| Scenario | Core Freq | Mesh/Ring Freq | Traffic | Expected |
|----------|-----------|----------------|---------|----------|
| A | Min (Pm) | Max (P0) | IDI (Supercollider) | No hang; no coherency error |
| B | Max (P0) | Min | IDI (Supercollider) | No hang; no coherency error |
| C | Sweep transition | Sweep | Memicals | Stable frequency transitions |

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Configure core at Pm, mesh at P0 | `python runPmx.py -x nwp.xml -p cpu_traffic -p pega_uncore -tM 6` |
| 2 | Start IDI traffic (Supercollider or Memicals) | Same traffic generators |
| 3 | Run for test duration; monitor for errors | No MCAs, no IERR |
| 4 | Swap: configure core at P0, mesh at Pm | Same script; different ratio targets |
| 5 | Repeat with traffic; monitor | Same error checks |

### NWP Topology Notes
- NWP mesh/ring: ring bus on CBB die; `pega_uncore` plug-in targets ring ratio
- IMH fabric frequency managed separately from CBB ring
- 2 CBBs on NWP: each CBB has its own ring domain

### NWP Pass Criteria
- No Machine Check Errors (MCAs/IERR) under any cross-combination
- No fabric deadlock or hang during frequency transitions
- Traffic completes without data errors (Supercollider coherency pass, Memicals data verify pass)
- Frequency transitions complete within expected latency bounds

---

## Section C: NWP Delta Impact Analysis

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| CBB count | 4 | 2 | Ring/mesh domain count differs |
| Ring domain | 4 ring domains (1/CBB) | 2 ring domains | Script handles via XML |
| IMH fabric | Present | Same | No change |
| Script XML | `dmr.xml` | `nwp.xml` | **Required change** |

---

## Section E: Risk Assessment

| # | Risk | Severity | Notes |
|---|------|----------|-------|
| 1 | `pega_uncore` plug-in NWP support | Medium | Verify `pega_uncore` knows NWP ring topology; may need NWP-specific config |
| 2 | NWP ring ratio min value | Low | Verify NWP minimum ring ratio differs from DMR |

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; verify `pega_uncore` NWP support**

Core/mesh cross-combination test is critical risk validation on NWP given the GNR pre-silicon risk precedent.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p cpu_traffic -p pega_uncore -tM 6`
2. Verify `pega_uncore` plug-in supports NWP ring topology
3. NWP has 2 ring domains (1 per CBB); verify plug-in targets both

**Priority**: High — `DMR_PO` + `NGA_MAIN` + `pm.xproducts.traffic`; motivated by GNR risk history
