# TCD: CBB CCF Fast Ring C3

| Field | Value |
|-------|-------|
| **TCD ID** | [16031169646](https://hsdes.intel.com/appstore/article-one/#/16031169646) |
| **Title** | CBB CCF Fast Ring C3 |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [22022420507 — CBB CCF Active States](https://hsdes.intel.com/appstore/article-one/#/22022420507) |
| **Feature** | CBB CCF Fast Ring C3 — shallow CCF idle state during PkgC0 |
| **KB last updated** | 2026-07-18 |

## Section 1: Architecture / Micro-architecture and Functionality

**CBB CCF Fast Ring C3** validates the shallow CCF idle power state where the CCF PMA autonomously gates the main global UCLK drivers while retaining Ring PLLs and VCCRING. This state reduces ring power during low-activity periods without PUnit involvement, enabling rapid exit (~100 ns) on wake events. Entry requires all cores idle, SANTA UpstreamEmpty, and voltage at or below FASTC3_VOLTAGE_LIMIT.

> **Architecture overview:** See [TPF 22022420507 — CBB CCF Active States](https://hsdes.intel.com/appstore/article-one/#/22022420507) §2 Design Details for full-stack architecture, GV sequencing, and Fast Ring C3 vs Ring C3 comparison.

### NWP-Specific Deltas

- Fast Ring C3 is **POR on NWP silicon** (unlike full Ring C3 which is HSLE/Simics only due to PkgC6 being fused off)
- 2 CBBs per socket — each CBB independently manages its own Fast C3 state
- NWP D2D PHY upgrade (16→32 GT/s) adds 72-cycle roundtrip latency at 2 GHz — affects wake event delivery timing from Ring C3 exit perspective

### TC Coverage Map

| TC | Scope | Environment |
|----|-------|-------------|
| [22022422865 — CBB CCF Fast Ring C3](https://hsdes.intel.com/appstore/article-one/#/22022422865) | Fast Ring C3 entry/exit, PLL state, CLK gating, core state, D2D state | silicon, virtual_platform |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| FASTC3_VOLTAGE_LIMIT | `base.ccf_pma.ccf_pmc_regs.fastc3_voltage_limit` (addr 0x15A8) | Ratio limit for Fast C3 entry; PCode-programmed |
| fast_c3_en | `base.ccf_pma.ccf_pmc_regs.fast_c3_en` | Feature enable bit (autonomous entry) |
| fast_c3_residency.counter | `base.ccf_pma.ccf_pmc_regs.fast_c3_residency.counter` | HW residency counter — cycles spent in Fast C3 |
| CCF PM FSM (pm_state) | `base.ccf_pma.pm_state` | Current CCF PMA state machine value |
| GlbdrvOff | Internal PMA signal | UCLK global driver gating status |
| UFS_STATUS.CURRENT_RATIO | TPMI cluster 0x00 | Reflects current CCF ring ratio |
| SANTA UpstreamEmpty | Internal PMA signal | Prerequisite for Fast C3 entry |

### Interface Access Matrix

| Interface | MSR | TPMI | CSR | Notes |
|-----------|-----|------|-----|-------|
| FASTC3_VOLTAGE_LIMIT | — | — | RW | PCode programs ratio_limit[10:0]; default 0x7FF |
| fast_c3_residency | — | — | R | HW cycle counter |
| UFS_STATUS | — | R | — | Via `cbb.tpmi.ufs.ufs_status` |
| pm_state | — | — | R | Via PythonSV `base.ccf_pma.pm_state` |

---

## Section 3: Reset, Power, and Clocking

- Ring PLL: **ON** — Fast C3 does not shut down Ring PLLs (key difference from full Ring C3)
- VCCRING: **ON** — power rail retained
- UCLK: **Gated** — main global drivers closed (`GlbdrvOff=1`); all CBOs and part of SBO gated
- Ungated UCLK domains: **SANTA** and part of SBO (including D2D) remain on ungated UCLK for upstream wake logic and inter-die communication
- Warm reset: restores CCF to Active state; Fast C3 state not preserved across reset
- PkgC6 entry: Fast C3 is a **prerequisite** for full Ring C3 — PCode forces Fast C3 entry (bypasses hysteresis) before Ring C3 sequence

---

## Section 4: Programming Model

### Fast C3 Entry Conditions (spec-derived)

1. All cores in **C6 or C1E**
2. **SANTA UpstreamEmpty** indication is true
3. **SB_ALL CLK_REQ** is off — no endpoint requesting SB clock
4. Above conditions hold for configured **hysteresis time**
5. Current voltage ratio **≤ FASTC3_VOLTAGE_LIMIT.ratio_limit**
6. Feature enable: `fast_c3_en == 1` OR `UDI == 0` (PkgC6/reset entry forces Fast C3)

### Fast C3 Entry Actions

1. Block CFI2UFI upstream traffic via Q-channel handshake
2. One-shot CCF drain — CBO trackers must be empty before ack
3. Block CCF PMA RSE pulse and ring scalability messages
4. Gate global drivers: `GlbdrvOff = 1`

### Fast C3 Exit Conditions

- Core exits C6/Cx → asserts **CLK_REQ** toward CCF FIL/CCFPMA
- Upstream traffic arrives from UFI2CFI (`UpstreamEmpty = 0`)
- Voltage ratio rises **above FASTC3_VOLTAGE_LIMIT**
- Dynamic disable: `fast_c3_en == 0 AND UDI == 1`

### Fast C3 Exit Actions

1. `GlbdrvOff = 0` — ungate global drivers
2. Wait deterministic time for clock toggling to resume
3. Unblock CFI2UFI traffic
4. Unblock RSE pulse — pending ring scalability pulse released

### Exit Latency

- Core wake path: ~62 cycles (~77 ns), rounded to **~100 ns at 800 MHz** ring min frequency
- SANTA snoop/upstream wake path: ~57 cycles (~72 ns), rounded to ~100 ns

### Automation

```python
# Fast Ring C3 test (PMX)
ccfu.ccf_fast_ring_c3_test(skt_num, 'cbbs', rtime=100, Log=log, verbose=None)
```

Script: `diamondrapids/pm/Active_PM/CCF_GV/pmx_ccf_cbo.py`
Option: `--test_ccf_fast_ring_c3`

---

## Section 5: Operational Behavior — Pass/Fail Bar

| Scenario | Pass Criteria | Fail Criteria |
|----------|--------------|---------------|
| Fast C3 entry during PkgC0 low-activity | `fast_c3_residency.counter` increments; `pm_state` shows Fast C3; `GlbdrvOff=1` (UCLK gated) | Counter does not increment; pm_state stuck in Active; UCLK not gated |
| Ring PLL state during Fast C3 | Ring PLL **ON** — PLL lock status maintained | Ring PLL off (should only occur in full Ring C3) |
| VCCRING during Fast C3 | VCCRING **ON** — power rail retained | VCCRING gated (premature power-off) |
| D2D link state during Fast C3 | D2D remains in **L0** (or L1 if PkgC6 path); link operational | D2D link down or unexpected state |
| Exit on core wake event | `fast_c3_residency.counter` stops incrementing; `pm_state` leaves Fast C3; `GlbdrvOff=0`; fabric active within ~100 ns | Counter continues incrementing after wake; pm_state stuck in Fast C3 |
| Exit on voltage above FASTC3_VOLTAGE_LIMIT | CCF exits Fast C3 when voltage exceeds ratio_limit | CCF remains in Fast C3 with voltage above limit |
| Ring scalability RSE blocked during Fast C3 | RSE pulse blocked during Fast C3; unblocked on exit; no stale scalability data | RSE fires during Fast C3 (unexpected telemetry) |
| Per-CBB independence | Each CBB enters/exits Fast C3 independently; one CBB in Fast C3 does not force the other | CBBs coupled — one entry forces the other |

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior | Env |
|----------|-------------------|-----|
| Fast C3 entry during active GV transition | PMA completes GV step first, then enters Fast C3; no abort | HSLE=Full, Si=Full |
| Wake event immediately after Fast C3 entry | Exit actions fire; ~100 ns exit latency; no event lost | HSLE=Full, Si=Full |
| Voltage ratio at FASTC3_VOLTAGE_LIMIT boundary | Entry allowed at == limit; exit triggered at > limit | HSLE=Full, Si=Full |
| D2D traffic arrives during Fast C3 | SANTA upstream wake triggers exit; D2D traffic serviced | HSLE=Full, Si=Full |
| All cores in C6 + Fast C3 + wake event | PMA exits Fast C3; ring fabric restores; core exits C6 | HSLE=Full, Si=Full |
| PkgC6 entry forces Fast C3 (UDI=0) | Hysteresis bypassed; immediate Fast C3 entry as Ring C3 prerequisite | HSLE=Full, Simics=Partial |
| fast_c3_en toggled while in Fast C3 | Exit occurs only when UDI=1 (not during PkgC6 hold) | HSLE=Full, Si=Full |
| Ring scalability message pending at Fast C3 entry | RSE pulse blocked; pending pulse drained or held until exit | HSLE=Full, Si=Full |
| Rapid Fast C3 entry/exit toggle (<1 ms) | GVFSM handles fast toggle; no PMA FSM hang | HSLE=Full, Si=Full |

---

## Section 7: Security / Safety / Policy

- Fast C3 transitions require ring 0 access for validation (PythonSV / PMX framework)
- CFI2UFI blocking respects Q-channel protocol — no transaction loss during entry
- CBO trackers must be empty (CCF drain) before Fast C3 acknowledgment — no data corruption risk

---

## Section 8: References

| Type | Reference | Scope |
|------|-----------|-------|
| HAS | [CBB CCF Power Management HAS — Fast Ring C3](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html) | Fast C3 entry/exit flow, FASTC3_VOLTAGE_LIMIT, UCLK gating |
| HAS | [DMR CBB CCF PM HAS v1.0](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.1.0.html) | CCF PMA FSM, Fast C3 state |
| HAS | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) | CBB ring power management, C-state coordination |
| HAS | [DMR Fabric DVFS HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR_PM_Features/DMR_Fabric_DVFS.html) | UFS_CONTROL/STATUS, ring frequency envelope |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM delta |
| KB | KB/pm_features/fabric_dvfs/fabric_dvfs_main.md | ELC Low / perf-idle state and Fast Ring C3 relationship |
| PMX script | `diamondrapids/pm/Active_PM/CCF_GV/pmx_ccf_cbo.py` | `ccf_fast_ring_c3_test` |
| Related TCD | [16031169647 — CBB CCF Ring C3](https://hsdes.intel.com/appstore/article-one/#/16031169647) | Full Ring C3 (deep, PLL off) — Fast C3 is prerequisite |
| Related TCD | [22022421209 — CBB CCF PM x CState](https://hsdes.intel.com/appstore/article-one/#/22022421209) | Idle exit / GV recovery on wake events |
| Parent TPF | [22022420507 — CBB CCF Active States](https://hsdes.intel.com/appstore/article-one/#/22022420507) | TP hierarchy context |
