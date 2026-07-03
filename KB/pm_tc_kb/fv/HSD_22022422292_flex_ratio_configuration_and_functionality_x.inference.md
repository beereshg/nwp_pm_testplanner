# Deep Analysis: Flex Ratio Configuration and Functionality X SST

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422292 |
| **Title** | Flex ratio configuration and functionality X SST |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | Flex Ratio cross-product with SST-PP |
| **NWP Disposition** | **Skip_ZBB** |

---

## Section A: NWP Disposition & Justification

**Disposition: Skip_ZBB**

This test verifies **Flex Ratio** behavior in combination with **SST-PP (Speed Select Technology — Performance Profile)**. The command `runPmx.py -x dmr.xml -p sst_pp` executes the SST-PP test plug-in.

**SST-PP is in the NWP Zero-Bug-Baseline (ZBB) list** — it is not supported on NWP. Because this test's execution depends on `sst_pp` plug-in (SST-PP is the cross-product vehicle), the test cannot be run on NWP.

The base Flex Ratio functionality (without SST-PP) is covered by TC 22022422287.

**Justification:**
- `sst_pp` plug-in requires SST-PP functionality — **ZBB on NWP**
- Cross-product test requires both features to be functional
- `New_Content` tag: this is a new test; not yet ported to NWP-safe mechanism
- `pm.xproducts.pm` tag: confirms PM cross-product test

---

## Section B: Skip Rationale

| Factor | Assessment |
|--------|-----------|
| SST-PP on NWP | **Not supported (ZBB)** |
| Flex Ratio alone | Covered by TC 22022422287 |
| Alternative (non-SST-PP cross) | Not defined — would need new TC |
| `To_be_ported` concern | Not tagged, but SST-PP is ZBB |

**Base feature coverage**: Flex Ratio is validated by TC 22022422287 (without SST-PP cross-product).

---

## Section C: Action Items

| # | Action | Owner |
|---|--------|-------|
| 1 | Skip this TC on NWP; covered for Flex Ratio by TC 22022422287 | Test team |
| 2 | If NWP ever enables SST-PP, revisit this test | Future NWP stepping |
| 3 | Adapt SST cross-product to NWP-supported SST feature (SST-TF/PCT if applicable) | NWP PM team |

---

## Section F: Recommendation

**Recommendation: SKIP — SST-PP is ZBB on NWP; base Flex Ratio covered by TC 22022422287**

This test requires SST-PP which is not supported on NWP. No adaptation possible without enabling SST-PP or changing the cross-product vehicle.

**Priority**: N/A — ZBB skip; Flex Ratio base coverage exists in TC 22022422287
