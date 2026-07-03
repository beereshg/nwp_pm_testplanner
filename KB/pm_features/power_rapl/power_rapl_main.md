# Power/RAPL — Main Flow

> **Status**: Restructured — NWP delta enriched from MCP HAS/MAS query
> **Parent**: [Power / RAPL](power_rapl_main.md)

## Baseline (DMR)

Power/RAPL is the umbrella for all **power limiting, current limiting, and proactive power management** features on NWP. It encompasses the full pipeline from power measurement (SVID telemetry) through firmware control (PID loops) to hardware enforcement (frequency clamping, fast throttle wires).

## HW Touchpoints

<!-- TODO: Extract from Legacy content or enrich via MCP HAS query -->
| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| | | | | |

## FW Touchpoints

<!-- TODO: Extract from Legacy content or enrich via MCP HAS query -->
| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| | | | | |

## OS Interfaces

<!-- TODO: Extract from Legacy content or enrich via MCP HAS query -->
| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| | | | | |

## NWP Delta

> **Authoritative source**: [NWP PM MAS — Major Changes from DMR](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/NWP_IMH_SOC_PM_MAS.html#major-changes-from-dmr-product)

**RAPL subsystem is supported on NWP** — only Socket RAPL (PL1/PL2). All other RAPL domains are ZBB'd and fused off.

### NWP Supported PM Features (from MAS §3)
1. Priority Core Turbo (PCT) profile for SST-TF
2. Pstates (HWP, range of P-states from Pn, P1, P0n, P04)
3. Core Cstates (C0, C1, C1e, C6)
4. Thermal Protection (ProcHot, Thermtrip, Memtrip)
5. **Socket RAPL** (PL1 with 1s TW; PL2 with 12ms TW) — *no change from DMR*
6. PkgS0, PkgS5 — *no change from DMR*
7. Max TDP 450W, Nominal TDP 350W
8. ITD on new digital domain [VCCFCFCAB]

### Summary Table

| Feature | NWP Status | ZBB HSD | Key Delta |
|---------|-----------|---------|----------|
| Socket RAPL (PL1/PL2) | **Supported** | — | No change from DMR, single NIO die |
| FastRAPL | **TBD** | — | Not in MAS §3 ZBB list — needs confirmation (part of Socket RAPL pipeline) |
| DRAM RAPL | **FUSED OFF** | [14025012732](https://hsdes.intel.com/appstore/article-one/#/article/14025012732) | Fused off on NWP |
| Platform RAPL (Psys) | **ZBB** | [22021155415](https://hsdes.intel.com/appstore/article/#/22021155415) | Not supported |
| PL4 (IccMax) | Supported | — | Punit/Pcode |
| PMAX | Supported | — | Reused |
| PEM | Supported | — | Reused |
| SIMPL | **ZBB** | — | ZBB'd per MAS §3 |
| RACL | **ZBB** | — | Single VCCIN, no per-VR current limiting needed |
| SVID | Supported/Modified | — | Single NIO topology |
| Memory PM (APD/PPD/SSR/DSREF) | **ZBB** | [22021155412](https://hsdes.intel.com/appstore/article/#/22021155412) | LPDDR6 — no APD, PPD, SSR, DSREF |
| Sideband PM | Supported/Limited | — | Memory flows removed |

### ZBB Features NOT Supported on NWP (from MAS §3)
1. No UFS — Mesh (Mem+IO) and CAB fixed at 2 GHz ([14024876702](https://hsdes.intel.com/appstore/article/#/14024876702))
2. No PkgC6 — no idle power requirements ([22021155362](https://hsdes.intel.com/appstore/article/#/22021155362), [22021155185](https://hsdes.intel.com/appstore/article/#/22021155185))
3. No PCIe L1 ([22021155368](https://hsdes.intel.com/appstore/article/#/22021155368))
4. No HSIO L0p ([22021155360](https://hsdes.intel.com/appstore/article/#/22021155360))
5. No UXI L1/L0p ([22021155419](https://hsdes.intel.com/appstore/article/#/22021155419))
6. No C2C accelerator link power savings
7. No Memory PM: APD/PPD, LPM1/2/3, SSR, SR ([22021155412](https://hsdes.intel.com/appstore/article/#/22021155412))
8. **No DRAM RAPL** — fused off ([14025012732](https://hsdes.intel.com/appstore/article-one/#/article/14025012732))
9. **No Platform RAPL / Psys** ([22021155415](https://hsdes.intel.com/appstore/article/#/22021155415))
10. No ADR ([22021155420](https://hsdes.intel.com/appstore/article/#/22021155420))
11. No SST-PP, SST-BF, SST-CP ([22021155414](https://hsdes.intel.com/appstore/article/#/22021155414))
12. No Favored Core / DCM ([22021155183](https://hsdes.intel.com/appstore/article/#/22021155183))
13. No TMUL ([22021155122](https://hsdes.intel.com/appstore/article/#/22021155122))

### Memory Subsystem PM Deltas
- MC issues self-refresh without clock stop prior to warm reset to flush commands/data
- Subchannel flip removed (DMR IMH2 MC0/1/4/5 ↔ HAMVF channel swap) — straight connectivity
- MMC removed → LP6 internal MCU
- Dedicated MCPLL per memstack (no PHY PLL sourcing)
- MSE MKTME keys reduced 2048 → 1028

### NWP PAS "Memory RAPL" Clarification
> NWP PAS mentions "RAPL via 12V rail sensor → e-fuse" for memory power calculation. This refers to **memory power measurement input to Socket RAPL** (aggregate SoC power), NOT a separate DRAM RAPL domain. DRAM RAPL as a standalone power-limiting feature is fused off per MAS §3.

## Legacy (Human-Curated Reference)

### NWP Spec Context
| Field | Value |
|-------|-------|
| HAS ref | NWP HAS: Socket RAPL (PL1 1s TW, PL2 12ms TW). Max TDP 450W, Nominal 350W |
| MAS ref | [NWP PM MAS §3](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/NWP_IMH_SOC_PM_MAS.html#major-changes-from-dmr-product): Socket RAPL only. ZBB: DRAM RAPL (fused off, [14025012732](https://hsdes.intel.com/appstore/article-one/#/article/14025012732)), Platform RAPL/Psys ([22021155415](https://hsdes.intel.com/appstore/article/#/22021155415)), SIMPL, FastRAPL, Fine Grained Energy |
| NWP delta | NWP 450W TDP. Only Socket RAPL. DRAM/Platform/SIMPL/FastRAPL/RACL all ZBB'd. |
| NWP supported | True (Socket RAPL only) |

### Architecture Summary

Power/RAPL is the umbrella for all **power limiting, current limiting, and proactive power management** features on NWP. It encompasses the full pipeline from power measurement (SVID telemetry) through firmware control (PID loops) to hardware enforcement (frequency clamping, fast throttle wires).

#### Power Limiting Hierarchy

```
 Time scale       Feature              Response
 ─────────────────────────────────────────────────────────
 ~500ns          PMax (HW)            Instant fast_throttle → Psafe freq clamp
 ~500ns          PL4 (SW→HW)          Customer power cap → adjusts PMax Vtrip thresholds
 ~1ms            Socket RAPL PL2      NN-PID → freq ceiling (12ms tau, burst power)
 ~1-5s           Socket RAPL PL1      NN-PID → freq ceiling (1-5s tau, sustained TDP)
 ~1ms            RACL (per-VR TDC)    NN-PID → freq ceiling (per-iMH, dual VCCIN)
 ~1ms            SIMPL/DFC            Proactive domain freq tradeoff (IccMax envelope)
 continuous      PEM                  Excursion monitoring + attribution (observability)
```

#### Key Architectural Properties

- **NN-PID everywhere**: DMR replaces classic PID with Neural Network PID (adaptive online training, no manual tuning) across all 9+ PID instances (Socket PL1/PL2, Platform PL1/PL2, DRAM, Fast RAPL, RACL, Thermal EMTTM, MemCLOS DRC). Backwards-compatible: learning_rate=0 → classic PID.
- **Dual VCCIN (DMR-AP)**: Two independent VRs (VCCIN_0: North iMH + CBB0/1, VCCIN_1: South iMH + CBB2/3) → per-VR PMax detection, per-VR RACL current limiting, independent SVID telemetry
- **Interface consolidation**: MSR and PECI PCS **deprecated** on DMR — writes silently dropped, reads return 0. All RAPL control via TPMI (in-band + OOB) and CSR (BIOS one-time)
- **Multi-threshold PMax**: 4 fuse-programmable Vtrip thresholds (Hard, Soft L1, Soft L2, FDD) with per-domain frequency ceilings
- **Proactive IccMax (SIMPL)**: Cross-die domain-priority frequency tradeoff to stay within PD IccMax.max envelope — complementary to reactive RAPL/RACL
- **NWP scope**: Only **Socket RAPL** is supported. DRAM RAPL, Platform RAPL/Psys, SIMPL, FastRAPL, Fine-Grained Energy are all **ZBB** (Zero-Based Budget)

#### FW Agent Topology

```
                    Root iMH (NIO on NWP)
                    ┌─────────────────────────────┐
                    │ Primecode (root)             │
                    │  • Runs all RAPL PIDs (PL1/PL2)  │
                    │  • Runs RACL PID (local VR)  │
                    │  • Resolves SIMPL policy     │
                    │  • SVID bus master           │
                    │  • PMax detection (local)    │
                    │  • PL4 Voffset computation   │
                    ├──────────┬──────────────────┤
                    │ HPM msgs │                  │
                    ▼          ▼                  │
              CBB0           CBB1                 │
              ┌──────────┐   ┌──────────┐        │
              │ PCode    │   │ PCode    │        │
              │  • Freq  │   │  • Freq  │        │
              │   enforce│   │   enforce│        │
              │  • PEM   │   │  • PEM   │        │
              │  • DFC   │   │  • DFC   │        │
              │  • PLR   │   │  • PLR   │        │
              └──────────┘   └──────────┘        │
                                                  │
              SVID Bus ◄──────────────────────────┘
              VCCIN_EHV0/1 MBVRs (telemetry + VID)
```

#### HPM Message Flow

| Opcode | Message | Direction | Purpose |
|--------|---------|-----------|--------|
| 0x14-0x15 | `RAPL_PERF_LIMIT` | Root→CBBs | Frequency ceilings: RAPL PID output, RACL PID output, per-CLOS limits, PLR flags, FIVR input voltage |
| 0x16 | `LEAF_PERF_STATUS` | CBBs→Root | Performance counters: Socket RAPL, Platform RAPL, RACL throttle counts |
| 0x20 | `SIMPL` | Root→Leaves | SIMPL policy number + per-domain freq limits |
| 0x21 | `SIMPL_RESPONSE` | Leaves→Root | SIMPL ack + leaf BW request |
| — | `PMAX_FREQUENCY_LIMIT` | iMH→CBBs | Psafe frequency ceilings for hard PMax |
| — | `PMAX_INST_PWR_CONTROLLED_FREQ_LIMIT` | iMH→CBBs | Dynamic PMax soft throttle freq ceiling |
| — | `PL4_CONFIG` | Root→Leaf iMH | PL4 Voffset for PMax threshold reprogramming |

### FW Agents
- **Agents**: BIOS (CSR one-time config), PCode (CBB: freq enforcement, PEM, DFC, PLR, PMax fast_throttle), Primecode (iMH: RAPL/RACL PIDs, SIMPL, PL4, SVID master)
- **Interfaces**: TPMI (primary in-band + OOB), CSR (BIOS), HPM (inter-die), SVID (VR telemetry + voltage), b2p_mailbox (SST-PP)
- **HW Blocks**: PMax comparator (analog FIVR voltage sense), SVID bus + VRCI registers, TPMI BAR, FIVR/VR PVSA, Core PLL + GVFSM, MBE (memory bandwidth enforcement)
- **Sub-features**: Socket RAPL, Fast RAPL (Supported), PMAX/PL4, RACL, SIMPL/DFC (ZBB), PEM, SVID, MemCLOS/DRC + CLTT

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR RAPL Simplification](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html) | has_references.yaml → dmr.rapl |
| HAS | [DMR RAPL - Register Programming](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html#register-programming) | has_references.yaml → dmr.rapl |
| FAS | [DMR RAPL - Fast RAPL](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html#fast-rapl) | has_references.yaml → dmr.rapl |
| HAS | [DMR RAPL - PL2 Interface](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html#pl2-interface) | has_references.yaml → dmr.rapl |
| HAS | [DMR RAPL - Primecode Flow for RAPL and RACL](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html#primecode-flow-for-rapl-and-racl) | has_references.yaml → dmr.rapl |
| HAS | [Socket RAPL HAS (Wave3 Common)](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html) | has_references.yaml → dmr.rapl |
| HAS | [GNR RAPL Tuning Guide](https://docs.intel.com/documents/pm_doc/src/server/GNR/post_si/RAPL_Tuning/RAPL_Tuning_Guide.html) | has_references.yaml → dmr.rapl |
| HAS | [RACL / VR TDC (Dual VCCIN)](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Dual_VCCIN_RACL_VRTDC/RACL_VR_TDC.html) | has_references.yaml → dmr.rapl |
| HAS | [DMR PMax HAS (Multi-Threshold)](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PMax.html) | has_references.yaml → dmr.pmax |
| HAS | [DMR PMax HAS - BIOS Configuration](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PMax.html#bios-configuration) | has_references.yaml → dmr.pmax |
| HAS | [DMR PMax HAS - PL4](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PMax.html#pl4) | has_references.yaml → dmr.pmax |
| HAS | [DMR PMax HAS - Registers](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PMax.html#registers) | has_references.yaml → dmr.pmax |
| HAS | [TPMI HAS (Arch Common)](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html) | has_references.yaml → dmr.tpmi |
| HAS | [DMR SIMPL HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_SIMPL.html) | has_references.yaml → dmr.simpl |
| HAS | [DMR SIMPL - Policy Definitions](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_SIMPL.html#simpl-policy-definitions-for-dmr) | has_references.yaml → dmr.simpl |
| HAS | [DMR SIMPL - DFC Fuses](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_SIMPL.html#simpl-policy-mapping-and-fuses) | has_references.yaml → dmr.simpl |
| HAS | [Perf Limit Reasons HAS - MSR](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/perf_limit_reasons/perf_limit_reasons_has.html#msr) | has_references.yaml → dmr.plr |
| HAS | [Perf Limit Reasons HAS - PLR Die Level](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/perf_limit_reasons/perf_limit_reasons_has.html#plr_die_level) | has_references.yaml → dmr.plr |
| HAS | [HPM Message Specification](https://docs.intel.com/documents/primecode/has/DMR/Hierarchical%20PM/HPM_Message_Specification.html) | dmr_fw_architecture.yaml → spec_references.hpm_spec |
| HAS | [Primecode Firmware Specification](https://docs.intel.com/documents/primecode/has/DMR/index.html) | dmr_fw_architecture.yaml → spec_references.primecode_has |
| HAS | [DMR D2D PM Perimeter HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/D2D/DMR_D2D_Perimeter.html) | D2D PM feature interface table: GPIO pins (PROCHOT_N, THERMTRIP_N, FAST_THROTTLE |
| HAS | [DMR RAPL Simplification HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/Platform_PM_Features/RAPL/DMR_RAPL_Simplification.html) | MSR 0x610/611/613/614 ZBB'd in DMR (writes silently dropped, reads return 0). PE |
| HAS | [DMR Handling of Punit Registers for HPM](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Punit_registers.html) | Defines register scope categorization for HPM multi-die topology. MSR scopes: (1 |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM MAS — Socket RAPL only; DRAM/Platform/SIMPL/FastRAPL ZBB'd |
| HAS | [NWP BIOS HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/BIOS/NWP.html) | BIOS RAPL/PL knob configuration |
| Primecode src | TODO | |
| PCode src | TODO | |
| Test scripts | TODO | |
| SharePoint | TODO | |

### NWP Delta Summary

#### Supported Features
| Feature | NWP Status | Key Change from DMR |
|---------|-----------|--------------------|
| Socket RAPL (PL1/PL2) | **Supported** | Single NIO replaces dual iMH as PID host. NWP Max TDP 450W / Nominal TDP 350W (vs DMR 500W max). PL1 TW 1s, PL2 TW 12ms. 2 CBBs (vs 4) |
| PMax (Multi-Threshold) | **Supported** | Single VCCIN expected on NWP → single PMax detector (vs dual). Verify D2D fast_throttle wiring to 2 CBBs |
| PL4 | **Supported** | Same Voffset mechanism. Single VCCIN simplifies Itrip split |
| RACL | **Conditional** | Only needed if dual VCCIN. If single VCCIN → `FUSE_TDC_LIMIT=0` disables RACL |
| PEM (gen3) | **Supported** | Per-CBB, no cross-die. Same 32-event TPMI interface. Verify NWP Product ID in PMT GUID |
| SVID | **Supported** | NIO is sole SVID bus master. LPDDR6 may change MBVR VR count/addressing |
| MemCLOS/DRC + CLTT | **Supported** | LPDDR6 MR4 thermal throttling. Verify MBE HW (LRM vs leaky bucket) on NWP Punit |
| Sideband | **Supported** | Minimal — 1 PSS test case |
| Fast RAPL | **Supported** | Sub-ms PEM/SVID IMON power excursion response; 500 µs PID loop; CBB TPMI `pem_status.fast_rapl` bit; NWP has 2 CBBs. Disposition: Runnable_On_N-1 |

#### ZBB Features (Not Validated on NWP)
| Feature | Reason |
|---------|--------|
| DRAM RAPL | ZBB — no DRAM RAPL domain |
| Platform RAPL / Psys | ZBB — no platform-level power domain |
| SIMPL / DFC | ZBB — proactive IccMax tradeoff not scoped |
| Fine-Grained Energy Reporting | ZBB — per-FIVR domain energy (disabled at PRQ) |

> **Note:** Fast RAPL is **Supported** on NWP (not ZBB). It was incorrectly listed here in earlier KB drafts. FV team confirmed via child TCs 22022421939 and 22022421944 (disposition: Runnable_On_N-1).

#### NWP-Specific Risks
- **NIO as sole controller**: All RAPL PIDs, SVID, PL4, and SIMPL policy on a single new die — no IMH0↔IMH1 redundancy or split
- **LPDDR6 MBVR topology**: Different VR count, SVID addresses, and IMON mapping vs DDR5. Verify SVID enumeration and telemetry accumulator configuration
- **2-CBB fan-out**: HPM `RAPL_PERF_LIMIT` and `LEAF_PERF_STATUS` to/from 2 CBBs (vs 4). Verify PID output scaling and per-CLOS distribution
- **NN-PID tuning**: NWP power/freq profiles differ — NN-PID weights trained on DMR may need re-validation on NWP power envelope
- **PMax single VCCIN**: If NWP is single-VCCIN, only one PMax detector exists → no per-iMH independence

### Related Sightings
<!-- TODO: Add additional DMR retrospective sightings -->

### Subflows — Status & Test Case Summary

| # | Subflow | Status | TCs | FV | PSS | PV | Key NWP Notes |
|---|---------|--------|-----|----|----|----|--------------|
| 1 | [Socket RAPL](socket_rapl.md) | Enriched | 52 | 31 | 10 | 11 | Core feature — NN-PID, TPMI, CSR. NIO sole host |
| 2 | [PMAX](pmax.md) | Enriched | 17 | 14 | 3 | — | Multi-threshold PMax + FIVR energy reporting |
| 3 | [RACL](racl.md) | Enriched | 16 | 14 | — | 2 | Per-VR TDC limiter. Conditional on dual VCCIN |
| 4 | [SIMPL](simpl.md) | Enriched | 10 | 8 | 2 | — | **ZBB on NWP** — DFC subset may still apply |
| 5 | [PEM](pem.md) | Enriched | 17 | 4 | 3 | 10 | gen3 excursion monitor, 32 events, TPMI-only |
| 6 | [SVID](svid.md) | Enriched | 5 | 5 | — | — | SVID bus protocol, VRCI, telemetry |
| 7 | [Memory PM](memory_pm.md) | Enriched | 4 | — | 4 | — | MemCLOS/DRC + CLTT |
| 8 | [PL4](pl4.md) | Enriched | 2 | — | — | 2 | Customer power cap → PMax Vtrip offset |
| 9 | [Sideband](sideband.md) | Enriched | 1 | — | 1 | — | Sideband harasser — periodic IOSF stress generator |
| — | ~~Pstate-PEM~~ | **Missing** | 6 | — | — | — | `pstate_pem.md` not found — broken link, TCs unaccounted |
| | **Total** | 9/9 enriched | **130** | **76** | **23** | **25** | |
