# Deep Analysis: SST-TF -- Validate All TF Buckets Without Power Limiting

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422216 |
| **Title** | SST-TF - Validate all TF buckets without power limiting |
| **Date** | 2026-07-16 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **TCD** | SST-TF Functionality |
| **TCD ID** | 22022420928 |
| **Status** | open |
| **Val Environment** | silicon,virtual_platform |
| **Owner Team** | soc.pm |
| **Automation** | runPmx.py -x nwp.xml -p sst_tf -tM 60 -M 5 --retry_count 2 |
| **Feature** | SST |
| **Sub-Feature** | SST-TF -- TRL bucket validation (non-power-limited) |
| **NWP Disposition** | Runnable_On_NWP |

---

## Test Case Intent

Verify SST-TF Turbo Ratio Limit (TRL) correctness by exercising **all 3 TF buckets** under workload and confirming HP cores achieve the expected bucket TRL ceiling. "Without power limiting" means PL1/PL2 are set high so RAPL does not mask the observed frequency — the test **must run workload** to verify runtime behavior, not just register propagation.

---

## Section A: NWP Disposition

**Disposition: Runnable_On_NWP**

SST-TF is the POR frequency management mechanism for NWP (underlying PCT). All TF infrastructure
(fuses, TPMI registers, PCode TrlManager, WP4 delivery) is present on NWP. Adapt DMR register
paths: `imh0/imh1` -> `nio0`; CBB loop `range(4)` -> `range(2)`; 48 cores/CBB on NWP.

---

## Section B: NWP Test Procedure

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP silicon or VP; SVOS booted |
| SST-TF enabled | `sst_pp_control.feature_state[1] = 1` |
| TF fuses populated | `sst_tf_info_0..8` non-zero |
| PL1/PL2 set high | Power limits set sufficiently high (e.g. 999 W) so RAPL does not throttle during workload |
| Stress tool | `stress-ng` or equivalent, pinnable to specific logical cores |
| HP/LP CLOS set | SST_CLOS_ASSOC: ~8 HP (CLOS[0]), ~88 LP (CLOS[3]) per NWP topology |

### Test Steps

| Step | Phase | Action | Expected Result (PASS) | Failure Indication |
|------|-------|--------|------------------------|-------------------|
| 1 | Setup | Verify SST-TF fuses readable on nio0, cbb0, cbb1 | Fuse registers non-zero; `sst_tf_info_0.feature_supported == 1` | Fuses zero or feature_supported == 0 |
| 2 | Setup | Set PL1/PL2 high; confirm no RAPL throttle asserted | `package_rapl_status.throttle_status == 0` | Power limit active before sweep starts |
| 3 | Bucket N | Read bucket boundary N from `sst_tf_info_8.num_core_<bucket>` | N readable; matches expected HP count threshold for this bucket | INFO_8 unreadable or zero |
| 4 | Bucket N | Assign exactly N cores to HP (CLOS[0]) via `sst_clos_assoc`; remaining cores to LP (CLOS[3]) | CLOS assignments updated; N cores in CLOS[0] | CLOS assignment mismatch |
| 5 | Bucket N | Pin stress workload to the N HP cores (sufficient to request turbo) | N HP cores in C0, requesting P0 via HWP; utilization > 95% | Cores idle; no turbo request issued |
| 6 | Bucket N | Read achieved HP ratio via `ia32_perf_status` / PCUDATA on HP cores | Observed ratio == bucket TRL from `sst_tf_info_2` (bucket 0), `sst_tf_info_4` (bucket 1), or `sst_tf_info_6` (bucket 2) | Ratio below expected TRL ceiling |
| 7 | Bucket N | Verify LP cores remain clipped at LP_CLIP_RATIO during HP stress | All LP core ratios <= `sst_tf_info_0.lp_clip_ratio_0` | LP core exceeds clip; TF enforcement broken |
| 8 | Bucket N | Confirm no RAPL throttle during measurement | `package_rapl_status.throttle_status == 0` | RAPL throttling — cannot attribute freq to TF |
| 9 | Post | Release stress; confirm all cores return to idle frequency | Cores drop below P1; no stuck ratio | Core stuck at high ratio after workload removed |
| 10 | Post | Verify no MCA logged during entire sweep | No MCA errors in log | MCA triggered during bucket sweep |

> **Note:** Steps 3–8 repeat for each TF bucket (0, 1, 2). Each bucket uses a different HP core count threshold from `sst_tf_info_8` and a different TRL from `sst_tf_info_2/4/6`.

### Health Checks

- SST-TF fuses non-zero; `feature_supported == 1` (Step 1).
- No RAPL throttle before or during sweep (Steps 2, 8).
- For each bucket: observed HP ratio == bucket TRL (Step 6).
- LP cores always <= LP_CLIP_RATIO_0 (Step 7).
- No MCA logged (Step 10).

### Pass / Fail Criteria

- **PASS**: All 3 buckets exercised under workload; for each bucket the HP cores achieve `sst_tf_info_<2|4|6>.hp_trl_ratio_0`; LP cores remain clipped to `sst_tf_info_0.lp_clip_ratio_0`; no RAPL throttling during measurement; no MCA.
- **FAIL**: Any HP core ratio falls below expected bucket TRL; any LP core exceeds clip; RAPL throttling asserted (masking TF result); MCA triggered.

---

## Section C: NWP Delta Impact

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| IMH die path | `imh0`, `imh1` | **`nio0`** | Fuse/TPMI paths change |
| CBB count | Up to 4 | **2** | Loop `range(4)` -> `range(2)` |
| Cores per CBB | 64 | **48** | HP count ~8, LP ~88 |
| PMX XML | `dmr.xml` | **`nwp.xml`** | Required for NWP topology |
| TRL bucket values | DMR-fused ratios | **NWP-fused ratios** | Verify via `sst_tf_info_2/4/6` |

---

## Section D: Spec Refs

- [SST Intel HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html)
- [NWP PM MAS -- SST-TF section](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [SST-TF Functionality TCD 22022420928](https://hsdes.intel.com/appstore/article-one/#/22022420928)

---

## Section E: Risk Assessment

| Risk / Open Item | Likelihood | Severity | Mitigation |
|-----------------|------------|----------|-----------|
| PMX Step 4 uses `dmr.xml` -- must change to `nwp.xml` | High | High | Update automation command field in HSD to nwp.xml |
| Step 2: `check_tpmi_matches_fuses()` not called by PMX harasser | Medium | Low | Run standalone before PMX as a pre-check |
| Step 3: MSR 0x1AD may be 0xFF on some configs (HSD 14025997048) | Medium | High | Assert MSR == sst_tf_info_2.ratio_0; fail if 0xFF |

---

## Section F: Recommendations

**Gap 1 -- Bucket sweep requires directed workload:**
The existing PMX sst_tf harasser does NOT do directed bucket sweeps — it runs random GV stress.
Per the TC title "Validate all TF buckets without power limiting", a proper implementation must:

1. Set PL1/PL2 high so RAPL doesn't throttle
2. For each bucket (0, 1, 2):
   - Read bucket N threshold from `sst_tf_info_8.num_core_<bucket>`
   - Assign N cores to CLOS[0] (HP), rest to CLOS[3] (LP)
   - Pin stress workload to N HP cores
   - Verify HP cores achieve bucket TRL from `sst_tf_info_<2|4|6>.hp_trl_ratio_0`
   - Verify LP cores remain at `sst_tf_info_0.lp_clip_ratio_0`

**Example automation (bucket sweep with workload):**
```python
import namednodes
from stress_pinned import start_stress, stop_stress  # Example stress wrapper

# Read bucket thresholds
nio = namednodes.sv.socket0.nio0.tpmi
bucket_cores = [
    nio.sst_tf_info_8.num_core_0,
    nio.sst_tf_info_8.num_core_1,
    nio.sst_tf_info_8.num_core_2
]
bucket_trl = [
    nio.sst_tf_info_2.hp_trl_ratio_0,  # bucket 0 TRL
    nio.sst_tf_info_4.hp_trl_ratio_0,  # bucket 1 TRL
    nio.sst_tf_info_6.hp_trl_ratio_0   # bucket 2 TRL
]
lp_clip = nio.sst_tf_info_0.lp_clip_ratio_0

for bucket_idx in [0, 1, 2]:
    N = bucket_cores[bucket_idx]
    expected_trl = bucket_trl[bucket_idx]
    
    # Assign N HP cores to CLOS[0], rest to CLOS[3]
    # ... (CLOS assignment code)
    
    # Start stress on HP cores
    start_stress(cpu_list=hp_core_list, load=100)
    time.sleep(2.0)  # Allow freq to stabilize
    
    # Check HP cores achieving bucket TRL
    for core in hp_core_list:
        perf_status = core.ia32_perf_status
        ratio = (perf_status >> 8) & 0xFF
        assert ratio == expected_trl, f"HP core {core} ratio {ratio} != {expected_trl}"
    
    # Check LP cores clipped
    for core in lp_core_list:
        ratio = (core.ia32_perf_status >> 8) & 0xFF
        assert ratio <= lp_clip, f"LP core {core} ratio {ratio} exceeds clip {lp_clip}"
    
    stop_stress()
```

**Gap 2 -- "Without power limiting" is a PRECONDITION:**
Set PL1/PL2 high before starting sweep. If RAPL throttles during measurement,
the observed frequency cannot be attributed to TF bucket enforcement — FAIL the test.

**Recommended command (workload-based sweep if script available):**
```bash
python -m pm.sst.sst_tf_validate --bucket-sweep --socket 0 --pl-high 999
```
