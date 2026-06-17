# Core C-States > MC6

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing added (2026-05-28)
> **Parent**: [Core C-States](core_c_states_main.md)

## Baseline (DMR)

Module C-State (MCx) represents the collective idle state of all cores within a **DCM (Dual Core Module) with shared MLC**. Module C-states are resolved by PMA/Acode after all enabled cores reach the required core C-state depth.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| ACP / PMA | CBB | Module C-state coordinator: monitors all core states, runs abortable MLC shrink FSM, sequences MC6 entry/exit | cfcclk_qactive=0, cfcpwr_qactive=0, inf_qactive=0 (all three for MC6) | PNC PM HAS §8.14 |
| SRL (Snoop Response Logic) | CBB | Default snoop responses for module while MLC is flushed and clocks are gated in MC6 | snoopq_empty; FIL stop_interface ack; snoop_response_default asserted | PNC PM HAS §8.14.3 |
| Q-channels (CFC_CLK / CFC_PWR / INF) | CBB | All three must be deasserted for MC6; MC3 only requires CFC_CLK deasserted | Q_CFC_CLK.qactive=0, Q_CFC_PWR.qactive=0, INF.qactive=0 | PNC PM HAS §8.14 |
| FIL (Fabric Interface Logic) | CBB | stop_interface handshake with PMA before MC6 power-gate; re-engages on exit | gfifo_empty detection; stop_interface / stop_interface_ack | PNC PM HAS §8.14.3 |
| FIVR | CBB | Module VR shutdown in MC6; C6SRAM content retained on vinf_aon | vinf_aon always-on; VCCmodule/VCCram gated in MC6 | DMR CBB PM HAS |
| MLC / L2$ | CBB | L2 flushed to L3 before MC6 entry; restored by first core on exit (DCM semaphore protocol) | MLC flush trigger; fast_init polling on exit; HW semaphore first/last | PNC PM HAS §8.14.3 |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Tensilica ACP) | CBB core perimeter | MC6 entry coordinator: evaluates all core states, triggers MLC shrink FSM, manages SRL engage, sequences power-gate | hal__get_is_module_in_mc6() L14971/L15131; MC6 entry conditions (7 gates); CPD interaction during MC6 | PNC PM HAS §8.14; Acode_PNC_SERVER.lst |
| uCode (PantherCove) | CBB core | Provides C6S MWAIT hint (with L2 shrink ucode_assist_info) that enables module MLC flush; acquires DCM semaphore on first-core exit | L2 shrink hint (C6S MWAIT); first/last semaphore acquire on MC6 exit; shared MLC state restore | PNC PM HAS §8.14 |
| PCode (CBB) | CBB | L2_DEMOTION_POLICY: dynamic hint (0x0–0x3) controlling MC3→MC6 flush aggressiveness; RESOLUTION_CONTROL.L2_FLUSH_DISALLOWED | L2_DEMOTION_POLICY CR; RESOLUTION_CONTROL programming; CBO BW hint processing | PNC PM HAS §8.14.3 |
| PrimeCode (IMH) | IMH | Receives HPM MC6 state from CBB PUnit; coordinates package-level idle if all modules in MC6 | HPM module_idle messages; package C-state aggregation | PrimeCode firmware |
| BIOS / UEFI | Platform | No direct MC6 knob — MC6 is automatically enabled when C6S MWAIT is used; BIOS sets C6Enable | C6Enable knob (enables C6S prerequisite for MC6) | BIOS PM HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MWAIT C6S | CPU instruction, EAX=0x23 | W | C6 with L2 flush — prerequisite for MC6 entry; sets L2 shrink ucode_assist_info | IA-32 SDM; PNC PM HAS §8.1.2 |
| MSR MC6 Residency | 0x664 | RO | Crystal cycles spent in Module C6 (MLC flushed, module power-gated) | PNC PM HAS §8.3.12 |
| MSR CC6 Residency | 0x3FD | RO | Crystal cycles spent in CC6 per core (prerequisite state before MC6) | PNC PM HAS §8.3 |
| RESOLUTION_CONTROL.L2_DEMOTION_POLICY | CR (PUnit-written) | RO to OS | 2-bit policy: 0x0=gradual, 0x3=instant flush; controls MC3→MC6 aggressiveness | PNC PM HAS §8.14.3 |
| RESOLUTION_CONTROL.L2_FLUSH_DISALLOWED | CR (PUnit-written) | RO to OS | When set, blocks MLC flush → module stays in MC3 | PNC PM HAS §8.14.3 |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| L2_DEMOTION_POLICY encoding | 0x0–0x3 | enum | 0x0=gradual demotion, 0x3=instant flush to MC6; set by PUnit dynamically | PNC PM HAS §8.14.3 |
| MC3→MC6 transition gate (TTT) | TTT < Threshold#1 | — | If wake deadline is near, PMA stays in MC3 instead of flushing to MC6 | PNC PM HAS §8.14.3 |
| MLC flush duration | Implementation-defined | — | L2+MLC flush required before power-gate; abortable on wake_req or S1-CPD | PNC PM HAS §8.14 |
| SRL engage latency | O(cycles) | — | FIL drains gfifo (snoopq_empty), issues stop_interface, receives ack | PNC PM HAS §8.14.3 |
| MC6 residency counter granularity | 1 crystal cycle | — | MSR 0x664 increments per crystal clock in MC6 | PNC PM HAS §8.3.12 |
| DCM semaphore protocol | First core wins | — | Second core waits for first core to restore shared MLC state on exit | PNC PM HAS §8.14 |

## NWP Delta

**MC6 (Module C6) is supported on NWP** — same architecture as DMR; MC6 is now the deepest idle state.

### Architecture Changes
- MC6 architecture unchanged: all cores in module in C6S, MLC flush, Q-channels deasserted, module power-gate
- NWP uses the same PantherCove (PNC) core as DMR — same Acode-managed MC6 FSM
- **MC6 is the deepest idle** on NWP (PkgC6 removed) — snoops handled by SRL until core wakeup
- Qchannel hints: cfcclk_qactive=0, cfcpwr_qactive=0, inf_qactive=0 (unchanged)

### Vs DMR
- Same MC6 definition but enters more frequently since PkgC6 is removed (MC6 is deepest idle)
- No PkgC6 flow to transition from MC6 into

### Validation Impact
- MC6 is the deepest idle state on NWP (no PkgC6 beyond it)
- Verify MC6 residency increases compared to DMR (where MC6 was transient to PkgC6)
- Verify SRL snoop handling in MC6 without subsequent PkgC6

## Legacy (Human-Curated Reference)

### Architecture Summary

Module C-State (MCx) represents the collective idle state of all cores within a **DCM (Dual Core Module) with shared MLC**. Module C-states are resolved by PMA/Acode after all enabled cores reach the required core C-state depth.

#### Module C-State Hierarchy *(confirmed: [PNC PM HAS §8.14](c:\github\NWP\PNC%20PM%20HAS%200.5_text.txt))*

| State | Core Condition | MLC Content | MLC Voltage | Snoops |
|-------|---------------|-------------|-------------|--------|
| **MC0** | ≥1 core at C0/C1 | Valid | Functional | Served |
| **MC1** | 1 core C1, other C1+ | Valid | Functional | Served |
| **MC1E** | 1 core C1E, other C1E+ | Valid | Functional | Served |
| **MC3** | All enabled cores in C6 | **Valid** | Functional | Served |
| **MC4** | All enabled cores in C6 | Valid | **Retention** | Not served |
| **MC6** | All enabled cores in C6 | **Flushed** | **Gated** | Served by SRL |

#### Q-Channel Resources per Module State *(confirmed: [PNC PM HAS §8.14](c:\github\NWP\PNC%20PM%20HAS%200.5_text.txt))*

| Module State | CFC_CLK.QACTIVE | CFC_PWR.QACTIVE | INF.QACTIVE | Description |
|-------------|-----------------|-----------------|-------------|-------------|
| MC0/MC1E/MC1T | 1 | 1 | 1 | All resources needed |
| **MC3** | **0** | 1 | 1 | CFC_CLK not needed — cores in C6, MLC not flushed |
| MC3' (transitional) | **1** | 1 | 1 | Re-asserts CFCCLK to regain uclk for MLC flush |
| MC4 | 0 | 1 | 1 | CFC_CLK not needed, SOC may lower voltage to retention |
| **MC6** | **0** | **0** | **0** | No resources needed — MLC flushed, power gated |

### Execution Flow

#### MC3 Entry *(confirmed: [PNC PM HAS §8.14.2](c:\github\NWP\PNC%20PM%20HAS%200.5_text.txt))*

```
Conditions: Both cores in C6 (powered off)
1. PMA→PUnit: deassert CFCCLK_QACTIVE (fabric clock not needed)
2. [Optional] PMA/Acode→PLL: switch to new Mclk frequency (lower power)
3. Module is now in MC3 by definition
   └── MLC content still valid, snoops still served (via PLL or SB clk)
```

#### MC3→MC6 Transition *(confirmed: [PNC PM HAS §8.14.3](c:\github\NWP\PNC%20PM%20HAS%200.5_text.txt))*

Conditions for MC6 entry (evaluated in priority order):
1. Module in MC3 (all enabled cores in C6)
2. No core_wake — PICLET reports no pending wakeup condition
3. TTT < Threshold#1 — if wake time is close, stay in MC3
4. PUnit L2_DEMOTION_POLICY: {0x0–0x2: increasingly aggressive demotion, 0x3: flush instantly}
5. Avoid-MC6 check: `RESOLUTION_CONTROL.L2_FLUSH_DISALLOWED` (if set, stay in MC3)
6. Avoid-MC3 check: PUnit static config (if set, skip MC3, flush immediately to MC6)
7. CBO hint: collocated CBO monitors fabric BW — blocks flush if BW too high

```
MC3 → MC6 Flow:
1. PMA calculates min(ARAT_TTT) of all cores
2. PMA MLC Shrink FSM triggered (abortable on wake_req or S1-CPD)
3. PMA→PUnit: assert CFCCLK_QACTIVE (regain fabric clock for flush)
4. PMA waits for CFCCLK in Q_RUN
5. PMA→MLC: request MLC flush
6. PMA detects module ready for MC6:
   ├── All cores in CC6
   ├── MLC flushed
   └── No wake requests pending
7. [If C6DRAM enabled] Offload C6SRAM to DRAM (disabled on LNC/DMR)
8. PMA→FIL: stop_interface + SRL engage
   ├── FIL waits for GFIFO to drain (snoopq_empty)
   └── SRL now provides default snoop response for sleeping module
9. FIL→PMA: interface stopped ack
10. PMA→PUnit: deassert CFCCLK_QACTIVE
11. PMA clock gates MLC clocks
12. PMA triggers PLL shutdown
13. PMA triggers C6SRAM power mux switch to vinf_aon
14. PMA asserts MLC Reset (clears first/last semaphore)
15. PMA deasserts PowerGood → module fully power-gated
```

#### MC6 Exit → MC3 → MC0

```
1. Wake trigger arrives at FIL/PICLET for any core in module
2. PMA reverse sequence: PowerGood → de-reset → PLL → clock → MLC init
3. First core reset handler:
   ├── Acquires semaphore (second core waits)
   ├── Restores shared MLC state
   ├── Polls MLC init completion (fast_init)
   ├── Clears LT_CRAM[Stop Snoops]
   └── Releases semaphore
4. Second core proceeds with its own C6 exit
5. Module returns to MC0 when any core reaches CC0
```

#### CPD Interaction *(confirmed: [PNC PM HAS §8.14](c:\github\NWP\PNC%20PM%20HAS%200.5_text.txt))*

- **S5-CPD while in MC6**: Core perimeter does NOT wake up cores. Sends CPD-ACK after Acode approval. Cores treated as acknowledged.
- **S1-CPD while in MC6**: Same — no core wake, CPD-ACK after Acode approval.
- **S5-CPD/S1-CPD not in MC6, one core active**: Sends CPD indication to active uCode, waits for acknowledge.
- **S5-CPD/S1-CPD not in MC6, one core in C6**: Does NOT wake the C6 core — treats as acknowledged.

### Key Registers & Interfaces

| Register | Description | Source |
|----------|-------------|--------|
| MSR `0x664` | MC6 residency counter (crystal cycles) | ✅ PNC PM HAS §8.3.12 |
| `RESOLUTION_CONTROL.L2_FLUSH_DISALLOWED` | Blocks L2 flush → stay in MC3 | ✅ PNC PM HAS §8.14.3 |
| `RESOLUTION_CONTROL.L2_DEMOTION_POLICY` | PUnit dynamic hint: 0x0–0x2 = progressive demotion, 0x3 = instant flush | ✅ PNC PM HAS §8.14.3 |
| `SRL` (Snoop Response Logic) | Default snoop response for sleeping module in MC6 | ✅ PNC PM HAS §8.14.3 |
| `CFCCLK_QACTIVE` | Fabric clock Q-channel active indication | ✅ PNC PM HAS §8.14 |
| `CFCPWR_QACTIVE` | Fabric power Q-channel active indication | ✅ PNC PM HAS §8.14 |
 