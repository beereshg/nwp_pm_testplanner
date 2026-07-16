# TCD 22022420925 -- SST-TF Enabling & Discovery

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420925](https://hsdes.intel.com/appstore/article-one/#/22022420925) |
| **Title** | SST-TF Enabling & Discovery |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030762937 -- NWP PM SST-TF (Turbo Frequency)](https://hsdes.intel.com/appstore/article-one/#/16030762937) |
| **Child TCs** | [22022422200](https://hsdes.intel.com/appstore/article-one/#/22022422200) -- TPMI register check (silicon)<br>[22022422201](https://hsdes.intel.com/appstore/article-one/#/22022422201) -- Dynamic enable/disable via TPMI (VP)<br>[22022422202](https://hsdes.intel.com/appstore/article-one/#/22022422202) -- CLOS IDs coverage (rejected NWP)<br>[16030715662](https://hsdes.intel.com/appstore/article-one/#/16030715662) -- ZBB Negative Checks (PSS)<br>[16030715714](https://hsdes.intel.com/appstore/article-one/#/16030715714) -- Fuse Propagation (PSS)<br>[16030715716](https://hsdes.intel.com/appstore/article-one/#/16030715716) -- Fuse Sanity (PSS) |
| **KB last updated** | 2026-07-15 |

---

## Section 1: Architecture / Micro-architecture and Functionality

**SST-TF (Speed Select Technology - Turbo Frequency)** partitions cores into **HP (high priority, CLOS[0])** and **LP (low priority, CLOS[3])** groups with distinct frequency ceilings. It is the **underlying mechanism for NWP PCT** (Priority Core Turbo). The feature is enabled by BIOS at CPL3 and managed by PCode at runtime.

<!-- raw-html -->
<div style="margin:16px 0;border:1px solid #bfcfe8;border-radius:8px;overflow:hidden;font-family:'Segoe UI',Arial,sans-serif;font-size:12px;">
  <div style="background:#0f4c81;color:#fff;padding:8px 16px;font-weight:700;font-size:12px;letter-spacing:.3px;">SST-TF Enabling & Discovery -- Data Flow</div>
  <div style="padding:16px 20px;background:#f8fafc;">
    <div style="display:flex;gap:0;align-items:flex-start;margin-bottom:12px;flex-wrap:wrap;">
      <div style="background:#fff3e0;border:2px solid #e65100;border-radius:6px;padding:8px 12px;min-width:120px;text-align:center;">
        <div style="font-weight:700;color:#e65100;font-size:11px;">SST-TF Fuses</div>
        <div style="font-size:10px;color:#555;line-height:1.6;margin-top:4px;">LP_CLIP_RATIO x6<br>HP TRL x3 buckets x6 CDYN<br>per PP level</div>
      </div>
      <div style="display:flex;flex-direction:column;align-items:center;padding:20px 8px 0;">
        <div style="font-size:10px;color:#555;">PH5 init</div>
        <div style="border-top:2px solid #555;width:40px;position:relative;"><span style="position:absolute;right:-6px;top:-7px;color:#555;font-size:14px;">&#9658;</span></div>
      </div>
      <div style="background:#e8f5e9;border:2px solid #2e7d32;border-radius:6px;padding:8px 12px;min-width:140px;text-align:center;">
        <div style="font-weight:700;color:#2e7d32;font-size:11px;">TPMI SST_TF_INFO_0..8</div>
        <div style="font-size:10px;color:#555;line-height:1.6;margin-top:4px;">Written by PrimeCode<br>SST_TF_INFO_0: LP clips<br>SST_TF_INFO_2..7: HP TRL<br>SST_TF_INFO_8: HP core counts</div>
      </div>
      <div style="display:flex;flex-direction:column;align-items:center;padding:20px 8px 0;">
        <div style="font-size:10px;color:#555;">CPL3</div>
        <div style="border-top:2px solid #555;width:40px;position:relative;"><span style="position:absolute;right:-6px;top:-7px;color:#555;font-size:14px;">&#9658;</span></div>
      </div>
      <div style="background:#e8eaf6;border:2px solid #3949ab;border-radius:6px;padding:8px 12px;min-width:120px;text-align:center;">
        <div style="font-weight:700;color:#3949ab;font-size:11px;">BIOS Enable</div>
        <div style="font-size:10px;color:#555;line-height:1.6;margin-top:4px;">SST_PP_CONTROL<br>feature_state[1]=1<br>CLOS_ASSOC: HP=CLOS0</div>
      </div>
      <div style="display:flex;flex-direction:column;align-items:center;padding:20px 8px 0;">
        <div style="font-size:10px;color:#555;">slow loop</div>
        <div style="border-top:2px solid #555;width:40px;position:relative;"><span style="position:absolute;right:-6px;top:-7px;color:#555;font-size:14px;">&#9658;</span></div>
      </div>
      <div style="background:#fce4ec;border:2px solid #c62828;border-radius:6px;padding:8px 12px;min-width:130px;text-align:center;">
        <div style="font-weight:700;color:#c62828;font-size:11px;">PCode TrlManager</div>
        <div style="font-size:10px;color:#555;line-height:1.6;margin-top:4px;">load_hp_clos_trl()<br>load_lp_clos_trl()<br>4 TRL tables active</div>
      </div>
    </div>
    <div style="background:#fff8e1;border:1px solid #f9a825;border-radius:5px;padding:8px 12px;font-size:11px;">
      <strong>Validation targets:</strong> (1) TPMI registers populated correctly from fuses &nbsp;&#8212;&nbsp; (2) feature_state[1] toggle causes TRL reload &nbsp;&#8212;&nbsp; (3) ZBB deprecated features (SST-PP/CP/BF) are disabled
    </div>
  </div>
</div>
<!-- /raw-html -->

### Key Concepts

| Concept | Description |
|---------|-------------|
| **SST-TF** | Speed Select Technology - Turbo Frequency. Partitions cores HP/LP via CLOS groups. Underlying mechanism for NWP PCT. |
| **HP cores** | CLOS[0]; elevated TRL; operated at P0max (~4.4 GHz). Assigned by BIOS via SST_CLOS_ASSOC. |
| **LP cores** | CLOS[3]; clipped to LP_CLIP_RATIO fuse (~P1). All other cores. |
| **SST_TF_INFO_0** | TPMI register: LP_CLIP_RATIO per 6 CDYN levels + FEATURE_SUPPORTED bit. Written by PrimeCode at reset PH5. |
| **SST_TF_INFO_2..7** | TPMI registers: HP TRL ratios; 3 buckets x 6 CDYN levels. |
| **SST_TF_INFO_8** | HP bucket core-counts (feature_revision >= 2). |
| **SST_PP_CONTROL.feature_state[1]** | Enable/disable bit for SST-TF. Toggled by BIOS (CPL3) or OS via TPMI. Detected by PCode SstManager in slow loop. |
| **TrlManager** | PCode component: maintains 4 TRL tables (legacy, sst_pp, hp_clos, lp_clos). Reloads from TPMI on enable/disable. |
| **ZBB (deprecated)** | SST-PP, SST-CP, SST-BF are deprecated on NWP. TPMI feature bits for these must remain 0. |

### NWP-Specific Deltas

- NWP uses **DLCP (Die-Level Cherry Picking)** for HP core selection — HP cores are **fuse-pinned**, not OS-configurable. CLOS_ASSOC is written by BIOS from fuse mask, not by OS.
- NWP has **2 CBBs** (cbb0 + cbb1) — TRL distribution loops iterate `range(2)` not `range(4)`.
- SST-PP, SST-CP, SST-BF are **deprecated on NWP** — TPMI feature bits must remain 0. ZBB negative TC validates this.
- Legacy MSR 0x1AD is still used by OS to read TRL, but **PCode reconciles TPMI TRL on each slow loop** — MSR writes do not persist.
- SST_TF_INFO_8 (HP bucket core-counts) requires **`feature_revision >= 2`** — TCs must check before reading.
- NWP root die is **NIO** (not IMH-P) — TPMI path is `sv.socket0.nio0.tpmi.sst_*`, not `sv.socket0.imh0`.
- `feature_state[1]` toggle takes **1+ slow-loop cycles** (~1 ms) to propagate — tests must poll, not use fixed sleep.

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422200 — SST-TF TPMI register check](https://hsdes.intel.com/appstore/article-one/#/22022422200) | Fuse-to-TPMI propagation | Validate SST_TF_INFO_0..8 populated correctly; LP clip ratios, HP TRL buckets, HP core counts per PP level |
| [22022422201 — SST-TF dynamic enable/disable via TPMI](https://hsdes.intel.com/appstore/article-one/#/22022422201) | Runtime enable/disable | Toggle `feature_state[1]` via TPMI; verify TRL transition within 1 slow-loop; bucket + status consistency |
| ~~[22022422202 — SST-TF CLOS IDs coverage](https://hsdes.intel.com/appstore/article-one/#/22022422202)~~ | ~~CLOS ID coverage (REJECTED)~~ | ~~NWP uses DLCP-pinned HP cores; arbitrary CLOS reassignment conflicts with DLCP mode~~ |
| [16030715662 — [PSS] ZBB Negative Checks](https://hsdes.intel.com/appstore/article-one/#/16030715662) | Deprecated feature disable | SST-PP/CP/BF disabled on NWP; no MCA or unexpected behavior when probed |
| [16030715714 — [PSS] Fuse Values Propagation](https://hsdes.intel.com/appstore/article-one/#/16030715714) | Fuse propagation per PP level | SST-TF fuses → TPMI space for current SST-PP level; LP_CLIP_RATIO + HP TRL match fuse expectations |
| [16030715716 — [PSS] Fuse Values Sanity](https://hsdes.intel.com/appstore/article-one/#/16030715716) | Fuse value sanity | SST-TF fuse values per design spec; monotonic LP clip ordering; HP TRL ≥ LP clip; bucket consistency |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Direction | Description |
|-----------|----------------|-----------|-------------|
| TPMI SST | SST_PP_CONTROL.feature_state[1] | RW | SST-TF enable bit. 1=enabled. PCode SstManager polls in slow loop. |
| TPMI SST | SST_TF_INFO_0 | RO | LP_CLIP_RATIO_0..5 per CDYN + FEATURE_SUPPORTED bit. Written at PH5. |
| TPMI SST | SST_TF_INFO_2..7 | RO | HP TRL ratios: 3 buckets x 6 CDYN levels. Written at PH5. |
| TPMI SST | SST_TF_INFO_8 | RO | HP bucket core-counts (feature_revision >= 2). |
| TPMI SST | SST_CLOS_ASSOC_0..N | RW | Per-core CLOS assignment. HP=CLOS[0], LP=CLOS[3]. Set by BIOS. |
| TPMI SST | SST_PP_INFO_4 | RO | ODC TRL source. ODC resolved = min(SST_PP_INFO_4, MSR 0x1AD, ODC_TURBO_MAX_RATIO). |
| MSR | 0x1AD (PRIMARY_TURBO_RATIO_LIMIT) | RW | HP TRL ratios (SSE/CDYN0). Updated from SST_TF_INFO_2 when TF active. |
| Fuse | SST_TF_CONFIG[0..4] | RO | LP clip ratios + HP TRL arrays per PP level. Source for PrimeCode PH5 init. |
| PythonSV | sv.socket0.nio0.tpmi.sst_tf_info_0.lp_clip_ratio_0 | RO | LP clip ratio for SSE (CDYN[0]) |
| PythonSV | sv.socket0.nio0.tpmi.sst_pp_control.feature_state | RW | Feature enable field |

---

## Section 3: Reset / Power / Clocking

- **Reset Phase 5 (PH5)**: PrimeCode `sstTfInfoInit()` reads SST_TF fuse arrays, builds TRL/clip tables, and writes SST_TF_INFO_0..8 to TPMI. This happens before BIOS CPL3 handoff -- TPMI is populated before BIOS reads it.
- **CPL3 (BIOS)**: BIOS enables SST-TF by writing `SST_PP_CONTROL.feature_state[1] = 1` and programs CLOS assignments (`SST_CLOS_ASSOC` registers). Overrides MSR 0x1AD.
- **PCode slow loop**: `SstManager` detects `feature_state[1]` change; calls `TrlManager::load_hp_clos_trl()` and `load_lp_clos_trl()` to reload from TPMI IO space. 1+ slow-loop latency before reload completes.
- **C-state cycle**: CLOS assignments and TRL tables persist across C-states. No reload needed.
- **SST_TF_INFO_0 FEATURE_SUPPORTED**: Must be 1 at runtime for the feature to be active. Set by PrimeCode based on fuse availability.

---

## Section 4: Programming Model

SST-TF enabling follows a multi-stage programming sequence spanning firmware reset, BIOS CPL3, and OS runtime. Each stage has specific responsibilities and constraints.

### Stage 1: Firmware Reset (PH5) — TPMI Population

PrimeCode populates SST-TF TPMI registers from fuses **before BIOS handoff**:

| Register | Populated From | Content |
|----------|----------------|---------|
| SST_TF_INFO_0 | SST_TF_CONFIG fuse array | LP_CLIP_RATIO_0..5 (6 CDYN levels) + FEATURE_SUPPORTED bit |
| SST_TF_INFO_2 | SST_TF_CONFIG fuse array | HP TRL bucket 0: 6 ratios (SSE through AVX512 CDYN) |
| SST_TF_INFO_4 | SST_TF_CONFIG fuse array | HP TRL bucket 1: 6 ratios |
| SST_TF_INFO_6 | SST_TF_CONFIG fuse array | HP TRL bucket 2: 6 ratios |
| SST_TF_INFO_8 | SST_TF_CONFIG fuse array | HP bucket core-count thresholds (requires feature_revision >= 2) |

**Constraints:**
- Registers are **read-only** after PH5 — BIOS/OS cannot modify TRL values.
- LP_CLIP_RATIO must be **monotonically non-increasing** across CDYN levels (higher CDYN = lower ratio).
- HP TRL must **exceed** LP_CLIP_RATIO for the same CDYN level.

### Stage 2: BIOS CPL3 — Feature Enable & CLOS Assignment

At CPL3, BIOS enables SST-TF and assigns cores to HP/LP groups:

**Step 2a — Read feature capability:**
```
Read SST_TF_INFO_0.FEATURE_SUPPORTED
  If == 0: SST-TF not fused; skip remaining steps
  If == 1: Proceed with enabling
```

**Step 2b — Program CLOS assignments:**
```
For each core in HP set (from DLCP fuse mask):
    Write SST_CLOS_ASSOC_<core> = 0   // CLOS[0] = HP
For each core in LP set (all others):
    Write SST_CLOS_ASSOC_<core> = 3   // CLOS[3] = LP
```

**Step 2c — Enable SST-TF:**
```
Write SST_PP_CONTROL.feature_state[1] = 1
```

**NWP constraint:** HP core selection is **DLCP fuse-pinned** — BIOS reads the HP core mask from fuses; OS cannot reassign cores between HP/LP at runtime.

### Stage 3: PCode Runtime — TRL Table Loading

PCode `SstManager` detects `feature_state[1]` change in the **slow loop** (~1 ms period):

```
On feature_state[1] transition 0→1:
    TrlManager.load_hp_clos_trl()   // Load HP TRL from SST_TF_INFO_2/4/6
    TrlManager.load_lp_clos_trl()   // Load LP clip from SST_TF_INFO_0
    Update MSR 0x1AD with HP TRL ratios

On feature_state[1] transition 1→0:
    TrlManager.restore_legacy_trl() // Revert to non-SST-TF TRL
```

**Latency:** 1+ slow-loop cycles before TRL tables are active after enable/disable.

### Stage 4: OS Runtime — Dynamic Control (Optional)

OS can toggle SST-TF at runtime via TPMI:

| Action | Programming Sequence | Latency |
|--------|---------------------|---------|
| Disable SST-TF | Write `SST_PP_CONTROL.feature_state[1] = 0` | 1+ slow-loop (~1 ms) |
| Re-enable SST-TF | Write `SST_PP_CONTROL.feature_state[1] = 1` | 1+ slow-loop (~1 ms) |
| Read current TRL | Read MSR 0x1AD | Immediate |

**Note:** MSR 0x1AD is writable by OS ring-0, but PCode **reconciles TPMI TRL on each slow loop** — MSR writes do not persist.

### Deprecated Features (ZBB)

On NWP, the following SST sub-features are **deprecated and must remain disabled**:

| Feature | TPMI Control | Required State |
|---------|--------------|----------------|
| SST-PP (Performance Profile) | SST_PP_CONTROL.pp_support | 0 |
| SST-CP (Core Power) | SST_CP_CONTROL.feature_state | 0 |
| SST-BF (Base Frequency) | SST_BF_CONTROL.feature_state | 0 |

BIOS/OS must not enable these; firmware ignores or rejects writes to these control bits.

---

## Section 5: Operational Behavior

| Scenario | Expected Behavior |
|----------|-------------------|
| Cold boot (TF fuse present) | SST_TF_INFO_0..8 populated by PrimeCode at PH5. FEATURE_SUPPORTED=1. |
| BIOS enable at CPL3 | feature_state[1]=1; CLOS_ASSOC programmed; TRL tables loaded by PCode slow loop. |
| HP core workload | Operates at HP TRL ratio (~P0max). MSR 0x1AD reflects SST_TF_INFO_2.hp_trl_ratio_0. |
| LP core workload | Frequency clipped to LP_CLIP_RATIO_0 (SSE). Higher CDYN = lower LP clip ratio. |
| OS disables TF at runtime | feature_state[1]=0; 1+ slow-loop latency; TRL reverts to legacy_trl or sst_pp_trl. |
| Deprecated features (SST-PP/CP/BF) | All disabled on NWP. TPMI feature bits = 0. ZBB negative TC verifies no MCA on disable. |

---

## Section 6: Corner Cases & Error Handling

- **CLOS ID coverage (TC 22022422202 -- REJECTED)**: TC was meant to verify any CLOS ID honors TRL. Rejected for NWP because NWP uses DLCP-pinned HP cores (fixed CLOS assignment via fuse mask). Testing arbitrary CLOS assignments conflicts with DLCP mode. Consider re-opening as a negative test.
- **LP clip ratio ordering**: Each CDYN level must be monotonically non-increasing. PrimeCode validates this at PH5; silicon test should verify TPMI reflects correct ordering.
- **feature_revision check**: SST_TF_INFO_8 (HP bucket core-counts) is only valid when `feature_revision >= 2`. TC should check feature_revision before reading INFO_8.
- **Slow-loop race**: feature_state change takes 1+ slow-loop cycles to propagate to TRL tables. Tests must add a polling wait (not a fixed sleep) before checking MSR 0x1AD.
- **SST-TF absent (no fuse)**: If SST_TF_INFO_0.FEATURE_SUPPORTED == 0, TC should log as "not supported" and exit gracefully, not fail.

---

## Section 7: Security / Safety / Policy

- SST-TF is controlled via TPMI (OS-accessible). Malformed CLOS assignments could cause unexpected frequency behavior -- PCode sanitizes CLOS values before use.
- Deprecated SST-PP/CP/BF TPMI writes must be rejected or ignored by firmware.
- MSR 0x1AD is writable by OS ring-0; PCode reconciles with TPMI TRL on each slow loop. Write should not persist beyond slow-loop.

---

## Section 8: References

- [SST Feature KB -- tf.md](../../../pm_features/sst/tf.md)
- [SST Intel HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html)
- [NWP PM MAS -- SST-TF section](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [PCT KB -- TCD 22022420855](TCD_22022420855_pct_enabling_discovery.md)
- [Parent TCD HSD 22022420925](https://hsdes.intel.com/appstore/article-one/#/22022420925)
