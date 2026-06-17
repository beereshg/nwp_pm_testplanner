# Platform PM Interface > PECI PM

> **Status**: Enriched
> **Parent**: [Platform PM Interface](platform_pm_interface_main.md)

## Architecture Summary

PECI (Platform Environment Control Interface) is the **out-of-band (OOB) management interface** between the BMC and the CPU package. For PM, the BMC uses PECI commands to read thermal data, power telemetry, and per-core MSRs without OS involvement. In DMR/NWP, PECI is delivered over **MCTP/I3C** (replacing the legacy PECI wire protocol).

### HW Path
```
BMC → I3C/MCTP → OOBMSM → PMSB → PUnit PECI Inbox → PCode PECI Mailbox Handler
```

OOBMSM receives the PECI-over-MCTP message, translates it, and writes to the PUnit's PECI inbox registers (`IO_PECI_INBOX_REQ_CMD`, `IO_PECI_INBOX_REQ_DATA_0..3`). A fastpath fires in PCode, which reads the inbox, dispatches the command, and writes the response to the PECI outbox for OOBMSM to return to the BMC.

### PECI PM Commands

| Command | Opcode | Description |
|---------|--------|-------------|
| **RdPkgConfig** | `0xA1` | Read Package Configuration Service (PCS). Generic read access to "Package Configuration Space" — thermal data, DIMM temps, power limits, telemetry. Index+Parameter fields select the PCS entry. |
| **WrPkgConfig** | `0xA5` | Write Package Configuration Service. Write access to PCS — e.g., set power limits, thermal thresholds. Dword data writes only. |
| **RdIAMSR** | `0xB1` | Read IA MSR. Reads an individual core's MSR via PECI. PCode forwards the request to μcode via the P2U (PCode-to-μcode) mailbox. 8-bit Thread ID (legacy). |
| **RdIAMSREx** | `0xD1` | Read IA MSR Extended. Same as RdIAMSR but supports **16-bit Thread ID** for high-core-count products (DMR 288+ threads). |
| **WrIAMSR_Ex** | `0xD5` | Write IA MSR Extended. Writes an MSR to a specific core via P2U mailbox. 16-bit Thread ID. |

### RdIAMSR / RdIAMSREx detail

This is the most validation-relevant PECI PM command. The flow:

1. BMC sends `RdIAMSR[Ex]` with `Thread_ID` + `MSR_Address`
2. PCode validates parameters, checks core is not in reset (`check_core_in_reset`)
3. **PkgC wake policy check** (`peci_cross_pkgc_checker`):
   - If core is in C6 and `WAKE_ON_PECI_INDICATOR` < `WAKE_FROM_COREC` → **BLOCK** (return `THREAD_UNAVAILABLE`)
   - If core in C6 and wake indicator ≥ `WAKE_FROM_COREC` → **READ** (wake core)
   - The wake indicator is a TPMI register written by the OS/customer
4. PCode sends P2U (PCode-to-μcode) request → μcode reads the MSR → returns data
5. PCode writes response to PECI outbox → OOBMSM returns to BMC

**Agent ID trust**: BMC provides an Agent ID. PCode checks if the agent is trusted (`is_agent_id_trusted`). Write MSR operations require either BMC_INIT=1 or a trusted agent ID.

### PM-relevant MSRs read via PECI

Tests exercise reading MSRs from cores while the BMC harasses the PECI interface. Common PM MSRs accessed:
- Thermal status MSRs (package/core temperature)
- Power limit MSRs (RAPL)
- HWP request/status MSRs
- Perf status MSRs

### Wake-on-PECI indicator values

| Value | Meaning |
|-------|---------|
| 0 (`NEVER_WAKE`) | Never wake package/core for PECI read — return THREAD_UNAVAILABLE |
| 1 (`WAKE_FROM_PKGC`) | Wake from PkgC6 but not CoreC6 |
| 2+ (`WAKE_FROM_COREC`) | Wake from both PkgC6 and CoreC6 |

## Execution Flow

1. **BMC** sends PECI command via I3C/MCTP to OOBMSM
2. **OOBMSM** translates MCTP to PMSB message → PUnit PECI inbox
3. **Fastpath** `IO_PECI_INBOX_REQ_CMD.RUN_BUSY` fires in PCode
4. **PeciMailbox::readMailboxRegisters()** reads inbox registers
5. **populateCommandStruct()** decodes opcode → remaps to handler index
6. **Handler dispatch** (RdPkgConfig → PCS handler, RdIAMSR → P2U path, etc.)
7. For MSR reads: P2U request → μcode reads MSR → P2U response → PCode
8. **sendResponse()** writes PECI outbox → OOBMSM → BMC
9. PkgC re-entry allowed after unblocking (`peci_block_unblock_cbbc(false)`)

## Key Registers & Interfaces

| Register | Role |
|----------|------|
| `IO_PECI_INBOX_REQ_CMD` | PECI request: opcode, write/read lengths, run-busy |
| `IO_PECI_INBOX_REQ_DATA_0..3` | PECI request data: host ID, index/parameter, thread ID, MSR addr |
| `IO_PECI_OUTBOX_*` | PECI response: completion code + data |
| `IO_ODC_PECI_WAKE_MODE` | Wake-on-PECI indicator (TPMI-writable by OS) |
| `ENABLE_RDIAMSR` (PCU info) | Fuse/config: "RdIAMSR() command is enabled" — default 1 |
| `IO_FASTPATH_MAILBOXES.PECI_REQ` | Fastpath bit for incoming PECI commands |

## Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [DMR Punit IP Gen4 Features HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/Punit/Punit_IP_Gen4_Features.html) | PECI standalone |
| HAS | [OOBMSM Punit Interactions](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/OOBMSM/H_SOC_OOBMSM_Punit_Interations.html) | OOBMSM↔Punit PECI path |
| Primecode src (common) | `src/flow/mailbox/peci/peci_common/v1_0/peci_mailbox.cpp` | `PeciMailbox` class — handler dispatch |
| Primecode src (compute) | `src/flow/mailbox/peci/peci_compute/v1_0/peci_mailbox_compute_handlers.cpp` | P2U request path for RdIAMSR |
| Primecode src (commands) | `src/flow/mailbox/peci/peci_common/v1_0/peci_mailbox.xml` | PECI command definitions (opcodes, fields) |
| PCode src (PECI handler) | `source/pcode/mailbox/peci_mbx.cpp` | CBB PCode: `read_ia_msr_cmd`, `read_ia_msr_ex_cmd`, `write_ia_msr_ex_cmd` |
| PCode src (PECI XML) | `source/mailbox/mboxgen_peci_server.xml` | CBB PECI mailbox services: IA_MSR, IA_MSR_EX, END_POINT_CONFIG |
| PCode src (MCTP layer) | `source/pcode/flows/mctp/mctp.cpp` | MCTP-to-PECI opcode translation |
| FAS | [OOBMSM Gen4 NWP FAS](https://docs.intel.com/documents/arch_datacenter/oobmsm/gen4/oobmsm_fw_gen4_nwp_fas.html) | NWP OOBMSM firmware — PECI/telemetry |

### Test interpretation
- **MSR_READ_HARASSER_REDFISH**: Stress test — BMC reads MSRs from all cores via Redfish/PECI while PM workloads run. Validates concurrent PECI access doesn't cause hangs or data corruption.
- **ILLEGAL_CORES**: Sends RdIAMSREx targeting disabled/non-existent core IDs. Expects `PECI_CC_ILLEGAL` (0x90) completion code. Validates boundary checks (`is_ccp_exist`, core mask validation).
- **SIMULTANEOUS_MSR_READ**: Multiple concurrent RdIAMSREx from BMC console targeting different cores. Validates serialization and P2U mailbox queueing doesn't deadlock.

## Related Sightings
<!-- Key DMR PECI sightings:
- PECI RdPkgConfig PCS 14 (DIMM Temp) incorrect values
- RdPkgConfig Index 0 returning 0x94 under MCA conditions
-->

## NWP Delta

- PECI PM carried from DMR — same OOBMSM→PUnit PECI inbox path
- NWP uses same Primecode `peci_common_v1_0` and `peci_compute_v1_0` flow versions
- NWP OOBMSM FAS is Gen4 variant (separate from DMR Gen3)
- RdIAMSREx 16-bit thread ID is essential for NWP high-core-count configurations
- Wake-on-PECI indicator behavior unchanged from DMR
