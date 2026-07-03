# Deep Analysis: SST-TF - Works on All CLOS IDs Regardless of Configuration

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422202 |
| **Title** | SST-TF - Works on all CLOS IDs regardless of configuration |
| **Date** | 2026-05-29 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SST |
| **Sub-Feature** | SST-TF — TRL honored across all CLOS IDs (CLOS 0–3) with arbitrary min/max configuration |
| **NWP Disposition** | **Runnable_On_N-1** |
| **HSD Status** | rejected |
| **Environment** | virtual_platform (VP/Simics) |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies a key correctness invariant of SST-TF: **TRL is honored regardless of which CLOS ID cores are assigned to**, with any valid min/max CLOS configuration. The test exercises CLOS IDs 0 through 3 — covering both HP (CLOS 0) and LP (CLOS 3) and the intermediate groups — confirming that SST-TF frequency enforcement is robust to arbitrary CLOS group assignments.

SST-TF is **functional on NWP** (not ZBB). NWP uses SST-TF as the underlying mechanism for PCT (Priority Core Turbo), making CLOS-based TRL enforcement a core requirement.

> ⚠️ **HSD Status: `rejected`** — This TC was rejected in the DMR context. For NWP enrichment, the test logic remains valid as a VP/Simics-executable CLOS coverage test. Confirm with test owner whether this TC should be re-opened for NWP before running.

**DMR → NWP Architecture Delta:**

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| SST-TF availability | Functional | ✅ Functional (not ZBB) | Test runs as-is |
| CLOS group count | 4 (CLOS 0–3) | 4 (CLOS 0–3) | No change |
| HP assignment | CLOS 0 | CLOS 0 (via PCT) | No change |
| LP assignment | CLOS 3 | CLOS 3 (via PCT) | No change |
| CLOS_CONFIG registers | `sst_clos_config_0..3` | `sst_clos_config_0..3` | Same register names |
| CLOS_ASSOC registers | `sst_clos_assoc_0..N` | `sst_clos_assoc_0..N` | Same; core count differs |
| Core count | 128 cores (4 CBBs × 32) | 96 cores (2 CBBs × 48) | ASSOC register coverage differs |
| TRL bucket lookup | Hash-based O(1) | Hash-based O(1) | Same mechanism |
| Run target | `dmr.xml` | `nwp.xml` | XML swap required |
| val_environment | virtual_platform | virtual_platform | VP/Simics run |

Tags: `New_Content`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: Interactions

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p sst_tf -tM 60 -M 5 --retry_count 2
```

### Swimlane Data

| Step | Actor | Action | Interface |
|------|-------|--------|-----------|
| 1 | Test | Enable SST-TF: `sst_pp_control.feature_state[1] = 0x1` | TPMI `SST_PP_CONTROL` |
| 2 | Test | Configure CLOS 0: set min/max to random values (min < max) | TPMI `sst_clos_config_0` |
| 3 | Test | Configure CLOS 1: set distinct min/max values | TPMI `sst_clos_config_1` |
| 4 | Test | Configure CLOS 2: set distinct min/max values | TPMI `sst_clos_config_2` |
| 5 | Test | Configure CLOS 3: set distinct min/max values | TPMI `sst_clos_config_3` |
| 6 | Test | Assign ALL cores to CLOS 0 via `sst_clos_assoc_0..N` | TPMI `SST_CLOS_ASSOC` |
| 7 | PCode | TrlManager detects CLOS config change; updates HP/LP CCP masks | HPM `COMPUTE_CLOS_CONFIG` |
| 8 | PCode | Workpoint calc applies HP TRL for CLOS 0 cores | WP4 — `hi_prio_clos_cdyn_trl` |
| 9 | Test | Verify all cores achieve TRL ≤ HP CLOS TRL bucket (CLOS 0) | Read core frequencies |
| 10 | Test | Repeat: assign ALL cores to CLOS 1 | TPMI `SST_CLOS_ASSOC` |
| 11 | PCode | TrlManager updates; CLOS 1 is intermediate — no HP elevation | WP4 — SST-PP TRL base |
| 12 | Test | Verify cores honor min ≤ freq ≤ max for CLOS 1 config | Read core frequencies |
| 13 | Test | Repeat for CLOS 2 | TPMI `SST_CLOS_ASSOC` |
| 14 | Test | Repeat: assign ALL cores to CLOS 3 (LP) | TPMI `SST_CLOS_ASSOC` |
| 15 | PCode | TrlManager applies LP CLOS clip ratio for CLOS 3 cores | WP4 — `low_prio_clos_cdyn_trl` |
| 16 | Test | Verify all LP cores clipped to LP clip ratio | Read core frequencies |

### Sequence Data

| # | From | To | Message | Interface |
|---|------|----|---------|-----------|
| 1 | Test | TPMI | Write `sst_pp_control.feature_state[1] = 1` | TPMI SST write |
| 2 | PCode slow-loop | PCode SstManager | Detect TF enable change | Internal slow-loop |
| 3 | PCode SstManager | PCode TrlManager | Signal: reload HP/LP CLOS TRL tables | Internal HPM |
| 4 | PCode TrlManager | TPMI IO | Read `SST_TF_INFO_0` (LP clip ratios per CDYN) | IO read |
| 5 | PCode TrlManager | TPMI IO | Read `SST_TF_INFO_2..7` (HP TRL ratios per CDYN × 3 buckets) | IO read |
| 6 | Test | TPMI | Write `sst_clos_config_0..3` with distinct min/max values | TPMI SST write |
| 7 | Test | TPMI | Write `sst_clos_assoc_0..N` — all cores → CLOS X | TPMI SST write |
| 8 | PCode | TrlManager | Send `HPM_MSG_COMPUTE_CLOS_CONFIG` with HP module count | HPM Root→Leaf |
| 9 | PCode WP Calc | Core FIVR | Apply HP TRL (CLOS 0) or LP clip (CLOS 3) per-core | WP4 frequency target |
| 10 | Test | Core telemetry | Read actual frequencies / TRL registers | TPMI / MSR read |

---

## Section C: Interface Coverage Assessment

| Interface | Register / Signal | Covered? | Notes |
|-----------|------------------|---------|-------|
| SST-TF enable | `sst_pp_control.feature_state[1]` | ✅ | Written in Step 1 |
| CLOS 0 config | `sst_clos_config_0.min_freq` / `.max_freq` | ✅ | Programmed with random values |
| CLOS 1 config | `sst_clos_config_1.min_freq` / `.max_freq` | ✅ | Programmed with distinct values |
| CLOS 2 config | `sst_clos_config_2.min_freq` / `.max_freq` | ✅ | Programmed with distinct values |
| CLOS 3 config | `sst_clos_config_3.min_freq` / `.max_freq` | ✅ | Programmed with distinct values |
| Core → CLOS assignment | `sst_clos_assoc_0..N` | ✅ | All cores assigned per iteration |
| HP TRL enforcement | `sst_tf_info_2..7` (HP CLOS TRL) | ✅ | Validated for CLOS 0 |
| LP TRL clip | `sst_tf_info_0` (LP clip ratio) | ✅ | Validated for CLOS 3 |
| Intermediate CLOS (1, 2) | TRL resolution | ⚠️ | Min/max config checked; intermediate CLOS TRL behavior implementation-dependent |
| CDYN-indexed TRL | Per-CDYN ratio check | ⚠️ | Test uses SSE workload; multi-CDYN coverage via separate bucket test |
| ODC TRL interaction | `IO_ODC_TRL_RATIOS` min | ❌ | Not explicitly tested; separate ODC coverage recommended |

---

## Section D: NWP Specification References

| Specification | Section | Relevance |
|--------------|---------|-----------|
| [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) | SST-TF CLOS Assignment | CLOS_ASSOC encoding, HP/LP TRL resolution |
| [SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) | SST_CLOS_CONFIG fields | min_freq, max_freq encoding per CLOS group |
| [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) | PCT / SST-TF | NWP PCT = SST-TF; CLOS groups remain active |
| KB: `sst/tf.md` | FW Touchpoints | PCode TrlManager CLOS TRL load flow |
| KB: `sst/trl.md` | TRL Architecture | 4-table model; HP/LP CLOS bucket dimensions |
| KB: `sst/sst_cp.md` | CLOS Infrastructure | NWP CLOS ordered throttling via PCT |

---

## Section E: NWP Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| HSD `rejected` — test may not be maintained | Medium | Medium | Verify TC is still valid for NWP; confirm with bg3 before running |
| CLOS 1 & 2 TRL behavior undefined in spec | Low | Low | Intermediate CLOS groups may resolve as SST-PP base TRL; document expected behavior per test plan |
| NWP core count difference affects CLOS_ASSOC coverage | Low | Low | NWP has 96 cores across 2 CBBs (vs 128); update ASSOC register sweep range |
| HP CCP mask detection latency (slow-loop) | Low | Low | 1+ slow-loop latency before TrlManager updates; add settle delay in test |
| VP-only (Simics) — silicon differences | Medium | Low | Results should correlate; re-verify on silicon once available |

---

## Section F: Recommendation

**Recommendation: ADOPT with review — `dmr.xml` → `nwp.xml`; confirm TC status before running (HSD `rejected`); NWP SST-TF CLOS coverage is required for PCT validation**

1. **Re-open or clone TC** for NWP if `rejected` was DMR-specific; tag with `NWP_PM_FV`
2. `python runPmx.py -x nwp.xml -p sst_tf -tM 60 -M 5 --retry_count 2` on VP/Simics
3. Verify all 4 CLOS groups exercised: CLOS 0 (HP) → elevated TRL; CLOS 3 (LP) → clipped; CLOS 1/2 → SST-PP base TRL
4. Update `sst_clos_assoc` sweep for NWP core count (96 cores, 2 CBBs)
5. Add slow-loop settle delay after CLOS_ASSOC writes before frequency check

**Priority**: Medium — `plc.feature.p1`; CLOS-based TRL correctness across all CLOS IDs is a fundamental SST-TF and PCT validation requirement on NWP
