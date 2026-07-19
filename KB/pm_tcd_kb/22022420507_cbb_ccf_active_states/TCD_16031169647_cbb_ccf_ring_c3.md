# TCD: CBB CCF Ring C3

| Field | Value |
|-------|-------|
| **TCD ID** | [16031169647](https://hsdes.intel.com/appstore/article-one/#/16031169647) |
| **Title** | CBB CCF Ring C3 |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [22022420507 — CBB CCF Active States](https://hsdes.intel.com/appstore/article-one/#/22022420507) |
| **Feature** | CBB CCF Ring C3 — deep CCF power-off state during PkgC6 |
| **KB last updated** | 2026-07-18 |

## Section 1: Architecture / Micro-architecture and Functionality

**CBB CCF Ring C3** validates the deep CCF idle power state where Ring PLLs are shut down, UCLK is fully gated, and the D2D UCIe link transitions to L1. This state is entered as part of PkgC6 flow after all cores reach C6 and the CCF fabric is drained. Entry requires Fast C3 as a prerequisite. The CCF PMA executes a save/restore FSM to preserve internal state across the power-off period. On wake, Ring PLLs restart and the fabric is re-initialized.

> **Architecture overview:** See [TPF 22022420507 — CBB CCF Active States](https://hsdes.intel.com/appstore/article-one/#/22022420507) §2 Design Details for full-stack architecture, GV sequencing, and Fast Ring C3 vs Ring C3 comparison.

### NWP-Specific Deltas

- **Ring C3 is ZBB on NWP customer silicon** — PkgC6 is fused off; full Ring C3 entry/exit is testable on **HSLE and Simics only**
- Focus on NWP: validate entry flow, register state, and save/restore FSM correctness in pre-silicon environments
- D2D L1 transition behavior differs from DMR due to NWP D2D PHY upgrade (16→32 GT/s)

### TC Coverage Map

| TC | Scope | Environment |
|----|-------|-------------|
| [22022422873 — CBB CCF Ring C3](https://hsdes.intel.com/appstore/article-one/#/22022422873) | Ring C3 entry/exit, PLL shutdown, VCCRING state, D2D L1, save/restore | HSLE, Simics (rejected on silicon — PkgC6 ZBB) |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| CCF_PMA_COMMAND | `base.ccf_pma.ccf_pmc_regs.ccf_pma_command` (addr 0x1244) | BLOCK_REQ[0] for fabric drain; MONITOR_COPY[1] for debug |
| CCF_WP[0] | `base.ccf_pma.ccf_pmc_regs.ccf_wp[0]` (addr 0x1100) | GV workpoint: TARGET_C_STATE=0x2 (C3), TARGET_MAX_RATIO=0x0 |
| RCSM_PHASE_CONTROL | PUnit → CCF PMA | Phase handshaking for C-state entry/exit |
| RESET_BYPASS_CFG | `base.ccf_pma.ccf_pmc_regs.reset_bypass_cfg` (addr 0x1200) | SKIP_SAVE_RESTORE[2] — debug bypass for S/R FSM |
| Ring PLL status | `base.cbb_pma.ring_pll_status` | PLL on/off state |
| D2D UCIe link state | `base.d2d.ucie_link_state` | L0/L1 state during Ring C3 |
| CCF PM FSM (pm_state) | `base.ccf_pma.pm_state` | Current PMA state machine value |
| S/R SRAM | Internal PMA | Save/restore storage for PMA state across C3 |

### Interface Access Matrix

| Interface | MSR | TPMI | CSR | Notes |
|-----------|-----|------|-----|-------|
| CCF_PMA_COMMAND | — | — | RW | Block/drain control |
| CCF_WP | — | — | RW | Workpoint + C-state target |
| RESET_BYPASS_CFG | — | — | RW | S/R bypass for debug |
| Ring PLL status | — | — | R | PLL lock/off state |
| D2D UCIe state | — | — | R | L0/L1 readback |
| pm_state | — | — | R | PMA FSM state |

---

## Section 3: Reset, Power, and Clocking

- Ring PLLs: **OFF** — shut down during Ring C3 (key difference from Fast Ring C3)
- VCCRING: **ON** — voltage rail retained (spec: VCCRING stays powered during Ring C3)
- UCLK: **Fully gated** — all clock domains stopped
- D2D UCIe: **L1** — link enters low-power state
- On exit: Ring PLL restart → wait for PLL lock → ungate clocks → fabric re-init → D2D L0 restore
- Save/Restore FSM: PMA saves internal state to S/R SRAM on entry; restores on exit (unless `RESET_BYPASS_CFG.SKIP_SAVE_RESTORE` set)
- Warm reset: restores CCF to Active state; Ring C3 state not preserved across reset

---

## Section 4: Programming Model

### Ring C3 Entry Sequence (PkgC6 flow, spec-derived)

1. CCF must already be in **Fast C3** (prerequisite)
2. PUnit writes `CCF_PMA_COMMAND.BLOCK_REQ=1` — blocks new transactions, initiates fabric drain
3. CCF PMA waits for write cache idle; stops periodic status polling
4. PUnit programs `CCF_WP[0]` with:
   - `TARGET_C_STATE = 0x2` (C3)
   - `TARGET_MAX_RATIO = 0x0`
   - `TARGET_VID` = appropriate voltage for C3
5. PUnit writes `RCSM_PHASE_CONTROL` to start C-state entry
6. CCF PMA acknowledges → saves internal state to S/R SRAM
7. Ring PLL shutdown → UCLK fully gated → D2D transitions to L1

### Ring C3 Exit Sequence (Wake event)

1. Wake event arrives (interrupt, traffic, PUnit command)
2. PUnit instructs CCF PMA to exit C3 via `RCSM_PHASE_CONTROL`
3. CCF PMA restores state from S/R SRAM
4. Ring PLL restart → wait for PLL lock
5. UCLK ungated → fabric re-initialized
6. D2D transitions from L1 → L0
7. CCF PMA returns to Active state

### Automation

```python
# Ring C3 test (PMX)
ccfu.ccf_ring_c3_test(skt_num, rtime=100, Log=log, verbose=None)
```

Script: `diamondrapids/pm/Active_PM/CCF_GV/pmx_ccf_cbo.py`
Option: `--test_ccf_ring_c3`

---

## Section 5: Operational Behavior — Pass/Fail Bar

| Scenario | Pass Criteria | Fail Criteria |
|----------|--------------|---------------|
| Ring C3 entry via PkgC6 | `pm_state` shows Ring C3; Ring PLL **OFF**; UCLK fully gated; D2D in **L1** | Ring PLL still on; UCLK not gated; pm_state stuck in Fast C3 or Active |
| VCCRING state during Ring C3 | VCCRING **ON** — rail retained | VCCRING gated (premature power-off causing data loss) |
| Save/Restore FSM on entry | PMA state saved to S/R SRAM; no assertion/error during save | Save FSM hangs; assertion fires; S/R SRAM write fails |
| Ring C3 exit on wake event | PLL restarts and locks; UCLK ungated; fabric re-initialized; D2D returns to L0; `pm_state` leaves Ring C3 | PLL fails to lock; fabric re-init hangs; D2D stuck in L1; pm_state stuck |
| State restore on exit | PMA internal state correctly restored from S/R SRAM — CCF functional post-restore | State corruption; CCF operates incorrectly after restore |
| RESET_BYPASS_CFG.SKIP_SAVE_RESTORE | When set: PCode handles save/restore instead of HW FSM; CCF still exits correctly | Skip flag set but PCode does not take over — state lost |
| Fast C3 prerequisite | Ring C3 entry only proceeds after CCF is in Fast C3 | Ring C3 attempted without Fast C3 — protocol violation |
| CCF_PMA_COMMAND.BLOCK_REQ drain | All outstanding CCF transactions drain before Ring C3 proceeds | Drain incomplete — transactions lost or corrupted |

### NWP Testability Note

Ring C3 is **ZBB on NWP customer silicon** (PkgC6 fused off). Pass/fail validation runs on **HSLE (single-die RTL)** and **Simics (VP)** only. On NWP silicon, only the Fast C3 prerequisite flow and register state observability are exercisable.

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior | Env |
|----------|-------------------|-----|
| Ring C3 entry with pending CCF request | Entry gated until fabric fully drained (BLOCK_REQ drain complete) | HSLE=Full, Simics=Partial |
| Wake event during Ring PLL restart | Queued; serviced after PLL lock achieved | HSLE=Full |
| Ring C3 exit with corrupted S/R SRAM | PMA detects and resets; RESET_BYPASS_CFG.SKIP_SAVE_RESTORE fallback | HSLE=Full |
| D2D L1 transition fails during Ring C3 entry | CCF PMA must handle L1 entry timeout; entry may abort | HSLE=Full |
| D2D L0 restore fails during Ring C3 exit | CCF PMA must handle L0 restore timeout; fabric re-init waits | HSLE=Full |
| PkgC6 ZBB on NWP silicon | Ring C3 deep state not exercised; only entry conditions and register state validated | Si=N/A, HSLE=Full, Simics=Partial |
| SKIP_SAVE_RESTORE + Ring C3 cycle | PCode manually saves/restores PMA state; HW FSM skipped | HSLE=Full |
| Ring C3 → exit → immediate re-entry | PLL must complete full restart before re-shutdown; no shortcut | HSLE=Full |

---

## Section 7: Security / Safety / Policy

- Ring C3 transitions require ring 0 access (PythonSV / PMX framework)
- Fabric drain (CCF_PMA_COMMAND.BLOCK_REQ) ensures no transaction loss — no data corruption risk
- S/R SRAM contents are internal PMA state only — no security-sensitive data exposed
- D2D L1 entry follows UCIe specification for link state negotiation

---

## Section 8: References

| Type | Reference | Scope |
|------|-----------|-------|
| HAS | [CBB CCF Power Management HAS — Ring C3](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.html) | Ring C3 entry/exit flow, PLL shutdown, S/R FSM |
| HAS | [DMR CBB CCF PM HAS v1.0](https://docs.intel.com/documents/pm_doc/src/DMR_CBB/IP%20Integration/CCF/CBB_CCF_PM.1.0.html) | CCF PMA FSM, RCSM phase control |
| HAS | [DMR PkgC Idle Flow HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Idle_Flow/DMR_PkgC.html) | PkgC6 entry/exit — Ring C3 trigger and wake event flow |
| HAS | [DMR CBB PM HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) | CBB ring power management, C-state coordination |
| MAS | [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | NWP PM delta; PkgC6 ZBB status |
| KB | KB/pm_features/core_c_states/pkgc.md | Package C-state coordination, Ring C3 trigger condition |
| KB | KB/pm_features/core_c_states/c6.md | Core C6 entry/exit flow — prerequisite for Ring C3 |
| PMX script | `diamondrapids/pm/Active_PM/CCF_GV/pmx_ccf_cbo.py` | `ccf_ring_c3_test` |
| Related TCD | [16031169646 — CBB CCF Fast Ring C3](https://hsdes.intel.com/appstore/article-one/#/16031169646) | Fast C3 (shallow, PLL on) — prerequisite for Ring C3 |
| Related TCD | [22022421209 — CBB CCF PM x CState](https://hsdes.intel.com/appstore/article-one/#/22022421209) | Idle exit / GV recovery on wake events |
| Parent TPF | [22022420507 — CBB CCF Active States](https://hsdes.intel.com/appstore/article-one/#/22022420507) | TP hierarchy context |
