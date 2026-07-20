# TCD: [NWP PM] OS2P Mailbox Validation

| Field | Value |
|-------|-------|
| **TCD ID** | [16030768338](https://hsdes.intel.com/appstore/article-one/#/16030768338) |
| **Title** | [NWP PM] OS2P Mailbox Validation |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030767552 -- NWP PM OS2P Mailbox](https://hsdes.intel.com/appstore/article-one/#/16030767552) |
| **Parent TP** | [16030765561 -- NWP PM Interfaces (OS2P/TPMI/PECI/PMT)](https://hsdes.intel.com/appstore/article-one/#/16030765561) |
| **KB last updated** | 2026-07-20 |
| **Feature** | PM Interfaces -- OS2P Mailbox |

## Section 1: Architecture / Micro-architecture and Functionality

**OS2P (OS-to-Punit) Mailbox** is the runtime software interface allowing the OS/kernel to send commands to PCode firmware. It is architecturally distinct from B2P (BIOS-to-Punit, boot-time only). This TCD validates that OS2P commands are correctly dispatched, processed, and return valid completion codes via both the legacy CSR path and the modern TPMI path.

> **Architecture overview:** See [TPF 16030767552 -- NWP PM OS2P Mailbox](https://hsdes.intel.com/appstore/article-one/#/16030767552) Section 2 Design Details for mailbox architecture, transport paths, and command handler routing.

### NWP-Specific Deltas

- NWP inherits DMR OS2P mailbox unchanged -- same command set and HW interface
- Both CSR and TPMI transport paths supported
- NWP Primecode uses same `os_csr_common_v1_0` and `os_tpmi_common_v1_0` flow versions
- Single NIO die -- OS2P commands route to NIO PUnit only
- `READ_PKG_CONFIG` (0x78) always supported -- used to mask unavailable IP instances reflecting NWP reduced topology

### TC Coverage Map

| TC | Scope | Environment |
|----|-------|-------------|
| [16030715638 -- [PSS] Mailbox Sweep](https://hsdes.intel.com/appstore/article-one/#/16030715638) | OS2P command sweep -- all accessible commands via CSR and TPMI paths | PSS |

### Coverage Gaps

| Gap | Recommended TC | Priority |
|-----|---------------|----------|
| FV OS2P validation (post-silicon) | *(TC TBD)* -- OS2P sweep on real silicon | H |
| OS2P via TPMI path (opcode 0xe) specifically | *(TC TBD)* -- TPMI-specific OS2P path verification | M |
| Invalid/unsupported command error handling | *(TC TBD)* -- negative test for invalid opcodes | M |

---

## Section 2: Interfaces and Protocols

| Interface | Path / Address | Access | Description |
|-----------|---------------|--------|-------------|
| OS_MAILBOX_INTERFACE (CSR) | PCU_CR_OS_MAILBOX_INTERFACE_CFG / MSR 0xB0 | RW | COMMAND[7:0], ADDR[28:8], RUN_BUSY[31], completion code |
| OS_MAILBOX_DATA (CSR) | PCU_CR_OS_MAILBOX_DATA_CFG / MSR 0xB1 | RW | Input/output data for mailbox command |
| OS_MAILBOX (TPMI) | TPMI SRAM opcode 0xe (OS_MAILBOX) | RW | TPMI-based OS mailbox -- same fields as CSR, routed via OOBMSM |
| IO_FASTPATH_MAILBOXES | Fastpath aggregator | Internal | Triggers PCode on OS mailbox write |

---

## Section 3: Reset, Power, and Clocking

- **Boot sequence**: OS2P mailbox available after RST_CPL3 (BIOS handoff)
- **Pre-CPL3 lockout**: Some commands (QUIESCE_PECI, PM_SECURITY_CONTROL) locked after RST_CPL3 -- only ACM/ACTM can use them
- **Warm reset**: OS2P state cleared; mailbox re-initialized by PrimeCode during reset sequence
- **PkgC interaction**: OS2P commands may fail or be deferred during deep PkgC states

---

## Section 4: Programming Model

OS2P uses a run-busy protocol:
1. OS writes `OS_MAILBOX_DATA` with input parameters
2. OS writes `OS_MAILBOX_INTERFACE` with COMMAND[7:0] + ADDR[28:8] + RUN_BUSY=1
3. Fastpath fires in Punit -- scheduler dispatches to OS mailbox flow
4. PCode reads interface+data registers, builds MbCmd::Command struct
5. Same B2P handler table processes the command opcode
6. Response written to OS_MAILBOX_INTERFACE (completion code) + OS_MAILBOX_DATA (return data)
7. RUN_BUSY cleared -- OS polls until 0

**TPMI path (opcode 0xe):** Same protocol but accessed via TPMI MMIO space. OOBMSM translates MMIO write to GPSB CR write to PUnit TPMI SRAM. Fastpath mechanism identical.

### Key OS2P-Accessible Commands

| Command | Opcode | Description | NWP Status |
|---------|--------|-------------|------------|
| READ_PM_CONFIG | 0x94 | Read PM configuration (sub-cmds: MIN_ICCP_LEVEL, PROG_SSC_CONTROL) | Supported |
| WRITE_PM_CONFIG | (write variant) | Write PM configuration | Supported |
| PM_MISC_CONTROL | 0xd0 | Read/write PM misc; sub-cmd THERM_MONITOR_STATUS (0x20) | Supported |
| READ_PKG_CONFIG | 0x78 | Read enabled IP instance mask | Supported (NWP topology) |
| CONFIG_TDP | 0x7F | SST configuration | Supported (SST-TF only) |
| SET_MC_FREQ / READ_MC_FREQ | -- | MC frequency set/read | Supported |
| QUIESCE_PECI / UNQUIESCE_PECI | -- | ACM/ACTM initiated; locked post-CPL3 | Supported |

### Completion Codes

| Code | Meaning |
|------|---------|
| 0x0 | SUCCESS |
| 0x1 | INVALID_COMMAND |
| 0x2 | TIMEOUT |
| 0x5 | ERR_INTERFACE_LOCKED_OBB |
| (converted) | NOT_SERVICED_ON_THIS_DIE -> INVALID_COMMAND |

---

## Section 5: Operational Behavior

> **WHAT:** OS2P mailbox commands are correctly dispatched and return valid responses via both CSR and TPMI paths.

| Scenario | Expected Outcome | TC Link |
|----------|-----------------|---------|
| Sweep all OS-accessible commands via CSR path | Each command returns valid completion code; data matches expected values | [16030715638](https://hsdes.intel.com/appstore/article-one/#/16030715638) |
| Sweep all OS-accessible commands via TPMI path (opcode 0xe) | Same results as CSR path | [16030715638](https://hsdes.intel.com/appstore/article-one/#/16030715638) |
| Invalid command opcode via OS2P | Returns INVALID_COMMAND (0x1) completion code | *(Gap -- no TC)* |
| READ_PKG_CONFIG on NWP | Returns correct IP instance mask for NWP topology | [16030715638](https://hsdes.intel.com/appstore/article-one/#/16030715638) |

**Pass/fail bar:**
- All supported OS2P commands return SUCCESS (0x0) completion code
- OS_MAILBOX_DATA contains expected return values for each command
- RUN_BUSY clears within timeout (<10ms per command)
- CSR path and TPMI path return identical results for same command
- Invalid commands return INVALID_COMMAND (0x1), not hang or crash
- READ_PKG_CONFIG returns topology mask consistent with NWP HW (single NIO, 2 CBBs)

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| **CSR vs TPMI path equivalence** | Same command via both paths should return identical results | ⚠️ Verification criterion -- add dual-path comparison in sweep TC | Add assertion in TC 16030715638 |
| **Invalid opcode rejection** | Unsupported opcode returns INVALID_COMMAND, no side effects | ❌ Not covered | New TC needed -- negative command test |
| **RUN_BUSY timeout** | OS polls but PCode never completes | ❌ Not covered | New TC needed -- timeout detection test |
| **Locked command post-CPL3** | QUIESCE_PECI/PM_SECURITY_CONTROL rejected after BIOS handoff | ❌ Not covered | New TC needed -- locked command rejection |
| **NOT_SERVICED_ON_THIS_DIE conversion** | Command sent to wrong die returns INVALID_COMMAND (converted) | ⚠️ Verification criterion -- relevant on DMR dual-die; NWP single NIO simplifies | Low priority for NWP |
| **Concurrent OS2P and B2P** | Both mailboxes active simultaneously -- no corruption | ⚠️ Verification criterion | Add to cross-product scenarios |

---

## Section 7: Security / Safety / Policy

- OS2P commands explicitly tagged with `<mbox_access mbox="OS" />` in B2P specification
- Post-CPL3 lockout prevents OS from using QUIESCE_PECI / PM_SECURITY_CONTROL
- OOB agent can lock OPC_THERMAL_MONITOR via INBAND_LOCK -- OS2P PM_MISC_CONTROL returns ERR_INTERFACE_LOCKED_OBB
- No OS2P command modifies security-critical state without BIOS pre-authorization

---

## Section 8: References

- [B2P Mailbox Specification](https://docs.intel.com/documents/primecode/has/DMR/BIOS%20Mailbox/B2P_mailbox_specification.html) -- OS2P commands defined with mbox="OS" tag
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/PM/NWP_IMH_SOC_PM_MAS.html) -- NWP PM specification
- KB: [platform_pm_interface/os2p_mailbox.md](../../pm_features/platform_pm_interface/os2p_mailbox.md) -- Feature KB reference
- KB: [platform_pm_interface/tpmi.md](../../pm_features/platform_pm_interface/tpmi.md) -- TPMI infrastructure
- Primecode src: `src/flow/mailbox/os/os_csr/os_csr_common/v1_0/os_csr.cpp`
- Primecode src: `src/flow/mailbox/os/os_tpmi/os_tpmi_common/v1_0/os_tpmi.cpp`
