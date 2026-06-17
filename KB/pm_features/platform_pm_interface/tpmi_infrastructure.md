# TPMI Infrastructure Reference

> **Source**: [TPMI Common Feature HAS v2.50](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html) — Stan Chen, Vivek Garg, Ankush Varma, Eric DeHaemer (Apr 2026)

TPMI (Topology Aware Register and PM Capsule Interface) is the **unified MMIO-based software interface** for all PM features starting from GNR. It replaces legacy MSR and PECI PCS interfaces with a PCIe VSEC-enumerable, hierarchical, firmware-patchable register framework.

---

## Architecture Overview

### Goals
- **Enumerable**: SW-discoverable via PCIe VSEC (VSEC_ID=0x42) — no CPUID changes needed per generation
- **Extensible**: Patchable PFS/LUT tables; add new PM features without HW changes
- **Hierarchical**: Supports HPM topology — per-die, per-package, root-only register scoping
- **MMIO-based**: Eliminates kernel trap overhead (userspace mmap after initial setup)
- **Access-controlled**: Per-feature opt-in/opt-out, IB/OOB access gating, per-line lock/write-disable

### Primary-to-Sideband Path
OOBMSM serves as the primary-to-sideband converter for TPMI:
```
SW (MMIO) → OOBMSM HostDD → LTM (address lookup) → GPSB → Punit EBB/CSR endpoint
```

### DMR Architecture
- **Dual OOBMSM**: Each IMH has its own OOBMSM with independent BDF, VSEC, PFS, LUT, LTM, Ocode
- **8KB TPMI SRAM** per Punit (vs 2KB on GNR)
- **Dual SAI policy**: TPMI_MAILBOX0 (first 128 lines) = P_U_CODE SAI; TPMI_MAILBOX1 (remaining 896) = OS_W SAI
- **PECI-to-HostDD loopback** supported (unlike GNR) — OOB TPMI access works during PkgC
- **PCS_SELECT always 0** — PCS is fully deprecated

---

## VSEC & PFS Structure

### VSEC Capability Structure
| Field | Bits | Description |
|-------|------|-------------|
| PCI Express Cap ID | 15:0 | 0x000B (Vendor-Specific Extended Capability) |
| Capability Version | 19:16 | 0x1 |
| Next Cap Offset | 31:20 | Next capability or 0x000 |
| VSEC_ID | 47:32 | **0x42** (TPMI PM_Features) |
| VSEC_REV | 51:48 | 0x1 |
| VSEC_LEN | 63:52 | 0x10 (16 bytes including this field) |
| NumEntries | 87:80 | Number of PFS entries |
| EntrySize | 95:88 | PFS entry size in DWORDs (=0x2) |
| tBIR | 98:96 | Target BAR Index Register |
| Address (Table Offset) | 127:99 | Offset from BAR to PFS base (Qword-aligned) |

> **DMR**: tBIR=0x2 (second 64-bit BAR). Read 3rd+4th 32-bit BAR registers for full 64-bit BAR.

### PFS (PM Feature Structure)
| Field | Bits | Description |
|-------|------|-------------|
| TPMI_ID | 7:0 | Feature identifier (see TPMI_ID Encoding) |
| NumEntries | 15:8 | Max Punit instances (superset chop) |
| EntrySize | 31:16 | Entry size per instance in DWORDs |
| CapOffset | 47:32 | Upper 16 bits of 26-bit offset (KB unit) from PFS base |
| Attribute | 49:48 | 0x0=BIOS, 0x1=OS |

### SW Discovery Flow
```
1. Search PCIe extended config space for VSEC_ID=0x42
2. Read tBIR + Table_Offset → BasePtr = BAR[tBIR] + VSEC.Table_Offset
3. For each PFS entry: BasePtr[feature] = BasePtr + PFS.CapOffset[feature]
4. For each instance p in 0..PFS.NumEntries-1:
     data = read(BasePtr[feature] + p * PFS.EntrySize*4 + 0)
     valid = (data != 0xFFFFFFFF_FFFFFFFF)   // All Fs = invalid instance
5. REG_mmio_addr = BasePtr[feature] + instance_idx * PFS.EntrySize*4 + Offset
```

---

## TPMI_ID Encoding

| TPMI_ID | Feature | Scope | DMR Notes |
|---------|---------|-------|-----------|
| 0x00 | **RAPL** | Package root | Socket/DRAM/Platform RAPL |
| 0x01 | **PEM** | Die-scoped | PnP Excursion Monitors |
| 0x02 | **UFS** | Die-scoped | Uncore Frequency Scaling |
| 0x03 | **PMAX** | Package root | PMAX detector |
| 0x04 | **DRC** | Die-scoped | Dynamic Resource Control |
| 0x05 | **SST** | Die-scoped | Intel Speed Select Technology |
| 0x06 | **MISC_CTRL** | Package root | Miscellaneous control/status (linked-list structure) |
| 0x07 | **RPLM** | Die-scoped | Runtime PLL Lock Status Monitor |
| 0x08 | **RIT** | Compute-scoped | Resource Isolation Technology (opt-in, disabled default) |
| 0x0A | **FHM** | Die-scoped | FIVR Health Monitor |
| 0x0B | **MISC_CTRL_A** | All instances | Misc control — all instances |
| 0x0C | **PLR** | Die-scoped | Perf Limit Reasons |
| 0x0D | **BMC_CTL** | Package root | BMC-to-Primecode mailbox |
| 0x0E | **OOB_DIE_CTLS** | Die-scoped | OOB die-scoped registers (ODC) |
| 0x0F | **OOB_PKG_CTLS** | Package root | OOB package-scoped registers (OPC) |
| 0x10 | **PFM** | Die-scoped | Proactive Frequency Management (opt-in, disabled default) |
| 0x80 | **TPMI_CONTROL** | — | Control interface (always enabled, cannot be disabled) |
| 0x81 | **TPMI_INFO** | Package root | BDF/APIC/partition mapping |
| 0x82 | **CPAT** | Die-scoped | CPAT (COR+) |
| 0xFD | **CSR_ALL** | All dielets | CSR registers on all Punits |
| 0xFE | **CSR_COMPUTE** | Compute | CSR on compute Punits |
| 0xFF | **CSR_PKG_ROOT** | Package root | CSR on package root Punit |

---

## TPMI Control Interface

### Mailbox Registers
| Offset | Register | Description |
|--------|----------|-------------|
| 0x0 | TPMI_CONTROL_STATUS | RUN_BUSY [0], OWNER [5:4], CPL [6], STATUS_CODE [15:8], PACKET_LENGTH [31:16] |
| 0x8 | TPMI_COMMAND_DATA | COMMAND [7:0], DATA [63:32] |
| 0x10 | TPMI_CAPABILITIES | 256-bit bitmask of supported TPMI_IDs |

### TPMI_GET_STATE (Command 0x10)
Returns: STATE [0], IB_WRITE_BLOCK [4], IB_READ_BLOCK [5], PCS_SELECT [6], TPMI_ID [15:8], LOCK [31]

### TPMI_SET_STATE (Command 0x11)
Sets: STATE [0], IB_WRITE_BLOCK [4], IB_READ_BLOCK [5], PCS_SELECT [6], TPMI_ID [15:8], LOCK [31] (W1S)

> **DMR**: PCS_SELECT is read-only=0 for inband; Ocode rejects SET_STATE with PCS_SELECT=1.

### Opt-out / Opt-in Access Control
| Feature | TPMI_ID | Polarity | Default State |
|---------|---------|----------|---------------|
| RAPL | 0x00 | opt-out | Enabled |
| PEM | 0x01 | opt-out | Enabled |
| UFS | 0x02 | opt-out | Enabled |
| PMAX | 0x03 | opt-out | Enabled |
| DRC | 0x04 | opt-out | Enabled |
| SST | 0x05 | opt-out | Enabled |
| MISC_CTRL | 0x06 | opt-out | Enabled |
| RPLM | 0x07 | opt-out | Enabled |
| RIT | 0x08 | **opt-in** | Disabled |
| FHM | 0x0A | opt-out | Enabled |
| PLR | 0x0C | opt-out | Enabled |
| BMC_CTL | 0x0D | N/A | Enabled (BMC-only) |
| OOB_DIE_CTLS | 0x0E | N/A | Enabled (BMC-only) |
| OOB_PKG_CTLS | 0x0F | N/A | Enabled (BMC-only) |
| PFM | 0x10 | **opt-in** | Disabled |
| TPMI_INFO | 0x81 | opt-out | Enabled |

> **Key rules**: OOB ≥ Inband. OOB can disable inband. Inband cannot disable OOB. Once opted-out, cannot opt-in until next reset.

### Interface Selection Truth Table (DMR — PCS_SELECT always 0)
| IB_READ_BLOCK | IB_WRITE_BLOCK | Interface Selection | RAPL Example |
|---------------|----------------|---------------------|--------------|
| 0 | 0 | IB TPMI R/W valid. OOB TPMI R/W valid | Inband: TPMI, CSR. OOB: TPMI |
| 0 | 1 | IB TPMI RO valid. OOB TPMI R/W valid | Inband: TPMI RO. OOB: TPMI |
| 1 | 1 | IB TPMI invalid. OOB TPMI R/W valid | Inband: No access. OOB: TPMI |
| 1 | 0 | **Invalid** — Ocode rejects | N/A |

### Roles & Responsibilities
| Agent | Responsibility |
|-------|---------------|
| **LTM/Ocode** | Initialize STATE/LOCK/IB_BLOCK/PCS_SELECT defaults; communicate INTERFACE_SELECT to all Punits; handle GET/SET_STATE; reject invalid combinations |
| **Pcode** | Consume PCS_SELECT/IB_WRITE_BLOCK to route PL/TW inputs to correct PID (IB vs OOB) |
| **BIOS** | Lock all TPMI features before OS boot (error + halt if any lock fails); provide debug knob for lock |
| **OS/Driver** | Opt-in/opt-out per feature via IB_READ/WRITE_BLOCK; atomic R-M-W within 2s timeout |
| **BMC** | Configure IB_WRITE_BLOCK=1 if BMC owns write access; use TPMI (not PCS) on DMR |

---

## DMR PFS & LUT Tables

### DMR PFS (per OOBMSM — identical for IMH0 and IMH1)
| Feature | TPMI_ID | NumEntries | EntrySize (DW) | CapOffset (KB) | Attribute |
|---------|---------|------------|----------------|----------------|-----------|
| TPMI_CONTROL | 0x80 | 1 | 12 | 4 | OS |
| RAPL | 0x00 | 1 | 96 | 8 | OS |
| PEM | 0x01 | 3 | 10 | 12 | OS |
| UFS | 0x02 | 3 | 20 | 16 | OS |
| PMAX | 0x03 | 1 | 6 | 20 | BIOS |
| DRC | 0x04 | 3 | 20 | 24 | OS |
| SST | 0x05 | 3 | 298 | 28 | OS |
| RIT | 0x08 | 2 | 8 | 36 | OS |
| FHM | 0x0A | 3 | 10 | 40 | OS |
| MISC_CTRL | 0x06 | 1 | 6 | 44 | OS |
| PLR | 0x0C | 3 | 10 | 48 | OS |
| BMC_CTL | 0x0D | 1 | 6 | 52 | OS |
| OOB_DIE_CTLS | 0x0E | 3 | 10 | 56 | OS |
| OOB_PKG_CTLS | 0x0F | 1 | 22 | 60 | OS |
| PFM | 0x10 | 3 | 10 | 64 | OS |
| TPMI_INFO | 0x81 | 1 | 4 | 68 | OS |
| CSR_ALL | 0xFD | 3 | 292 | 72 | OS |
| CSR_COMPUTE | 0xFE | 2 | 292 | 80 | OS |
| CSR_PKG_ROOT | 0xFF | 1 | 292 | 84 | OS |

### DMR LUT — RAPL mapping (TPMI_ID=0x0)
| OOBMSM | CapOffset | Feature | PortID | First Register | Overlayed Register |
|--------|-----------|---------|--------|----------------|--------------------|
| IMH0 | 8K | RAPL | imh0 | PCU_CR_TPMI_MAILBOX1[0] | SOCKET_RAPL_DOMAIN_HEADER |
| IMH1 | 8K | RAPL | imh1 | PCU_CR_TPMI_MAILBOX1[0] | SOCKET_RAPL_DOMAIN_HEADER |

> RAPL is package-scoped (NumEntries=1). Only one instance valid per partition. Leaf IMH RAPL registers are write-protected via TPMI_WRITE_DISABLE.

### DMR Die ID / Port ID
| Die | Die ID | Role |
|-----|--------|------|
| imh0 | 8 | Primary IMH |
| imh1 | 9 | Secondary IMH |
| cbb0 | 0 | CBB under IMH0 |
| cbb1 | 1 | CBB under IMH0 |
| cbb2 | 2 | CBB under IMH1 |
| cbb3 | 3 | CBB under IMH1 |

---

## Storage, Fastpath & Access Protection

### TPMI SRAM
- **Width**: 64-bit lines
- **Size**: 8KB on DMR (1024 lines), 2KB on GNR (256 lines)
- **Fastpath**: IO_FASTPATH_MAILBOXES.TPMI_REQ → IO_FASTPATH_TPMI_LINE_AGGREGATOR → IO_FASTPATH_TPMI_LINEMASK
- **Init**: HW zeros at cold reset (MBIST); Pcode programs from OSXML + fuses at warm reset; retains across OS patch load

### Access Protection
| Type | Mechanism |
|------|-----------|
| **RO** | Pcode sets PCU_CR_TPMI_WRITE_DISABLE bit at init |
| **RW-L** | On fastpath: if lock field set → Pcode sets WRITE_DISABLE bit → HW prevents RAM write |
| **Lock race** | SW must: (1) set lock bit, (2) read lock_status until 1, (3) proceed |
| **Unused instances** | Must be write-protected via TPMI_WRITE_DISABLE to prevent fastpath noise |
| **SAI** | TPMI SRAM SAI = OS_W (writable by any SW unless locked) |

### Register Requirements
- 64-bit width per register
- All fields in a register must share same access type (no RO+RW mix)
- First register (offset 0) = HEADER with INTERFACE_VERSION [7:0]
- HEADER must have ≥1 non-zero bit; all-1s HEADER = invalid instance
- CR registers must be contiguous; share same offset/name across dielets

### Interface Version Contract
- **Major** [7:5]: Changed offset, renamed/removed field, width change → driver exits without loading
- **Minor** [4:0]: New field in reserved bits, appended register → driver flags change, update needed for new capability

---

## TPMI_INFO (TPMI_ID 0x81)

### TPMI_BUS_INFO (rev 0.2 — DMR)
| Field | Bits | Description |
|-------|------|-------------|
| FUN | 2:0 | PCIe function number |
| DEV | 7:3 | PCIe device number |
| BUS | 15:8 | PCIe bus number |
| PACKAGE_ID | 23:16 | X2APIC Package ID |
| SEGMENT | 31:24 | PCIe segment number |
| PARTITION | 33:32 | 0=IMH0, 1=IMH1 |
| CD_MASK | 49:34 | Bitmap of compute die IDs this partition supports |
| LOCK | 63:63 | BIOS locks after init |

### MSR 0x54: PM_LOGIC_ID
| Field | Bits | Description |
|-------|------|-------------|
| LP_ID | 2:0 | Core/thread ID within module |
| MODULE_ID | 10:3 | Module ID |
| PM_DOMAIN_ID | 15:11 | Compute die ID (maps to CD_MASK) |

---

## SW Interface Transition (DMR)

### MSR Deprecation on DMR
| MSR | Name | Feature | DMR Status |
|-----|------|---------|------------|
| 0x606 | PACKAGE_POWER_SKU_UNIT | RAPL | **Deprecated** (read=0, write=drop) |
| 0x610 | PACKAGE_RAPL_LIMIT | RAPL | **Deprecated** |
| 0x611 | PACKAGE_ENERGY_STATUS | RAPL | **Deprecated** |
| 0x612 | PACKAGE_ENERGY_TIME_STATUS | RAPL | **Deprecated** |
| 0x613 | PACKAGE_OVERFLOW_STATUS | RAPL | **Deprecated** |
| 0x614 | PACKAGE_POWER_SKU | RAPL | **Deprecated** |
| 0x618 | DRAM_PLANE_POWER_LIMIT | RAPL | **Deprecated** |
| 0x619 | DDR_ENERGY_STATUS | RAPL | **Deprecated** |
| 0x61B | DRAM_PLANE_OVERFLOW_STATUS | RAPL | **Deprecated** |
| 0x61C | DRAM_POWER_INFO_CFG | RAPL | **Deprecated** |
| 0x64D | PLATFORM_ENERGY_STATUS | RAPL | **Deprecated** |
| 0x65C | PLATFORM_POWER_LIMIT | RAPL | **Deprecated** |
| 0x665 | PLATFORM_POWER_INFO | RAPL | **Deprecated** |
| 0x666 | PLATFORM_RAPL_SOCKET_PERF_STATUS | RAPL | **Deprecated** |
| 0x60F | RAPL_ENERGY_REPORT | RAPL | **Deprecated** |
| 0x620 | UNCORE_RATIO_LIMIT | UFS | **Deprecated** (since GNR) |
| 0x621 | UNCORE_PERF_STATUS | UFS | **Deprecated** (since GNR) |
| 0x64F | CORE_PERF_LIMIT_REASONS | PLR | **Deprecated** (since GNR) |
| 0x6B1 | RING_PERF_LIMIT_REASONS | PLR | **Deprecated** (since GNR) |
| 0x601 | VR_CURRENT_CONFIG | PL4 | **Deprecated** (since GNR) |

### PCS Deprecation on DMR
- All 53 GNR PCS services removed on DMR
- Replaced by: TPMI (control/status) + PMT (telemetry/monitoring/streaming)
- New TPMI registers: OOB_DIE_CTLS (ODC), OOB_PKG_CTLS (OPC)

### Per-Feature Interface Evolution
| Feature | SPR IB | GNR IB | DMR IB | SPR OOB | GNR OOB | DMR OOB |
|---------|--------|--------|--------|---------|---------|---------|
| RAPL | MSR | MSR+TPMI | **TPMI** | PCS | PCS+TPMI | **TPMI** |
| PEM | N/A | TPMI | **TPMI** | PCS | PCS+TPMI | **TPMI** |
| UFS | MSR | TPMI | **TPMI** | N/A | TPMI | **TPMI** |
| PMAX | Mailbox | TPMI | **TPMI** | N/A | TPMI | **TPMI** |
| SST | Mailbox | TPMI | **TPMI** | Mailbox | TPMI | **TPMI** |

---

## OOB_DIE_CTLS (ODC) Registers
| Index | Register | Access | Key Fields |
|-------|----------|--------|------------|
| 0 | ODC_HEADER | RO | INTERFACE_VERSION [7:0] |
| 1 | ODC_PECI_WAKE_MODE | RW | WAKE_ON_PECI_INDICATOR [7:0]: 0=disable, 1=PkgC6 wake, 2=Core C6+PkgC6 wake |
| 2 | ODC_TURBO_MAX_RATIO | RW | TURBO_MAX_RATIO [7:0] |
| 3 | ODC_TRL_NUMCORES | RO/V | NUM_CORE_0..7 [63:0] (8×8-bit) per current PP level |
| 4 | ODC_TRL_RATIOS | RO/V | RATIO_0..7 [63:0] (8×8-bit) = min(fuse, MSR 0x1AD, ODC_TURBO_MAX_RATIO) |

## OOB_PKG_CTLS (OPC) Registers
| Index | Register | Access | Key Fields |
|-------|----------|--------|------------|
| 0 | OPC_HEADER | RO | INTERFACE_VERSION [7:0], MEMORY_CHANNELS [15:8] |
| 1 | OPC_PKGC_ENTRY_CONTROL | RW | PREVENT_PKGC [0] |
| 2 | OPC_PKG_THERM_STATUS | RO/V | Thermal/PROCHOT/OOS/Threshold/Power/PMAX status+log bits [13:0] |
| 3 | OPC_PKG_THERM_STATUS_LOG_CLEAR | RW/1C | W1C to clear corresponding log bits in OPC_PKG_THERM_STATUS |
| 4 | OPC_THERMAL_MONITOR | RW | DECAY_FACTOR [6:0], ENABLE_EWMA [7], INBAND_LOCK [30] |
| 5 | OPC_HWP_CAPABILITY | RO/V | HIGHEST/GUARANTEED/MOST_EFFICIENT/LOWEST_PERFORMANCE (4×8-bit) |
| 6 | OPC_HWP_CONTROLS | RW | MIN/MAX/EPP [31:0], MIN/MAX/EPP override bits [34:32], ALT_EPB [43:40] |
| 7-10 | OPC_DIMM_TEMPS_0..3 | RW | DIMM temps U8.0 × 4 channels per register (16 channels total) |

---

## DMR-Specific Implementation Notes
1. **TPMI SRAM init**: Primecode uses OSXML defaults + TDP fuse → PL1=TDP, PL2=1.2×TDP, PL1_EN always active
2. **Unused instance registers**: Must set TPMI_WRITE_DISABLE=1 to prevent fastpath noise
3. **CSR_* controllability**: All 3 CSR_xxx share same control settings (Ocode workaround for PECI-HostDD loopback gap)
4. **PCS_SELECT**: Always 0 on DMR; Ocode rejects SET_STATE with PCS_SELECT=1
5. **BMC-only features** (BMC_CTL, ODC, OPC): Initialized with STATE=1, LOCK=1, IB_WRITE_BLOCK=1, IB_READ_BLOCK=1
6. **OOB TPMI access during PkgC**: Supported via PECI-to-HostDD loopback (DMR only)
7. **MCU patch revision**: Use S3M.SOCCM_REVIDS (not VSEC_SPARE_2 as on GNR)

---

## Validation Starting Points
- Validate VSEC capability structure integrity
- Validate PFS table correctness (TPMI_ID, NumEntries, EntrySize, CapOffset)
- Validate LUT PortID and first register mapping
- HEADER never returns all-Fs unless feature disabled or instance absent
- Non-existent Punit / invalid offset returns all-Fs
- End-to-end R/W flow for SRAM and CSR register types
- Lock semantics (RO, RW-L) enforcement
- Fastpath handling on SRAM write
- SAI enforcement
- TPMI control interface (GET/SET_STATE) all combinations
- Both inband and OOB access paths

---

## Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [TPMI Common Feature HAS v2.50](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html) | Primary TPMI architecture spec |
| HAS | [TPMI LTM FW](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html#ltm-fw) | Interface selection truth table |
| HAS | [DMR Manageability & Telemetry](https://docs.intel.com/documents/arch_datacenter/DMR/Manageability%20and%20Telemetry/Telemetry_and_Manageability_HAS.html#tpmi-support) | DMR OOBMSM VSEC mapping |
| HAS | [DMR D2D Telem/Mgmt Flows](https://docs.intel.com/documents/arch_datacenter/DMR/D2D/Telem_Mng_D2D_flows.html#tpmi-register-access-flow) | DMR TPMI register access flow |
| FAS | [OOBMSM FW Gen4 FAS](https://docs.intel.com/documents/arch_datacenter/OOBMSM/Gen4/OOBMSM_FW_Gen4_FAS.html#tpmi-support) | DMR Ocode TPMI implementation |
| FAS | [OOBMSM FW Gen3 FAS](https://docs.intel.com/documents/arch_datacenter/OOBMSM/Gen3/OOBMSM_FW_Gen3_FAS.html#tpmi-support-1) | GNR Ocode TPMI implementation |
| Data | [DMR PFS/LUT IMH0 (xlsx)](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/assets/DMR/TPMI_Data_Structures_rev2p7_DMR0.xlsx) | DMR TPMI data structures - IMH0 |
| Data | [DMR PFS/LUT IMH1 (xlsx)](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/assets/DMR/TPMI_Data_Structures_rev2p7_DMR1.xlsx) | DMR TPMI data structures - IMH1 |
| JSON | [DMR PFS IMH0](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/assets/PFS_DMR0_2p7.json) / [IMH1](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/assets/PFS_DMR1_2p7.json) | Machine-readable PFS |
| JSON | [DMR LUT IMH0](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/assets/LUT_DMR0_2p7.json) / [IMH1](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/assets/LUT_DMR1_2p7.json) | Machine-readable LUT |
| Data | [TPMI Sheets (xlsx)](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/assets/TPMI_Sheets.xlsx) | ID encoding, PFS, access control tables |
| Data | [DMR Transitions (xlsx)](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/assets/DMR/DMR_transitions.xlsx) | PCS→TPMI/PMT transition details |
| Data | [DMR Global ID HAS](https://docs.intel.com/documents/arch_datacenter/DMR/ConfigFabric/Global_IDs/7nm_wave4_DMR_Global_ID_HAS.html#die-id-strap) | Die ID / Port ID assignment |
| HAS | [Punit IP MAS (TPMI baseline)](https://docs.intel.com/documents/sysip_pm/MAS_wave4/Feature_MAS/Punit_VSEC/Punit_VSEC.html) | Punit VSEC baseline |
| HAS | [DMR CBB TPMI](https://docs.intel.com/documents/pm_doc/src/server/arch_common/TPMI/TPMI.html) | CBB TPMI feature list |
| Feature HAS | [RAPL DVSEC](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/RAPL_DVSEC/RAPL_DVSEC.html) | RAPL TPMI register layout |
| Feature HAS | [PEM](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/PEM/PEM_HAS.html) | PEM TPMI registers |
| Feature HAS | [UFS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/Hierarchical%20UFS/HPM_UFS.html) | UFS TPMI registers |
| Feature HAS | [SST](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html#tpmi-sst-interface) | SST TPMI registers |
| Feature HAS | [PLR](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/perf_limit_reasons/perf_limit_reasons_has.html#tpmi) | PLR TPMI registers |
| Feature HAS | [RIT](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/RIT/RIT.html#tpmi-interface) | RIT TPMI registers |
| Feature HAS | [FHM](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/FIVR_Monitor/GNR_FIVR_monitor.html) | FIVR Health Monitor |
| Feature HAS | [PFM / SIMPL](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_SIMPL.html#configuration-and-observability) | PFM TPMI registers |
| Feature HAS | [BMC_CTL](https://docs.intel.com/documents/arch_datacenter/GNR_Family/Common/RAS/BMC_CTL_TPMI_ras_offload.html) | BMC control TPMI |
| OSXML | `/nfs/sc/disks/sdg74_1200/schen6/DMR/` | DMR TPMI OSXML files |
