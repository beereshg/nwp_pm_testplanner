# SoC Thermal > Prochot

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing + Baseline topology (2026-05-28)
> **Parent**: [SoC Thermal](soc_thermal_main.md)
> **Source Confidence**: High — enriched from DMR D2D Perimeter HAS, CBB PM HAS, NWP PM MAS, NWP SoC MAS

## Baseline (DMR)

**What it does**: PROCHOT (`XX_PROCHOT_N`) is a package-level GPIO input that signals a platform thermal power-cap; the CPU must reduce power to `PROCHOT_RESPONSE_POWER` within ~250 nS. Input-only since SPR — the CPU never drives PROCHOT outbound.

**Topology**:
```
Platform GPIO ──XX_PROCHOT_N──> IMH0 (Primary PrimeCode)
                                  |── YY_PROCHOT_N (D2D GPIO) ──> IMH1
                                  └── YY_PROCHOT_N (T-connect) ──> CBB0..CBB3
                                                                    Punit HW fast_throttle (~20 nS)
                                                                    PCode IO_FASTPATH_THERMAL
```

**Key operational principle**: CBB Punit fires `fast_throttle` to cores/HQM/CPM immediately (~20 nS, HW only). IMH0 PrimeCode converts `PROCHOT_RESPONSE_POWER` (Watts) → per-CDYN-index frequency ceilings via a fused 6-point P-F profile, then sends HPM `PROCHOT_INST_PWR_CONTROLLED_FREQ_LIMIT` to all leaves. CBB PCode de-asserts fast_throttle once the optimal WP is applied. Post-deassert, PBM budgets scaled >>2 to prevent re-entry power spike.

**Boot activation**: HW fast_throttle path active from power-on. PrimeCode PROCHOT_RESPONSE_POWER translation active from PH2.52 (PCode kernel enabled).

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| GPIO (Platform) | Package pin | Receives platform thermal assertion | `XX_PROCHOT_N` (active low) | [GNR PROCHOT HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/PROCHOT/prochot_top.html) |
| Punit (IMH) | IMH0 (primary) | Aggregates PROCHOT, distributes to secondary IMH + CBBs, converts power→frequency via P-F profile | `PROCHOT_N` out, `YY_PROCHOT_N_TX` D2D, HPM `PROCHOT_FREQ_LIMIT` | [DMR D2D Perimeter](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/D2D/DMR_D2D_Perimeter.html) |
| D2D Stack (UCIe) | IMH↔CBB, IMH↔IMH | Physical transport of PROCHOT_N via async GPIO bumps (low-latency, survives PkgC) | `PROCHOT_N` GPIO bump (IMH→CBB T-connect), `YY_PROCHOT_N_TX/RX` (IMH0→IMH1) | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) |
| Punit (CBB) | CBB0-3 | Receives PROCHOT_N wire → HW fast_throttle (~20ns) to cores, HQM, CPM; PCode applies optimal freq limit | `fast_throttle` out, `IO_FASTPATH_THERMAL`, `IO_THROTTLE_INDICATIONS` | [CBB PM Threat Model](https://docs.intel.com/documents/pm_doc/src/dmr_cbb/has/cbb_pm_threat_model/cbb_power_management_threat_model.html) |
| Core (PantherCove) | CBB | Receives fast_throttle → immediate frequency reduction | `fast_throttle` in | — |
| HQM / CPM | CBB | Throttled via fast_throttle instance 1 | `IO_LOCAL_THROTTLE_MASK` config | — |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| PrimeCode (IMH) | IMH0 + IMH1 | Translates `PROCHOT_RESPONSE_POWER` → per-domain frequency limits; sends HPM to CBBs; clips to [PKG_MIN_POWER, TDP]; scales RAPL PBM budgets post-deassert | HPM `PROCHOT_INST_PWR_CONTROLLED_FREQ_LIMIT`, PBM budget >>2 scaling | HAS |
| PCode (CBB) | CBB0-3 | Receives `IO_FASTPATH_THERMAL` interrupt; reads `IO_THROTTLE_INDICATIONS` to confirm PROCHOT cause; applies core WP from HPM message; de-asserts fast_throttle via `THROTTLE_0_RESET` | `IO_FASTPATH_THERMAL` handler, `IO_THROTTLE_INDICATIONS` R/W | HAS |
| BIOS / UEFI | Platform | Programs `PROCHOT_RESPONSE_POWER` default = current TDP from `SST_PP_INFO` RAPL TPMI register | Boot-time TPMI programming | HAS |
| Acode (Core) | Core | Participates in C-state interaction — PROCHOT does NOT wake from PkgC (cores in C6 cannot throttle further) | — | HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| TPMI | `PROCHOT_RESPONSE_POWER` (MISC_CTRL_BLOCK, Feature ID 0x1, offset 0x06) | RW | Power limit in 0.125W units; [14:0] = power value, [63] = LOCK bit. Range clipped to [PKG_MIN_POWER, TDP] | [DVSEC MMIO HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/DVSEC%20MMIO/dvsec_mmio.html#misc_ctrl) |
| MSR | `IA32_THERM_STATUS` (0x19C) | Core | [2] PROCHOT_STATUS (RO), [3] PROCHOT_LOG (RW sticky) | SDM |
| MSR | `IA32_THERM_INTERRUPT` (0x19B) | Core | [2] PROCHOT_INT_ENABLE — per-core interrupt subscription | SDM |
| MSR | `IA32_PACKAGE_THERM_STATUS` (0x1B1) | Package | [2] PROCHOT_STATUS (RO), [3] PROCHOT_LOG (RW sticky) | SDM |
| MSR | `IA32_PACKAGE_THERM_INTERRUPT` (0x1B2) | Package | [2] PROCHOT_INT_ENABLE — package interrupt enable | SDM |
| MSR | `MSR_POWER_CTL` (0x1FC) | Package | [22] PROCHOT_RESPONSE (legacy, unused since SPR), [23] PROCHOT_LOCK (locks VR_THERM_ALERT_DISABLE) | HAS |
| HPM | `PROCHOT_INST_PWR_CONTROLLED_FREQ_LIMIT` (PM2IP) | Internal | FREQ_CEILING_LIMIT per Cdyn Level 0-4 + Fabric (10-bit ratios) | [HPM Spec](https://docs.intel.com/documents/primecode/has/DMR/Hierarchical%20PM/HPM_Message_Specification.html#PROCHOT_FREQ_LIMIT) |
| PLR | Bit 4 (`PLATFORM`) | Mailbox | Coarse PLR: platform thermal assertion | HAS |
| PLR | Bit 57 (`XXPROCHOT`) | Mailbox | Fine-grain PLR: PROCHOT pin triggered | HAS |
| Fuse | `SOCKET_VIRUS_POWER_FREQUENCY_CURVE_*` | — | 6-point P-F profile (power points × Cdyn indices × fabric) | [Pmax P-F HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PMax.html#fuses) |
| Fuse | `TDP_TO_PSAFE_MULTIPLIER` | — | Psafe = (1 + mult) × TDP. Format U0.7, default 0x33 (0.4) | HAS |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| Platform total reaction time | ~22 | μS | PSU SMBAlert# detect (~20 μS) + FPGA (~2.5 μS) + CPU (~250 nS) | Legacy Architecture Summary |
| CPU reaction budget (GPIO to freq applied) | ~250 | nS | Package pin boundary to frequency reduction; met by HW fast_throttle | Legacy Architecture Summary |
| HW fast_throttle assertion latency | ~20 | nS | CBB Punit HW, no firmware; immediate clock division to cores/HQM/CPM | Legacy Architecture Summary |
| PCode fast_throttle de-assert | ~1 | slow-loop (~1 mS) | After PROCHOT_INST_PWR_CONTROLLED_FREQ_LIMIT HPM applied to cores | Legacy Execution Flow |
| PROCHOT_RESPONSE_POWER resolution | 0.125 | W/LSB | TPMI [14:0]; clipped to [PKG_MIN_POWER, TDP] | Legacy Key Registers |
| Psafe multiplier (TDP_TO_PSAFE_MULTIPLIER) | 0.4 | — | Fuse=0x33 (U0.7); Psafe=(1+0.4)×TDP | Legacy Key Registers |
| PBM budget deration post-deassert | ×0.25 (>>2) | — | PL1 + PL2 budgets; prevents re-entry spike | Legacy Execution Flow |
| P-F profile interpolation points | 6 | — | Fused per die; interpolated at runtime per Cdyn index + fabric | Legacy Execution Flow |

## NWP Delta

**PROCHOT is fully supported on NWP** — confirmed in [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html): "Thermal Protection (including ProcHot, Thermtrip, Memtrip)".

### Topology Changes
- **Single NIO die** replaces dual IMH → no IMH-to-IMH `YY_PROCHOT_N` wire needed
- **2 CBBs** (vs 4) → NIO sends PROCHOT_N to CBB0 and CBB1 only (T-connect topology preserved)
- NIO has 4 D2D stacks (D2D_0..3) connecting to 2 CBBs; no D2D_4/D2D_5 (those were IMH-to-IMH)
- D2D bandwidth doubled to 32 GT/s (symmetric read/write) — no impact on PROCHOT GPIO bump latency

### Functional Changes
- **No cross-die PROCHOT aggregation** — single NIO is sole aggregator
- **No SST-PP cross-product** — SST-PP/BF/CP removed on NWP, so `PROCHOT_RESPONSE_POWER` doesn't interact with SST-PP level switching
- Same PROCHOT_RESPONSE_POWER → frequency conversion via P-F profile
- Same fast_throttle HW path on CBB (~20ns reaction)
- Same PBM budget scaling post-deassert

### Validation Impact
- Simplifies test: only 1 NIO + 2 CBBs to verify (fewer D2D paths)
- No IMH-to-IMH PROCHOT wire test needed
- CBB PM flows fully leveraged from DMR — "no plans to add nor deprecate any CBB PM flow" (NWP PM MAS)

## Legacy (Human-Curated Reference)

### Architecture Summary

PROCHOT (`XX_PROCHOT_N`) is a **package-level GPIO input** pin used by the platform to signal a thermal power-cap condition to the SOC. When asserted, the CPU must reduce power to the `PROCHOT_RESPONSE_POWER` limit.

**Key DMR/GNR characteristics:**
- **Input mode only** (since SPR) — SOC does not assert PROCHOT outbound. Output/bidirectional modes removed.
- Platform uses inbound PROCHOT to indicate power capping due to: VR thermal (PSU redundancy failure), peak power reduction, boot-time power limiting
- Starting GNR: PROCHOT response is **power-domain** (not frequency-domain) — platform programs `PROCHOT_RESPONSE_POWER` in Watts, PCode converts to frequency via fused power-frequency profile
- PkgC × Prochot: PROCHOT does **not** cause a PkgC wake — in PkgC, cores are in C6 and fabric is clock-gated, so throttling cannot help

#### Timing Budget

The total platform PROCHOT reaction time is ~22μS, broken down as:

| Stage | Time | Description |
|-------|------|-------------|
| PSU/CRPS detection | ~20μS | SMBAlert# maximum reaction time |
| FPGA logic | ~2.5μS | Platform FPGA processing |
| **CPU reaction** | **~250nS** | From GPIO pin boundary to frequency reduction applied |

The ~250nS CPU budget is met via the fast-throttle hardware path (HW asserts instantly, PCode follows up with optimal frequency).

#### SOC Connectivity
- Primary IMH receives the GPIO signal and forwards to secondary IMH and leaf CBBs via **die-to-die (D2D) wire** (`YY_PROCHOT_N`)
- Prochot wire path: `gpio_xxprochot_n_rxdata` → `o_punit_interdie_prochot` → D2D → CBB GPIO
- Each die takes action independently — collectively meet platform expectations

### Execution Flow

#### IMH Entry Flow
1. Platform asserts `XX_PROCHOT_N` GPIO
2. Primary IMH receives GPIO signal → ships to secondary IMH and leaf CBBs via D2D wire
3. IMH PrimeCode translates `PROCHOT_RESPONSE_POWER` to frequency limits for:
   - Core (per CDYN index), IO Fabric, Memory Fabric, CBB Fabric
4. PrimeCode clips power value: `PKG_MIN_POWER ≤ PROCHOT_RESPONSE_POWER ≤ TDP`
5. PrimeCode sends HPM `PROCHOT_POWER_LIMITED_FREQ_LIMIT` to secondary IMH and leaf CBBs with ceiling values:
   - `CDYN_INDEX_LIMIT_0..3`, `CBB_FABRIC_LIMIT`, `IMH_MEMORY_FABRIC_LIMIT`, `IMH_IO_FABRIC_LIMIT`
6. Both IMH PrimeCodes reduce their respective fabric frequencies per the Prochot power frequency limit

#### CBB Entry Flow
1. CBB Punit HW asserts **fast_throttle** to cores immediately on seeing D2D Prochot wire — no PCode involvement for initial throttle
2. Fast-throttle throttles: **Cores (BigCore & Atom)**, **HQM**, **CPM** (Punit has 2 fast_throttle outputs: instance 0 → cores, instance 1 → HQM/CPM, configured via `IO_LOCAL_THROTTLE_MASK`)
3. PCode receives fastpath interrupt (`IO_FASTPATH_THERMAL`), reads `IO_THROTTLE_INDICATIONS` to confirm PROCHOT cause
4. CBB PCode reduces core frequencies per `PROCHOT_POWER_LIMITED_FREQ_LIMIT` HPM message
5. CBB PCode de-asserts fast_throttle (via `IO_THROTTLE_INDICATIONS[THROTTLE_0_RESET]=1`) once the Core WP is applied — fast_throttle is sub-optimal for performance, PCode replaces it with optimal frequency limit

#### IMH Exit Flow
1. Platform de-asserts `XX_PROCHOT_N` → primary IMH de-asserts D2D signals
2. Both IMH PrimeCodes remove their fabric frequency ceilings due to Prochot

#### CBB Exit Flow
1. CBB PCode removes core frequency ceiling per `PROCHOT_POWER_LIMITED_FREQ_LIMIT`

#### Rapid GPIO Toggling Scenarios

Platform can toggle `xxPROCHOT_N` faster than PCode can process. The architecture defines expected behavior for each scenario:

| Scenario | Wire State at PCode FP Detection | Expected Behavior |
|----------|----------------------------------|-------------------|
| 1 | Asserted (first assertion) | Apply freq limit → de-assert fast_throttle → enforce limit until de-assert |
| 2 | De-asserted (toggled back before PCode saw it) | De-assert fast_throttle only (RAPL budget reduction optional) |
| 3 | Asserted (re-asserted before PCode processed de-assert) | Apply freq limit → de-assert fast_throttle → enforce until de-assert |
| 4 | De-asserted (normal de-assertion) | Remove freq limit → reduce RAPL budget |
| 5 | Asserted (re-asserted during de-assert processing) | De-assert fast_throttle → enforce freq limit until de-assert |
| 6 | De-asserted (second de-assertion) | Remove freq limit → reduce RAPL budget |

PCode uses `IO_FASTPATH_THERMAL`, `IO_THERMAL_INDICATIONS`, and `IO_THROTTLE_INDICATIONS` to distinguish scenarios. The `IO_THERM_INDICATIONS` prochot wire bit is only set in root PCode.

#### Power-to-Frequency Conversion

Starting GNR, PCode no longer does runtime power-to-frequency calculation. Instead, HVM fuses a **6-point power-frequency profile** per die:

```
Fuses (per die):
  SOCKET_VIRUS_POWER_FREQUENCY_CURVE_POWER_POINT_y              (y=0..5)
  SOCKET_VIRUS_POWER_FREQUENCY_CURVE_IA_CDYN_INDEX_x_FREQUENCY_POINT_y  (x=0..5, y=0..5)
  SOCKET_VIRUS_POWER_FREQUENCY_CURVE_CFC_FREQUENCY_POINT_y      (y=0..5, fabric)
```

PCode interpolates between these 6 points to convert `PROCHOT_RESPONSE_POWER` → frequency ceiling per Cdyn level + fabric. The profile assumes IccMax.Max scenario.

**Psafe**: `Psafe = (1 + TDP_TO_PSAFE_MULTIPLIER) × TDP`. Fuse `TDP_TO_PSAFE_MULTIPLIER` format U0.7, typical value 0.4 (fuse=0x33). Cross-product with SST-PP uses current SST-PP level TDP.

#### PBM Budget Scaling (Post-Prochot)

After PROCHOT de-assertion, PCode scales down RAPL PID budgets to prevent power spike:

```
pl1_pbm_budget = pl1_pbm_budget >> 2    // 4× scale-down (tunable post-si)
pl2_pbm_budget = pl2_pbm_budget >> 2    // 4× scale-down (tunable post-si)
```

This prevents accumulated low-power budget from causing immediate jump to high frequency → another PROCHOT event. Does NOT apply to Psys RAPL budget (no data showing the problem exists for Psys).

The deration only happens in the **root PCode** (iMH) as it runs the RAPL algorithms.

### Key Registers & Interfaces

#### TPMI

| Register | Domain | ID | Bits | Access | Description |
|----------|--------|----|------|--------|-------------|
| `PROCHOT_RESPONSE_POWER` | TPMI MISC_CTRL_BLOCK | 0x06 (Feature ID 0x1) | [14:0] | RW | Power limit (0.125W units). Range: 0 (=default TDP) to 0x7FFF. PCode clips to [PKG_MIN_POWER, TDP] |
| | | | [62:15] | RW | Reserved |
| | | | [63] | RW | LOCK — lock until next reset |

**BIOS behavior**: When customer writes 0 → BIOS reads current TDP from `SST_PP_INFO-1` RAPL TPMI register and programs that as default. After boot, if SW changes `PROCHOT_RESPONSE_POWER`, it is NOT auto-updated on SST-PP level switches — SW responsibility.

#### MSRs

| MSR | Address | Scope | Key Fields | Notes |
|-----|---------|-------|------------|-------|
| `IA32_THERM_STATUS` | 0x19C | Core | `PROCHOT_STATUS[2]` (RO), `PROCHOT_LOG[3]` (RW, sticky) | Set on assertion, SW clears LOG |
| `IA32_THERM_INTERRUPT` | 0x19B | Core | `PROCHOT_INT_ENABLE[2]` | Per-core interrupt subscription |
| `IA32_PACKAGE_THERM_STATUS` | 0x1B1 | Package | `PROCHOT_STATUS[2]` (RO), `PROCHOT_LOG[3]` (RW, sticky) | Package-level equivalent |
| `IA32_PACKAGE_THERM_INTERRUPT` | 0x1B2 | Package | `PROCHOT_INT_ENABLE[2]` | Package interrupt enable |
| `MSR_POWER_CTL` | 0x1FC | Package | `ENABLE_BIDIR_PROCHOT[0]` (legacy, unused), `DIS_PROCHOT_OUT[21]` (legacy, unused), `PROCHOT_RESPONSE[22]`, `PROCHOT_LOCK[23]` | Since SPR, bits 0/21/22 unused. PROCHOT_LOCK also locks `VR_THERM_ALERT_DISABLE` |

> **Note**: `PROCHOT_LOCK` (bit 23) will be renamed to `VR_THERM_ALERT_DISABLE_LOCK` since PROCHOT output is no longer supported.

#### HPM Messages

| Message | Opcode | Direction | Format |
|---------|--------|-----------|--------|
| `PROCHOT_INST_PWR_CONTROLLED_FREQ_LIMIT` | PM2IP | Root → All leaves | `FREQ_CEILING_LIMIT` per Cdyn Level 0-4 + Fabric (10-bit ratios) |

Same HPM message format as PMAX_SOFT/PMAX_HARD/FASTRAPL — only the PM Agent ID subfield differs.

#### PCode IO Registers (Internal)

| IO Register | Purpose |
|-------------|--------|
| `IO_FASTPATH_THERMAL` | Fastpath interrupt from Punit HW on PROCHOT assertion |
| `IO_THERMAL_INDICATIONS` | Live wire state — which feature caused the event |
| `IO_THROTTLE_INDICATIONS` | Live status of PROCHOT/PMAX/FastRAPL wires (bits 4-6). PCode writes `THROTTLE_0_RESET=1` to clear fast_throttle |
| `IO_LOCAL_THROTTLE_MASK` | Configures which IPs fast_throttle affects (instance 0: cores, instance 1: HQM/CPM) |
| `IO_FASTPATH_THERMAL_MASK_CONTROL` | Static config for fastpath generation |

#### Fuses

| Fuse | Default | Description |
|------|---------|-------------|
| `ALLOW_PROCHOT_OUT` | 0 | Legacy — no longer relevant (CPU cannot drive PROCHOT out since SPR) |
| `SOCKET_VIRUS_POWER_FREQUENCY_CURVE_POWER_POINT_y` | — | 6-point P-F profile power points (y=0..5) |
| `SOCKET_VIRUS_POWER_FREQUENCY_CURVE_IA_CDYN_INDEX_x_FREQUENCY_POINT_y` | — | Per-Cdyn-level frequency at each power point (x=0..5, y=0..5) |
| `SOCKET_VIRUS_POWER_FREQUENCY_CURVE_CFC_FREQUENCY_POINT_y` | — | Fabric frequency at each power point (y=0..5) |
| `TDP_TO_PSAFE_MULTIPLIER` | 0x33 (0.4) | Psafe = (1 + mult) × TDP. Format U0.7 |
| `PCU_CR_FIRM_CONFIG[MEMHOT0_TO_PROCHOT_OUT_EN]` | — | MemHot-to-Prochot output mapping (legacy, unused in input-only mode) |

#### PLR Bits

| PLR Bit | Name | Description |
|---------|------|-------------|
| 4 | `PLATFORM` | Coarse PLR: platform thermal assertion |
| 57 | `XXPROCHOT` | Fine-grain PLR: PROCHOT pin triggered |

### Collateral Links
| Type | Link | Notes |
|------|------|-------|
| HAS (GNR PROCHOT) | [GNR PROCHOT HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/PROCHOT/prochot_top.html) | Primary spec — timing, P-F profile, scenarios, BIOS |
| HAS (DMR Thermal) | [DMR SoC Thermal HAS — Prochot](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/Thermals/DMR_Thermal.html#prochot-flow) | DMR-specific Prochot flow section |
| HAS (HPM) | [HPM Spec — PROCHOT_FREQ_LIMIT](https://docs.intel.com/documents/primecode/has/DMR/Hierarchical%20PM/HPM_Message_Specification.html#PROCHOT_FREQ_LIMIT) | HPM message definition |
| HAS (Pmax P-F) | [Pmax HAS — Power-Frequency Profile](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PMax.html#fuses) | Shared P-F fuse table |
| HAS (DVSEC MMIO) | [MISC_CTRL_BLOCK](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/DVSEC%20MMIO/dvsec_mmio.html#misc_ctrl) | TPMI MISC_CTRL_BLOCK for PROCHOT |
| HAS (PM Interrupt) | [PM Interrupt Arch HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/pm_interrupt_arch/pm_interrupt_arch.html) | Multi-die interrupt delivery |
| MRF | [Prochot flow MRF](https://hsdes-pre.intel.com/appstore/spark/mrf?id=1309549959&tenant=server_platf&family=1309245501) | Flow sequence diagram |
| HSD | 22013026933 | GNR PROCHOT feature HSD |
| HSD | 22013116607 | GNR PROCHOT BIOS HSD |
| Related KB | [ACP Thermal](acp.md) | EMTTM context, VR HOT flow |
| NWP PM MAS | [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM feature delta list |
| NWP SoC MAS | [NWP SoC MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/overview/nwp_imh_soc_mas.html) | NWP D2D topology and die construction |

### Test Case Details

**22022421548 — Verify Prochot CBB Entry and Exit Flow**
- Assert PROCHOT GPIO → verify CBB fast_throttle fires immediately → core frequencies drop to PROCHOT limit → de-assert → verify recovery

**22022421553 — Verify Prochot IMH Entry and Exit Flow**
- Assert PROCHOT GPIO → verify D2D wire propagation → IMH fabric frequencies drop per HPM limits → de-assert → verify fabrics recover

**22022421557 — Verify Prochot Response Power**
- Program various `PROCHOT_RESPONSE_POWER` values → assert PROCHOT → verify SOC power stays within programmed limit
- Verify clipping: power value clipped to `[PKG_MIN_POWER, TDP]`

**22021969976 — [PSS] Injected Prochot Entry**
- Inject PROCHOT via platform FPGA signals (`H_CPU0_PROCHOT_LVC1_R_N`) → verify throttle response and fabric frequency reduction

**22022023845 — [PSS] PLR Status Registers Check for Prochot Events**
- Assert PROCHOT → read PLR mailbox → verify `PLATFORM` (bit 4) and `XXPROCHOT` (bit 57) set
- De-assert → verify bits clear
- Priority 2-high: PROCHOT is a critical safety mechanism

### Related Sightings
<!-- TODO: Add sightings specific to this sub-feature -->

### Source Notes
