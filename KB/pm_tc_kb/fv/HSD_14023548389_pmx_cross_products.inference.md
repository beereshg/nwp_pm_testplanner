# Deep Analysis: PMX Cross Products

| Field | Value |
|-------|-------|
| **HSD ID** | 14023548389 |
| **Title** | pmx cross products |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | (blank) |
| **Sub-Feature** | PMx cross-product — run multiple PMx plugins concurrently or in sequence |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

*Note: HSD steps field is completely empty — no test content provided.*

Based on title "pmx cross products": this test runs multiple PMx plugins in combination to validate cross-feature behavior via the `runPmx.py` framework.

---

## Section B: NWP-Specific Test Procedure

*Test content entirely missing in source HSD. Below is inferred from PMx cross-product testing context.*

### NWP PMx Cross-Product Approach

| Step | Action | NWP Command |
|------|--------|-------------|
| 1 | Run RAPL + C-states PMx concurrently | `python runPmx.py -x nwp.xml -p rapl,cstate -tM 60` |
| 2 | Run PMAX + RAPL cross | Sequential PMx test |
| 3 | Run thermals + C-states cross | Concurrent stress |
| 4 | Verify all PMx plugins pass | No regression |

### Pass Criteria
- All selected PMx cross-product combinations pass
- No feature interaction causing failures
- `runPmx.py -x nwp.xml` framework stable

---

## Section F: Recommendation

**Recommendation: ADOPT — Empty source content; define specific PMx plugin combinations for NWP; `dmr.xml` → `nwp.xml`; exclude ZBB feature plugins**

**Priority**: Low — `(blank)` feature; content TBD — prioritize after individual PMx tests pass
