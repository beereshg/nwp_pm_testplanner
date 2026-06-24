# TCD: MC Shallow Self Refresh Boot Time Setup

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421228](https://hsdes.intel.com/appstore/article-one/#/22022421228) |
| **Title** | MC Shallow Self Refresh Boot Time Setup |
| **Status** | rejected |
| **Owner** | bg3 |
| **Parent TP** | [16030762531 — NWP PM AIPM - Memory Trunk Clock Gating & SSR](https://hsdes.intel.com/appstore/article-one/#/16030762531) |
| **KB last updated** | 2026-06-22 |
| **NWP Disposition** | **ZBB — MC SSR boot setup not required; SSR not enabled on NWP** |

## Section 1: Architecture / Micro-architecture and Functionality

### Feature Overview

This TCD covers boot-time MC SSR setup: RC workpoints, P-channel enabling, hysteresis/SSR residency timers, and capability register checkout. Unlike the IO TCG equivalent (TCD 22022421240 — which is open because RC_MIO IS programmed), MC SSR boot setup is **rejected** because the MC SSR feature itself is ZBB'd — the MC never programs SSR workpoints or enables P-channel SSR flows on NWP.

**Co-design confirmed (2026-06-22)**: *"PkgC6 is not supported on NWP. Therefore, there will not be any SR, nor any SSR flows supported from the IP teams."*

| HSD | Title | Status | Reason |
|-----|-------|--------|--------|
| *(TC)* | IO Trunk Clock gating_Auto_Idle WP checkout | **Rejected — ZBB** | MC SSR workpoints not programmed on NWP |
| *(TC)* | IO Trunk Clock gating_Check Timers (hysteresis + SSR residency) | **Rejected — ZBB** | SSR residency timer not applicable; feature ZBB'd |
| *(TC)* | IO Trunk Clock gating_PChannel enabling | **Rejected — ZBB** | SSR P-channel not enabled on NWP |
| *(TC)* | IO Trunk Clock gating_RC Capability0 reg checkout | **Rejected — ZBB** | MC SSR RC capability not relevant without SSR |
| *(TC)* | IO Trunk Clock gating_RC PState table checkout | **Rejected — ZBB** | SSR pstate table not configured on NWP |

### Why Boot Setup is Rejected (Unlike IO TCG)

The IO TCG boot setup (TCD 22022421240) is open because PrimeCode **does** program the RC_MIO registers at boot even on NWP. For MC SSR, the MC firmware **does not** program SSR-specific workpoints or enable SSR flows because SSR is ZBB'd from the MC team's perspective. The programming infrastructure is absent, not just the runtime trigger.

---

## Section 2: Interfaces and Protocols

Not applicable — MC SSR P-channel, workpoint, and timer programming are not executed on NWP.

---

## Section 3: Reset, Power, and Clocking

Not applicable — SSR ZBB'd on NWP.

---

## Section 4: Programming Model

Not applicable — SSR workpoints and timers not programmed on NWP.

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

- [AIPM KB — aipm.md](../../pm_features/pm_cross_products/aipm.md) — MC SSR ZBB confirmation; TPF review 2026-06-01
- [NWP HAS Overview](https://docs.intel.com/documents/custom-xeon/newport-docs/has/overview/nwp_has.html) — NWP Memory PM feature delta
- [NWP HAS Comments](https://docs.intel.com/documents/custom-xeon/newport-docs/has/comments.html) — MC team ZBB statement; PkgC6 ZBB SSR impact
- [LPDDR6 HAS](https://docs.intel.com/documents/iparch/mc/has/gen6/releases/lpddr6/lpddr6.html) — WCK always-on; no clock stop; no power-down
