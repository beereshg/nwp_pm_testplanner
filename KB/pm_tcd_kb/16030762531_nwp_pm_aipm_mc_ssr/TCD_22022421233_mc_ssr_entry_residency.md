# TCD: MC Shallow Self Refresh Entry / Residency

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421233](https://hsdes.intel.com/appstore/article-one/#/22022421233) |
| **Title** | MC Shallow Self Refresh Entry / Residency |
| **Status** | rejected |
| **Owner** | bg3 |
| **Parent TP** | [16030762531 — NWP PM AIPM - Memory Trunk Clock Gating & SSR](https://hsdes.intel.com/appstore/article-one/#/16030762531) |
| **KB last updated** | 2026-06-22 |
| **NWP Disposition** | **ZBB — SSR entry never occurs on NWP; perfmon counter stays zero** |

## Section 1: Architecture / Micro-architecture and Functionality

### Feature Overview

This TCD covers MC SSR entry detection and residency counter validation via perfmon. The TC (Perfmon debug counters — Autonomous Entry) verifies that SSR_RESIDENCY PMON counter accumulates when the MC autonomously enters SSR. On NWP, SSR is ZBB'd — SSR entry never occurs, perfmon counter remains at zero, and this TC has no valid test basis.

**Co-design confirmed (2026-06-22)**: *"Memory Power Management: No APD/PPD, No LPM1/LPM2/LPM3, No Shallow Self-Refresh (SSR), No Self-Refresh (SR). See HSD. Also documented in NWP Memory Feature Set Delta."*

| HSD | Title | Status | Reason |
|-----|-------|--------|--------|
| *(TC)* | MC SSR Perfmon debug counters — Autonomous Entry | **Rejected — ZBB** | SSR_RESIDENCY PMON counter never increments; SSR entry ZBB'd on NWP |

### Parallel with IO TCG Entry/Residency (TCD 22022421244)

Both this TCD (MC SSR) and TCD 22022421244 (IO TCG) cover perfmon-based residency validation. Both are rejected for the same reason pattern: the entry condition is ZBB'd on NWP, so the perfmon counter never increments. TCD 22022421244 is rejected due to no L1 trigger; this TCD is rejected due to SSR ZBB.

---

## Section 2: Interfaces and Protocols

SSR_RESIDENCY PMON counter — not applicable on NWP (SSR ZBB'd).

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

- [AIPM KB — aipm.md](../../pm_features/pm_cross_products/aipm.md) — MC SSR ZBB; TPF review 2026-06-01
- [NWP HAS Overview](https://docs.intel.com/documents/custom-xeon/newport-docs/has/overview/nwp_has.html) — NWP Memory PM feature delta
- [NWP HAS Comments](https://docs.intel.com/documents/custom-xeon/newport-docs/has/comments.html) — MC team ZBB statement
- [LPDDR6 HAS](https://docs.intel.com/documents/iparch/mc/has/gen6/releases/lpddr6/lpddr6.html)
- [TCD 22022421244 — IO TCG Entry/Residency](https://hsdes.intel.com/appstore/article-one/#/22022421244) — Parallel IO TCG rejected TC (same pattern)
