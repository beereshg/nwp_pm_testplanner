# TPF 16030762530 — AIPM - IO Trunk Clock Gating

| Field | Value |
|-------|-------|
| **TPF ID** | [16030762530](https://hsdes.intel.com/appstore/article-one/#/16030762530) |
| **Title** | [NWP PM] AIPM - IO Trunk Clock Gating |
| **Parent TP** | [16030762529 — [NWP PM] Autonomous Idle PM (AIPM)](https://hsdes.intel.com/appstore/article-one/#/16030762529) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Feature Classification & Introduction

**MIO Trunk Clock Gating (TCG)** is a sub-feature of AIPM (Autonomous Idle PM) that enables hardware-driven trunk clock gating for the I/O fabric (MIO stacks) when idle. The Resource Controller (RC_MIO, one per MIO/IO stack) monitors Q-channel activity from each IP in the stack; when both late and noise Q-channels are simultaneously idle and accepting, the RC gates the trunk clock autonomously — no OS or firmware intervention required at steady state.

**Classification:** Silicon-heavy. The RC_MIO hardware performs autonomous gating; PrimeCode firmware programs boot-time workpoints and Q-channel FSM policy at PH6. No OS driver involvement — AIPM is fully below-OS.

**Gating mechanism:**
- **Fuse:** `pcode_aipm_mio_trunk_clock_gating_disable` — globally disables MIO TCG (debug override for bringup)
- **BIOS knob:** AIPM enable/disable via platform BIOS setup
- **Runtime trigger:** PCIe/CXL/UXI device L1 entry (de-asserts QActive) — **ZBB on NWP**

**NWP disposition — infrastructure validation only:** AIPM TCG has **no valid positive-path runtime scenario on NWP**. Every entry trigger is ZBB'd (PCIe L1 [HSD 22021155368], UXI L1/L0p [HSD 22021155419], HSIO L0p [HSD 22021155360]) and empty stacks are statically disabled at boot rather than AIPM-gated. PkgC6 is also ZBB'd [HSD 22021155362], removing the only DVP Q_STOPPED recovery path from DMR. The surviving open TCs validate boot-time RC programming correctness, reset recovery, and negative inhibit for disabled stacks.

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| NIO dies per socket | 1 | NWP SOC topology |
| MIO stacks per NIO | Up to 6 (UIO_A, UIO_E, etc.) | NWP MIO MAS |
| RC_MIO variant | Gen4 lnpv | RC TRM HAS |
| NUM_QCH_LATE per RC | 9 | MAS §6.2 |
| NUM_QCH_NOISE per RC | 9 | MAS §6.2 |
| NUM_IDLE_WORKPOINTS | 2 (active + idle) | MAS §6.2 |
| Boot WP programming phase | PH6 (post-reset-exit) | MAS §9.1 |
| AIPM disable fuse | `pcode_aipm_mio_trunk_clock_gating_disable` | NWP fuse map |
| PCIe L1 | ZBB | HSD 22021155368 |
| UXI L1/L0p | ZBB | HSD 22021155419 |
| PkgC6 | ZBB | HSD 22021155362 |

---

## Section 2: Design Details

### MIO Trunk Clock Gating Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:16px;font-family:Arial,sans-serif;max-width:640px">
  <div style="font-weight:700;font-size:13px;text-align:center;margin-bottom:12px;border-bottom:2px solid #333;padding-bottom:8px">MIO Trunk Clock Gating — Full-Stack Architecture (NWP)</div>
  <div style="background:#999;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 5: OS / Tool</strong> — ❌ No OS involvement<br/>
    <small>AIPM is fully below-OS; no sysfs/driver interface. PythonSV namednodes for FV readback only.</small>
  </div>
  <div style="background:#ED7D31;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 4: BIOS Configuration</strong><br/>
    <small>AIPM enable/disable BIOS knob · QVFS_ENABLE boot policy</small>
  </div>
  <div style="background:#A020F0;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 3: PrimeCode (NIO PUnit) — Boot-Time Programming</strong><br/>
    <small>§9.1 RC WP programming: CR_VR_WP_ACTIVE/IDLE, CR_CLK_WP_ACTIVE/IDLE, QVFS_ENABLE, FORCE_ACTIVE_TV_CV_COPY<br/>§9.2 IP-disable skip: CMPL_STATUS=2 → skip RA<br/>§9.3 UFS survivability freq (Intel internal, A0 bringup)</small>
  </div>
  <div style="background:#70AD47;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 2: RC_MIO (Resource Controller — per MIO stack)</strong><br/>
    <small>Q-channel FSM: monitors late QCh (9) + noise QCh (9) · Autonomous trunk clock gate when idle · Hysteresis timer · FIVR idle workpoint transition</small>
  </div>
  <div style="background:#FF0000;color:#fff;padding:10px;margin:4px;border-radius:4px;text-align:center">
    <strong>Layer 1: Silicon / HW</strong><br/>
    <small>Late QCh IPs: HIOP, IOMMU, PCIe RP, CXL, UXI/ULA, FBLP · Noise QCh: DVP · LFCLK PLL RA · FIVR (per stack) · ISA (o_safemode)</small>
  </div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV | Notes |
|---|---|---|---|---|---|---|
| OS / Tool | ❌ | ❌ | ❌ | ❌ | ❌ | No OS interface — AIPM is below-OS |
| BIOS Configuration | ✅ safe | ❌ | ❌ | ✅ | ❌ | BIOS knob validation; VP safe for negative testing |
| PrimeCode (NIO PUnit) Boot-Time Programming | ✅ | ✅ | ✅ | ✅ | ❌ | Core validation layer — all pre-Si + FV tiers |
| RC_MIO (Resource Controller) | ✅ | ✅ | ❌ | ✅ | ❌ | RC register readback; HSLE covers within-die RC; no XOS needed |
| Silicon / HW (Q-channels, FIVR, PLL) | ❌ | ✅ | ❌ | ✅ | ❌ | RTL-level QCh; FV observes real silicon; runtime TCG ZBB limits what can be exercised |

### MIO TCG Boot / Reset Flow (NWP)

```
  Power-On / Warm Reset / Surprise Reset
       │
       ▼
  PrimeCode PH6 (post-reset-exit)
       │
       ├─ For each MIO stack:
       │   ├─ Read RA: CURRENT_VRCI, CURRENT_CLKI
       │   ├─ Check CMPL_STATUS
       │   │     ├─ CMPL_STATUS = 2 → IP disabled/in-reset → SKIP RA (§9.2)
       │   │     └─ CMPL_STATUS ≠ 2 → proceed
       │   ├─ Program: CR_VR_WP_ACTIVE, CR_CLK_WP_ACTIVE (from RA)
       │   ├─ Program: CR_VR_WP_IDLE, CR_CLK_WP_IDLE (ratio=0, PLL_MODE=1)
       │   ├─ Program: QVFS_ENABLE = 1
       │   ├─ Program: FORCE_ACTIVE_TV_CV_COPY
       │   └─ Program: QCH_FSM_POLICY.ENABLE_AUTO_IDLE = 1 (per late QCh)
       │
       ├─ Check fuse: pcode_aipm_mio_trunk_clock_gating_disable
       │   └─ If set → do NOT program autonomous idle
       │
       └─ DONE — RC_MIO armed for autonomous TCG
            (but runtime entry never fires on NWP — L1 ZBB)
```

### MIO TCG Architecture — RC Autonomous Gating (DMR Reference)

```
  IO Stack in PC0 (active)
       │
       ├── Late QCh (9 channels):
       │   HIOP, IOMMU, PCIe RP, CXL, UXI/ULA, FBLP ...
       │         │
       │         └── Device enters L1 → IP de-asserts QActive
       │
       ├── Noise QCh (9 channels):
       │   DVP (Debug Trace Packetizer)
       │         │
       │         └── DVP idle → QActive de-asserted
       │
       └── RC_MIO observes:
             ALL late QCh idle + ALL noise QCh idle
                    │
                    ▼  hysteresis timer expires
             Gate trunk clock autonomously
                    │
                    ├── FIVR transitions to idle workpoint
                    └── LFCLK PLL may shut down (PLL_MODE=1)

  ❌ On NWP: L1 ZBB → late QCh never idle → RC never gates
```

### DVP Q_STOPPED Risk Chain (NWP — Permanently Broken)

```
  TCG entry (no-device / IP-disable scenario)
       │
       ▼
  DVP noise QCh enters Q_STOPPED
       │
       ▼
  DVP spec: will NOT assert QActive from Q_STOPPED
  RC AIPM: sends QReq only to QCh that asserted active (late QCh)
       → noise QCh (DVP) never receives QReq
       │
       ▼
  DMR recovery: PkgC6 entry/exit → QReq to ALL QCh → DVP recovers
  NWP: PkgC6 ZBB → NO recovery event → DVP stuck Q_STOPPED permanently
```

### Interface & Register Matrix

| Register / Signal | NWP Path | Field | Default | Feature Effect | Tier Validated |
|---|---|---|---|---|---|
| RC late QCh FSM policy | `sv.socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regss` | `enable_auto_idle` (bit 0) | 0 (PrimeCode sets to 1) | Enables autonomous idle for late QCh | PSS, FV |
| RC noise QCh control | `sv.socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_noise_regs0` | `force_qactive_value`, `force_qactive_enable` | 0 | PkgC workaround for DVP Q_STOPPED; no trigger on NWP | FV |
| CR_CLK_WP_ACTIVE | RC_MIO WP registers | ratio, PLL_MODE | From RA CURRENT_CLKI | Active clock workpoint | PSS, FV |
| CR_CLK_WP_IDLE | RC_MIO WP registers | ratio=0, PLL_MODE=1 | From RA | Idle clock workpoint (never triggered at runtime) | PSS, FV |
| CR_VR_WP_ACTIVE / IDLE | RC_MIO WP registers | voltage workpoint | From RA CURRENT_VRCI | Active/idle voltage workpoint | PSS, FV |
| QVFS_ENABLE | RC_MIO | enable bit | 0 (PrimeCode sets to 1) | Q-channel VFS autonomous enable | PSS, FV |
| RC Capability0 | `sv.socket0.imh0.resctrl.rc_mio_ew.resctrl_prv_capability0` | NUM_QCH_LATE, NUM_QCH_NOISE, NUM_IDLE_WP | HW | Discovery register: 9 / 9 / 2 for Gen4 lnpv | FV |
| AIPM disable fuse | `sv.sockets.imhs.fuses.punit.pcode_aipm_mio_trunk_clock_gating_disable` | disable bit | 0 | Globally disables MIO TCG | FV |
| DVP QSM status | `dvp_status.qsmstatus` | QSM state | — | 0 = Q_STOPPED; health check for DVP interaction | FV |
| CMPL_STATUS | Per-RA (FIVR RA, LFCLK PLL RA) | status field | — | 2 = IP disabled/in-reset → PrimeCode skips RA | PSS, FV |

### Observability

| Observable | Type | Tool / Command | What It Shows |
|---|---|---|---|
| RC WP registers | Register readback | `sv.socket0.imh0.resctrl.rc_mio_ew.cr_clk_wp_active.read()` | Active clock workpoint value; compare to RA CURRENT_CLKI |
| QCh FSM policy | Register readback | `sv.socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regss[N].qch_fsm_policy.show()` | enable_auto_idle bit; confirms PrimeCode programming |
| RC Capability0 | Register readback | `sv.socket0.imh0.resctrl.rc_mio_ew.resctrl_prv_capability0.show()` | NUM_QCH_LATE=9, NUM_QCH_NOISE=9, NUM_IDLE_WP=2 |
| AIPM fuse | Fuse readback | `sv.sockets.imhs.fuses.punit.pcode_aipm_mio_trunk_clock_gating_disable.read()` | 0 = enabled; 1 = globally disabled |
| DVP QSM status | Register readback | `dvp_status.qsmstatus` read per stack | 0 = Q_STOPPED (risk indicator); expected non-zero for healthy DVP |
| CMPL_STATUS | RA register | Per-RA read during boot | 2 = IP disabled → PrimeCode skip path verified |

### SKU / Config Distinctions

| SKU / Config | Distinction | TCDs Affected |
|---|---|---|
| AIPM fuse disabled (`pcode_aipm_mio_trunk_clock_gating_disable = 1`) | RC not programmed for autonomous idle; all boot-time WP writes skipped | All 4 TCDs |
| IO stack fuse-disabled (CMPL_STATUS=2) | PrimeCode skips RA for that stack; AIPM not enabled | TCD Boot Time Setup, TCD Cross Products (IO Stack Disable TC) |
| UIO_E stacks (x8 UXI-only) | Reduced QCh set vs UIO_A; no PCIe/CXL/IOMMU/HIOP late QCh; UXI never de-asserts QActive on NWP | TCD Entry/Residency (confirms ZBB for these stacks) |
| PkgC6 ZBB | Removes DVP Q_STOPPED recovery path; `force_qactive_enable` PrimeCode WA has no trigger | TCD Entry/Residency, TCD Cross Products |

### Agent Source Ownership

| Layer / Agent | Key Artifact (source file / FAS) |
|---|---|
| PrimeCode (NIO PUnit) | `src/flow/aipm/` — RC WP boot programming; `src/flow/pkgc/` — DVP force_qactive toggle |
| PCode (CBB) | PkgC handshake; HPM messages for PkgC entry/exit |
| BIOS | AIPM BIOS knob; QVFS_ENABLE boot policy |
| RC_MIO HW | RC TRM HAS — Gen4 lnpv variant; autonomous QCh FSM |
| DVP HW | DVP IP spec (Gen4 R2303) — noise QCh participant |

---

## Section 3: Validation Strategy

MIO Trunk Clock Gating on NWP is **infrastructure validation** — the RC hardware is present and PrimeCode programs it at boot, but runtime TCG entry never fires. The validation strategy therefore focuses on:

1. **Boot-time correctness** — verifying PrimeCode correctly programs RC workpoints, QCh FSM policy, and capability registers at PH6
2. **Negative path / inhibit correctness** — verifying PrimeCode does NOT enable AIPM for disabled stacks (CMPL_STATUS=2) and that the AIPM fuse disable works
3. **Reset recovery** — verifying RC state is correctly re-initialized after warm reset and surprise reset
4. **Cross-product** — verifying RC/AIPM infrastructure interactions with PMX, IO stack disable, and reset flows

Layer coverage is mapped in §2 — the Validation-Tier Layer Claim table identifies which tier validates each stack layer and flags any unclaimed layers as accepted gaps.

### Tier Definitions

| Tier | Environment | Interface | What It Validates |
|---|---|---|---|
| PSS — VP | Simics (virtual platform) | PythonSV → RC model | PrimeCode boot-time WP logic; CMPL_STATUS skip path; fuse-disable path |
| PSS — HSLE | Single-die NIO RTL | PythonSV → RC RTL | Within-die RC register correctness; RC Capability0 HW values |
| PSS — XOS | Both-die RTL (NIO+CBB) | PythonSV → full RTL | Not required — AIPM is NIO-local; no cross-die protocol |
| FV | Post-silicon NWP | PythonSV → namednodes | Real silicon RC behavior; DVP interaction risk validation; reset recovery |
| PV | Post-silicon NWP + Ubuntu | N/A | ❌ Not applicable — AIPM has no OS interface |

---

## Section 4: Tier Coverage

### Bug Coverage Matrix

| Bug Category | PSS (VP) | PSS (HSLE) | PSS (XOS) | FV | PV |
|---|---|---|---|---|---|
| PrimeCode WP programming logic error (wrong value written) | ✅ | ✅ | ❌ N/A | ✅ | ❌ |
| PrimeCode CMPL_STATUS=2 skip logic error | ✅ | ✅ | ❌ N/A | ✅ | ❌ |
| AIPM fuse disable not honored | ✅ | ❌ | ❌ | ✅ | ❌ |
| RC Capability0 HW mismatch (wrong Gen4 variant) | ❌ | ✅ | ❌ | ✅ | ❌ |
| RC WP not restored after warm/surprise reset | ⚠️ limited | ❌ | ❌ | ✅ | ❌ |
| DVP Q_STOPPED after TCG (no-device/IP-disable) | ❌ | ❌ | ❌ | ✅ | ❌ |
| AIPM incorrectly enabled for disabled stack | ✅ | ✅ | ❌ | ✅ | ❌ |
| Runtime TCG entry/residency bug | ❌ | ❌ | ❌ | ❌ ZBB | ❌ |

### Scenario Coverage Across Tiers

| Scenario | PSS | FV | PV | Unique Value |
|---|---|---|---|---|
| Boot WP programming correctness (all stacks) | ✅ | ✅ | ❌ | Verifies PrimeCode §9.1 programming logic |
| QCh FSM enable_auto_idle set correctly | ✅ | ✅ | ❌ | Confirms autonomous idle armed after boot |
| RC Capability0 register discovery checkout | ❌ | ✅ | ❌ | HW discovery — only meaningful on real silicon |
| Idle WP values (ratio=0, PLL_MODE=1) | ✅ | ✅ | ❌ | Confirms idle WP populated even though never triggered |
| CMPL_STATUS=2 skip logic (IP-disable) | ✅ | ✅ | ❌ | Negative path — critical safety check |
| AIPM fuse disable honored | ✅ | ✅ | ❌ | Confirms no RC programming when fuse set |
| Warm reset → RC WP re-initialization | ⚠️ | ✅ | ❌ | Reset recovery correctness |
| Surprise reset → clean RC state | ❌ | ✅ | ❌ | Uncontrolled reset recovery |
| PMX RC register exerciser | ❌ | ✅ | ❌ | PMX infrastructure for NWP AIPM registers |
| DVP QSM health check post-TCG entry | ❌ | ✅ | ❌ | Detect DVP Q_STOPPED regression early |

---

## Section 5: Risks & Dependencies

### Active Risks

- **DVP Q_STOPPED permanently broken on NWP** — When any MIO stack enters TCG (no-device or IP-disable scenario), DVP in that stack enters Q_STOPPED. On DMR, PkgC6 entry/exit provided recovery via `force_qactive_enable` toggle. On NWP, PkgC6 is ZBB'd — there is **no recovery event**. DVP tracing from any stack that enters TCG will be permanently broken for the rest of the boot unless RTL or firmware is fixed. **Mitigation:** Include mandatory DVP QSM health check (`dvp_status.qsmstatus`) in TCD 1 and TCD 2 TCs; escalate to NWP DFD/IO RTL team for proactive QReq to noise QCh on TCG exit. See [HSD 14026152660](https://hsdes.intel.com/appstore/article/#/14026152660).

- **NWP DFD team confirmation pending** — Whether NWP MIO RTL changed DVP-to-RC QCh wiring or added proactive QReq to noise QCh on TCG exit is not yet confirmed. If unchanged, DVP traces from any stack entering TCG are permanently broken.

- **PrimeCode NWP team action pending** — Replacement trigger for `force_qactive_enable` management needs to be identified; PkgC6 entry/exit is no longer available on NWP.

### Accepted Coverage Limitations (by design — no new TCs required)

| Gap ID | Description | Coverage Today | Accepted Rationale |
|--------|-------------|----------------|-------------------|
| **G-1** | Runtime TCG entry/residency (active-link gating) | ❌ None | PCIe L1 ZBB [HSD 22021155368], UXI L1/L0p ZBB [HSD 22021155419] — the primary runtime trigger does not exist on NWP; no way to exercise |
| **G-2** | No-device stack runtime TCG (empty slot idle gating) | ❌ None | NWP MAS confirms empty stacks are statically disabled at boot (CMPL_STATUS=2), not runtime AIPM-gated; no valid scenario |
| **G-3** | TCG perfmon residency counters | ❌ None | Counter never increments without TCG entry; no valid entry trigger on NWP |
| **G-4** | Spurious wakes from gated state | ❌ None | No gated state to generate spurious wake from |
| **G-5** | TCG × ADR / Hot Plug / Seamless patching | ❌ None | All require prior TCG entry state; entry unreachable on NWP |
| **G-6** | PV / OS layer validation | ❌ None | AIPM has no OS interface; entirely below-OS feature |

---

## Section 6: DFX Considerations

- **DVP interaction:** DVP (Debug Trace Packetizer) is a noise QCh participant. TCG entry causes DVP to enter Q_STOPPED, which on NWP is permanent due to PkgC6 ZBB. Any DFD capture (ITH T2 / DVP) from a stack that has entered TCG will be unusable. TCD 1 and 2 must include DVP QSM health checks.

- **RC telemetry:** RC_MIO exposes workpoint and QCh FSM state via register readback — primary FV observation method for boot-time programming checkout.

- **AIPM fuse disable:** `pcode_aipm_mio_trunk_clock_gating_disable` provides a global safety override to disable TCG for bringup debug without modifying BIOS or firmware.

---

## Section 7: Common Corner Cases

| Corner Case | Affected TCDs | Expected Behavior |
|---|---|---|
| Warm reset → RC WP re-initialization | TCD Cross Products (22022421242) | PrimeCode re-programs all RC workpoints at PH6 after warm reset; register values match initial boot |
| Surprise reset → clean RC state | TCD Cross Products (22022421242) | After uncontrolled reset, RC state is clean and re-programmed correctly; no residual state from pre-reset |
| CMPL_STATUS=2 on one stack, others normal | TCD Boot Time Setup (22022421240), TCD Cross Products (22022421242) | PrimeCode skips RA for disabled stack; programs normally for all others |
| AIPM fuse disabled + all stacks active | All TCDs | RC not programmed for autonomous idle; boot WP programming skipped entirely |
| DVP enters Q_STOPPED after no-device TCG | TCD Boot Time Setup (22022421240), TCD Entry/Residency (22022421244) | DVP permanently stuck Q_STOPPED on NWP; mandatory health check required |
| UIO_E stacks (UXI-only, no PCIe/CXL) | TCD Entry/Residency (22022421244) | Reduced QCh set; UXI never de-asserts QActive on NWP; confirms ZBB for these stacks |
| Mixed stack state (some disabled, some active) | TCD Boot Time Setup (22022421240) | PrimeCode handles each stack independently; CMPL_STATUS=2 stacks skipped; active stacks programmed normally |

---

## Section 8: TCD Coverage Summary & References

### Child TCDs

| TCD ID | Title | Status | Segment | TC Count (open/total) |
|---|---|---|---|---|
| [22022421240](https://hsdes.intel.com/appstore/article-one/#/22022421240) | MIO Trunk Clock gating Boot Time Setup | open | FV | 3 open / 4 total |
| [22022421242](https://hsdes.intel.com/appstore/article-one/#/22022421242) | MIO Trunk Clock gating Cross products | open | FV | 4 open / 8 total |
| [22022421244](https://hsdes.intel.com/appstore/article-one/#/22022421244) | MIO Trunk Clock gating Entry / Residency | rejected | FV | 0 open / 2 total (ZBB) |
| [22022421236](https://hsdes.intel.com/appstore/article-one/#/22022421236) | MIO Trunk Clock gating Actions | rejected | FV | 0 open / 4 total (ZBB) |

### References

- [AIPM KB — aipm.md](../../pm_features/pm_cross_products/aipm.md) — Full AIPM architecture, NWP delta, DVP risk analysis, proposed test scope
- [RC TRM HAS](https://docs.intel.com/documents/sysip_pm/resource_controller/TRM/TRM.html) — RC Gen4 lnpv capability registers and autonomous idle specification
- [NWP IMH SoC PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — §9.1–9.3 RC boot-time workpoint programming; §9.2 IP-disable skip
- [NWP NIO MIO MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/mio/nwp_nio_mio.html) — NWP MIO clock interfaces
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html) — NWP feature applicability
- [DMR IO Trunk Clock Gating HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_IO_trunk_clock_gating_support.html) — DMR reference implementation
- [DVP IP Spec (Gen4 R2303)](https://docs.intel.com/documents/arch_dfd/DFD_IP/DTF%20VISA%20Packetizer%20IP/gen4/releases/R2303/) — DVP noise QCh behavior
- [HSD 14026152660](https://hsdes.intel.com/appstore/article/#/14026152660) — DVP stuck Q_STOPPED after TCG entry (DMR sighting)
- [HSD 14025929892](https://hsdes.intel.com/appstore/article-one/#/14025929892) — PrimeCode force_qactive_enable PkgC workaround
- [HSD 22021155368](https://hsdes.intel.com/appstore/article/#/22021155368) — PCIe L1 ZBB on NWP
- [HSD 22021155419](https://hsdes.intel.com/appstore/article/#/22021155419) — UXI L1/L0p ZBB on NWP
- [HSD 22021155360](https://hsdes.intel.com/appstore/article/#/22021155360) — HSIO L0p ZBB on NWP
- [HSD 22021155362](https://hsdes.intel.com/appstore/article/#/22021155362) — PkgC6 ZBB on NWP
- [HSD 22021155412](https://hsdes.intel.com/appstore/article/#/22021155412) — No Memory PM (APD/PPD/LPM/SSR/SR) on NWP