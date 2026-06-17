# Power/RAPL > SVID (Serial Voltage ID)

> **Status**: Restructured — NWP delta enriched from MCP HAS/MAS query
> **Parent**: [Power / RAPL](power_rapl_main.md)

## Baseline (DMR)

SVID (Serial Voltage ID) is a 3-wire serial synchronous bus (VCLK, VDIO, ALERT#) connecting one master (PCU/Punit) and up to 15 slave VR controllers on each bus. It allows the CPU to send voltage commands (SetVID), power state commands (SetPS), and query VR parameters (GetReg). The protocol is defined in the SVID specification, with VRCI (VR Controller Interface) as the standard register interface abstraction.

## HW Touchpoints

<!-- TODO: Extract from Legacy content or enrich via MCP HAS query -->
| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| | | | | |

## FW Touchpoints

<!-- TODO: Extract from Legacy content or enrich via MCP HAS query -->
| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| | | | | |

## OS Interfaces

<!-- TODO: Extract from Legacy content or enrich via MCP HAS query -->
| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| | | | | |

## NWP Delta

**SVID (Serial Voltage Identification) is supported on NWP** with topology changes.

### Architecture Changes
- NWP has **single NIO die** managing SVID (vs dual IMH on DMR)
- SVID flows managed by NIO Punit
- **Safe WP change request is NOT POR** on NWP
- SVID rail topology updated for NWP NIO die + 2 CBBs

### Validation Impact
- Verify SVID communication through NIO single-die topology
- Skip Safe WP change request tests (not POR)
- Verify SVID rail assignments for NWP-specific VR topology

## Legacy (Human-Curated Reference)

---

### Architecture Summary

SVID (Serial Voltage ID) is a 3-wire serial synchronous bus (VCLK, VDIO, ALERT#) connecting one master (PCU/Punit) and up to 15 slave VR controllers on each bus. It allows the CPU to send voltage commands (SetVID), power state commands (SetPS), and query VR parameters (GetReg). The protocol is defined in the SVID specification, with VRCI (VR Controller Interface) as the standard register interface abstraction.

#### Key Architectural Facts
- **Bus topology**: 1 master (PCU), up to 15 slaves per bus, 4-bit addressing
- **CCI PM SVID**: Drives **2 external SVID buses**, supports max **16 logical VRs**
  - Max 12 VRs can perform telemetry pushes (VR IDs 0–11)
  - Max 8 VRs can be controlled by the dispatcher (VR IDs 0–7)
- **Power domain**: `vinf_aon`
- **Reset**: Most logic on `vinfaon_pwrgood_rst_b`; PMSB request-generating logic on `punit_prim_rst_b`
- **VRCI abstraction**: SVID uses the PMSB endpoint to communicate with PCU; VRCI defines a standard register set per VR. This allows MBVR/FIVR/LDO to be interchangeable with no Pcode changes
- **PkgC integration**: SVID controller is **dispatcher-controlled** (not RC-controlled) for PkgC flows. AllCall broadcast via `SVID_ALLCALL_CNTRL` sets retention voltage on entry and restores active voltage on exit

#### Register Spaces
Three register spaces are addressed via IOSF-SB:
1. **VRCI registers** (Addr[14]=1): Standard VR registers per VRCI spec — status, capability, workpoint, telemetry accumulators
2. **Telemetry CRs** (Addr[14]=0): Telemetry configuration — push enable, masking, stagger, mapping
3. **SVID CRs** (Addr[14]=0): Controller configuration — addressing, error config, command interface

---

### Execution Flow

#### Initialization (Reset Phase)
1. **Pcode enumerates VRs** — reads CAPABILITY register per VR to discover present VRs
2. **Pcode programs SVID_ADDR_CONFIG[0:15]** — maps logical VR IDs to physical SVID bus addresses
   - Sets Valid bit, VR_ADDR[3:0], SVID_Bus_ID[1:0]
   - Sets VID_Code_Step (5mV vs 10mV), HP_Telemetry, I_IN_polling bits
3. **Pcode programs SVID_POLL_PRIORITY_CONFIG** — sets status polling priority order
4. **Pcode initializes telemetry** — programs SVID_IMON_MASK, SVID_PWRIN_MASK, SVID_TELE_CFG, SVID_TELEMETRY_MAP_CFG
5. **Pcode initializes WP1/WP2 VRCI registers** — writes active and retention workpoints for AllCall usage
6. **Primecode programs dispatcher** — writes `IO_WP_SVID_ALL_CALL_RV_PS` for PkgC AllCall

#### Runtime Command Flow
1. **Pcode writes SVID_COMMAND register** — sets ADDRESS, COMMAND, PAYLOAD, then RUN_BUSY=1
2. **SVID HW transmits on bus** — arbiter selects request, transmitter sends frame
3. **VR responds with ACK/NAK** — response payload captured in SVID_DATAIN
4. **RUN_BUSY clears** — Pcode polls until clear, reads response

#### PkgC Flow (AllCall)
1. **Entry**: Dispatcher writes SVID_ALLCALL_CNTRL with SetWP (WP2=retention voltage, decay ramp)
2. **VR ramps to retention voltage** — ALERT# asserts until settled
3. **Exit**: Dispatcher writes SVID_ALLCALL_CNTRL with SetWP (WP1=active voltage, fast ramp)
4. **VR ramps to active voltage** — ALERT# asserts until settled

#### Telemetry Flow (HW-Offloaded)
1. **IMON polling**: HW periodically reads I_OUT_TELEMETRY from each enabled VR (controlled by SVID_IFC_CONFIG.IOUT_TSC_SEL)
2. **Accumulation**: Results accumulated in I_OUT_ACCUMULATOR / P_IN_ENERGY_ACCUMULATOR (VRCI registers)
3. **Push**: SVID pushes accumulated values to Punit via TELE_ULONG PMSB messages (2 TeleIDs per message)
4. **Pcode reads telemetry** — handles accumulator rollover, uses for RAPL power calculations

#### Arbitration Priority
1. PkgC/Dispatcher request (highest)
2. Pcode command (via SVID_COMMAND)
3. AllCall (via SVID_ALLCALL_CNTRL)
4. Alert/status polling
5. IMON polling (lowest — can be starved)

#### Arbiter FSM States
| State | Trigger | Description |
|-------|---------|-------------|
| SVID_ARB_IDLE | — | Waiting for any request |
| SVID_ARB_TURN_ON | Request arrival | Set turn-on counter, wait |
| SVID_ARB_READY | Counter done | Set ready counter, wait |
| SVID_ARB_SELECT | Ready | Select frame for transmission |
| SVID_ARB_PKG | PkgC request | PkgC/Dispatcher transaction |
| SVID_ARB_PCODE | Pcode request | Pcode command transaction |
| SVID_ARB_DISPATCHER | Dispatcher request | Dispatcher SetWP via VRCI |
| SVID_ARB_ALERT | Alert pin | Alert/status poll transaction |
| SVID_ARB_IMON | IMON tick | IMON polling transaction |
| SVID_ARB_TURN_OFF | Xmt_done | Idle wait after transmission |
| SVID_ARB_ERROR | Max retry error | Assert error bit, signal PM_EVENT |
| SVID_ARB_IDLE_WAIT | Counter set | Wait before returning to idle |
| SVID_ARB_IDLE_ON | io_svid_config2.svid_idle_en | Wait on counter with idle enabled |

#### SVID_CONFIG2 — PkgC Behavior Masks
| Field | Bits | Default | Description |
|-------|------|---------|-------------|
| PKGC_IMON_ON_MASK | 15:12 | 4'b1000 | Per-state mask for telemetry pull disable: [PkgC entry, in-PkgC, PkgC exit, reserved]. Default disables pulls during PkgC exit |
| PKGC_CLK_OFF_MASK | 11:8 | 4'b1010 | Per-state mask for SVID bus clock turn-off disable. Default prevents clock off during PkgC entry and exit |

---

### SVID Commands

| Opcode | Command | Required | Description |
|--------|---------|----------|-------------|
| 01h | SetVID-fast | VR12 | Set VID with maximum slope — quick PkgC6 exit |
| 02h | SetVID-slow | VR12 | Set VID with slow slope — normal GV transition |
| 03h | SetVID-decay | VR12 | Output voltage decays with load — PkgC6 entry |
| 04h | SetPS | VR12 | Configure VR power state for efficiency |
| 05h | SetRegADR | VR12 | Set address pointer in VR data register table |
| 06h | SetRegDAT | VR12 | Write data to register at current address pointer |
| 07h | GetReg | VR12 | Read register contents from VR |

---

### VR Addressing

SVID uses logical addressing (0–15) mapped to physical bus addresses via SVID_ADDR_CONFIG registers.

#### EGS VR Map (Reference)
| Logical ID | VR | Physical Addr |
|------------|-----|---------------|
| 00h | VCCIN | 00h |
| 01h | VCCINFAON | 01h |
| 02h | VCCFA_EHV | 02h |
| 03h | VCCFA_EHV_FIVR | 03h |
| 04h–0Fh | Platform-specific | Config-dependent |

---

### Key Registers & Interfaces

#### VRCI Registers (per VR — Addr[14]=1)
| Addr | Register | Supported | Description |
|------|----------|-----------|-------------|
| 0x0 | STATUS | Y | VR status (settled, alerts) |
| 0x1 | CAPABILITY | Y | VR capabilities |
| 0x2 | GP_ALERT_CONFIG | Y | General purpose alert configuration |
| 0x3 | EVENT_CONFIG | Y | Event configuration |
| 0x4 | RAMP_RATE_CONFIG | Y | Voltage ramp rate configuration |
| 0x7 | VR_MAX | Y | Maximum VR parameters |
| 0x8 | WORKPOINT | Y | Active workpoint (target voltage) |
| 0x14 | I_OUT_TELEMETRY | Y | Output current telemetry (low byte) |
| 0x15 | I_OUT_TELEMETRY_HI | Y | Output current telemetry (high byte) |
| 0x18 | I_SAMPLE_TELEMETRY | Y | Current sample telemetry |
| 0x1B | P_IN_ENERGY | Y | Input energy telemetry (low) |
| 0x1C | P_IN_ENERGY_HI | Y | Input energy telemetry (high) |
| 0x24 | I_OUT_ACCUMULATOR | Y | Output current accumulator |
| 0x25 | I_OUT_NUM_SAMPLES_SNAPSHOT | Y | I_OUT sample count (snapshot) |
| 0x2B | P_IN_ENERGY_ACCUMULATOR | Y | Input energy accumulator |
| 0x2C | P_IN_ENERGY_NUM_SAMPLES_SNAPSHOT | Y | P_IN sample count (snapshot) |
| 0x33 | I_OUT_NUM_SAMPLES_RAW | Y | I_OUT sample count (raw) |
| 0x36 | P_IN_ENERGY_NUM_SAMPLES_RAW | Y | P_IN sample count (raw) |

#### SVID Controller CRs (Addr[14]=0)
| Register | Scope | Description |
|----------|-------|-------------|
| SVID_ADDR_CONFIG (×16) | Per VR | Logical-to-physical mapping, valid, VR type, HP telem, I_IN |
| SVID_POLL_PRIORITY_CONFIG (×2) | Per Bus | Status poll priority order for VRs |
| SVID_CONFIG0 | Global | Turn-on/off counters, error retry threshold |
| SVID_CONFIG1 | Global | PS_CHANGED_DELAY, VC_SETTLED_DELAY, AUTO_ACK |
| SVID_IFC_CONFIG | Per Bus | IMON polling rate (IOUT_TSC_SEL), bus frequency, PWRIN address |
| SVID_VR_ERROR_STATUS | Global | Per-VR max-retry error mask |
| SVID_IFC_ERROR_STATUS | Global | Per-interface error counters and types |
| SVID_MISC_STATUS | Global | HW polling idle status per interface |
| SVID_ERROR_CONFIG | Global | GP_ALERT/PD_HARD_ERR enable per error type |
| SVID_COMMAND | Global | Pcode→HW command interface (RUN_BUSY, CMD, ADDR, PAYLOAD) |
| SVID_DATAIN | Global | VR read response data |
| SVID_ALLCALL_CNTRL | Global | VR13 AllCall broadcast (SetWP for PkgC) |

#### Telemetry Configuration CRs
| Register | Description |
|----------|-------------|
| SVID_TELE_CTRL | Telemetry push enable/disable |
| SVID_TELE_CFG | Push delay, sample mode |
| SVID_TELE_COARSE_UNIT_CFG | Timer unit width for coarse delay |
| SVID_TELE_VR_MASK_CFG | Per-VR telemetry mask (VR 0–11) |
| SVID_TELE_ID_MASK_CFG | Per-TeleID mask (I_OUT, P_IN, accumulators) |
| SVID_IMON_MASK | VR mask for IMON polling + telemetry |
| SVID_PWRIN_MASK | VR mask for PWRIN polling + telemetry |
| SVID_TELEMETRY_STAGGER_CFG | Stagger counter for push alignment |
| SVID_TELEMETRY_GAT_CFG | Global alignment timer trigger value |
| SVID_TELEMETRY_MAP_CFG | Physical-to-logical TeleID mapping (6→4) |

---

### Interface Touch Points

SVID is a **PMSB-only** interface — no MSR, TPMI, CSR, or mailbox exposure. All Pcode-to-VR communication flows through the PMSB endpoint.

| Register/Parameter | MSR | IN_TPMI | OOB_TPMI | CSR | Fuses | MB |
|--------------------|-----|---------|----------|-----|-------|----|
| SVID_COMMAND | — | — | — | — | — | PMSB |
| SVID_ADDR_CONFIG | — | — | — | — | VR mapping | PMSB |
| VRCI (per VR) | — | — | — | — | — | PMSB |
| Telemetry CRs | — | — | — | — | — | PMSB |
| AllCall (PkgC) | — | — | — | — | — | PMSB/Dispatcher |
| VR Type/Config | — | — | — | — | ConfigROM | — |

---

### VR14 Enhancements

#### High Current Support
VR14 VRs support current above 255A via a scaling register (50h). **Effective ICCMax** = ICCMax × 2^IMON_ScalingFactor. Pcode reads:
1. Register 21h (ICCMax)
2. Register 50h (scaling factor)
3. Calculates effective ICCMax

#### High Precision Telemetry
VR14 provides 16-bit telemetry (upper byte = integer, lower byte = fractional). Registers 71h (IOUT) and 72h (PWR_IN) give higher resolution than 8-bit. **SVID_ADDR_CONFIG[25]** must be set by Pcode for VR14 VRs with HP telemetry capability.

#### I_IN Telemetry for Psys
**SVID_ADDR_CONFIG[26]** enables polling I_IN instead of I_OUT for Psys devices. Pcode reads ICC_IN_MAX and Input Voltage instead of ICC_MAX.

---

### DC Loadline Reading from VR (VR14)

Pcode reads DC loadline from the VCCIN MBVR over SVID (Wave3+). VR14 makes DC_LL registers mandatory.

**Equation**: $DC\_LL = (\text{Register 23h}) \times 0.1 \text{ m}\Omega + (\text{Register 36h}) \times 0.001 \text{ m}\Omega$

#### Pcode Flow
1. Read register 23h (DC_LL coarse) and 36h (DC_LL_FINE) from VCCIN VR via SVID GetReg
2. Compute DC_LL per equation above
3. Make available to BIOS via `VR_HANDLER.GET_DC_LL` B2P mailbox
4. BIOS can override via `VR_HANDLER.SET_DC_LL` B2P mailbox (format U12.12.0 for 0.001 mΩ resolution)
5. Value retained until next cold boot (persistent variable in Pcode)

#### Error Handling
- **LL read failure from VR** → fatal MCA
- **LL from VR > FUSED_LL** → fatal MCA
- **BIOS SET_DC_LL > FUSED_LL** → Pcode returns error, ignores BIOS value, uses VR value
- OCMB can disable SVID (sticky across warm reset) to avoid protocol errors during BCLK OC — DC_LL must be persistent

#### Usage
- **RAPL**: DC_LL used in platform power estimation (V_droop = I × LL)
- **EDP/IccMax**: DC_LL used to compute Pmax thresholds and VR droop budgets
- **Pmax detector**: BIOS uses DC_LL to compute Vtrip point for Pmax detector ADC
- **FIVR energy reporting**: $V_2 = V_1 - I_1 \times R$ where R = DC_LL
- **VCCDDRHV LL**: DMR extends DC_LL reading to VCCDDRHV VRs (I-TDC increased from 32A to 65A)

---

### SVID Telemetry for MBVR Energy Reporting

#### MBVR Rails with SVID IMON Telemetry (per iMH)
| Rail | Die | Description |
|------|-----|-------------|
| VCCANA | iMH | Analog supply |
| VCCDDR_HV | iMH | DDR high-voltage (requires DC_LL on DMR) |
| VCCINF | iMH | Infrastructure supply |
| VCCIN_EHV | iMH | Extra-high voltage input (requires DC_LL) |
| VCCFA_EHV | iMH | FIVR analog extra-high voltage |

Pcode reads IMON for each MBVR every ~1 ms via SVID bus. Energy is computed as:
- **MBVR with DC_LL**: $P_{in} = I_1 \times (V_1 - I_1 \times R)$
- **MBVR without DC_LL**: $P_{in} = I_1 \times V_1$

Accumulated energy stored in Punit telemetry SRAM (7 registers × 64-bit per iMH die). Exposed to SW via PMT/OOB-MSM.

#### Punit Controller — IO_TELE_SVID_CONFIG (0xfd518)
| Bits | Field | Reset | Description |
|------|-------|-------|-------------|
| 31:20 | IO_TELE_FIRST_OFFSET | 0x5d0 | Telemetry array offset for first SVID VR |
| 19:18 | TELEBITS | 0x2 | Bits needed to address TeleIDs: 2'b10 = 4 TeleIDs per VR |
| 9:8 | EXT_LOGPORTID | 0x3 | Extended logical port ID of first SVID in SoC |
| 7:0 | FIRST_LOGPORTID | 0xff | Logical port ID of first SVID in SoC |

SVID telemetry is organized as 12 group IDs (VRs), with up to 4 TeleIDs per VR, using TELE_ULONG message format. Pcode configures this register during telemetry initialization (Phase 4/5).

#### FIVR Energy — SVID as Input Voltage Source
For FIVR domains (VCCCORE, VCCR, VCCFIXDIG, etc.), SVID provides the input voltage $V_2$ used in FIVR energy equations:
- $V_2 = V_1 - I_1 \times R$ (where $V_1$ = VR voltage, $I_1$ = VR IMON current, $R$ = DC_LL)
- iMH Punit computes $V_2$ every ~1 ms and sends to CBBs via HPM message `HPM_MSG_RAPL_PERF_LIMIT.FIVR_INPUT_VOLTAGE`
- Per-FIVR power: $P_{in} = I_{in\_FIVR} \times V_2$
- Feature controlled by fuse `DOMAIN_ENERGY_REPORTING_ENABLE` (disabled at PRQ)

---

### Alert & Error Handling

#### VR Status1 Register Bits
| Bit | Field | Description |
|-----|-------|-------------|
| 0 | VR_Settled | VR at target voltage |
| 1 | ThermAlert | Over-temperature |
| 2 | IccMaxAlert | Over-current (latched) |
| 3 | VID_DAC_high | Over-voltage (>30mV above target) |
| 7 | ReadStatus2 | Protocol error indication |

#### PM_EVENT Types to Punit
| Error Type | GP_ALERT | PD_HARD_ERR | Description |
|-----------|----------|-------------|-------------|
| 3-Strike | No | Yes | Max retry exceeded on bus |
| Over Voltage | Yes | No | VID_DAC_high alert |
| Over Current | Yes | No | IccMaxAlert |
| Thermal | Yes | No | ThermAlert |
| Protocol Error | Yes | No | ReadStatus2 asserted |

#### SVID Error Reporting Architecture (Gen-to-Gen Evolution)

| Generation | Error Path | Details |
|------------|-----------|---------|
| **Pre-GNR (SPR)** | PM_EVENT → Pcode → MCA bank | SVID errors reported via PM_EVENT message to Pcode; Pcode logs to MCA bank with FW MSCOD |
| **GNR+** | Reported Error CR + IERR wire → Punit HW | SVID writes 64-bit Reported Error Register via PMSB; asserts UC IERR wire for sideband-independent signaling. **IP Type = 0x2 (SVID)** in Reported Error Register |
| **DMR** | Same as GNR + RAS IP owns GPIO | SVID error flows unchanged; RAS IP (not Punit) now owns CATERR/RMCA GPIO pins and MCA bank merging |

##### Reported Error Register Format (SVID → Punit)
| Bits | Field | Description |
|------|-------|-------------|
| 2:0 | IP Type | **0x2 = SVID** (hardcoded) |
| 6:3 | IP Specific Error Code | Per SVID error definition (3-strike, single err, VR_HOT, etc.) |
| 22:7 | Unique Port ID | 16-bit PMSB port ID for sender validation |
| 54:23 | MCA Misc IP Error Log | SVID-specific debug info (VR number, error type, bus) |
| 57:55 | Error Severity | 011=UC (PCC), 010=UCNA, others reserved |
| 58 | Overflow | Set if SVID detected error but could not send to Punit |

##### MC_MISC Layout for SVID Errors
| MC_MISC Bits | Source | Description |
|--------------|--------|-------------|
| 11:9 | IP Type | 0x2 = SVID |
| 15:12 | IP Error Code | SVID error type |
| 31:16 | Unique Port ID | SVID PMSB port ID |
| 63:32 | IP Error Log | SVID-specific info (VR#, bus#, request type) |

##### SVID Error Aggregation Registers (in SVID IP, Gen4+)
| Register | Instances | Description |
|----------|-----------|-------------|
| SVID_AGG_ERR_CONFIG_3STRIKE_ERR | N | Enable signaling for 3-strike bus errors |
| SVID_AGG_ERR_CONFIG_SINGLE_ERR | N | Enable signaling for single bus errors |
| SVID_AGG_ERR_CONFIG_VR_HOT | N | Enable signaling for VR over-temperature alerts |
| SVID_AGG_ERR_CONFIG_VR_ICC_MAX | N | Enable signaling for VR over-current alerts |
| SVID_AGG_ERR_CONFIG_VR_STATUS2 | N | Enable signaling for VR protocol errors |
| SVID_AGG_ERR_CONFIG_VR_VID_DAC_HIGH | N | Enable signaling for VR over-voltage alerts |
| SVID_AGG_ERR_FW_CONFIG | 1 | Controls logging/signaling of FW-initiated transaction errors |
| SVID_AGG_ERR_STATUS_3STRIKE_ERR_IFC | 2 | AllCall 3-strike error status (per bus) |
| SVID_AGG_ERR_STATUS_3STRIKE_ERR_VR | 2 | Per-VR 3-strike error status |
| SVID_AGG_ERR_STATUS_SINGLE_ERR_IFC | 2 | AllCall single error status (per bus) |
| SVID_AGG_ERR_STATUS_SINGLE_ERR_VR | 2 | Per-VR single error status |
| SVID_AGG_ERR_STATUS_VR_HOT | 4 | VR over-temperature alert status |
| SVID_AGG_ERR_STATUS_VR_ICC_MAX | 4 | VR over-current alert status |
| SVID_AGG_ERR_STATUS_VR_STATUS2 | 4 | VR protocol error status |

Each AGG_ERR_STATUS register logs **latest** and **earliest** error info (VR number, request type, valid/overflow/signaled bits). The earliest error is preserved until explicitly cleared.

##### Pcode Error Loop — SVID Quiesce on Fatal MCA
On fatal MCA or IERR, Pcode/Primecode must quiesce SVID access:
- Disable IMON/PWR_IN telemetry polling
- Disable ITD on MBVRs
- Halt SVID command issuance
- Enter error loop (halt slowloop/fastpath, only handle PECI)

##### IO_FASTPATH_GLOBAL.SVID_REQ (bit 21)
Set when SVID has a request — covers SVID Cmd Sent, VR Settled, and SVID Error events. Pcode polls this as part of fastpath processing.

---

### SVID as Standalone IP (Gen4 / IPPUNIT-177)

Starting Gen4 (DMR+), SVID is separated from the Punit into an independent IP:
- **SVID gets its own PMSB sideband endpoint** (previously shared via `pmsrvr_sep`)
- **SVID gets its own DVP** for debug visibility (was shared with Punit)
- All SVID CRs, VRCI registers, telemetry registers, and error aggregation registers move to the SVID IP
- Punit exposes **parameters** for SVID CR addresses so Punit can still write AllCall/VRCI:

| Parameter | Default | Description |
|-----------|---------|-------------|
| SVID_ALLCALL_CNTRL_CR_ADDR | 524 | Address Punit writes for AllCall |
| SVID_DISP_PKGC_STATUS_CR_ADDR | 528 | Address for PkgC status to SVID |
| VRCI_STATUS_CR_ADDR_0 | 16384 | VRCI STATUS base address |
| VRCI_VR_WP_CR_ADDR_0 | 16416 | VRCI WORKPOINT base address |

#### Impact on NWP
- SVID and Punit are independently instantiable — SVID can be on a different die than Punit
- SVID GPIO pins (ALERT, CLK, DATA) connect only to HPM root die (package master)
- `idle_pm` uses `IO_IDLE_PM_CONTROL.IS_ROOT` to detect MBVR initiator (replaces bump enable logic)
- Settled indication changed from PM_EVENT simple message to CR write (IPPUNIT-184) — standard fabric compliant
- SB ordering relaxation (IPPUNIT-167): non-posted messages can pass prior posted messages; only affects Punit→SVID

---

### GPIO Bump Enable Fuses for SVID

In multi-die HPM topologies, SVID GPIO pins are enabled only on the die that is the package master. The `GPIO_BUMP_ENABLES` register (0x1048, package scope) is populated from fuses between config_req and config_done.

| Bit | Field | Default | Description |
|-----|-------|---------|-------------|
| 5 | enable_SVID0 | 0x0 (disabled) | Enables SVID bus 0 GPIO bumps (xxSVIDALERT0, xxSVIDCLK0, xxSVIDDATA0) |
| 6 | enable_SVID1 | 0x0 (disabled) | Enables SVID bus 1 GPIO bumps (xxSVIDALERT1, xxSVIDCLK1, xxSVIDDATA1) |

#### Behavior
- **Disabled (default)**: SVID bump inputs use safe values (tx_en deasserted, rx_en deasserted). SVID controller does not drive the bus.
- **Enabled**: After config_done, SVID bump fences are removed and normal SVID bus operation begins (earliest functional: **Phase 4**)
- Fuses are per-die, configured by SoC integration team based on HPM topology. Non-root dies have SVID0/1 disabled.

---

### Die-to-Die SVID Signal Coordination

#### GPIO Signals (Package Master / Root Die Only)
| Signal | Type | Description |
|--------|------|-------------|
| xxSVIDALERT0_N | Input | SVID bus 0 alert (VR status change indication) |
| xxSVIDALERT1_N | Input | SVID bus 1 alert |
| xxSVIDCLK0 | Output | SVID bus 0 clock |
| xxSVIDCLK1 | Output | SVID bus 1 clock |
| xxSVIDDATA0 | In/Out | SVID bus 0 data |
| xxSVIDDATA1 | In/Out | SVID bus 1 data |

#### MBVR Q-Channel Signals (Die-to-Die via EMIB/MDFC)
For PkgC SVID ramp coordination across dies:

| Signal | Type | Description |
|--------|------|-------------|
| MBVR_Qactive_in/out | In/Out | MBVR ramp active indication |
| MBVR_Qreq_n_in/out | In/Out | MBVR ramp request (active low) |
| MBVR_Qaccept_n_in/out | In/Out | MBVR ramp accept (active low) |
| MBVR_Qdeny_in/out | In/Out | MBVR ramp deny |

These Q-channel signals coordinate VR voltage transitions during PkgC entry/exit across root and leaf Punit dies.

---

### Source References

#### Primecode (IMH-level firmware)
| # | File | Description |
|---|------|-------------|
| 1 | `src/ip/svid/v1_0/svid.hpp` | Base SVID IP class definition |
| 2 | `src/ip/svid/v1_0/svid_gen3.cpp` | Gen3 SVID driver implementation |
| 3 | `src/ip/svid/v1_0/svid_gen3.hpp` | Gen3 SVID driver header |
| 4 | `src/ip/svid/v1_0/svid_gen3_evt_handler.cpp` | SVID event handler (alerts, PM_EVENT) |
| 5 | `src/ip/svid/v1_0/svid_gen3_evt_handler.hpp` | Event handler header |
| 6 | `src/ip/svid/v1_0/svid_mailbox_cmds.cpp` | SVID mailbox command interface |
| 7 | `src/ip/svid/v1_0/svid_mailbox_cmds.hpp` | Mailbox commands header |
| 8 | `src/ip/svid/v2_0/svid.cpp` | V2.0 SVID driver (NWP/DMR) |
| 9 | `src/ip/svid/v2_0/svid.hpp` | V2.0 SVID header |
| 10 | `src/ip/svid/v2_0/svid_pmeter.cpp` | SVID power metering (IMON/PMON integration) |
| 11 | `src/ip/svid/v2_0/svid_pmeter.hpp` | Power meter header |
| 12 | `src/ip/svid/v2_0/svid_mailbox_cmds.cpp` | V2.0 mailbox commands |
| 13 | `src/ip/svid/v1_1/svid_gen3_oc.cpp` | Overclocking SVID variant |
| 14 | `src/ip/core/corecommon/v1_0/base_ia_svid.cpp` | Core IA SVID integration |
| 15 | `src/cfgdata/nwp_imh/v1_0/ip_headers/svid_MsgCr.hpp` | NWP SVID message/CR definitions |

#### Pcode (CBB die-level firmware)
| # | File | Description |
|---|------|-------------|
| 1 | `source/pcode/drivers/svid/` | SVID driver directory |
| 2 | `source/pcode/flows/workpoint_calc/workpoint_calc.h` | Workpoint calculation — SVID VID code, ramp type |

---

### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| SVID HAS | [10nm SVID HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SVID/10nm%20SVID%20HAS.html) | Primary spec — CCI PM SVID, VRCI, telemetry, commands |
| PM RAS/MCA HAS | [DMR PM MCA/RAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/RAS/PM_RAS_MCA.html) | SVID error reporting architecture, Reported Error Register, MC_MISC format, error severity, blast radius |
| SVID Standalone IP | [IPPUNIT-177 Feature HAS](https://docs.intel.com/documents/sysip_pm/HAS_gen4/IPPUNIT-177_Feature_HAS.html) | Gen4 SVID separation from Punit — own PMSB EP, DVP, full CR list, error aggregation registers |
| SVID Standalone Jira | [IPPUNIT-177](https://jira.devtools.intel.com/browse/IPPUNIT-177) | Tracking Jira for standalone SVID IP feature |
| Punit Gen4 Features | [Punit IP Gen4 Features](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/Punit/Punit_IP_Gen4_Features.html) | Gen4 feature list — IPPUNIT-177 (standalone SVID), IPPUNIT-184 (settled CRWr), IPPUNIT-167 (SB ordering) |
| UCNA Error Handling | [UCNA Error Handling HAS](https://docs.intel.com/documents/pm_doc/src/server/SPR-SP/UCNA%20Error%20Handling/UCNA%20Error%20Handling.html) | UCNA support for bad devices — impacts SVID/FIVR error logging (IO_FIRMWARE_MCA_MISC race condition fix) |
| Interdie GPIO/MDFC | [DMR PM Interdie Signals](https://docs.intel.com/documents/pm_doc/src/server/archived_deprecated/DMR/PM%20Components/wave4_gpio_interdie.html) | SVID GPIO on root die only; MBVR Q-channel EMIB signals for PkgC coordination |
| SVID Error MAS | [SVID Error Reporting MAS](https://docs.intel.com/documents/sysip_pm/MAS_wave4/Feature_MAS/Punit_SVID_Error_Reporting_Feature_MAS/Punit_SVID_Error_Reporting_Feature_MAS.html) | SVID error MAS — detailed error types and signaling (referenced in PM RAS HAS) |
| SOC Construction | [DMR SOC Construction HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/SOC_PM_HAS/DMR_SOC_Construction_HAS.html) | SVID = dispatcher-controlled IP in PkgC; PM Strap includes SVID |
| PkgC HAS | [DMR PkgC HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Idle_Flow/DMR_PkgC.html) | PkgC entry/exit VR voltage flows via AllCall |
| PEM KB | [pem.md](pem.md) | PEM uses SVID telemetry (IMON/PMON) for energy reporting |
| Socket RAPL KB | [socket_rapl.md](socket_rapl.md) | RAPL uses SVID power telemetry for package power calculation |
| GPIO Bump Enables | [Punit GPIO Enables](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/Punit%20GPIO%20enables/punit_gpio_enables.html) | SVID bump enable fuses (enable_SVID0 bit 5, enable_SVID1 bit 6), GPIO_BUMP_ENABLES register 0x1048 |
| FIVR Energy Report | [DMR FIVR Energy Report](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Fine%20grained%20energy%20reporting/DMR_fivrenergy_report.html) | MBVR IMON via SVID for energy reporting, FIVR I_IN telemetry equations, V2 = V1 - I1×R |
| IccMax/Pmax HAS | [IccMax Pmax Management](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Power%20Delivery/IccMax%20Pmax%20Management%20HAS.html) | DC loadline read from VCCIN VR via SVID (reg 23h+36h), Pmax detector LL, EDP budgeting |
| Telemetry HAS | [10nm Server Telemetry](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Telemetry/10nm%20Server%20Telemetry%20HAS.html) | IO_TELE_SVID_CONFIG (0xfd518), SVID TELE_ULONG format, 12 GroupIDs × 4 TeleIDs |
| SVID HAS (Reference) | [10nm SVID HAS #reference](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SVID/10nm%20SVID%20HAS.html#reference) | Arbiter FSM, VR14 HP telemetry flow, SVID_CONFIG2 PkgC masks, IMON polling block diagram |

---

---

### Related Sightings
<!-- No NWP SVID sightings cataloged yet -->

---

### NWP Delta

NWP inherits DMR SVID architecture (Wave3 CCI PM SVID with VRCI). Key NWP-specific areas to validate:
- **VR map**: NWP platform-specific VR logical-to-physical address mapping (SVID_ADDR_CONFIG)
- **Rail configuration**: NWP may have different MBVR rail set than DMR-AP (verify VCCIN, VCCINFAON, VCCFA_EHV availability)
- **Primecode version**: NWP uses `src/ip/svid/v2_0/` — verify svid_pmeter and mailbox cmd support
- **Telemetry configuration**: Validate IMON/PWRIN mask, HP telemetry, TeleID mapping for NWP VR topology
- **PkgC AllCall**: Verify WP1/WP2 programming and dispatcher integration for NWP PkgC entry/exit

---

### Validation Starting Points

1. **Basic SVID comms**: Use PythonSV to read SVID_MISC_STATUS — verify HW_POLLING_IS_IDLE per interface
2. **VR enumeration**: Read SVID_ADDR_CONFIG[0:15] — verify valid VRs match platform VR map
3. **Command test**: Write SVID_COMMAND with GetReg(STATUS) to each valid VR — verify ACK and SVID_DATAIN
4. **IMON check**: Read I_OUT_ACCUMULATOR for enabled VRs — verify non-zero accumulation
5. **Error status**: Read SVID_VR_ERROR_STATUS and SVID_IFC_ERROR_STATUS — should be clean
6. **PkgC VR voltage**: Trigger PkgC6 entry/exit, verify VR voltage transitions via VRCI WORKPOINT read
