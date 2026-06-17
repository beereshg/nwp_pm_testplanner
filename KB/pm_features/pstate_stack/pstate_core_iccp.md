# Pstate Stack > Pstate-Core ICCP

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [P-State Stack](pstate_stack_main.md)

## Baseline (DMR)

**What it does**: ICCP (Intelligent Current/Capacitance Proxy) is a license-based current-limiter for AVX-512/AMX workloads. Heavy vector/matrix instructions draw significantly more current than scalar code, risking EDP exceedance. ICCP assigns 5 license levels (L0=unrestricted scalar → L4=heaviest AMX), each with a fused turbo ratio cap that decreases with workload intensity.

**Topology**:
```
Core ucode (AVX-512/AMX detected) ──HPM license request (level L0-L4)──> CBB PCode
  CBB PCode:
    ├── Cdyn estimator (NN-based dynamic capacitance proxy)
    ├── FIT (Frequency Integration Technology) coordination across cores
    ├── License arbitration: active-core count × level × package EDP
    └── Grant license → set per-core turbo ratio cap (fused limit for that level)
              │
        Core FIVR + PLL clamp to capped frequency (if currently above)
              │
    IA32_PERF_STATUS (MSR 0x198) reflects capped ratio
```

**Key operational principle**: License grants are per-core. PCode evaluates aggregate Cdyn (all active cores × their instructions) against package current envelope before granting. On L4 (heaviest AMX), ratio cap is lowest fused value. On license release (instruction phase ends), PCode restores L0 cap immediately.

**Boot activation**: Fused per-license ratio limits programmed by BIOS via B2P mailbox `AVX_ICCP_CONFIG` at POST. ICCP active from CPL3 handoff.

ICCP (Intelligent Current/Capacitance Proxy) is a license-based current-limiting mechanism for AVX/AMX workloads. Heavy vector/matrix instructions draw significantly more current than scalar code, potentially exceeding the package electrical design point (EDP). ICCP enforces per-core frequency caps based on the granted license level, preventing current exceedance while maximizing performance within safe limits.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| Core AVX/AMX execution unit | CBB Top Die | Executes AVX-512/AMX instructions; triggers license request to PCode on instruction boundary | HPM license request signal | ACP PM HAS |
| Core FIVR | CBB Top Die | Clamps voltage to ICCP-capped ratio; follows PLL frequency change | FIVR control; GV done | CBB PM HAS |
| Core PLL | CBB Top Die | Clamps frequency to license-level fused ratio cap | PLL ratio control | CBB PM HAS |
| HPM bus | Core→PCode | Carries license request (L0-L4) from core microcode to CBB PCode; carries grant response | HPM message bus | DMR ICCP HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core CCP | Detects AVX-512/AMX instruction execution; determines required license level (L0-L4); sends HPM license request to PCode; releases on phase end | HPM license request | ACP PM HAS |
| PCode / PEGA (CBB) | CBB Base Die | Receives HPM license requests; evaluates active-core count, Cdyn estimates (NN-based), package current envelope; grants/adjusts license; sets per-core turbo ratio cap to fused value for that level; releases on L0 request | `source/pcode/flows/autonomous_pstate/` ICCP handler; Cdyn/FIT/NN pipeline | [DMR ICCP HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_ICCP.html) |
| PrimeCode (IMH) | IMH die | No direct ICCP license role; fabric frequency limits from PrimeCode constrain headroom available to ICCP | HPM power limits | DMR SoC PM HAS |
| BIOS / UEFI | Platform | Programs per-license fused turbo ratio limits via B2P mailbox `AVX_ICCP_CONFIG` at POST | B2P `AVX_ICCP_CONFIG` mailbox command | DMR CBB PM HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `TURBO_RATIO_LIMIT` | 0x1AD-0x1AE | RW | Per-core-count turbo ratio limits; modified by ICCP license grants | Intel SDM |
| MSR `IA32_PERF_STATUS` | 0x198 | RO | Reflects current ICCP-capped operating ratio | Intel SDM |
| B2P mailbox `AVX_ICCP_CONFIG` | PCU BAR MMIO | WO (BIOS) | Programs per-license (L0-L4) fused turbo ratio caps at POST | DMR CBB PM HAS |
| ICCP telemetry (PMT) | PMT watcher | RO | ICCP license state, Cdyn estimate per-core — observability for BMC | Primecode PMT Spec |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| ICCP license levels | 5 | — | L0 (unrestricted scalar) → L4 (heaviest AMX); each has fused turbo ratio cap | Legacy Architecture Summary |
| License grant latency | <1 | mS | HPM request → PCode arbitration → grant within one slow-loop | Legacy Execution Flow |
| License release latency | Immediate | — | Core releases license on instruction phase end; PCode restores L0 cap | Legacy Execution Flow |
| Cdyn estimator | NN-based | — | Neural-network dynamic capacitance proxy; workload phase detection | Legacy Architecture Summary |
| FIT coordination | DCM only (DMR) | — | Multi-die FIT N/A on NWP (monolithic single die) | Legacy NWP Delta |

## NWP Delta

**ICCP (Integrated Current Core Performance) and Cdyn fitting are fully supported on NWP server** — reused from DMR.

- ICCP telemetry and Cdyn fitting flows unchanged
- PantherCove BigCore Cdyn model reused
- Same fuse-based Cdyn fitting parameters
- 2 CBBs — fewer per-core ICCP aggregation paths but same algorithm

### Validation Impact
- Same ICCP/Cdyn test cases apply
- Verify Cdyn telemetry accuracy with NWP fuse values

## Legacy (Human-Curated Reference)

### Architecture Summary

ICCP (Intelligent Current/Capacitance Proxy) is a license-based current-limiting mechanism for AVX/AMX workloads. Heavy vector/matrix instructions draw significantly more current than scalar code, potentially exceeding the package electrical design point (EDP). ICCP enforces per-core frequency caps based on the granted license level, preventing current exceedance while maximizing performance within safe limits.

ICCP defines 5 license levels (L0–L4), where L0 is unrestricted (scalar) and L4 is the most constrained (heavy AMX). Each license level has a fused turbo ratio limit that decreases as the workload intensity increases. When a core begins executing AVX-512 or AMX instructions, the core requests the appropriate license from PCode. PCode evaluates the total active core count and current license distribution across the die, then grants or adjusts licenses to stay within the package current envelope.

The ICCP pipeline includes Cdyn estimation (dynamic capacitance proxy for current), FIT (Frequency Integration Technology) coordination across cores, and an NN (neural network) predictor for workload phase detection. PCode uses these inputs to determine the optimal license level and corresponding frequency cap for each core. See `dmr_cbb_iccp_cdyn_fit_nn_pipeline.md` in KB for detailed pipeline documentation.

### Execution Flow

1. **Fuse Programming** — Per-license turbo ratio limits are fused at manufacturing. BIOS reads fused ICCP ratio limits and programs them into PCode-accessible registers.
2. **Workload Detection** — Core microcode detects AVX-512/AMX instruction execution and determines the required license level (L0–L4) based on instruction type and width.
3. **License Request** — Core sends license request to PCode via HPM (Hardware P-state Message) with the required license level.
4. **PCode Arbitration** — PCode evaluates active core count, current license grants across all cores, Cdyn estimates, and package power/current limits to determine if the requested license can be granted.
5. **License Grant & Frequency Cap** — PCode grants the license and sets the core's maximum turbo ratio to the fused limit for that license level. Core PLL transitions to the capped frequency if currently above it.
6. **License Release** — When the core stops executing heavy instructions, it releases the license. PCode restores the core's turbo ratio limit to the unrestricted (L0) level.

### Key Registers & Interfaces

| Register / MSR | Address | Description |
|----------------|---------|-------------|
| TURBO_RATIO_LIMIT | MSR 0x1AD–0x1AE | Per-core-count turbo ratio limits |
| ICCP License Level | PCode internal | Current granted license (L0–L4) |
| IA32_PERF_STATUS | MSR 0x198 | Reflects ICCP-capped frequency |
| AVX_ICCP_CONFIG | B2P Mailbox | ICCP configuration mailbox command |
| Cdyn estimator | PCode internal | Dynamic capacitance proxy |
| HPM license request | Core→PCode | License request/grant protocol |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR ICCP HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_ICCP.html) | ICCP license levels and ratio limits |
| HAS | [DMR Turbo HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html) | Turbo ratio limits per license |
| HAS | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) | CBB PM ICCP integration |
| MAS | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP ICCP specification |
| KB | `KB/dmr_cbb_iccp_cdyn_fit_nn_pipeline.md` | Detailed ICCP/Cdyn/FIT/NN pipeline |
| PCode src | `source/pcode/flows/autonomous_pstate/` | ICCP license flow |

### Related Sightings

ICCP license grant/revoke timing sightings are common during DMR bring-up. Monitor for frequency overshoot during license transitions and Cdyn estimation inaccuracy on NWP.

### NWP Delta

| Aspect | DMR | NWP | Notes |
|--------|-----|-----|-------|
| License levels | L0–L4 | Same | 5 license levels preserved |
| Cdyn estimator | NN-based pipeline | Same | Neural network predictor reused |
| FIT coordination | Multi-die | Monolithic (single die) | DCM FIT N/A on NWP |
| AVX-512 / AMX | Supported | Supported | Same instruction set support |
| Fused ratio limits | Per-SKU | Per-SKU | Different fuse values per NWP SKU |
