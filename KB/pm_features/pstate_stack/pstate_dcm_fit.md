# Pstate Stack > Pstate-DCM FIT

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [P-State Stack](pstate_stack_main.md)

## Baseline (DMR)

**What it does**: DCM FIT (Dual Chip Module Frequency Integration Technology) coordinates P-state transitions across two dies in a multi-die package — each die's PCode exchanges frequency/power data via HPM over D2D and the FIT algorithm converges both dies onto compatible operating points within the shared package TDP. **NWP: N/A — monolithic single-die product; test case carried as Runnable_On_N-1 (expected skip).**

**Topology**:
```
[DMR only — DCM not present on NWP]
Die 0 PCode ──HPM D2D channel──> Die 1 PCode
  Exchanges: current frequency, power consumption, turbo headroom
  FIT algorithm: adjusts per-die turbo headroom so:
    power(die0) + power(die1) ≤ PACKAGE_POWER_LIMIT (MSR 0x610)
  Converges both dies to compatible frequency operating points
```

**Key operational principle**: Each die monitors its own power and sends updates to the peer die each slow-loop. When one die reduces load and frees power headroom, the FIT algorithm makes that headroom available to the other die for frequency boost. Monolithic NWP does not need this — single PCode owns all power budget.

**Boot activation**: DCM detection via package fuses at PCode init. D2D HPM link established if DCM detected. No-op on monolithic NWP.

DCM FIT (Dual Chip Module Frequency Integration Technology) coordinates P-state transitions across multiple dies in a multi-die package. In a DCM configuration, two dies share a single package power budget, requiring frequency coordination to prevent one die from consuming excessive power headroom at the expense of the other.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| D2D HPM channel | Die-to-Die | Carries inter-die frequency/power exchange messages for FIT coordination; active only in DCM packages | HPM message bus; D2D UCIe link | DMR CBB PM HAS |
| Package fuses | IMH | Encode DCM vs monolithic topology; PCode reads at boot to detect configuration | Fuse bits; `DCM_CONFIG` | DMR CBB PM HAS |
| PACKAGE_POWER_LIMIT register | IMH (Root) | Shared package TDP limit; FIT algorithm distributes headroom between dies | MSR 0x610; RAPL PKG PL1/PL2 | Intel SDM |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core CCP | No direct DCM FIT role | — | — |
| PCode (CBB, per die) | CBB Base Die | DCM detection at boot; establishes D2D HPM channel if DCM; sends current frequency + power to peer die each slow-loop; runs FIT algorithm to adjust turbo headroom for shared TDP compliance; no-op on monolithic NWP | `source/pcode/flows/autonomous_pstate/` FIT coordination | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) |
| PrimeCode (IMH) | IMH die | No direct DCM FIT role; package power limits fed to PCode via HPM | HPM power limit HPMs | DMR SoC PM HAS |
| BIOS / UEFI | Platform | Programs `PACKAGE_POWER_LIMIT` (MSR 0x610) PL1/PL2; no FIT-specific BIOS config | Boot-time RAPL programming | Intel SDM |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `PACKAGE_POWER_LIMIT` | 0x610 | RW | PL1[14:0] + PL2[46:32] — shared package TDP; FIT distributes budget between dies | Intel SDM |
| HPM D2D channel | D2D (internal) | RW | Inter-die frequency/power exchange (internal FW interface; not SW-visible) | DMR CBB PM HAS |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| DCM FIT applicability | N/A | — | NWP is monolithic (single die); DCM FIT is a no-op / skip | Legacy NWP Delta |
| FIT convergence period | ~1 | mS | Each die sends power/freq update per PCode slow-loop; FIT converges iteratively | Legacy Execution Flow |
| Package TDP split | Dynamic | — | FIT redistributes headroom as per-die load changes | Legacy Execution Flow |
| NWP test case status | Runnable_On_N-1 | — | Carried for regression only; expected skip/no-op on NWP silicon | Legacy Architecture Summary |

## NWP Delta

**DCM FIT (Dynamic Capacitance Model Fitting) is fully supported on NWP server** — reused from DMR.

- DCM FIT algorithms and telemetry unchanged
- Same runtime fitting mechanism
- 2 CBBs — same per-CBB DCM FIT behavior

### Validation Impact
- Same DCM FIT test cases apply

## Legacy (Human-Curated Reference)

### Architecture Summary

DCM FIT (Dual Chip Module Frequency Integration Technology) coordinates P-state transitions across multiple dies in a multi-die package. In a DCM configuration, two dies share a single package power budget, requiring frequency coordination to prevent one die from consuming excessive power headroom at the expense of the other.

PCode on each die communicates via HPM (Hardware P-state Messages) over the die-to-die (D2D) interface to exchange current frequency, power consumption, and turbo headroom information. The FIT algorithm ensures that both dies converge on compatible frequency operating points that collectively stay within the package TDP envelope.

NWP is a monolithic (single-die) product, so DCM FIT is architecturally N/A. The test case is carried as Runnable_On_N-1 for regression coverage but is expected to be a no-op or skip on NWP silicon.

### Execution Flow

1. **DCM Detection** — During boot, PCode detects whether the package is a DCM (two dies) or monolithic (single die) configuration via package fuses.
2. **D2D Link Establishment** — If DCM, PCode establishes the HPM communication channel over the D2D interconnect between the two dies.
3. **Power Budget Partitioning** — Package TDP is partitioned between the two dies based on their respective workloads and fused power allocation ratios.
4. **Frequency Coordination** — Each die's PCode sends its current/target frequency and power consumption to the other die. The FIT algorithm adjusts each die's turbo headroom to stay within the shared package budget.
5. **Convergence** — Both dies converge on coordinated frequency operating points. If one die reduces load, the freed power headroom is made available to the other die.

### Key Registers & Interfaces

| Register / MSR | Address | Description |
|----------------|---------|-------------|
| DCM_CONFIG | PCode internal | DCM vs monolithic detection |
| HPM D2D channel | D2D interface | Inter-die frequency coordination messages |
| PACKAGE_POWER_LIMIT | MSR 0x610 | Package-level power limit (shared) |
| FIT coordination state | PCode internal | Per-die frequency/power exchange |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR Turbo HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html) | DCM FIT turbo coordination |
| HAS | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) | CBB PM multi-die coordination |
| MAS | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP monolithic — DCM N/A |
| PCode src | `source/pcode/flows/autonomous_pstate/` | FIT coordination flow |

### Related Sightings

No DCM FIT sightings applicable to NWP (monolithic die). DMR DCM sightings exist but are not transferable.

### NWP Delta

| Aspect | DMR | NWP | Notes |
|--------|-----|-----|-------|
| Package topology | DCM (2 dies) supported | Monolithic (single die) | DCM FIT N/A on NWP |
| D2D HPM coordination | Active | N/A | No inter-die frequency sync needed |
| Test case | Full validation | Expected skip/no-op | Carried for regression only |
