# TCD 22022420858 -- PCT Functionality

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420858](https://hsdes.intel.com/appstore/article-one/#/22022420858) |
| **Title** | PCT - Functionality |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030762939 -- NWP PM PCT (Priority Core Turbo)](https://hsdes.intel.com/appstore/article-one/#/16030762939) |
| **Scope distinct from** | TCD 22022420855 (PCT - Enabling & Discovery) |
| **Child TCs** | [22022422104](https://hsdes.intel.com/appstore/article-one/#/22022422104) -- All HP in C6 (VP)<br>[22022422105](https://hsdes.intel.com/appstore/article-one/#/22022422105) -- Default HP selection (VP)<br>[22022422110](https://hsdes.intel.com/appstore/article-one/#/22022422110) -- SST-PP x PCT (rejected)<br>[22022422116](https://hsdes.intel.com/appstore/article-one/#/22022422116) -- Turbo freq check (VP)<br>[22022422117](https://hsdes.intel.com/appstore/article-one/#/22022422117) -- TDP convergence (VP)<br>[16030715676](https://hsdes.intel.com/appstore/article-one/#/16030715676) -- PSS All HP in C6<br>[16030715680](https://hsdes.intel.com/appstore/article-one/#/16030715680) -- PSS BIOS Negative<br>[16030715684](https://hsdes.intel.com/appstore/article-one/#/16030715684) -- PSS Default Disabled<br>[16030715686](https://hsdes.intel.com/appstore/article-one/#/16030715686) -- PSS Default HP selection<br>[16030715692](https://hsdes.intel.com/appstore/article-one/#/16030715692) -- PSS Turbo freq check<br>[16030715694](https://hsdes.intel.com/appstore/article-one/#/16030715694) -- PSS enable/disable<br>[16030717717](https://hsdes.intel.com/appstore/article-one/#/16030717717) -- PV Custom Config<br>[16030717718](https://hsdes.intel.com/appstore/article-one/#/16030717718) -- PV Partition Sweep<br>[16030717719](https://hsdes.intel.com/appstore/article-one/#/16030717719) -- PV PCT Disable<br>[16030768619](https://hsdes.intel.com/appstore/article-one/#/16030768619) -- Default Enabled<br>[16030768620](https://hsdes.intel.com/appstore/article-one/#/16030768620) -- TPMI runtime enable/disable<br>[16030768621](https://hsdes.intel.com/appstore/article-one/#/16030768621) -- TPMI runtime negative |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Architecture / Micro-architecture and Functionality

PCT Functionality covers the **runtime enforcement** of HP/LP frequency ceilings once PCT is enabled. The key invariants are: (1) HP cores operate at HP TRL ceiling; (2) LP cores are always clipped regardless of HP state; (3) under RAPL PL1, LP is throttled first (Ordered Throttle). PCT uses the SST-TF CLOS infrastructure unchanged -- no PCT-specific PCode logic beyond the standard SST-TF flow.

<!-- raw-html -->
<div style="margin:16px 0;border:1px solid #bfcfe8;border-radius:8px;overflow:hidden;font-family:'Segoe UI',Arial,sans-serif;font-size:11.5px;max-width:900px;">
  <div style="background:#1e3a5f;color:#fff;padding:10px 18px;font-weight:700;font-size:12px;letter-spacing:.5px;text-align:center;">
    PCT Runtime Functional Flow -- HP/LP Enforcement &amp; Ordered Throttling
  </div>

  <!-- FW Policy layer -->
  <div style="background:#ede9fe;border-bottom:1px solid #c4b5fd;padding:10px 16px;">
    <div style="font-weight:700;color:#5b21b6;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;">PCode / Punit -- Per-Cycle Resolution</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <div style="flex:1;min-width:170px;background:#fff;border:1px solid #c4b5fd;border-radius:4px;padding:7px 10px;font-size:10px;line-height:1.8;">
        <strong>Inputs per cycle:</strong><br>
        Active HP core count (C0/C1)<br>
        CDYN / license (SSE/AVX2/AVX3/AMX)<br>
        SST_TF_INFO_2 (HP TRL ratios)<br>
        SST_TF_INFO_0 (LP clip ratios)<br>
        RAPL PL1 budget
      </div>
      <div style="flex:1;min-width:170px;background:#fff;border:1px solid #c4b5fd;border-radius:4px;padding:7px 10px;font-size:10px;line-height:1.8;">
        <strong>Resolution:</strong><br>
        Select HP bucket (by HP core count)<br>
        WP4_HP = HP TRL for current CDYN<br>
        WP4_LP = LP_CLIP for current CDYN<br>
        Apply Ordered Throttle if power limited
      </div>
      <div style="flex:1;min-width:170px;background:#fff3e0;border:2px solid #e65100;border-radius:4px;padding:7px 10px;font-size:10px;line-height:1.8;">
        <strong>Ordered Throttle (PRIORITY_TYPE=1):</strong><br>
        Phase A: LP frequency &darr; first<br>
        Phase B: HP maintained while LP &gt; min<br>
        Phase C: HP &darr; only if LP at minimum<br>
        <span style="color:#c2410c;font-weight:600;">LP always reduced before HP</span>
      </div>
    </div>
  </div>
  <div style="text-align:center;background:#f8fafc;padding:3px 0;font-size:10px;color:#64748b;">&#11015; WP4_HP and WP4_LP per CLOS group</div>

  <!-- WP4 layer -->
  <div style="background:#fdf4ff;border-bottom:1px solid #e879f9;padding:8px 16px;">
    <div style="font-weight:700;color:#86198f;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">WP4 Broadcast via PMSB Sideband</div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;font-size:10.5px;">
      <div style="background:#fff;border:1px solid #f0abfc;border-radius:4px;padding:5px 10px;flex:1;min-width:140px;"><strong>WP4 for HP (CLOS[0/1])</strong><br><span style="font-size:10px;color:#555;">HP TRL ceiling per CDYN<br>~4.4 GHz on NWP</span></div>
      <div style="background:#fff;border:1px solid #f0abfc;border-radius:4px;padding:5px 10px;flex:1;min-width:140px;"><strong>WP4 for LP (CLOS[2/3])</strong><br><span style="font-size:10px;color:#555;">LP clip ceiling per CDYN<br>~P1 on NWP</span></div>
      <div style="background:#fff;border:1px solid #f0abfc;border-radius:4px;padding:5px 10px;flex:1;min-width:180px;"><strong>MASK_HIGH / MASK_LOW</strong><br><span style="font-size:10px;color:#555;">Identifies which cores get WP4_HP vs WP4_LP<br>Based on CLOS_ASSOC (std) or fuse (DLCP)</span></div>
    </div>
  </div>
  <div style="text-align:center;background:#f8fafc;padding:3px 0;font-size:10px;color:#64748b;">&#11015; ACP / Acode applies per-core ceiling</div>

  <!-- Core Runtime -->
  <div style="background:#f0fdf4;border-bottom:1px solid #86efac;padding:10px 16px;">
    <div style="font-weight:700;color:#15803d;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;">Core Runtime Behavior (2 CBBs &times; 48 cores = 96 total on NWP)</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <div style="flex:1;min-width:200px;background:#dcfce7;border:2px solid #16a34a;border-radius:5px;padding:8px 10px;font-size:10.5px;">
        <strong style="color:#15803d;">HP Cores -- ~8 cores (CLOS[0])</strong><br>
        Ceiling: HP TRL ~4.4 GHz per CDYN<br>
        Bucket: f(active HP count) -- 3 buckets<br>
        HWP_CAP.highest_perf = P0max<br>
        In C6: <em>LP cores still clipped</em>
      </div>
      <div style="flex:1;min-width:200px;background:#fff7ed;border:2px solid #ea580c;border-radius:5px;padding:8px 10px;font-size:10.5px;">
        <strong style="color:#c2410c;">LP Cores -- ~88 cores (CLOS[3])</strong><br>
        Ceiling: LP_CLIP ~P1 per CDYN<br>
        <strong>Always clipped -- even when all HP in C6</strong><br>
        HWP_CAP.highest_perf = LP clip<br>
        Throttled first under RAPL PL1
      </div>
    </div>
    <div style="margin-top:8px;background:#fef9c3;border:1px solid #ca8a04;border-radius:5px;padding:7px 12px;font-size:10px;color:#713f12;">
      <strong>Key functional invariant:</strong> LP ceiling is enforced by CLOS_CONFIG[3].max regardless of HP core state.
      All HP cores in C6 does NOT release the LP clip. Verified by TC 22022422104 and [PSS] 16030715676.
    </div>
  </div>

  <!-- Frequency hierarchy -->
  <div style="background:#f8fafc;padding:10px 16px;">
    <div style="font-weight:700;color:#374151;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;">Frequency Hierarchy (NWP Values)</div>
    <div style="display:flex;gap:6px;align-items:flex-end;flex-wrap:wrap;">
      <div style="background:#16a34a;color:#fff;border-radius:4px;padding:5px 10px;text-align:center;font-size:10px;min-width:100px;"><strong>P0max / F3</strong><br>~4.4 GHz<br>HP cores</div>
      <div style="background:#64748b;color:#fff;border-radius:4px;padding:5px 10px;text-align:center;font-size:10px;min-width:100px;opacity:.7;"><strong>P0half</strong><br>~3.9 GHz<br>(not used with PCT)</div>
      <div style="background:#64748b;color:#fff;border-radius:4px;padding:5px 10px;text-align:center;font-size:10px;min-width:100px;opacity:.6;"><strong>P0n</strong><br>~3.6 GHz<br>(all-core, no PCT)</div>
      <div style="background:#ea580c;color:#fff;border-radius:4px;padding:5px 10px;text-align:center;font-size:10px;min-width:100px;"><strong>F2 / LP_CLIP</strong><br>~P1 ~2.3 GHz<br>LP cores clipped here</div>
      <div style="background:#374151;color:#fff;border-radius:4px;padding:5px 10px;text-align:center;font-size:10px;min-width:80px;opacity:.6;"><strong>P1 / Pn</strong><br>Floor</div>
    </div>
  </div>
</div>
<!-- /raw-html -->

### Key Concepts

| Concept | Description |
|---------|-------------|
| **LP always clipped** | CLOS_CONFIG[3].max enforces LP ceiling regardless of HP C-state. Critical invariant tested by TC 22022422104. |
| **Ordered Throttle** | SST_CP_PRIORITY_TYPE=1 — three phases under RAPL PL1: (A) LP frequency drops first; (B) HP maintained at PCT TRL while LP still has headroom; (C) **HP is throttled when LP is already at its minimum floor and PL1 is still exceeded**. HP throttle is deferred — not prevented. |
| **HP bucket** | 3 buckets; higher bucket = fewer active HP cores = higher per-core HP TRL. |
| **Default disabled (NWP)** | PctHpModuleCount=0 at boot. No CLOS differentiation; conventional turbo only. |
| **Default enabled (GNR fuse)** | CAPID4.bit29=1 auto-enables PCT; validated by TC 16030768619 (not NWP POR). |
| **TPMI runtime toggle** | SST_PP_CONTROL.feature_state[1] writable at runtime via Intel SST tool. |
| **SST-PP x PCT (rejected)** | TC 22022422110 rejected; SST-PP switching is a separate NWP validation scope. |

### NWP Topology

- CBBs: 2 (cbb0, cbb1) -- loop `range(2)`
- Cores per CBB: 48 (24 DCMs x 2 PNC cores) -- loop `range(48)`
- Total cores: 96 -- HP: ~8 (CLOS[0]), LP: ~88 (CLOS[3])
- PCT frequency target: ~4.4 GHz (POR-1); turbo frequency check must use NWP value, not GNR 4.6 GHz
- RAPL PL1 register: TPMI SOCKET_RAPL_PL1_CONTROL (MSR 0x610/0x638 deprecated on DMR/NWP)
- SST-BF: ZBB on NWP -- DQ mutex tests verify no interference, not active conflict

---

## Section 2: Interfaces and Protocols

| Interface | Register | Direction | Functional Purpose |
|-----------|----------|-----------|--------------------|
| TPMI | SST_CLOS_CONFIG[0].max | RW | HP frequency ceiling = SST_TF_INFO_2.RATIO_0 |
| TPMI | SST_CLOS_CONFIG[3].max | RW | LP clip ceiling = SST_TF_INFO_0.LP_CLIP_RATIO_0 |
| TPMI | SST_CP_CONTROL.priority_type | RW | 1 = Ordered Throttle (LP first) |
| TPMI | SST_CP_CONTROL.sst_cp_enable | RW | PCT globally enabled |
| TPMI | SST_CLOS_ASSOC_0..N | RW | Per-core: HP=CLOS[0], LP=CLOS[3] |
| TPMI | SST_PP_CONTROL.feature_state[1] | RW | SST-TF active; runtime toggle target |
| MSR | IA32_HWP_CAPABILITIES (0x771) | RO | HP: highest_perf=P0max; LP: highest_perf=LP_clip (DLCP) |
| MSR | IA32_PERF_STATUS (0x198) | RO | Current ratio; HP should show ~4.4 GHz, LP at clip |
| MSR | 0x1AD PRIMARY_TURBO_RATIO_LIMIT | RO | HP TRL broadcast; must = SST_TF_INFO_2.RATIO_0 |
| TPMI | SST_TF_INFO_0.lp_clip_ratio_0 | RO | LP clip source value (from fuse via PH5) |
| TPMI | SST_TF_INFO_2.ratio_0 | RO | HP TRL source value (from fuse via PH5) |
| NVRAM | PctHpModuleCount | -- | 0 = PCT disabled; N = N HP modules enabled |
| PythonSV | sv.socket0.nio0.tpmi.sst_clos_config_0 | RW | HP CLOS ceiling config |
| PythonSV | sv.socket0.cpu0.ia32_hwp_capabilities | RO | Per-core HP/LP frequency reporting |

---

## Section 3: Reset / Power / Clocking

- **Phase 5 (PrimeCode)**: Fuses read; SST_TF_INFO_0/2 populated. HP TRL and LP clip values fixed before BIOS.
- **CPL3 (BIOS)**: Programs CLOS_CONFIG[0/3], CLOS_ASSOC, SST_CP_CONTROL.priority_type=1, SST_PP_CONTROL.feature_state[1]=1. All functionality tests assume this precondition complete.
- **Runtime**: PCode slow loop (1ms RAPL PID) computes WP4_HP/LP per CDYN and broadcasts via PMSB. Ordered throttle kicks in when socket power exceeds PL1: LP frequency reduces first (Phase A/B); if budget is still exceeded after LP reaches its minimum floor, HP frequency is then reduced (Phase C). HP is throttled last — not exempt.
- **TPMI runtime toggle**: SST_PP_CONTROL.feature_state[1] can be toggled at runtime via Intel SST tool. PCode reacts within 1 slow-loop cycle; HWP_CAPABILITY.highest_perf updates per core.
- **C-state interaction**: HP cores in C6 do NOT release LP clip. LP cores remain at CLOS_CONFIG[3].max ceiling. Power freed by HP C6 is not redistributed to LP.

---

## Section 4: Programming Model

### Preconditions (Enabling -- see TCD 22022420855)

| Step | Actor | Register | Value |
|------|-------|----------|-------|
| 1 | PrimeCode PH5 | SST_TF_INFO_0/2 | LP clip / HP TRL from fuse |
| 2 | BIOS CPL3 | SST_CLOS_CONFIG[0].max | = SST_TF_INFO_2.ratio_0 |
| 3 | BIOS CPL3 | SST_CLOS_CONFIG[3].max | = SST_TF_INFO_0.lp_clip_ratio_0 |
| 4 | BIOS CPL3 | SST_CP_CONTROL.priority_type | = 1 |
| 5 | BIOS CPL3 | SST_CLOS_ASSOC[core] | HP=CLOS[0], LP=CLOS[3] |
| 6 | BIOS CPL3 | SST_PP_CONTROL.feature_state[1] | = 1 |

### TC 22022422116 / 16030715692: Turbo frequency check

```python
nio = sv.socket0.nio0
hp_trl = nio.tpmi.sst_tf_info_2.ratio_0
lp_clip = nio.tpmi.sst_tf_info_0.lp_clip_ratio_0

for cbb_idx in range(2):
    for core_idx in range(48):
        core = sv.socket0.getbypath(f"cbb{cbb_idx}.compute0.module{core_idx//2}.core{core_idx%2}")
        hwp_high = core.ia32_hwp_capabilities.highest_performance
        clos = sv.socket0.nio0.tpmi.sst_clos_assoc.read_field(f"clos_{core_idx}")
        if clos == 0:  # HP
            assert hwp_high == hp_trl, f"HP core {core_idx} expected {hp_trl}, got {hwp_high}"
        else:          # LP
            assert hwp_high == lp_clip, f"LP core {core_idx} expected {lp_clip}, got {hwp_high}"
```

### TC 22022422104 / 16030715676: All HP cores in C6 -- LP still clipped

```python
# Force all HP cores into C6
for hp_core in hp_cores:
    hp_core.force_c6()

import time; time.sleep(0.1)  # wait for C6 entry

# Verify LP cores not exceeding clip
for lp_core in lp_cores:
    freq = lp_core.ia32_perf_status & 0xFF
    assert freq <= lp_clip, f"LP core exceeded clip ({freq} > {lp_clip}) when all HP in C6"
```

### TC 22022422117: TDP convergence (Ordered Throttle)

```python
# Set RAPL PL1 below current power draw to trigger throttle
set_rapl_pl1(low_limit)
time.sleep(0.2)  # allow throttle to take effect

# Verify LP frequency dropped before HP
lp_ratios = [get_core_ratio(c) for c in lp_cores]
hp_ratios = [get_core_ratio(c) for c in hp_cores]

# LP must be at or near clip minimum before HP starts dropping
assert min(lp_ratios) < lp_clip, "LP not throttled yet"
assert min(hp_ratios) >= hp_trl * 0.9, "HP throttled before LP exhausted"
```

### TC (TBD): PCT × RAPL — Phase C HP throttle under severe power limit

Covers the regime where PL1 is set so aggressively that LP reaches its minimum floor and budget is still exceeded, forcing HP to throttle (Phase C). TC 22022422117 covers Phases A/B only.

```python
import time

# Set PL1 aggressively to force Phase C
nio = sv.socket0.nio0
hp_trl = nio.tpmi.sst_tf_info_2.ratio_0
lp_floor = nio.tpmi.sst_tf_info_0.lp_clip_ratio_0  # Pn; LP floor once LP_CLIP exhausted

severe_pl1_watts = get_tdp_watts() * 0.35  # ~35% TDP — forces Phase C on NWP
set_socket_rapl_pl1(severe_pl1_watts)       # TPMI SOCKET_RAPL_PL1_CONTROL
time.sleep(0.5)  # allow multiple 1ms PID cycles to converge

lp_ratios = [get_core_ratio(c) for c in lp_cores]
hp_ratios = [get_core_ratio(c) for c in hp_cores]

# Phase A/B invariant: LP must have reached floor before HP drops
assert max(lp_ratios) <= lp_floor + 1, \
    f"LP not at minimum floor (max={max(lp_ratios)}, floor={lp_floor}) before HP throttle"

# Phase C invariant: HP must have throttled below HP TRL
assert min(hp_ratios) < hp_trl, \
    f"HP did not throttle in Phase C (min={min(hp_ratios)}, trl={hp_trl})"

# Power convergence: socket power within 10% of PL1
socket_power = get_socket_power_watts()
assert abs(socket_power - severe_pl1_watts) / severe_pl1_watts < 0.10, \
    f"Power did not converge: {socket_power:.1f}W vs {severe_pl1_watts:.1f}W"

# Ordering check: HP drop must not precede LP reaching floor
# (verify via IA32_PERF_STATUS snapshot sequence across the throttle ramp)
```

### TC 16030768620: TPMI runtime enable/disable

```python
# Disable PCT
nio.tpmi.sst_pp_control.feature_state.write(0)
time.sleep(0.05)
# All cores should now have same highest_perf (conventional turbo)
perfs = [get_hwp_highest_perf(c) for c in all_cores]
assert len(set(perfs)) == 1, "All cores should have same perf when PCT disabled"

# Re-enable PCT
nio.tpmi.sst_pp_control.feature_state.write(1)
time.sleep(0.05)
hp_perf = get_hwp_highest_perf(hp_cores[0])
lp_perf = get_hwp_highest_perf(lp_cores[0])
assert hp_perf > lp_perf, "HP must have higher highest_perf than LP"
```

---

## Section 5: Operational Behavior

| Scenario | Expected Behavior | TC(s) |
|----------|-------------------|-------|
| Normal PCT active | HP at ~4.4 GHz; LP clipped at ~P1; HWP_CAP differs per core; runtime control writes verified complete via `SST_CP_CONTROL.HANDSHAKE` / `SST_CP_STATUS.LAST_HANDSHAKE` match | 22022422116, 16030715692 |
| All HP cores in C6 | LP cores still clipped at LP_CLIP -- invariant; **under PL1 pressure, verify LP clip maintained before HP throttles** (Co-Design finding #11, spec: ordered throttling + power-limited behavior) | 22022422104, 16030715676 |
| Default HP selection | 8 HP cores in CLOS[0]; first 2 per partition per CBB | 22022422105, 16030715686 |
| TDP convergence (Phase A/B) | LP drops first under RAPL PL1; HP TRL maintained while LP has headroom; **ordered throttle verified across all 4 CLOS groups: CLOS0 > CLOS1 > CLOS2 > CLOS3** (Co-Design finding #10, spec: ordered throttling section, Intel SST HAS) | 22022422117 |
| PCT × RAPL Phase C — HP throttle under severe limit | LP at minimum floor with PL1 still exceeded: HP drops below HP TRL; power converges to PL1 | *(TC TBD)* |
| PCT disabled (default) | SST_CP_ENABLE=0; all cores at conventional TRL; no HP/LP split | 16030715684 |
| PCT enabled automatically | feature_state[1]=1 at boot; HP/LP differentiation active | 16030768619 |
| TPMI runtime disable/enable | SST tool toggle; HWP_CAP updates within 1 slow-loop | 16030768620 |
| TPMI runtime negative | Invalid CLOS write rejected; illegal feature combo flagged | 16030768621 |
| BIOS negative | Invalid Partition Count rejected; default preserved | 16030715680 |
| PV partition sweep | All valid counts 0..max programmed; CLOS consistent | 16030717718 |
| PV custom config | User-specified HP positions; CLOS_ASSOC matches config | 16030717717 |
| PV PCT disable | Partition Count=0; conventional turbo; MSR 0x1AD not overridden | 16030717719 |
| SST-PP x PCT (rejected) | TC 22022422110 rejected -- SST-PP switching separate scope | -- |

---

## Section 6: Corner Cases & Error Handling

- **LP clip when all HP in C6**: CLOS_CONFIG[3].max is the HW-enforced ceiling. HP C6 does not release LP frequency. Test must verify LP frequency under load with HP forced idle.
- **TPMI negative -- feature_state=0 with CLOS set**: When PCT disabled at runtime, CLOS assignments persist in TPMI but HP/LP differentiation stops. Verify no residual frequency bias.
- **Default disabled on NWP/DMR**: Unlike GNR (CAPID4.bit29 auto-enables), NWP requires explicit BIOS opt-in (Partition Count > 0). TC 16030715684 verifies default-disabled state.
- **Default enabled (TC 16030768619)**: Tests GNR-style auto-enable. On NWP this TC is likely POR-irrelevant but validates the code path for platforms where CAPID4.bit29=1.
- **Partition count bounds**: Max HP = SST_TF_INFO_8.NUM_CORE_0 / MAX_LPIDS. BIOS must reject values above this. TC 16030715680 validates the rejection path.
- **SST-PP x PCT (TC 22022422110 rejected)**: Dynamic SST-PP switching while PCT active tested and rejected for NWP. SST-PP switching scope belongs to a separate TCD.
- **SST-BF conflict**: ZBB on NWP. DQ rules (TC 22022422118) verify no interference. Actual mutex not exercised.
- **Phase C — HP throttle under severe PL1** *(gap — TC TBD)*: TC 22022422117 verifies Phase A/B only — LP drops before HP, HP TRL preserved while LP has headroom. It does **not** cover Phase C: when PL1 is set aggressively low (≈30–50% TDP) and LP is already at its minimum floor, HP must throttle too. This regime has no TC. Candidate: new TC in this TCD targeting PL1 ≈ 35% TDP with PTAT on all 96 cores, verifying LP is at floor before HP drops and that power converges to PL1.
- **Runtime disable — stale `CLOS_ASSOC` with `SST_CP_ENABLE=0`** *(gap — TC TBD)*: TC 16030768620 covers runtime disable/enable via `feature_state` toggle. It does **not** explicitly verify that stale `CLOS_ASSOC` entries in TPMI do not cause misreporting after disable. After `SST_PP_CONTROL.feature_state[1]=0`: `CLOS_ASSOC[core]` entries persist in TPMI SRAM; `SST_CP_ENABLE` goes to 0; OS tools and `IA32_HWP_CAPABILITIES.highest_performance` must show no HP/LP differentiation despite stale assignment. Candidate: extend TC 16030768620 with an explicit stale-state negative assertion after disable.
- **Re-enable after disable — stale state must not reactivate** *(gap — TC TBD)*: After disable (feature_state=0) with stale `CLOS_ASSOC`, a subsequent re-enable must produce fresh HP/LP differentiation from the CLOS assignments (not from stale state). No TC verifies that the re-enable path correctly reactivates ordering rather than producing incorrect frequency assignment. Candidate: add as step 4 in TC 16030768620 (disable → assert no differentiation → re-enable → assert correct HP>LP differentiation restored).

---

## Section 7: Security / Safety / Policy

- SST_CLOS_ASSOC and SST_PP_CONTROL are writable by OS ring-0. Malicious reassignment of HP/LP possible without Supervisor-Mode restriction.
- On DLCP SKUs, PCT_Module_Mask fuse provides hardware enforcement of HP positions that cannot be overridden by SW.
- Invalid TPMI writes (out-of-range CLOS_ASSOC, illegal feature_state combinations) should be silently ignored or clamped -- verified by TC 16030768621.

---

## Section 8: References

- [PCT (Priority Core Turbo) HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html)
- [Priority Core Turbo Technology White Paper](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/IC_PCT.html)
- [DMR Turbo HAS -- PCT section](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html)
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html)
- [NWP PM MAS -- PCT section](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [HSD 14025997048](https://hsdes.intel.com/appstore/article-one/#/14025997048) -- MSR 0x1AD must not be 0xFF
- [PCT Enabling & Discovery TCD 22022420855](https://hsdes.intel.com/appstore/article-one/#/22022420855)
- [SST-TF Functionality TCD 22022420928](https://hsdes.intel.com/appstore/article-one/#/22022420928)
- KB: KB/pm_features/sst/pct.md
