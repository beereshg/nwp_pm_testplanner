# OSPL — Main Flow

> **Status**: Enriched — full touchpoint enrichment (2026-05-28)
> **Generated**: 2026-05-23 from nwp_pm_test_cases.json (2 TCs)

## Baseline (DMR)

**OSPL (OS Power Limits)** provides the OS-to-firmware mailbox interface for runtime power limit updates. The OS writes PL1/PL2/PL4 values via either a CSR-based (`OS_MAILBOX_INTERFACE` 0x3b808, `OS_MAILBOX_DATA` 0x3b80c) or TPMI-based mailbox opcode; Primecode processes the command through a fastpath interrupt handler, updates the RAPL engine, and returns a completion response.

**Topology:** Single IMH die (NIO). OS → PCU mailbox registers (CSR) or TPMI cluster → Primecode fastpath interrupt → command routing → RAPL PID update → FIVR/VR voltage/frequency workpoint. No cross-socket coordination required (NIO is sole IMH host). BIOS initializes PL1/PL2 values and configures security policy via B2P mailbox during POST.

**Boot activation:** BIOS programs initial power limits via B2P mailbox. OS mailbox active from first OS write post-handoff. Two interface paths: CSR (legacy) and TPMI (preferred, array payload support).

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| PCU OS Mailbox Registers | IMH | CSR-path: `OS_MAILBOX_INTERFACE` (0x3b808) command/opcode/run_busy; `OS_MAILBOX_DATA` (0x3b80c) PL payload | run_busy edge; fastpath interrupt to Primecode | Primecode src `src/flow/mailbox/os/` |
| TPMI OS_MAILBOX cluster | IMH | TPMI-path: `OS_MAILBOX_INTERFACE_N0`, `OS_MAILBOX_DATA_N0`; array payload support | TPMI opcode dispatch | TPMI Common HAS |
| RAPL PID Controller | IMH | Enforces PL1/PL2/PL4 limits; receives new targets from mailbox handler; NN-PID loop for power capping | RAPL_PID_FREQ_OUTPUT; power limit registers | DMR RAPL Simplification HAS |
| FIVR / VR | IMH | Applies voltage/frequency workpoint after RAPL update; VF sequencer services new target | VF sequencer; FIVR voltage ramp | DMR RAPL Simplification HAS |
| B2P Mailbox | IMH ↔ BIOS | Configures initial power limits and OS mailbox security policy during POST | B2P command/response registers | B2P Mailbox Specification |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Primecode (IMH Punit) | IMH | OS mailbox fastpath: register read, opcode parse, RAPL update trigger, response compose; handles both CSR and TPMI paths | `OsCSRInterface::readMailboxRegisters()`; `OsTPMIInterface::writeMailboxRegisters()`; `composeResponseToMailbox()`; route to RAPL flow | `src/flow/mailbox/os/os_csr/`; `src/flow/mailbox/os/os_tpmi/` |
| BIOS / UEFI | Platform | Initial PL1/PL2 config via B2P mailbox; security policy enabling OS mailbox access | B2P mailbox write sequence; BIOS OSPL/RAPL knob | B2P Mailbox Specification |

## OS Interfaces

| Interface | Address / ID | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| `OS_MAILBOX_INTERFACE` | CSR 0x3b808 | RW | Command opcode, parameters, run_busy flag (write to set; firmware clears on completion) | Primecode src |
| `OS_MAILBOX_DATA` | CSR 0x3b80c | RW | PL1/PL2/PL4 payload (32-bit) | Primecode src |
| TPMI `OS_MAILBOX` opcode | TPMI cluster | RW | Array-capable power limit read/write; preferred interface | TPMI Common HAS |
| B2P mailbox | BIOS-time only | WO | Initial power limit configuration and OS mailbox security policy | B2P Mailbox Specification |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| Mailbox transaction latency | ~250 | µs | Single PL write + run_busy poll cycle | OSPL Stress NWP Delta |
| run_busy hold time | < timeout | µs | Firmware must always clear; stuck high = mailbox hang risk | Primecode src |
| RAPL PID convergence | ~1 | ms | Typical; depends on VF workpoint distance from new target | DMR RAPL Simplification HAS |
| PL1 valid range | 0 – TDP | W | OS-configurable; clamped to HW limits by firmware | Socket RAPL HAS |
| PL2 valid range | 0 – PMax | W | OS-configurable; clamped to PMax fuse by firmware | DMR PMax HAS |
| Stress iteration count | 100s – 1000s | cycles | OSPL Stress TC (HSD 14020219848) | OSPL Stress |

## NWP Delta

| Aspect | DMR (N-1) | NWP | Source |
|--------|----------|-----|--------|
| OS mailbox CSR path | Fully supported | Same — NIO reuses Primecode mailbox handler | NWP PM MAS |
| OS mailbox TPMI path | Fully supported | Same | NWP PM MAS |
| RAPL PL1/PL2/PL4 update | Supported | Same — NIO as sole IMH host | NWP PM MAS |
| Cross-socket OSPL | Root IMH broadcasts to Leaf IMH | N/A — NIO is sole host | NWP topology |
| D2D state during OSPL | UCIe D2D link active; risk of D2D state loss (HSDs 15018542791, 15018597011) | **No D2D on NIO** — simplifies; no D2D state loss risk | NWP NIO topology |
| Mailbox throughput | ~250 µs/transaction | Same expected — verify NIO fastpath latency post-Si | OSPL Stress analysis |

## Legacy (Human-Curated Reference)

### NWP Spec Context
| Field | Value |
|-------|-------|
| HAS ref | NWP HAS: OS Power Limit interface |
| MAS ref | NWP PM MAS: OSPL supported |
| NWP delta | Carried from DMR — NIO as sole host, no D2D simplifies OSPL |
| NWP supported | True |

### Architecture Summary

**OSPL (OS Power Limits)** provides the OS-to-firmware mailbox interface for runtime power limit updates. The OS writes PL1/PL2/PL4 values via either a CSR-based or TPMI-based mailbox; Primecode processes the command through a fastpath interrupt handler, updates the RAPL engine, and returns a completion response.

```
  ┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
  │ OS / SVOS    │     │ Primecode        │     │ RAPL Engine  │
  │              │     │ (IMH Punit)      │     │              │
  │ OS_MAILBOX   ├───►│ Fastpath handler ├───►│ PL1/PL2/PL4  │
  │ _INTERFACE   │     │ Command routing  │     │ NN-PID loop  │
  │ _DATA        │◄───┤ Response compose  │     │              │
  └──────────────┘     └──────────────────┘     └──────────────┘
   CSR (0x3b808)                                 Voltage/Freq
   or TPMI opcode                                workpoint
```

### Two Subflows

| Subflow | Purpose |
|---------|--------|
| **OSPL Basic Flows** | Validates single mailbox read/write transactions — run_busy handshake, correct PL propagation to RAPL |
| **OSPL Stress** | Rapid cycling of PL values — validates mailbox throughput, RAPL PID convergence, no MCA/timeout under load |

### FW Agents
- **Agents**: Primecode (IMH Punit) — OS mailbox handler + RAPL coordination
- **Interfaces**: OS_MAILBOX_INTERFACE/DATA (CSR), OS_MAILBOX TPMI opcode, B2P mailbox (BIOS config)
- **HW Blocks**: PCU mailbox registers, RAPL PID controller, FIVR/VR voltage regulators
- **Sub-features**: OSPL Basic Flows, OSPL Stress

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR RAPL Simplification](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html) | OSPL as RAPL interface |
| HAS | [Socket RAPL HAS (Wave3 Common)](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html) | PL1/PL2 targets |
| HAS | [DMR PMax HAS — PL4](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PMax.html#pl4) | PL4 power limit interaction |
| HAS | [B2P Mailbox Specification](https://docs.intel.com/documents/primecode/has/DMR/BIOS%20Mailbox/B2P_mailbox_specification.html) | BIOS↔Punit mailbox for initial OSPL config |
| HAS | [DMR SoC PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_PM_HAS.html) | DMR SoC PM overview |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM MAS — OSPL supported |
| Primecode src | `src/flow/mailbox/os/os_csr/os_csr_common/v1_0/` | CSR-path mailbox handler |
| Primecode src | `src/flow/mailbox/os/os_tpmi/os_tpmi_common/v1_0/` | TPMI-path mailbox handler |
| Primecode src | `src/flow/rapl/` | RAPL package/psys/PBM flows |

### Related Sightings

| HSD | Title | Relevance |
|-----|-------|----------|
| 15018542791 | VF Sequencer Watchdog Timeout after OSPL | D2D state loss during OSPL — Primecode fix |
| 15018597011 | MCA GPSB Timeout during OSPL | IO Skip Disables workaround persistence |

## Subflows (2)

| # | Subflow | Status | TCs | Segment | Notes |
|---|---------|--------|-----|---------|-------|
| 1 | [OSPL Basic Flows](ospl_basic_flows.md) | Enriched | 1 | FV | Runtime PL read/write validation |
| 2 | [OSPL Stress](ospl_stress.md) | Enriched | 1 | FV | Rapid PL cycling, convergence, no MCA |
| | **Total** | 2/2 enriched | **2** | | |
