# Platform PM Interface > TPMI

> **Status**: Enriched
> **Parent**: [Platform PM Interface](platform_pm_interface_main.md)

## Architecture Summary

**TPMI (Topology-aware Register and PM Capsule Interface)** is a flexible, PCIe VSEC-based MMIO interface that exposes PM feature registers to software. It replaces many traditional MSR-based PM controls with a software-software contract interface — data can be added/changed without modifying hardware.

### Key architectural properties
- Implemented via **PCIe Vendor-Specific Extended Capabilities (VSEC)**
- **OOBMSM** hosts the PCIe function and converts MMIO operations → IOSF → GPSB CR operations to PUnit
- PUnit provides **2KB addressable GPSB CR space** (4KB physical including ECC) = "TPMI SRAM"
- **Fastpath mechanism**: software writes to TPMI SRAM trigger a fastpath event to PCode; PCode writes back do NOT trigger fastpath (avoids infinite loops)
- Each 64-bit SRAM line can be independently **locked** (read-only for SW) via `TPMI_WRITE_DISABLE` registers

### In-Band vs Out-of-Band access

| Access type | Path | Who |
|-------------|------|-----|
| **In-Band** | OS driver → PCIe MMIO → OOBMSM → GPSB → PUnit TPMI SRAM | Linux `intel_tpmi` kernel driver |
| **Out-of-Band (OOB)** | BMC → I3C/MCTP → OOBMSM → GPSB → PUnit TPMI SRAM | BMC management agent |

Both paths converge at the OOBMSM VSEC MMIO space. The OOB path has additional control registers (`OOB_DIE_CTRL` opcode 0x15, `OOB_PKG_CTRL` opcode 0x16) that allow the BMC to manage per-die and per-package PM settings, including the ability to **disable in-band writes** for specific TPMI features.

### TPMI Feature Opcodes (PM features mapped to TPMI SRAM)

| Opcode | Feature | Description |
|--------|---------|-------------|
| 0x0 | **RAPL** | Socket/DRAM/Platform power limits and status |
| 0x1 | **PEM** | Power & Performance Excursion Monitors |
| 0x2 | **UFS** | Uncore Frequency Scaling |
| 0x3 | **MemCLOS** | Memory Class-of-Service (memory bandwidth QoS) |
| 0x4 | **SST** | Intel Speed Select Technology (SST-PP, SST-CP, SST-BF, SST-TF) |
| 0x5 | **TPMI_INFO** | TPMI bus info (BDF, package ID) — written by BIOS at CPL3 |
| 0x6 | **FHM** | FIVR Health Monitor |
| 0x7 | **PMAX** | Maximum Power Level |
| 0x8 | **MISC_CTL** | Miscellaneous controls |
| 0x9 | **PROCHOT** | Prochot configuration |
| 0xa | **PLR** | Performance Limit Reasons |
| 0xc | **PKG_ENERGY_TIME** | RAPL package energy & time status counters |
| 0xd | **RAPL_ENERGY_REPORT** | RAPL energy reporting |
| 0xe | **OS_MAILBOX** | OS2P mailbox via TPMI (see [OS2P Mailbox](os2p_mailbox.md)) |
| 0xf | **OC_MAILBOX** | Overclocking mailbox |
| 0x10 | **MISC_PKG_CTLS** | Miscellaneous package controls |
| 0x11 | **INTERFACE_SELECT** | RAPL interface selection (MSR vs TPMI) |
| 0x12 | **BMC_MAILBOX** | BMC-to-Punit mailbox via TPMI |
| 0x15 | **OOB_DIE_CTRL** | OOB die-level control (DMR+ only) |
| 0x16 | **OOB_PKG_CTRL** | OOB package-level control (DMR+ only) |
| 0x18 | **AUX_MAILBOX** | Auxiliary mailbox (DMR+ only) |
| 0x19 | **ASSERT_ERR0** | Err0 assertion interface |
| 0x1c | **CPAT** | CPAT interface (COR only) |

## Execution Flow

### Reset initialization
1. **Cold reset**: BIST zeros TPMI SRAM. **Warm reset**: Primecode clears SRAM at `ResetSeq::CLEAR_HPM_SRAM` (~834μs)
2. Each PM feature hooks to `TPMI_INIT` reset sequence to populate its TPMI SRAM region
3. Features call `TpmiMailbox::writeLine()` to set initial values and `lockLine()` for read-only registers
4. BIOS writes `TPMI_BUS_INFO` (BDF + package ID) at CPL3

### Runtime (fastpath)
1. Software writes to TPMI MMIO space (in-band or OOB)
2. OOBMSM translates MMIO write → IOSF → GPSB CR write to PUnit TPMI SRAM
3. **Fastpath chain**: `IO_FASTPATH_MAILBOXES.TPMI_REQ` → `IO_FASTPATH_TPMI_LINE_AGGREGATOR` → `IO_FASTPATH_TPMI_LINEMASK_[0-7]`
4. PCode `TPMI::handle_tpmi_fast_path_tx()` reads aggregator → identifies changed lines
5. For each changed line, PCode reads the SRAM data, looks up the registered command handler
6. Command handler processes the change (e.g., RAPL updates power limit, UFS updates frequency target)
7. Handler writes response back to TPMI SRAM if needed

### PLR TPMI Mailbox (PCode CBB example)
PCode CBB has a dedicated `PLRmbx` flow that registers `IO_PLR_MAILBOX_INTERFACE` with the TPMI fastpath system, supporting READ/WRITE commands for per-CCP and per-ring-domain Performance Limit Reasons.

## Key Registers & Interfaces

| Register | Role |
|----------|------|
| `PCU_CR_TPMI_MAILBOX_[0-255]` | 256×64-bit TPMI SRAM lines (data exchange between driver and PCode) |
| `PCU_CR_TPMI_WRITE_DISABLE[0-3]` | Lock bits — each bit locks one SRAM line for SW writes |
| `IO_FASTPATH_MAILBOXES.TPMI_REQ` [25] | Level-1 fastpath aggregator for any TPMI write |
| `IO_FASTPATH_TPMI_LINE_AGGREGATOR` [7:0] | Level-2: each bit = one 32-line group that changed |
| `IO_FASTPATH_TPMI_LINEMASK_[0-7]` [31:0] | Level-3: per-line change indicators (clear-on-read) |
| `IO_FASTPATH_TPMI_AGGREGATOR` | 32-bit register for TPMI FP events (PCode CBB) |
| `IO_PLR_MAILBOX_INTERFACE` / `IO_PLR_MAILBOX_DATA` | PLR TPMI mailbox (PCode CBB) |

## Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [TPMI HAS (Arch Common)](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html) | Architecture specification |
| HAS | [TPMI Specification](https://docs.intel.com/documents/arch_datacenter/DMR/Overview/FirmwareArch.html) | DMR firmware architecture |
| HAS | [TPMI SST Interface](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html#tpmi-sst-interface) | SST via TPMI |
| HAS | [MemCLOS DRC VSEC MMIO](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/MemCLOS/MemCLOS_DRC.html#vsec-mmio) | MemCLOS via TPMI |
| HAS | [PEM VSEC Interface](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/PEM/PEM_HAS.html#vsec-mmio) | PEM via TPMI |
| HAS | [RAPL VSEC Interface](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/RAPL_DVSEC/RAPL_DVSEC.html) | RAPL via TPMI |
| HAS | [MISC Registers](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/HPM%20Punit%20CSR/hpm_punit_regs.html#virtual-msr) | MISC registers via TPMI |
| HAS | [BMC Mailbox](https://docs.intel.com/documents/arch_datacenter/GNR_Family/Common/RAS/BMC_CTL_TPMI_ras_offload.html) | BMC mailbox via TPMI |
| Primecode src (mailbox) | `src/flow/mailbox/tpmi/v1_0/tpmi_mailbox.cpp` | `TpmiMailbox` class — SRAM read/write/lock APIs |
| Primecode src (commands) | `src/flow/mailbox/tpmi/v1_0/tpmi_mailbox_commands.hpp` | TPMI command registration and handlers |
| Primecode src (os_tpmi) | `src/flow/mailbox/os/os_tpmi/os_tpmi_common/v1_0/os_tpmi.cpp` | OS mailbox via TPMI path |
| Primecode src (OOB handlers) | `src/flow/mailbox/tpmi_handlers/oob_die_control/` | OOB die control handlers |
| Primecode src (OOB handlers) | `src/flow/mailbox/tpmi_handlers/oob_package_control/` | OOB package control handlers |
| Primecode src (TPMI OSXML) | `src/cfgdata/tpmi_osxml/v1_0/AddressMap_TPMI.os.xml` | TPMI address map definition |
| Primecode src (RDL) | `src/cfgdata/dmr_io/v1_0/ip_headers/pm_tpmi_mailbox_rdl.hpp` | TPMI register offset enums |
| Primecode doc | `src/doc/tpmi.dox` | Comprehensive TPMI documentation |
| PCode src (TPMI flow) | `source/pcode/flows/tpmi.cpp` | CBB PCode: TPMI SRAM init, lock, fastpath handler |
| PCode src (PLR TPMI) | `source/pcode/flows/plr_tpmi_mailbox.cpp` | CBB PCode: PLR TPMI mailbox |
| PCode src (TPMI address map) | `source/tpmi/AddressMap_TPMI.os.xml` | CBB TPMI address map |

### Test interpretation
- **InBand Read Block**: Validates that locked TPMI lines correctly block in-band writes and return expected completion codes
- **Inband Harasser**: Stress test — continuous in-band TPMI reads/writes while PM workloads run; validates fastpath doesn't drop events
- **OOB Writes**: BMC writes to TPMI SRAM via OOB path; validates OOB-written values are correctly processed by PCode
- **OOB Harasser**: Stress test — concurrent OOB TPMI writes; validates no data corruption or fastpath loss
- **OOB Disable Inband Write**: BMC uses OOB control registers to disable in-band writes for specific features; validates enforcement

## Related Sightings
<!-- Key known sighting: HSD 16012989777 - Primecode unable to write to locked lines in TPMI SRAM -->

## NWP Delta

- TPMI carried from DMR — same PCIe VSEC / OOBMSM / TPMI SRAM architecture
- NWP Primecode inherits `tpmi_v1_0` flow and same handler registration infrastructure
- DMR+ opcodes (`OOB_DIE_CTRL` 0x15, `OOB_PKG_CTRL` 0x16, `AUX_MAILBOX` 0x18, `ASSERT_ERR0` 0x19) apply to NWP
- NWP-specific TPMI filtering may differ (check `source/tpmi/cbb_tpmi_feature_filter.py`)
- `CPAT` opcode 0x1c is COR-only, not applicable to NWP
- TPMI SRAM size: Primecode uses 256×64-bit lines (2KB addressable); PCode CBB uses 1024-entry addressable space
- SIMPL TPMI support added (rev 0.7, Apr 2026) — check NWP applicability
