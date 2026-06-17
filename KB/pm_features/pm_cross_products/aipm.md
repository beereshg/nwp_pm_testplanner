# PM Cross Products > Autonomous Idle PM (AIPM)

> **Status**: Enriched — HW/FW/OS touchpoints + KPI & Timing + Baseline topology + NWP scoping + PkgC6/L1 combined impact analysis + TPF TC review + AIPM/PkgC6 independence clarification (2026-06-01)
> **Expert**: Hector (AIPM feature owner — open question on DVP/TCG mitigation, see [Open Questions](#open-questions))
> **Parent**: [PM Cross Products](pm_cross_products_main.md)
> **TP Feature HSD**: [22022562533](https://hsdes.intel.com/appstore/article-one/#/22022562533)

## Baseline (DMR)

**AIPM (Autonomous Idle PM)** enables hardware-driven low-power state entry for the I/O fabric (MIO stacks) and memory controllers when idle, without OS involvement. The Resource Controller (RC) monitors Q-channel activity from each IP in a stack; when both late and noise Q-channels are idle and accepting, the RC gates the trunk clock autonomously — no OS or firmware intervention required at steady state.

**Topology (DMR reference):**
```
  PrimeCode (IMH Punit)
       │  boot-time RC programming (§9.1 WP, QVFS_ENABLE, FORCE_ACTIVE_TV_CV_COPY)
       ▼
  RC_MIO (per IMH, per MIO stack)   ← lnpv Gen4 variant
  ├── Late QCh: LFCLK domain IPs (HIOP, IOMMU, PCIe, CXL, UXI/ULA, FBLP …)
  ├── Noise QCh: DVP IPs (debug trace packetizers)
  └── P-channel → ISA → UXI/ULA pstate
       │
       ▼  trunk clock gate (autonomous, when both QCh idle+accept)
  FIVR (stack FIVR — may power-gate if FIVR not shared)
```

**Key operational principle**: RC AIPM gates the trunk clock if both late and noise Q-channels are simultaneously idle. On any QActive assertion (e.g., NSIP2APB sideband access), the RC un-gates and sends QReq only to the QCh that asserted — other QCh (e.g., DVP) remain in Q_STOPPED until independently trigged. This behavior created the DVP/TCG incompatibility sighting on DMR (see [Risk: TCG/DVP Interaction](#risk-tcgdvp-interaction-dmr-sighting-14026152660) below).

**Boot activation**: PrimeCode programs RC workpoints during boot (PH6 / post-reset-exit):
- §9.1: `CURRENT_VRCI`/`CURRENT_CLKI` read from RA; `CR_VR_WP_ACTIVE`, `CR_CLK_WP_ACTIVE`, `FORCE_ACTIVE_TV_CV_COPY`, `QVFS_ENABLE` written
- §9.2: PrimeCode skips RA with `CMPL_STATUS=2` (IP held in reset / IP-disable path)
- §9.3: UFS survivability — mesh/CAB at lower frequency for A0 bring-up (Intel internal)

## HW Touchpoints

| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| RC_MIO (per stack) | IMH/NIO | Monitors late + noise QCh; gates trunk clock autonomously; programs FIVR idle workpoints | `resctrl_prvt_idle_late_regsN.qch_fsm_policy`; `resctrl_prvt_idle_noise_regsN.i_qch_ctrl`; `CR_VR_WP_ACTIVE/IDLE`; `CR_CLK_WP_ACTIVE/IDLE`; `QVFS_ENABLE` | [RC TRM HAS](https://docs.intel.com/documents/sysip_pm/resource_controller/TRM/TRM.html); MAS §6, §9 |
| LFCLK PLL RA (per stack) | IMH/NIO | PMSB RA for per-stack LFCLK PLL resource; RC reads `CURRENT_CLKI` from here | `CURRENT_CLKI`; `CMPL_STATUS` | PMSB RA spec |
| FIVR (per MIO stack) | IMH/NIO | Stack power rail; RC programs idle workpoint or power-gates if FIVR not shared | `CURRENT_VRCI`; `CMPL_STATUS`; VR workpoint registers | FIVR HAS |
| DVP (Debug Trace Packetizer) | IMH/NIO | Noise QCh participant; when in Q_STOPPED, **cannot** self-assert QActive — must receive QReq from RC | `dvp_status.qsmstatus` (0=Q_STOPPED); `dvp_status.qactivestatus`; `force_qactive_enable` RC override | DVP spec; [HSD 14026152660](https://hsdes.intel.com/appstore/article/#/14026152660) |
| ISA (IP State Aggregator) | Per MIO stack | Drives `o_safemode` per IP for clock-gate wake; aggregates UXI/ULA pstate requests | `o_safemode` per IP | MIO HAS |
| PCIe RP / CXL / UXI | Per stack | Late QCh participants; assert QActive when link not in L1/L0p/idle | Q-channel signals per IP | PCIe/CXL/UXI HAS |

## FW Touchpoints

| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| PrimeCode (NIO Punit) | NIO (IMH on DMR) | Boot-time RC WP programming (§9.1–9.3); IP-disable skip logic (`CMPL_STATUS=2`); UFS survivability freq programming; PkgC entry/exit DVP Qactive override management | `rc_mio_boot_wp_program()`; `aipm_mio_trunk_clock_gating_disable` fuse check; `force_qactive_enable` toggle on PkgC entry/exit | PrimeCode `src/flow/aipm/` or `src/flow/pkgc/`; [HSD 14025929892](https://hsdes.intel.com/appstore/article-one/#/14025929892) |
| PCode (CBB) | CBB Punit | Coordinates PkgC entry/exit events; signals PrimeCode to assert/clear `force_qactive_enable` for DVP QCh during PkgC transitions | PkgC handshake; HPM messages | PCode CBB flows |
| BIOS | Platform init | Sets `QVFS_ENABLE` boot policy; enables/disables AIPM features via BIOS knob | BIOS AIPM knobs | NWP BIOS HAS |

## OS Interfaces

| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| `pcode_aipm_mio_trunk_clock_gating_disable` | Fuse / pcode fuse override | RW (pysv) | Disables MIO trunk clock gating globally; debug override | `sv.sockets.imhs.fuses.punit.pcode_aipm_mio_trunk_clock_gating_disable` |
| `resctrl_prvt_idle_late_regsN.qch_fsm_policy` | RC register | RW | QCh FSM autonomous idle enable (`enable_auto_idle` bit 0); set during boot by PrimeCode | `sv.socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regss` |
| `resctrl_prvt_idle_noise_regsN.i_qch_ctrl.force_qactive_value/enable` | RC register | RW | Override DVP noise QCh QActive; used as PkgC workaround for DVP stuck in Q_STOPPED | RC MIO registers |
| BIOS AIPM knob | BIOS setup | Config | Enables/disables AIPM globally or per sub-feature | Platform BIOS HAS |

## KPI & Timing

| Parameter | Value | Units | Condition / Notes | Source |
|-----------|-------|-------|-------------------|--------|
| RC trunk clock gate latency | ~few µs | µs | After both late+noise QCh assert idle+accept | RC TRM HAS |
| Boot WP programming | PH6 (post-reset-exit) | boot phase | PrimeCode programs per-RC ACTIVE/IDLE workpoints | MAS §9.1 |
| `CMPL_STATUS` check | Per-RA boot scan | - | PrimeCode skips RA when CMPL_STATUS=2 (IP in reset) | MAS §9.2 |
| DVP Q_STOPPED recovery | **PERMANENT on NWP** | - | PkgC6 ZBB removes the only recovery path; DVP stuck Q_STOPPED permanently once any stack enters no-device/IP-disable TCG | [HSD 14026152660](https://hsdes.intel.com/appstore/article/#/14026152660); see Combined Impact §3 |
| NUM_IDLE_WORKPOINTS | 2 | workpoints | Per RC_MIO: active WP + idle WP | MAS §6.2 |
| NUM_QCH_LATE | 9 | channels | RC_MIO Gen4 lnpv variant | MAS §6.2 |
| NUM_QCH_NOISE | 9 | channels | RC_MIO Gen4 lnpv variant | MAS §6.2 |

## NWP Delta

### Spec-Based Applicability Matrix (NWP)

The AIPM MIO trunk-gating runtime entry condition (per DMR HAS and NWP MAS) requires:
1. Stack in **PC0 active-idle**
2. Attached IO links in **L1/L2** so IPs withdraw clk_req/Qactive
3. RC observes QCh idle → hysteresis → gates trunk

**NWP spec confirmation (2026-05-31 — NWP MAS query):** Runtime no-device trunk gating is NOT supported on NWP. Empty/unconnected stacks are handled exclusively through static stack-disable and power-gate at boot/reset (BIOS + PrimeCode CMPL_STATUS=2 path). AIPM is not enabled for those stacks. The only valid AIPM runtime trigger is L1 entry — which is ZBB on NWP for both PCIe and UXI. UXI only gates during PC6 (not runtime idle), and PkgC6 is also ZBB. **Conclusion: there is no valid positive-path AIPM TCG scenario on NWP.**

| Condition | Feature Relevant? | NWP Status |
|-----------|-------------------|------------|
| L1 supported, PkgC not supported | ✅ Yes — active-idle AIPM use case | L1 ZBB'd — not this |
| L1 not supported, PkgC supported | ❌ No — no L1 idle trigger; UXI only gates on PC6 | PkgC also ZBB'd |
| **L1 not supported, PkgC not supported** | ❌ **No valid runtime TCG entry** | **NWP actual state** |
| **No device attached (empty stack)** | ❌ **Not applicable** — empty stacks statically disabled + power-gated at boot; AIPM not enabled | **ZBB — spec confirmed** |
| Stack disabled | ❌ **Not relevant as AIPM target** — AIPM must NOT be enabled; negative inhibit test only | TC 22022423019 |

**Bottom line for NWP**: **AIPM trunk clock gating has no valid positive-path scenario on NWP.** Every entry trigger is ZBB'd (PCIe L1, UXI L1/L0p, PkgC6) and empty stacks are statically disabled at boot rather than AIPM-gated. The only surviving open TCs are boot-time register programming checkout (infrastructure) and negative inhibit correctness (stack-disable, warm reset, surprise reset).

### Architectural Clarification: AIPM vs PkgC6 Independence (2026-06-01)

> **Source**: Co-Design NWP HAS/MAS query (2026-06-01) + TPF 22022562533 TC review

A common confusion when reading the NWP AIPM disposition: **AIPM (MIO trunk clock gating) is architecturally independent of PkgC6**. The RC operates at the IO stack level and can gate the trunk clock when QActive is de-asserted — even with the CPU/package fully active. PkgC6 is not a prerequisite.

This means the ZBB conclusion is **not** because PkgC6 is ZBB'd. The chain is:

```
AIPM trunk clock gate condition:
  QActive de-asserted by all IPs in stack
        │
        └─ Primary trigger on server platforms: PCIe/CXL device enters L1
                    │
                    └─ PCIe L1 is ZBB on NWP [HSD 22021155368]
                       UXI L1/L0p is ZBB on NWP [HSD 22021155419]
                            │
                            └─ No trigger → AIPM never fires for active stacks
                               Empty stacks → static disable at boot, not AIPM
                               ───────────────────────────────────────────────
                               Result: ZBB for all positive-path TCG scenarios
```

**The RC HW mechanism IS present in NWP.** The co-design NWP MAS confirms the QChannel infrastructure, hysteresis timer, and RC trunk gate capability exist. However the runtime entry condition has no valid trigger on NWP because **the devices that would de-assert QActive (PCIe/CXL entering L1) are themselves ZBB'd**.

PkgC6 being ZBB has a **separate, compounding impact**: it removes the only recovery path for DVP Q_STOPPED (see Risk section). This is an independent concern from whether AIPM positive paths exist.

**Implication for MC Shallow Self-Refresh**: MC SSR is also ZBB on NWP, but again not because PkgC6 is ZBB. SSR requires PkgC6 as a *prerequisite* (MC must enter SR before package can go C6), so when PkgC6 is ZBB'd, SSR has no valid use case — but the root ZBB is the memory power management architecture decision (no APD/PPD/LPM/SSR specified for NWP).

### TPF TC Review Outcome (2026-06-01)

All 14 MC Shallow Self-Refresh TCs are correctly ZBB'd per NWP spec. Of the 18 MIO Trunk Clock Gating TCs, the following are confirmed ZBB (updated from initial review that incorrectly assumed L1 still valid):

| TC | Title | Status | Confirmed Reason |
|----|-------|--------|-----------------|
| 22022422982 | QActive deassertion | ZBB ✅ | No L1 trigger → QActive never de-asserts for active stacks |
| 22022422984 | No Devices attached | ZBB ✅ | Empty stacks statically disabled at boot (spec confirmed) |
| 22022422987 | CXL Link in L1 | ZBB ✅ | CXL L1 ZBB on NWP |
| 22022422989 | PCIe Link in L1 | ZBB ✅ | PCIe L1 ZBB [HSD 22021155368] |
| 22022423009 | x ADR | ZBB ✅ | ADR supported but no prior TCG entry for cross-product |
| 22022423014 | x PC6 | ZBB ✅ | PkgC6 ZBB on NWP |
| 22022423018 | x Hot Plug / Hot Eject | ZBB ✅ | No prior TCG entry state to exit from |
| 22022423022 | x Seamless patching | ZBB ✅ | No prior TCG entry |
| 22022423027 | Perfmon debug counters | ZBB ✅ | Counter never increments without TCG entry |
| 22022423029 | Spurious Wakes | ZBB ✅ | No gated state to generate spurious wake from |
| 22022422990 | Late QChannel / Noise QChannel | **OPEN** | Boot-time RC programming checkout — independent of runtime TCG |
| 22022422992 | Auto Idle WP checkout | **OPEN** | Boot-time WP register correctness — infrastructure |
| 22022422994 | Hysteresis Timer | **OPEN** | Boot-time register checkout — infrastructure |
| 22022423000 | RC Capability0 reg checkout | **OPEN** | Boot-time register correctness — infrastructure |
| 22022423016 | x Warm Reset | **OPEN** | Reset recovery correctness — NWP-applicable |
| 22022423017 | PMX cross-product | **OPEN** | PMX applicable to NWP |
| 22022423019 | x IO Stack Disable | **OPEN** | Negative path: PrimeCode must NOT enable AIPM for disabled stacks |
| 22022423025 | x Surprise Reset | **OPEN** | Reset correctness — NWP-applicable |

### Open Questions

> **Pending input from Hector (AIPM feature expert)**

1. **DVP Q_STOPPED mitigation on NWP**: With PkgC6 ZBB'd, the `force_qactive_enable` PrimeCode workaround [HSD 14025929892] has no trigger. What is the NWP plan — RC exit interrupt, RTL fix, or DVP excluded from noise QCh aggregation?
2. **No-device stack TCG confirmation**: Spec says static disable at boot, not runtime AIPM. Is this definitively settled, or is there a bring-up mode where no-device stacks still enter runtime TCG?
3. **UIO_E stacks (x8 UXI-only)**: There is no L1 on NWP, so UXI never de-asserts QActive. AIPM trunk gating has no trigger on UIO_E stacks. Is there any other mechanism on NWP UIO_E that could cause QActive de-assertion?

### Sub-Feature Disposition

| Sub-Feature | NWP Disposition | Rationale |
|-------------|-----------------|-----------|
| **MIO Trunk Clock Gating (active links — PCIe/CXL/UXI in L1)** | ❌ **ZBB — Out of Scope** | No PCIe L1 ([HSD 22021155368](https://hsdes.intel.com/appstore/article/#/22021155368)), No UXI L1/L0p ([HSD 22021155419](https://hsdes.intel.com/appstore/article/#/22021155419)), No HSIO L0p ([HSD 22021155360](https://hsdes.intel.com/appstore/article/#/22021155360)) — L1 is the primary runtime trigger; without it the autonomous idle condition is never met for active links |
| **MIO Trunk Clock Gating (no-device-attached)** | ❌ **ZBB — Spec Confirmed** | Per NWP MAS: empty/unconnected stacks are statically disabled + power-gated at boot by BIOS and PrimeCode (CMPL_STATUS=2 path). Runtime AIPM trunk gating is NOT enabled for these stacks. TC 22022422984 rejected. |
| **MIO Trunk Clock Gating (IP-disable / disabled stack)** | ⚠️ **Negative test only** | Spec: AIPM must NOT be enabled for disabled stacks. TC 22022423019 validates PrimeCode correctly skips `QCH_FSM_POLICY` write for disabled stacks — inhibit correctness, not runtime gating. |
| **Hot Plug / Hot Eject from gated state** | ❌ **ZBB — Entry unreachable** | No valid AIPM TCG entry on NWP → no gated state to ungate from. TC 22022423018 rejected. |
| **Seamless patching unwind from TCG** | ❌ **ZBB — Entry unreachable** | Requires prior TCG entry. TC 22022423022 rejected. |
| **Perfmon autonomous entry counters** | ❌ **ZBB — No entry event** | No autonomous TCG entry on NWP → counter never increments. TC 22022423027 rejected. |
| **Spurious wakes from TCG** | ❌ **ZBB — No gated state** | No gated state to exit from. TC 22022423029 rejected. |
| **Boot-time RC WP Programming** | ✅ **Keep — Infrastructure** | Boot-time register programming checkout is independent of runtime TCG; validates RC register correctness regardless |
| **IP-disable skip logic (CMPL_STATUS=2)** | ✅ **Keep — Negative path** | PrimeCode must correctly identify disabled stacks at boot and skip AIPM enable; verifiable regardless of runtime TCG |
| **UFS Survivability** | ✅ **Keep — Intel Internal Only** | ZBB for customer; needed for A0 power-on at lower frequencies; P3 priority |
| **MC Shallow Self-Refresh** | ❌ **ZBB — Out of Scope** | No APD/PPD/LPM/SSR/SR for NWP customer ([HSD 22021155412](https://hsdes.intel.com/appstore/article/#/22021155412)); `AIPM_MC_SHALLOW_SELF_REFRESH_DISABLE = 1` |
| **Idle WP Programming** | ✅ **Keep (P2)** | `CR_VR_WP_IDLE` / `CR_CLK_WP_IDLE` (ratio=0, PLL_MODE=1) correctness needed for no-device stacks |

### NWP Architecture Changes Impacting AIPM

| Change | Impact on AIPM |
|--------|---------------|
| **Single NIO die (vs 2× IMH)** | One set of RC_MIO instances; no cross-die RC coordination needed; simplifies boot WP programming scope |
| **Unique FIVR per MIO stack** | FIVR power-gate behavior is deterministic per stack (no shared-FIVR ambiguity as in DMR); idle WP covers only that stack's FIVR |
| **DTS RA removed from MIO stack PMSB** | One fewer RA to enumerate during boot scan; CMPL_STATUS check scope reduced per stack |
| **UIO_E (P3, x8 UXI-only)** | Reduced QCh set vs UIO_A; no PCIe/CXL/IOMMU/HIOP late QCh — only UXI QCh present. There is no L1 on NWP so UXI never de-asserts QActive → AIPM trunk gating has no trigger on UIO_E stacks. |
| **PkgC6 ZBB** | PkgC entry/exit was the only event that drove QReq to **all** QCh simultaneously — its removal eliminates the natural DVP Q_STOPPED recovery path. PrimeCode `force_qactive_enable` WA has no trigger on NWP without PkgC6 (see Risk section) |
| **PCIe L1 + UXI L1/L0p ZBB (combined with PkgC6 ZBB)** | **Critical combined effect**: active-link TCG never fires (L1 ZBB) so the main power-saving use case is gone. The narrow surviving TCG scenarios (no-device, IP-disable) *do* still enter Q_STOPPED for DVP — but with PkgC6 also ZBB'd there is **no recovery event**. DVP tracing from any stack that enters TCG will be permanently broken for the rest of the boot unless RTL or firmware is fixed |
| **DFD DVP clock domain** | NWP NIO uses `dtf_clk = 0.800 GHz` from a dedicated dtf-PLL (VCCINF, Early availability) — **same clock architecture as DMR**. The "lfclk_1g" source was incorrect (corrected from NWP SoC Clock HAS §5.3). No clock domain change to DVP on NWP; the TCG/DVP Q_STOPPED incompatibility is therefore architecturally unchanged and carries forward to NWP with the same RTL behavior. |

### Risk: TCG/DVP Interaction — Permanently Broken on NWP Without Fix

#### Root Cause (DMR Sighting [14026152660](https://hsdes.intel.com/appstore/article/#/14026152660))

```
TCG entry → DVP noise QCh enters Q_STOPPED
                    │
                    ▼
  DVP spec: will NOT assert QActive from Q_STOPPED
  RC AIPM:  sends QReq only to QCh that asserted active (late QCh)
            → noise QCh (DVP) never receives QReq
                    │
                    ▼
  DVP stuck Q_STOPPED indefinitely
```

#### DMR Recovery Path (now gone on NWP)

On DMR, PkgC6 entry drove QReq to **all** QCh simultaneously — the only event that could rescue DVP from Q_STOPPED. The DMR PrimeCode workaround ([HSD 14025929892](https://hsdes.intel.com/appstore/article-one/#/14025929892)) hooked into PkgC6 entry/exit to toggle `force_qactive_enable` on the RC noise QCh registers.

```
On DMR:
  TCG entry → DVP enters Q_STOPPED
  PkgC6 entry/exit → RC drives QReq to ALL QCh → DVP recovers to Q_RUN
  PrimeCode WA: toggle force_qactive_enable on PkgC entry/exit

On NWP:
  No-device/IP-disable TCG → DVP enters Q_STOPPED   ← still happens
  PkgC6 ZBB → NO recovery event exists
  Result: DVP stuck Q_STOPPED permanently once any stack enters TCG
```

#### NWP Combined Effect: PkgC6 ZBB + L1 ZBB

| Scenario | DMR | NWP |
|----------|-----|-----|
| Active-link TCG fires | ✅ Yes (requires PCIe L1 / UXI L1) | ❌ Never (L1 ZBB'd — links always active) |
| No-device / IP-disable TCG fires | ✅ Yes | ✅ Yes — still enters TCG |
| DVP enters Q_STOPPED after TCG | ✅ Yes | ✅ Yes — same HW behavior |
| Recovery via PkgC6 entry/exit | ✅ Yes | ❌ PkgC6 ZBB'd — no recovery event |
| PrimeCode WA trigger exists | ✅ PkgC6 entry/exit | ❌ No equivalent trigger defined |
| Net DVP state after TCG | Recovers at next PkgC6 | **Stuck Q_STOPPED permanently** |

**Practical consequence for NWP**: Any time a no-device or IP-disabled MIO stack enters TCG (which is the test goal for TCD 1 and 2), the DVP in that stack will be permanently stuck in Q_STOPPED for the remainder of the boot. DFD captures via ITH T2/DVP from that stack will be unusable.

#### PrimeCode WA Options for NWP

| Option | Notes | Viability |
|--------|-------|----------|
| Hook into RC TCG exit interrupt (if RC supports it) | RC asserts interrupt on TCG exit; PrimeCode toggles `force_qactive_enable` | Check NWP RC_MIO HAS for exit interrupt support |
| Periodic PrimeCode task | Timer-based `force_qactive_enable` pulse | Possible but defeats TCG power savings; defeats idle |
| Suppress DVP noise QCh from TCG eligibility | DVP excluded from QCh aggregation → always stays Q_RUN | Cleanest; prevents issue without recovery needed; needs RTL change |
| RTL fix: proactive QReq to noise QCh on TCG exit | HW sends QReq to all QCh on any TCG exit, not just the triggering QCh | Architectural fix; should be raised with NWP DFD/IO RTL team |

#### Net AIPM Power Impact on NWP

| Scenario | Expected Savings |
|----------|----------------|
| Active-link TCG | ❌ Zero — L1 ZBB'd, links never idle |
| No-device stacks | ✅ Small — trunk clock gated for empty slots only |
| IP-disabled stacks | ✅ Meaningful — FIVR/PLL at lowest PS for fuse-disabled configs |
| MC Self-Refresh | ❌ Zero — PkgC6 + APD/PPD/LPM all ZBB'd |

**AIPM on NWP is effectively infrastructure validation** (RC WP programming correctness, IP-disable resource handdown) rather than power-savings validation. The bulk of DMR AIPM power benefit is lost due to the combined ZBB stack.

#### Action Items

1. **NWP DFD team**: Confirm whether NWP MIO RTL changed DVP-to-RC QCh wiring or added proactive QReq to noise QCh on TCG exit. If unchanged, DVP traces from any stack entering TCG are permanently broken.
2. **PrimeCode NWP team**: Identify the replacement trigger for `force_qactive_enable` management — PkgC6 entry/exit is no longer available on NWP.
3. **AIPM TCD 1 & 2**: Include a **DVP QSM status health check** (`dvp_status.qsmstatus`) pre/post TCG entry as a mandatory verification step, to detect the Q_STOPPED regression on NWP early in bring-up.

## Proposed Test Scope (NWP, ~30% of DMR AIPM coverage)

| # | TCD Title | Priority | Notes |
|---|-----------|----------|-------|
| 1 | `AIPM_MIO_TrunkCG_NoDevice_StackIdle` | P1 | Empty MIO slot → verify trunk clock gates via RC telemetry (`qch_fsm_policy`); **mandatory**: check `dvp_status.qsmstatus` pre/post — expect Q_STOPPED (HW) and confirm no permanent stuck state if DVP WA applied |
| 2 | `AIPM_MIO_TrunkCG_IPDisable_ResourceDown` | P1 | Fuse-disable MIO stack → verify RC takes FIVRs/PLLs to lowest PS; CMPL_STATUS=2 skip; **mandatory**: DVP QSM health check post-TCG entry |
| 3 | `AIPM_BootWP_ActiveWP_AllRCs` | P1 | Post-boot: read RC WP regs; cross-check against RA `CURRENT_VRCI`/`CURRENT_CLKI` |
| 4 | `AIPM_BootWP_IPDisable_SkipLogic` | P2 | Disable a FIVR/PLL → verify PrimeCode skips that RA (`CMPL_STATUS=2`) |
| 5 | `AIPM_IdleWP_Programming_Correctness` | P2 | Verify `CR_VR_WP_IDLE` / `CR_CLK_WP_IDLE` (ratio=0, PLL_MODE=1) set correctly |
| 6 | `AIPM_UFS_Survivability_LowerFreq` | P3 | Intel internal: program mesh to <2 GHz via dispatcher, verify operation |

## Legacy (Human-Curated Reference)

### Collateral Links

- TP Feature: [HSD 22022562533 — Autonomous Idle PM (AIPM)](https://hsdes.intel.com/appstore/article-one/#/22022562533)
- [RC TRM HAS](https://docs.intel.com/documents/sysip_pm/resource_controller/TRM/TRM.html)
- NWP NIO MIO MAS: [docs.intel.com/…/NWP_NIO_MIO.html](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/MIO/NWP_NIO_MIO.html)
- DMR MIO TCG doc: [docs.intel.com/…/DMR_IO_trunk_clock_gating_support.html](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_IO_trunk_clock_gating_support.html)
- DVP IP spec (Gen4 R2303): [docs.intel.com/…/DTF VISA Packetizer IP/gen4/releases/R2303](https://docs.intel.com/documents/arch_dfd/DFD_IP/DTF%20VISA%20Packetizer%20IP/gen4/releases/R2303/)

### Related Sightings / HSDs

| HSD | Title | Relevance |
|-----|-------|-----------|
| [14026152660](https://hsdes.intel.com/appstore/article/#/14026152660) | [X1 A0] MIO Trunk Clock gating — QActive not deasserting for MIOs with unpopulated ports | Root cause: DVP stuck Q_STOPPED after TCG entry; architectural TCG/DVP incompatibility |
| [14025929892](https://hsdes.intel.com/appstore/article-one/#/14025929892) | PkgC workaround + MIO TCG DVP interaction fix | PrimeCode `force_qactive_enable` PkgC entry/exit toggle; A0 HW fix expected B0 |
| [22021155368](https://hsdes.intel.com/appstore/article/#/22021155368) | No PCIe L1 (NWP ZBB) | Drives TCG active-link scope to ZBB |
| [22021155419](https://hsdes.intel.com/appstore/article/#/22021155419) | No UXI L1/L0p (NWP ZBB) | Drives TCG active-link scope to ZBB |
| [22021155360](https://hsdes.intel.com/appstore/article/#/22021155360) | No HSIO L0p (NWP ZBB) | Drives TCG active-link scope to ZBB |
| [22021155412](https://hsdes.intel.com/appstore/article/#/22021155412) | No Memory PM (APD/PPD/LPM/SSR/SR) | MC Shallow Self-Refresh ZBB |
| [22021155362](https://hsdes.intel.com/appstore/article/#/22021155362) | No PkgC6 (NWP ZBB) | Removes natural DVP Q_STOPPED recovery mechanism |

### Source Notes

- NWP scoping derived from `nwp_pm_fv/scripts/_post_aipm_scoping.py` (HSD 22022562533 description)
- DMR bug retrospective: `dmr_pm_bug_retrospective/dmr_pm_sighting_query_results.json` (sighting 14026152660)
- RC parameters (NUM_IDLE_WORKPOINTS=2, NUM_QCH_LATE/NOISE=9, lnpv variant) from MAS §6.2
