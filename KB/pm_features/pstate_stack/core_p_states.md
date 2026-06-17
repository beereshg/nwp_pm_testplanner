# PState Stack > Core P-States

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [P-State Stack](pstate_stack_main.md)

## Baseline (DMR)

**What it does**: Core P-states define discrete V/F operating points anchored at **Pn** (LFM/max efficiency), **P1** (guaranteed base), **P0n** (Turbo Ratio Limit), and (NWP-new) **P04** (P0n÷4 minimum HWP guardrail). PCode arbitrates among HWP, legacy PERF_CTL, PEGA, and OOB requestors and commands FIVR+PLL for each GV transition.

**Topology**:
```
OS ──IA32_HWP_REQUEST (MSR 0x774)────────> CBB PCode PEGA engine
OS ──IA32_PERF_CTL (MSR 0x199) (legacy)─> (arbitration)
OOB ──TPMI P-state MMIO────────────────>     │
PEGA internal autonomous req ────────────>    │
                                              ▼
                                     Resolved target ratio
                                    (thermal limits, ICCP, EET, power)
                                              │
                              ┌───────────────┼───────────────┐
                              ▼               ▼               ▼
                        Core FIVR      Core PLL        IA32_PERF_STATUS
                       (voltage)     (frequency)         (MSR 0x198)
```

**Key operational principle**: PEGA evaluates EPP/EPB hints, thermal headroom, and power limits to compute an autonomous recommendation. Final ratio = min(all constraints). GV (Geyserville) transition: FIVR targets new voltage, PLL transitions frequency. APERF/MPERF counters track effective vs requested frequency ratio over time.

**Boot activation**: BIOS programs fused P-state limits (Pn, P1, P0n) at POST; sets `IA32_PM_ENABLE` HWP enable. P-states active from CPL3 handoff. NWP adds P04 = P0n÷4 as firmware-enforced HWP_REQUEST minimum (NWP PM MAS §3).

Core P-states define the discrete voltage/frequency operating points available to each CPU core. The P-state hierarchy is anchored by four named reference points: **Pn** (maximum efficiency/LFM ratio), **P1** (guaranteed/base frequency), **P0n** (Turbo Ratio Limit — highest turbo ratio), and for NWP, **P04** (P0n ÷ 4 — minimum HWP ratio guardrail). Each P-state maps to a specific voltage-frequency pair on the V/F curve, with PCode managing the actual voltage and PLL frequency transitions.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| Core FIVR | CBB Top Die | Per-core voltage regulator; targets voltage for each GV transition; isochronously coordinated with PLL | FIVR control signals; GV done | CBB PM HAS |
| Core PLL | CBB Top Die | Per-core frequency generation; transitions to target ratio on GV command | PLL lock signal; ratio control | CBB PM HAS |
| APERF / MPERF counters | CBB Top Die | Track actual (APERF) vs maximum (MPERF) frequency over a window; used to compute effective frequency | `APERF` CR; `MPERF` CR | Intel SDM |
| TPMI P-state | Per IMH | OOB P-state request path (BMC-initiated); writes to TPMI registers that PCode arbitrates alongside HWP requests | TPMI MMIO; OOBMSM VSEC BAR | TPMI HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core CCP | No direct P-state request; informs PCode of workload characteristics via SHORT_TELEM | SHORT_TELEM feedback | ACP PM HAS |
| PCode / PEGA (CBB) | CBB Base Die | Arbitrates HWP, PERF_CTL, PEGA autonomous, OOB requestors; resolves final target ratio applying thermal/ICCP/EET/power constraints; commands FIVR+PLL for GV; updates IA32_PERF_STATUS | PEGA engine; `source/pcode/flows/pega/`; `source/pcode/flows/autonomous_pstate/` | [CBB PEGA HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html) |
| PrimeCode (IMH) | IMH die | Propagates package-scope frequency limits (fabric, power limits) to CBBs via HPM; no direct per-core ratio control | HPM `DNS_EVENT_DELIVERY`; power limit HPMs | DMR SoC PM HAS |
| BIOS / UEFI | Platform | Programs fused P-state limits (Pn, P1, P0n); enables HWP via `IA32_PM_ENABLE[0]`; configures PEGA knobs; programs turbo via B2P mailbox | Boot-time MSR/mailbox programming | Intel SDM |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `IA32_PM_ENABLE` | 0x770 | RW | [0] `HWP_ENABLE` — enables Hardware P-states; write-once per boot | Intel SDM |
| MSR `IA32_HWP_CAPABILITIES` | 0x771 | RO | `HIGHEST_PERFORMANCE[7:0]`=P0n; `GUARANTEED_PERFORMANCE[15:8]`=P1; `MOST_EFFICIENT_PERFORMANCE[23:16]`=Pn; `LOWEST_PERFORMANCE[31:24]` | Intel SDM |
| MSR `IA32_HWP_REQUEST` | 0x774 | RW | `MIN_PERFORMANCE[7:0]`; `MAX_PERFORMANCE[15:8]`; `DESIRED_PERFORMANCE[23:16]`; `EPP[31:24]` — OS P-state request | Intel SDM |
| MSR `IA32_PERF_CTL` | 0x199 | RW | [15:8] target ratio (legacy PERF_CTL; lower priority than HWP) | Intel SDM |
| MSR `IA32_PERF_STATUS` | 0x198 | RO | [15:8] current operating ratio | Intel SDM |
| TPMI P-state | TPMI_ID (OOB_PKG) | RW (BMC) | OOB P-state min/max/desired override via BMC | TPMI HAS |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| GV (voltage/frequency) transition | ~few | μS | Core FIVR + PLL isochronous transition per GV event | Legacy Execution Flow |
| HWP PEGA evaluation period | ~1 | mS | PCode slow-loop; resolves final target ratio per CBB | Legacy Execution Flow |
| P04 minimum guardrail (NWP) | P0n ÷ 4 | ratio units | Firmware rejects HWP_REQUEST min below P04; NWP-only addition | [NWP PM MAS §3](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) |
| P-state hierarchy points | 4 | — | Pn (LFM), P1 (guaranteed), P0n (turbo max), P04 (HWP min; NWP only) | Legacy NWP Pstate Range table |
| APERF/MPERF effective freq | Ratio | — | APERF/MPERF measured per window; reflects actual vs requested | Intel SDM |

## NWP Delta

**Core P-states are fully supported on NWP server** — reused from DMR with no changes.

- PantherCove (PNC) BigCore reused from DMR — same P-state capability
- CBB PM flows all leveraged from DMR — "no plans to add nor deprecate any CBB PM flow" (NWP PM MAS)
- HWP (Hardware P-states) fully supported
- 2 CBBs (vs 4 in DMR) — 96 cores max (48 per CBB) vs up to 192 in DMR-AP
- Single NIO die (derivative of IMH2) — P-state coordination simplified (1 root)

### Topology Impact
- Fewer cores → different turbo ratio profiles (fuse-dependent, not algorithm change)
- SST-PP/BF/CP removed on NWP → no SST-level P-state cross-products
- Same P-state MSR interfaces, same TPMI, same mailbox

## Legacy (Human-Curated Reference)

### Architecture Summary

Core P-states define the discrete voltage/frequency operating points available to each CPU core. The P-state hierarchy is anchored by four named reference points: **Pn** (maximum efficiency/LFM ratio), **P1** (guaranteed/base frequency), **P0n** (Turbo Ratio Limit — highest turbo ratio), and for NWP, **P04** (P0n ÷ 4 — minimum HWP ratio guardrail). Each P-state maps to a specific voltage-frequency pair on the V/F curve, with PCode managing the actual voltage and PLL frequency transitions.

P-state requests can originate from multiple sources: the OS via HWP MSRs (MSR 0x774 HWP_REQUEST), legacy PERF_CTL (MSR 0x199), the PEGA (Performance and Energy Guided Autonomy) engine within PCode, or Out-of-Band (OOB) management via TPMI. PCode arbitrates among all requestors and resolves the final target ratio, then initiates the core PLL frequency change and FIVR voltage transition.

The resolved P-state is reflected in MSR 0x198 (IA32_PERF_STATUS), which reports the current operating frequency ratio. Validation confirms that requested P-states are correctly applied and observable, and that the arbitration logic correctly prioritizes among competing requests from PEGA, HWP, and OOB interfaces.

### Execution Flow

1. **BIOS Configuration** — BIOS programs fused P-state limits (Pn, P1, P0) into platform registers during boot. Turbo enable, HWP enable, and PEGA configuration are set via BIOS knobs.
2. **OS/OOB Request** — OS writes desired P-state via HWP_REQUEST (MSR 0x774) or legacy PERF_CTL (MSR 0x199). Alternatively, OOB management writes via TPMI P-state control registers.
3. **PEGA Arbitration** — PCode's PEGA engine evaluates workload characteristics, EPP/EPB hints, thermal headroom, and power limits to compute an autonomous P-state recommendation.
4. **P-state Resolution** — PCode resolves the final target ratio from all requestors (OS, OOB, PEGA internal) considering turbo limits, ICCP license, EET, and thermal constraints.
5. **Voltage/Frequency Transition** — PCode commands the core FIVR to target voltage and the core PLL to target frequency. The GV (Geyserville) transition completes in microseconds.
6. **Status Reporting** — Updated frequency is reflected in IA32_PERF_STATUS (MSR 0x198). Performance counters (APERF/MPERF) track actual vs requested frequency over time.

### Key Registers & Interfaces

| Register / MSR | Address | Description |
|----------------|---------|-------------|
| IA32_PERF_STATUS | MSR 0x198 | Current P-state ratio (read-only) |
| IA32_PERF_CTL | MSR 0x199 | Legacy P-state request (write) |
| IA32_HWP_REQUEST | MSR 0x774 | HWP min/max/desired ratio + EPP |
| IA32_HWP_CAPABILITIES | MSR 0x771 | HWP guaranteed/highest/lowest/efficient ratios |
| IA32_PM_ENABLE | MSR 0x770 | HWP enable bit |
| PEGA control | PCode internal | PEGA autonomous P-state engine configuration |
| TPMI P-state | TPMI MMIO | OOB P-state request interface |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [Core P-State HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) | P-state hierarchy and arbitration |
| HAS | [DMR CBB PEGA HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html) | PEGA autonomous P-state engine |
| HAS | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) | CBB power management overview |
| MAS | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP P-state specification |
| PCode src | `source/pcode/flows/autonomous_pstate/` | Core P-state flow implementation |
| PCode src | `source/pcode/flows/pega/` | PEGA engine |

### NWP Pstate Range (from PM MAS §3)

The NWP PM MAS explicitly defines the HWP operating range across four named reference points:

| Point | Definition | Source |
|-------|------------|--------|
| **Pn** | Maximum efficiency ratio — LFM (lowest operating frequency, best power) | Xeon 25/26 RCF HAS §6.2.11.1 |
| **P1** | Guaranteed ratio — base/non-turbo maximum frequency | RCF HAS, `HWP_CAPABILITIES.Guaranteed_Performance` |
| **P0n** | Turbo Ratio Limit (TRL) — max turbo the part supports | `IA32_HWP_CAPABILITIES.Highest_Performance` |
| **P04** | P0n ÷ 4 — minimum HWP ratio guardrail enforced by firmware | NWP PM MAS §3; Xeon 25/26 RCF HAS |

> **P04 (P0n/4)** is a NWP-specific addition. Firmware prevents the HWP minimum performance field from being set below P0n/4. Example: if P0n = 40 (4.0 GHz), P04 = 10 (1.0 GHz).
>
> Source: [NWP IMH SOC PM MAS §3 — PM Features Changes](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)

### Related Sightings

No P-state-specific sightings identified for NWP at this time. DMR sightings related to P-state request/status mismatch should be monitored during NWP bring-up.

### NWP Delta

| Aspect | DMR | NWP | Notes |
|--------|-----|-----|-------|
| P-state hierarchy | Pn, P1, P0n | Pn, P1, P0n, **P04** | NWP PM MAS §3 explicitly adds P04 (= P0n/4) as minimum HWP ratio guardrail — new vs DMR |
| PEGA engine | Supported | Supported | Same autonomous P-state flow |
| HWP interface | MSR 0x770-0x774 | Same | No MSR changes |
| OOB via TPMI | Supported | Supported | Same TPMI interface |
| Core PLL | CBB core PLL | NWP core PLL | Different PLL IP, same interface |
