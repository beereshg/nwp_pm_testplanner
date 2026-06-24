# TCD: MC Shallow Self Refresh Cross Products

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421230](https://hsdes.intel.com/appstore/article-one/#/22022421230) |
| **Title** | MC Shallow Self Refresh Cross Products |
| **Status** | rejected |
| **Owner** | bg3 |
| **Parent TP** | [16030762531 — NWP PM AIPM - Memory Trunk Clock Gating & SSR](https://hsdes.intel.com/appstore/article-one/#/16030762531) |
| **KB last updated** | 2026-06-22 |
| **NWP Disposition** | **ZBB — All cross-products require prior SSR entry; SSR ZBB'd on NWP** |

## Section 1: Architecture / Micro-architecture and Functionality

### Feature Overview

Cross-product TCs testing MC SSR interactions with ADR, reset, PMX, and PkgC6. All rejected because SSR entry never occurs on NWP (SSR ZBB'd), so no cross-product scenario involving SSR state has a valid test basis.

**Co-design confirmed (2026-06-22)**: *"Memory Power Management: No APD/PPD, No LPM1/LPM2/LPM3, No Shallow Self-Refresh (SSR), No Self-Refresh (SR). See HSD. Also documented in NWP Memory Feature Set Delta."*

| HSD | Title | Status | Reason |
|-----|-------|--------|--------|
| *(TC)* | MC SSR x ADR | **Rejected — ZBB** | ADR interaction with SSR requires prior SSR entry; never occurs on NWP |
| *(TC)* | MC SSR x Reset | **Rejected — ZBB** | Reset recovery from SSR state; SSR state never entered on NWP |
| *(TC)* | MC SSR PMX | **Rejected — ZBB** | SSR PMX exerciser not applicable without SSR feature enabled |
| *(TC)* | MC SSR cross PC6 | **Rejected — ZBB** | PkgC6 ZBB'd on NWP AND SSR ZBB'd — double ZBB |

### Note on x Reset vs IO TCG x Warm/Surprise Reset

The IO TCG warm reset and surprise reset TCs (in TCD 22022421242) are **open** because they test RC_MIO register re-initialization, which happens regardless of runtime TCG entry. The MC SSR x Reset TC tests **recovery from SSR state** — which requires SSR to have been entered first. Since SSR entry is ZBB'd on NWP, this cross-product has no valid scenario.

---

## Section 2: Interfaces and Protocols

Not applicable — SSR entry never occurs; no cross-product SSR state to test.

---

## Section 3: Reset, Power, and Clocking

Not applicable — SSR ZBB'd on NWP.

---

## Section 4: Programming Model

Not applicable — see feature context in Section 1.

---

## Section 5: Operational Behavior

Not applicable — see feature context in Section 1.

---

## Section 6: Corner Cases & Error Handling

Not applicable — see feature context in Section 1.

---

## Section 7: Security / Safety / Policy

Not applicable — see feature context in Section 1.

---

## Section 8: References

- [AIPM KB — aipm.md](../../pm_features/pm_cross_products/aipm.md) — MC SSR ZBB; all 14 SSR TCs confirmed ZBB
- [NWP HAS Overview](https://docs.intel.com/documents/custom-xeon/newport-docs/has/overview/nwp_has.html) — NWP Memory PM feature delta
- [NWP HAS Comments](https://docs.intel.com/documents/custom-xeon/newport-docs/has/comments.html) — MC team ZBB; PkgC6 ZBB impact
- [LPDDR6 HAS](https://docs.intel.com/documents/iparch/mc/has/gen6/releases/lpddr6/lpddr6.html)
