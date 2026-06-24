# TCD: MIO Trunk Clock gating Cross products

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421242](https://hsdes.intel.com/appstore/article-one/#/22022421242) |
| **Title** | MIO Trunk Clock gating Cross products |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TP** | [16030762530 — NWP PM AIPM - IO Trunk Clock Gating](https://hsdes.intel.com/appstore/article-one/#/16030762530) |
| **KB last updated** | 2026-06-22 |
| **NWP Disposition** | **Mixed — reset/negative-path open; runtime-entry-dependent cross-products rejected** |

## Section 1: Architecture / Micro-architecture and Functionality

### Feature Overview

Cross-product TCs testing TCG interactions with other platform events. Split into two groups:
- **Open**: reset sequences, negative-path (IO Stack Disable), and PMX — NWP-applicable because
  they validate correct behavior when TCG infrastructure interacts with reset/disable flows
- **Rejected**: ADR, PC6, Hot Plug, Seamless patching — require prior TCG entry, which never
  occurs on NWP

| HSD | Title | Status | Reason |
|-----|-------|--------|--------|
| [22022423009](https://hsdes.intel.com/appstore/article-one/#/22022423009) | IO Trunk Clock gating x ADR | **Rejected** | No prior TCG entry state to exit from on NWP |
| [22022423014](https://hsdes.intel.com/appstore/article-one/#/22022423014) | IO Trunk Clock gating x PC6 | **Rejected** | PkgC6 ZBB'd on NWP; requires prior TCG entry |
| [22022423016](https://hsdes.intel.com/appstore/article-one/#/22022423016) | IO Trunk Clock gating x Warm Reset | **Open** | Reset recovery correctness — PrimeCode re-programs RC at reset exit; NWP-applicable |
| [22022423017](https://hsdes.intel.com/appstore/article-one/#/22022423017) | IO Trunk Clock gating_PMX | **Open** | PMX (PUnit MSR eXerciser) infrastructure applicable to NWP |
| [22022423018](https://hsdes.intel.com/appstore/article-one/#/22022423018) | MIO Trunk Clock Gating x Hot Plug / Hot Eject | **Rejected** | Requires prior TCG entry to test exit from gated state |
| [22022423019](https://hsdes.intel.com/appstore/article-one/#/22022423019) | MIO Trunk Clock gating x IO Stack Disable | **Open** | Negative path: verify PrimeCode does NOT enable AIPM for disabled stacks (CMPL_STATUS=2) |
| [22022423022](https://hsdes.intel.com/appstore/article-one/#/22022423022) | MIO Trunk Clock gating x Seamless patching | **Rejected** | Requires prior TCG entry state to verify retention across MCU patch |
| [22022423025](https://hsdes.intel.com/appstore/article-one/#/22022423025) | MIO Trunk Clock gating x Surprise Reset | **Open** | Surprise reset recovery — RC re-init correctness after uncontrolled reset |

### Open TCs — NWP Applicability Rationale

- **Warm Reset (22022423016)**: PrimeCode re-programs RC_MIO workpoints at every PH6. This TC verifies the re-init is complete and correct after warm reset.
- **Surprise Reset (22022423025)**: Same as warm reset but uncontrolled path. Verifies RC state is clean after surprise reset.
- **IO Stack Disable (22022423019)**: Negative correctness — verifies PrimeCode applies CMPL_STATUS=2 skip correctly for disabled stacks and does NOT program AIPM for them.
- **PMX (22022423017)**: PUnit MSR exerciser — applicable to NWP for RC/PUNIT interface validation.

---

## Section 2: Interfaces and Protocols

Warm/surprise reset path: PrimeCode re-programs RC via PUnit MMIO at PH6. IO stack disable: PrimeCode reads CMPL_STATUS from RA per §9.2.

---

## Section 3: Reset, Power, and Clocking

All RC state lost on warm/surprise reset — PrimeCode must re-program at PH6. Warm Reset TC verifies workpoints correctly restored. Surprise Reset TC verifies clean-state recovery.

---

## Section 4: Programming Model

| TC | Key Verification |
|----|-----------------|
| Warm Reset | After reset: RC workpoints = expected values; QCh FSM policy re-enabled |
| Surprise Reset | After uncontrolled reset: same workpoint check; no residual state from pre-reset |
| IO Stack Disable | Disabled stack: CMPL_STATUS=2 → PrimeCode skips RA → AIPM NOT enabled for that stack |
| PMX | RC/PUnit MMIO register accessibility via PMX exerciser |

---

## Section 5: Operational Behavior

Warm/Surprise reset: RC re-programmed at PH6 identically to initial boot. Stack disable: per §9.2, PrimeCode skips RA and does not activate AIPM — this is a required negative-path test.

---

## Section 6: Corner Cases & Error Handling

ADR, PC6, Hot Plug, Seamless patching all require the trunk clock to have been gated prior to the cross-product event — since TCG entry never fires on NWP, these cross-products have no valid scenario.

---

## Section 7: Security / Safety / Policy

IO Stack Disable TC is safety-relevant: if PrimeCode incorrectly enables AIPM for a disabled stack, it could cause power/clock anomalies.

---

## Section 8: References

- [AIPM KB — aipm.md](../../pm_features/pm_cross_products/aipm.md) — TPF review; open/rejected split justification
- [NWP PM MAS §9.2](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — CMPL_STATUS=2 skip logic for disabled stacks
- [PCIe L1 ZBB — HSD 22021155368](https://hsdes.intel.com/appstore/article-one/#/22021155368)
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html)
- [DMR IO Trunk Clock Gating HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_IO_trunk_clock_gating_support.html)
