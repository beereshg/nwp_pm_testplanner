# Deep Analysis: SST-PP Static Boot Flow Silicon

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422195](https://hsdes.intel.com/appstore/article-one/#/22022422195) |
| **Title** | SST-PP Static Boot flow_silicon |
| **Date** | 2026-06-22 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SST |
| **Sub-Feature** | SST-PP — OSPL Static Boot Profile |
| **Parent TCD** | [22022420914 — SST-PP Static Boot flow](https://hsdes.intel.com/appstore/article-one/#/22022420914) |
| **NWP Disposition** | **Skip_ZBB** |
| **Val Environment** | silicon, virtual_platform |
| **Framework** | os-svos |
| **Origin** | DIAMOND RAPIDS |
| **Owner** | mps |
| **Tags** | plc.feature.p1, PMSS_NWP_READINESS_CHECK |
| **DMR Command** | `runPmx.py -x dmr.xml -p sst_pp -tM 60 --retry_count 2` |

## KB References
- KB Article: [KB/pm_features/sst/pp.md](../../../pm_features/sst/pp.md)

## Version History
- v1 (2025-07-24): Initial stub — Skip_ZBB only
- v2 (2026-06-22): Full enrichment — OSPL static boot flow, all sections A-G, NWP register paths, PSS grading

---

## Test Case Intent

Verify the **SST-PP Static Boot Flow** on NWP silicon: the platform boots directly into a
fixed performance profile pre-selected by BIOS via the **OSPL (Operating System Performance
Level)** register. PCode applies the selected profile's TDP, frequency caps, and core counts
during early boot (reset Phase 3–4). The OS observes the profile as the system's base
capability — not a runtime switch, but a boot-time committed configuration.

**Specific verification:**
1. BIOS OSPL knob programs `sst_ospl` register to select SST-PP profile index
2. After boot: `sst_ospl` register reflects configured profile index
3. Active TDP and frequency caps match the selected SST-PP profile per HAS definition
4. `runPmx.py -x dmr.xml -p sst_pp` automation PASS

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP silicon or emulation with SST/HGS and PM flow enabled |
| FW stack | AcodeFW, Pcode, Pstate driver, Cstate Driver, DMR SVOS, DMR PythonSV repo, Patch23 installed |
| BIOS | OSPL knob set to non-default SST-PP profile index before boot |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Configure BIOS OSPL knob to select a non-default SST-PP profile; boot to OS | System boots into selected profile; no MCA or hang during profile application in PH3/PH4 | Boot hang, MCA, or profile not applied |
| 2 | Read `sst_ospl` register; compare to BIOS-configured profile index | OSPL register = BIOS-configured index; profile TDP and frequency caps are active | OSPL register mismatch or default profile retained |
| 3 | Read SST-PP profile data (TDP, frequency caps, core counts) from TPMI `SST_PP_INFO_*` for the active PP level; compare to HAS specification | Active profile parameters exactly match HAS spec for the selected OSPL index | Parameter mismatch from HAS |
| 4 | Run `runPmx.py -x dmr.xml -p sst_pp -tM 60 --retry_count 2` | Automation PASS; static boot OSPL flow verified end-to-end | Script FAIL or timeout |

### Pass / Fail Criteria

- **PASS**: OSPL register = BIOS knob value; SST-PP profile TDP/freq/core-count match HAS; no MCA, no hang; automation passes
- **FAIL**: OSPL register mismatch; profile parameters differ from HAS; MCA or hang; NLOG error-level event; automation failure

---

## Section A: NWP Delta

**Disposition: Skip_ZBB — SST-PP is ZBB'd on NWP (both static and dynamic)**

SST-PP (Performance Profile) is fully ZBB'd on NWP. Both `SstResetInit_next` and
`SstTpmiResetInit_next` are in `ok_going_zero.txt` (lines 270, 297–298). The OSPL-based
static boot flow relies on SST-PP infrastructure that is not activated on NWP initial silicon.

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| SST-PP static boot via OSPL | ✅ Functional | ❌ **ZBB'd** | TC cannot run — feature not available |
| SST-PP dynamic runtime switch | ✅ Functional | ❌ **ZBB'd** | ZBB HSD 22021155414 |
| OSPL register (`sst_ospl`) | `sv.socket0.imhX.punit.sst_ospl` — same path as DMR | Likely not functional (ZBB) | PP infrastructure disabled; path itself unchanged |
| SST-PP fuses (PP0–PP4) | Programmed | Not applicable | Single PP level on NWP |
| `runPmx.py -x dmr.xml` | DMR topology | Needs `nwp.xml` | Config swap required if ever re-evaluated |
| NWP SST features active | SST-PP + SST-TF/BF/CP | **SST-TF + PCT only** | All PP variants ZBB'd |

**ZBB References:**
- [HSD 22021155414](https://hsdes.intel.com/appstore/article-one/#/22021155414) — SST-PP/BF/CP/HGS ZBB'd on NWP
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- `nwp_imh/v1_0/ok_going_zero.txt` lines 270, 297–298

---

## Section B: Interactions

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | BIOS setup | User sets OSPL knob to target PP index (e.g., PP1) | BIOS Setup Menu |
| 2 | BIOS CPL3 | Writes target PP index to `sst_ospl` / `SST_PP_CONTROL.SST_PP_LEVEL` | [TPMI MMIO] |
| 3 | PrimeCode Phase 5 | Reads SST-PP fuses; populates `SST_PP_HEADER` + `SST_PP_INFO_0..11` per PP level | [Internal fuse→TPMI] |
| 4 | PCode PH3/PH4 | Reads OSPL; resolves `ALLOWED_LEVEL_MASK`; applies selected profile TDP/freq/core-count via BIOS CPL3 `update_cfgs()` | [HPM sideband] |
| 5 | PCode runtime | Enforces profile constraints: P1 ratios, TRL array, T_THROTTLE | [PMSB sideband] |
| 6 | OS/PythonSV | Reads `sst_ospl`; reads `SST_PP_STATUS`, `SST_PP_INFO_*` for active profile; validates against HAS | [TPMI MMIO / CSR] |

### Sequence Data

| # | From | To | Message | Interface |
|---|----|------|---------|-----------|
| 1 | BIOS | TPMI SRAM | Write `SST_PP_CONTROL.SST_PP_LEVEL = target_index` | [TPMI MMIO] |
| 2 | PrimeCode | Fuse Controller | Read SST_PP fuses (PP levels, TDP, P1, TRL arrays) | [Internal] |
| 3 | PrimeCode | TPMI SRAM | Write `SST_PP_HEADER.SST_PP_LEVEL_EN_MASK` + `SST_PP_INFO_0..11` | [Internal] |
| 4 | PCode | TPMI SRAM | Read OSPL → resolve `ALLOWED_LEVEL_MASK` | [TPMI MMIO] |
| 5 | PCode | All CBBs | Broadcast active profile TDP/freq constraints via HPM | [HPM sideband] |
| 6 | Test/PythonSV | TPMI SRAM | Read `SST_PP_STATUS.SST_PP_LEVEL`; read `SST_PP_INFO_*` | [TPMI MMIO] |

---

## Section C: Coverage

| Coverage Area | DMR Coverage | NWP Gap | Adaptation Required |
|--------------|-------------|---------|---------------------|
| OSPL register programming | Covered | ⚠️ ZBB'd | Not applicable on NWP |
| SST-PP static boot profile apply | Covered | ⚠️ ZBB'd | Feature not functional |
| SST_PP_INFO_* profile content match | Covered (PP0–PP4) | ⚠️ ZBB'd | Only PP0 relevant on NWP |
| PH3/PH4 profile propagation | Covered | ⚠️ ZBB'd | Reset sequence not triggered |
| `runPmx.py -x dmr.xml` static boot | Covered | ❌ Config mismatch | Needs `nwp.xml` if re-enabled |
| Automation PASS threshold | 60s timeout, 2 retries | N/A (ZBB) | — |

---

## Section D: Spec Refs & Validation Points

### Key Registers

| Register | NWP Namednodes Path | Purpose | Access |
|----------|--------------------|---------|----|
| SST_PP_CONTROL.SST_PP_LEVEL | `sv.socket0.cbb{X}.base.tpmi.sst_pp_control.sst_pp_level` | Active/requested PP level | RW |
| SST_PP_STATUS.SST_PP_LEVEL | `sv.socket0.cbb{X}.base.tpmi.sst_pp_status.sst_pp_level` | Acknowledged PP level | RO/V |
| SST_PP_HEADER.ALLOWED_LEVEL_MASK | `sv.socket0.cbb{X}.base.tpmi.sst_pp_header.allowed_level_mask` | Runtime-valid PP levels | RO |
| SST_PP_HEADER.SST_PP_LEVEL_EN_MASK | `sv.socket0.cbb{X}.base.tpmi.sst_pp_header.sst_pp_level_en_mask` | Fuse-defined available levels | RO |
| sst_ospl | `sv.socket0.imh0.punit.sst_ospl` | OSPL register (same path as DMR) | RW |
| SST_PP_INFO_0 | `sv.socket0.cbb{X}.base.tpmi.sst_pp_info_0` | Active profile TDP power | RO |

> **NWP register path note**: `sst_ospl` namednodes path is unchanged from DMR — `sv.socket0.imhX.punit.sst_ospl` (no path swap needed).

### PythonSV Validation (NWP, for reference — feature ZBB'd)

```python
# NWP register path: same as DMR (imhX.punit)
# All values ZBB'd but readable for structural check

# Read OSPL register
ospl = sv.socket0.imh0.punit.sst_ospl.read()
print(f"OSPL register: {hex(ospl)}")

# Read PP control/status per CBB
for cbb_idx in range(2):   # NWP: 2 CBBs
    ctrl = sv.socket0.getbypath(f"cbb{cbb_idx}").base.tpmi.sst_pp_control.sst_pp_level.read()
    status = sv.socket0.getbypath(f"cbb{cbb_idx}").base.tpmi.sst_pp_status.sst_pp_level.read()
    allowed = sv.socket0.getbypath(f"cbb{cbb_idx}").base.tpmi.sst_pp_header.allowed_level_mask.read()
    print(f"CBB{cbb_idx}: CTRL_level={ctrl} STATUS_level={status} ALLOWED={hex(allowed)}")

# Check if PP is ZBB'd (expect allowed_level_mask = 0x1, only PP0)
# On NWP with SST-PP ZBB'd: LEVEL_EN_MASK should be 1 (PP0 only)
en_mask = sv.socket0.cbb0.base.tpmi.sst_pp_header.sst_pp_level_en_mask.read()
print(f"PP_LEVEL_EN_MASK: {hex(en_mask)}  (expect 0x1 on NWP = PP0 only)")
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
| 1 | SST-PP ZBB'd on NWP — feature not activatable | **High** | Root cause of Skip disposition; blocks all OSPL static boot validation |
| 2 | `dmr.xml` config in automation — NWP config file (`nwp.xml`) not referenced | Medium | If feature re-enabled in future stepping, config swap required |
| 3 | OSPL register path — `imhX.punit.sst_ospl` **unchanged** on NWP (no path swap needed) | — | Risk removed; namednodes path identical to DMR |
| 4 | Only PP0 level expected available on NWP if ZBB partially lifted | Medium | Validate `ALLOWED_LEVEL_MASK = 0x1` (PP0 only) |
| 5 | `runPmx.py` relies on DMR topology assumptions in `-p sst_pp` plugin | Medium | Plugin may need NWP topology update before re-enabling |

---

## Section F: Recommendations

**Recommendation: SKIP — SST-PP is ZBB'd on NWP; static OSPL boot flow not applicable.**

If SST-PP is re-enabled in a future NWP stepping:
1. Change `-x dmr.xml` → `-x nwp.xml` in automation command
2. OSPL register path: `sv.socket0.imhX.punit.sst_ospl` — **no change needed** (same as DMR)
3. Update CBB loop bounds: `range(4)` → `range(2)`, `range(64)` → `range(48)`
4. Verify `SST_PP_LEVEL_EN_MASK` reflects NWP-supported PP levels (currently expected = PP0 only)
5. Validate `runPmx.py` `-p sst_pp` plugin handles NWP topology (2 CBBs, 48 cores/CBB)

---

## Section G: PSS Grading

### Grading Table

| Sl No | Dimension | Value | Rationale |
|-------|-----------|-------|----------|
| 1 | NWP Delta | Yes | NWP topology differs (2 CBBs, NIO path); more critically SST-PP infrastructure is ZBB'd |
| 2 | Applicable NWP | **No (ZBB)** | SST-PP is explicitly ZBB'd on NWP — HSD 22021155414; `ok_going_zero.txt` entries |
| 3 | PSS Environment | N/A (ZBB) | Feature not activatable in any pre-Si environment on NWP |
| 4 | Silicon Only | Partial | If ZBB lifted: OSPL boot flow requires hardware reset sequence; VP cannot simulate early-boot profile application |
| 5 | Test Content | DMR_M | DMR-origin; medium adaptation needed (config file, register paths, loop bounds) if ever re-enabled |
| 6 | OS | sv-os | PythonSV-based register reads under SVOS |

### Verdict

**Skip_ZBB** — SST-PP Static Boot flow is not executable on NWP because SST-PP is ZBB'd. No PSS environment can verify this feature on NWP. Re-evaluate if SST-PP support is added to a future NWP stepping.

### Environment Coverage

| Environment | Coverage | Notes |
|-------------|----------|-------|
| Simics VP | No | SST-PP ZBB'd; fuses not programmed for PP1-PP4 |
| HSLE | No | Feature infrastructure disabled |
| Post-Silicon | No (ZBB) | Blocked until ZBB lifted |

### Key Notes

| Area | Detail |
|------|--------|
| Reuse Level | Medium (DMR_M) — once ZBB lifted |
| Main Adaptation | Config: `dmr.xml` → `nwp.xml`; OSPL path: `imhX` → `nio`; CBB loop 4→2 |
| Limitation | Feature entirely ZBB'd; no structural validation possible |
| Validation Strategy | Skip until NWP stepping with SST-PP support confirmed |
