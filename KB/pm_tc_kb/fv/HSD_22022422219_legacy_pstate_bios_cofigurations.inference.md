# Deep Analysis: Legacy Pstate Bios Configurations

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422219 |
| **Title** | Legacy Pstate Bios cofigurations |
| **Date** | 2026-06-22 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | Legacy P-states / EIST BIOS menu verification |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Status** | open |
| **Owner** | akurathi |
| **Val Environment** | virtual_platform |
| **Val Framework** | os-svos, python-sv |
| **Automation** | yes |
| **Tags** | PMSS_NWP_READINESS_CHECK |


---

## Test Case Intent

Verify that BIOS menu knobs for **Legacy P-states (EIST / Enhanced Intel SpeedStep Technology)** are present and functional on Newport. The test exercises all supported BIOS combinations — SpeedStep enable/disable, Single PCTL enable, and EIST PSD coordination type (HW_ALL, SW_ALL, SW_ANY) — and confirms the programmed values are reflected in the corresponding architectural MSRs after reboot.

### Pre-Conditions

- NWP platform (virtual_platform / SVOS) booted with flexcon test framework available
- `NWPSV.ini` (or equivalent NWP platform config) available for flexcon
- BIOS supports SpeedStep, Single PCTL, and EIST PSD knobs (verify with NWP BIOS team)
- Platform stable enough to reboot between BIOS knob changes

### Test Steps

| Step | Action | Interface | Expected |
|------|--------|-----------|----------|
| 1 | Configure BIOS: SpeedStep = **Enable**; reboot | BIOS menu / xmlcli | `IA32_MISC_ENABLES[16] = 1` after boot |
| 2 | Read `IA32_MISC_ENABLES` MSR (0x1A0) | `sv.socket0.nio.punit` path | Bit 16 = 1 (GV3 enabled) |
| 3 | Configure BIOS: SpeedStep = **Disable**; reboot | BIOS menu / xmlcli | `IA32_MISC_ENABLES[16] = 0` after boot |
| 4 | Read `IA32_MISC_ENABLES` MSR | CSR | Bit 16 = 0 (GV3 disabled) |
| 5 | Configure BIOS: Single PCTL = **Enable**; reboot | BIOS menu | `MISC_PWR_MGMT[0] = 1`, PSD coord = SW_ANY |
| 6 | Read `MISC_PWR_MGMT` MSR (0x1AA) | CSR | Bit 0 = 1 |
| 7 | Configure BIOS: EIST PSD coord = **HW_ALL**; reboot | BIOS menu | PSD ACPI object reports HW_ALL coordination |
| 8 | Configure BIOS: EIST PSD coord = **SW_ALL**; reboot | BIOS menu | PSD ACPI object reports SW_ALL coordination |
| 9 | Run flexcon PM validation | `python flexcon.py -i NWPSV.ini --onlyspecifiedmodules -m flexconPM` | No failures / hangs |

### Pass / Fail Criteria

**PASS:**
- `IA32_MISC_ENABLES[16]` matches SpeedStep BIOS setting after each reboot
- `MISC_PWR_MGMT[0]` matches Single PCTL BIOS setting
- PSD ACPI coordination type matches BIOS selection
- flexcon PM module reports no failures on NWP

**FAIL:**
- Any MSR bit does not reflect BIOS programming
- Platform hang or crash during BIOS knob change
- flexcon reports P-state coordination errors

---

## Section A: NWP Delta

**Disposition: Runnable_On_N-1**

Legacy P-states (EIST/GV3) are **fully supported on NWP with no architectural changes** from DMR. The test can run as-is with a flexcon platform config substitution.

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Legacy P-states (EIST) | Supported | **Supported — no change** (NWP PM MAS) | No functional delta |
| `IA32_MISC_ENABLES[16]` (GV3) | MSR 0x1A0, bit 16 | Identical architectural MSR | Direct reuse |
| `MISC_PWR_MGMT[0]` (Single PCTL) | MSR 0x1AA, bit 0 | Identical | Direct reuse |
| PSD ACPI coord type | HW_ALL / SW_ALL / SW_ANY | Same ACPI structure | Direct reuse |
| Register path | `sv.socket0.imh0.punit.*` | `sv.socket0.nio.punit.*` | Path prefix swap only |
| CBB count | 4 | 2 | No impact on BIOS knob test |
| flexcon config | `DMRSV.ini` | `NWPSV.ini` | **Single adaptation required** |
| BIOS knob names | DMR BIOS | NWP BIOS — may use identical names; confirm | Low risk |

**Key Justification:**
- NWP PM MAS explicitly states: "No plans to add nor deprecate any CBB PM flow" — legacy P-states included
- `IA32_MISC_ENABLES` and `MISC_PWR_MGMT` are architectural x86 MSRs — identical on NWP
- `PMSS_NWP_READINESS_CHECK` tag confirms this TC is in NWP readiness scope
- No `DMR_PO` tag — not a DMR bring-up blocker; generally applicable

---

## Section B: Interactions

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | OS/Test | Configure BIOS knob (SpeedStep, Single PCTL, PSD coord) via xmlcli/BIOS menu | [Test logic] |
| 2 | BIOS | At boot: write `IA32_MISC_ENABLES[16]` per SpeedStep knob | [CSR] |
| 3 | BIOS | At boot: write `MISC_PWR_MGMT[0]` per Single PCTL knob | [CSR] |
| 4 | BIOS | At boot: configure PSD ACPI object with selected coordination type | [ACPI] |
| 5 | PCode (CBB×2) | Read `IA32_MISC_ENABLES[16]`; set PEGA GV3 mode (legacy or HWP) accordingly | [Internal] |
| 6 | OS/Test | Post-boot: read MSRs to verify BIOS programming | [CSR] |
| 7 | OS/Test | Run flexcon PM module; verify P-state coordination type matches BIOS | [Test logic] |

### Sequence Data

| # | From | To | Message | Interface |
|---|------|----|---------|-----------|
| 1 | OS/Test | BIOS | Set SpeedStep knob value (Enable/Disable) | [Test logic] |
| 2 | BIOS | HW | Write `IA32_MISC_ENABLES[16]` at boot | [CSR] |
| 3 | BIOS | HW | Write `MISC_PWR_MGMT[0]` at boot | [CSR] |
| 4 | BIOS | HW | Publish PSD ACPI object with coord type | [ACPI] |
| 5 | PCode (CBB×2) | HW | Read MSR state; configure PEGA P-state arbitration mode | [Internal] |
| 6 | OS/Test | HW | Read `IA32_MISC_ENABLES` and `MISC_PWR_MGMT` for post-boot verification | [CSR] |
| 7 | OS/Test | PCode (CBB×2) | flexcon: exercise P-state transitions under legacy coordination | [Test logic] |

---

## Section C: Coverage

| Coverage Dimension | Details |
|--------------------|---------|
| **BIOS knob combinations** | SpeedStep Enable, SpeedStep Disable, Single PCTL Enable, EIST PSD HW_ALL, SW_ALL, SW_ANY |
| **MSRs verified** | `IA32_MISC_ENABLES` (0x1A0) bit 16; `MISC_PWR_MGMT` (0x1AA) bit 0 |
| **ACPI coverage** | PSD coordination type (HW_ALL, SW_ALL, SW_ANY) via ACPI _PSD object |
| **GV3 path** | SpeedStep enable → PEGA operates in legacy OS-directed mode (`IA32_PERF_CTL`) |
| **Not covered** | P-state performance validation (covered by `22022422224`); HWP knobs (covered by `22022422301`); Turbo knobs (covered by `22022422408`) |
| **NWP scope** | All 2 CBBs share the same BIOS knob state; single verification pass covers both |

---

## Section D: Spec Refs

| Reference | Artifact | Relevance |
|-----------|----------|-----------|
| Intel SDM Vol. 3B §14.1 | `IA32_MISC_ENABLES` (MSR 0x1A0), bit 16 = Enhanced Intel SpeedStep Enable | Primary MSR for SpeedStep BIOS knob effect |
| Intel SDM Vol. 3B §14.3 | `MISC_PWR_MGMT` (MSR 0x1AA), bit 0 = single PCTL coordination | MSR for Single PCTL BIOS knob |
| Intel SDM Vol. 3B §8.7 | ACPI PSD object — P-state dependency (coordination type HW_ALL/SW_ALL/SW_ANY) | PSD coordination verification |
| NWP PM MAS §2 | "No plans to add nor deprecate any CBB PM flow" | Legacy P-states confirmed supported on NWP |
| CBB PEGA HAS | PEGA P-state mode selection — reads `IA32_MISC_ENABLES[16]` to determine legacy vs HWP mode | FW touchpoint for GV3 enable |
| KB: `KB/pm_features/pstate_stack/pstate_stack_main.md` | P-state stack KB article — EIST/Legacy section; NWP delta table | Project-local reference |

---

## Section E: Risk Assessment

| Risk | Severity | Likelihood | Mitigation |
|------|----------|-----------|------------|
| NWP BIOS knob names differ from DMR (e.g. SpeedStep renamed) | Medium | Low | Confirm with NWP BIOS team before running; check NWP BIOS setup documentation |
| `virtual_platform` BIOS model may not fully emulate all BIOS menu options for legacy P-states | Medium | Medium | Run pre-check: enumerate available BIOS knobs via xmlcli; skip inapplicable knobs with documented N/A note |
| `NWPSV.ini` flexcon config missing or incomplete for legacy P-state test scenarios | Medium | Medium | Verify config covers flexconPM legacy mode; adapt from `DMRSV.ini` if needed |
| `IA32_MISC_ENABLES` path differs on NWP (`nio` vs `imh0`) | Low | Low | Use NWP path `sv.socket0.nio.punit.ptpcioregs.ia32_misc_enables`; path-swap only |
| PSD ACPI object not populated in virtual_platform | Low | Low | If PSD not available, document as sim limitation; verify on real hardware / emulation |

---

## Section F: Recommendations

**Recommendation: ADOPT — Architecturally identical; single config adaptation required**

Legacy P-state BIOS knob verification maps cleanly to NWP with minimal adaptation.

**Required adaptations:**
1. Replace `DMRSV.ini` with `NWPSV.ini` in flexcon invocation
2. Confirm NWP BIOS knob names for SpeedStep and Single PCTL with NWP BIOS team
3. Update register path: `sv.socket0.imh0.*` → `sv.socket0.nio.*`
4. Verify `flexconPM` module supports NWP legacy P-state scenario

**PythonSV verification snippet (NWP paths):**
```python
# NWP Legacy P-state BIOS configuration verification
# Path: sv.socket0.nio.punit (NWP equivalent of sv.socket0.imh0.punit on DMR)

# Check IA32_MISC_ENABLES[16] (Enhanced Intel SpeedStep = GV3 enable)
misc_en = sv.socket0.nio.punit.ptpcioregs.ia32_misc_enables.read()
gv3 = (misc_en >> 16) & 1
print(f"IA32_MISC_ENABLES: 0x{misc_en:016X}")
print(f"  GV3 (SpeedStep) bit[16]: {gv3}  (1=enabled, 0=disabled)")

# Check MISC_PWR_MGMT[0] (Single PCTL enable)
misc_pwr = sv.socket0.nio.punit.ptpcioregs.misc_pwr_mgmt.read()
single_pctl = misc_pwr & 1
print(f"MISC_PWR_MGMT: 0x{misc_pwr:08X}")
print(f"  Single PCTL bit[0]: {single_pctl}  (1=enabled)")
```

**Priority:** Low — no `DMR_PO` tag; BIOS configuration baseline verification; run after HWP and Turbo BIOS knob TCs

---

## Version History

| Version | Date | Author | Notes |
|---------|------|--------|-------|
| v1 | 2025-07-24 | val_agent | Initial enrichment |
| v2 | 2026-06-22 | val_agent | Full template rebuild — added Test Intent, Steps, Pass/Fail, Section B swimlane/sequence tables, Section C Coverage, Section D Spec Refs, Section E Risk; updated NWP register paths |
