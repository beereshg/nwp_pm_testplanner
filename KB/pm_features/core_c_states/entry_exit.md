# Core C-States > Entry/Exit

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing added (2026-05-28)
> **Parent**: [Core C-States](core_c_states_main.md)

## Baseline (DMR)

Core C-state entry and exit is a **multi-agent coordinated flow** involving uCode, PMA (Core Power Management Agent), Acode (ACP firmware on Tensilica), PCode (CBB), and Primecode (IMH). The key architectural change in PNC/LNC (used in DMR/NWP) vs older generations is that **C-state management has moved inside the Core Perimeter** — the PMA/Acode now owns C-state entry/exit/demotion rather than the SoC-level PUnit.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| ACP / PMA | CBB | Core C-state FSM owner for entire entry/exit sequence; asserts/deasserts PowerGood, isolation, reset | core_active, cfcclk/pwr/inf_qactive, powergood, core_reset, core_isolation | PNC PM HAS §8.12 |
| PICLET / FIL | CBB | Entry: blocks break events at point-of-no-return; Exit: replays queued interrupts to APIC after C6SRAM restore | piclet_enable, piclet_replay_ack, gfifo_empty, stop_interface, interrupt_redirect | PNC PM HAS §8.12.2 |
| C6SRAM | CBB | State save on entry (GP/FP/APIC/CRegs per thread); state restore on exit; first core acquires HW semaphore | save/restore triggers; ML3_CR_PIC_BOOT_MESSAGE base addr; DCM semaphore | PNC PM HAS §8.12 |
| Q-channels (CFC_CLK / CFC_PWR / INF) | CBB | Entry: PMA deasserts when resources not needed; Exit: PMA reasserts to regain fabric clock/power | Q_CFC_CLK.qactive, Q_CFC_PWR.qactive, INF.qactive | PNC PM HAS §8.1 |
| FIVR | CBB | Entry: powers down core domain; vinf_aon retains C6SRAM; Exit: powers up, asserts PowerGood | VCCcore off; vinf_aon = 1; FIVR ramp-up on exit | DMR CBB PM HAS |
| SCF / Fabric | CBB + IMH | Fabric remains active during CC6 (snoops served); deactivated only at full package C6 | CFC_CLK/PWR Q-channel aggregation | DMR SoC PM HAS |
| ARAT-TTT (timer) | CBB | Written by uCode before C6 entry with wake deadline (CTC-based); fires break event via PICLET if no other wakeup | CORE_PMA_CR_ARAT_TTT; CTC comparison | PNC PM HAS §8.5.3 |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| uCode (PantherCove) | CBB core | Orchestrates full entry/exit: EAX parsing, demotion check, flush, PICLET setup, ARAT-TTT, point-of-no-return, C6 exit reset handler, PICLET replay | TC6 entry 10-step flow; ROB nukeaction (CC6 coordinator); PICLET enable/replay; CC6 exit reset handler; CC1→CC0 wake | PNC PM HAS §8.4; §8.12 |
| Acode (Tensilica ACP) | CBB core perimeter | C6Enter/C6Exit interrupt handler; budget release on entry; WP update and timer restart on exit | core_c6_enter() L15323; core_c6_exit() L15423; initiate_core_electric_budget_release_flow(); halt__common_actions_* | PNC PM HAS §8; Acode_PNC_SERVER.lst |
| PCode (CBB) | CBB | Budget negotiation on exit (INC_GB/DEC_GB); WISH_ALLOW and demotion policy; CRWr for ARAT-TTT and CORE_STATUS updates | INC_GB / DEC_GB commands; WP1/WP3/WP4 grant; RESOLUTION_CONTROL; CORE_STATUS update | PNC PM HAS §8.12 |
| PrimeCode (IMH) | IMH | Package C-state coordination; D2D fabric gating when all CBBs idle; HPM C-state messages | HPM PkgC_idle; D2D power-gating; cross-CBB package aggregation | PrimeCode firmware |
| BIOS / UEFI | Platform | Programs entry/exit knobs at boot; configures ACPI C-state objects for OS | C6Enable; C1AutoDemotion; MonitorMWait; ACPI _CST population | BIOS PM HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MWAIT | CPU instruction | W | Requests C-state; EAX[7:4]=state, EAX[3:0]=sub-state; all C6 variants (C6/C6A/C6S/C6SA/C6S-P) and C1/C1E | IA-32 SDM; PNC PM HAS §8.1.2 |
| MSR CLOCK_CST_CONFIG_CONTROL | 0xE2 | RW | Enable/disable C6 entry; C1/C3 demotion and undemotion controls | PNC PM HAS §8.6.5 |
| MSR CC1 Residency | 0x778 | RO | Crystal cycles in CC1 (including C1E); confirms C6 exit landing state | PNC PM HAS §8.3 |
| MSR CC6 Residency | 0x3FD | RO | Crystal cycles in CC6 power-gated state | PNC PM HAS §8.3 |
| MSR MC6 Residency | 0x664 | RO | Crystal cycles in Module C6 | PNC PM HAS §8.3.12 |
| CORE_PMA_CR_ARAT_TTT | CR (uCode-written) | WO from OS | Wake deadline timer written by uCode before C6 entry | PNC PM HAS §8.5.3 |
| CORE_PMA_CR_CORE_STATUS | CR (uCode-written) | RO to OS | Core C-state value updated by uCode on state transitions | PNC PM HAS §8.4 |
| CPUID.05H | Leaf 5, EDX | RO | Enumerates supported C-state sub-states and MWAIT hint encodings | IA-32 SDM |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| C6 exit latency (DMR target) | ~30 | µs | CC6 → CC0 via full PUnit budget negotiation path | DMR PSS KPI target |
| C6A (Autonomous) exit latency | < 30 | µs | No PUnit involvement; PMA retains electrical budget | PNC PM HAS §8.5 |
| C6 entry point of no return | After interrupt window | — | APIC state saved; global event inhibit set; no clean abort after this | PNC PM HAS §8.12 |
| Budget negotiation (INC_GB / DEC_GB) | Per C6 exit (non-auto) | — | PUnit → PMA handshake; WP1/3/4 update before core power-up | PNC PM HAS §8.12 |
| PICLET replay latency | < 1 | µs | FIL interrupt replay after C6SRAM restore; non-blocking for OS | PNC PM HAS §8.12.2 |
| C6 entry minTTT abort threshold | Workload-tuned | µs | minTTT < threshold → abort C6 entry → stay in C1 | PNC PM HAS §8.12 |
| CC6 entry coordination (2-thread) | Synchronous | — | ROB nukeaction fires on primary thread only after both threads reach TC6 | PNC PM HAS §8.12 |

## NWP Delta

**C-state entry/exit flows are supported on NWP** — same PantherCove (PNC) core as DMR; no core-level change.

### Architecture Changes
- NWP uses the same PantherCove (PNC) core as DMR — uCode, Acode, PCode manage C6 entry/exit as on DMR
- **No autonomous E-core C6** — core C6 requires the same Acode/PCode involvement as DMR
- **No PkgC6 entry/exit flows** (PkgC6 removed on NWP)
- With MKI/MCI introduction, some change in NIO/CBB interaction sequence expected — **TBD**

### Validation Impact
- Core C6 entry/exit latency tests: same scenarios as DMR (same PNC architecture, same FW agents)
- Module C6 (MC6) entry/exit: same Acode-managed flow as DMR
- **No PkgC6 entry/exit tests needed**
- Verify C6 exit latency KPIs (30 μs target from DMR — confirm applicability on NWP)

## Legacy (Human-Curated Reference)

### Architecture Summary

Core C-state entry and exit is a **multi-agent coordinated flow** involving uCode, PMA (Core Power Management Agent), Acode (ACP firmware on Tensilica), PCode (CBB), and Primecode (IMH). The key architectural change in PNC/LNC (used in DMR/NWP) vs older generations is that **C-state management has moved inside the Core Perimeter** — the PMA/Acode now owns C-state entry/exit/demotion rather than the SoC-level PUnit.

#### Thread vs Core vs Module vs Package C-States

| Level | Definition | FW Agent | Resolution |
|-------|-----------|----------|------------|
| **Thread C-state (TCx)** | Per-thread idle state (TC0→TC1→TC1E→TC6→TC7) | uCode | OS MWAIT/HLT → uCode updates `CORE_PMA_CR_THREAD_STATUS` |
| **Core C-state (CCx)** | `CCx = min(T1, T2, …Tn)` — all threads must be at TCx or deeper | uCode (coordination) | ROB triggers nukeaction when `thread_active=0` for all threads |
| **Module C-state (MCx)** | All cores in module at CCx or deeper; MLC flush possible | PMA/Acode | PMA evaluates all core states, negotiates Q-channels |
| **Package C-state (PCx)** | All modules idle; uncore resources can be powered down | PCode/Primecode | HPM coordination across CBBs/IMH |

#### C-State Hierarchy (PNC Enumeration) *(confirmed: [PNC PM HAS §8.1.2](c:\github\NWP\PNC%20PM%20HAS%200.5_text.txt))*

| C-state | MWAIT EAX | Sub-state | MLC Flush | PkgC Allowed | Turbo Upside | Autonomous Exit |
|---------|-----------|-----------|-----------|-------------|-------------|----------------|
| C1 | 0x00 | 0 (keep VR) | No | PC0 | No | Yes |
| C1E | 0x01 | 1 (lose VR) | No | PC0 | No | Yes |
| C1T | 0x02 | — | No | PC0 | Yes (partial) | No |
| C6 | 0x22 | — | No | PC0 | Yes (full) | No |
| C6A | 0x24 | — | No | PC0 | No | **Yes** |
| C6S | 0x23 | — | **Yes** | PC0 | Yes (full) | No |
| C6S-P | 0x20 | — | **Yes** | **PC6** | Yes (full) | No |
| C6SA | 0x25 | — | **Yes** | PC0 | No | **Yes** |

**Key insight**: PNC introduces fine-grained MWAIT sub-states with knobs: **P** (Package), **A** (Autonomous), **S** (cache flush), **T** (Turbo update), **E** (Efficiency/C1E). These are handled inside PMA, not exposed to SoC.

#### Q-Channel Resource Negotiation Rules *(confirmed: [PNC PM HAS §8.1.2](c:\github\NWP\PNC%20PM%20HAS%200.5_text.txt))*

- PMA relinquishes `CFC_CLK` Q-channel only if **all cores** requested MWAIT with **P** (Package) bit
- PMA relinquishes `CFC_PWR` Q-channel only if **all cores** requested MWAIT with **S** (flush) AND **P** (Package) bits
- **Autonomous** (A) MWAIT: PMA does **not** relinquish electrical budget — core can exit C6 without SoC involvement
- **Efficiency** (E/C1E) MWAIT: core relinquishes voting rights only

### Execution Flow

#### C-State Entry — General Flow *(confirmed: [PNC PM HAS §8.4](c:\github\NWP\PNC%20PM%20HAS%200.5_text.txt))*

```
1. OS/SW issues MWAIT(EAX=target C-state, sub-state) or HLT
   ├── uCode parses EAX[7:4] = target C-state, EAX[3:0] = sub-state
   └── uCode reads CORE_PMA_CR_IO_UCODE_CFG.WISH_ALLOW for demotion check

2. Thread-Level Entry (TC1/TC6/TC7)
   ├── Flush TLB (if partitioned), purge IFU
   ├── Freeze APIC counters
   ├── Set up event inhibits
   ├── Update CORE_PMA_CR_THREAD_STATUS (thread_state, wish_state, wish_substate)
   └── Issue sleep_nuke → thread goes to sleep

3. Core-Level Coordination (CC6 only — when ALL threads at TC6)
   ├── ROB detects: (thread_active == 0) AND (MISC_POWER[C3_C6_C7] set on both threads)
   ├── ROB injects nukeaction event to PRIMARY thread
   ├── Primary thread wakes, verifies other thread still asleep
   ├── Core caches flushed: DCU wbinvd, I-$ invalidate, victim-$ invalidate
   ├── Core control registers saved to C6SRAM (base address from ML3_CR_PIC_BOOT_MESSAGE)
   ├── minTTT calculated: if TTT-CTC < C6_threshold → early exit to C1
   ├── Write CORE_PMA_CR_ARAT_TTT with wake deadline
   ├── PICLET setup: uCode configures FIL_CR_PIC_CONFIG0/1, enables PICLET
   ├── PMA→FIL: interrupt redirection to PICLET enabled
   ├── FIL→PMA: piclet_enable_ack
   ├── *** POINT OF NO RETURN ***
   │   ├── Open interrupt window — last abort chance
   │   ├── If pending break events → abort to C0
   │   └── Else: Set ML3_CR_PIC_GLOBAL_EVENT_INHIBIT (all interrupts inhibited except Wake/Reset)
   ├── Save APIC state to C6SRAM
   ├── Update CORE_PMA_CR_CORE_STATUS (core_state=CC6, wish, substate)
   └── Core_active deasserts → core clock trunks gated

4. Acode/PMA Electrical Phase
   ├── PMA→Acode: C6Enter interrupt
   │   ├── Acode disables non-C6 timers
   │   └── Acode sets Acode_C6_ENTRY_BP=0
   ├── PMA→PUnit: CRWr update CCP_ARAT_TTT + Core_status in punit
   ├── PMA asserts inner core reset
   ├── PMA shuts off clocks → Core acknowledges clock gating
   ├── PMA enables isolation for inner core
   └── PMA deasserts PowerGood → core powered down

5. Acode Function: core_c6_enter() [Acode_PNC_SERVER.lst L15323]
   ├── halt__common_actions_for_c6_enter_and_ecp_en_during_c6(scope)
   ├── initiate_core_electric_budget_release_flow(scope)
   │   └── If blocked: wpu__request_block_core(scope)
   └── Return
```

#### C-State Exit — Staged Exit Flow *(confirmed: [PNC PM HAS §8.12.3–8.12.4](c:\github\NWP\PNC%20PM%20HAS%200.5_text.txt))*

```
1. Wake Trigger
   ├── FIL/PICLET detects break event (IPI, MSI, VLW, Monitor, Timer, Sideband)
   └── PICLET→PMA: wake request

2. PMA/Acode Wake Sequence
   ├── PMA→Acode: C6Exit interrupt
   │   ├── Acode restarts timers with remaining time
   │   └── Acode clears in_C6_state flag
   ├── PMA asserts *_Qactive indications (cfcpwr, cfcclk, inf)
   ├── PMA waits for fabric wake (cfcpwr/cfcclk_qreq_b = '0)
   ├── PMA→PUnit: Update CORE_STATUS[state] (core is electrically out of C6)

3. Budget Negotiation (if no budget cached)
   ├── PMA→PUnit: budget request (ICCP_request)
   ├── PUnit→PMA: WP1, WP3, WP4 updates
   ├── PUnit→PMA: INC_GB command → PMA returns INC_GB_ACK
   ├── PUnit→PMA: DEC_GB command → PMA returns DEC_GB_ACK
   ├── PMA→Acode: FGV change interrupt
   └── Acode→PMA: update WP CRs

4. Electrical Power-Up
   ├── PMA→PD: power up CoreN domain
   ├── PMA→Core: assert CoreN PowerGood
   ├── PMA→CLK: reset throttle on (TBD if other core is also exiting)
   └── PMA deasserts Reset for CoreN domain

5. uCode Core Reset Handler (CC6 → CC1)
   ├── uCode initializes marbles, arch registers (Int + FP)
   ├── Trigger I-$ and DL1$ initialization
   ├── Read CORE_WAKEUP_INFO.RESET_TYPE:
   │   ├── C6_EXIT: restore from C6SRAM
   │   ├── CRST_WARM_INIT: exit from C6 with warm reset (skip C6 restore)
   │   └── CRST_COLD: full cold reset init
   ├── Restore patch state, core CRegs, APIC state
   ├── Semaphore check (DCM: first core gets semaphore, second waits)
   ├── If first core exiting MC6: restore shared state, poll MLC init, clear LT_CRAM
   ├── PICLET disable + replay: FIL replays queued interrupts back to APIC
   │   ├── FIL blocks incoming interrupts during replay
   │   ├── FIL disables interrupt redirection to PICLET
   │   ├── FIL unblocks U2C path
   │   └── FIL sets piclet_replay_ack
   ├── Restore Core MLC state
   ├── Core now at CC1, threads still at TCx
   └── Wait for real break event

6. Thread Wake (CC1 → CC0)
   ├── Break event propagates to APIC → thread wakes up
   ├── uCode runs TCx unwind flow (per-thread state restore)
   ├── Update THREAD_STATUS(TC0) + CORE_STATUS(CC0)
   └── Core fully operational

7. Acode Function: core_c6_exit() [Acode_PNC_SERVER.lst L15423]
   ├── halt__common_actions_for_c6_exit_and_ecp_en_while_core_not_in_c6(scope)
   ├── timer__restart_core_c6_dis_timers(scope)
   ├── tm_add_task(TASK_ID_A2U_E, scope)
   ├── timer__get_absolute_time_nsec(&curr_ts)
   └── crbus__read_core_crs_defaults_or_restore_crs(scope)
```

#### Abort / Unwind Points *(confirmed: [PNC PM HAS §8.12.2](c:\github\NWP\PNC%20PM%20HAS%200.5_text.txt))*

During C-state entry there are specific interrupt windows where abort is possible:

| Abort Point | Condition | Action |
|------------|-----------|--------|
| After TC6 sleep_nuke | Break event to thread | TC6 unwind → return to TC0 |
| After coordination start, PIC-End loop | Break event for primary thread | Primary runs `primary_thread_unwind_after_coordination` |
| After coordination start, PIC-End loop | Break event for secondary thread only | Primary unwinds coordination, returns to TCx sleep |
| After PICLET enable, final int window | Break event detected | Last abort — full CCx unwind |
| **After point of no return** | **No abort possible** | Must complete to CC6, then exit normally |

### Key Registers & Interfaces

| Register | Description | Source |
|----------|-------------|--------|
| `CORE_PMA_CR_THREAD_STATUS` | Thread state (wish, current, sub-state) — written by uCode | ✅ PNC PM HAS §8.4 |
| `CORE_PMA_CR_CORE_STATUS` | Core state (CC0/CC1/CC6) — written by uCode at coordination, updated by PMA at exit | ✅ PNC PM HAS §8.12 |
| `CORE_PMA_CR_IO_UCODE_CFG.WISH_ALLOW` | Merged demotion control (PUnit + Acode) — read by uCode | ✅ PNC PM HAS §8.6 |
| `CORE_PMA_CR_ARAT_TTT` | Wake deadline (absolute CTC time) — written by uCode, consumed by PMA | ✅ PNC PM HAS §8.5.3 |
| `CORE_PMA_CR_CONFIG_0[C1E]` | C1E enable bit — read by uCode during entry | ✅ PNC PM HAS §8.5.4 |
| `FIL_CR_PIC_CONFIG0/1` | PICLET configuration — written by uCode at CC6 coordination | ✅ PNC PM HAS §8.12.2 |
| `ML3_CR_PIC_GLOBAL_EVENT_INHIBIT` | Global interrupt inhibit (point of no return) | ✅ PNC PM HAS §8.12.2 |
| `ML3_CR_PIC_BOOT_MESSAGE` | C6SRAM base address in MLC | ✅ PNC PM HAS §8.12.2 |
| `CORE_WAKEUP_INFO` | Reset type + last C-state type — read by uCode at exit | ✅ PNC PM HAS §9 |
| `ROB1_CR_MISC_POWER[C3_C6_C7]` | Per-thread coordination request bit | ✅ PNC PM HAS §8.12.2 |
| `ROB1_CR_MISC_INFO[C3_C6_C7]` | Coordination-done bit (shared CR) | ✅ PNC PM HAS §8.12.2 |
| MSR `0xE2` (CLOCK_CST_CONFIG_CONTROL) | C6 demotion enable/disable (reflected in RESOLUTION_CONTROL) | ✅ PNC PM HAS §8.6.5 |
| MSR `0x3FD` | CC6 residency counter (crystal cycles) | ✅ PNC PM HAS §8.3 |
| MSR `0x664` | MC6 residency counter (crystal cycles) | ✅ PNC PM HAS §8.3.12 |

 