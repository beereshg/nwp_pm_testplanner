# TCD: MIO Trunk Clock gating Actions

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421236](https://hsdes.intel.com/appstore/article-one/#/22022421236) |
| **Title** | MIO Trunk Clock gating Actions |
| **Status** | rejected |
| **Owner** | bg3 |
| **Parent TP** | [16030762530 — NWP PM AIPM - IO Trunk Clock Gating](https://hsdes.intel.com/appstore/article-one/#/16030762530) |
| **KB last updated** | 2026-06-22 |
| **NWP Disposition** | **ZBB — Runtime TCG entry triggers not available on NWP** |

## Section 1: Architecture / Micro-architecture and Functionality

### Feature Overview

This TCD covers the **runtime entry-trigger actions** that cause the RC_MIO to gate the MIO
trunk clock: Q-channel deassertion events (devices entering L1), no-device stack conditions,
and CXL/PCIe link L1 entry. All four TCs are rejected on NWP because the runtime entry
triggers (PCIe L1, CXL L1, UXI L1) are ZBB'd — the hardware Q-channel infrastructure is
present, but no device ever de-asserts QActive at runtime.

| HSD | Title | Status | Reason |
|-----|-------|--------|--------|
| [22022422982](https://hsdes.intel.com/appstore/article-one/#/22022422982) | IO Trunk Clock gating_QActive deassertion | **Rejected — ZBB** | No L1 trigger on NWP → QActive always asserted for active stacks |
| [22022422984](https://hsdes.intel.com/appstore/article-one/#/22022422984) | MIO Trunk Clock gating Actions_No Devices attached in PC0 | **Rejected — ZBB** | Empty stacks statically disabled at boot (BIOS + PrimeCode CMPL_STATUS=2); not runtime AIPM-gated |
| [22022422987](https://hsdes.intel.com/appstore/article-one/#/22022422987) | MIO Trunk Clock gating CXL Link in L1 | **Rejected — ZBB** | CXL L1 ZBB on NWP |
| [22022422989](https://hsdes.intel.com/appstore/article-one/#/22022422989) | MIO Trunk Clock gating PCIe Link in L1 | **Rejected — ZBB** | PCIe L1 ZBB on NWP [HSD 22021155368] |

### Architecture Context

The RC_MIO hardware is present on NWP and programmed at boot. However:
- PCIe L1 → ZBB ([HSD 22021155368](https://hsdes.intel.com/appstore/article-one/#/22021155368))
- UXI L1/L0p → ZBB ([HSD 22021155419](https://hsdes.intel.com/appstore/article-one/#/22021155419))
- CXL L1 → ZBB
- Empty stacks: statically power-gated at boot, not runtime AIPM-gated

Without any L1 entry, QActive is never de-asserted → RC never observes idle condition → trunk clock never gated. Boot-time setup TCs (in sibling TCD 22022421240) remain open as infrastructure validation.

---

## Section 2: Interfaces and Protocols

Late Q-channel signals (PCIe/CXL/UXI QActive/QAccept) are present but never asserted idle at runtime on NWP due to L1 ZBB. RC hardware monitoring is active but never triggers.

---

## Section 3: Reset, Power, and Clocking

RC_MIO re-initialized after each reset. PrimeCode programs boot-time workpoints (PH6). Trunk clock gate never activates at runtime on NWP.

---

## Section 4: Programming Model

Boot-time workpoint programming executes on NWP (see TCD 22022421240). Runtime TCG programming (workpoint transition on idle) never executes — no valid idle trigger.

---

## Section 5: Operational Behavior

**DMR**: PC/CXL/UXI enters L1 → QActive de-asserted → RC enters hysteresis → gates trunk clock. **NWP**: L1 ZBB'd → QActive always asserted → trunk clock never gated. Empty stacks disabled statically at boot.

---

## Section 6: Corner Cases & Error Handling

Not applicable — runtime TCG actions never occur on NWP.

---

## Section 7: Security / Safety / Policy

Not applicable — see feature context in Section 1.

---

## Section 8: References

- [AIPM KB — aipm.md](../../pm_features/pm_cross_products/aipm.md) — Full architecture and NWP delta
- [PCIe L1 ZBB — HSD 22021155368](https://hsdes.intel.com/appstore/article-one/#/22021155368) — Primary TCG trigger ZBB
- [UXI L1 ZBB — HSD 22021155419](https://hsdes.intel.com/appstore/article-one/#/22021155419) — Secondary TCG trigger ZBB
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — §9.2 static stack disable (CMPL_STATUS=2)
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html)
- [NWP Validation Domain Expectations](https://wiki.ith.intel.com/spaces/CustomCpuProductDevelopment/pages/4447220900/NWP+Validation+Domain+Expectations)
- [DMR IO Trunk Clock Gating HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_IO_trunk_clock_gating_support.html) — DMR reference
