# TPF 16030763140 — [NWP PM] Memory Thermal Management

| Field | Value |
|-------|-------|
| **TPF ID** | [16030763140](https://hsdes.intel.com/appstore/article-one/#/16030763140) |
| **Title** | [NWP PM] Memory Thermal Management |
| **Parent TP** | [16030763137 — NWP PM Thermal Management](https://hsdes.intel.com/appstore/article-one/#/16030763137) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-19 |

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
| CLTT MR4 based | [22022420548](https://hsdes.intel.com/appstore/article-one/#/22022420548) | MR4 temp → MC throttle thresholds → throttle levels | Active (POR) |
| CLTT PECI based | [22022420554](https://hsdes.intel.com/appstore/article-one/#/22022420554) | BMC DIMM temp via PECI → MC throttle | **ZBB_N/A** on NWP LP6 |
| CLTT TSOD based | [22022420563](https://hsdes.intel.com/appstore/article-one/#/22022420563) | TSOD sensor → SPD controller → MC throttle | **ZBB_N/A** on NWP LP6 |
| Memhot | [22022420570](https://hsdes.intel.com/appstore/article-one/#/22022420570) | MEMHOT_OUT assertion on threshold; MEMHOT_IN response | Active |
| Memtrip | [22022420575](https://hsdes.intel.com/appstore/article-one/#/22022420575) | Catastrophic memory temp → MEMTRIP_N → shutdown | Active |

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

| TCD ID | Title | Status | TC Count | Disposition |
|---|---|---|---|---|
| 22022420548 | CLTT MR4 based | Active | 8 | POR |
| 22022420554 | CLTT PECI based | ZBB_N/A | 4 | Not POR on NWP LP6 |
| 22022420563 | CLTT TSOD based | ZBB_N/A | 8 (5 rejected) | Not POR on NWP LP6 |
| 22022420570 | Memhot | Active | 7 | POR |
| 22022420575 | Memtrip | Active | 8 | POR |
