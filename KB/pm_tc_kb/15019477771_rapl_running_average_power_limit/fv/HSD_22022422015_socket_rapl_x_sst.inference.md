# Deep Analysis: Socket RAPL x SST

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422015 |
| **Title** | Socket rapl x SST |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | RAPL cross-product with SST (Speed Select Technology) |
| **NWP Disposition** | **Skip_ZBB** |

---

## Section A: NWP Disposition & Justification

**Disposition: Skip_ZBB**

This test verifies **Socket RAPL interaction with SST (Speed Select Technology)**. The GNR HAS §RAPL×SST describes the interaction between RAPL limits and SST operating points.

**NWP ZBB restriction**: All SST features (SST-PP, SST-BF, SST-CP, HGS) are **Zero Bug Baseline (ZBB)** on NWP — they are not implemented or enabled on NWP silicon. Therefore, the RAPL × SST cross-product cannot be tested on NWP.

**Disposition: Skip_ZBB** — SST is a prerequisite feature that is ZBB on NWP. This test does not apply until SST is validated on NWP platform.

---

## Section B: NWP ZBB Impact

### SST Features (all ZBB on NWP)

| SST Feature | NWP Status |
|-------------|------------|
| SST-PP (Performance Profile) | ZBB — not functional |
| SST-BF (Base Frequency) | ZBB — not functional |
| SST-CP (Core Power) | ZBB — not functional |
| HGS (Hardware Group Select) | ZBB — not functional |

### RAPL × SST Interaction (cannot test on NWP)
- SST changes active core counts and TDP per profile
- RAPL limits must adjust with SST profile changes
- Without SST operational, this cross-product is not exercisable

---

## Section F: Recommendation

**Recommendation: SKIP — Socket RAPL × SST is Skip_ZBB because all SST features (SST-PP, SST-BF, SST-CP, HGS) are ZBB on NWP**

This test case does not apply to NWP validation scope. No NWP-adapted procedure is possible until SST is validated.

**Priority**: N/A (ZBB)
