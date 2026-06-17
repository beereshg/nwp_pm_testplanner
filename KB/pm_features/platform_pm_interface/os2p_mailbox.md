# Platform PM Interface > OS2P Mailbox

> **Status**: Enriched
> **Parent**: [Platform PM Interface](platform_pm_interface_main.md)

## Architecture Summary

The OS2P (OS-to-Punit) Mailbox is a software interface allowing the **OS/kernel** to send commands to PCode firmware at runtime. It is architecturally **distinct from B2P** (BIOS-to-Punit, used during boot/reset). OS2P reuses the same command encoding and handler infrastructure as the B2P mailbox, but accesses it through different HW registers.

**Two transport paths exist for OS2P** (both supported in DMR/NWP):

| Path | HW access | Primecode class | Source |
|------|-----------|-----------------|--------|
| **OS CSR** (legacy) | Dedicated `OS_MAILBOX_INTERFACE` / `OS_MAILBOX_DATA` IO registers in PCU CR space | `OsCSRInterface` → inherits `BiosMailbox` | `src/flow/mailbox/os/os_csr/` |
| **OS TPMI** (modern) | TPMI SRAM opcode `0xe` (`OS_MAILBOX`) — writes to TPMI MMIO translated by OOBMSM | `OsTPMIInterface` → inherits `BiosMailbox` | `src/flow/mailbox/os/os_tpmi/` |

Both paths funnel into the **same B2P mailbox command handler table** — the OS2P interface parses the run-busy/interface/data registers, builds a `MbCmd::Command` struct, and dispatches to the same handler function as the corresponding B2P command. Commands exposed via OS2P are explicitly tagged with `<mbox_access access_type="RW" mbox="OS" />` in the bios_mailbox.xml specification.

### Key OS2P-accessible commands

| Command | Opcode | Description |
|---------|--------|-------------|
| `READ_PM_CONFIG` | `0x94` | Read PM configuration; sub-commands: `MIN_ICCP_LEVEL` (0x2), `PROG_SSC_CONTROL` (0x7) |
| `WRITE_PM_CONFIG` | (write variant of 0x94) | Write PM configuration — same sub-commands as READ |
| `PM_MISC_CONTROL` | `0xd0` | Read/write PM misc controls; sub-command `THERM_MONITOR_STATUS` (0x20) — configures EWMA decay factor & enable |
| `SET_MC_FREQ` / `READ_MC_FREQ` | — | MC frequency set/read — available via OS2P for MC Refresh Parameters Enforcement to lock out future changes |
| `QUIESCE_PECI` / `UNQUIESCE_PECI` | — | ACM/ACTM uses OS2P MSRs to initiate — locked after RST_CPL3 |
| `PM_SECURITY_CONTROL` | `0xd5` | ACTM uses OS2P to initiate UPI_SAI_FILTER enable/disable — locked after RST_CPL3 |

### PM_MISC_CONTROL detail (opcode 0xd0)

- Sub-command `THERM_MONITOR_STATUS` (0x20): configures the EWMA thermal monitoring window
  - `DECAY_FACTOR` [6:0]: decay factor X — window size (TAU) clipped at 1ms–100s
  - `ENABLE_EWMA` [7]: enable bit for the feature
  - R/W bit [24]: 0=READ, 1=WRITE
  - Can be locked by OOB agent via TPMI `OPC_THERMAL_MONITOR` control register (returns `ERR_INTERFACE_LOCKED_OBB` when locked)
  - Not serviced by CBB — resolved in root die, sent to all dies via SOCKET_THERMAL HPM message

## Execution Flow

1. **OS writes** `OS_MAILBOX_DATA` then `OS_MAILBOX_INTERFACE` (with run-busy=1) — via CSR or TPMI path
2. **Fastpath fires** in Punit → scheduler dispatches to OS mailbox flow
3. `OsCSRInterface::readMailboxRegisters()` or `OsTPMIInterface` reads interface+data registers
4. `populateCommandStruct()` extracts command, sub-command, param, data fields into `MbCmd::Command`
5. **Same B2P handler** for that command opcode processes the request
6. **Response written** back to `OS_MAILBOX_INTERFACE` (completion code) + `OS_MAILBOX_DATA` (return data), run-busy cleared
7. `NOT_SERVICED_ON_THIS_DIE` completion code is converted to `INVALID_COMMAND` before returning to OS

## Key Registers & Interfaces

| Register | Role |
|----------|------|
| `OS_MAILBOX_INTERFACE` (CSR path) | Command + sub-command + run-busy + completion code |
| `OS_MAILBOX_DATA` (CSR path) | Input/output data for command |
| `TPMI_MAILBOX[OS_MAILBOX]` (TPMI path) | TPMI SRAM lines for OS_MAILBOX_INTERFACE_N0 and OS_MAILBOX_DATA_N0 |
| `IO_FASTPATH_MAILBOXES` | Fastpath aggregator — triggers PCode on OS mailbox write |

## Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [B2P Mailbox Specification](https://docs.intel.com/documents/primecode/has/DMR/BIOS%20Mailbox/B2P_mailbox_specification.html) | OS2P commands defined within B2P spec with `mbox="OS"` tag |
| Primecode src (CSR) | `src/flow/mailbox/os/os_csr/os_csr_common/v1_0/os_csr.cpp` | `OsCSRInterface` — legacy CSR-based OS mailbox |
| Primecode src (TPMI) | `src/flow/mailbox/os/os_tpmi/os_tpmi_common/v1_0/os_tpmi.cpp` | `OsTPMIInterface` — TPMI-based OS mailbox |
| Primecode src (commands) | `src/flow/mailbox/bios/v3_0/bios_mailbox.xml` | Command definitions with `<mbox_access mbox="OS" />` tags |
| PCode src | `source/mailbox/tools/hpm_bios_mailbox.xml` | PCode CBB-side mailbox XML references OS2P commands |

## Related Sightings
<!-- No known OS2P-specific sightings catalogued yet -->

## NWP Delta

- OS2P carried from DMR — same command set and HW interface
- Both CSR and TPMI transport paths supported
- NWP Primecode inherits the same `os_csr_common_v1_0` and `os_tpmi_common_v1_0` flow versions
- No NWP-specific new OS2P commands identified in current spec
