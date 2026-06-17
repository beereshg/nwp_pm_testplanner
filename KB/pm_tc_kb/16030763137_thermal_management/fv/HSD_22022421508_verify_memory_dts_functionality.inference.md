# Deep Analysis: [IMH DTS & Telemetry] Verify Memory DTS Functionality

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421508 |
| **Title** | [IMH DTS & Telemetry] Verify Memory DTS Functionality |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | DTS — Memory (DDR PHY) thermal sensors via MC_E & MC_W Resource Controllers |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **Memory DTS** functionality. From test step IP table:

| IP Stack | No. of DTS | IMH RS location | DTS location | Comment |
|----------|-----------|-----------------|--------------|---------|
| Memory | 4 | inside DDR PHY in SOC | one DTS per 2 DDR channels; 3 RS in each DDR channel | |

Flow:
1. Read DTS temperature in Memory IP (DDR PHY)
2. Read temperature in corresponding Resource Controller — **MC_E & MC_W**
3. Read temperature in PUNIT telemetry
4. Compare all — should match

Tags: `DMR_PO`, `NGA_MAIN`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`

NWP has DDR memory channels in iMH die. MC_E and MC_W are the two memory controller RC halves. 4 DTS sensors (1 per 2 DDR channels) = covers all DDR PHY thermal zones.

---

## Section B: NWP-Specific Test Procedure

### Memory DTS Architecture (NWP)

| Parameter | DMR | NWP |
|-----------|-----|-----|
| Memory DTS count | 4 | 4 (verify from NWP HAS — same expected) |
| DTS granularity | 1 per 2 DDR channels | 1 per 2 DDR channels |
| RS per channel | 3 RS per DDR channel | Same expected |
| RCs | MC_E, MC_W | MC_E, MC_W |

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Run dts_telemetry PMx | `python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2` |
| 2 | Read Memory DTS (all 4 instances, per DDR PHY) | `sv.socket0.imh0.<ddr_phy_N>.dts.temperature.read()` |
| 3 | Read MC_E RC temperature | `sv.socket0.imh0.mc_e.<telem_reg>.read()` |
| 4 | Read MC_W RC temperature | `sv.socket0.imh0.mc_w.<telem_reg>.read()` |
| 5 | Read PUNIT telemetry | `sv.socket0.imh0.punit.<mem_telem_reg>.read()` |
| 6 | Compare all — DTS ≈ MC_E/MC_W ≈ PUNIT telem | All 4 DTS checked |
| 7 | Stress memory (bandwidth workload) | Verify DTS and telemetry track under load |

### NWP Notes
- NWP: single `imh0`; MC_E covers east DDR channels; MC_W covers west DDR channels
- 4 Memory DTS total (1 per 2 DDR channels)
- Both MC_E and MC_W RCs must be verified (different DDR channel groups)
- `NGA_MAIN` tag → tested in NGA automation

### Pass Criteria
- All 4 Memory DTS, MC_E RC, MC_W RC, and PUNIT telemetry agree
- Telemetry updates under memory bandwidth stress
- MC_E and MC_W independently report correct temperatures for their channel groups

---

## Section D: Key Registers & Validation Points

```python
# NWP Memory DTS read (example pattern)
for dts_idx in range(4):  # 4 Memory DTS instances
    dts_temp = sv.socket0.imh0.getbypath(f"<ddr_phy_{dts_idx}_dts>").temperature.read()
    print(f"Memory DTS[{dts_idx}] = {dts_temp}")

# MC_E and MC_W telemetry
mc_e_temp = sv.socket0.imh0.mc_e.<telem_reg>.read()
mc_w_temp = sv.socket0.imh0.mc_w.<telem_reg>.read()
punit_mem_temp = sv.socket0.imh0.punit.<mem_telem>.read()
```

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; 4 Memory DTS in imh0; both MC_E and MC_W RC paths**

1. `python runPmx.py -x nwp.xml -p dts_telemetry -tM 60 --retry_count 2`
2. NWP: 4 Memory DTS in `sv.socket0.imh0.*` DDR PHY blocks
3. Verify chain: Memory DTS (×4) → MC_E RC + MC_W RC → PUNIT telemetry
4. Stress test with memory bandwidth workload

**Priority**: High — `plc.feature.p1`, `NGA_MAIN`; Memory DTS is critical for DDR thermal throttling decisions (memory thermal management)
