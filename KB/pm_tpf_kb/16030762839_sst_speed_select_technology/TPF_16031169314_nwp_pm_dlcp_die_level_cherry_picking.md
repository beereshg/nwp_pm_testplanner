# TPF 16031169314 — NWP PM DLCP (Die Level Cherry Picking)

| Field | Value |
|-------|-------|
| **TPF ID** | [16031169314](https://hsdes.intel.com/appstore/article-one/#/16031169314) |
| **Title** | NWP PM DLCP (Die Level Cherry Picking) |
| **Parent TP** | [16030762839 — NWP PM SST](https://hsdes.intel.com/appstore/article-one/#/16030762839) |
| **Status** | open |
| **Owner** | bg3 |
| **KB last updated** | 2026-07-18 |
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

*(Populate from TCD 16030982802 KB — see KB extraction checklist)*

> **Note:** DLCP inherits the SST-TF CLOS enforcement stack from standard PCT (same CBB PCode path). The DLCP delta is exclusively in the HP core *selection* mechanism (fuse vs BIOS computation). Full-stack diagram, ordered throttle, and frequency hierarchy are shared with PCT TPF 16030762939 §2.

---

## Section 3: Validation Strategy

DLCP requires the same three-tier approach as PCT, with an additional PSS scope for fuse-gating verification:

- **PSS**: VP for DLCP-absent (fuse=0) negative check; HSLE XOS for per-CBB `SST_TF_INFO_10` programming
- **FV**: silicon fuse readout, CLOS programming from fuse mask, HP/LP enforcement
- **PV**: OS-visible `SST_TF_INFO_101.QUALIFIED_MODULE_MASK`, `IA32_HWP_CAPABILITIES` per-core differentiation

---

## Section 5: Risks & Dependencies

### Active Risks

- **No PV TCs yet:** All 4 existing TCs are PSS/FV scope only. PV coverage (OS-visible DLCP discovery via `SST_TF_INFO_101.QUALIFIED_MODULE_MASK`, intel-speed-select reporting, per-core `IA32_HWP_CAPABILITIES`) is a gap — 3 PV TCs needed (TCD TBD: DLCP - PV Discovery / Topology).
- **NWP silicon availability:** DLCP depends on OTP fuse `PCT_Module_Mask`; not all NWP QDFs will have DLCP active. PV/FV TCs must check QDF capability before execution.

### Accepted Coverage Limitations (by design — no new TCs required)

| Gap ID | Description | Coverage Today | Accepted Rationale |
|--------|-------------|----------------|-------------------|
| **G-1** | HSLE XOS (IMH2+CBB both-die) not required for any identified DLCP scenario | HSLE single-die covers per-CBB TPMI programming; DLCP operates per-CBB dielet independently | Co-Design T1 audit found no specific DLCP control/telemetry behavior that provably requires cross-die IMH2↔CBB protocol. Accept: single-die HSLE is sufficient for all identified PSS DLCP scenarios. |

---

## Section 6: DFX Considerations

- `PCT_Module_Mask` is OTP fuse — not patchable at runtime; DFX can only verify final fuse value.
- `SST_TF_INFO_10` is read-only post Phase 5 — DFX write-protect verification is a TC requirement (TC TBD under TCD 16030982802).

### Child TCDs

| TCD ID | Title | Segment | TC Count |
|--------|-------|---------|----------|
| [16030982802](https://hsdes.intel.com/appstore/article-one/#/16030982802) | PCT - DLCP (Die Level Cherry Picking) | PSS/FV/PV | 4 |

### References

- [PCT HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — `PCT_Module_Mask`; `SST_TF_INFO_10`; DLCP HP core discovery
- [NWP SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — `SST_TF_INFO_101.QUALIFIED_MODULE_MASK` (NWP-specific)
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP DLCP scope
- Parent PCT TPF: [16030762939 — NWP PM PCT](https://hsdes.intel.com/appstore/article-one/#/16030762939) (standard PCT; shares SST-TF enforcement stack)
