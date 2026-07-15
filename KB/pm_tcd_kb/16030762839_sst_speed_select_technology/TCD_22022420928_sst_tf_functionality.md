# TCD 22022420928 -- SST-TF Functionality

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420928](https://hsdes.intel.com/appstore/article-one/#/22022420928) |
| **Title** | SST-TF Functionality |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030762937 -- NWP PM SST-TF (Turbo Frequency)](https://hsdes.intel.com/appstore/article-one/#/16030762937) |
| **Child TCs** | [22022422212](https://hsdes.intel.com/appstore/article-one/#/22022422212) -- All HP cores in C6 (VP, open)<br>[22022422216](https://hsdes.intel.com/appstore/article-one/#/22022422216) -- Validate all TF buckets, no power limit (silicon+VP, open)<br>[16030715704](https://hsdes.intel.com/appstore/article-one/#/16030715704) -- PSS All Cores HP CLOS0/1 (open)<br>[16030715706](https://hsdes.intel.com/appstore/article-one/#/16030715706) -- PSS All Cores LP CLOS2/3 (open)<br>[16030715710](https://hsdes.intel.com/appstore/article-one/#/16030715710) -- PSS Dynamic Enable/Disable (open)<br>[22022422205](https://hsdes.intel.com/appstore/article-one/#/22022422205) -- All CLOS0/1 HP (rejected)<br>[22022422207](https://hsdes.intel.com/appstore/article-one/#/22022422207) -- All CLOS2/3 LP (rejected)<br>[22022422214](https://hsdes.intel.com/appstore/article-one/#/22022422214) -- HP cores in C6 emulation (rejected)<br>[22022422215](https://hsdes.intel.com/appstore/article-one/#/22022422215) -- Randomize CLOS groups (rejected) |
| **KB last updated** | 2026-07-15 |

---

## Section 1: Architecture / Micro-architecture and Functionality

**SST-TF Functionality** covers the runtime behavior of HP (high priority) and LP (low priority) core frequency enforcement once SST-TF is enabled. With TF enabled, HP cores (CLOS[0]) operate at an elevated TRL (~P0max), while LP cores (CLOS[3]) are clipped to LP_CLIP_RATIO. PCode enforces these limits via the TrlManager and 4 TRL tables (legacy, sst_pp, hp_clos, lp_clos).

<!-- raw-html -->
<div style="margin:16px 0;border:1px solid #bfcfe8;border-radius:8px;overflow:hidden;font-family:'Segoe UI',Arial,sans-serif;font-size:12px;">
  <div style="background:#0f4c81;color:#fff;padding:8px 16px;font-weight:700;font-size:12px;">SST-TF Runtime Frequency Enforcement</div>
  <div style="padding:16px 20px;background:#f8fafc;">
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:14px;">
      <div style="flex:1;min-width:200px;background:#e8f5e9;border:2px solid #2e7d32;border-radius:6px;padding:10px 12px;">
        <div style="font-weight:700;color:#2e7d32;font-size:11px;margin-bottom:5px;">HP Cores (CLOS[0])</div>
        <div style="font-size:10px;color:#333;line-height:1.8;">
          &#8226; Freq = HP TRL ratio (P0max ~4.4 GHz)<br>
          &#8226; TRL from SST_TF_INFO_2..7 (3 buckets)<br>
          &#8226; Bucket selected by active HP core count<br>
          &#8226; Must be in C0 to benefit from HP TRL<br>
          &#8226; When in C6: LP cores still clipped &#10003;
        </div>
      </div>
      <div style="flex:1;min-width:200px;background:#fff3e0;border:2px solid #e65100;border-radius:6px;padding:10px 12px;">
        <div style="font-weight:700;color:#e65100;font-size:11px;margin-bottom:5px;">LP Cores (CLOS[3])</div>
        <div style="font-size:10px;color:#333;line-height:1.8;">
          &#8226; Freq = LP_CLIP_RATIO (per CDYN, from SST_TF_INFO_0)<br>
          &#8226; Always clipped regardless of HP core state<br>
          &#8226; LP clip &ge; P1 (never goes below min turbo)<br>
          &#8226; 6 LP clip values (one per CDYN level)<br>
          &#8226; Enforced even when all HP cores in C6
        </div>
      </div>
    </div>
    <div style="background:#e8eaf6;border:1px solid #3949ab;border-radius:5px;padding:8px 12px;font-size:11px;margin-bottom:10px;">
      <strong>3 TF Buckets:</strong> bucket = f(active HP core count). Higher bucket index = fewer HP cores active = higher per-core TRL.
      &nbsp; SST_TF_INFO_2 (bucket 0) &rarr; SST_TF_INFO_4 (bucket 1) &rarr; SST_TF_INFO_6 (bucket 2).
    </div>
    <div style="background:#fff8e1;border:1px solid #f9a825;border-radius:5px;padding:8px 12px;font-size:11px;">
      <strong>Key functional invariant:</strong> LP clip is enforced by PCode regardless of HP core state.
      Even when all HP cores are in C6, LP cores must not exceed LP_CLIP_RATIO.
      This is validated by TC 22022422212.
    </div>
  </div>
</div>
<!-- /raw-html -->

### Key Concepts

| Concept | Description |
|---------|-------------|
| **TF Bucket** | Core-count-dependent TRL tier. 3 buckets: fewer active HP cores = higher per-core TRL ceiling. |
| **HP TRL** | Elevated turbo ratio limit for CLOS[0] cores. Sourced from SST_TF_INFO_2/4/6 per CDYN level. |
| **LP Clip** | LP_CLIP_RATIO from SST_TF_INFO_0. Applied per CDYN level. Cannot exceed this regardless of bucket. |
| **CLOS assignment** | HP=CLOS[0], LP=CLOS[3]. Set by BIOS in SST_CLOS_ASSOC registers. |
| **All-HP scenario** | All cores in CLOS[0]: entire system operates at HP TRL. Bucket 0 (most cores active). |
| **All-LP scenario** | All cores in CLOS[3]: entire system at LP clip. Validates LP enforcement floor. |
| **HP-in-C6 scenario** | HP cores idle in C6 while LP cores run: LP cores must still be clipped. Critical invariant. |
| **Power limit interaction** | Tests in this TCD run without power limiting (NOT power limited) to isolate TRL enforcement from throttling. |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Direction | Description |
|-----------|----------------|-----------|-------------|
| TPMI SST | SST_TF_INFO_0.lp_clip_ratio_0..5 | RO | LP clip ratios per CDYN (0=SSE .. 5=AMX). Enforced by PCode per-core. |
| TPMI SST | SST_TF_INFO_2/4/6 | RO | HP TRL ratios: bucket 0/1/2 x 6 CDYN levels. |
| TPMI SST | SST_CLOS_ASSOC_0..N | RW | Per-core CLOS assignment. BIOS sets HP=CLOS[0], LP=CLOS[3]. |
| TPMI SST | SST_PP_CONTROL.feature_state[1] | RW | SST-TF enable bit; toggle for dynamic enable/disable test. |
| MSR | 0x1AD (TURBO_RATIO_LIMIT) | RO | Active TRL for CDYN[0]/SSE; reflects HP TRL when TF enabled. |
| MSR | IA32_HWP_CAPABILITIES (per-core) | RO | HP cores: highest_perf = P0max; LP cores: highest_perf = LP clip. |
| PythonSV | sv.socket0.nio0.tpmi.sst_tf_info_0.lp_clip_ratio_0 | RO | LP clip for SSE |
| PythonSV | sv.socket0.nio0.tpmi.sst_clos_assoc_0 | RW | CLOS assignment for core group 0 |
| PythonSV | sv.socket0.cpu0.ia32_hwp_capabilities | RO | Highest perf field per core |

---

## Section 3: Reset / Power / Clocking

- **PH5**: PrimeCode initializes SST_TF_INFO_0..8 from fuses. LP and HP TRL values fixed.
- **CPL3 (BIOS)**: SST-TF enabled (`feature_state[1]=1`), CLOS_ASSOC programmed.
- **Runtime**: PCode TrlManager enforces HP and LP TRL per CDYN level on every workpoint calculation.
- **C-state interaction**: HP cores in C6 do not change LP clip enforcement. LP cores continue to be clipped.
- **Dynamic disable**: `feature_state[1]=0` reverts TRL tables to legacy_trl; 1+ slow-loop cycles latency.

---

## Section 4: Programming Model

### TC 22022422216: Validate all TF buckets without power limiting

```python
# Setup: SST-TF enabled, no RAPL limit active
import time
nio = sv.socket0.nio0

# Read bucket boundaries from TPMI
bucket0_trl = nio.tpmi.sst_tf_info_2.hp_trl_ratio_0  # SSE CDYN
bucket1_trl = nio.tpmi.sst_tf_info_4.hp_trl_ratio_0
bucket2_trl = nio.tpmi.sst_tf_info_6.hp_trl_ratio_0
assert bucket0_trl <= bucket1_trl <= bucket2_trl, "Buckets must be non-decreasing"

# Sweep: configure N HP cores, read achieved TRL from MSR 0x1AD
for n_hp in [all_cores, half_cores, few_cores]:
    configure_clos(hp_core_count=n_hp)
    time.sleep(0.1)
    actual_trl = sv.socket0.cpu0.ia32_primary_turbo_ratio_limit & 0xFF
    # Verify matches expected bucket
    expected = bucket_for_count(n_hp, bucket0_trl, bucket1_trl, bucket2_trl)
    assert actual_trl == expected
```

### TC 22022422212: All HP cores in C6 -- verify LP still clipped

```python
# Verify LP cores still clipped when all HP cores are idle in C6
lp_clip = nio.tpmi.sst_tf_info_0.lp_clip_ratio_0  # SSE clip

# Force all HP cores into C6 idle
force_hp_cores_c6()
time.sleep(0.1)  # allow C6 entry

# Run workload on LP cores, read their frequency
for lp_core in lp_cores:
    freq = get_core_frequency(lp_core)
    assert freq <= ratio_to_mhz(lp_clip), f"LP core {lp_core} exceeded clip: {freq} MHz"
```

### TC 16030715710 (PSS): Dynamic enable/disable

```python
# Enable SST-TF
nio.tpmi.sst_pp_control.feature_state.write(1)
time.sleep(0.02)  # wait 1+ slow-loop cycle
assert nio.tpmi.sst_pp_control.feature_state.read() == 1
# Verify HP TRL active
hp_trl = sv.socket0.cpu0.ia32_primary_turbo_ratio_limit & 0xFF
assert hp_trl == nio.tpmi.sst_tf_info_2.hp_trl_ratio_0

# Disable SST-TF
nio.tpmi.sst_pp_control.feature_state.write(0)
time.sleep(0.02)
# Verify legacy TRL restored
legacy_trl = sv.socket0.cpu0.ia32_primary_turbo_ratio_limit & 0xFF
assert legacy_trl < hp_trl, "Legacy TRL should be lower than HP TRL"
```

---

## Section 5: Operational Behavior

| Scenario | Expected Behavior |
|----------|-------------------|
| All cores HP (CLOS[0]) | MSR 0x1AD = HP TRL bucket 0 ratio. All cores can achieve P0max. |
| All cores LP (CLOS[3]) | All cores clipped to LP_CLIP_RATIO_0 (SSE). LP clip < HP TRL. |
| Mixed HP+LP, no power limit | HP cores at HP TRL; LP cores at LP clip. Verified per CDYN. |
| All HP cores idle (C6) | LP cores still clipped to LP_CLIP_RATIO. Invariant: TF clip independent of HP C-state. |
| Bucket sweep | Reduce active HP core count: bucket index increases; higher per-core HP TRL. |
| SST-TF disabled at runtime | TRL reverts to legacy_trl within 1 slow loop. HP/LP distinction removed. |
| CDYN scaling | Higher CDYN (AVX3/TMUL/AMX): HP TRL decreases (power constrained). LP clip also decreases. Both tracked in TPMI per-register. |

---

## Section 6: Corner Cases & Error Handling

- **Rejected TCs (22022422205/07/15)**: All-HP, all-LP, and random CLOS assignment scenarios rejected because NWP uses DLCP-pinned CLOS assignments (fuse mask controls HP core positions). Testing arbitrary CLOS configurations does not reflect NWP production behavior.
- **Emulation TC rejected (22022422214)**: HP-in-C6 emulation variant rejected; covered by VP TC 22022422212.
- **CDYN alignment**: LP clip ratio 0 (SSE) is the binding limit for SSE workloads. AVX3/AMX workloads use ratios 3-5. Verify all 6 CDYN clips in the fuse sanity test.
- **Power limit interaction**: TF TRL enforcement can be masked by RAPL throttling. All functionality tests must disable RAPL limits or use sufficiently high PL1/PL2 to avoid interference.
- **Slow-loop latency on disable**: feature_state toggle is not instantaneous. Poll MSR 0x1AD to confirm revert rather than using a fixed sleep.

---

## Section 7: Security / Safety / Policy

- CLOS_ASSOC registers are OS-writable. Malicious reassignment of HP/LP roles is possible at ring-0. PCode does not validate CLOS assignments against fuse intent.
- LP clip enforcement is a PCode invariant. Even with malformed CLOS writes, LP cores must not exceed LP_CLIP_RATIO as long as TF is enabled.

---

## Section 8: References

- [SST Feature KB -- tf.md](../../../pm_features/sst/tf.md)
- [SST Intel HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html)
- [NWP PM MAS -- SST-TF section](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [Sibling TCD -- SST-TF Enabling & Discovery 22022420925](https://hsdes.intel.com/appstore/article-one/#/22022420925)
- [PCT KB -- TCD 22022420855](TCD_22022420855_pct_enabling_discovery.md)
