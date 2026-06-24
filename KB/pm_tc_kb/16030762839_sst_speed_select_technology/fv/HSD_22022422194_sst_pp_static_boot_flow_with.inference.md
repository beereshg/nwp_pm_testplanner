# Deep Analysis: SST-PP Static Boot Flow with OSPL

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422194](https://hsdes.intel.com/appstore/article-one/#/22022422194) |
| **Title** | SST-PP Static Boot flow with OSPL |
| **Date** | 2026-06-22 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SST |
| **Sub-Feature** | SST-PP — state retention after OS Patch Loading (OSPL) |
| **Parent TCD** | [22022420914 — SST-PP Static Boot flow](https://hsdes.intel.com/appstore/article-one/#/22022420914) |
| **NWP Disposition** | **Skip_ZBB** |
| **Val Environment** | silicon |
| **Framework** | os-svos |
| **Origin** | DIAMOND RAPIDS |
| **Owner** | mps |
| **Tags** | DMR_PO, PMSS_NWP_READINESS_CHECK |
| **DMR Command** | `runPmx.py -x dmr.xml -p sst_pp -tM 60 --retry_count 2` |

## KB References
- KB Article: [KB/pm_features/sst/pp.md](../../../pm_features/sst/pp.md)

## OSPL Definition
> **OSPL = OS Patch Loading** — a live microcode update applied by the OS after boot (e.g., via
> `wrmsr 0x79` / Intel MCU update path). This is distinct from the `sst_ospl` CSR register.
> The test verifies that SST-PP profile configuration is **retained and consistent** after the
> OS performs a microcode patch load event.

## Version History
- v1 (2025-07-24): Initial stub — Skip_ZBB only
- v2 (2026-06-22): Full enrichment — OSPL = OS Patch Loading definition, all sections A-G

---

## Test Case Intent

Verify **SST-PP state retention across an OS Patch Loading (OSPL) event**. The concern:
when the OS applies a live microcode update, PCode re-initializes certain PM state. This TC
confirms that the SST-PP profile committed at boot (TDP, frequency caps, core-count mask)
is correctly preserved — or re-applied — after the OSPL event, and that no unintended profile
regression or hang occurs.

**Specific verification:**
1. Boot into a non-default SST-PP profile (e.g., PP1/PP2) via BIOS OSPL knob
2. Trigger OS Patch Loading (live MCU update)
3. After OSPL: `sst_ospl` register and `SST_PP_STATUS.SST_PP_LEVEL` match pre-OSPL values
4. Active TDP and frequency caps unchanged from pre-OSPL profile
5. `runPmx.py -x dmr.xml -p sst_pp` automation PASS

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP silicon with SST/HGS and PM flow enabled |
| FW stack | AcodeFW, Pcode, Pstate driver, Cstate Driver, DMR SVOS, DMR PythonSV repo, Patch23 installed |
| BIOS | OSPL knob set to non-default SST-PP profile index before boot |
| MCU patch | A valid microcode update package available for OS-level patch loading |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Configure BIOS OSPL knob to select a non-default SST-PP profile; boot to OS | System boots into selected profile; no MCA or hang in PH3/PH4 | Boot hang, MCA, or profile not applied |
| 2 | Record pre-OSPL state: read `sst_ospl`, `SST_PP_STATUS.SST_PP_LEVEL`, active TDP/freq from `SST_PP_INFO_*` | Baseline profile registers read successfully | Register read failure |
| 3 | Apply OS Patch Loading (OSPL): trigger live MCU update via OS mechanism | MCU update completes; no MCA, hang, or unexpected reset | MCA, hang, or uncontrolled reset during OSPL |
| 4 | After OSPL: re-read `sst_ospl`, `SST_PP_STATUS.SST_PP_LEVEL`, active TDP/freq | All values match pre-OSPL snapshot; profile retained | Any register mismatch vs pre-OSPL baseline |
| 5 | Run `runPmx.py -x dmr.xml -p sst_pp -tM 60 --retry_count 2` | Automation PASS; SST-PP static boot + OSPL retention verified | Script FAIL or timeout |

### Pass / Fail Criteria

- **PASS**: All post-OSPL registers match pre-OSPL snapshot; SST-PP profile TDP/freq/core-count match HAS; no MCA, no hang; automation passes
- **FAIL**: Any register mismatch post-OSPL; profile regressed to default; MCA or hang during OSPL; NLOG error-level event; automation failure

---

## Section A: NWP Delta

**Disposition: Skip_ZBB — SST-PP is ZBB'd on NWP; OSPL retention flow not testable**

SST-PP is fully ZBB'd on NWP. Without SST-PP functional, no non-default profile can be
committed at boot, so the OSPL retention check has no baseline to compare against.

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| SST-PP static boot via BIOS knob | ✅ Functional | ❌ **ZBB'd** | No non-default profile to retain |
| OS Patch Loading (OSPL) mechanism | ✅ Functional | ✅ Functional | OSPL itself works; but SST-PP is ZBB'd |
| SST-PP state post-OSPL retention | ✅ Tested | ❌ N/A (ZBB) | Nothing to retain |
| `sst_ospl` register (namednodes) | `sv.socket0.imhX.punit.sst_ospl` | Same path — **unchanged** | No path swap needed |
| `runPmx.py -x dmr.xml` | DMR topology | Needs `nwp.xml` | Config swap required if re-enabled |
| NWP active SST features | SST-PP + TF/BF/CP | **SST-TF + PCT only** | All PP variants ZBB'd |

**ZBB References:**
- [HSD 22021155414](https://hsdes.intel.com/appstore/article-one/#/22021155414) — SST-PP/BF/CP ZBB'd on NWP
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- `nwp_imh/v1_0/ok_going_zero.txt` lines 270, 297–298

---

## Section B: Interactions

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | BIOS setup | Set OSPL knob → selects SST-PP profile index at boot | BIOS Setup Menu |
| 2 | PrimeCode PH5 | Read SST-PP fuses; populate `SST_PP_HEADER` + `SST_PP_INFO_0..11` | [Internal fuse→TPMI] |
| 3 | PCode PH3/PH4 | Apply selected profile TDP/freq/core-count; write `SST_PP_STATUS` | [HPM sideband] |
| 4 | OS | Record pre-OSPL register snapshot | [TPMI MMIO / MSR] |
| 5 | OS | Trigger OS Patch Loading — write MCU update blob via `wrmsr 0x79` or equivalent | [MSR 0x79] |
| 6 | PCode | Handle OSPL event: preserve or re-apply SST-PP profile; update `SST_PP_STATUS` | [Internal / HPM] |
| 7 | Test/PythonSV | Re-read `sst_ospl`, `SST_PP_STATUS`, `SST_PP_INFO_*`; compare to pre-OSPL snapshot | [TPMI MMIO] |

### Sequence Data

| # | From | To | Message | Interface |
|---|----|------|---------|-----------|
| 1 | BIOS | TPMI SRAM | Write `SST_PP_CONTROL.SST_PP_LEVEL = target_index` | [TPMI MMIO] |
| 2 | PCode | All CBBs | Broadcast active profile constraints | [HPM sideband] |
| 3 | OS | MSR 0x79 | Write MCU update blob (OS Patch Loading) | [MSR] |
| 4 | PCode | Internal | Re-validate SST-PP state post-OSPL; re-populate STATUS | [Internal] |
| 5 | Test | TPMI SRAM | Read `SST_PP_STATUS`, `SST_PP_INFO_*`; diff vs pre-OSPL | [TPMI MMIO] |

---

## Section C: Coverage

| Coverage Area | DMR Coverage | NWP Gap | Adaptation Required |
|--------------|-------------|---------|---------------------|
| SST-PP static boot profile apply | Covered | ⚠️ ZBB'd | Feature not functional |
| Pre-OSPL register snapshot | Covered | ⚠️ ZBB'd | No valid non-default profile |
| OSPL (MCU live update) trigger | Covered | ✅ OSPL mechanism works | Only SST-PP side is ZBB'd |
| Post-OSPL SST-PP state retention check | Covered | ⚠️ ZBB'd | Nothing to retain |
| `runPmx.py -x dmr.xml` static boot + OSPL | Covered | ❌ Config mismatch | Needs `nwp.xml` if re-enabled |

---

## Section D: Spec Refs & Validation Points

### Key Registers

| Register | NWP Namednodes Path | Purpose | Access |
|----------|--------------------|---------|----|
| sst_ospl | `sv.socket0.imhX.punit.sst_ospl` | OSPL boot profile index — **path unchanged from DMR** | RW |
| SST_PP_CONTROL.SST_PP_LEVEL | `sv.socket0.cbbX.base.tpmi.sst_pp_control.sst_pp_level` | Active/requested PP level | RW |
| SST_PP_STATUS.SST_PP_LEVEL | `sv.socket0.cbbX.base.tpmi.sst_pp_status.sst_pp_level` | Acknowledged PP level | RO/V |
| SST_PP_INFO_0 | `sv.socket0.cbbX.base.tpmi.sst_pp_info_0` | Active profile TDP power | RO |
| MSR 0x79 | `sv.socket0.imh0.punit` (PCode internal) | OS Patch Loading trigger (microcode update) | WO |

### PythonSV Validation Sketch (for reference — ZBB'd on NWP)

```python
# Pre-OSPL snapshot
pre_ospl = sv.socket0.imh0.punit.sst_ospl.read()
pre_level = sv.socket0.cbb0.base.tpmi.sst_pp_status.sst_pp_level.read()
pre_info0 = sv.socket0.cbb0.base.tpmi.sst_pp_info_0.read()
print(f"Pre-OSPL: ospl={hex(pre_ospl)} level={pre_level} info0={hex(pre_info0)}")

# --- OS triggers OSPL (MCU update) here ---

# Post-OSPL check
post_ospl = sv.socket0.imh0.punit.sst_ospl.read()
post_level = sv.socket0.cbb0.base.tpmi.sst_pp_status.sst_pp_level.read()
post_info0 = sv.socket0.cbb0.base.tpmi.sst_pp_info_0.read()
print(f"Post-OSPL: ospl={hex(post_ospl)} level={post_level} info0={hex(post_info0)}")

assert pre_ospl == post_ospl, f"OSPL register changed: {hex(pre_ospl)} -> {hex(post_ospl)}"
assert pre_level == post_level, f"PP level changed: {pre_level} -> {post_level}"
assert pre_info0 == post_info0, f"PP INFO_0 changed: {hex(pre_info0)} -> {hex(post_info0)}"
print("PASS: SST-PP state retained across OSPL")
```

### References
- [Intel SST HAS — SST-PP Registers](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html#sst-pp-registers)
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [HSD 22021155414](https://hsdes.intel.com/appstore/article-one/#/22021155414) — ZBB confirmation
- KB: KB/pm_features/sst/pp.md

---

## Section E: Risk Assessment

| # | Risk / Open Item | Severity | Notes |
|---|-----------------|----------|-------|
| 1 | SST-PP ZBB'd on NWP — no non-default profile available for retention test | **High** | Root cause of Skip; blocks entire flow |
| 2 | OSPL mechanism itself (MCU live update) works on NWP — but SST-PP side can't be verified | Medium | OSPL isolation test possible if needed |
| 3 | `dmr.xml` in automation — `nwp.xml` config required if re-enabled | Medium | Config swap on re-enable |
| 4 | `sst_ospl` namednodes path **unchanged** from DMR — no adaptation needed | — | Risk removed |
| 5 | Post-OSPL PCode re-init sequence may differ between DMR and NWP stepping | Medium | Re-validate when ZBB lifted |

---

## Section F: Recommendations

**Recommendation: SKIP — SST-PP is ZBB'd on NWP; OSPL retention test not applicable.**

If SST-PP is re-enabled on a future NWP stepping:
1. Change `-x dmr.xml` → `-x nwp.xml` in automation command
2. `sst_ospl` register path: `sv.socket0.imhX.punit.sst_ospl` — **no change needed** (same as DMR)
3. CBB loop bounds: `range(4)` → `range(2)`, core counts 64 → 48
4. Verify PCode post-OSPL re-init sequence preserves SST-PP state on NWP topology
5. Confirm MCU patch package compatible with NWP stepping for OSPL trigger

---

## Section G: PSS Grading

### Grading Table

| Sl No | Dimension | Value | Rationale |
|-------|-----------|-------|----------|
| 1 | NWP Delta | Yes | SST-PP ZBB'd; OSPL trigger mechanism same; post-OSPL retention path may differ in NWP PCode |
| 2 | Applicable NWP | **No (ZBB)** | SST-PP explicitly ZBB'd — HSD 22021155414; no non-default profile to retain |
| 3 | PSS Environment | N/A (ZBB) | OSPL (MCU live update) not typically modeled in VP/HSLE; SST-PP side also ZBB'd |
| 4 | Silicon Only | Yes | Live MCU update + PM state retention requires real hardware reset flow |
| 5 | Test Content | DMR_M | DMR-origin; medium adaptation (config, CBB bounds) needed if ZBB lifted |
| 6 | OS | sv-os | PythonSV register reads under SVOS; MCU update via OS mechanism |

### Verdict

**Skip_ZBB** — SST-PP is not activatable on NWP. Without a committed non-default SST-PP profile at boot, there is no state to retain across OSPL. Re-evaluate when SST-PP support is confirmed for a future NWP stepping.

### Key Notes

| Area | Detail |
|------|--------|
| OSPL clarification | OSPL = OS Patch Loading (live MCU update), NOT the `sst_ospl` Performance Level register |
| `sst_ospl` register | Path unchanged from DMR — `sv.socket0.imhX.punit.sst_ospl` |
| Reuse Level | Medium (DMR_M) — config swap + CBB loop update once ZBB lifted |
| Key validation risk | Post-OSPL PCode re-init behavior may differ on NWP; must re-validate |
