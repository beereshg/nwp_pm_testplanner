# TCD: [IMH Thermal] Cross-Die Thermal Propagation

| Field | Value |
|-------|-------|
| **TCD ID** | [16031170080](https://hsdes.intel.com/appstore/article-one/#/16031170080) |
| **Title** | [IMH Thermal] Cross-Die Thermal Propagation |
| **Status** | draft |
| **Parent TPF** | [16031170063 — IMH Thermal Control](https://hsdes.intel.com/appstore/article-one/#/16031170063) |
| **Feature** | Cross-Die Thermal |
| **Sub-Feature** | HPM cross-die thermal throttle signaling |
| **NWP Disposition** | New |
| **KB last updated** | 2026-07-19 |
| **Co-Design ref** | Ingest tracker N1; Co-Design cross-die thermal query 2026-07-19 |
| **Spec refs** | NWP IMH SoC PM MAS: cross-die thermal; DMR thermal flows: cross-die throttle open items |

---

## Section 1: Architecture / Micro-architecture and Functionality

**Cross-Die Thermal Propagation** validates the mechanism by which thermal throttle decisions propagate between IMH and CBB dies on NWP. When one die cannot self-cool via local throttling, it sends a cross-die throttle request to the other die(s) via HPM messages, forcing remote throttle action.

> **Architecture overview:** See TPF — IMH Thermal Control §Design Details.

### Key Behavioral Facts (from Co-Design spec query)

- **IMH → CBB:** HPM message `DNS_EVENT_DELIVERY[cross_die_throttle]` sent when IMH self-throttle is insufficient. CBB overrides its current temperature to TJMax as input to EMTTM PID controller → triggers frequency throttling.
- **CBB → IMH:** HPM message `UPS_EVENT_DELIVERY[cross_die_throttle]` sent when CBB cannot self-cool. IMH forces fabric frequencies to P1.
- **D2D link in L1:** FAST_THROTTLE_IN_0 virtual wire available for hard throttle signaling with <1ns latency. HPM message path requires D2D link wake.
- **No explicit latency spec** for HPM-based cross-die thermal propagation; hard throttle wires are ~1ns.

---

## Section 2: Functional Requirements / Spec Refs

| FR ID | Requirement | Spec ref |
|---|---|---|
| FR1 | IMH→CBB: DNS_EVENT_DELIVERY[cross_die_throttle] delivered → CBB overrides temp to TJMax → EMTTM PID throttles | NWP IMH SoC PM MAS: cross-die thermal |
| FR2 | CBB→IMH: UPS_EVENT_DELIVERY[cross_die_throttle] delivered → IMH forces fabric to P1 | NWP IMH SoC PM MAS: cross-die thermal |
| FR3 | D2D link in L1: FAST_THROTTLE_IN_0 wire propagates hard throttle | DMR thermal flows: D2D thermal wires |
| FR4 | Cross-die throttle deassertion → remote die resumes normal thermal control | NWP IMH SoC PM MAS |

---

## Section 5: Pass/Fail Bar

| Bar | Measurable criterion | Spec ref |
|---|---|---|
| IMH→CBB propagation | IMH thermal event → DNS_EVENT_DELIVERY sent → CBB EMTTM PID input = TJMax → CBB frequency reduced | NWP IMH SoC PM MAS |
| CBB→IMH propagation | CBB thermal event → UPS_EVENT_DELIVERY sent → IMH fabric frequency = P1 | NWP IMH SoC PM MAS |
| Hard throttle wire | FAST_THROTTLE_IN_0 asserted → remote die throttles within ~1ns (relative ordering) | DMR thermal flows |
| Recovery | Cross-die throttle deasserted → remote die resumes normal frequency within spec'd PID loop period | NWP IMH SoC PM MAS |

---

## Section 6: Corner Cases / Coverage

| Scenario | TC ID | Env | Verdict |
|---|---|---|---|
| IMH→CBB cross-die throttle (HPM) | TBD | XOS, FV | |
| CBB→IMH cross-die throttle (HPM) | TBD | XOS, FV | |
| Hard throttle wire (FAST_THROTTLE_IN_0) | TBD | XOS, FV | |
| D2D link in L1 → wake + throttle propagation | TBD | XOS, FV | |
| Cross-die throttle deassertion recovery | TBD | XOS, FV | |
| Both dies requesting cross-die throttle simultaneously | TBD | XOS, FV | |

---

## Section 8: Open Items

- Cross-die thermal requires **XOS** environment (IMH2+CBB together) — single-die HSLE insufficient
- Confirm D2D FAST_THROTTLE_IN_0 wire availability on NWP
- Determine if additional TCs needed for multi-CBB (cbb0 + cbb1) thermal isolation
