# OSPL > OSPL Stress

> **Status**: Enriched — full touchpoint enrichment (2026-05-28)
> **Parent**: [OSPL](ospl_main.md)

## Baseline (DMR)

Validates the OS-to-Punit mailbox interface under **rapid, repeated power limit updates** to stress run_busy handshake throughput, fastpath interrupt handling rate, and RAPL PID convergence under sustained cycling load. The test alternates PL1/PL2 between min and max values at maximum mailbox rate for hundreds to thousands of iterations, verifying: no mailbox hang (run_busy never stuck), no MCA, no RAPL oscillation or VF sequencer watchdog timeout.

**Topology:** Same as OSPL Basic Flows. Stress exposes sideband contention (OS mailbox vs B2P/HPM messages), RAPL integral windup risk, and — on DMR — D2D link state interactions during rapid GV. On NWP (no D2D), the D2D state loss failure mode is eliminated.

**Boot activation:** Same as OSPL Basic Flows. Stress test begins after OS brings system to steady-state thermal/power condition.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| PCU OS Mailbox Registers | IMH | CSR-path at max throughput: run_busy handshake rate stress; `OS_MAILBOX_INTERFACE` (0x3b808), `OS_MAILBOX_DATA` (0x3b80c) | run_busy rate; fastpath interrupt edge | Primecode src |
| TPMI OS_MAILBOX cluster | IMH | TPMI-path alternative under stress; array payload | TPMI opcode dispatch | TPMI Common HAS |
| RAPL PID Controller | IMH | Must converge to each new PL within ~1 ms; no integral windup under rapid cycling | Power limit registers; RAPL_PID_FREQ_OUTPUT | DMR RAPL Simplification HAS |
| VF Sequencer / FIVR | IMH | GV triggered per RAPL convergence under rapid cycling; must not watchdog-timeout (HSD 15018542791 on DMR) | VF sequencer timeout register; FIVR handshake | Primecode fix HSD 15018542791 |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Primecode (IMH Punit) | IMH | Fastpath handler at max OS mailbox rate; RAPL update + response compose per iteration; no hang/timeout or integral windup under sustained load | Same handlers as basic flows; emphasis on throughput and convergence stability | `src/flow/mailbox/os/os_csr/`; `src/flow/mailbox/os/os_tpmi/` |
| BIOS / UEFI | Platform | Security policy must allow rapid OS mailbox writes without rate-limiting | B2P security policy | B2P Mailbox Specification |

## OS Interfaces

| Interface | Address / ID | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| `OS_MAILBOX_INTERFACE` | CSR 0x3b808 | RW | Command opcode + run_busy — stress write rate | Primecode src |
| `OS_MAILBOX_DATA` | CSR 0x3b80c | RW | PL1/PL2 payload alternated min/max | Primecode src |
| TPMI `OS_MAILBOX` opcode | TPMI cluster | RW | Array-capable write/read under stress | TPMI Common HAS |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| Stress iteration count | 100s – 1000s | cycles | TC 14020219848 | OSPL Stress TC |
| Mailbox transaction latency | ~250 | µs | Per transaction at stress rate | OSPL Stress NWP Delta |
| run_busy stuck-high | 0 | occurrences | Must be 0 throughout stress run | Primecode src |
| MCA count | 0 | events | No MCAs during rapid PL cycling | OSPL Stress TC |
| RAPL PID convergence per update | ~1 | ms | Must converge; rapid cycling must not cause integral windup | DMR RAPL Simplification HAS |

## Legacy (Human-Curated Reference)

### Architecture Summary

The OSPL Stress test ("OSPL cycles") validates the **OS-to-Punit mailbox interface under rapid, repeated power limit updates**. The test issues many back-to-back mailbox write transactions at high frequency, stressing the run_busy handshake, fastpath interrupt handling, and RAPL engine convergence.

### Stress Dimensions

| Dimension | Description |
|-----------|-------------|
| **Rapid cycling** | Alternate PL1/PL2 between min and max values at maximum mailbox throughput |
| **Concurrent PM activity** | Exercise OSPL while other PM features are active (PkgC, turbo, thermal) |
| **Interface alternation** | Switch between CSR and TPMI mailbox paths if both available |
| **Timeout validation** | Verify run_busy never gets stuck (firmware always clears within timeout) |
| **RAPL convergence** | Verify RAPL PID loop converges to new power target after each update |

### Failure Modes Targeted

- **Mailbox timeout**: run_busy stuck high — firmware fastpath handler didn't fire or took too long
- **RAPL oscillation**: Rapid PL changes cause PID integral windup or voltage sequencer watchdog timeout
- **Sideband contention**: OS mailbox competes with BIOS B2P mailbox or HPM messages
- **D2D state loss**: OSPL update during D2D link power management causes link state corruption

### Execution Flow

1. **Read baseline**: Capture current PL1/PL2 values
2. **Cycle loop**: For N iterations (typically hundreds to thousands):
   - Write new PL value via OS mailbox
   - Poll run_busy until clear (with timeout)
   - Verify completion code = success
   - Optionally verify RAPL status reflects new limit
3. **Final validation**: Confirm no MCAs, no hung mailbox, RAPL engine at expected state

### Key Registers & Interfaces

See [OSPL Basic Flows](ospl_basic_flows.md) for register details.

### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR RAPL Simplification](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html) | OSPL as RAPL interface |
| HAS | [Socket RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html) | PL1/PL2 target registers |
| Primecode src | `src/flow/mailbox/os/os_csr/os_csr_common/v1_0/` | CSR-path mailbox handler |
| Primecode src | `src/flow/mailbox/os/os_tpmi/os_tpmi_common/v1_0/` | TPMI-path mailbox handler |

| HSD ID | Title | Segment | NWP Scope |
|--------|-------|---------|-----------|  
| 14020219848 | OSPL cycles | FV | Runnable_On_N-1 |

### Related Sightings

| HSD | Title | Relevance |
|-----|-------|----------|
| 15018542791 | VF Sequencer Watchdog Timeout after OSPL | D2D state loss during rapid OSPL updates |

## NWP Delta

| Area | DMR (N-1) | NWP | Notes |
|------|----------|-----|-------|
| OSPL stress cycling | Fully supported | Same expected | NIO mailbox handler reused |
| Mailbox throughput | ~250 µs per transaction | Same expected | ⚠ Verify NIO fastpath latency |
| D2D interaction | UCIe D2D link active | No D2D on NIO | Simplifies — no D2D state loss risk |
