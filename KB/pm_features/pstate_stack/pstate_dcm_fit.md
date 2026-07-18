# Pstate Stack > Pstate-DCM FIT

> **Status**: Corrected + Enriched — intra-die Dual Core Module FIT; NWP fully applicable (2026-07-17)
> **Parent**: [P-State Stack](pstate_stack_main.md)
> **TC**: [22022422273](https://hsdes.intel.com/appstore/article-one/#/22022422273) — KB: `KB/pm_tc_kb/fv/HSD_22022422273_dcm_fit.inference.md`

> ⚠️ **Correction (2026-07-17)**: Earlier revisions of this file described DCM FIT as "Dual Chip Module Frequency Integration Technology" (die-to-die inter-die coordination). That description was **incorrect** for this feature and TC. The correct feature is **DCM FIT = Dual Core Module Frequency Isolation Tolerance** — an intra-die, per-module mechanism that isolates two PNC cores sharing a PLL and FIVR within a single DCM. NWP has this topology and the feature is **Runnable** on NWP.

## Baseline (DMR)

**What it does**: DCM FIT (Dual Core Module Frequency Isolation Tolerance) provides per-DCM frequency isolation between the two PantherCove (PNC) cores within a Dual-Core Module that share the same PLL and FIVR. Without FIT, a heavy AVX-512 workload on Core 0 forces Core 1 (even if running a light SSE workload) to drop to the same AVX-512 TRL floor — the "noisy neighbor" effect that degrades QoS in multi-tenant/VM environments. DCM FIT allows software to program a per-DCM tolerance (via TPMI, in units of 100 MHz relative to SSE P0x) so pCode permits the lighter-workload core to run within FIT units of its SSE ceiling, independent of the heavier core's ICCP license. **NWP: Fully applicable — same 2-PNC-core DCM topology.**

**Topology**:
```
Within one DCM (module) on DMR or NWP:
  Core 0 (AVX-512 / heavy) ──┐
                              ├── Shared PLL + FIVR
  Core 1 (SSE / light)  ──────┘
  
  Without FIT: both cores forced to AVX-512 TRL
  With FIT (tolerance = N × 100 MHz):
    Core 0: AVX-512 TRL
    Core 1: ≥ SSE P0x − N×100 MHz  (isolated from Core 0's ICCP level)

  pCode PEGA enforces tolerance via TPMI per-DCM FIT register
  BIOS / hypervisor programs FIT tolerance at boot or runtime
```

**Key operational principle**: pCode PEGA monitors each core's ICCP license level. When cores in the same DCM have divergent ICCP levels (e.g. Core 0 has AVX-512, Core 1 has SSE), the FIT algorithm prevents Core 1 from being dragged down to Core 0's lower TRL beyond the programmed tolerance. The per-DCM TPMI register stores the tolerance; pCode reads it and enforces it each slow-loop evaluation.

**Boot activation**: BIOS programs per-DCM FIT tolerance via TPMI during boot. Default is typically FIT disabled (0) unless BIOS configures a non-zero value. pCode activates FIT enforcement as part of PEGA initialization.

DCM FIT (Dual Core Module Frequency Isolation Tolerance) is an intra-die feature targeting per-module PLL/FIVR sharing between two PNC cores. In a DCM, both cores share the same VR domain, so without FIT the lower-cdyn core is penalized when its DCM partner runs a high-cdyn workload.

## HW Touchpoints

| IP Block | Die/Location | Role | Key Signals | HAS Reference |
|----------|-------------|------|-------------|---------------|
| Core PLL (per DCM) | CBB Top Die | Shared by both PNC cores in a module; FIT ensures lighter-workload core not forced below SSE P0x − tolerance | PLL ratio command from pCode | [DCM PNC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/DCM%20PNC%20PM%20HAS/dmr_dcm_pm_has.html) |
| Core FIVR (per DCM) | CBB Top Die | Shared VR domain for both PNC cores in a module; voltage resolution must satisfy both cores' operating points | FIVR VID; GV transitions | DCM PNC PM HAS |
| TPMI per-DCM FIT register | CBB TPMI SRAM | Stores FIT tolerance (0–N in 100 MHz units); written by BIOS/hypervisor; read by pCode PEGA each slow-loop | TPMI MMIO; OOBMSM BAR | TPMI HAS |
| `IA32_PERF_STATUS (0x198)` | Per core | Current operating ratio — primary observability register per PNC core | MSR per core | Intel SDM |
| `IA32_CORE_PERF_LIMIT_REASONS (0x64F)` | Per core | PLR: AVX throttle bit (Core 0), FIT isolation status (Core 1) | MSR per core | Intel SDM |

## FW Touchpoints

| Agent | Location | Role | Key Functions | Source |
|-------|----------|------|---------------|--------|
| Acode (Core microcode) | Core CCP | Executes per-core GV transitions at FIVR+PLL level; provides SHORT_TELEM workload feedback (IPC, PCNT/ACNT, ICCP level) to pCode PEGA | GV sequence; SHORT_TELEM (~102.4 μS) | ACP PM HAS |
| PCode PEGA (CBB) | CBB Base Die | Central FIT enforcer: reads per-core ICCP license levels; evaluates per-DCM FIT tolerance from TPMI; resolves Core 1 frequency floor as max(Core1_ICCP_TRL, SSE_P0x − FIT_tolerance); updates per-core PLR; no D2D coordination needed (intra-die) | `source/pcode/flows/autonomous_pstate/`; `source/pcode/flows/pega/` | [CBB PEGA HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html) |
| BIOS / UEFI | Platform | Programs per-DCM FIT tolerance via TPMI at boot; default typically 0 (disabled) | TPMI MMIO writes at boot | TPMI HAS |

## OS Interfaces

| Interface | Address | Access | Description | Spec Reference |
|-----------|---------|--------|-------------|----------------|
| `IA32_PERF_STATUS` | 0x198 | RO | Current core ratio — read per PNC core to verify FIT isolation | Intel SDM |
| `IA32_CORE_PERF_LIMIT_REASONS` | 0x64F | RO/RW1C | Per-core PLR: AVX throttle (Core 0), FIT isolation (Core 1) | Intel SDM |
| TPMI FIT tolerance | TPMI MMIO | RW | Per-DCM FIT tolerance in 100 MHz units; 0 = disabled | TPMI HAS |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| NWP DCM topology | Same as DMR | — | 2 PNC cores per module; 24 DCMs per CBB; 2 CBBs | DCM PNC PM HAS |
| FIT tolerance unit | 100 | MHz | Per unit programmed in TPMI FIT register | DCM PNC PM HAS |
| FIT evaluation period | ~1 | mS | pCode PEGA slow loop re-evaluates ICCP levels and FIT tolerance | Legacy FW Agents |
| NWP test case status | **Runnable** | — | DCM topology confirmed on NWP; only adaptation: `nwp.xml` | Updated 2026-07-17 |

## NWP Delta

**DCM FIT is fully applicable and Runnable on NWP.** NWP has the same intra-die DCM topology as DMR (2 PNC cores per module sharing PLL/FIVR), and pCode PEGA's FIT enforcement mechanism carries over unchanged.

| Aspect | DMR | NWP | Notes |
|--------|-----|-----|-------|
| DCM topology (intra-die) | 2 PNC cores/module; 24 DCMs/CBB; 4 CBBs | 2 PNC cores/module; 24 DCMs/CBB; 2 CBBs | Mechanism identical; scale only |
| FIT enforcement (pCode PEGA) | Full | Full | No change |
| TPMI per-DCM FIT register | Present | Present | Same layout |
| Automation XML | `dmr.xml` | `nwp.xml` | Only required adaptation |
| NWP test case status | N/A (source) | **Runnable** | Prior "Runnable_On_N-1" was based on wrong inter-die assumption |

### Validation Impact
- TC 22022422273 "DCM FIT" is **Runnable** on NWP; same test steps apply
- Automation: `python runPmx.py -x nwp.xml -p fit_check -tM 60`
- PythonSV loop: `range(2)` for CBBs (NWP has 2, not 4)

## Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS | [DCM PNC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/DCM%20PNC%20PM%20HAS/dmr_dcm_pm_has.html) | Authoritative: DCM FIT architecture, TPMI register, ICCP-based isolation |
| HAS | [CBB PEGA HAS](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/Features/PEGA/PEGA.html) | PEGA FIT enforcement flow |
| HSD | [22022422273 (TC)](https://hsdes.intel.com/appstore/article-one/#/22022422273) | DCM FIT TC — current HSD description |
| HSD | [22022420473 (TPF)](https://hsdes.intel.com/appstore/article-one/#/22022420473) | Pstate-DCM FIT TPF |
| Intel SDM | `IA32_CORE_PERF_LIMIT_REASONS (0x64F)` | Per-core PLR bit definitions |

## Related Sightings

None known for DCM FIT on NWP or DMR as of 2026-07-17.
