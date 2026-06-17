# SoC Thermal > Thermal Interrupts

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SoC Thermal](soc_thermal_main.md)

## Baseline (DMR)

**What it does**: Thermal interrupts are the OS notification path for PM events — delivered via LVT Thermal Interrupt (APIC vector) or SMI. PCode evaluates enable bits vs status bits each slow-loop and writes core PMA CRs directly over GPSB (GNR+); CCP generates the local LVT interrupt autonomously.

**Topology**:
```
Root IMH PrimeCode ─HPM DNS_EVENT_DELIVERY[THERMAL_INTERRUPT] (RR=1)─> CBB0..N
CBB PCode ──────────────────────────────────────────────────────────────┤
  Writes U2C_CR_EVENTS_DIRECTED[THRMINT] via GPSB                      │
  (GNR+: direct, no uBox intermediary)                                  │
CCP (per-core) ─────────────────────────────────────────────────────────┘
  Detects status/log transition matching enabled interrupt bit
  Generates LVT Thermal Interrupt → Core ISR reads IA32_THERM_STATUS
  [DOMA/SKT: CCP generates autonomously; BigCore: PCode-triggered]
LOCK_THERM_INT=1 → any core event UPS_EVENT_DELIVERY → Root → all-cores DNS
```

**Key operational principle**: Core scope = `IA32_THERM_INTERRUPT` (0x19B) enables → `IA32_THERM_STATUS` (0x19C) log bits. Package scope = `IA32_PACKAGE_THERM_INTERRUPT` (0x1B2) → `IA32_PACKAGE_THERM_STATUS` (0x1B1) log bits. PCode writes `THERM_STATUS_UPDATE` PMA CR only when status changes (avoids unnecessary PMSB traffic). Package interrupt propagation: ~100s μS latency from Root detection to leaf core delivery.

**Boot activation**: Interrupts active after BIOS configures `IA32_THERM_INTERRUPT` and `IA32_PACKAGE_THERM_INTERRUPT`; S0 and S1 only (inhibited in S1, not functional in S3/S4).

Thermal interrupts are the mechanism by which PCode notifies OS/SW of power-management events. Intel server CPUs use the **LVT Thermal Interrupt** vector (a dedicated APIC vectored interrupt) or optionally **SMI** to deliver these notifications. Multiple PM features piggyback on this architecture: Socket Thermal, HWP, HGS, Pmax, and Prochot.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| APIC LVT Thermal Interrupt | Per-core | Hardware interrupt vector delivery; dedicated thermal LVT entry in local APIC; also carries HWP/HGS interrupts | LVT register in APIC; CCP LVT thermal entry | Intel SDM |
| CCP (per-core) | CBB Top Die | Autonomous interrupt generation (GNR+/DOMA): detects status/log bit transitions matching enabled bits → fires LVT interrupt | `U2C_CR_EVENTS_DIRECTED[THRMINT]`; `U2C_CR_EVENTS_BROADCAST[PCUSMI]` | CBB Thermal Mgmt HAS |
| GPSB bus | IMH→CBB | Direct portid-override writes from PCode to CCP PMA CRs (GNR+: no uBox intermediary) | GPSB transaction | CBB Thermal Mgmt HAS |
| HPM bus | IMH↔CBBs | Carries `DNS_EVENT_DELIVERY[THERMAL_INTERRUPT]` (Root→Leaf, RR=1) and `UPS_EVENT_DELIVERY[THERMAL_INTERRUPT]` (Leaf→Root for LOCK_THERM_INT) | HPM message bus | Socket Thermal HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| Acode (Core microcode) | Core PMA | No thermal interrupt generation role (GNR+: CCP generates autonomously); Core EMTTM PID feeds status bits | — | — |
| PCode (CBB) | CBB Base Die | Evaluates per-CCP thermal status each slow loop; writes `THERM_STATUS_UPDATE` PMA CR (only on change); sends `UPS_EVENT_DELIVERY` to Root if `LOCK_THERM_INT=1` | `ThermalReport::update_ccp_therm_status_tx()`; `IO_THERM_INTERRUPT` read; `THERM_STATUS_UPDATE` write | CBB Thermal Mgmt HAS |
| PrimeCode (IMH) | IMH die | Aggregates package telemetry; evaluates `IA32_PACKAGE_THERM_INTERRUPT` thresholds; sends `DNS_EVENT_DELIVERY[THERMAL_INTERRUPT]` (RR=1) to all leaf CBBs; generates local pkg interrupts | HPM `DNS_EVENT_DELIVERY`; `IO_MISC_PCODE_HW_COMMANDS[SEND_CORES_THERMAL_INTERRUPT_MULTICAST]` | Socket Thermal HAS |
| BIOS / UEFI | Platform | Configures `IA32_THERM_INTERRUPT` and `IA32_PACKAGE_THERM_INTERRUPT` enable bits; programs threshold1/2 relative temperature values | Boot-time MSR programming | Intel SDM |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| MSR `IA32_THERM_INTERRUPT` | 0x19B (per-core) | RW | [0] HIGH_TEMP_INT_EN; [1] LOW_TEMP_INT_EN; [2] PROCHOT_INT_EN; [4] OOS_INT_EN; [14:8] THRESHOLD1_REL_TEMP; [15] THRESHOLD1_INT_EN; [22:16] THRESHOLD2_REL_TEMP; [23] THRESHOLD2_INT_EN | Intel SDM |
| MSR `IA32_THERM_STATUS` | 0x19C (per-core) | RO/RWC | [0/1] THERMAL_MONITOR_STATUS/LOG; [2/3] PROCHOT_STATUS/LOG; [4/5] OOS_STATUS/LOG; [6/7] THRESHOLD1_STATUS/LOG; [8/9] THRESHOLD2_STATUS/LOG; [10/11] POWER_LIMIT_STATUS/LOG; [23:16] TEMPERATURE | Intel SDM |
| MSR `IA32_PACKAGE_THERM_INTERRUPT` | 0x1B2 | RW | Package-scope enable bits: HIGH_TEMP[0], LOW_TEMP[1], PROCHOT[2], OOS[4], THRESHOLD1[14:8/15], THRESHOLD2[22:16/23], PMAX[?], HW_FEEDBACK_NOTIFICATION[?] | Intel SDM |
| MSR `IA32_PACKAGE_THERM_STATUS` | 0x1B1 | RO/RWC | Package-scope status/log: THERMAL_MONITOR[0/1], PROCHOT[2/3], OOS[4/5], THRESHOLD1[6/7], THRESHOLD2[8/9], POWER_LIMIT[10/11], PMAX[12/13], HW_FEEDBACK_NOTIFICATION_LOG[26]; TEMPERATURE[23:16] | Intel SDM |
| MSR `MSR_MISC_PWR_MGMT` | 0x1AA | RW | [22] `LOCK_THERM_INT` — escalates core thermal interrupts to package-scope (deprecated since GNR) | Intel SDM |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| Core interrupt latency | ~1 | mS | PCode slow-loop evaluation → `THERM_STATUS_UPDATE` write → CCP fires LVT | Legacy Execution Flow |
| Package interrupt propagation | ~100s | μS | Root detects event → HPM DNS_EVENT_DELIVERY → leaf CBB writes PMA CR → CCP fires LVT | Legacy Execution Flow |
| EWMA filter (α) | 0.7 | — | Applied to per-CCP temp before THERMAL_MONITOR_STATUS evaluation for interrupt | Legacy Execution Flow |
| PCode status-write guard | On change only | — | `THERM_STATUS_UPDATE` written only when status changes from previous; avoids unnecessary PMSB traffic | Legacy Execution Flow |
| SMI thermal mode cadence | N/A | — | `THERM_EVENT_FFM[ENABLE_FFM]=1` → SMI on all thermal events (legacy BIOS path; deprecated since GNR) | Legacy Execution Flow |
| C6 interrupt handling | Pend | — | GNR+: interrupt pended when core in C6; sent on C6 exit (changed from legacy skip) | Legacy Cross-Product table |

## NWP Delta

**Thermal interrupts are fully supported on NWP** — no changes from DMR.

- `IA32_THERM_INTERRUPT` (0x19B) and `IA32_PACKAGE_THERM_INTERRUPT` (0x1B2) MSRs supported
- Thermal LVT interrupt delivery unchanged
- HWP interrupt reuse of thermal interrupt vector unchanged
- Thermal interrupt functionality: S0 and S1 only (inhibited in S1, not functional in S3/S4)

### Validation Impact
- Same thermal interrupt test cases apply
- Verify interrupt delivery with NWP CBB topology (2 CBBs)

## Legacy (Human-Curated Reference)

### Architecture Summary

Thermal interrupts are the mechanism by which PCode notifies OS/SW of power-management events. Intel server CPUs use the **LVT Thermal Interrupt** vector (a dedicated APIC vectored interrupt) or optionally **SMI** to deliver these notifications. Multiple PM features piggyback on this architecture: Socket Thermal, HWP, HGS, Pmax, and Prochot.

#### Interrupt Types

| Type | Vector | Delivery | Usage |
|------|--------|----------|-------|
| **LVT Thermal Interrupt** | Dedicated vector ID | APIC → ISR | Default: OS thermal handler |
| **SMI** | Non-vectored | SMM handler | Legacy BIOS thermal management (`THERM_EVENT_FFM[ENABLE_FFM]=1`) |

#### Scope Model

| Scope | Trigger Source | Delivery Target | Enable Register | Status Register |
|-------|---------------|-----------------|-----------------|-----------------|
| **Core** | Per-CCP thermal event | Specific core only | `IA32_THERM_INTERRUPT` (0x19B) | `IA32_THERM_STATUS` (0x19C) |
| **Package** | Package-level event (OOS, PROCHOT, HW_FEEDBACK) | All cores (or masked subset) | `IA32_PACKAGE_THERM_INTERRUPT` (0x1B2) | `IA32_PACKAGE_THERM_STATUS` (0x1B1) |

#### Multi-Die Interrupt Delivery (GNR/DMR)

```
Root (iMH)                              Leaf CBBs
┌──────────────────┐                    ┌──────────────────┐
│ Aggregates pkg   │  DNS_EVENT_DELIVERY│ Receives HPM     │
│ telemetry from   │ ───────────────→   │ Writes core CRs: │
│ all leaves       │    (RR=1)          │ U2C_DIRECTED_    │
│                  │                    │ EVENTS[THRMINT]  │
│ Evaluates pkg    │ ←───────────────   │                  │
│ thresholds       │  DNS_EVENT_DELIVERY│ Generates local  │
│                  │    (Ack)           │ LVT interrupt    │
│ Updates local    │                    │ to its cores     │
│ PACKAGE_THERM_   │                    └──────────────────┘
│ STATUS           │                    ┌──────────────────┐
│ Generates local  │  DNS_EVENT_DELIVERY│ Same as above    │
│ interrupts       │ ───────────────→   │ for LeafN        │
└──────────────────┘                    └──────────────────┘
```

**Key change from SPR**: Starting GNR, PCode writes core CRs `U2C_CR_EVENTS_DIRECTED[THRMINT]` and `U2C_CR_EVENTS_BROADCAST[PCUSMI]` **directly over GPSB** (no uBox intermediary). For BigCore, these are `U2C_DIRECT_EVENTS` and `U2C_BROADCAST_EVENTS` (both CCP-scoped).

#### DOMA/T2C Impact on Interrupts

With DOMA (SKT/LNC cores), the CCP handles interrupt register ownership:

| Aspect | BigCore (non-DOMA) | SKT (DOMA) |
|--------|-------------------|------------|
| `THERM_INTERRUPT` | CCP-scoped, SW rd/wr to PUnit IO | Per-core instance in CCP, CCP aggregates to module CR for PUnit |
| `THERM_STATUS` | PCode updates PUnit IO, PUnit computes log bits | Per-core instance in CCP, PCode updates PUnit IO + CCP CR, CCP computes log bits |
| Interrupt generation | PCode generates | **CCP generates autonomously** based on log/status bits |
| Exception | LOCK_THERM_INT and SMI always PCode-generated | Same |

PCode writes `THERM_STATUS_UPDATE` (PMA CR, module-scoped, over PMSB) whenever status changes. PCode must write all fields **except**: log bits (CCP-computed), TEMPERATURE, RESOLUTION, VALID.

---

### Execution Flow

#### Core Thermal Interrupt Flow

1. **PCode evaluates** per-CCP thermal status each slow loop (`ThermalReport::update_ccp_therm_status_tx`)
2. **PCode reads** `IO_THERM_INTERRUPT` for the CCP to check which interrupts are enabled
3. **PCode computes** status bits:
   - `THERMAL_MONITOR_STATUS` = EWMA-filtered temp ≥ eff_tj_max (0→1: HIGH_TEMP, 1→0: LOW_TEMP)
   - `THRESHOLD1/2_STATUS` = temp_delta ≤ threshold relative temp
   - `PROCHOT_STATUS` = live prochot wire state from `IO_INTERDIE_THROTTLE_SIGNALS_STATUS`
   - `POWER_LIMITATION_STATUS` = PLR indicates CCP is power limited
   - `CURRENT_LIMIT_STATUS` = same source as power limitation
4. **PCode writes** `THERM_STATUS_UPDATE` PMA CR (only if changed from last write — avoids unnecessary PMSB traffic)
5. **CCP detects** status/log bit transition matching enabled interrupt → generates LVT Thermal Interrupt to core
6. **OS ISR** reads `IA32_THERM_STATUS`, processes event, clears log bits

#### Package Thermal Interrupt Flow

1. **Root PCode (iMH)** receives periodic `SOCKET_THERMAL` telemetry HPM from all leaf CBBs
2. **Root aggregates** telemetry → computes package min/max temps, margins
3. **Root evaluates** against `IA32_PACKAGE_THERM_INTERRUPT` thresholds
4. **Root updates** local `IA32_PACKAGE_THERM_STATUS` and generates local interrupts
5. **Root sends** `DNS_EVENT_DELIVERY[THERMAL_INTERRUPT]` HPM (RR=1) to all leaf CBBs
6. **Each leaf PCode** receives HPM → writes `IO_MISC_PCODE_HW_COMMANDS[SEND_CORES_THERMAL_INTERRUPT_MULTICAST]=1` → interrupts all local cores
7. **Leaf sends** `DNS_EVENT_DELIVERY` (Ack) back to Root

**Propagation delay**: ~100s of μS between root detecting event and leaf cores receiving interrupt (due to HPM message latency).

#### LOCK_THERM_INT Flow (Core → Package Escalation)

When `MSR_MISC_PWR_MGMT[LOCK_THERM_INT]=1`:

1. PCode sets `RESOLUTION_CONTROL[LOCK_THERM_INT]` in all CCPs → disables autonomous CCP interrupt generation
2. On any core thermal event → leaf PCode sends `UPS_EVENT_DELIVERY[THERMAL_INTERRUPT]` (RR=1) to Root
3. Root sends `DNS_EVENT_DELIVERY` to all leaves → all cores get interrupted
4. Effectively transforms core-scoped interrupt into package-scoped

> **Deprecation note**: `LOCK_THERM_INT` and `THERM_EVENT_FFM` not documented in customer-facing docs since GNR. Expected to be deprecated in future SoCs.

#### SMI Flow (THERM_EVENT_FFM)

When `THERM_EVENT_FFM[ENABLE_FFM]=1`:

1. CPU generates SMI instead of LVT thermal interrupt for ALL thermal events
2. Leaf sends `UPS_EVENT_DELIVERY` to Root (does NOT send local interrupts)
3. Root checks `THERM_EVENT_FFM[ENABLE_FFM]` → sets `FFM_SMI_SIGNALED=1` → triggers SMI
4. Root sends `DNS_EVENT_DELIVERY` to all leaves → leaves also generate SMI
5. All cores enter SMM → BIOS SMM handler reads status registers, clears `FFM_SMI_SIGNALED`
6. PCode waits for SW to clear `SMI_SIGNALED` bits before issuing another SMI

#### Cross-Product: Core C-States

| Core State | Interrupt Behavior (GNR+) |
|------------|--------------------------|
| C0 | Normal delivery |
| C6 | **Pend** the interrupt — send when core exits C6 (changed from legacy "skip") |
| C6 + SMI | Send immediately — SMI requires all cores to halt |
| C6 + LOCK_THERM_INT | May pend, send, or skip (implementation choice) |
| SKT/DOMA cores | PCode doesn't know core C-state → CCP handles: triggers interrupt after core exits C6 |

#### Cross-Product: SST-PP Level Change

During dynamic SST-PP level switch, SW offlines/C6s some cores. PCode should NOT send interrupts to cores being offlined to avoid spurious wakes and performance jitter.

---

### Key Registers & Interfaces

#### Interrupt Trigger Table

| Enable Bit | Trigger Condition | Comments |
|------------|-------------------|----------|
| `IA32_THERM_INTERRUPT[HIGH_TEMP_INT_ENABLE]` (bit 0) | `THERM_STATUS[THERMAL_MONITOR_STATUS]` 0→1 | Temperature crossed above trip point |
| `IA32_THERM_INTERRUPT[LOW_TEMP_INT_ENABLE]` (bit 1) | `THERM_STATUS[THERMAL_MONITOR_STATUS]` 1→0 | Temperature dropped below trip point |
| `IA32_THERM_INTERRUPT[PROCHOT_INT_ENABLE]` (bit 2) | `THERM_STATUS[PROCHOT_STATUS]` 0→1 or 1→0 | SDM expects interrupt only on 0→1 of `PROCHOT_LOG` |
| `IA32_THERM_INTERRUPT[OOS_INT_ENABLE]` (bit 4) | `THERM_STATUS[OOS_STATUS]` 0→1 or 1→0 | SDM expects interrupt only on 0→1 of `OOS_LOG` |
| `IA32_THERM_INTERRUPT[THRESHOLD1_INT_ENABLE]` (bit 15) | `THERM_STATUS[THRESHOLD1_STATUS]` 0→1 or 1→0 | Relative temp in bits [14:8] |
| `IA32_THERM_INTERRUPT[THRESHOLD2_INT_ENABLE]` (bit 23) | `THERM_STATUS[THRESHOLD2_STATUS]` 0→1 or 1→0 | Relative temp in bits [22:16] |
| `IA32_THERM_INTERRUPT[POWER_LIMIT_INT_ENABLE]` | `THERM_STATUS[POWER_LIMIT_STATUS]` 0→1 or 1→0 | SDM expects only 0→1 of `POWER_LIMIT_LOG` |
| `IA32_PACKAGE_THERM_INTERRUPT[HW_FEEDBACK_NOTIFICATION_ENABLE]` | `PKG_THERM_STATUS[HW_FEEDBACK_NOTIFICATION_LOG]` 0→1 | HFI/HGS table update |
| `IA32_PACKAGE_THERM_INTERRUPT[PMAX_INT_ENABLE]` | `PKG_THERM_STATUS[PMAX_LOG]` 0→1 | Pmax event |

#### Core-Scope MSRs

| MSR | Address | Key Fields |
|-----|---------|------------|
| `IA32_THERM_STATUS` | 0x19C | `THERMAL_MONITOR_STATUS[0]`, `LOG[1]`, `PROCHOT_STATUS[2]`, `LOG[3]`, `OOS_STATUS[4]`, `LOG[5]`, `THRESHOLD1_STATUS[6]`, `LOG[7]`, `THRESHOLD2_STATUS[8]`, `LOG[9]`, `POWER_LIMIT_STATUS[10]`, `LOG[11]`, `CURRENT_LIMIT[12]`, `LOG[13]`, `CROSS_DOMAIN[14]`, `LOG[15]`, `TEMPERATURE[23:16]`, `RESOLUTION[30:27]`, `VALID[31]` |
| `IA32_THERM_INTERRUPT` | 0x19B | `HIGH_TEMP_INT_EN[0]`, `LOW_TEMP_INT_EN[1]`, `PROCHOT_INT_EN[2]`, `OOS_INT_EN[4]`, `THRESHOLD1_REL_TEMP[14:8]`, `THRESHOLD1_INT_EN[15]`, `THRESHOLD2_REL_TEMP[22:16]`, `THRESHOLD2_INT_EN[23]`, `HW_FEEDBACK_NOTIFICATION_ENABLE[25]` (directed pkg interrupt, future) |

#### Package-Scope MSRs

| MSR | Address | Key Fields |
|-----|---------|------------|
| `IA32_PACKAGE_THERM_STATUS` | 0x1B1 | `THERMAL_MONITOR_STATUS[0]`, `PROCHOT_STATUS[2]`, `OOS_STATUS[4]`, `THRESHOLD1_STATUS[6]`, `THRESHOLD2_STATUS[8]`, `POWER_LIMIT_STATUS[10]`, `PMAX_STATUS[12]`, `HW_FEEDBACK_NOTIFICATION_LOG[26]`, `TEMPERATURE[23:16]`, `VALID[31]`, `DIRECTED_PKG_THERMAL_INTERRUPT_ACK[25]` (future) |
| `IA32_PACKAGE_THERM_INTERRUPT` | 0x1B2 | `HIGH_TEMP_INT_EN[0]`, `LOW_TEMP_INT_EN[1]`, `PROCHOT_INT_EN[2]`, `OOS_INT_EN[4]`, `THRESHOLD1_REL_TEMP[14:8]` + `INT_EN[15]`, `THRESHOLD2_REL_TEMP[22:16]` + `INT_EN[23]`, `PMAX_INT_EN[?]`, `HW_FEEDBACK_NOTIFICATION_EN[?]` |

#### Control MSRs

| MSR | Address | Key Fields |
|-----|---------|------------|
| `MSR_MISC_PWR_MGMT` | 0x1AA | `LOCK_THERM_INT[22]` — if set, core thermal interrupt sent to ALL cores |
| `THERM_EVENT_FFM` | 0x5E | `ENABLE_FFM[0]` — SMI instead of LVT thermal. `FFM_SMI_SIGNALED[1]` — SMI was thermal. `FFM_MCP_SMI_SIGNALED[2]` — SMI was MCP thermal |

#### HPM Messages

| Message | Direction | Purpose |
|---------|-----------|---------|
| `DNS_EVENT_DELIVERY` | Root → Leaf | `Event[0]` = Thermal Interrupt. RR=1 requests Ack. |
| `UPS_EVENT_DELIVERY` | Leaf → Root | `Event[0]` = Thermal Interrupt. Used for LOCK_THERM_INT and THERM_EVENT_FFM escalation. |
| `SOCKET_THERMAL` | Leaf → Root | Periodic telemetry (OOS, temps, margins) — triggers pkg interrupt evaluation |

#### PCode Internal Registers

| Register | Description |
|----------|-------------|
| `THERM_STATUS_UPDATE` (PMA CR) | PCode writes to CCP to update status bits (module-scoped, PMSB) |
| `IO_MISC_PCODE_HW_COMMANDS` | `SEND_CORES_THERMAL_INTERRUPT_MULTICAST[bit]` — PCode writes 1 to broadcast interrupt |
| `RESOLUTION_CONTROL` | `LOCK_THERM_INT` — disables CCP autonomous interrupt generation |
| `U2C_DIRECT_EVENTS` | `THRMINT` — PCode writes to trigger directed LVT thermal interrupt (BigCore CCP-scoped) |
| `U2C_BROADCAST_EVENTS` | `PCUSMI` — PCode writes to trigger SMI (BigCore CCP-scoped) |

---

### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS (PM Interrupt) | [PM Interrupt Arch HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/pm_interrupt_arch/pm_interrupt_arch.html) | Primary spec — interrupt triggers, multi-die delivery, DOMA, C-state cross-product |
| HAS (Socket Thermal) | [Socket Thermal Mgmt](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_Thermal_Mgmt/Socket_Thermal_Mgmt_HAS.html) | Package thermal interrupt evaluation at iMH |
| HAS (CBB Thermal Mgmt) | [DMR CBB Thermal Management](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Thermal/Thermal%20Management/Thermal%20Management.html) | PCode `THERM_STATUS_UPDATE` writes, OOS detection |
| PCode src | `source/pcode/flows/thermals/thermal_report.cpp` | `update_ccp_therm_status_tx()` — per-CCP status computation; `update_imh_interrupt_req()` — DNS_EVENT_DELIVERY handler |
| PCode src | `source/pcode/flows/thermals/thermal_report.h` | `set_threshold_bits()`, `set_therm_monitor_bits()`, `set_prochot_bit()` |
| Related KB | [ACP Thermal](acp.md) | EMTTM, eff_tj_max, DTS telemetry |
| Related KB | [CBB Thermal Mgmt](cbb_thermal_management.md) | Full MSR field definitions |
| Related KB | [Prochot](prochot.md) | PROCHOT interrupt details |
| HSD | 22015379184 | LOCK_THERM_INT and THERM_EVENT_FFM deprioritization |
| HSD | 22013373025 | GNR C6 cross-product with thermal interrupts |
| HSD | 22013154844 | SPR C6 cross-product with thermal interrupts |

#### Validation Approach

- **HW_FEEDBACK_NOTIFICATION** (22022421588): Enable `IA32_PACKAGE_THERM_INTERRUPT[HW_FEEDBACK_NOTIFICATION_ENABLE]` → trigger HFI table update → verify `IA32_PACKAGE_THERM_STATUS[HW_FEEDBACK_NOTIFICATION_LOG]` set and LVT interrupt delivered to subscribed cores. Verify `DIRECTED_PKG_THERMAL_INTERRUPT_ENABLE` bit 25 behavior if supported.
- **HIGH_TEMP** (22022421595): Enable `IA32_THERM_INTERRUPT[HIGH_TEMP_INT_ENABLE]` → inject temperature above eff_tj_max via DTS TAP → verify `THERMAL_MONITOR_STATUS` transitions 0→1 → verify LVT interrupt fires on the specific core. Verify no interrupt when enable bit is 0.
- **IA32_PACKAGE_THERM_INTERRUPT** (22022421610): Program all enable bits in `MSR 0x1B2` (HIGH/LOW_TEMP, PROCHOT, OOS, THRESHOLD1/2, PMAX, HW_FEEDBACK) → trigger each event → verify corresponding interrupt delivered to ALL cores. Verify `DNS_EVENT_DELIVERY` HPM propagation to all leaf CBBs. Verify threshold relative temp fields program correctly.
- **IA32_THERM_INTERRUPT** (22022421614): Program all enable bits in `MSR 0x19B` → trigger each event → verify interrupt delivered to ONLY the subscribed core (not other cores). Verify each bit independently. Verify OOS_INT_EN bit 4 triggers on OOS transitions.
- **LOW_TEMP** (22022421618): Enable `LOW_TEMP_INT_ENABLE` → heat core above trip → let it cool below → verify `THERMAL_MONITOR_STATUS` transitions 1→0 → LVT interrupt fires. Verify symmetric with HIGH_TEMP.
- **OUT_OF_SPEC** (22022421620): Enable `OOS_INT_ENABLE` → inject temp > eff_tj_max + 10°C sustained > 3mS → verify `OOS_STATUS` transitions 0→1, `OOS_LOG` set, interrupt fires. Verify clears when temp drops. Verify both core (`0x19C`) and package (`0x1B1`) OOS status.
- **PROCHOT** (22022421627): Enable `PROCHOT_INT_ENABLE` → assert `xxPROCHOT_N` GPIO → verify `PROCHOT_STATUS` 0→1 transition triggers interrupt. Verify `PROCHOT_LOG` sticky until SW clears. De-assert → verify interrupt fires on 1→0 transition (if implemented per HAS; SDM only expects 0→1 of LOG).
- **THRESHOLD_1** (22022421629): Program `THRESHOLD1_REL_TEMP[14:8]` to a value N (°C below TjMax) → heat core to cross threshold → verify `THRESHOLD1_STATUS` toggles → interrupt fires on both 0→1 and 1→0 transitions.
- **THRESHOLD_2** (22022421633): Same as THRESHOLD_1 but for `THRESHOLD2_REL_TEMP[22:16]` and `THRESHOLD2_STATUS`. Verify independent of THRESHOLD_1.

---

### Related Sightings
<!-- No NWP thermal interrupt sightings identified yet — populate as they arise -->

---

### NWP Delta

> **Items to verify for NWP** (not yet confirmed — check NWP HAS when available):

| Area | Question | DMR/GNR Baseline |
|------|----------|-----------------|
| Multi-die HPM | Same `DNS_EVENT_DELIVERY` / `UPS_EVENT_DELIVERY` flow? NWP NIO topology? | DMR: Root→Leaf HPM, ~100s μS propagation delay |
| Core CR write path | Same direct GPSB write to `U2C_DIRECT_EVENTS`? | GNR+: PCode writes directly (no uBox intermediary) |
| DOMA/T2C | NWP core type — PNC (SKT-style DOMA) or different? | DMR: BigCore CCP-scoped, SKT has per-core CCP instances |
| CCP autonomous interrupts | If NWP uses DOMA cores, CCP generates interrupts autonomously | DMR BigCore: PCode generates; SKT: CCP generates |
| `LOCK_THERM_INT` | Deprecated? Still functional? | GNR: Not customer-documented, expected deprecation |
| `THERM_EVENT_FFM` | Deprecated? SMI flow still supported? | GNR: Not customer-documented, expected deprecation |
| `DIRECTED_PKG_THERMAL_INTERRUPT_ENABLE` | Supported in NWP? (bit 25 of THERM_INTERRUPT + bit 25 of PKG_THERM_STATUS) | GNR: Not POR, CPUID.06h.EAX[24]=0 |
| `PACKAGE_THERM_INTERRUPT_MASK` | Minimizing pkg interrupts — supported? | GNR: Not POR, defined but not implemented |
| C6 cross-product | Same "pend, don't skip" behavior? | GNR+: Pend interrupt until core exits C6 (changed from SPR legacy "skip") |
| SST-PP cross-product | Same: don't interrupt offlined cores during SST-PP switch? | GNR: PCode avoids interrupting cores being offlined |
| OOS threshold for interrupt | Same eff_tj_max + 10°C, 3mS timer? | DMR PCode: `OOS::temperature_offset=10°C`, `thermal_timer_threshold=3mS` |
| HW_FEEDBACK_NOTIFICATION | HFI table update frequency — same interrupt rate? | GNR: Scales with core count, known perf concern |
