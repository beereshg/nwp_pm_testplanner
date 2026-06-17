# Power/RAPL > PEM (PnP Excursion Monitor)

> **Status**: Restructured — NWP delta enriched from MCP HAS/MAS query
> **Parent**: [Power / RAPL](power_rapl_main.md)

## Baseline (DMR)

PEM provides configurable power and performance excursion monitors for CSP at-scale manageability. It detects **sustained** core frequency drops below a user-defined threshold (FET) and reports which throttling reason caused the excursion (RAPL, thermal, PROCHOT, PMAX, etc.). PEM filters out transient events using an EWMA algorithm and provides per-event duration counters.

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

**PEM (PnP Excursion Monitor) is supported on NWP** — reused from DMR.

- Energy metering and TPMI telemetry flows are reused
- PEM EWMA-based excursion detection maintained
- TPMI register interface unchanged

### Validation Impact
- Same PEM test cases apply
- Verify PEM telemetry via TPMI on NWP NIO die

## Legacy (Human-Curated Reference)

### Architecture Summary

PEM provides configurable power and performance excursion monitors for CSP at-scale manageability. It detects **sustained** core frequency drops below a user-defined threshold (FET) and reports which throttling reason caused the excursion (RAPL, thermal, PROCHOT, PMAX, etc.). PEM filters out transient events using an EWMA algorithm and provides per-event duration counters.

**Key capability**: Enables OOB/inband detection of sustained performance degradation, differentiation between transient vs. persistent throttling, and per-source attribution (which PL, which interface).

**Scope**: Die-scoped feature — each die has its own PEM instance. No cross-die PEM communication. PEM is a **Pcode** (CBB) feature. Primecode is not directly involved.

**Generations**:
| Gen | Products | PEM_STATUS / PEM_COUNTER bits | Interfaces |
|-----|----------|-------------------------------|------------|
| gen1 | SPR/EMR | 17 events (PBM, PL1/PL2, Thermal, PROCHOT, PMAX) | OOB: PECI PCS. IB: OS2P mailbox |
| gen2 | GNR/SRF | 32 events aligned with fine-grain PLR (per-source PL1/PL2/PPL1/PPL2) | OOB: PCS or TPMI. IB: TPMI + PMT |
| **gen3** | **DMR** | 32 events: adds RACL (bit 22), RAS (bit 30), renames to INBAND/CSR/OOB | **OOB: TPMI only. IB: TPMI + PMT. PCS deprecated** |

### Execution Flow

```
SW (Customer)                                  Pcode (CBB)
     │                                              │
     │  1. Configure FET, Time Window                │
     ├─────────────────────────────────────────────►│
     │  2. Enable PEM (PEM_CONTROL.ENABLE_PEM=1)    │
     ├─────────────────────────────────────────────►│
     │                                              │
     │         ┌─────── PEM Slowloop (~1ms) ────────┤
     │         │ For each event[r]:                  │
     │         │   Check if core freq < FET          │
     │         │   excursion[r] = (throttled below   │
     │         │                   FET by reason r)  │
     │         │   avg_status[r] = EWMA(excursion[r])│
     │         │   if avg_status[r] > 0.9:           │
     │         │     set PEM_STATUS[r] = 1           │
     │         │     increment PEM_COUNTER[r]        │
     │         └────────────────────────────────────┤
     │                                              │
     │  3. Poll PEM_STATUS (periodic)               │
     ├─────────────────────────────────────────────►│
     │◄─────────────────── return PEM_STATUS ────────┤
     │                                              │
     │  4. If non-zero → read PEM_COUNTER[event_id] │
     ├─────────────────────────────────────────────►│
     │◄─────────────────── return counter value ─────┤
     │                                              │
     │  5. Clear PEM_STATUS (W0C: write 0 to clear) │
     ├─────────────────────────────────────────────►│
```

#### EWMA Algorithm

```
If excursion[r] has occurred:
    set_status[r] = 1
Else:
    set_status[r] = 0

avg_set_status[r] = EWMA(set_status[r]) over time window (PEM_TW)

If avg_set_status[r] > PEM_threshold (default 0.9):
    set PEM_STATUS[r] = 1
    increment PEM_COUNTER[r]
```

- EWMA runs **continuously** for each event regardless of PEM_STATUS value — ensures accurate re-detection after SW clears status
- PEM_COUNTER[r] increments **only** while excursion is actively occurring (EWMA above threshold)
- PEM_STATUS[r] remains set until **SW explicitly clears** (W0C semantics) — Pcode does not auto-clear
- TW formula: time window ≈ 2.3 × 2^TW ms. Valid TW: 0-17. Max TW ≈ 302 seconds
- Counter unit: 1ms. Wraparound at ~49 days — SW must handle

#### Event Handling Details

- **PEM_THERMAL**: Pcode checks current thermal/EMTTM status each slowloop. If any core throttled below FET → set excursion, apply EWMA
- **PEM_PBM**: Checks if any core throttled below FET due to Socket RAPL and/or Platform RAPL
- **PEM_EXT_PROCHOT**: Checks if ext_prochot asserted AND any core throttled below FET
- **PEM_PL_INBAND/CSR/OOB**: If throttled below FET due to PBM AND specific interface (TPMI inband / CSR / OOB TPMI) is the most constraining → set corresponding bit
- **PEM_PMAX**: Checks if PMAX asserted AND any core throttled below FET
- **PEM_FAST_RAPL**: Fast RAPL firing causing freq limit below FET
- **PEM_RACL** (gen3 only): RACL condition limiting frequency
- **PEM_RAS** (gen3 only): RAS limit causing frequency reduction

### Key Registers & Interfaces

#### PEM_CONTROL (TPMI index 1)
| Field | Bits | Width | Access | Description | Default |
|-------|------|-------|--------|-------------|---------|
| FET | 7:0 | 8 | RW | Frequency Excursion Threshold (core ratio). Pm ≤ FET ≤ P01 | 0 |
| TW | 14:8 | 7 | RW | Time window: ≈2.3×2^TW ms. Valid 0-17. Max ≈302s | 0 |
| RSVD1 | 23:16 | 8 | RW | Reserved | 0 |
| ENABLE_PEM | 31:31 | 1 | RW | 0=Disable (default), 1=Enable PEM | 0 |
| RSVD2 | 63:32 | 32 | RW | Reserved | 0 |

#### PEM_STATUS — gen3 / DMR (TPMI index 2)
| Bit | Name | Description |
|-----|------|-------------|
| 0 | ANY | Set if excursion occurs due to any reason (logical OR of all other bits) |
| 1-5 | RSVD | Reserved (bits [5:0] owned by Acode — not used by PEM) |
| 6 | FCT | Frequency limited due to FCT |
| 7 | PCS_TRL | OOB TRL override limiting core frequency |
| 8 | MTPMAX | Power exceeds Pmax.app limit |
| 9 | FAST_RAPL | Fast RAPL firing |
| 10 | PKG_PL1_INBAND | Socket RAPL PL1 from OS/SW (TPMI inband) |
| 11 | PKG_PL1_CSR | Socket RAPL PL1 from BIOS (CSR) |
| 12 | PKG_PL1_OOB | Socket RAPL PL1 from OOB SW (TPMI OOB) |
| 13 | PKG_PL2_INBAND | Socket RAPL PL2 from OS/SW |
| 14 | PKG_PL2_CSR | Socket RAPL PL2 from BIOS |
| 15 | PKG_PL2_OOB | Socket RAPL PL2 from OOB SW |
| 16 | PLATFORM_PL1_INBAND | Platform RAPL PL1 from OS/SW |
| 17 | PLATFORM_PL1_CSR | Platform RAPL PL1 from BIOS |
| 18 | PLATFORM_PL1_OOB | Platform RAPL PL1 from OOB SW |
| 19 | PLATFORM_PL2_INBAND | Platform RAPL PL2 from OS/SW |
| 20 | PLATFORM_PL2_CSR | Platform RAPL PL2 from BIOS |
| 21 | PLATFORM_PL2_OOB | Platform RAPL PL2 from OOB SW |
| 22 | **RACL** | RACL condition (gen3 new) |
| 23 | PER_CORE_THERMAL | Core temp exceeds thermal threshold |
| 24 | ICCMAX | DFC/SIMPL frequency capping |
| 25 | XXPROCHOT | Platform prochot input pin |
| 26 | HOT_VR | Platform VR_HOT input pin |
| 27-28 | RSVD | Reserved |
| 29 | PCS_PSTATE | Not Supported on DMR |
| 30 | **RAS** | RAS limit (gen3 new) |
| 31 | RSVD | Reserved |

> All bits are RW0C. PEM_ANY (bit 0) is auto-set by Pcode when any other bit is set, auto-cleared when all other bits are cleared. SW can clear individual bits via RMW (write 0 to clear, write 1 has no effect).

#### PEM_COUNTER (gen3 / DMR)
- 32 counters, one per PEM event ID (1:1 mapping to PEM_STATUS bits)
- 32-bit duration counter per event, unit = 1ms, wraparound at ~49 days
- Exposed via **PMT** (read-only). Each event has a dedicated TPMI register via PMT
- Counter increments only while corresponding excursion is actively occurring

#### PEM_HEADER (TPMI index 0)
| Field | Bits | Description |
|-------|------|-------------|
| INTERFACE_VERSION | 7:0 | PEM version (gen3 = 1) |
| OFFSET_PMT_INFO | 15:8 | Qword offset to PMT Info register (default = 3) |
| RSVD | 63:16 | Reserved |

#### PEM_PMT_INFO (TPMI index 3)
| Field | Bits | Description |
|-------|------|-------------|
| GUID | 31:0 | PMT GUID (0 = invalid entry) |
| SAMPLE_ID | 47:32 | PMT Sample ID |
| SAMPLE_COUNT | 63:48 | Number of PEM counters |

#### DMR Software Interfaces

**Inband (DMR)**:
| Register | Read | Write |
|----------|------|-------|
| PEM_CONTROL | PMT and TPMI | TPMI |
| PEM_STATUS | PMT and TPMI | TPMI |
| PEM_COUNTER | PMT | None (read-only) |

**OOB (DMR)**:
| Register | Read | Write |
|----------|------|-------|
| PEM_CONTROL | PMT and TPMI | TPMI |
| PEM_STATUS | PMT and TPMI | TPMI |
| PEM_COUNTER | PMT | None |

> **DMR delta**: PCS (PECI index 75) is **deprecated** for PEM on DMR. Both IB and OOB use TPMI only. PCS_PSTATE (bit 29) is not supported.

#### Interface Matrix (DMR / gen3)

| Register | MSR | IN_TPMI | OOB_TPMI | CSR | Fuses | MB (Mailbox) |
|----------|-----|---------|----------|-----|-------|--------------|
| PEM_HEADER (idx 0) | — | RO | RO | — | — | — |
| PEM_CONTROL (idx 1) | — | RW | RW | — | — | — |
| PEM_STATUS (idx 2) | — | RW0C | RW0C | — | — | — |
| PEM_PMT_INFO (idx 3) | — | RO (PMT) | RO (PMT) | — | — | — |
| PEM_COUNTER (32 events) | — | RO (PMT) | RO (PMT) | — | — | — |
| FET (freq threshold) | — | via PEM_CONTROL | via PEM_CONTROL | — | — | — |
| TW (time window) | — | via PEM_CONTROL | via PEM_CONTROL | — | — | — |
| ENABLE_PEM | — | via PEM_CONTROL | via PEM_CONTROL | — | — | — |

> **Key**: RW = read-write, RO = read-only, RW0C = read / write-0-to-clear, — = not supported on DMR
>
> - **MSR**: No PEM MSRs exist. PEM has always been a TPMI/PCS feature.
> - **IN_TPMI**: OS/driver reads via TPMI MMIO (TPMI_ID for PEM). PMT provides read-only access to counters. TPMI provides R/W to CONTROL and W0C to STATUS.
> - **OOB_TPMI**: BMC access via TPMI (RdEndpointCfg/WrEndpointCfg). Same registers as inband. PCS_SELECT must be 0 (TPMI mode) — PCS is deprecated on DMR.
> - **CSR**: No CSR interface for PEM.
> - **Fuses**: No PEM-specific fuses. PEM relies on RAPL/thermal fuses indirectly (TDP, thermal thresholds).
> - **MB (Mailbox)**: OS Mailbox (cmd 0xD0) was available on GNR — **deprecated on DMR**. No B2P/U2P/A2P mailbox for PEM.

#### Legacy Interfaces (pre-DMR, for reference)
- **PECI PCS**: Index 75, sub-commands: PEM_CONTROL (0x0), PEM_STATUS (0x1), PEM_COUNTER (0x2)
- **OS Mailbox**: Command 0xD0, sub-commands: PEM_CONTROL (0x40), PEM_STATUS (0x41), PEM_COUNTER (0x42)
- PCS gen2 removes OOB_PEM_ENABLE (bit 30) — interface mutex via TPMI control interface instead

### Input Resolution (DMR)

On DMR, TPMI is the sole interface — no PCS/TPMI conflict resolution needed.

On GNR (gen2), Pcode resolves PCS vs TPMI: last written value is "resolved" value. Pcode updates both interfaces with status but does NOT synchronize inputs between them. BMC should select one interface at boot via [TPMI control interface](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/DVSEC%20MMIO/dvsec_mmio.html#tpmi-control-interface).

### DMR Behavioral Notes (gen3)

- PEM_STATUS is RW0C: SW writes 0 to clear bits; writing 1 is ignored. Pcode caches register value
- If SW clears all bits except ANY → Pcode clears ANY in next slowloop (~1ms)
- SW may miss brief updates between read and write-0 — harmless if limit persists (detected in subsequent slowloops)
- Counters & status registers are **intact over OS patch load** — Pcode does not reset on PEM disable/re-enable
- PEM known limitation: Acode-only events (e.g. Cdyn-driven WP4 clipping) may not trigger PEM. No customer complaints reported; erratum may be published if impact confirmed

### Use Case Examples

#### Fatal Platform Throttling Detection
Set FET = AVX3 P1, TW = 100ms, poll PEM_STATUS every 60 min. If non-zero → read PEM_COUNTER. Calculate K% = PEM_COUNTER / 60 min. Flag error if K > 80%.

#### Workload Frequency Characterization
Set FET = freq_x, TW = 4ms, run workload 1 min. Read PEM_STATUS/COUNTER. Calculate K% = PEM_COUNTER / 1 min. Adjust freq_x until K ≤ 10% → found best-fit FET.

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS | [PEM HAS v1.04 (ITS)](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/PEM/PEM_HAS.html) | Full PEM spec — gen1/2/3, EWMA, mailbox, TPMI, FAQs |
| HAS | [IC PEM HAS v1.00](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/PEM/IC_PEM_HAS.html) | Intel Confidential version (customer-safe) |
| Spreadsheet | [PEM Register Definition](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/PEM/assets/PEM_register_definition.xlsx) | PEM_STATUS/COUNTER/CONTROL source tables |
| Spreadsheet | [PEM VSEC Sheets](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/PEM/assets/PEM_VSEC_sheets.xlsx) | TPMI register layout source |
| Spreadsheet | [PEM PCS Commands](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/PEM/assets/PEM_PCS_commands.xlsx) | Legacy PCS interface (deprecated on DMR) |
| HAS | [CBB Telemetry HAS — PEM Counters](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/CBB_Telemetry/TelemetryAggregator_CBB.html#pem_counter_any) | PEM PMT event definitions |
| HAS | [TPMI HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/DVSEC%20MMIO/dvsec_mmio.html) | TPMI address mapping, PFS, VSEC |
| HAS | [TPMI Control Interface](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/DVSEC%20MMIO/dvsec_mmio.html#tpmi-control-interface) | IB_WRITE_BLOCK, PCS_SELECT |
| FAS | [Pcode PLR FAS](https://sdg74-web.sc.intel.com/pcode/w4/master/perf_limit_reasons.html) | Fine-grain PLR bit definitions (gen2/3 mapping) |
| HAS | [DMR PLR HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PLR.html) | Perf Limit Reasons spec |
| HAS | [GNR PMT HAS](https://docs.intel.com/documents/arch_datacenter/OOBMSM/Gen3/OOBMSM_FW_Gen3_FAS.html#pmt-architecture-for-the-oob-msm) | PMT architecture |
| HAS | [DMR PMT HAS](https://docs.intel.com/documents/arch_datacenter/OOBMSM/Gen4/OOBMSM_FW_Gen4_FAS.html#pmt-telemetry) | DMR PMT telemetry |
| PDF | [PEM HAS rev1.02 PDF](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/PEM/assets/PEM%20HAS%20rev1.02.pdf) | Pre-DMR post-si clarifications snapshot |
| HSD | [22015128052](https://hsdes.intel.com/appstore/article/#/22015128052) | PEM_ANY counter behavior clarification |
| TPMI | [TPMI Infrastructure Reference](../tpmi_infrastructure.md) | Common TPMI VSEC/PFS/LUT discovery |
| KB | [Socket RAPL](socket_rapl.md) | PEM monitors Socket RAPL PL1/PL2 throttling — PID controllers, TPMI registers, HPM messaging |
| HAS | [DMR RAPL Simplification HAS v1.05](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_RAPL_Simplification.html) | Socket/Platform/Fast RAPL — PEM events driven by these controllers |
| HAS | [Socket RAPL HAS (Wave3/GNR)](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html) | Legacy RAPL reference (PID details, throttle below Pm) |
| HAS | [TPMI/DVSEC MMIO HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/DVSEC%20MMIO/dvsec_mmio.html) | TPMI address mapping, PFS, VSEC — PEM registers accessed via TPMI |
| HAS | [TPMI Roles & Responsibilities](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/DVSEC%20MMIO/dvsec_mmio.html#roles-and-responsibilities) | PCS_SELECT, IB/OOB access control for PEM TPMI |
| Primecode src | `src/flow/pem/pem_compute/v1_0/pem_compute.{cpp,hpp}` | PEM compute flow — TPMI mailbox read/write, EWMA config, PCS_SELECT |
| Primecode src | `src/flow/pem/pem_compute/v1_0/pem_pcs_handlers.{cpp,hpp}` | PEM PCS mailbox handlers (legacy, deprecated on DMR) |
| Primecode src | `src/flow/pem/pem_io/v1_0/pem_io.{cpp,hpp}` | PEM IO flow — TPMI reset init |
| Primecode src | `src/cfgdata/dmr_io/v1_0/ip_headers/pm_tpmi_mailbox_rdl.hpp` | TPMI register addresses (PEM_HEADER/CONTROL/STATUS/PMT_INFO offsets) |
| Primecode src | `src/cfgdata/dmr_io/v1_0/ip_headers/punit_MsgCr_p230_GPSB_d.hpp` | PEM GPSB message register definitions |
| Primecode src | `src/doc/pem.dox` | PEM design documentation |
| Primecode test | `tests/flow/pem/pem_io/v1_0/pem_io_mocklib_ut.cpp` | PEM IO flow unit tests |
| Primecode test | `tests/mock_library_cpputest/pem_compute.{cpp,hpp}` | PEM compute mock library |
| PCode src | `source/pcode/flows/slow_limits/pem_telemetry.h` | **Core PEM implementation** — PEM_Telemetry class, EWMA algorithm, PemLimitReasons enum (32 events), counter→telemetry pointer map, slowloop transactions |
| PCode src | `source/pcode/flows/slow_limits/rapl/rapl.h` | RAPL EWMA/excursion detection — PEM consumes RAPL throttle state |
| PCode src | `source/pcode/flows/slow_limits/plr/plr.h` | PLR (Perf Limit Reasons) — shares PEM event bit definitions |
| PCode src | `source/pcode/flows/telemetry.h` | `write_pem_pmt_info()` — PEM PMT telemetry registration |
| PCode src | `source/pcode/kernel/flow_id.h` | PEM flow ID registration |
| PCode src | `source/pcode/kernel/event_id.h` | PEM event ID definitions |
| PCode src | `source/pcode/flows/slow_limits/slow_limits_interface.h` | `CcpSlowLimitsId` — PEM maps slow-limit IDs to PEM reason bits |

### Validation Starting Points (from HAS)

1. Validate all applicable SW read/write interfaces for CONTROL, STATUS, and COUNTERS via TPMI
2. Validate thermally induced throttling below FET is reported in PEM_STATUS and PEM_COUNTER
   - Set FET to various trip points: AVX512 P1, SSE P1, P0n, P01, PN
   - Inject temperature, ext PROCHOT, PMAX to trigger thermal excursion
3. Validate power-limit induced throttling from TPMI inband/OOB/CSR for Socket RAPL PL1/PL2
4. Validate RACL (bit 22) and RAS (bit 30) excursion reporting (gen3 new)
5. Validate PEM_ANY (bit 0) auto-set/auto-clear behavior
6. Validate W0C clear semantics — partial clear, full clear, RMW patterns
7. Validate counter persistence across PEM disable/re-enable and OS patch load

### Related Sightings
<!-- TODO: Add sightings specific to this sub-feature -->

### NWP Delta
<!-- TODO: Describe NWP-specific changes for this sub-feature -->
