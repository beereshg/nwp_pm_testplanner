# TCD: MIO Trunk Clock gating Entry / Residency

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421244](https://hsdes.intel.com/appstore/article-one/#/22022421244) |
| **Title** | MIO Trunk Clock gating Entry / Residency |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TP** | [16030762530 — NWP PM Autonomous Idle PM (AIPM)](https://hsdes.intel.com/appstore/article-one/#/16030762530) |
| **KB last updated** | 2026-06-22 |
| **NWP Disposition** | **ZBB — No valid positive-path TCG scenario on NWP** |

## Section 1: Architecture / Micro-architecture and Functionality

### Feature Overview

**MIO Trunk Clock Gating (TCG)** is part of AIPM (Autonomous Idle PM). The Resource Controller
(RC_MIO, one per MIO/IO stack) monitors Q-channel activity from every IP in the stack. When
**both** the late Q-channel and noise Q-channel are simultaneously idle and accepting, the RC
autonomously gates the trunk clock — no OS or firmware intervention required at steady state.
This reduces dynamic power whenever the IO fabric is idle.

**Entry / Residency validation** (this TCD) verifies:
1. The RC correctly detects idle Q-channel conditions and gates the trunk clock (Entry)
2. Perfmon counters accumulate gating residency time (Residency)
3. The trunk un-gates correctly when any Q-channel asserts active

### Why ZBB on NWP — Architectural Chain

> **Source**: Co-Design NWP MAS query (2026-05-31, confirmed by AIPM feature owner)

The RC hardware mechanism **is present** in NWP — the QChannel infrastructure, hysteresis
timer, and RC trunk gate capability exist. However, the runtime entry condition has no valid
trigger:

```
AIPM Trunk Clock Gate condition:
  QActive de-asserted by ALL IPs in stack
        │
        └─ Primary runtime trigger: PCIe/CXL/UXI device enters L1
                    │
                    ├─ PCIe L1 → ZBB on NWP  [HSD 22021155368]
                    ├─ UXI L1/L0p → ZBB on NWP  [HSD 22021155419]
                    └─ HSIO L0p → ZBB on NWP  [HSD 22021155360]
                            │
                            └─ No trigger → RC never sees full-idle QCh
                               Empty stacks → statically disabled at boot
                               (BIOS + PrimeCode CMPL_STATUS=2 path),
                               not runtime AIPM-gated
                               ─────────────────────────────────────────
                               Result: No valid positive-path TCG scenario
```

**NWP spec confirmation (2026-05-31)**: Runtime no-device trunk gating is NOT supported on
NWP. Empty/unconnected stacks are handled exclusively through static stack-disable and
power-gate at boot/reset. The only valid AIPM runtime trigger is L1 entry — which is ZBB on
NWP for both PCIe and UXI.

### TCs Under This TCD

| HSD | Title | Status | Reason |
|-----|-------|--------|--------|
| [22022423027](https://hsdes.intel.com/appstore/article-one/#/22022423027) | IO Trunk Clock gating_Perfmon debug counters - Autonomous Entry | **Rejected — ZBB** | Perfmon counter never increments without TCG entry; no valid entry trigger on NWP |
| [22022423029](https://hsdes.intel.com/appstore/article-one/#/22022423029) | MIO Trunk Clock gating Spurious Wakes | **Rejected — ZBB** | No gated state to generate spurious wake from; TCG never enters |

### Architecture Reference

| Component | Role | NWP Status |
|-----------|------|-----------|
| RC_MIO (per stack) | Monitors late + noise QCh; gates trunk clock autonomously | HW present; no valid trigger |
| Late QCh participants | PCIe RP, CXL, UXI/ULA, HIOP, IOMMU, FBLP | L1 ZBB → QActive always asserted |
| Noise QCh participants | DVP (Debug Trace Packetizer) | Present; RC firmware programs at boot |
| LFCLK PLL RA | Per-stack LFCLK resource; RC reads `CURRENT_CLKI` | Present; programmed at PH6 |
| FIVR (stack FIVR) | Stack power rail; RC programs idle workpoint | Present; idle WP programmed at PH6 |

### Boot-Time Programming (NWP — still executed)

PrimeCode programs RC workpoints at PH6 (post-reset-exit) even on NWP:
- §9.1: `CR_VR_WP_ACTIVE/IDLE`, `CR_CLK_WP_ACTIVE/IDLE`, `QVFS_ENABLE`, `FORCE_ACTIVE_TV_CV_COPY`
- §9.2: PrimeCode skips RA with `CMPL_STATUS=2` for disabled/IP-in-reset stacks
- This boot-time programming IS valid on NWP and covered by separate open TCs

---

## Section 2: Interfaces and Protocols

| Interface | Description | NWP |
|-----------|-------------|-----|
| Late Q-channel | QActive/QAccept signaling from PCIe/CXL/UXI/HIOP/IOMMU | HW present; L1 trigger ZBB |
| Noise Q-channel | QActive/QAccept from DVP (debug trace packetizer) | HW present |
| P-channel | RC → ISA → UXI pstate request (power-gate path) | HW present |
| RC register interface | PrimeCode programs WP/FSM via PUnit MMIO at boot | Active on NWP |

---

## Section 3: Reset, Power, and Clocking

- RC_MIO is reset at warm reset; PrimeCode re-programs workpoints after each reset exit
- Empty stacks: BIOS + PrimeCode applies `CMPL_STATUS=2` → stack powered off statically
- Trunk clock: gated by RC when idle (not functional on NWP at runtime)
- FIVR: idle workpoint programmed at boot even on NWP; never triggered at runtime

---

## Section 4: Programming Model

| Register | Path | Description |
|----------|------|-------------|
| `resctrl_prvt_idle_late_regsN.qch_fsm_policy` | `sv.socket0.imh0.resctrl.rc_mio_ew.*` | QCh FSM autonomous idle enable (bit 0 = `enable_auto_idle`) |
| `resctrl_prvt_idle_noise_regsN.i_qch_ctrl` | RC_MIO MMIO | Noise QCh control; `force_qactive_value/enable` used as PkgC workaround |
| `CR_VR_WP_ACTIVE` / `CR_CLK_WP_ACTIVE` | RC_MIO WP registers | Active workpoint written by PrimeCode at PH6 |
| `CR_VR_WP_IDLE` / `CR_CLK_WP_IDLE` | RC_MIO WP registers | Idle workpoint (never reached at runtime on NWP) |
| `QVFS_ENABLE` | RC_MIO | QVFS autonomous enable; programmed at PH6 |
| `pcode_aipm_mio_trunk_clock_gating_disable` | `sv.sockets.imhs.fuses.punit.*` | Debug fuse override to disable TCG globally |

---

## Section 5: Operational Behavior

**DMR (reference)**: When all late and noise Q-channel IPs assert idle+accept, RC enters
hysteresis timer. After timer expires, RC gates trunk clock. Perfmon counters accumulate
residency. On any QActive assertion, RC un-gates immediately and sends QReq only to the
asserting QCh.

**NWP**: Boot-time RC programming executes identically. Runtime TCG never fires because:
- PCIe/CXL/UXI never enter L1 (L1 ZBB'd)
- Empty stacks are statically power-gated, not AIPM-gated
- Perfmon counters remain at zero for TCG residency

---

## Section 6: Corner Cases & Error Handling

| Scenario | DMR | NWP |
|----------|-----|-----|
| DVP stuck in Q_STOPPED after TCG | Workaround: PkgC6 entry/exit triggers `force_qactive_enable` | **Permanent risk** — PkgC6 also ZBB'd; no recovery path. See [HSD 14026152660](https://hsdes.intel.com/appstore/article-one/#/14026152660) |
| Spurious wakes from gated state | TC 22022423029 | N/A — gated state never reached |
| Warm reset recovery | RC re-programmed by PrimeCode post-reset | Open TC 22022423016 — NWP applicable |
| Stack disable inhibit | PrimeCode must NOT enable AIPM for disabled stacks | Open TC 22022423019 — NWP applicable |

---

## Section 7: Security / Safety / Policy

- `pcode_aipm_mio_trunk_clock_gating_disable` fuse can disable TCG globally (debug/safety override)
- BIOS AIPM knob controls feature enable/disable at platform level
- No security-sensitive registers in TCG path

---

## Section 8: References

- [AIPM KB — aipm.md](../../pm_features/pm_cross_products/aipm.md) — Full AIPM architecture, NWP delta, DVP risk analysis
- [DMR IO Trunk Clock Gating Support HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_IO_trunk_clock_gating_support.html) — Reference implementation (DMR-specific)
- [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — §9.1–9.3 RC boot-time workpoint programming
- [NWP NIO/MIO MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/mio/nwp_nio_mio.html) — NWP MIO clock interfaces and clock-related signals
- [NWP Clock HAS](https://docs.intel.com/documents/custom-xeon/newport-docs/has/rcf/clocks/nwp_clock_has.html) — MIO Links clocking chapter
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html) — NWP feature applicability
- [NWP Validation Domain Expectations](https://wiki.ith.intel.com/spaces/CustomCpuProductDevelopment/pages/4447220900/NWP+Validation+Domain+Expectations) — MIO link states + clock gating validation scope (notes uncertainty for NWP)
- [HIOP Gen4 HAS](https://docs.intel.com/documents/iparch/HIOP/HAS/Gen4/HIOP_GEN4_HAS.html) — HIOP IP dynamic trunk clock gating; quiesce-before-enable requirement
- [HSD 22021155368 — PCIe L1 ZBB on NWP](https://hsdes.intel.com/appstore/article-one/#/22021155368) — Blocks primary TCG trigger
- [HSD 22021155419 — UXI L1/L0p ZBB on NWP](https://hsdes.intel.com/appstore/article-one/#/22021155419) — Blocks secondary TCG trigger
- [HSD 22021155360 — HSIO L0p ZBB on NWP](https://hsdes.intel.com/appstore/article-one/#/22021155360) — Blocks tertiary TCG trigger
- [HSD 14026152660 — DVP stuck Q_STOPPED](https://hsdes.intel.com/appstore/article-one/#/14026152660) — NWP risk: no PkgC6 recovery path
