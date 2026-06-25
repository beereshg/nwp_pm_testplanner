# TCD: [SoC Thermal Management] IMH DTS & Telemetry

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420593](https://hsdes.intel.com/appstore/article-one/#/22022420593) |
| **Title** | [SoC Thermal Management] IMH DTS & Telemetry |
| **Status** | open |
| **Parent TP** | [16030763137 -- NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Feature** | SoC Thermal |
| **Sub-Feature** | DTS — Accelerator IP thermal sensor via CFCIO Resource Controller |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**IMH DTS & Telemetry** covers the thermal sensing topology, sensor validity, and telemetry reporting paths on the NWP NIO/IMH root die. The NIO die is derived from **DMR IMH2**; DMR IMH DTS placement is the correct domain baseline unless NWP-specific deltas override.

Seven distinct IMH/NIO thermal sensing domains are validated by this TCD:

| Domain | DMR Baseline | Notes |
|--------|-------------|-------|
| **Accelerator** | 1 DTS (accelerator misc block) | CFCIO Resource Controller pull path |
| **CGU / AON DTS** | 1 DTS — always-on, no power gating, last in cattrip daisy chain | DTS-AON lives in CGU; special thermtrip anchor |
| **D2D** | 5 DTS (UCIe adaptor) | D2D/UCIe-adjacent sensing |
| **IO Fabric** | DMR baseline; NWP has dedicated I/O Mesh Domain | IO-mesh/fabric sensing |
| **MIO** | 3 DTS (controller misc blocks) | MIO/controller-stack sensing |
| **Memory** | 4 DTS/IMH | NWP adds more MR4-related telemetry pulls |
| **Memory Fabric** | 4 DTS; **CFCMEM Mesh** grew in NWP | Extra DTS/TSRD entries in Newport CFCMEM path |

**Key NWP telemetry changes vs DMR (NWP PM MAS):**
- DTS temperature telemetry pulled via **PMSB** by **`RC_MIO_EW`** (primary) and **`RC_CFCMEM_EW`** (additional entries)
- Total DTS/TSRD entry count increased; RC telemetry indexing must account for NWP-specific allocations
- NIO PM telemetry updated for Newport: more MR4 pulls; CFCIO Mesh and CFCMEM Mesh expanded

### Block Diagram

```
  NWP NIO / IMH Root Die — DTS Sources
  +----------+----------+----------+----------+----------+----------+----------+
  | Accel    | CGU/AON  | D2D      | IO       | MIO      | Memory   | Memory   |
  | DTS      | DTS      | DTS      | Fabric   | DTS      | DTS      | Fabric   |
  | (1 DTS)  | (always- | (5 DTS,  | DTS      | (3 DTS,  | (4 DTS/  | DTS      |
  | CFCIO RC | on; last | UCIe     | (IO Mesh)| ctrl     | IMH)     | (CFCMEM  |
  |          | cattrip) | adaptor) |          | misc)    |          | Mesh)    |
  +----------+----------+----------+----------+----------+----------+----------+
         |
  IMH DTS Aggregation / Thermal Puller
  RC_MIO_EW (PMSB pull, primary)
  RC_CFCMEM_EW (PMSB pull, additional DTS/TSRD entries)
         |
         v
  PCode / Primecode Telemetry Consumer
  (thermal reporting, policy inputs, thermtrip chain)
         |
         v
  TPMI / MSR / PMSB (software-visible telemetry)
  + CBB0 / CBB1 root/cross-die reporting context
```

### Per-TC Domain Mapping

| TC | Domain | Key DTS facts |
|----|--------|---------------|
| 22022421487 | Accelerator | 1 DTS; accelerator misc block; CFCIO RC pull path |
| 22022421498 | CGU / AON | Always-on; no power gating; last in cattrip daisy chain |
| 22022421501 | D2D | 5 DTS; inside UCIe adaptor |
| 22022421504 | IO Fabric | IO Mesh domain; NWP dedicated I/O fabric path |
| 22022421506 | MIO | 3 DTS; controller misc blocks |
| 22022421508 | Memory | 4 DTS/IMH; NWP adds more MR4 telemetry pulls |
| 22022421515 | Memory Fabric | 4 DTS; CFCMEM Mesh expanded; extra DTS/TSRD entries |

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421487](https://hsdes.intel.com/appstore/article-one/#/22022421487) | [IMH DTS & Telemetry] Verify Accelerator DTS Functionality | Runnable_On_N-1 |
| [22022421498](https://hsdes.intel.com/appstore/article-one/#/22022421498) | [IMH DTS & Telemetry] Verify CGU DTS Functionality | Runnable_On_N-1 |
| [22022421501](https://hsdes.intel.com/appstore/article-one/#/22022421501) | [IMH DTS & Telemetry] Verify D2D DTS Functionality | Runnable_On_N-1 |
| [22022421504](https://hsdes.intel.com/appstore/article-one/#/22022421504) | [IMH DTS & Telemetry] Verify IO Fabric DTS Functionality | Runnable_On_N-1 |
| [22022421506](https://hsdes.intel.com/appstore/article-one/#/22022421506) | [IMH DTS & Telemetry] Verify MIO DTS Functionality | Runnable_On_N-1 |
| [22022421508](https://hsdes.intel.com/appstore/article-one/#/22022421508) | [IMH DTS & Telemetry] Verify Memory DTS Functionality | Runnable_On_N-1 |
| [22022421515](https://hsdes.intel.com/appstore/article-one/#/22022421515) | [IMH DTS & Telemetry] Verify Memory Fabric DTS Functionality | Runnable_On_N-1 |

---

## Section 2: Interfaces and Protocols

| Interface | Path | Purpose |
|-----------|------|---------|
| **Domain DTS instances** | Per-domain (Accel/CGU/D2D/IO Fabric/MIO/Memory/Mem Fabric) | Per-domain temperature sensing; up to 6 diodes per DTS |
| **CGU / AON DTS** | CGU — always-on, no power gating | Thermtrip chain anchor; special availability across power states |
| **`RC_MIO_EW` PMSB pull** | Resource Controller via PMSB | Primary DTS telemetry collection path for IMH/NIO domains |
| **`RC_CFCMEM_EW` PMSB pull** | Resource Controller via PMSB | Additional DTS/TSRD entries for Memory Fabric / CFCMEM Mesh |
| TPMI | `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.*` | Software-visible thermal status and telemetry |
| PMSB | `sv.socket0.imh0.compute*.pma*.gpsb` | PM telemetry bus — carries DTS pull traffic |
| **MR4 telemetry** | Memory subsystem RC paths | NWP-increased MR4 temperature pull entries |

---

## Section 3: Reset, Power, and Clocking

- **CGU / AON DTS** is always available — no power gating, no diode toggling, single diode; thermtrip chain terminates here; remains functional independent of ordinary FIVR/domain power state
- Non-AON DTS instances (D2D, MIO, Memory, Memory Fabric, IO Fabric, Accelerator) depend on their respective power/clock domain initialization and RC telemetry framework bring-up
- DTS telemetry validity depends on PMSB RC telemetry initialization; `RC_MIO_EW` and `RC_CFCMEM_EW` must be active before DTS readings are valid
- NWP DTS/TSRD entry count is larger than DMR; test expectations must account for NWP-specific RC index allocations
- Warm reset preserves DTS configuration; cold reset re-initializes RC telemetry state and DTS operating modes

---

## Section 4: Programming Model

IMH DTS/telemetry programming focuses on RC telemetry pull configuration and domain-to-DTS index mapping:

- **DTS placement** (DMR baseline + NWP deltas): Accelerator (1), CGU/AON (1), D2D (5 — UCIe adaptor), IO Fabric (IO Mesh domain), MIO (3 — controller misc), Memory (4/IMH), Memory Fabric (4 — CFCMEM Mesh)
- **`RC_MIO_EW`** — primary PMSB telemetry puller for DTS; collects per-diode/per-domain temperature readings
- **`RC_CFCMEM_EW`** — secondary puller; additional DTS/TSRD entries for NWP-expanded Memory Fabric / CFCMEM Mesh
- **MR4 pulls** — NWP PM telemetry adds more memory-subsystem MR4 temperature pull entries vs DMR
- **CFCIO Mesh / CFCMEM Mesh** — both expanded in NWP; RC index allocations updated accordingly
- DTS fuse/config (diode enable, sleep mode) follows domain-specific programming; BIOS/Primecode initialize during early boot
- OS reads IMH thermal telemetry read-only via TPMI and PMSB surfaces

---

## Section 5: Operational Behavior

This TCD validates **per-domain DTS presence, valid telemetry reporting, correct RC pull path, and AON vs non-AON behavior** — not active throttling.

1. Each domain DTS samples temperature from local/remote diodes per configured mode
2. Temperature readings collected via PMSB pull by `RC_MIO_EW` (primary) and `RC_CFCMEM_EW` (Memory Fabric additional entries)
3. pCode / Primecode thermal consumers aggregate reported values for:
   - thermal status and reporting
   - thermal policy inputs
   - thermtrip chain participation (CGU/AON DTS as final anchor)
4. Software-visible thermal state available via TPMI / PMSB surfaces
5. Validation focuses on: sensor presence, temperature reading validity, correct domain-to-RC-index mapping, NWP-updated entry counts

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| DTS read before RC/PMSB telemetry initialized | Telemetry unavailable or invalid; must not be consumed as valid thermal state |
| CGU/AON DTS active while other domains power-gated | AON path remains functional; thermtrip chain anchor still valid |
| NWP RC index mapping differs from DMR assumptions | Validation must use NWP-specific RC index allocations; DMR offsets may be wrong |
| D2D/UCIe hotspot vs Memory Fabric hotspot | Correct domain-specific DTS/RC path reports each independently |
| CFCMEM Mesh expanded DTS entries not properly indexed | Memory Fabric telemetry gap; `RC_CFCMEM_EW` must cover new NWP entries |
| MR4 pull entries increased vs DMR | Memory DTS coverage must account for NWP-increased MR4 telemetry slots |
| Cross-domain simultaneous hotspots | Each domain's telemetry should remain distinguishable through its RC collection path |

---

## Section 7: Security / Safety / Policy

- DTS telemetry visibility is privileged PM/debug information
- Validation that injects or overrides DTS/RC telemetry values requires controlled test access
- Because CGU/AON DTS also feeds the thermtrip protection chain, test injection near that path must avoid unintentionally triggering catastrophic HWRS shutdown behavior
- NWP RC index changes vs DMR must be validated against NWP-specific documentation, not assumed from DMR alone

---

## Section 8: References

- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP NIO DTS/AON/thermtrip; RC_MIO_EW + RC_CFCMEM_EW PMSB pull; NWP DTS/TSRD entry count increase; MR4 pull additions
- [NWP IMH SCF MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/scf/nwp_imh_scf_mas.html) -- NIO root-die context; CFCIO Mesh / CFCMEM Mesh topology
- [DMR Thermal HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/thermals/dmr_thermal.html) -- DMR IMH DTS placement (Accel/CGU/D2D/IO Fabric/MIO/Memory/Mem Fabric); domain DTS counts
- [NWP DFT MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/dft/nwp_dft_mas.html) -- NIO die context and thermal DTS placement validation reference
- [NWP PM MAS -- Telemetry](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NIO PM telemetry updates; RC index changes; DTS/remote-diode placement note
