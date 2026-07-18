# TPF 16031169314 — NWP PM DLCP (Die Level Cherry Picking)

| Field | Value |
|-------|-------|
| **TPF ID** | [16031169314](https://hsdes.intel.com/appstore/article-one/#/16031169314) |
| **Title** | NWP PM DLCP (Die Level Cherry Picking) |
| **Parent TP** | [16030762839 — NWP PM SST](https://hsdes.intel.com/appstore/article-one/#/16030762839) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-18 (sections 2–8 enriched from TCD 16030982802 KB) |
| **Source** | Created from Co-Design T1 gap audit (2026-07-18); DLCP is architecturally distinct from standard PCT — `SST_TF_INFO_101.QUALIFIED_MODULE_MASK` is NWP-specific |
| **Duplicate note** | TPF 16031169315 is an empty duplicate created by accident — set to `rejected` status |

---

## Section 1: Feature Classification & Introduction

**DLCP (Die Level Cherry Picking)** is a NWP-specific variant of PCT (Priority Core Turbo) where HP core positions are **fixed at manufacturing time** via the `PCT_Module_Mask` OTP fuse (read into `SST_TF_INFO_10` at PrimeCode Phase 5), rather than being computed by BIOS from APIC-ID/MADT order at boot.

Key distinction from standard PCT: the `SST_TF_INFO_101.QUALIFIED_MODULE_MASK` register is NWP-specific and provides the OS-level HP module qualification mask distinct from the SST-TF core-count model.

**Feature gating:** OTP fuse `PCT_Module_Mask` — hardware-enforced, not BIOS-configurable.

### Feature-Specific Constants

| Parameter | Value | Source |
|---|---|---|
| `SST_TF_INFO_10` | Per-CBB dielet HP mask (read-only post Phase 5) | PCT HAS |
| `SST_TF_INFO_101.QUALIFIED_MODULE_MASK` | NWP-specific OS-visible HP qualification mask | NWP SST HAS |
| `PCT_Module_Mask` | OTP fuse — manufacturing-time HP assignment | PCT HAS |

---

## Section 2: Design Details

> DLCP inherits the SST-TF CLOS enforcement stack from standard PCT (same CBB PCode path). The DLCP delta is exclusively in the HP core *selection* mechanism (fuse vs BIOS computation). Full-stack diagram, ordered throttle, and frequency hierarchy are shared with PCT TPF 16030762939 §2.

### Full-Stack Cross-Layer Diagram

<!-- raw-html -->
<div style="border:2px solid #333;border-radius:8px;padding:12px;font-family:Arial,sans-serif;max-width:650px;">
  <div style="text-align:center;font-weight:700;font-size:13px;margin-bottom:8px;color:#1e3a5f;">DLCP Full-Stack: OTP Fuse → PrimeCode → BIOS → OS</div>
  <div style="background:#4472C4;color:#fff;padding:8px;margin:4px;border-radius:4px;text-align:center;"><strong>Layer 5: OS / Tool</strong> — intel-speed-select, sysfs cpufreq, scheduler HP/LP discovery via IA32_HWP_CAPABILITIES</div>
  <div style="background:#2E75B6;color:#fff;padding:8px;margin:4px;border-radius:4px;text-align:center;"><strong>Layer 4: BIOS</strong> — reads SST_TF_INFO_10 at CPL3, programs SST_CLOS_ASSOC per DLCP mask, builds MADT</div>
  <div style="background:#ED7D31;color:#fff;padding:8px;margin:4px;border-radius:4px;text-align:center;"><strong>Layer 3: PrimeCode (CBB PUnit)</strong> — Phase 5: reads PCT_Module_Mask fuse → writes SST_TF_INFO_10 (RO); runtime: enforces HP/LP TRL separation</div>
  <div style="background:#A020F0;color:#fff;padding:8px;margin:4px;border-radius:4px;text-align:center;"><strong>Layer 2: TPMI Interface</strong> — SST_TF_INFO_10 (RO), SST_CLOS_ASSOC (RW), SST_CP_CONTROL (RW), SST_TF_INFO_101.QUALIFIED_MODULE_MASK (NWP-specific RO)</div>
  <div style="background:#FF0000;color:#fff;padding:8px;margin:4px;border-radius:4px;text-align:center;"><strong>Layer 1: Silicon / OTP Fuse</strong> — PCT_Module_Mask per CBB dielet (set once at sort, hardware-immutable)</div>
</div>
<!-- /raw-html -->

### Validation-Tier Layer Claim

| Layer | PSS (VP) | PSS (HSLE) | FV | PV | Notes |
|---|---|---|---|---|---|
| L5: OS / Tool | ❌ | ❌ | ❌ | ✅ | Requires booted OS + intel-speed-select |
| L4: BIOS | ✅ safe | ❌ | ✅ | ✅ | VP safe for negative BIOS tests |
| L3: PrimeCode | ✅ | ✅ | ✅ | indirect | Phase 5 fuse-to-register validated across tiers |
| L2: TPMI Interface | ✅ | ✅ | ✅ | indirect | Register read/write validated |
| L1: Silicon / OTP Fuse | ❌ | ❌ | ✅ | indirect | Fuse readout requires real silicon |

### DLCP Boot / Reset Flow

<!-- raw-html -->
<div style="margin:14px 0;border:1px solid #bfcfe8;border-radius:8px;overflow:hidden;font-family:'Segoe UI',Arial,sans-serif;font-size:11.5px;max-width:860px;">
  <div style="background:#1e3a5f;color:#fff;padding:8px 16px;font-weight:700;font-size:12px;letter-spacing:.5px;text-align:center;">DLCP Boot Flow: OTP Fuse &rarr; TPMI &rarr; BIOS &rarr; OS Discovery</div>
  <div style="padding:14px 18px;background:#f8fafc;">
    <div style="display:flex;gap:8px;align-items:stretch;margin-bottom:4px;">
      <div style="flex:1;background:#fff3e0;border:2px solid #e65100;border-radius:6px;padding:8px 12px;">
        <div style="font-weight:700;color:#c2410c;font-size:10.5px;margin-bottom:4px;">&#128295; Manufacturing (OTP Fuse)</div>
        <div style="font-size:10px;color:#333;line-height:1.8;">
          <strong>PCT_Module_Mask</strong> fuse per CBB dielet<br>
          Encodes which modules are HP (bit=1)<br>
          One fuse per CBB (cbb0, cbb1 on NWP)<br>
          <span style="color:#92400e;">Set once at sort — hardware-immutable</span>
        </div>
      </div>
    </div>
    <div style="text-align:center;font-size:10px;color:#64748b;padding:2px 0;">&#11015; Reset Phase 5</div>
    <div style="display:flex;gap:8px;align-items:stretch;margin-bottom:4px;">
      <div style="flex:1;background:#ede9fe;border:2px solid #6d28d9;border-radius:6px;padding:8px 12px;">
        <div style="font-weight:700;color:#5b21b6;font-size:10.5px;margin-bottom:4px;">PrimeCode Phase 5 (per CBB)</div>
        <div style="font-size:10px;color:#333;line-height:1.8;">
          Reads PCT_Module_Mask fuse<br>
          Writes <strong>SST_TF_INFO_10</strong> TPMI register (RO)<br>
          cbb0: INFO_10 &larr; cbb0 PCT_Module_Mask<br>
          cbb1: INFO_10 &larr; cbb1 PCT_Module_Mask<br>
          <span style="color:#5b21b6;">Happens before BIOS CPL3 handoff</span>
        </div>
      </div>
    </div>
    <div style="text-align:center;font-size:10px;color:#64748b;padding:2px 0;">&#11015; CPL3 (BIOS reads SST_TF_INFO_10)</div>
    <div style="display:flex;gap:8px;align-items:stretch;margin-bottom:4px;">
      <div style="flex:1;background:#dcfce7;border:2px solid #16a34a;border-radius:6px;padding:8px 12px;">
        <div style="font-weight:700;color:#15803d;font-size:10.5px;margin-bottom:4px;">&#10003; Scenario A: DLCP Active (INFO_10 &ne; 0)</div>
        <div style="font-size:10px;color:#333;line-height:1.8;">
          SST_CLOS_ASSOC[core] &larr; DLCP mask<br>
          Modules in mask &rarr; CLOS[0] (HP, ~4.4 GHz)<br>
          Modules not in mask &rarr; CLOS[3] (LP, ~P1)<br>
          <strong>MADT APIC-ID order ignored</strong> for HP selection
        </div>
      </div>
      <div style="flex:1;background:#f1f5f9;border:2px solid #94a3b8;border-radius:6px;padding:8px 12px;">
        <div style="font-weight:700;color:#475569;font-size:10.5px;margin-bottom:4px;">&#9711; Scenario B: DLCP Absent (INFO_10 = 0)</div>
        <div style="font-size:10px;color:#333;line-height:1.8;">
          SST_CLOS_ASSOC[core] &larr; MADT/APIC-ID order<br>
          First N modules per partition &rarr; HP<br>
          TC 16030982833 runs as <em>negative check</em><br>
          TC 16030982837 skipped (no DLCP mask to validate)
        </div>
      </div>
    </div>
    <div style="text-align:center;font-size:10px;color:#64748b;padding:2px 0;">&#11015; OS / PythonSV observability</div>
    <div style="display:flex;gap:8px;align-items:stretch;">
      <div style="flex:1;background:#e0f2fe;border:1px solid #7dd3fc;border-radius:6px;padding:8px 12px;font-size:10.5px;">
        <div style="font-weight:700;color:#0369a1;margin-bottom:4px;">IA32_HWP_CAPABILITIES (MSR 0x771) per-core</div>
        <div style="display:flex;gap:8px;">
          <div style="flex:1;background:#dcfce7;border:1px solid #16a34a;border-radius:4px;padding:5px 8px;font-size:10px;"><strong>HP cores:</strong><br>highest_perf = P0max<br>OS sees elevated ceiling</div>
          <div style="flex:1;background:#fff7ed;border:1px solid #ea580c;border-radius:4px;padding:5px 8px;font-size:10px;"><strong>LP cores:</strong><br>highest_perf = LP_CLIP<br>OS sees clipped ceiling</div>
        </div>
        <div style="margin-top:6px;font-size:9.5px;color:#0369a1;">OS/scheduler can discover HP/LP without TPMI query in DLCP mode</div>
      </div>
    </div>
  </div>
</div>
<!-- /raw-html -->

### Interface & Register Matrix

| Register / MSR | Type | Field | Default | Feature Effect | Tier Validated |
|---|---|---|---|---|---|
| `PCT_Module_Mask` | OTP fuse | — | 0 (DLCP absent) | Manufacturing-fixed HP module mask per CBB dielet | FV |
| `SST_TF_INFO_10` | TPMI (RO) | — | 0 | HP module mask exposed to BIOS/OS per CBB dielet | PSS, FV |
| `SST_TF_INFO_101.QUALIFIED_MODULE_MASK` | TPMI (RO) | — | 0 | NWP-specific OS-visible HP qualification mask | FV, PV |
| `SST_CLOS_ASSOC` | TPMI (RW) | per-module | 0 | CLOS assignment — must follow DLCP mask when non-zero | PSS, FV |
| `SST_CP_CONTROL` | TPMI (RW) | `sst_cp_enable` | 0 | PCT global enable (1 = on) | PSS, FV, PV |
| `SST_CP_CONTROL` | TPMI (RW) | `sst_cp_priority_type` | 0 | Ordered throttle (1 = Ordered) | PSS, FV |
| `IA32_HWP_CAPABILITIES` | MSR 0x771 | `highest_perf[31:24]` | — | HP = P0max; LP = LP_CLIP in DLCP mode | FV, PV |
| `CAPID4.bit29` | Fuse | — | — | PCT capability fuse (must be 1) | FV |

### Observability

| Observable | Type | Tool / Command | What It Shows |
|---|---|---|---|
| `SST_TF_INFO_10` per CBB | TPMI register | `sv.socket0.cbbX.base.tpmi.sst_tf_info_10.read()` | DLCP HP module mask (0 = absent) |
| `SST_TF_INFO_101.QUALIFIED_MODULE_MASK` | TPMI register | `sv.socket0.nio.punit.tpmi.sst_tf_info_101.read()` | NWP-specific OS-visible DLCP mask |
| `IA32_HWP_CAPABILITIES` per core | MSR 0x771 | `pd.debug.access_to_msr(0x771, core=N)` | Per-core HP/LP `highest_perf` value |
| `CAPID4.bit29` | Fuse readout | `sv.socket0.nio.punit.ptpcioregs.ptpcioregs.capid4.capid4_29.get_value()` | PCT capability gate |
| `SST_CLOS_ASSOC` per module | TPMI register | `sv.socket0.cbbX.base.tpmi.sst_clos_assoc_0.read()` | CLOS assignment per module |

### SKU / Config Distinctions

| SKU / Config | Distinction | TCDs Affected |
|---|---|---|
| `PCT_Module_Mask = 0` (DLCP absent) | TCs pivot to Scenario B — negative checks only; TC 16030982837 skipped | TCD 16030982802 (all 4 TCs) |
| `CAPID4.bit29 = 0` (PCT not fuse-capable) | All DLCP TCs skip — PCT not available on this SKU | TCD 16030982802 (all 4 TCs) |
| NWP 2-CBB topology | Each CBB has independent `PCT_Module_Mask` and `SST_TF_INFO_10` — HP masks may differ per CBB | TCD 16030982802 (TC 16030982844) |

---

## Section 3: Validation Strategy

DLCP requires the same three-tier approach as PCT, with an additional PSS scope for fuse-gating verification.

> Layer coverage is mapped in §2 — Validation-Tier Layer Claim table identifies which tier validates each stack layer and flags any unclaimed layers as accepted gaps.

### Tier Definitions

| Tier | Environment | Interface | What It Validates |
|---|---|---|---|
| PSS — VP | Simics (virtual platform) | PythonSV → TPMI model | Firmware logic (Phase 5 fuse-to-register), BIOS flows, safe negative testing (Scenario B) |
| PSS — HSLE | Single-die RTL (CBB) | PythonSV → TPMI RTL | Within-die PCode fuse readout + SST_TF_INFO_10 programming |
| FV | Post-silicon NWP | PythonSV → namednodes | Real silicon fuse readout, CLOS programming from fuse mask, HP/LP TRL enforcement |
| PV | Post-silicon NWP + Ubuntu | intel-speed-select → sysfs | OS-visible DLCP discovery, per-core IA32_HWP_CAPABILITIES, scheduler HP/LP differentiation |

---

## Section 4: Tier Coverage

### Bug Coverage Matrix

| Bug Category | PSS (VP) | PSS (HSLE) | FV | PV |
|---|---|---|---|---|
| PrimeCode Phase 5 fuse-to-TPMI logic error | ✅ | ✅ | ✅ | indirect |
| SST_TF_INFO_10 write-protect violation | ✅ | ✅ | ✅ | ❌ |
| BIOS SST_CLOS_ASSOC ignores DLCP mask | ✅ safe | ❌ | ✅ | indirect |
| IA32_HWP_CAPABILITIES HP/LP mismatch | ❌ | ❌ | ✅ | ✅ |
| DLCP mask cross-CBB inconsistency | ❌ | ❌ | ✅ | indirect |
| OS SST_TF_INFO_101.QUALIFIED_MODULE_MASK incorrect | ❌ | ❌ | ❌ | ✅ |
| CAPID4.bit29 fuse gating failure | ❌ | ❌ | ✅ | indirect |
| BIOS negative validation (invalid CLOS assignment) | ✅ safe | ❌ | ❌ risky | ❌ |

### Scenario Coverage Across Tiers

| Scenario | PSS | FV | PV | Unique Value |
|---|---|---|---|---|
| A — DLCP Active (PCT_Module_Mask ≠ 0) | ✅ | ✅ | gap | Full fuse-to-OS HP/LP pipeline |
| B — DLCP Absent (PCT_Module_Mask = 0) | ✅ | ✅ | gap | Negative check: INFO_10 = 0, MADT fallback |
| Per-CBB independent mask validation | ❌ | ✅ | gap | NWP 2-CBB topology coverage |
| SST_TF_INFO_10 write-protect | ✅ | ✅ | ❌ | HW enforcement verification |

---

## Section 5: Risks & Dependencies

### Active Risks

- **No PV TCs yet:** All 4 existing TCs are PSS/FV scope only. PV coverage (OS-visible DLCP discovery via `SST_TF_INFO_101.QUALIFIED_MODULE_MASK`, intel-speed-select reporting, per-core `IA32_HWP_CAPABILITIES`) is a gap — 3 PV TCs needed (TCD TBD: DLCP - PV Discovery / Topology).
- **NWP silicon availability:** DLCP depends on OTP fuse `PCT_Module_Mask`; not all NWP QDFs will have DLCP active. PV/FV TCs must check QDF capability before execution.
- **PV tier unclaimed in §4:** Scenarios A, B, and per-CBB validation all show PV=gap. No PV TC has been authored yet.

### Accepted Coverage Limitations (by design — no new TCs required)

| Gap ID | Description | Coverage Today | Accepted Rationale |
|--------|-------------|----------------|-------------------|
| **G-1** | HSLE XOS (IMH2+CBB both-die) not required for any identified DLCP scenario | HSLE single-die covers per-CBB TPMI programming; DLCP operates per-CBB dielet independently | Co-Design T1 audit found no specific DLCP control/telemetry behavior that provably requires cross-die IMH2↔CBB protocol. Accept: single-die HSLE is sufficient for all identified PSS DLCP scenarios. |
| **G-2** | Real-power / TDP convergence not DLCP-scoped | DLCP changes HP core *selection*, not power budget | Power convergence is validated under RAPL/PMAX TPFs; DLCP fuse mask does not affect aggregate power |

---

## Section 6: DFX Considerations

- `PCT_Module_Mask` is OTP fuse — not patchable at runtime; DFX can only verify final fuse value via `CAPID4` readout.
- `SST_TF_INFO_10` is read-only post Phase 5 — DFX write-protect verification is a TC requirement (TC 16030982833 covers write-protect check).
- No VISA/ITH T2 observability needed — DLCP state is fully visible via TPMI registers and MSR 0x771.

---

## Section 7: Common Corner Cases

| Corner Case | Affected TCDs | Expected Behavior |
|---|---|---|
| `PCT_Module_Mask = 0` on NWP SKU | TCD 16030982802 (all 4 TCs) | TCs pivot to Scenario B (negative checks); TC 16030982837 skips |
| DLCP mask conflicts with MADT BIOS algorithm | TCD 16030982802 | `SST_CLOS_ASSOC` must match `SST_TF_INFO_10` mask, not MADT order |
| `SST_TF_INFO_10` SW write attempt | TCD 16030982802 (TC 16030982833) | Write-protect: attempted write must not change value |
| HP mask differs per CBB (asymmetric fuse) | TCD 16030982802 (TC 16030982844) | Each CBB has its own independent HP mask — cross-CBB consistency not guaranteed |
| `CAPID4.bit29 = 0` (PCT not fuse-capable) | TCD 16030982802 (all TCs) | All DLCP TCs must skip gracefully |

---

## Section 8: TCD Coverage Summary & References

### Child TCDs

| TCD ID | Title | Segment | TC Count |
|--------|-------|---------|----------|
| [16030982802](https://hsdes.intel.com/appstore/article-one/#/16030982802) | PCT - DLCP (Die Level Cherry Picking) | PSS/FV/PV | 4 |

### References

- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — `PCT_Module_Mask`; `SST_TF_INFO_10`; DLCP HP core discovery
- [NWP SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — `SST_TF_INFO_101.QUALIFIED_MODULE_MASK` (NWP-specific)
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP DLCP scope
- Parent PCT TPF: [16030762939 — NWP PM PCT](https://hsdes.intel.com/appstore/article-one/#/16030762939) (standard PCT; shares SST-TF enforcement stack)
- CCB HSD 14026595435 — NWP PCT 8 HP cores, 4.4 GHz target
