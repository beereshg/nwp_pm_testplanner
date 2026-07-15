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
<div style="margin:16px 0;border:1px solid #bfcfe8;border-radius:8px;overflow:hidden;font-family:'Segoe UI',Arial,sans-serif;font-size:11.5px;max-width:900px;">
  <div style="background:#1e3a5f;color:#fff;padding:10px 18px;font-weight:700;font-size:12px;letter-spacing:.5px;text-align:center;">
    NWP SST-TF / PCT Architecture &mdash; Full Stack
  </div>

  <!-- Layer 1: SW/Policy -->
  <div style="background:#f1f5f9;border-bottom:1px solid #cbd5e1;padding:10px 16px;">
    <div style="font-weight:700;color:#374151;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">Software / Policy Layer</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;font-size:10.5px;color:#374151;">
      <div style="background:#fff;border:1px solid #cbd5e1;border-radius:4px;padding:5px 10px;">BIOS / OS / VMM / Validation SW</div>
      <div style="background:#fff;border:1px solid #cbd5e1;border-radius:4px;padding:5px 10px;">Enables feature / profile</div>
      <div style="background:#fff;border:1px solid #cbd5e1;border-radius:4px;padding:5px 10px;">Programs SST-PP / PCT policy</div>
      <div style="background:#fff;border:1px solid #cbd5e1;border-radius:4px;padding:5px 10px;">Reads TPMI discovery / status</div>
      <div style="background:#fff;border:1px solid #cbd5e1;border-radius:4px;padding:5px 10px;">Programs CLOS_ASSOC / HP selection</div>
    </div>
  </div>
  <div style="text-align:center;background:#f8fafc;padding:3px 0;font-size:10px;color:#64748b;">&#11015; TPMI / control programming</div>

  <!-- Layer 2: TPMI -->
  <div style="background:#e0f2fe;border-bottom:1px solid #7dd3fc;padding:10px 16px;">
    <div style="font-weight:700;color:#0369a1;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">TPMI / Arch Discovery &amp; Control View</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:10.5px;">
      <div style="background:#fff;border:1px solid #bae6fd;border-radius:4px;padding:5px 9px;"><strong>SST_PP_CONTROL.feature_state[TF]</strong> &mdash; enable bit</div>
      <div style="background:#fff;border:1px solid #bae6fd;border-radius:4px;padding:5px 9px;"><strong>SST_CLOS_ASSOC_0..N</strong> &mdash; per-core HP/LP assignment</div>
      <div style="background:#fff;border:1px solid #bae6fd;border-radius:4px;padding:5px 9px;"><strong>SST_TF_INFO_0</strong> &mdash; LP clip ratios per CDYN (6 levels)</div>
      <div style="background:#fff;border:1px solid #bae6fd;border-radius:4px;padding:5px 9px;"><strong>SST_TF_INFO_2/4/6</strong> &mdash; HP TRL bucket0/1/2 x CDYN</div>
      <div style="background:#fff;border:1px solid #bae6fd;border-radius:4px;padding:5px 9px;"><strong>SST_TF_INFO_8</strong> &mdash; bucket boundaries / HP core-count thresholds</div>
      <div style="background:#fff;border:1px solid #bae6fd;border-radius:4px;padding:5px 9px;"><strong>SST_TF_INFO_101</strong> &mdash; QUALIFIED_MODULE_MASK (NWP DLCP/PCT)</div>
    </div>
  </div>
  <div style="text-align:center;background:#f8fafc;padding:3px 0;font-size:10px;color:#64748b;">&#11015; configuration / visibility</div>

  <!-- Layer 3: FW Policy -->
  <div style="background:#ede9fe;border-bottom:1px solid #c4b5fd;padding:10px 16px;">
    <div style="font-weight:700;color:#5b21b6;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">FW Policy / Resolution Layer &mdash; PCode / Punit</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <div style="flex:1;min-width:200px;">
        <div style="font-size:10px;font-weight:700;color:#5b21b6;margin-bottom:4px;">Inputs:</div>
        <div style="font-size:10px;color:#374151;line-height:1.8;background:#fff;border:1px solid #c4b5fd;border-radius:4px;padding:6px 10px;">
          Active SST-PP level &bull; SST-TF enable state<br>
          CLOS / HP-LP grouping &bull; Qualified module mask<br>
          TRL/TF tables / FACT / ISS / fuses<br>
          Active core count (C0/C1)<br>
          CDYN / license (SSE, AVX2, AVX3, AMX&hellip;)
        </div>
      </div>
      <div style="flex:1;min-width:200px;">
        <div style="font-size:10px;font-weight:700;color:#5b21b6;margin-bottom:4px;">Responsibilities:</div>
        <div style="font-size:10px;color:#374151;line-height:1.8;background:#fff;border:1px solid #c4b5fd;border-radius:4px;padding:6px 10px;">
          Own global TRL/FACT/ISS/SST-TF policy tables<br>
          Determine active HP bucket from HP core count<br>
          Resolve HP target row per CDYN/license<br>
          Resolve LP clipped row per CDYN/license<br>
          Update TPMI-visible state &bull; Program WP4
        </div>
      </div>
    </div>
  </div>
  <div style="text-align:center;background:#f8fafc;padding:3px 0;font-size:10px;color:#64748b;">&#11015; resolved per-priority workpoints</div>

  <!-- Layer 4: WP4 -->
  <div style="background:#fdf4ff;border-bottom:1px solid #e879f9;padding:10px 16px;">
    <div style="font-weight:700;color:#86198f;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">WP4 Generation / PUNIT Delivery Mechanism</div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px;font-size:10.5px;">
      <div style="background:#fff;border:1px solid #f0abfc;border-radius:4px;padding:6px 10px;"><strong>MASK_HIGH / MASK_LOW</strong><br><span style="font-size:10px;color:#555;">Identifies HP vs LP cores/modules</span></div>
      <div style="background:#fff;border:1px solid #f0abfc;border-radius:4px;padding:6px 10px;"><strong>WP4_HIGH_HP / WP4_LOW_HP</strong><br><span style="font-size:10px;color:#555;">Resolved HP freqs per CDYN/license</span></div>
      <div style="background:#fff;border:1px solid #f0abfc;border-radius:4px;padding:6px 10px;"><strong>WP4_HIGH_LP / WP4_LOW_LP</strong><br><span style="font-size:10px;color:#555;">Resolved LP clipped freqs per CDYN</span></div>
    </div>
    <div style="margin-top:6px;font-size:10px;color:#86198f;background:#fff;border:1px solid #f0abfc;border-radius:4px;padding:5px 10px;"><strong>GO command:</strong> ACP must not apply WP4 until corresponding GO_* arrives</div>
  </div>
  <div style="text-align:center;background:#f8fafc;padding:3px 0;font-size:10px;color:#64748b;">&#11015; masked WP4 writes + GO</div>

  <!-- Layer 5: ACP/Acode -->
  <div style="background:#fff7ed;border-bottom:1px solid #fed7aa;padding:10px 16px;">
    <div style="font-weight:700;color:#c2410c;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">ACP / Acode-Side Core PM Enforcement</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <div style="flex:1;min-width:160px;background:#fff;border:1px solid #fed7aa;border-radius:4px;padding:6px 10px;font-size:10.5px;">
        <strong>Receives:</strong><br>WP4 row for this core/group<br>GO command
      </div>
      <div style="flex:2;min-width:200px;background:#fff;border:1px solid #fed7aa;border-radius:4px;padding:6px 10px;font-size:10.5px;">
        <strong>Applies per CDYN/license:</strong><br>
        HP cores &rarr; resolved HP turbo ceiling<br>
        LP cores &rarr; resolved LP clip ceiling<br>
        <span style="font-size:10px;color:#92400e;">This is where policy becomes an enforceable per-core runtime limit.</span>
      </div>
    </div>
  </div>
  <div style="text-align:center;background:#f8fafc;padding:3px 0;font-size:10px;color:#64748b;">&#11015; runtime frequency limitation / turbo ceiling</div>

  <!-- Layer 6: Core Runtime -->
  <div style="background:#f0fdf4;border-bottom:1px solid #86efac;padding:10px 16px;">
    <div style="font-weight:700;color:#15803d;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">Core / Module Runtime Behavior</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <div style="flex:1;min-width:200px;background:#dcfce7;border:2px solid #16a34a;border-radius:5px;padding:8px 10px;font-size:10.5px;">
        <strong style="color:#15803d;">HP Cores (CLOS[0])</strong><br>
        Use HP TRL row &bull; Bucket by active HP count<br>
        Fewer HP active &rarr; higher bucket &rarr; higher ceiling
      </div>
      <div style="flex:1;min-width:200px;background:#fff7ed;border:2px solid #ea580c;border-radius:5px;padding:8px 10px;font-size:10.5px;">
        <strong style="color:#c2410c;">LP Cores (CLOS[3])</strong><br>
        Use LP clipped row &bull; Capped at LP_CLIP_RATIO per CDYN<br>
        Remain clipped even when HP cores in C6
      </div>
      <div style="flex:1;min-width:160px;background:#f0f9ff;border:1px solid #7dd3fc;border-radius:5px;padding:8px 10px;font-size:10px;color:#0369a1;">
        <strong>Observability:</strong><br>
        IA32_HWP_CAPABILITIES<br>MSR 0x1AD / TRL views<br>Perf counters
      </div>
    </div>
  </div>

  <!-- Bottom: Customer View -->
  <div style="background:#1e3a5f;padding:10px 16px;">
    <div style="font-weight:700;color:#e2e8f0;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">NWP Customer View: PCT vs SST-TF</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <div style="flex:1;min-width:200px;background:#0f4c81;border:1px solid #3b82f6;border-radius:5px;padding:8px 10px;font-size:10.5px;color:#e0f2fe;">
        <strong style="color:#93c5fd;">PCT (customer-facing policy)</strong><br>
        Selects / designates HP modules<br>Uses qualified-module mask<br>Defines who gets preferred turbo
      </div>
      <div style="flex:1;min-width:200px;background:#312e81;border:1px solid #818cf8;border-radius:5px;padding:8px 10px;font-size:10.5px;color:#e0e7ff;">
        <strong style="color:#a5b4fc;">SST-TF (enforcement mechanism)</strong><br>
        Provides HP turbo ratios<br>Provides LP clip ratios<br>Delivers differentiated ceilings via WP4/ACP
      </div>
      <div style="flex:1;min-width:180px;background:#1e3a5f;border:1px solid #60a5fa;border-radius:5px;padding:8px 10px;font-size:10px;color:#93c5fd;">
        <strong>FW-driven:</strong> profile, bucket, HP/LP rows, TPMI updates, WP4<br>
        <strong>Acode-driven:</strong> per-core ceiling enforcement at runtime
      </div>
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
