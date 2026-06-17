# Pstate Stack > Pstate-PLR

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [P-State Stack](pstate_stack_main.md)

## Baseline (DMR)

**What it does**: Performance Limit Reasons (PLR) is the hardware diagnostic register set that reports why the CPU is not running at its maximum possible turbo. Sticky log bits in MSR 0x64F (die-level, 16+ reasons) and MSR 0x6B0 (package-level) latch when any constraint actively limits turbo. TPMI PLR mirrors these for OOB access. PLR is the first-line diagnostic for unexpectedly low frequency.

**Topology**:
```
PCode P-state evaluation loop (each PEGA cycle, ~1mS):
  if resolved_freq < requested_turbo:
    identify active constraint(s):
      thermal limit → bit THERMAL
      PL1/PL2 power limit → bit POWER_LIMIT_1 / POWER_LIMIT_2
      ICCP license → bit ICCP
      EET attenuation → bit EET
      PROCHOT assertion → bit PROCHOT
      ...
    set sticky log bits: MSR 0x64F (die-level) + MSR 0x6B0 (pkg-level)
    mirror to TPMI PLR registers (OOB polling)
OS/tools read 0x64F → identify throttle cause → write 1 to clear log bit
```

**Key operational principle**: PLR log bits are sticky — they latch when a limit is active and remain set until explicitly cleared by software. Status bits (lower half of register) reflect the current live state; log bits (upper half) reflect ever-asserted. Reading PLR captures historical throttle events even after the condition cleared.

**Boot activation**: PLR registers are available from CPL3 handoff. TPMI PLR available after platform init. Log bits start cleared; accumulate during runtime.

Performance Limit Reasons (PLR) provides a transparent reporting mechanism for why the CPU is not running at its maximum possible frequency. When PCode limits the core frequency below the requested turbo ratio, the reason is logged in PLR status registers accessible via MSR 0x64F (IA32_CORE_PERF_LIMIT_REASONS) and TPMI PLR registers.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| MSR interface | Per-core (0x64F) | Die-level PLR status + log bits; each bit = specific turbo limiting reason; sticky log bits until SW clear | MSR 0x64F | Intel SDM; [PLR HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/perf_limit_reasons/perf_limit_reasons_has.html) |
| MSR interface | Package (0x6B0) | Package-level PLR status + log bits; thermal/power limits at package scope | MSR 0x6B0 | Intel SDM |
| TPMI SRAM | Per IMH | OOB-accessible PLR registers; BMC monitors PLR without OS intervention; die-level + package-level | TPMI MMIO; OOBMSM BAR | TPMI HAS |
| PROCHOT GPIO | Platform | External thermal assertion from VR/platform; asserts PROCHOT PLR bit when platform too hot | PROCHOT_STATUS pin | CBB PM HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core CCP | No direct PLR role; thermal/perf events reported to PCode via SHORT_TELEM | SHORT_TELEM | ACP PM HAS |
| PCode / PEGA (CBB) | CBB Base Die | Evaluates all constraints each P-state cycle; sets die-level PLR log bits in MSR 0x64F when any limit is active; updates TPMI PLR; manages sticky log bit mechanism | PLR status update; `source/pcode/flows/autonomous_pstate/` | [PLR HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/perf_limit_reasons/perf_limit_reasons_has.html) |
| PrimeCode (IMH) | IMH die | Propagates IMH-scope package power limit events to CBB PCode; triggers PACKAGE_POWER_LIMIT PLR bit when IMH-side limit reduces turbo headroom | IMH power limit HPM | DMR SoC PM HAS |
| BIOS / UEFI | Platform | Configures PL1/PL2 power limits (MSR 0x610) that trigger POWER_LIMIT PLR bits; programs PROCHOT enable; enables TPMI PLR reporting | PL1/PL2 config; PROCHOT enable | Intel SDM |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `IA32_CORE_PERF_LIMIT_REASONS` | 0x64F | RO (status) / RW1C (log) | Die-level PLR: status bits [15:0] = live state; log bits [31:16] = ever-asserted (cleared by writing 1) | Intel SDM; [PLR HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/perf_limit_reasons/perf_limit_reasons_has.html#msr) |
| MSR `PACKAGE_PERF_LIMIT_REASONS` | 0x6B0 | RO (status) / RW1C (log) | Package-level PLR: same status+log bit structure as 0x64F | Intel SDM |
| TPMI PLR die-level | TPMI MMIO | RO (BMC OOB) | Mirror of MSR 0x64F; BMC polls for throttle monitoring without OS | TPMI HAS |
| TPMI PLR package-level | TPMI MMIO | RO (BMC OOB) | Mirror of MSR 0x6B0; package thermal/power limits visible OOB | TPMI HAS |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| PLR evaluation period | ~1 | mS | PCode evaluates constraints and updates PLR bits each PEGA slow-loop iteration | Legacy Execution Flow |
| PLR log bit behavior | Sticky | — | Log bits latch on assertion; remain set until SW writes 1-to-clear; status bits reflect live state | Legacy Architecture Summary |
| PLR reason count | 16+ | bits | Die-level MSR 0x64F; organized into thermal, power, ICCP, EET, PROCHOT, etc. | Legacy Architecture Summary |
| NWP inactive PLR bits | SST-PP, SST-BF bits | — | PLR bits for removed NWP features should never assert; useful negative-space baseline | Legacy NWP Delta |
| Package PLR scope | Monolithic NWP | — | Package-level PLR simpler on single-die NWP vs multi-die DMR | Legacy NWP Delta |

## NWP Delta

**PLR (Performance Limit Reasons) is fully supported on NWP server** — reused from DMR.

- PLR reporting and telemetry unchanged
- Same PLR bit definitions and mailbox interface
- Same TPMI PLR registers
- All PLR reason codes valid on NWP (PROCHOT, THERMAL, RAPL, VR_THERM, etc.)

### Topology Impact
- Some PLR bits related to removed features (SST-PP, PkgC6, DRAM RAPL) will never assert on NWP
- Core PLR bits fully applicable (2 CBBs, same per-core behavior)

### Validation Impact
- Same PLR test cases apply for active features
- Verify PLR bits for removed features show "not asserted" baseline

## Legacy (Human-Curated Reference)

### Architecture Summary

Performance Limit Reasons (PLR) provides a transparent reporting mechanism for why the CPU is not running at its maximum possible frequency. When PCode limits the core frequency below the requested turbo ratio, the reason is logged in PLR status registers accessible via MSR 0x64F (IA32_CORE_PERF_LIMIT_REASONS) and TPMI PLR registers.

PLR tracks 16+ distinct limiting reasons organized into die-level and package-level categories. Die-level reasons include: thermal throttling, power limit (PL1/PL2/PL4), ICCP license downgrade, EET turbo attenuation, prochot assertion, and turbo transition attenuation. Package-level reasons include: platform power limit, package thermal, VR (voltage regulator) current limit, and max turbo limit.

Each PLR bit is a sticky status bit that latches when the corresponding limit is active. Software can read these bits to diagnose why performance is below expectations. The bits are cleared by writing 1 to the corresponding log bit. PLR is critical for datacenter performance debugging — when users report "frequency lower than expected," PLR is the first diagnostic check.

### Execution Flow

1. **PCode Frequency Decision** — During each P-state evaluation cycle, PCode computes the maximum allowed frequency considering all constraints (thermal, power, ICCP, EET, prochot, etc.).
2. **Limit Detection** — If the resolved frequency is lower than the requested/turbo frequency, PCode identifies which constraint(s) are active.
3. **PLR Bit Setting** — PCode sets the corresponding PLR status bits in MSR 0x64F (die-level) and package-level PLR registers. Bits are sticky until software clears them.
4. **TPMI PLR Reporting** — PLR status is also exposed via TPMI registers for OOB monitoring by BMC.
5. **Software Read** — OS or debug tools read MSR 0x64F to determine active performance limits. Each bit maps to a specific reason (e.g., bit 0 = PROCHOT, bit 1 = thermal, bit 4 = PL1, etc.).
6. **Validation** — Test induces known limiting conditions (thermal, power limit, ICCP heavy workload) and verifies the correct PLR bits are set. Clears bits and confirms they re-assert when condition persists.

### Key Registers & Interfaces

| Register / MSR | Address | Description |
|----------------|---------|-------------|
| IA32_CORE_PERF_LIMIT_REASONS | MSR 0x64F | Die-level PLR status + log bits |
| PACKAGE_PERF_LIMIT_REASONS | MSR 0x6B0 | Package-level PLR status |
| TPMI PLR die-level | TPMI MMIO | OOB die-level PLR |
| TPMI PLR package-level | TPMI MMIO | OOB package-level PLR |
| PROCHOT_STATUS | Platform GPIO | External thermal assertion |
| PACKAGE_POWER_LIMIT | MSR 0x610 | PL1/PL2 power limits |
| IA32_PERF_STATUS | MSR 0x198 | Current (limited) ratio |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [Perf Limit Reasons HAS — MSR](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/perf_limit_reasons/perf_limit_reasons_has.html#msr) | MSR 0x64F bit definitions |
| HAS | [Perf Limit Reasons HAS — PLR Die Level](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/perf_limit_reasons/perf_limit_reasons_has.html#plr_die_level) | Die-level PLR details |
| HAS | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) | PLR in CBB PM context |
| MAS | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PLR specification |
| PCode src | `source/pcode/flows/autonomous_pstate/` | PLR status update logic |

### Related Sightings

PLR bit stuck-on (especially thermal and PL1 bits) is a common DMR sighting pattern. See also KB `plr_debug_flow.md` for PLR debug methodology.

### NWP Delta

| Aspect | DMR | NWP | Notes |
|--------|-----|-----|-------|
| MSR 0x64F | 16+ reason bits | Same | Same bit definitions expected |
| TPMI PLR | Die + package level | Same | Same TPMI registers |
| PLR bit mapping | DMR bit assignments | Same | No new reason bits expected for NWP |
| Package PLR | Multi-die package | Single-die package | Package-level simpler on monolithic NWP |
