# TCD: MIO Trunk Clock gating Boot Time Setup

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421240](https://hsdes.intel.com/appstore/article-one/#/22022421240) |
| **Title** | MIO Trunk Clock gating Boot Time Setup |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TP** | [16030762530 — NWP PM AIPM - IO Trunk Clock Gating](https://hsdes.intel.com/appstore/article-one/#/16030762530) |
| **KB last updated** | 2026-06-22 |
| **NWP Disposition** | **Mixed — 3 open (register programming verifiable), 1 rejected (hysteresis timer = hardware default)** |

## Section 1: Architecture / Micro-architecture and Functionality

### Feature Overview

This TCD covers **boot-time RC_MIO programming correctness** — the PrimeCode and PCode
sequences that initialize the Resource Controller workpoints, Q-channel FSM policy, hysteresis
timer, and capability registers at reset exit (PH6). These are NWP-applicable because the RC
hardware is present and PrimeCode programs it regardless of whether runtime TCG entry ever fires.

| HSD | Title | Status | Reason |
|-----|-------|--------|--------|
| [22022422990](https://hsdes.intel.com/appstore/article-one/#/22022422990) | IO Trunk Clock Gating_Late QChannel and Noise QCh enabling | **Open** | PrimeCode explicitly programs `ENABLE_AUTO_IDLE` at PH6 — verifiable |
| [22022422992](https://hsdes.intel.com/appstore/article-one/#/22022422992) | IO Trunk Clock gating_Auto Idle WP checkout | **Open** | PrimeCode explicitly programs `CR_CLK_WP_IDLE/ACTIVE` — verifiable |
| [22022422994](https://hsdes.intel.com/appstore/article-one/#/22022422994) | IO Trunk Clock gating_Hysterisis Timer | **Rejected** | Hardware default — PrimeCode does NOT program this; timer never fires; no verifiable expected value |
| [22022423000](https://hsdes.intel.com/appstore/article-one/#/22022423000) | IO Trunk Clock gating_RC Capability0 reg checkout | **Open** | Hardware discovery register — always meaningful; NUM_QCH_LATE=9, NUM_QCH_NOISE=9, NUM_IDLE_WP=2 |

### Architecture Context

PrimeCode programs RC_MIO workpoints at PH6 (post-reset-exit) per MAS §9.1–9.3:
- `CR_VR_WP_ACTIVE` / `CR_CLK_WP_ACTIVE` — active-state workpoints
- `CR_VR_WP_IDLE` / `CR_CLK_WP_IDLE` — idle workpoints (populated even though never triggered at runtime)
- `QVFS_ENABLE` — Q-channel VFS autonomous enable
- `FORCE_ACTIVE_TV_CV_COPY` — initial TV/CV copy
- Per §9.2: PrimeCode skips RA with `CMPL_STATUS=2` for disabled/IP-in-reset stacks

RC Capability0 register (NWP Gen4 lnpv variant):
- `NUM_IDLE_WORKPOINTS` = 2 (active WP + idle WP)
- `NUM_QCH_LATE` = 9
- `NUM_QCH_NOISE` = 9

### NWP Register Paths

| Register | NWP Path |
|----------|----------|
| RC late QCh FSM policy | `sv.socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regss` |
| RC noise QCh control | `sv.socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_noise_regs0` |
| RC workpoints | `sv.socket0.imh0.resctrl.rc_mio_ew.cr_clk_wp_active` / `cr_clk_wp_idle` |
| RC Capability0 | `sv.socket0.imh0.resctrl.rc_mio_ew.resctrl_prv_capability0` |
| AIPM disable fuse | `sv.sockets.imhs.fuses.punit.pcode_aipm_mio_trunk_clock_gating_disable` |

---

## Section 2: Interfaces and Protocols

PrimeCode communicates with RC_MIO via PUnit MMIO at boot. RC reads LFCLK PLL RA (`CURRENT_CLKI`) and FIVR RA (`CURRENT_VRCI`) to determine initial workpoint values.

---

## Section 3: Reset, Power, and Clocking

All RC workpoints re-initialized after each reset exit (PH6). PrimeCode §9.2 skip logic handles IP-disable stacks (CMPL_STATUS=2). Warm reset and surprise reset TCs (in sibling TCD 22022421242) verify re-initialization correctness.

---

## Section 4: Programming Model

| Register | Expected Value | Source |
|----------|---------------|--------|
| `resctrl_prvt_idle_late_regsN.qch_fsm_policy.enable_auto_idle` | 1 (enabled) | MAS §9.1 |
| `CR_CLK_WP_ACTIVE` | From LFCLK RA `CURRENT_CLKI` | MAS §9.1 |
| `CR_CLK_WP_IDLE` | Idle workpoint from RA | MAS §9.1 |
| `QVFS_ENABLE` | 1 | MAS §9.1 |
| `RC Capability0.NUM_QCH_LATE` | 9 (Gen4 lnpv) | RC TRM HAS |
| `RC Capability0.NUM_QCH_NOISE` | 9 (Gen4 lnpv) | RC TRM HAS |
| `RC Capability0.NUM_IDLE_WORKPOINTS` | 2 | RC TRM HAS |

---

## Section 5: Operational Behavior

PrimeCode reads LFCLK and FIVR RA values, then programs RC workpoints during PH6. If a stack has CMPL_STATUS=2 (IP in reset or disabled), PrimeCode skips that RA and does not enable AIPM for that stack. Boot-time programming is complete and correct on NWP regardless of runtime TCG never firing.

---

## Section 6: Corner Cases & Error Handling

| Scenario | NWP Handling |
|----------|-------------|
| CMPL_STATUS=2 (IP disabled) | PrimeCode skips RA; AIPM not enabled for that stack (§9.2) |
| AIPM fuse disable | `pcode_aipm_mio_trunk_clock_gating_disable` = 1 → RC not programmed for autonomous idle |
| RC capability mismatch | Would indicate wrong RC variant (lnpv vs others); capability0 read validates |

---

## Section 7: Security / Safety / Policy

`pcode_aipm_mio_trunk_clock_gating_disable` fuse disables TCG globally — safety override for bringup.

---

## Section 8: References

- [AIPM KB — aipm.md](../../pm_features/pm_cross_products/aipm.md) — §9.1–9.3 boot programming detail
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — §9.1 RC workpoint programming; §9.2 IP-disable skip
- [RC TRM HAS](https://docs.intel.com/documents/sysip_pm/resource_controller/TRM/TRM.html) — RC Gen4 lnpv capability registers
- [NWP MIO MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/mio/nwp_nio_mio.html) — NWP MIO clock interfaces
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html)
- [DMR IO Trunk Clock Gating HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_IO_trunk_clock_gating_support.html)
