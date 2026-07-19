# CBB CCF Power Management — Main Flow

 > **Status**: T6 lineage + T2 WHAT-boundary + T1 coverage gap findings ingested (2026-07-18)
> **Source**: Co-Design `codesign-ask-specs-and-wikis` T6/T2/T1 queries

## Overview

CBB CCF Power Management controls the CCF (Converged Coherent Fabric) ring power state transitions
within each CBB die. The CCF PMA (Power Management Agent) is the central hardware agent that executes
C-state entry/exit sequences (C0 ↔ C3 ↔ C6), ring GV (working-point transitions for frequency/voltage),
PLL management, and register save/restore — orchestrated by PCode (CBB Punit) via PMSB messaging.

**NWP note**: NWP reuses DMR CBB silicon (CAB die). The CCF PMA architecture, registers, and
PCode interfaces are identical to DMR-SP. No NWP-specific CCF PM deltas have been identified.

## Generational Lineage (T6)

> Ingested from Co-Design T6 query 2026-07-18. Provenance per row; `no spec access` = Co-Design
> had no direct document for that generation.

### Known Aliases

| Era | Name(s) |
|-----|---------|
| Pre-ADL | CCF PM, Ring PM, Uncore PM (no CCF PMA agent — Punit drove ring transitions directly) |
| ADL+ | CCF PMA (CCF Power Management Agent), CCF PM |
| DMR+ | CBB CCF PM (CBB-scoped naming after chiplet split) |

### Lineage Table

| Generation | Change (interface/behavior/scope) | Interface impact | Spec ref (doc + clause, verbatim) | Source collection | Validation impact |
|---|---|---|---|---|---|
| SKL | no spec access | - | - | - | no spec access |
| GLC | no spec access | - | - | - | no spec access |
| PNC | no spec access | - | - | - | no spec access |
| PMR | no spec access | - | - | - | no spec access |
| GFC | no spec access | - | - | - | no spec access |
| **ADL** | Introduction of CCF PMA as central agent for CCF power management; Punit/Pcode interface via PMSB; CCF workpoint (`CCF_WP`) register controls C-state, VID, ratio, PS; Save/restore flows defined; MSR interface for legacy, MMIO for new flows | MSR + PMSB/CR interface; CCF_WP register; CCF PMA FSM; Save/restore via S/R FSMs | `pm-doc-src-adl-ip-integration-ccf-adl-ccf-pm.html` — "CCF PM Architecture", "CCF C3 and CCF C6 Entry/Exit" | ADL | **adapt** (test must use new CCF_WP, PMSB, and PMA flows) |
| **MTL** | DMU replaces Punit as CCF PMA interface; CCF PMC replaces PMA; `CCF_WP` register persists; Save/restore flows updated for INF-VNN domain; **TPMI interface introduced** for PM features | DMU/PMC interface; TPMI MMIO; CCF_WP register; S/R FSMs for INF-VNN | `pm-doc-src-mtl-ip-integration-ccf-mtl-ccf-pm.html` — "CCF PM Architecture", "CCF C3 and CCF C6 Entry/Exit" | MTL | **adapt** (test must use DMU/PMC and TPMI MMIO) |
| **LNL** | DMU/PMC interface continues; `CCF_WP` and `RESET_BYPASS_CFG` registers; S/R FSMs for INF-VNN; TPMI MMIO interface for PM features; CCF PMA FSMs for C-state transitions | DMU/PMC interface; TPMI MMIO; CCF_WP, RESET_BYPASS_CFG | `pm-doc-src-lnl-ip-integration-ccf-lnl-ccf-pm.html` — "CCF PM Architecture", "C3 C6 Entry/Exit", "RESET_BYPASS_CFG" | LNL | unchanged |
| **DMR** | CCF PMA as central agent; Punit interface via PMSB; `CCF_WP`, `RESET_BYPASS_CFG`, and `CCF_PMA_COMMAND` registers; S/R FSMs for VCCR; TPMI MMIO; Ring scalability and GV flows centralized in PMA | PMSB/CR interface; TPMI MMIO; CCF_WP, RESET_BYPASS_CFG, CCF_PMA_COMMAND | `pm-doc-src-dmr-cbb-ip-integration-ccf-cbb-ccf-pm-1-0.html` — "CCF PM Architecture", "CBB CCF C3 Entry/Exit", "RESET_BYPASS_CFG" | DMR_CBB | unchanged |
| **GNR** | Same as DMR — CCF PMA, PMSB, CCF_WP/RESET_BYPASS_CFG/CCF_PMA_COMMAND | PMSB/CR; TPMI MMIO | `pm-doc-src-dmr-cbb-ip-integration-ccf-cbb-ccf-pm-html` | GNR_wikis | unchanged |
| **CWF** | Same as DMR | PMSB/CR; TPMI MMIO | `pm-doc-src-dmr-cbb-ip-integration-ccf-cbb-ccf-pm-html` | CWF_wikis | unchanged |
| **COR** | Same as DMR | PMSB/CR; TPMI MMIO | `pm-doc-src-cor-cbb-ip-integration-ccf-cbb-ccf-pm-html` — "CCF PM Architecture", "CCF PMA Interfaces" | COR_CBB | unchanged |
| **NWP** | Same as DMR | PMSB/CR; TPMI MMIO | `pm-doc-src-dmr-cbb-ip-integration-ccf-cbb-ccf-pm-html` | NWP, NWP_wiki | unchanged |

### NWP Tail Summary

NWP inherits the DMR/COR/GNR/CWF CCF PMA architecture with PMSB/TPMI interfaces,
`CCF_WP`/`RESET_BYPASS_CFG`/`CCF_PMA_COMMAND` registers, and S/R FSMs for VCCR.
**No interface or behavioral delta from DMR/COR** — validation tests written for DMR/COR
are directly reusable for NWP. The major inflection points were **ADL** (feature introduction)
and **MTL** (DMU/PMC + TPMI migration).

### Key Registers (from lineage)

| Register | Offset | Key Fields | Introduced |
|----------|--------|------------|------------|
| `CCF_WP` (ccf_wp[7]) | 0x1138 | `TARGET_C_STATE` [14:11], `TARGET_VID` [10:0], `TARGET_MAX_RATIO` [24:16], `TARGET_PS` [31:29] | ADL |
| `RESET_BYPASS_CFG` | 0x1200 | Skip PLL reset, skip save/restore, skip LLC BIST (debug/survivability) | LNL |
| `CCF_PMA_COMMAND` | — | PMA command interface | DMR |

## HW Touchpoints

> To be enriched — pending full spec extraction.

## FW Touchpoints

> To be enriched — pending full spec extraction.

## OS Interfaces

> To be enriched — pending full spec extraction.

## NWP Delta

**None identified.** NWP reuses DMR CBB silicon; CCF PMA architecture, registers, and
PCode interfaces are identical per Co-Design lineage analysis.

## T2 WHAT-Boundary Findings

> Ingested from Co-Design T2 grouping query 2026-07-18.
> **Status**: Gap rows — no HSD writes pending. Requires human confirmation before any action.

### High Risk

| Finding | Spec ref | Current coverage | Action | Status |
|---|---|---|---|---|
| **TCD 22022421179 clubs 3 behaviors** — Fast Ring C3 (PLL ON), Ring C3 (PLL OFF, Q-channel deassert), C-state wake events (ia_distress update). Different expected outcomes and bars. | DMR CBB C State HAS §4.0; CCF PM HAS §"CCF PM States"; PkgC MAS §"Hold Ring Fast C3" | TC 22022422865, 22022422868, 22022422873 | Split into 3 TCDs: "CBB CCF Fast Ring C3", "CBB CCF Ring C3", "CBB CCF C-state Wake Events" | ✅ **DONE 2026-07-18** — TCD [16031169646](https://hsdes.intel.com/appstore/article-one/#/16031169646) (Fast Ring C3, TC 22022422865), TCD [16031169647](https://hsdes.intel.com/appstore/article-one/#/16031169647) (Ring C3, TC 22022422873). TC 22022422868 already under TCD 22022421209. Original TCD 22022421179 marked [SPLIT]. |
| **Uniform Fabric Frequency TCDs (22022421207–22022421218)** — 7 TCDs with no TCs, no WHAT/bar, bullet chars in titles. **Confirmed POR** (opt-in via BIOS/TPMI bit 30). Not ZBB — needs WHAT/bars and TCs. | Fabric DVFS HAS §"UNIFORM_CBB_FABRIC_FREQ_MODE"; UFS_CONTROL; HPM 0x1b messaging; NWP CBB HAS ("no plans to deprecate any CBB PM flow") | none | Define WHAT/bars; fix bullet-char titles; create TCs | *(ACTIONABLE — POR confirmed 2026-07-18)* |

### Medium Risk

| Finding | Spec ref | Current coverage | Action | Status |
|---|---|---|---|---|
| **Ring Scalability/Distress/Telemetry overlap** — 6 TCDs (22022421190–22022421205) test overlapping spec clauses with unclear WHAT boundaries | CCF PMA HAS §14–16; Ring Scalability MAS; P-state Stack HAS §"Ring distress" | TC 22022422886–22022422905 | Merge or clarify WHAT boundaries; consider "CBB CCF Ring Scalability/Distress/Telemetry Integration" | ✅ **DONE 2026-07-18** — Option B (sharpen, not merge). Titles updated to reflect data-path layers: PMON Counter Infrastructure → CBO Lookup Telemetry → SBO Snoop Telemetry → Distress Signal Path → Distress Grade Delivery → PCode Ring Scalability Algorithm. CBO TC SBO overlap noted for TC-level fix. |
| **PMON/CBO/SBO Telemetry overlap** — 3 TCDs (22022421190, 22022421194, 22022421202) test counter access/enable/disable with similar bars | CCF 1.0 HAS; CLR CBB Changes MAS | TC 22022422886, 22022422889, 22022422900 | Merge into "CBB CCF Telemetry Counters" or differentiate bars | ✅ **DONE 2026-07-18** — Kept separate (distinct spec layers: PMON events vs CBO lookup vs SBO snoop). Titles sharpened. TC 22022422889 needs SBO steps removed (covered by TC 22022422900). |
| **BIOS programming gap** — TCD 22022421165 TC only covers UncoreFreqCtrlCbb, not full UFS_CONTROL field programming | Fabric DVFS HAS; OakStream CpuPM FAS | TC 22022422850 | new TC [under TCD 22022421165] | *(TC TBD)* |
| **Multi-VF curve gap** — TCD 22022421174 TC doesn't cover all VF curve ratio points for all FIVRs | GVFSM MAS; DMR Fuse Specification | TC 22022422863 | new TC [under TCD 22022421174] | *(TC TBD)* |
| **Ring distress/telemetry fields** — no single TC covers all fields (ia_distress, snoop_level, etc.) | P-state Stack HAS; CCF PM 1.0 HAS | TC 22022422894, 22022422895, 22022422905 | new TC [under TCD 22022421197 or 22022421205] | *(TC TBD)* |

### Low Risk

| Finding | Spec ref | Current coverage | Action | Status |
|---|---|---|---|---|
| **TCD 22022421205 title typo** — "CCB" should be "CBB" | — | TC 22022422905 | Fix title | ✅ **DONE 2026-07-18** — Title updated to "CBB CCF PCODE algorithm for distress input" |
| **Per-die TPMI scoping** — TCD 22022421171 bar doesn't cite spec clause for per-die isolation | CBB TPMI HAS; CBB Overview HAS | TC 22022422859 | bar change [TCD 22022421171 §5] | *(TBD)* |

### Spec Refs for TCD §2 Linkage

> Copy these into TCD §2 (Functional Requirements) when actioning findings.

| TCD | Spec ref to add |
|---|---|
| 22022421165 | Fabric DVFS HAS; OakStream CpuPM FAS |
| 22022421168 | CCF PMA HAS; GVFSM MAS |
| 22022421171 | CBB TPMI HAS; CBB Overview HAS |
| 22022421174 | GVFSM MAS; DMR Fuse Specification |
| 22022421179 | DMR CBB C State HAS §4.0; CCF PM HAS §"CCF PM States"; PkgC MAS §"Hold Ring Fast C3" |
| 22022421183 | GVFSM MAS §"NonAutoGV/Fast GV" |
| 22022421190–22022421205 | CCF PMA HAS §14–16; Ring Scalability MAS; P-state Stack HAS §"Ring distress" |
| 22022421207–22022421218 | Fabric DVFS HAS §"UNIFORM_CBB_FABRIC_FREQ_MODE"; UFS_CONTROL |

## T1 Coverage Gap Findings

> Ingested from Co-Design T1 coverage gap audit 2026-07-18.
> **Status**: Gap rows — no HSD writes pending. Requires human confirmation before any action.
> 10 spec-defined behaviors have no TC coverage at any tier.

### High Risk

| Gap | Spec ref | Coverage | Tier | Action | Status |
|---|---|---|---|---|---|
| **No negative/boundary validation** — invalid UFS_CONTROL, out-of-range PEGA, bad TPMI values | NWP CCF HAS; DMR CBB HAS §3.2.8; Telemetry HAS "Negative Validation" | none | FV | new TCD [CBB CCF PM Negative/Boundary Validation] | *(TBD)* |
| **No CCF PMA save/restore** — S/R FSM, RESET_BYPASS_CFG.SKIP_SAVE_RESTORE, DFD_EN across C-state | DMR CBB CCF PM HAS "CCF PMA Save/Restore"; NWP CCF HAS | none | FV | new TCD [CBB CCF PMA Save/Restore Across C-State] | *(TBD)* |
| **No cross-die IMH↔CBB HPM coordination** — HPM 0x1b, 0x14, 0x15, Uniform Fabric Freq end-to-end | DMR Fabric DVFS HAS; DMR CBB HAS; NWP CCF HAS | none | FV | new TCD [CBB CCF Cross-Die HPM Coordination] | *(TBD)* |

### Medium Risk

| Gap | Spec ref | Coverage | Tier | Action | Status |
|---|---|---|---|---|---|
| **No state transition coverage** — enable→disable→re-enable for CCF PM features | DMR CBB HAS; DMR Reset Widget MAS; NWP Reset Construction MAS | none | FV | new TCD [CBB CCF PM State Transition Coverage] | *(TBD)* |
| **No RESET_BYPASS_CFG coverage** — SKIP_BIST, SKIP_PLL_RESET, SKIP_SAVE_RESTORE | DMR CBB CCF PM HAS "RESET_BYPASS_CFG"; NWP CCF HAS | none | FV | new TCD [CBB CCF RESET_BYPASS_CFG Debug/Survivability] | *(TBD)* |
| **No ELC modes** — UFS_CONTROL ELC fields, thresholds, ratios for CCF ring | DMR CBB HAS "Efficiency Latency Control"; Fabric DVFS HAS | none | FV | new TCD [CBB CCF ELC Modes] | *(TBD)* |
| **No abort handling** — PCode abort, LLC_COMMAND phase, CCF PMA FSM abort points | DMR CBB CCF PM HAS "Abort handling during C-state flows" | none | FV | new TCD [CBB CCF PMA Abort Handling During C-State Entry] | *(TBD)* |
| **No FIVR/PLL sequencing** — ordering, resource readiness, reset sequencing for ring GV | DMR CBB HAS "FIVR control"; NWP Reset Construction MAS | none | FV | new TCD [CBB CCF FIVR/PLL Sequencing for Ring GV] | *(TBD)* |
| **No error injection/recovery** — error registers, recovery flows, injection hooks | DMR RAS HAS; NWP RAS HAS; DMR CBB HAS | none | FV | new TCD [CBB CCF PMA Error Injection and Recovery] | *(TBD)* |

### Low Risk

| Gap | Spec ref | Coverage | Tier | Action | Status |
|---|---|---|---|---|---|
| **No CCF PMA command register** — CCF_PMA_COMMAND, block/unblock/monitor_copy | DMR CBB CCF PM HAS "CCF PMA Interfaces" | none | FV | new TCD [CBB CCF PMA Command Register Interface] | *(TBD)* |

### Structural Issues (from T1 hierarchy audit)

| Issue | Detail | Action |
|---|---|---|
| 3 telemetry TCs misparented | PMON (22022422886), CBO (22022422889), SBO (22022422900) under UFF TCD 22022421207 | ✅ **DONE 2026-07-18** — Re-parented: 22022422886→TCD 22022421190, 22022422889→TCD 22022421194, 22022422900→TCD 22022421202 |
| 1 C-state wake TC misparented | TC 22022422868 under UFF TCD 22022421209; script not implemented | move TC; implement script |
| 5 orphan TCDs | 22022421190, 22022421194, 22022421199, 22022421202, 22022421205 — titles updated but no TCs | ✅ **3/5 resolved** — 22022421190, 22022421194, 22022421202 now have TCs. 22022421199 and 22022421205 still orphaned. |
| TC 22022422896 deprecated | Merged into TC 22022422894 | close/archive |

## References

| Type | Link | Scope |
|------|------|-------|
| HAS | [DMR CBB CCF PM HAS v1.0](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.1.0.html) | CCF PMA architecture, C-state entry/exit, GV, S/R |
| HAS | [NWP CBB CCF HAS](https://docs.intel.com/documents/clientsilicon/dmr_cbb/global/ccf/nwp_ccf.html) | NWP-specific CCF deltas from DMR CBB |
| HAS | [DMR CBB Address Map](https://docs.intel.com/documents/ClientSilicon/DMR_CBB/global/NCU/CBBAddressMap.html) | CBB register address map |
