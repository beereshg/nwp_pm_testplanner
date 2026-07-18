# TCD 22022420858 -- PCT Functionality

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420858](https://hsdes.intel.com/appstore/article-one/#/22022420858) |
| **Title** | PCT - Functionality |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030762939 -- NWP PM PCT (Priority Core Turbo)](https://hsdes.intel.com/appstore/article-one/#/16030762939) |
| **Scope distinct from** | TCD 22022420855 (PCT - BIOS Enabling), TCD 16031169297 (PCT - TPMI Runtime Control), TCD 16031169298 (PCT - DQ Rules & Negative Validation) |
| **WHAT** | PCT runtime frequency enforcement behaves per spec — HP/LP CLOS ceilings, LP clip invariant under HP C-state, ordered throttle phase ordering under RAPL PL1 |
| **Child TCs (live)** | [22022422116](https://hsdes.intel.com/appstore/article-one/#/22022422116) -- PCT - Turbo frequency check (FV)<br>[16030715686](https://hsdes.intel.com/appstore/article-one/#/16030715686) -- [PSS] Default HP core selection<br>[16030715692](https://hsdes.intel.com/appstore/article-one/#/16030715692) -- [PSS] Turbo frequency check |
| **KB last updated** | 2026-07-18 (TC refresh) |

### Reorg: Co-Design T2 Finding (2026-07-18)

**Source:** Co-Design T2 WHAT-boundary check against [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST spec separates discovery/control/runtime behavior, BIOS role, and ordered-throttling/runtime behavior into distinct functional areas.

TCD 22022420858 was overloaded with 17 TCs spanning 5+ distinct WHATs. Reorg moves 10 TCs to sibling TCDs that already exist:

| TC | Moved To (live HSD) | Rationale | Status |
|----|---------|-----------|--------|
| 16030768620 | [16031169297](https://hsdes.intel.com/appstore/article-one/#/16031169297) TPMI Runtime Control | TPMI runtime enable/disable = distinct WHAT | ✅ Done |
| 16030715694 | [16031169297](https://hsdes.intel.com/appstore/article-one/#/16031169297) TPMI Runtime Control | PSS enable/disable = runtime control scope | ✅ Done |
| 16030768621 | [16031169308](https://hsdes.intel.com/appstore/article-one/#/16031169308) Negative / Boundary Validation | TPMI negative = negative WHAT | ✅ Done |
| 16030715680 | [16031169308](https://hsdes.intel.com/appstore/article-one/#/16031169308) Negative / Boundary Validation | BIOS negative = negative WHAT | ✅ Done |
| 22022422118 | [16031169298](https://hsdes.intel.com/appstore/article-one/#/16031169298) DQ Rules & Negative | Fuse DQ rules = DQ WHAT | ✅ Done |
| 22022422110 | [16031169298](https://hsdes.intel.com/appstore/article-one/#/16031169298) DQ Rules & Negative | SST-PP x PCT (rejected) = DQ scope | ✅ Done (2026-07-18) |
| 16030768619 | [22022420855](https://hsdes.intel.com/appstore/article-one/#/22022420855) BIOS Enabling | Default enabled = enabling WHAT | ✅ Done |
| 16030715684 | [16031169217](https://hsdes.intel.com/appstore/article-one/#/16031169217) PV BIOS Disable | Default disabled = PV disable scope | ✅ Done |
| 16030717717 | [22022420862](https://hsdes.intel.com/appstore/article-one/#/22022420862) PV BIOS Config | PV custom config = PV BIOS WHAT | ✅ Done |
| 16030717718 | [22022420862](https://hsdes.intel.com/appstore/article-one/#/22022420862) PV BIOS Config | PV partition sweep = PV BIOS WHAT | ✅ Done |
| 16030717719 | [16031169217](https://hsdes.intel.com/appstore/article-one/#/16031169217) PV BIOS Disable | PV PCT disable = PV disable WHAT | ✅ Done |

> **Note (2026-07-18):** Live HSD revealed TCD [16031169308](https://hsdes.intel.com/appstore/article-one/#/16031169308) (PCT - Negative / Boundary Validation) as a separate sibling from 16031169298 (DQ Rules). Negative TCs (BIOS negative, TPMI negative) went to 16031169308; DQ/fuse TCs went to 16031169298.

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

**Spec boundary (Co-Design T2, 2026-07-18):** [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) separates discovery/control/runtime behavior into distinct functional areas. This TCD covers only the **runtime enforcement** interfaces — CLOS frequency ceilings and ordered throttle under RAPL PL1. Runtime toggle (SST_PP_CONTROL.feature_state), negative validation (invalid CLOS writes), and DQ rules belong to sibling TCDs.

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

### Preconditions (Enabling — see TCD 22022420855)

| Step | Actor | Register | Value |
|------|-------|----------|-------|
| 1 | PrimeCode PH5 | SST_TF_INFO_0/2 | LP clip / HP TRL from fuse |
| 2 | BIOS CPL3 | SST_CLOS_CONFIG[0].max | = SST_TF_INFO_2.ratio_0 |
| 3 | BIOS CPL3 | SST_CLOS_CONFIG[3].max | = SST_TF_INFO_0.lp_clip_ratio_0 |
| 4 | BIOS CPL3 | SST_CP_CONTROL.priority_type | = 1 |
| 5 | BIOS CPL3 | SST_CLOS_ASSOC[core] | HP=CLOS[0], LP=CLOS[3] |
| 6 | BIOS CPL3 | SST_PP_CONTROL.feature_state[1] | = 1 |

### Runtime Frequency Enforcement Invariants

Once BIOS enabling is complete, PCode enforces per-core frequency ceilings via the standard SST-TF CLOS flow. The key programming model invariants that validation must observe:

- **HP ceiling**: `SST_CLOS_CONFIG[0].max` = `SST_TF_INFO_2.ratio_0` — HP cores (CLOS[0]) operate up to the HP TRL (~4.4 GHz on NWP). `IA32_HWP_CAPABILITIES.highest_performance` on HP cores reflects this ceiling.
- **LP clip**: `SST_CLOS_CONFIG[3].max` = `SST_TF_INFO_0.lp_clip_ratio_0` — LP cores (CLOS[3]) are clipped at LP_CLIP (~P1). `IA32_HWP_CAPABILITIES.highest_performance` on LP cores reflects the clip.
- **Per-core CLOS association**: `SST_CLOS_ASSOC[core]` maps each core to either CLOS[0] (HP) or CLOS[3] (LP). The CLOS assignment determines which frequency ceiling applies.
- **Ordered throttle**: When `SST_CP_CONTROL.priority_type = 1` and RAPL PL1 constrains power, LP cores are throttled first (Phase A/B) before HP cores are reduced (Phase C).
- **MSR 0x1AD alignment**: `PRIMARY_TURBO_RATIO_LIMIT` must equal `SST_TF_INFO_2.ratio_0` — BIOS overrides this MSR at CPL3.

---

## Section 5: Operational Behavior

| Scenario | Expected Behavior | TC(s) |
|----------|-------------------|-------|
| Normal PCT active | HP at ~4.4 GHz; LP clipped at ~P1; HWP_CAP differs per core | [22022422116](https://hsdes.intel.com/appstore/article-one/#/22022422116) (FV), [16030715692](https://hsdes.intel.com/appstore/article-one/#/16030715692) (PSS) |
| Default HP selection (PSS) | 8 HP cores in CLOS[0]; first 2 per partition per CBB | [16030715686](https://hsdes.intel.com/appstore/article-one/#/16030715686) (PSS) |
| All HP cores in C6 | LP cores still clipped at LP_CLIP — invariant | Moved → [TCD 16031169309](https://hsdes.intel.com/appstore/article-one/#/16031169309) (22022422104, 16030715676) |
| TDP convergence (Phase A/B) | LP drops first under RAPL PL1; HP TRL maintained | Moved → [TCD 22022420855](https://hsdes.intel.com/appstore/article-one/#/22022420855) (22022422117) |
| TPMI runtime disable/enable | Toggle SST-TF at runtime | Moved → [TCD 16031169297](https://hsdes.intel.com/appstore/article-one/#/16031169297) |
| DQ rules / negative | Fuse DQ, BIOS/TPMI negative | Moved → [TCD 16031169298](https://hsdes.intel.com/appstore/article-one/#/16031169298) / [16031169308](https://hsdes.intel.com/appstore/article-one/#/16031169308) |
| PV BIOS scenarios | Disable, partition sweep, custom config | Moved → [TCD 22022420862](https://hsdes.intel.com/appstore/article-one/#/22022420862) / [16031169217](https://hsdes.intel.com/appstore/article-one/#/16031169217) |

---

## Section 6: Corner Cases & Error Handling

> **Post-reorg scope (2026-07-18):** Only runtime frequency enforcement corner cases remain here.
> TPMI negative, BIOS negative, DQ rules, enable/disable state, and PV BIOS scenarios moved to sibling TCDs.

| Corner Case | Description | Current Coverage | Action Required |
|-------------|-------------|-----------------|----------------|
| **LP clip when all HP in C6** | CLOS_CONFIG[3].max HW-enforced ceiling; HP C6 does not release LP frequency | ✅ Covered by TC 22022422104 (now under [TCD 16031169309](https://hsdes.intel.com/appstore/article-one/#/16031169309)) | No action — covered in sibling TCD |
| **Turbo frequency per-core validation** | HP cores hit HP TRL; LP cores hit LP clip; HWP_CAP differs per CLOS | ✅ Covered by TC 22022422116 (FV) + 16030715692 (PSS) | No action |
| **Default HP core selection** | 8 HP in CLOS[0], first 2 per partition per CBB, MADT order | ⚠️ PSS only (16030715686); FV TC 22022422105 moved to [TCD 22022420855](https://hsdes.intel.com/appstore/article-one/#/22022420855) | Consider: FV TC under this TCD for runtime HP selection verification, or confirm 22022420855 covers it |
| **HP bucket transition under core C6** | Active HP count drops → remaining HP should ratchet to higher-ratio bucket | ❌ No TC covers HP bucket ratchet-up on partial HP C6 | Gap — new TC needed |
| **PCT × C-states: partial HP C6 + active LP** | HP C6 mixed workload: bucket ratchet-up AND LP still clipped | ❌ TC 22022422104 tests all-HP-in-C6 only (now in sibling TCD); no partial HP C6 test | Gap — new TC needed (4 of 8 HP in C6 + LP stress) |
| **Phase C — HP throttle under severe PL1** | PL1 ≈35% TDP, LP at floor, HP must throttle | ❌ TC 22022422117 (Phase A/B only, now under TCD 22022420855) | Gap — new TC needed under this or cross-product TCD |
| **PCT × RAPL: PL2 burst + PL4 clamp** | PL2 burst: do HP cores get headroom above HP TRL? PL4 clamp with PCT? | ❌ No TC validates | Gap — new TC needed |

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
