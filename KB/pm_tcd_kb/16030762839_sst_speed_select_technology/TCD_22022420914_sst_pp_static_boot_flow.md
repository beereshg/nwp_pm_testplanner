# TCD 22022420914 -- SST-PP Static Boot Flow

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420914](https://hsdes.intel.com/appstore/article-one/#/22022420914) |
| **Title** | SST-PP Static Boot Flow |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030762940 -- NWP PM SST-PP (Perf Profile) Static](https://hsdes.intel.com/appstore/article-one/#/16030762940) |
| **Child TCs** | [22022422194](https://hsdes.intel.com/appstore/article-one/#/22022422194) -- SST-PP Static Boot flow with OSPL<br>[22022422195](https://hsdes.intel.com/appstore/article-one/#/22022422195) -- SST-PP Static Boot flow (silicon) |
| **KB last updated** | 2026-07-16 |

---

## Section 1: Architecture / Micro-architecture and Functionality

**SST-PP Static Boot Flow** validates that NWP boots into a fixed SST performance profile selected by BIOS at CPL3 via the **OSPL (Operating System Performance Level)** register. Unlike Dynamic SST-PP (which allows runtime profile switching), Static PP commits the profile at boot time and maintains it for the entire session, including across OS Patch Loading (OSPL/microcode update) events.

### Key Scenarios

| Scenario | What is validated |
|----------|-------------------|
| Cold boot with PP level N | BIOS selects PP level via OSPL register at CPL3; PCode applies TDP/TRL/P1 from SST_PP_INFO |
| SST-PP state after OSPL event | OS applies live microcode update; PCode re-initializes; SST-PP profile retained |
| PP level parameters match fuses | TDP, P1, TRL match SST_PP_INFO TPMI registers (populated from fuses at PH5) |
| Invalid PP level handling | BIOS writes unsupported level; PCode falls back to level 0 without MCA |

### NWP-Specific Deltas

- NWP supports **Static PP only** -- Dynamic PP (runtime level switching) is **not POR**.
- OSPL register path: `sv.socket0.nio0.tpmi.sst_pp_control.current_config_level` (NIO root die).
- NWP has **1 active PP level** (level 0) by default; additional levels depend on SKU fusing.
- SST_PP_INFO_0..11 populated by PrimeCode at PH5 from fuses.
- After OSPL (microcode patch), PCode must re-read `current_config_level` and re-apply -- critical retention check.

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422195 -- SST-PP Static Boot flow (silicon)](https://hsdes.intel.com/appstore/article-one/#/22022422195) | Cold boot PP application | Verify boot into BIOS-selected PP level; PCode applies TDP/TRL/P1; registers match fuses |
| [22022422194 -- SST-PP Static Boot flow with OSPL](https://hsdes.intel.com/appstore/article-one/#/22022422194) | OSPL retention | Trigger microcode update; verify SST-PP profile retained post-update |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Direction | Description |
|-----------|----------------|-----------|-------------|
| TPMI SST | SST_PP_CONTROL.current_config_level | RW | Active PP level selector. Written by BIOS at CPL3. |
| TPMI SST | SST_PP_INFO_0 | RO | PP level 0: TDP, P1, max cores. |
| TPMI SST | SST_PP_INFO_4 | RO | PP level 0 TRL ratios (ODC source). |
| TPMI SST | SST_PP_INFO_11 | RO | Pm/P0 fabric ratios for selected level. |
| TPMI SST | SST_PP_CONTROL.lock | RW | Lock bit -- prevents runtime change after CPL3. |
| MSR | 0x64F (MSR_CONFIG_TDP_CONTROL) | RW | Legacy PP level select. PCode reconciles with TPMI. |
| PythonSV | sv.socket0.nio0.tpmi.sst_pp_control.current_config_level | RW | Active level readback. |
| PythonSV | sv.socket0.nio0.tpmi.sst_pp_info_0.tdp | RO | TDP for PP level 0. |

---

## Section 3: Reset / Power / Clocking

- **PH5**: PrimeCode populates SST_PP_INFO_0..11 TPMI from fuses before BIOS.
- **CPL3 (BIOS)**: Reads available levels, selects target, writes `current_config_level`. May set lock.
- **PCode slow loop**: Detects level change; applies TDP/TRL/P1 to turbo resolver and RAPL.
- **OSPL event**: PCode re-inits PM state. Must re-read `current_config_level` and re-apply profile.
- **Warm reset**: PP level lost; BIOS re-programs at next CPL3.

---

## Section 4: Programming Model

### Boot-time PP Selection (BIOS CPL3)

```python
nio = sv.socket0.nio0
num_levels = nio.tpmi.sst_pp_control.max_config_level + 1
tdp_0 = nio.tpmi.sst_pp_info_0.tdp
p1_0 = nio.tpmi.sst_pp_info_0.base_frequency
# Select level 0
nio.tpmi.sst_pp_control.current_config_level.write(0)
import time; time.sleep(0.02)
assert nio.tpmi.sst_pp_info_11.p0_fabric_ratio > 0
```

### OSPL Retention Check

```python
pre_level = nio.tpmi.sst_pp_control.current_config_level
pre_tdp = nio.tpmi.sst_pp_info_0.tdp
# ... microcode update (OSPL) happens here ...
post_level = nio.tpmi.sst_pp_control.current_config_level
post_tdp = nio.tpmi.sst_pp_info_0.tdp
assert post_level == pre_level, "PP level changed after OSPL"
assert post_tdp == pre_tdp, "TDP changed after OSPL"
```

---

## Section 5: Operational Behavior

| Scenario | Expected Behavior |
|----------|-------------------|
| Cold boot PP level 0 | PCode applies TDP/TRL/P1 from SST_PP_INFO_0. |
| OSPL microcode patch | PP profile retained across PCode re-init. |
| Invalid PP level | PCode falls back to level 0. No MCA. |
| Lock bit set | Runtime writes to current_config_level rejected. |

---

## Section 6: Corner Cases & Error Handling

- **OSPL race**: PP re-application must be atomic during PCode re-init.
- **PP level > max_config_level**: PCode clamps to level 0.
- **Lock + write**: Silently dropped when lock=1.
- **Single PP level**: Level 1+ gracefully falls back to 0.
- **TDP/TRL mismatch after OSPL**: Critical silicon safety check.

---

## Section 7: Security / Safety / Policy

- SST_PP_CONTROL.lock prevents OS override of BIOS-selected level.
- TPMI is ring-0 accessible. Without lock, OS could change level.
- Fuse-derived SST_PP_INFO is read-only.

---

## Section 8: References

- [SST Intel HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html)
- [NWP PM MAS -- SST-PP](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [SST Feature KB -- pp.md](../../../pm_features/sst/pp.md)
- [Sibling TCD -- SST-PP Dynamic (22022420897)](https://hsdes.intel.com/appstore/article-one/#/22022420897)
