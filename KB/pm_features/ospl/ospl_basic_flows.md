# OSPL > OSPL Basic Flows

> **Status**: Enriched — full touchpoint enrichment (2026-05-28)
> **Parent**: [OSPL](ospl_main.md)

## Baseline (DMR)

Validates the **OS-to-Punit mailbox interface** for runtime power limit updates via single read/write transactions. Tests the full handshake: OS writes `OS_MAILBOX_DATA` (PL value), writes `OS_MAILBOX_INTERFACE` (command + run_busy=1), polls until run_busy=0, reads completion response, and verifies the RAPL engine enforces the new power limit. Both CSR path (0x3b808/0x3b80c) and TPMI path validated.

**Topology:** OS (Linux/SVOS) → PCU mailbox CSR (0x3b808/0x3b80c) or TPMI `OS_MAILBOX` cluster → Primecode fastpath interrupt (fclk edge) → command parse + RAPL routing → RAPL PID update → FIVR/VR workpoint. BIOS enables OS mailbox access via B2P security policy during POST.

**Boot activation:** B2P mailbox programs initial PL1/PL2 and security policy. OS mailbox active from first OS write post-handoff.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| PCU OS Mailbox Registers | IMH | CSR-path: `OS_MAILBOX_INTERFACE` (0x3b808) command/opcode/run_busy; `OS_MAILBOX_DATA` (0x3b80c) PL payload | run_busy handshake; fastpath interrupt edge | Primecode src |
| TPMI OS_MAILBOX cluster | IMH | TPMI-path: `OS_MAILBOX_INTERFACE_N0`, `OS_MAILBOX_DATA_N0`; array payload support | TPMI opcode dispatch | TPMI Common HAS |
| RAPL PID Controller | IMH | Receives new PL1/PL2 target from mailbox handler; runs NN-PID power capping loop | Power limit registers; RAPL_PID_FREQ_OUTPUT | DMR RAPL Simplification HAS |
| FIVR / VR | IMH | Applies new voltage/frequency workpoint after RAPL update | VF sequencer; voltage ramp | DMR RAPL Simplification HAS |
| B2P Mailbox | IMH ↔ BIOS | Configures initial power limits and OS mailbox security policy | B2P command/response | B2P Mailbox Specification |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Primecode (IMH Punit) | IMH | OS mailbox fastpath: register read, opcode parse, RAPL update trigger, response compose; handles CSR and TPMI paths | `OsCSRInterface::readMailboxRegisters()`; `OsTPMIInterface::writeMailboxRegisters()`; `composeResponseToMailbox()`; route to RAPL flow | `src/flow/mailbox/os/os_csr/os_csr_common/v1_0/`; `src/flow/mailbox/os/os_tpmi/os_tpmi_common/v1_0/` |
| BIOS / UEFI | Platform | Initial PL1/PL2 config via B2P; security policy enabling OS mailbox writes | B2P mailbox write sequence | B2P Mailbox Specification |

## OS Interfaces

| Interface | Address / ID | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| `OS_MAILBOX_INTERFACE` | CSR 0x3b808 | RW | Command opcode, parameters, run_busy flag (write to set; firmware clears) | Primecode src |
| `OS_MAILBOX_DATA` | CSR 0x3b80c | RW | PL1/PL2/PL4 payload (32-bit) | Primecode src |
| TPMI `OS_MAILBOX` opcode | TPMI cluster | RW | Array-capable power limit write/read; preferred interface | TPMI Common HAS |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| Mailbox transaction latency | ~250 | µs | Single PL write + run_busy poll cycle | OSPL Stress NWP Delta |
| run_busy stuck-high | 0 | occurrences | Must never occur; firmware always clears within timeout | Primecode src |
| PL readback match | 100 | % | Written value must equal read-back value | TC 14020221052 |
| RAPL PID convergence | ~1 | ms | Typical post-PL-update; depends on VF workpoint distance | DMR RAPL Simplification HAS |

## Legacy (Human-Curated Reference)

### Architecture Summary

OSPL Basic Flows validates the **OS-to-Punit mailbox interface** for runtime power limit updates. The OS writes power limit values via either CSR-based or TPMI-based mailbox registers, Primecode processes the command and updates the RAPL engine, and the OS reads back the completion status.

### OS Mailbox Transaction Flow

```
  OS (Linux/SVOS)                Primecode (IMH Punit)              RAPL Engine
       │                                 │                              │
       │  Write OS_MAILBOX_DATA           │                              │
       ├───────────────────────────────►│                              │
       │  Write OS_MAILBOX_INTERFACE       │                              │
       │  (command + run_busy=1)           │                              │
       ├───────────────────────────────►│                              │
       │                                 │  Fastpath interrupt          │
       │                                 ├───────────────────────────►│
       │                                 │  Parse command               │
       │                                 │  Route to RAPL flow          │
       │                                 │                 Update PL1/PL2│
       │                                 │◄───────────────────────────┤
       │  Write response + run_busy=0     │                              │
       │◄───────────────────────────────┤                              │
       │  Read response                   │                              │
```

### Two Interface Paths

| Interface | Registers | Description |
|-----------|-----------|-------------|
| **CSR** (legacy) | `OS_MAILBOX_INTERFACE` (0x3b808), `OS_MAILBOX_DATA` (0x3b80c) | Direct CR access, 32-bit payload |
| **TPMI** (preferred) | `OS_MAILBOX_INTERFACE_N0`, `OS_MAILBOX_DATA_N0` (via TPMI opcode `OS_MAILBOX`) | Telemetry-based, array payload support |

### Runtime Update Test

The OSPL runtime update test (14020221052) validates:
1. Read current PL1/PL2 values via OS mailbox
2. Write new power limit values
3. Verify run_busy handshake completes (no timeout)
4. Read back updated values and confirm they match
5. Verify RAPL engine enforces new limits

### Execution Flow

1. **BIOS configures**: Initial power limits via B2P mailbox, security policy for OS mailbox access
2. **OS writes data**: `OS_MAILBOX_DATA` ← new power limit value(s)
3. **OS writes command**: `OS_MAILBOX_INTERFACE` ← opcode + parameters + `run_busy=1`
4. **Fastpath interrupt**: Primecode `OsCSRInterface::readMailboxRegisters()` or `OsTPMIInterface::writeMailboxRegisters()` fires
5. **Command routing**: Mailbox handler parses opcode, routes to RAPL flow for power limit update
6. **RAPL update**: Internal PL1/PL2/PL4 state updated, triggers voltage/frequency workpoint changes
7. **Response composed**: `composeResponseToMailbox()` writes completion code + data
8. **run_busy cleared**: OS polls until `run_busy=0`, reads response

### Key Registers & Interfaces

| Register | Address | Description | Source |
|----------|---------|-------------|--------|
| `OS_MAILBOX_INTERFACE` | `0x3b808` | Command/opcode + run_busy control (CSR path) | Primecode source |
| `OS_MAILBOX_DATA` | `0x3b80c` | Power limit payload (32-bit) | Primecode source |
| TPMI `OS_MAILBOX` opcode | — | TPMI-based mailbox access (array payload) | TPMI Common HAS |

### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR RAPL Simplification](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html) | OSPL as RAPL interface |
| HAS | [Socket RAPL HAS (Wave3 Common)](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html) | PL1/PL2 target registers |
| HAS | [B2P Mailbox Specification](https://docs.intel.com/documents/primecode/has/DMR/BIOS%20Mailbox/B2P_mailbox_specification.html) | BIOS↔Punit mailbox |
| Primecode src | `src/flow/mailbox/os/os_csr/os_csr_common/v1_0/` | CSR-path mailbox handler |
| Primecode src | `src/flow/mailbox/os/os_tpmi/os_tpmi_common/v1_0/` | TPMI-path mailbox handler |
| Primecode src | `src/flow/rapl/` | RAPL package/psys/PBM flows |

| HSD ID | Title | Segment | NWP Scope |
|--------|-------|---------|-----------|  
| 14020221052 | OSPL runtime update | FV | Runnable_On_N-1 |

### Related Sightings

| HSD | Title | Relevance |
|-----|-------|----------|
| 15018542791 | VF Sequencer Watchdog Timeout after OSPL | Primecode loses D2D_Link state |
| 15018597011 | MCA GPSB Timeout during OSPL | IO Skip Disables workaround not persisted |

## NWP Delta

| Area | DMR (N-1) | NWP | Notes |
|------|----------|-----|-------|
| OS mailbox CSR path | Fully supported | Same expected | NIO reuses Primecode mailbox handler |
| OS mailbox TPMI path | Fully supported | Same expected | |
| RAPL integration | PL1/PL2/PL4 update | Same expected | NIO as sole IMH host |
| Security policy | BIOS-configurable | Same expected | |
