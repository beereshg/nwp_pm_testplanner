# TPF 16030763140 — [NWP PM] Memory Thermal Management

| Field | Value |
|-------|-------|
| **TPF ID** | [16030763140](https://hsdes.intel.com/appstore/article-one/#/16030763140) |
| **Title** | [NWP PM] Memory Thermal Management |
| **Parent TP** | [16030763137 — NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-20 |

---

## Section 1: Feature Classification & Introduction

**Memory Thermal Management** covers the detection and response to memory-device thermal conditions on NWP, including Closed-Loop Thermal Throttling (CLTT), MEMHOT signaling, and MEMTRIP catastrophic protection. On NWP with **LPDDR6**, only **MR4-based CLTT is POR** — TSOD-based and PECI-based CLTT are not supported (ZBB/N/A).

**Classification:** Silicon-heavy (MC hardware thermal detection) + Firmware (PCode/Primecode throttle policy enforcement). The MC autonomously polls MR4 temperature; firmware evaluates thresholds and enforces throttle levels.

**Gating mechanism:**
- **BIOS knobs:** `thermalthrottlingsupport` = MR4 mode; TSOD/PECI modes disabled
- **MC registers:** `dimm_temp_thresh` (low/mid/high/memtrip/2xrefresh), `dimm_throttle_therm_*_level`
- **MR4 polling:** MC issues in-band MRR to all DRAMs every ~128ms (configurable); max temp per subchannel

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| Memory technology | LPDDR6 (SOCAMM) | NWP SOC |
| CLTT mode (POR) | MR4-based only | NWP IMH MAS; Co-Design confirmation |
| TSOD-based CLTT | Not POR (ZBB) — no TSOD on LP6 | NWP PAS |
| PECI-based CLTT | Not POR (ZBB) — no PECI CLTT on LP6 | Co-Design confirmation |
| MR4 polling interval | ~128ms (configurable) | NWP MC spec |
| Subchannel treatment | Each subchannel = rank for temp polling | NWP LPDDR6 spec |
| IMH count | 1 (imh0 only) | NWP SOC topology |
| MEMHOT_IN response | Memory power reduce within 100 us | NWP GPIO HAS |
| Spec backing | NWP IMH SoC PM MAS: memory thermal; NWP GPIO HAS: MEMHOT/MEMTRIP | Co-Design |

### Feature Scope — Sub-Features

| Sub-Feature | TCD | Description | Status |
|---|---|---|---|
| BIOS Thermal Programming | [22022420548](https://hsdes.intel.com/appstore/article-one/#/22022420548) MTM-ENUM-001 | Threshold/level register defaults; TSOD disabled on LP6 | Active (POR) |
| MR4 Temperature Reporting | [16031179224](https://hsdes.intel.com/appstore/article-one/#/16031179224) MTM-CONTRACT-001 | MR4 temp → MC polling → dimm_mr4_temp registers | Active (POR) |
| Throttle Level Enforcement | [16031179225](https://hsdes.intel.com/appstore/article-one/#/16031179225) MTM-CONTRACT-002 | Zone-based BW throttle enforcement | Active (POR) |
| MEMHOT Pin | [22022420570](https://hsdes.intel.com/appstore/article-one/#/22022420570) MTM-CONTRACT-003 | MEMHOT_OUT assertion / MEMHOT_IN response | Active (POR) |
| MEMTRIP Trigger | [22022420575](https://hsdes.intel.com/appstore/article-one/#/22022420575) MTM-CONTRACT-004 | Catastrophic temp → MEMTRIP_N | Active (POR) |
| Throttle Observability | [16031179227](https://hsdes.intel.com/appstore/article-one/#/16031179227) MTM-OBS-001 | Status registers / TPMI reporting | Active (POR) |
| E2E CLTT Ramp | [16031179228](https://hsdes.intel.com/appstore/article-one/#/16031179228) MTM-SCENARIO-001 | Full poll→threshold→throttle flow | Active (POR) |
| MEMHOT Override | [16031179229](https://hsdes.intel.com/appstore/article-one/#/16031179229) MTM-SCENARIO-002 | MEMHOT_IN overrides CLTT | Active (POR) |
| MEMTRIP Shutdown | [16031179230](https://hsdes.intel.com/appstore/article-one/#/16031179230) MTM-SCENARIO-003 | Trip → Thermtrip → shutdown | Active (POR) |
| MEMHOT+CLTT Interaction | [16031179231](https://hsdes.intel.com/appstore/article-one/#/16031179231) MTM-SCENARIO-004 | MEMHOT_IN during active CLTT | Active (POR) |
| Thermal Cycling Soak | [16031179232](https://hsdes.intel.com/appstore/article-one/#/16031179232) MTM-SOAK-001 | Repeated ramp/cool stress | Active (POR) |
| CLTT PECI based | [22022420554](https://hsdes.intel.com/appstore/article-one/#/22022420554) | BMC DIMM temp via PECI → MC throttle | **ZBB_N/A** on NWP LP6 |
| CLTT TSOD based | [22022420563](https://hsdes.intel.com/appstore/article-one/#/22022420563) | TSOD sensor → SPD controller → MC throttle | **ZBB_N/A** on NWP LP6 |

---

## Section 2: Design Details

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:16px;font-family:Arial,sans-serif;max-width:640px">
  <div style="font-weight:700;font-size:13px;text-align:center;margin-bottom:12px;border-bottom:2px solid #333;padding-bottom:8px">Memory Thermal Management — Full-Stack Architecture (NWP LPDDR6)</div>
  <div style="background:#4472C4;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 5: BIOS / Init</strong> — thermalthrottlingsupport=MR4; threshold/level register programming; disable TSOD polling (PERIODIC_POLL_COMMAND_ENABLE=0)</div>
  <div style="background:#2F5496;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 4: MC MR4 Polling</strong> — In-band MRR to all DRAMs (~128ms); max temp per subchannel; populate dimm_mr4_temp registers</div>
  <div style="background:#ED7D31;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 3: MC Threshold Engine</strong> — Compare dimm_mr4_temp vs dimm_temp_thresh (low/mid/high/crit/memtrip) → select throttle level</div>
  <div style="background:#A020F0;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 2: PCode / Primecode Policy</strong> — Cross-die HPM coordination; MEMHOT_OUT assertion (MH_TEMP_STAT vs DIMM_TEMP_EV_OFST); MEMHOT_IN response</div>
  <div style="background:#70AD47;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center"><strong>Layer 1: GPIO / Platform</strong> — MEMHOT_OUT_N pin; MEMHOT_IN_N pin (100us response); MEMTRIP_N pin (catastrophic)</div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | Notes |
|---|---|---|---|---|---|---|
| Layer 5: BIOS / Init | ✅ | ❌ | ❌ | ✅ | ✅ | VP validates BIOS knob programming |
| Layer 4: MC MR4 Polling | ❌ | ✅ | ✅ | ✅ | indirect | RTL MC polling logic |
| Layer 3: MC Threshold Engine | ❌ | ✅ | ✅ | ✅ | indirect | RTL threshold comparison |
| Layer 2: PCode / Primecode Policy | ✅ | ✅ | ✅ | ✅ | indirect | VP: firmware policy; XOS: cross-die HPM |
| Layer 1: GPIO / Platform | ❌ | ✅ | ✅ | ✅ | ✅ | Pin-level assertion/response |

### MR4-Based CLTT Flow

```
MR4 Polling (MC HW):
  MC → MRR to all DRAMs every ~128ms
  → max temp per subchannel → dimm_mr4_temp[ch][sc]

Threshold Comparison (MC HW):
  dimm_mr4_temp vs:
    dimm_temp_low_maxthreshold  (THRT_MID boundary)
    dimm_temp_mid_maxthreshold  (THRT_HIGH boundary)
    dimm_temp_high_maxthreshold (THRT_CRIT boundary)
    dimm_temp_memtrip_threshold (MEMTRIP trigger)

Throttle Enforcement:
  Below LOW  → No throttle
  LOW..MID   → dimm_throttle_therm_low_level  (THRT_LO)
  MID..HIGH  → dimm_throttle_therm_mid_level  (THRT_MID)
  HIGH..CRIT → dimm_throttle_therm_high_level (THRT_HIGH)
  Above CRIT → dimm_throttle_therm_crit_level (THRT_CRIT)
  Above MEMTRIP → MEMTRIP_N assertion → catastrophic shutdown
```

### Interface & Register Matrix

| Register | Description | Access |
|---|---|---|
| `dimm_mr4_temp[ch][sc]` | MR4 temperature reading per channel/subchannel | MC register |
| `dimm_temp_low/mid/high_maxthreshold` | Throttle threshold boundaries | MC register (BIOS programs) |
| `dimm_temp_memtrip_threshold` | MEMTRIP trigger threshold | MC register (BIOS programs) |
| `dimm_throttle_therm_low/mid/high/crit_level` | Throttle bandwidth reduction per level | MC register (BIOS programs) |
| `MH_TEMP_STAT` | Hottest DIMM temperature (PCode writes) | PCode → MC |
| `DIMM_TEMP_EV_OFST` | MEMHOT_OUT assertion threshold | MC register |
| `PERIODIC_POLL_COMMAND_ENABLE` | Must be 0 for LP6 (disable TSOD polling) | MC register |

---

## Section 3: Validation Strategy

Layer coverage is mapped in §2 — Validation-Tier Layer Claim table.

Key strategy:
- **MR4 polling correctness:** HSLE validates RTL MC polling path; FV validates on silicon
- **Threshold/level enforcement:** HSLE/FV inject MR4 temperature codes, verify correct throttle level applied
- **MEMHOT signaling:** FV validates pin assertion/response timing (100us for MEMHOT_IN)
- **MEMTRIP catastrophic:** FV/HSLE validates trip trigger at threshold; PV validates platform shutdown
- **Cross-die coordination:** XOS required for IMH↔CBB memory thermal HPM

---

## Section 4: Tier Coverage

| TCD | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV |
|---|---|---|---|---|---|
| CLTT MR4 | ✅ | ✅ | ✅ | ✅ | indirect |
| Memhot | ❌ | ✅ | ✅ | ✅ | ✅ |
| Memtrip | ❌ | ✅ | ✅ | ✅ | ✅ |

---

## Section 5: Risks & Dependencies

- **NWP LP6 single CLTT mode:** Only MR4 is POR — no fallback if MR4 polling fails
- **Subchannel-as-rank:** NWP LP6 treats each subchannel as a rank for polling — different from DDR5 DIMM topology
- **MEMHOT_IN 100us latency:** Tight timing requirement for MC response to external throttle request
- **2 TCDs ZBB'd:** TSOD and PECI CLTT are not POR on NWP — validation resources should not be spent on these

### Accepted Coverage Limitations

| Gap | Reason | Spec ref |
|---|---|---|
| TSOD-based CLTT | Not POR for NWP LPDDR6 — no TSOD sensor on SOCAMM | NWP PAS |
| PECI-based CLTT | Not POR for NWP LPDDR6 — PECI CLTT is DDR5/DDR4 only | Co-Design confirmation |

---

## Section 6: DFX Considerations

- MC thermal status registers for MR4 temperature readback
- TPMI for memory thermal status reporting
- PCode debug trace for cross-die HPM memory thermal coordination

---

## Section 7: Common Corner Cases

- MR4 polling timeout — what happens if DRAM doesn't respond to MRR?
- All subchannels at MEMTRIP simultaneously — verify MEMTRIP_N asserted correctly
- MEMHOT_IN during active MR4 throttle — verify lower bound wins
- Threshold boundary edge cases (temp exactly at threshold boundary)
- MEMHOT_OUT + MEMHOT_IN active simultaneously

---

## Section 8: TCD Coverage Summary & References

### Current TCD Structure (Pre-Reorganization)

| TCD ID | Title | Status | TC Count | Disposition |
|---|---|---|---|---|
| 22022420548 | CLTT MR4 based | Active | 8 | POR |
| 22022420554 | CLTT PECI based | ZBB_N/A | 4 | Not POR on NWP LP6 |
| 22022420563 | CLTT TSOD based | ZBB_N/A | 8 (5 rejected) | Not POR on NWP LP6 |
| 22022420570 | Memhot | Active | 7 (1 rejected) | POR |
| 22022420575 | Memtrip | Active | 8 (2 rejected) | POR |

---

### Reorganization: Layered TCD Model (Proposed)

**Feature prefix:** `MTM` (Memory Thermal Management)

**Issues with current structure:**
1. TCDs organized by sub-feature (flat) — mixes CONTRACT and SCENARIO validation layers
2. No ENUM TCD — BIOS programming validation scattered across CLTT MR4
3. No OBS TCD — throttle status observability not separated
4. TC titles use ad-hoc `[MR4]` / `[Memhot]` / `[Memtrip]` tags + `_emulation` suffix for PSS
5. Memtrip TCD has open TCs for non-POR modes (PECI: 22022421439, 22022421441) that should be ZBB'd
6. Duplicate TC: "Memhot_Out mode functionality (copy)" (22022421412) unclear vs 22022421423

---

#### Proposed TCD Structure

| Layer | TCD ID | Title | Invariant | Gate |
|---|---|---|---|---|
| ENUM | [22022420548](https://hsdes.intel.com/appstore/article-one/#/22022420548) | MTM-ENUM-001 - BIOS Thermal Programming Consistency | BIOS threshold/level registers match expected defaults; TSOD polling disabled on LP6 | — |
| CONTRACT | [16031179224](https://hsdes.intel.com/appstore/article-one/#/16031179224) | MTM-CONTRACT-001 - MR4 Temperature Reporting | MC polls all DRAMs via in-band MRR; dimm_mr4_temp populated correctly per subchannel within ~128ms | MTM-ENUM-001 |
| CONTRACT | [16031179225](https://hsdes.intel.com/appstore/article-one/#/16031179225) | MTM-CONTRACT-002 - Throttle Level Enforcement | Correct throttle bandwidth level applied for each temperature zone (low/mid/high/crit) | MTM-CONTRACT-001 |
| CONTRACT | [22022420570](https://hsdes.intel.com/appstore/article-one/#/22022420570) | MTM-CONTRACT-003 - MEMHOT Pin Assertion & Response | MEMHOT_OUT asserts when MH_TEMP_STAT > DIMM_TEMP_EV_OFST; MEMHOT_IN response throttles MC within 100us | MTM-ENUM-001 |
| CONTRACT | [22022420575](https://hsdes.intel.com/appstore/article-one/#/22022420575) | MTM-CONTRACT-004 - MEMTRIP Trigger | MEMTRIP_N asserts when dimm_mr4_temp > dimm_temp_memtrip_threshold; catastrophic shutdown initiated | MTM-CONTRACT-001 |
| OBS | [16031179227](https://hsdes.intel.com/appstore/article-one/#/16031179227) | MTM-OBS-001 - Thermal Throttle Status Observability | MH_TEMP_STAT, throttle level status, TPMI thermal reporting reflect actual thermal state accurately | MTM-CONTRACT-002 |
| SCENARIO | [16031179228](https://hsdes.intel.com/appstore/article-one/#/16031179228) | MTM-SCENARIO-001 - E2E MR4 Thermal Throttle Ramp | Full CLTT flow: temp ramp → threshold crossing → throttle level change → BW reduction observed | MTM-OBS-001 |
| SCENARIO | [16031179229](https://hsdes.intel.com/appstore/article-one/#/16031179229) | MTM-SCENARIO-002 - MEMHOT Overrides CLTT Throttle | MEMHOT_IN active → MC applies MEMHOT policy superseding MR4-based throttle | MTM-CONTRACT-003 |
| SCENARIO | [16031179230](https://hsdes.intel.com/appstore/article-one/#/16031179230) | MTM-SCENARIO-003 - MEMTRIP Catastrophic Shutdown Sequence | Temp above trip threshold → MEMTRIP_N → Thermtrip signal → system shutdown | MTM-CONTRACT-004 |
| SCENARIO | [16031179231](https://hsdes.intel.com/appstore/article-one/#/16031179231) | MTM-SCENARIO-004 - MEMHOT + Active CLTT Interaction | MEMHOT_IN during active MR4 throttle — more aggressive throttle wins | MTM-CONTRACT-003 |
| SOAK | [16031179232](https://hsdes.intel.com/appstore/article-one/#/16031179232) | MTM-SOAK-001 - Thermal Throttle Cycling Stability | Repeated thermal ramp/cool cycles — no stuck throttle, no MCA, no leaked status | all SCENARIO pass |

---

#### TC Remapping (Existing TCs → Proposed TCDs)

| TC ID | Current Title | Current TCD | Target TCD | Proposed Title |
|---|---|---|---|---|
| 22022421317 | [MR4] Verify DIMM Thresholds match with default values programed by BIOS | 22022420548 | MTM-ENUM-001 | MTM-ENUM-001 / FV / threshold-defaults |
| 22022421334 | [MR4] Verify DIMM throttle levels values match with default values | 22022420548 | MTM-ENUM-001 | MTM-ENUM-001 / FV / throttle-level-defaults |
| 16030715643 | [PSS]MemClos Feature Discovery | 22022420548 | MTM-ENUM-001 | MTM-ENUM-001 / PSS / feature-discovery |
| 22022421328 | [MR4] Verify DIMM temp is updated by the MC | 22022420548 | MTM-CONTRACT-001 | MTM-CONTRACT-001 / FV / mr4-temp-update |
| 22022421331 | [MR4] Verify DIMM temp is updated by the MC_emulation | 22022420548 | MTM-CONTRACT-001 | MTM-CONTRACT-001 / PSS / mr4-temp-update |
| 16030715640 | [PSS]Mclos0 Throttling Status | 22022420548 | MTM-OBS-001 | MTM-OBS-001 / PSS / throttle-status |
| 22022421341 | [MR4] Verify end to end Functionality | 22022420548 | MTM-SCENARIO-001 | MTM-SCENARIO-001 / FV / e2e-cltt-ramp |
| 16030715742 | [PSS]MR4-based CLTT | 22022420548 | MTM-SCENARIO-001 | MTM-SCENARIO-001 / PSS / e2e-cltt-ramp |
| 22022421423 | [Memhot] Verify Memhot_Out mode functionality | 22022420570 | MTM-CONTRACT-003 | MTM-CONTRACT-003 / FV / memhot-out-assertion |
| 22022421422 | [Memhot] Verify Memhot_In mode functionality | 22022420570 | MTM-CONTRACT-003 | MTM-CONTRACT-003 / FV / memhot-in-response |
| 22022421412 | [Memhot] MR4 Verify Memhot_Out mode functionality (copy) | 22022420570 | MTM-CONTRACT-003 | ⚠️ DUPLICATE — merge with 22022421423 or reject |
| 22022421411 | [Memhot] MR4 Verify Memhot_In mode functionality | 22022420570 | MTM-CONTRACT-003 | MTM-CONTRACT-003 / FV / memhot-in-mr4-context |
| 22022421415 | [Memhot] Memhot Disables MR4-based | 22022420570 | MTM-SCENARIO-002 | MTM-SCENARIO-002 / FV / memhot-overrides-cltt |
| 22022421419 | [Memhot] Memhot Disables MR4-based_emulation | 22022420570 | MTM-SCENARIO-002 | MTM-SCENARIO-002 / PSS / memhot-overrides-cltt |
| 22022421420 | [Memhot] Memhot Disables TSOD-based | 22022420570 | — | **rejected** (TSOD not POR) |
| 22022421434 | [Memtrip] MR4 based | 22022420575 | MTM-CONTRACT-004 | MTM-CONTRACT-004 / FV / memtrip-mr4-trigger |
| 22022421437 | [Memtrip] Memtrip to Thermtrip | 22022420575 | MTM-SCENARIO-003 | MTM-SCENARIO-003 / FV / memtrip-to-thermtrip |
| 22022421425 | [Memtrip] Disables Memtrip MR4-based | 22022420575 | MTM-SCENARIO-003 | MTM-SCENARIO-003 / FV / memtrip-disable-check |
| 22022421427 | [Memtrip] Disables Memtrip MR4-based_emulation | 22022420575 | MTM-SCENARIO-003 | MTM-SCENARIO-003 / PSS / memtrip-disable-check |
| 22022421439 | [Memtrip] PECI based | 22022420575 | — | ⚠️ ZBB — reject (PECI not POR on LP6) |
| 22022421441 | [Memtrip] PECI based_emulation | 22022420575 | — | ⚠️ ZBB — reject (PECI not POR on LP6) |
| 22022421428 | [Memtrip] Disables Memtrip TSOD-based | 22022420575 | — | **already rejected** |
| 22022421443 | [Memtrip] TSOD based | 22022420575 | — | **already rejected** |

---

#### Coverage Gaps Identified

| Gap | Layer | Description | Action |
|---|---|---|---|
| GAP-1 | CONTRACT | No TC validates throttle level enforcement per-zone (low→mid→high→crit bandwidth reduction) | Create MTM-CONTRACT-002 TCD + TCs |
| GAP-2 | OBS | Only 1 PSS TC for throttle status observability; no FV TC | Add FV TC under MTM-OBS-001 |
| GAP-3 | SCENARIO | MEMHOT_IN during active CLTT (corner case in §7) has no TC | Create MTM-SCENARIO-004 TCs |
| GAP-4 | SCENARIO | MR4 polling timeout (corner case in §7) has no TC | Add negative scenario under MTM-CONTRACT-001 or new TCD |
| GAP-5 | SCENARIO | All subchannels at MEMTRIP simultaneously (corner case §7) — no dedicated TC | Add to MTM-CONTRACT-004 or MTM-SCENARIO-003 |
| GAP-6 | SOAK | No soak/stress TCD for repeated thermal cycling | Create MTM-SOAK-001 |
| GAP-7 | ACTION | Memtrip TCs 22022421439/22022421441 (PECI-based) open but should be rejected | Reject these TCs |
| GAP-8 | ACTION | TC 22022421412 is a duplicate "(copy)" — merge or reject | Reject or merge |

---

#### HSD Actions Required

| # | Action | Target | Details |
|---|---|---|---|
| 1 | Retitle TCD | 22022420548 | → `MTM-ENUM-001 - BIOS Thermal Programming Consistency` |
| 2 | Retitle TCD | 22022420570 | → `MTM-CONTRACT-003 - MEMHOT Pin Assertion & Response` |
| 3 | Retitle TCD | 22022420575 | → `MTM-CONTRACT-004 - MEMTRIP Trigger` |
| 4 | Create TCD | *new* | `MTM-CONTRACT-001 - MR4 Temperature Reporting` under TPF 16030763140 |
| 5 | Create TCD | *new* | `MTM-CONTRACT-002 - Throttle Level Enforcement` under TPF 16030763140 |
| 6 | Create TCD | *new* | `MTM-OBS-001 - Thermal Throttle Status Observability` under TPF 16030763140 |
| 7 | Create TCD | *new* | `MTM-SCENARIO-001 - E2E MR4 Thermal Throttle Ramp` under TPF 16030763140 |
| 8 | Create TCD | *new* | `MTM-SCENARIO-002 - MEMHOT Overrides CLTT Throttle` under TPF 16030763140 |
| 9 | Create TCD | *new* | `MTM-SCENARIO-003 - MEMTRIP Catastrophic Shutdown Sequence` under TPF 16030763140 |
| 10 | Create TCD | *new* | `MTM-SCENARIO-004 - MEMHOT + Active CLTT Interaction` under TPF 16030763140 |
| 11 | Create TCD | *new* | `MTM-SOAK-001 - Thermal Throttle Cycling Stability` under TPF 16030763140 |
| 12 | Reparent TCs | 22022421328, 22022421331 | Move from 22022420548 → MTM-CONTRACT-001 |
| 13 | Reparent TCs | 22022421341, 16030715742 | Move from 22022420548 → MTM-SCENARIO-001 |
| 14 | Reparent TCs | 16030715640 | Move from 22022420548 → MTM-OBS-001 |
| 15 | Reparent TCs | 22022421415, 22022421419 | Move from 22022420570 → MTM-SCENARIO-002 |
| 16 | Reparent TCs | 22022421437, 22022421425, 22022421427 | Move from 22022420575 → MTM-SCENARIO-003 |
| 17 | Reject TCs | 22022421439, 22022421441 | PECI not POR on NWP LP6 |
| 18 | Reject TC | 22022421412 | Duplicate "(copy)" — merge intent into 22022421423 |
| 19 | Retitle all POR TCs | per mapping table above | Apply `{TCD-ID} / {backend} / {variant}` convention |

---

### Microarch→Scenario Coverage Matrix

| # | Element (from §2) | Category | Implied WHAT | Realized as TCD | TC(s) | Tier | Status |
|---|---|---|---|---|---|---|---|
| 1 | MC MR4 in-band MRR polling (~128ms) | Interface | MC polls all DRAMs, populates dimm_mr4_temp per subchannel | MTM-CONTRACT-001 | 22022421328, 22022421331 | FV, PSS | ✓ |
| 2 | dimm_temp_low/mid/high_maxthreshold comparison | FSM | Correct zone selected for given temperature | MTM-CONTRACT-002 | GAP | — | ⚠️ GAP |
| 3 | dimm_throttle_therm_*_level bandwidth reduction | Register | Correct BW reduction applied per zone | MTM-CONTRACT-002 | GAP | — | ⚠️ GAP |
| 4 | MEMHOT_OUT_N pin assertion (MH_TEMP_STAT > DIMM_TEMP_EV_OFST) | Interface | Pin asserts at programmed threshold | MTM-CONTRACT-003 | 22022421423, 22022421412 | FV | ✓ |
| 5 | MEMHOT_IN_N pin response (100us) | Interface | MC reduces memory power within 100us of MEMHOT_IN assertion | MTM-CONTRACT-003 | 22022421422, 22022421411 | FV | ✓ |
| 6 | MEMTRIP_N assertion at memtrip_threshold | Interface | Pin asserts when temp exceeds catastrophic threshold | MTM-CONTRACT-004 | 22022421434 | FV | ✓ |
| 7 | BIOS programming of thresholds/levels | Register | Registers programmed to expected defaults; TSOD disabled | MTM-ENUM-001 | 22022421317, 22022421334 | FV | ✓ |
| 8 | PERIODIC_POLL_COMMAND_ENABLE = 0 (LP6) | Register | TSOD polling disabled on LP6 platform | MTM-ENUM-001 | 16030715643 | PSS | ✓ |
| 9 | MH_TEMP_STAT / throttle status reporting | Counter | Thermal status reflects actual temperature zone | MTM-OBS-001 | 16030715640 | PSS | ⚠️ PARTIAL (no FV) |
| 10 | Full CLTT flow: poll → threshold → throttle → BW | E2E flow | Temperature ramp produces correct throttle response | MTM-SCENARIO-001 | 22022421341, 16030715742 | FV, PSS | ✓ |
| 11 | MEMHOT_IN supersedes MR4 throttle | Cross-path | MEMHOT policy overrides CLTT when active | MTM-SCENARIO-002 | 22022421415, 22022421419 | FV, PSS | ✓ |
| 12 | MEMTRIP → Thermtrip → shutdown | E2E flow | Catastrophic temp triggers system shutdown sequence | MTM-SCENARIO-003 | 22022421437 | FV | ✓ |
| 13 | MEMHOT_IN during active CLTT (lower bound wins) | Cross-path | More aggressive throttle wins when both active | MTM-SCENARIO-004 | GAP | — | ⚠️ GAP |
| 14 | MR4 polling timeout (DRAM non-responsive) | Error condition | MC handles non-responding DRAM gracefully | GAP | GAP | — | ⚠️ GAP |
| 15 | All subchannels at MEMTRIP simultaneously | Corner case | MEMTRIP_N asserted correctly for multi-subchannel event | MTM-CONTRACT-004 | GAP | — | ⚠️ GAP |
| 16 | Repeated thermal ramp/cool cycles (stress) | Soak | No stuck throttle, no MCA, no leaked status | MTM-SOAK-001 | GAP | — | ⚠️ GAP |
| 17 | Threshold boundary (temp exactly at boundary) | Corner case | Deterministic zone assignment at boundary value | MTM-CONTRACT-002 | GAP | — | ⚠️ GAP |

---

### References

- [NWP IMH SoC PM MAS — Memory Thermal section](https://hsdes.intel.com/appstore/article-one/#/16030763137)
- [NWP GPIO HAS — MEMHOT/MEMTRIP pin specification]
- [NWP LPDDR6 Memory Specification — MR4 Temperature Reporting]
- [Co-Design confirmation: TSOD/PECI CLTT not POR on NWP LP6]
