# PState Stack > Mailbox

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [P-State Stack](pstate_stack_main.md)

## Baseline (DMR)

**What it does**: B2P (MMIO, BIOS at POST) and OS2P (MSR 0x150, OS at runtime) mailboxes provide command/response channels for P-state parameters that cannot be set via MSR writes alone — turbo ratio limits, ICCP license config, SST-PP level, and power limit overrides. TPMI mailbox provides an OOB equivalent.

**Topology**:
```
BIOS (POST) ──write─> B2P Mailbox (MMIO, PCU BAR)
                        ├── RUN/BUSY bit set → PCode mailbox interrupt
                        ├── PCode validates, executes, writes completion code
                        └── BIOS polls BUSY=0 → reads response
OS driver ──write────> OS2P Mailbox (MSR 0x150)
                        └── same PCode handler
BMC/OOB ─────────────> TPMI Mailbox (MMIO, OOBMSM BAR)
                        └── same PCode handler
```

**Key operational principle**: All three mailbox paths (B2P/OS2P/TPMI) converge on the same PCode mailbox handler. Completion code 0 = success; non-zero = error. Parameter range validation is mandatory — out-of-range inputs return error codes without side effects. Each command has a specific opcode + sub-command; sweep test validates all P-state-related opcodes.

**Boot activation**: B2P mailbox available from PCode init (PH1). OS2P available from CPL3 handoff. TPMI mailbox available after TPMI SRAM init (PH2.x).

The BIOS-to-PCode (B2P) and OS-to-PCode (OS2P) mailbox interfaces provide a command/response channel for configuring P-state stack parameters that cannot be set through MSR writes alone. Mailbox commands control features such as turbo ratio limits, ICCP license configuration, SST-PP level selection, and power limit overrides.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| PCU (Power Control Unit) | IMH die | Hosts B2P mailbox registers (MMIO, PCU BAR); hardware RUN/BUSY mechanism; interrupt to PCode on write | PCU BAR MMIO registers; `MAILBOX_INTERFACE` | DMR CBB PM HAS |
| TPMI SRAM (OOB mailbox) | Per IMH | TPMI-accessible mailbox registers for OOB (BMC) mailbox path; same semantics as B2P | TPMI MMIO; OOBMSM VSEC BAR | TPMI HAS |
| MSR interface | Per-core | OS2P mailbox delivered via MSR 0x150; hardware serializes to PCode mailbox handler | MSR 0x150 `PCODE_MAILBOX_INTERFACE` | Intel SDM |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core CCP | No direct mailbox role | — | — |
| PCode (CBB / IMH) | CBB / IMH Base Die | Mailbox interrupt handler: reads command opcode + data, validates parameter ranges, executes (turbo limits, ICCP config, power limits), writes completion code + response data | `source/pcode/flows/autonomous_pstate/` mailbox handler; PCODE_MAILBOX_INTERFACE | [CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) |
| PrimeCode (IMH) | IMH die | Handles IMH-scope mailbox commands (package power limits, TPMI mailbox); routes to CBB PCode as needed via HPM | HPM mailbox routing | DMR CBB PM HAS |
| BIOS / UEFI | Platform | Issues B2P commands during POST (turbo limits, ICCP config, SST-PP level); polls RUN/BUSY until complete; reads completion code | B2P MMIO write; BUSY poll | Intel SDM |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| B2P Mailbox | MMIO (PCU BAR) | RW | `MAILBOX_INTERFACE`: opcode[7:0], sub-cmd[15:8], data[31:16], RUN_BUSY[31]; response in `MAILBOX_DATA` | DMR CBB PM HAS |
| OS2P Mailbox | MSR 0x150 | RW | `PCODE_MAILBOX_INTERFACE`: same encoding as B2P; OS runtime P-state config | Intel SDM |
| TPMI Mailbox | TPMI MMIO | RW (BMC) | OOB equivalent of B2P; same command set; access via OOBMSM BAR | TPMI HAS |
| Completion code | Mailbox response | RO | 0x00 = success; non-zero = error code (invalid param, unsupported, etc.) | DMR CBB PM HAS |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| Mailbox completion time | <1 | mS | PCode processes command within one slow-loop iteration | Legacy Execution Flow |
| B2P RUN/BUSY polling | Synchronous | — | BIOS polls until BUSY=0 before reading response | Legacy Execution Flow |
| Completion code success | 0x00 | — | Non-zero = error; SW must check before using response data | Legacy Key Registers |
| Command types (P-state) | Multiple | — | Turbo ratio limits, ICCP config, power limits, SST-PP level selection | Legacy Architecture Summary |

## NWP Delta

**P-state mailbox interface is fully supported on NWP server** — reused from DMR.

- Mailbox interface for P-state and PM commands unchanged
- Same command set, same encoding, same response format
- Single NIO root — mailbox routing simplified (1 root vs 2 IMH)

### Validation Impact
- Same mailbox test cases apply
- Verify mailbox routing with NIO→2 CBB topology

## Legacy (Human-Curated Reference)

### Architecture Summary

The BIOS-to-PCode (B2P) and OS-to-PCode (OS2P) mailbox interfaces provide a command/response channel for configuring P-state stack parameters that cannot be set through MSR writes alone. Mailbox commands control features such as turbo ratio limits, ICCP license configuration, SST-PP level selection, and power limit overrides.

Each mailbox command consists of a command opcode, sub-command, and data payload written to the mailbox MSR or MMIO interface. PCode processes the command and returns a completion code with optional response data. The mailbox sweep test validates all P-state-related command opcodes for correct encoding, parameter range acceptance, error code reporting, and functional effect.

B2P mailbox commands are typically issued during BIOS POST to configure platform-level P-state parameters before OS handoff. OS2P commands are issued at runtime for dynamic reconfiguration. Both interfaces share the same PCode mailbox handler infrastructure.

### Execution Flow

1. **Command Preparation** — Caller (BIOS or OS driver) prepares mailbox command with opcode, sub-command, and parameter data.
2. **Mailbox Write** — Command is written to B2P mailbox (MMIO) or OS2P mailbox (MSR 0x150 or TPMI). A run/busy bit is set to trigger PCode processing.
3. **PCode Processing** — PCode's mailbox interrupt handler reads the command, validates parameters, executes the requested operation, and writes the result.
4. **Completion Check** — Caller polls the run/busy bit until cleared, then reads the completion code and response data.
5. **Validation** — Sweep test iterates all P-state-related mailbox commands, verifying accepted parameter ranges, correct error codes for out-of-range inputs, and functional effects on P-state behavior.

### Key Registers & Interfaces

| Register / MSR | Address | Description |
|----------------|---------|-------------|
| B2P Mailbox | MMIO (PCU BAR) | BIOS-to-PCode command interface |
| OS2P Mailbox | MSR 0x150 | OS-to-PCode command interface |
| TPMI Mailbox | TPMI MMIO | OOB mailbox interface |
| Mailbox command | Various opcodes | Turbo limits, ICCP config, SST-PP, power limits |
| Completion code | Mailbox response | 0=success, non-zero=error code |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) | Mailbox command definitions |
| HAS | [Core P-State HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) | P-state mailbox context |
| MAS | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP mailbox specification |
| PCode src | `source/pcode/flows/autonomous_pstate/` | Mailbox handler for P-state commands |

### Related Sightings

No mailbox-specific sightings identified for NWP. Mailbox command compatibility between DMR and NWP should be verified during bring-up.

### NWP Delta

| Aspect | DMR | NWP | Notes |
|--------|-----|-----|-------|
| B2P Mailbox | Supported | Supported | Same command set expected |
| OS2P Mailbox | MSR 0x150 | Same | No interface changes |
| TPMI Mailbox | Supported | Supported | OOB mailbox preserved |
| Command set | Full P-state commands | Same | Verify new NWP-specific opcodes if any |
