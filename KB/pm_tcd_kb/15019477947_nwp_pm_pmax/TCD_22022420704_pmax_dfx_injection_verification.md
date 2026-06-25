# TCD: PMAX DFX Injection Verification

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420704](https://hsdes.intel.com/appstore/article-one/#/22022420704) |
| **Title** | PMAX DFX Injection Verification |
| **Parent TPF** | [15019477947](https://hsdes.intel.com/appstore/article-one/#/15019477947) |
| **Feature** | PMAX |
| **NWP Disposition** | Runnable_On_N-1 (Silicon Only TCs) / PSS |
| **KB last updated** | 2026-06-25 |

## Section 1: Architecture / Micro-architecture and Functionality

**PMAX DFX Injection** provides test-controlled PMAX event generation without requiring actual VccIN voltage droop. Three injection mechanisms available:

| Mechanism | Register | Trigger Type | TC |
|-----------|----------|-------------|-----|
| **Software inject** | `io_pmax_config.global_pmax_inject` | Global digital inject; bypasses voltage sensing | 22022421792 |
| **TAP/uCR inject** | `PMAX_DFX_DETECT_INJECT` uCR | Spoof FTPmaxDetect wires (wire 0 / wire 1); 100 ns pulse | 22022421792 |
| **DAC inject** | DAC code (hardware) | Analog VccIN droop simulation; tests real detection path | 22022421794 |

All injection paths verify: `package_therm_status.pmax_log = 1`; `perf_limit_reasons.pmax_bit set`; system stable during event.

NWP: single IMH0; 2 CBBs; `pmax_status6.mt0_cbb_trig_count` increments on each event.

### TC Coverage Map

| TC ID | Title | NWP Disposition |
|-------|-------|----------------|
| [22022421792](https://hsdes.intel.com/appstore/article-one/#/22022421792) | PMAX DFX INJECT Register Verification (TAP) | Runnable_On_N-1 |
| [22022421794](https://hsdes.intel.com/appstore/article-one/#/22022421794) | PMAX Hard Throttle using DAC | Runnable_On_N-1 |
| [16030715666](https://hsdes.intel.com/appstore/article-one/#/16030715666) | [PSS] PLR Status registers Check for PMAX Events | PSS |
| [16030715669](https://hsdes.intel.com/appstore/article-one/#/16030715669) | [PSS] PMAX DFX Injection Throttle | PSS |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| PMAX_DFX_DETECT_INJECT uCR | TAP network | Spoof FTPmaxDetectXXnnnH[0]/[1]; 100 ns pulse |
| global_pmax_inject | sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_inject | Software DFX inject; no hardware VR needed |
| global_pmax_latch_bypass | sv.socket0.imh0.pcodeio_map.io_pmax_config.global_pmax_latch_bypass | Must be 1 for inject to reach Punit |
| pmax_log | sv.socket0.imh0.punit.throttle.package_therm_status.pmax_log | Event log; must set on each inject |
| mt0_cbb_trig_count | sv.socket0.imh0.pmax.pmax0.pmax_status6.mt0_cbb_trig_count | Increments on each PMAX hard throttle event |

---

## Section 3: Reset, Power, and Clocking

- TAP-based inject available independent of boot phase (DFX hook)
- Software inject requires punit_supervises_pmax=1 and global_pmax_latch_bypass=1
- DAC inject requires external DAC hardware; tests real analog detection path
- mt0_cbb_trig_count is sticky; clear via TAP register before test

---

## Section 4: Programming Model

- Software inject: `global_pmax_latch_bypass=1; global_pmax_inject=1` → triggers Punit PMAX event
- TAP inject: write PMAX_DFX_DETECT_INJECT uCR to spoof wire 0 or wire 1 (100 ns pulse)
- DAC inject: set DAC code to exceed Vtrip 0 threshold → real analog droop detection
- All paths: verify `pmax_log=1` during inject; `mt0_cbb_trig_count` increments

---

## Section 5: Operational Behavior

**Software/TAP inject flow:**
1. Configure supervision and bypass
2. Assert inject → Punit sees PMAX event within 1-2 poll cycles
3. pmax_log asserts; PLR bit set; freq throttle to Psafe
4. Clear inject → pmax_log clears; freq recovers

**DAC inject flow:**
1. Set DAC code to droop VccIN below Vtrip 0 threshold
2. Real analog detection path fires; mt0_cbb_trig_count increments
3. Hard throttle applied; system stable
4. Remove DAC code; recovery

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-----------------|
| Wire 0 inject works but wire 1 does not | One fast threshold wire not connected on NWP |
| pmax_log = 0 after inject | global_pmax_latch_bypass not set; or supervision off |
| mt0_cbb_trig_count not incrementing | Counter not cleared before test; or DAC not reaching threshold |
| System hang during DAC inject | Excessive VccIN droop; power delivery issue |

---

## Section 7: Security / Safety / Policy

- DFX inject mechanisms are debug/validation hooks; not available in production silicon
- DAC inject requires controlled power lab environment
- TAP-based inject requires JTAG/DFX access

---

## Section 8: References

- [DMR PMax Detector HAS](https://docs.intel.com/documents/arch_datacenter/pmax/dmr/dmr_pmax_detector_has/dmr_pmax_detector_has.html) — PMAX_DFX_DETECT_INJECT uCR; FTPmaxDetect wires; DAC trigger path
- [DMR PMax HAS](https://docs.intel.com/documents/pm_doc/src/server/dmr/pm_features/dmr_pmax.html) — global_pmax_inject; latch bypass; pmax_status6 counter
