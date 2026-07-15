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

### Step 1: Verify TPMI registers populated from fuses (TC 22022422200, PSS 16030715714/16)

```python
# Check SST_TF_INFO_0 -- LP clip ratios
skt = sv.socket0
nio = skt.nio0  # NWP single NIO
assert nio.tpmi.sst_tf_info_0.feature_supported == 1, "SST-TF not enabled in fuses"
lp_clip = nio.tpmi.sst_tf_info_0.lp_clip_ratio_0
assert lp_clip > 0, "LP clip ratio not populated"
# Check monotonically non-increasing across CDYN levels (higher CDYN = lower ratio)
ratios = [nio.tpmi.sst_tf_info_0.read_field(f"lp_clip_ratio_{i}") for i in range(6)]
for i in range(len(ratios)-1):
    assert ratios[i] >= ratios[i+1], f"LP ratios not monotonic at CDYN[{i}]"

# Check SST_TF_INFO_2 -- HP TRL bucket 0 (SSE)
hp_trl = nio.tpmi.sst_tf_info_2.hp_trl_ratio_0
assert hp_trl > lp_clip, "HP TRL must exceed LP clip ratio"
```

### Step 2: Dynamic enable/disable via TPMI (TC 22022422201)

```python
# Enable SST-TF
nio.tpmi.sst_pp_control.feature_state.write(1)  # bit[1]=1
# Wait 1 slow loop cycle (~10ms), then verify TRL reload
import time; time.sleep(0.02)
# Verify HP TRL now active in MSR 0x1AD
hp_trl_msr = sv.socket0.cpu0.ia32_primary_turbo_ratio_limit  # MSR 0x1AD
hp_trl_tpmi = nio.tpmi.sst_tf_info_2.hp_trl_ratio_0
assert hp_trl_msr & 0xFF == hp_trl_tpmi, "MSR 0x1AD not updated from SST_TF_INFO_2"

# Disable SST-TF
nio.tpmi.sst_pp_control.feature_state.write(0)
time.sleep(0.02)
# Verify legacy TRL restored
```

### ZBB deprecated features (TC 16030715662)

```python
# SST-PP, SST-CP, SST-BF must be disabled on NWP
assert nio.tpmi.sst_pp_control.pp_support == 0, "SST-PP must be disabled (ZBB)"
# Check SST-CP: BLOS/IBT field
assert nio.tpmi.sst_cp_control.feature_state == 0, "SST-CP must be disabled (ZBB)"
```

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
