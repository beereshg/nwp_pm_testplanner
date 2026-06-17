# SST > HGS

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing (2026-05-28)
> **Parent**: [SST](sst_main.md)
> **Source Confidence**: High — Architecture from PCode `hgs.h`/`hgs.cpp`, Primecode `base_ia_hgs.hpp`/`hgs.hpp`, HPM message definitions. HGS ZBB'd on NWP per [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — HGS transactions appear in NWP `ok_going_zero.txt`.

## Baseline (DMR)

**HGS (Hardware-Guided Scheduling)** provides OS scheduler hints by writing a performance table to core-accessible memory via the P2U (PCode-to-Ucode) mailbox. Each core slot receives a value of 100 (capable/active) or 0 (parked), exposed to the OS via CPUID/HFI for thread placement. **HGS is ZBB’d on NWP** — transactions `HgsConfigureTx_next`, `HgsTableInitTx_next`, and `HgsTimerEvent_next` are zeroed out in `ok_going_zero.txt`.

**Topology (DMR reference)**: PCode Root → HPM HGS_UPDATE → Leaf CBBs → P2U mailbox → Core memory (one HGS table entry per CCP/module). Primecode assigns CPUID line indices via `LP_DATA` PMA CR writes on each LP.

```
HGS table update flow (DMR — ZBB’d on NWP)
├── SstManager resolves sst_resolved_module_mask (from active PP level)
├── Root sends HPM HGS_UPDATE to all Leaf CBBs
├── Leaf HGS::handle_hpm_msg() computes changed CCP mask
├── Fill hgs_table[]: 100 for active cores, 0 for parked
├── P2U mailbox writes table (8 bytes per write: header + data rows)
└── OS reads CPUID HFI → schedules threads on cores with non-zero values
```

**Boot activation**: N/A on NWP (ZBB’d). DMR: triggered by SST-PP level change or module park event.

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| P2U Mailbox | CBB compute | PCode-to-Ucode channel; writes HGS table to core-accessible memory | P2U opcode HGS; 8 bytes per write | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| CPUID HFI table | Compute core | OS-visible hardware feedback interface; per-core performance value from HGS | CPUID HFI leaf | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| LP_DATA PMA CR | Per-LP (compute core) | Stores CPUID line index for HGS table position assigned by Primecode | COMPUTE0_CORE_SLICE0_CR_LP_DATA | Primecode `base_ia_hgs.cpp` |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| PCode (CBB Leaf) | Leaf CBB | HGS table fill (100/0 per core); P2U FSM: idle→send_p2u_mailbox→pending_p2u_mailbox | `hgs.cpp::handle_hpm_msg()`, `fill_hgs_table()` | PCode source |
| PCode (CBB Root) | Root CBB | Resolves sst_resolved_module_mask; sends HPM HGS_UPDATE to all Leaf CBBs | `sst_manager.cpp`, `hpm_msgs.xml::HGS_UPDATE` | PCode source |
| PrimeCode (IMH) | IMH-P | Assigns CPUID line indices to each LP via LP_DATA PMA CR writes | `base_ia_hgs.cpp::assignCpuidLineIndex()` | Primecode source |
| BIOS | Pre-OS | HGS configuration via READ_HGS_CONFIG / WRITE_HGS_CONFIG BIOS mailboxes | BIOS Mailbox HGS services | PCode mailbox XML |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| CPUID | HFI leaf | RO | Per-core performance value (0=parked, 100=capable); OS scheduler input for thread placement | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| MSR | MISC_PWR_MGMT2.ENABLE_HWP | RW | HGS requires HWP enabled; read by PCode as prerequisite gate | [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) |
| Camarillo Mailbox | HGS_TABLE, HGS_CONFIG | RW | OOB interface for HGS table read and update rate configuration | PCode Camarillo mailbox XML |

## KPI & Timing

| Parameter | Value / Target | Source |
|-----------|----------------|--------|
| HGS performance value (active core) | 100 (HGS_ENABLED_CORE_CONSTANT_VALUE) | PCode `hgs.h` |
| HGS performance value (parked core) | 0 | PCode `hgs.h` |
| P2U write granularity | 8 bytes per write (header + data rows) | PCode `hgs.cpp` |
| HGS FSM states | 3: idle → send_p2u_mailbox → pending_p2u_mailbox | PCode source |
| NWP status | ❌ ZBB’d — HgsConfigureTx_next, HgsTableInitTx_next, HgsTimerEvent_next in ok_going_zero.txt | `nwp_imh/v1_0/ok_going_zero.txt` lines 195–197 |

## NWP Delta

### NWP Status: ❌ ZBB'd

HGS (Hardware Guided State) is an SST-PP variant. Since SST-PP is ZBB'd on NWP, HGS is also ZBB'd. Test cases listed as `Runnable_On_N-1` are expected to serve as **negative validation only**.

| Aspect | NWP Behavior | Source |
|--------|-------------|--------|
| HGS (SST-PP variant) | ❌ ZBB'd | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html), [HSD 22021155414](https://hsdes.intel.com/appstore/article/#/22021155414) |

## Legacy (Human-Curated Reference)

### Architecture Summary

**HGS (Hardware-Guided Scheduling)** provides OS scheduler hints identifying which cores are highest-performing, enabling intelligent thread placement. PCode maintains an HGS table (one entry per CCP/module) with a constant performance value (100) for active/favored cores and 0 for parked cores. This table is written to core-visible memory via the P2U (PCode-to-Ucode) mailbox and exposed to the OS through CPUID leaf / HWP_CAPABILITIES, allowing the OS scheduler to preferentially schedule threads on capable cores. HGS is **ZBB'd on NWP** (transactions listed in `ok_going_zero.txt`: `HgsConfigureTx_next`, `HgsTableInitTx_next`, `HgsTimerEvent_next`).

#### How It Works

1. **Root CBB** (PCode `SstManager`) resolves the `sst_resolved_module_mask` from the current SST-PP level's core configuration
2. **HPM message** `HGS_UPDATE` is sent from Root to all Leaf CBBs requesting an HGS table refresh
3. Each **Leaf PCode** (`HGS::handle_hpm_msg()`) computes changed CCP mask, fills `hgs_table[]` with `HGS_ENABLED_CORE_CONSTANT_VALUE` (100) for active cores, 0 for parked
4. **P2U mailbox** writes table data to core-accessible memory in groups (8 bytes per write, header + data rows)
5. **Primecode** (`base_ia_hgs.cpp`) handles CPUID line index assignment — each CCP is assigned a sequential line index written to `LP_DATA` PMA CR for all LPs in the module
6. **OS** reads CPUID/HFI table and steers threads to cores with non-zero performance values

#### FSM States
- `idle` → waiting for HPM trigger
- `send_p2u_mailbox` → sending table rows via P2U
- `pending_p2u_mailbox` → all writes sent, awaiting P2U completion ACK


### Key Registers & Interfaces

| Register / Interface | Type | Description |
|---------------------|------|-------------|
| HPM `HGS_UPDATE` message | HPM | Root→Leaf trigger for HGS table refresh |
| `COMPUTE0_CORE_SLICE0_CR_LP_DATA` | Sideband CR | Per-LP CPUID line index for HGS table position |
| `MISC_PWR_MGMT2.ENABLE_HWP` | MSR | HGS requires HWP enabled |
| P2U Mailbox (opcode `HGS`) | Mailbox | PCode→Ucode channel for writing HGS table to memory |
| BIOS Mailbox `READ_HGS_CONFIG` / `WRITE_HGS_CONFIG` | Mailbox | BIOS interface for HGS configuration |
| Camarillo Mailbox `HGS_TABLE`, `HGS_CONFIG` | Mailbox | OOB interface — includes `HGS_CLASS`, `HGS_DCC_UPDATE_RATE`, `HGS_REGULAR_UPDATE_RATE` |


### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) | HGS section |
| PCode HGS flow | `source/pcode/flows/hgs.cpp`, `hgs.h` | Core HGS logic, P2U table write |
| PCode HPM msg defs | `source/hpm/hpm_msgs.xml` | `HGS_UPDATE` message definition |
| PCode mailbox | `source/mailbox/mboxgen_camarillo.xml` | `HGS_TABLE`, `HGS_CONFIG` services |
| Primecode HGS flow | `src/flow/hgs/v2_0/hgs.cpp`, `hgs.hpp` | `HgsConfigureTx`, `HgsTableInitTx`, Primecode-side HGS |
| Primecode base IA HGS | `src/ip/core/corecommon/v1_0/base_ia_hgs.cpp`, `base_ia_hgs.hpp` | CPUID line index, LP_DATA writes |
| NWP ZBB evidence | `src/cfgdata/nwp_imh/v1_0/ok_going_zero.txt` | Lines 195–197, 3087, 5948–5949 |


### Related Sightings
<!-- TODO: Add sightings specific to this sub-feature -->
