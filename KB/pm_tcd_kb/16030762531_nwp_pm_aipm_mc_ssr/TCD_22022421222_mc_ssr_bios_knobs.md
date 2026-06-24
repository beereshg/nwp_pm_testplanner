# TCD: MC Shallow Self Refresh BIOS knobs

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421222](https://hsdes.intel.com/appstore/article-one/#/22022421222) |
| **Title** | MC Shallow Self Refresh BIOS knobs |
| **Status** | rejected |
| **Owner** | bg3 |
| **Parent TP** | [16030762531 — NWP PM AIPM - Memory Trunk Clock Gating & SSR](https://hsdes.intel.com/appstore/article-one/#/16030762531) |
| **KB last updated** | 2026-06-22 |
| **NWP Disposition** | **ZBB — MC SSR not enabled on NWP; BIOS SSR knobs not required** |

## Section 1: Architecture / Micro-architecture and Functionality

### Feature Overview

This TCD covers BIOS knob configuration for enabling/disabling MC Shallow Self-Refresh. On NWP, SSR is ZBB'd by MC team decision — SSR BIOS knobs have no effect and are not a required validation item.

**Co-design confirmed (2026-06-22)**: *"Memory Power Management: No APD/PPD, No LPM1/LPM2/LPM3, No Shallow Self-Refresh (SSR), No Self-Refresh (SR). Also documented in NWP Memory Feature Set Delta."*

| HSD | Title | Status | Reason |
|-----|-------|--------|--------|
| *(1 TC — BIOS knobs)* | MC Shallow Self Refresh BIOS knobs | **Rejected — ZBB** | SSR ZBB'd on NWP; no SSR BIOS knob validation needed |

---

## Section 2: Interfaces and Protocols

SSR BIOS knobs would configure MC SSR enable/disable. Not applicable on NWP — SSR not enabled.

---

## Section 3: Reset, Power, and Clocking

Not applicable — SSR ZBB'd on NWP.

---

## Section 4: Programming Model

Not applicable — SSR BIOS knob programming not required.

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

- [AIPM KB — aipm.md](../../pm_features/pm_cross_products/aipm.md) — MC SSR ZBB confirmation
- [NWP HAS Overview](https://docs.intel.com/documents/custom-xeon/newport-docs/has/overview/nwp_has.html) — NWP Memory PM feature set delta
- [NWP HAS Comments](https://docs.intel.com/documents/custom-xeon/newport-docs/has/comments.html) — MC team ZBB statement
- [LPDDR6 HAS](https://docs.intel.com/documents/iparch/mc/has/gen6/releases/lpddr6/lpddr6.html) — LPDDR6 power mode support table
