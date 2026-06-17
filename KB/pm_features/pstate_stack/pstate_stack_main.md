# Pstate Stack — Main Flow

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [P-State Stack](pstate_stack_main.md)

## Baseline (DMR)

**What it does**: The P-state stack encompasses all mechanisms that control and report core operating frequency and voltage. It spans 15 sub-features covering the full frequency hierarchy (Pn → P1 → P0n → P04 → P01), V/F curve management, HWP autonomous selection, legacy OS-directed control, turbo boost, ICCP license arbitration, EET efficiency-based attenuation, EPB/EPP hints, flex ratio, PLR reporting, and the mailbox interfaces. Three firmware agents (Acode, PCode/PEGA, PrimeCode) collaborate to resolve, execute, and report every P-state transition.

**Topology**:
```
OS/BMC inputs:
  IA32_PERF_CTL (0x199) — legacy ratio request
  IA32_HWP_REQUEST (0x774) — HWP min/max/desired/EPP
  TPMI (OOB) — BMC power policy override
                 ↓
         PCode PEGA engine (CBB, ~1 mS slow loop)
           inputs: ICCP license | EET efficiency | EPB/EPP | thermal limit | PL1/PL2
           resolved_ratio = min(TRL[active_cores], ICCP_cap, EET_cap, thermal, power)
           clamp: max(P04, resolved_ratio)  [NWP: P04 = P0n/4 minimum guardrail]
                 ↓
         Acode (core perimeter GV sequence)
           voltage-first up, frequency-first down via Core FIVR + PLL
                 ↓
  IA32_PERF_STATUS (0x198) — current ratio (OS observability)
  PLR (MSR 0x64F) — which constraint limited turbo (diagnostic)
```

**Key operational principle**: PCode PEGA is the single arbiter for all frequency decisions — OS hints (HWP_REQUEST, PERF_CTL) are inputs, not direct commands. PEGA enforces TRL, ICCP, EET, thermal, and power constraints on top of OS requests. All limiting reasons are reported transparently via PLR. OOB TPMI interfaces allow BMC to override OS requests without OS cooperation.

**Boot activation**: BIOS enables HWP (`IA32_PM_ENABLE[0]`=1), configures PL1/PL2, programs ACPI _PSS, reads fuse TRL/VIDs. PCode initializes PEGA, V/F table, and turbo range at early init. P-state stack is active from CPL3 handoff.

The P-state stack defines the complete hierarchy of core frequency/voltage operating points and the firmware agents that manage transitions between them. The stack spans from Pn (minimum efficiency ratio) through P1 (guaranteed base frequency) to P0 (maximum turbo), with turbo sub-ratios P0n (n-core turbo) down to P04 (4-core turbo) and P01 (single-core max turbo). Each operating point maps to a voltage on the V/F curve, with PCode managing all transitions through the core FIVR and PLL.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| Core FIVR (Fully Integrated VR) | CBB Top Die | Executes voltage transitions on each GV; voltage-first on upward, follows frequency on downward transitions | VID bus from Acode/PCode; core voltage rail | CBB PM HAS |
| Core PLL | CBB Top Die | Executes frequency transitions (GV); receives ratio command from Acode; lock signal gating | PLL ratio control; PLL lock | CBB PM HAS |
| APERF / MPERF counters | Per-core | Track actual vs max-rate cycles; APERF/MPERF ratio = effective frequency utilization observable by OS | APERF CR (0xE8); MPERF CR (0xE7) | Intel SDM |
| TRL fuse register | IMH die | Stores fused max turbo per active core count (1..N); basis for turbo headroom in PEGA | Fuse read at boot | CBB PM HAS |
| TPMI SRAM | Per IMH | OOB-accessible P-state and turbo control registers (HWP, TRL, EPB, PLR); BMC power management interface | TPMI MMIO; OOBMSM BAR | TPMI HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core CCP | Executes core GV (Geyserville) transitions at Core FIVR + PLL level; provides SHORT_TELEM workload feedback (IPC, cache miss, PCNT/ACNT) to PCode PEGA engine | GV sequence; SHORT_TELEM push (~102.4μS) | [ACP PM HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Autonomous%20Core%20Perimeter/Autonomous%20Core%20Perimeter%20PM%20HAS.html) |
| PCode / PEGA (CBB) | CBB Base Die | Central P-state arbiter: reads OS HWP_REQUEST / PERF_CTL / TPMI OOB; applies TRL + ICCP + EET + EPB/EPP + thermal + power constraints; resolves final ratio; enforces P04 minimum (NWP); manages turbo (1CPM, PCT); updates PLR; commands Acode for GV | `source/pcode/flows/autonomous_pstate/`; `source/pcode/flows/pega/`; `source/pcode/flows/hwpm/` | [CBB PEGA HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html) |
| PrimeCode (IMH) | IMH die | Manages package-level power limits (PL1/PL2) that propagate as turbo headroom constraints to CBB PCode; configures turbo ratio limits; no per-core frequency decisions | `src/flow/turbo/`; HPM power limit interface | DMR SoC PM HAS |
| BIOS / UEFI | Platform | Enables HWP (`IA32_PM_ENABLE`=1); programs TRL overrides; sets PL1/PL2; configures 1CPM/PCT/EET knobs; populates ACPI _PSS; reads fuse VIDs for thermal planning | Boot-time MSR writes; ACPI tables; BIOS knobs | Intel SDM |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `IA32_PERF_CTL` | 0x199 | RW | Legacy P-state: OS writes target ratio directly; PCode executes GV (HWP off) | Intel SDM |
| MSR `IA32_PERF_STATUS` | 0x198 | RO | Current operating ratio — primary OS frequency observability register | Intel SDM |
| MSR `IA32_PM_ENABLE` | 0x770 | RW | [0] HWP enable — write-once per boot; activates PEGA autonomous mode | Intel SDM |
| MSR `IA32_HWP_REQUEST` | 0x774 | RW | HWP: [7:0] Min (≥P04 on NWP); [15:8] Max; [23:16] Desired (0=auto); [31:24] EPP | Intel SDM |
| MSR `IA32_CORE_PERF_LIMIT_REASONS` | 0x64F | RO/RW1C | Die-level PLR: status + sticky log bits for all active turbo limiting reasons | Intel SDM; PLR HAS |
| TPMI P-state registers | TPMI MMIO | RW (BMC) | OOB HWP request, TRL override, EPB, PLR — full P-state management without OS | TPMI HAS |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| PEGA evaluation period | ~1 | mS | PCode slow loop evaluates all P-state constraints and resolves target ratio | Legacy Architecture Summary |
| GV transition latency | ~few | μS | Core FIVR + PLL transition per ratio change; Fast GV reduces latency | Legacy FW Agents |
| P-state hierarchy levels | Pn, P1, P0n, P04, P01 | — | NWP explicitly adds P04 = P0n÷4 as minimum HWP guardrail (PM MAS §3) | Subflow pstate_hwp.md NWP Delta |
| SHORT_TELEM push period | ~102.4 | μS | Acode pushes workload telemetry to PCode for PEGA inputs | ACP PM HAS |
| Active P-state subflows | 15 | — | 14 enriched + pstate_pem.md (skeleton); 43 TCs total across all subflows | Subflows table above |
| NWP CBB PM delta | None | — | "No plans to add nor deprecate any CBB PM flow" — NWP PM MAS §2 | Legacy Architecture Summary |

## NWP Delta

**P-state stack is fully supported on NWP server** — all features reused from DMR with no additions or deprecations.

### Summary Table

| Feature | NWP Status | Key Delta |
|---------|-----------|-----------|
| Core P-states / HWP | Supported | No change |
| HGS / Thread Director | Supported | No change |
| P-state Mailbox | Supported | No change |
| ICCP / Cdyn Fitting | Supported | No change |
| DCM FIT | Supported | No change |
| EET | Supported | No change |
| EPB / SAPM DLL | Supported | No change |
| Flex Ratio | Supported | No change |
| Guaranteed Ratio (P1) | Supported | No SST-PP level variation |
| Legacy P-states (EIST) | Supported | No change |
| PLR | Supported | Some bits never assert (removed features) |
| Turbo Mode / TRL | Supported | Different TRL profile (96 cores vs DMR) |
| V/F Curve | Supported | No SST-PP V/F variation |

### Architecture-Level Deltas
- **All CBB PM flows reused** — "no plans to add nor deprecate any CBB PM flow" (NWP PM MAS)
- **PantherCove BigCore reused** — same P-state capability per core
- **2 CBBs** (vs 4 in DMR) — 96 cores max, different TRL fuse profile
- **Single NIO** (derivative of IMH2) — simplified P-state coordination
- **SST-PP/BF/CP removed** — no SST-level P-state cross-products
- **No PkgC6** — removes PkgC6↔P-state interaction tests

## Legacy (Human-Curated Reference)

### NWP Spec Context
| Field | Value |
|-------|-------|
| HAS ref | NWP HAS: HWP, P-states (Pn, P1, P0n, P04), PEGA, Legacy |
| MAS ref | NWP PM MAS: Full P-state stack supported. No change from DMR. |
| NWP delta | No delta. Full P-state support. HGS ZBB'd. DCM FIT N/A (monolithic). |
| NWP supported | True |

### Architecture Summary

The P-state stack defines the complete hierarchy of core frequency/voltage operating points and the firmware agents that manage transitions between them. The stack spans from Pn (minimum efficiency ratio) through P1 (guaranteed base frequency) to P0 (maximum turbo), with turbo sub-ratios P0n (n-core turbo) down to P04 (4-core turbo) and P01 (single-core max turbo). Each operating point maps to a voltage on the V/F curve, with PCode managing all transitions through the core FIVR and PLL.

Three firmware agents collaborate in the P-state stack: **PCode** (CBB power management microcontroller) owns autonomous P-state selection via the PEGA engine, turbo ratio limit enforcement, ICCP license management, EET, and PLR reporting. **Acode** (core perimeter microcode) handles core-level GV (Geyserville) transitions — the actual voltage/frequency change sequence at the core PLL/FIVR level. **Primecode** (package-level firmware) manages package power limits (PL1/PL2), turbo ratio limit configuration, and cross-die coordination (DCM FIT on multi-die products).

P-state requests enter the stack from three interfaces: **MSR interface** (OS writes to PERF_CTL or HWP_REQUEST), **TPMI interface** (OOB/BMC writes for remote management), and **PCode-internal PEGA engine** (autonomous selection based on workload, efficiency, thermal, and power inputs). PCode arbitrates among all inputs and resolves the final target ratio, considering turbo limits (TRL), ICCP license, EET attenuation, flex ratio, SST-PP level, thermal constraints, and power limits. The resolved frequency is reflected in IA32_PERF_STATUS (MSR 0x198) and any limiting reasons are logged in PLR registers (MSR 0x64F).

On NWP, the full P-state stack is supported with no architectural delta from DMR. HGS (Hardware-Guided Scheduling) is ZBB'd and DCM FIT is N/A since NWP is monolithic. All other sub-features — HWP, Legacy P-state, Turbo, ICCP, EET, EPB/EPP, Flex Ratio, V/F curve, PLR — are fully supported.

**NWP CBB PM flows**: Per NWP PM MAS §2, **NWP CBB PM flows are 100% reused from DMR CBB** — "no plans to add nor deprecate any CBB PM flow." The only CBB changes for NWP are UCIe D2D upgraded to 32 GT/s and buffer/queue size increases. The CBB CCF GV operates in **NonAutoGV mode** (same as DMR) — CCF does not autonomously select workpoints; instead it responds to the target workpoint written to `CCF_WP` register by Pcode.

### FW Agents
- **PCode** — Autonomous P-state selection (PEGA), turbo management, ICCP, EET, PLR reporting
- **Acode** — Core GV transitions (voltage/frequency change at core PLL/FIVR)
- **Primecode** — Package power limits, turbo ratio limit configuration, cross-die coordination
- **Interfaces**: MSR (0x198/0x199/0x770-0x777), TPMI (OOB), B2P/OS2P mailbox
- **HW Blocks**: Core PLL, FIVR, DLVR, PEGA engine

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [Core P-State HAS (Wave3 Common)](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) | P-state hierarchy, MSR definitions |
| HAS | [DMR Turbo HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html) | Turbo, TRL, PCT, 1CPM |
| HAS | [DMR Turbo — Priority Core Turbo (PCT)](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html#priority-core-turbo-pct) | PCT specification |
| HAS | [DMR Turbo — Module Turbo (1CPM)](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html#module-turbo-1-core-per-module) | 1CPM specification |
| HAS | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) | CBB PM overview |
| HAS | [DMR CBB PEGA HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html) | PEGA autonomous P-state engine |
| HAS | [DMR CCB Power Management HAS Index](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/index.html) | CBB PM HAS index |
| HAS | [DMR ICCP HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_ICCP.html) | ICCP license levels |
| HAS | [Perf Limit Reasons HAS — MSR](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/perf_limit_reasons/perf_limit_reasons_has.html#msr) | PLR MSR bit definitions |
| HAS | [Perf Limit Reasons HAS — PLR Die Level](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/perf_limit_reasons/perf_limit_reasons_has.html#plr_die_level) | Die-level PLR |
| HAS | [NWP BIOS HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/BIOS/NWP.html) | BIOS P-state/turbo knobs |
| HAS | [Autonomous Core Perimeter (ACP) PM HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Autonomous%20Core%20Perimeter/Autonomous%20Core%20Perimeter%20PM%20HAS.html) | Acode-driven GV transitions |
| HAS | [NWP CBB HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/cbb/nwp_cbb.html) | NWP CBB delta from DMR — confirms no PM flow changes; 48 cores/CBB, UCIe D2D 32 GT/s |
| HAS | [NWP CBB CCF HAS](https://docs.intel.com/documents/clientsilicon/dmr_cbb/global/ccf/nwp_ccf.html) | NWP CCF delta — PM unchanged; main difference is higher read/write BW to iMH |
| HAS | [DMR CBB CCF PMA PM HAS v1.0](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.1.0.html) | CCF GV (NonAutoGV mode), Ring C3/Fast Ring C3, FIVR control |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM MAS — full P-state stack |
| MAS | [PNC GV_CTRL MAS (Single FIVR)](https://intel.sharepoint.com/:w:/r/sites/TheLions/PNC/_layouts/15/Doc.aspx?sourcedoc=%7B58AA80A3-7B0F-4972-B40F-28D85D137E3F%7D) | PNC core PM / PMSB interaction |
| PCode src | `source/pcode/flows/autonomous_pstate/` | Core P-state and turbo flows |
| PCode src | `source/pcode/flows/pega/` | PEGA autonomous engine |
| PCode src | `source/pcode/flows/hwpm/` | HWP flow |
| Primecode src | `src/flow/turbo/` | Turbo ratio limit enforcement |

### Related Sightings

P-state stack sightings from DMR that should be monitored during NWP bring-up include: turbo ratio not reaching fused TRL, ICCP license grant timing, PLR bits stuck-on, HWP OOB vs native mode conflicts, APERF/MPERF counter accuracy drift, and V/F curve fuse mismatches. See individual subflow articles for per-feature sighting details.

### Subflows (14)

| # | Subflow | TCs | Status | Notes |
|---|---------|-----|--------|-------|
| 1 | [Core P-States](core_p_states.md) | 3 | Enriched | PSS: PEGA/HWP/OOB P-state request, PERF_STATUS |
| 2 | [HGS](hgs.md) | 2 | Enriched | PSS: HW Feedback bits — ZBB'd on NWP |
| 3 | [Mailbox](mailbox.md) | 1 | Enriched | PSS: B2P/OS2P mailbox sweep |
| 4 | [Pstate-Core ICCP](pstate_core_iccp.md) | 3 | Enriched | FV/PV: License L0–L4, AVX/AMX frequency caps |
| 5 | [Pstate-DCM FIT](pstate_dcm_fit.md) | 1 | Enriched | FV: Multi-die freq coordination — N/A on NWP |
| 6 | [Pstate-EET](pstate_eet.md) | 1 | Enriched | FV: Energy Efficient Turbo attenuation |
| 7 | [Pstate-EPB and SAPM-DLL](pstate_epb_and_sapm_dll.md) | 3 | Enriched | FV/PV: EPB/EPP sweep, SAPM-DLL voltage |
| 8 | [Pstate-Flex ratio](pstate_flex_ratio.md) | 2 | Enriched | FV/PV: BIOS flex ratio cap on P1 |
| 9 | [Pstate-Guaranteed Ratio P1](pstate_guaranteed_ratio_p1.md) | 1 | Enriched | FV: P1 resolution from fuses/flex/SST-PP/thermal |
| 10 | [Pstate-HWP](pstate_hwp.md) | 4 | Enriched | FV/PV: HWP native + OOB mode |
| 11 | [Pstate Legacy](pstate_legacy.md) | 7 | Enriched | FV/PV: PERF_CTL, Fast GV, counters, Solar |
| 12 | [Pstate-PEM](pstate_pem.md) | 3 | Skeleton | PEM sub-feature (not enriched in this pass) |
| 13 | [Pstate-PLR](pstate_plr.md) | 1 | Enriched | FV: Performance Limit Reasons MSR 0x64F |
| 14 | [Pstate-Turbo Mode](pstate_turbo_mode.md) | 9 | Enriched | FV/PV: TRL, 1CPM, PCT, turbo harasser |
| 15 | [Pstate-V-F curve](pstate_v_f_curve.md) | 2 | Enriched | FV: V/F fuses, Near TDP, DLVR |
