# Deep Analysis: SST-TF - Verify Fusing

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422217 |
| **Title** | SST-TF - verify fusing |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SST |
| **Sub-Feature** | SST-TF — fuse logical ordering validation for LP clip ratios and TRL bucket ratios |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test validates that SST-TF fuses have logically consistent ordering:
1. `sst_tf_config_{level}_lp_clip_ratio_cdyn_index{cdyn}` must be **non-increasing** at higher cdyn (longer instructions → lower frequency)
2. `sst_tf_config_{level}_turbo_ratio_limit_cores_numcore{bucket}` must be **non-decreasing** at higher buckets (more cores at higher bucket)
3. `sst_tf_config_{level}_turbo_ratio_limit_ratios_cdyn_index{cdyn}_ratio{bucket}` must be **non-increasing** at higher buckets AND at higher cdyn

SST-TF is **functional on NWP**. Fuse checks are read-only and can run without thermal stress.

Tags: `DMR_PO`, `NGA_MAIN`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p sst_tf -tM 60 -M 5 --retry_count 2
```

### NWP Fuse Ordering Rules

| Fuse Pattern | Ordering Rule |
|--------------|---------------|
| `lp_clip_ratio_cdyn_index{N}` | Non-increasing: cdyn0 ≥ cdyn1 ≥ cdyn2 |
| `turbo_ratio_limit_cores_numcore{N}` | Non-decreasing: bucket0 ≤ bucket1 ≤ bucket2 |
| `turbo_ratio_limit_ratios_cdyn_index{cdyn}_ratio{bucket}` | Non-increasing: bucket0 ≥ bucket1 ≥ bucket2 AND cdyn0 ≥ cdyn1 |

### NWP Fuse Check Script
```python
# NWP: read SST-TF fuses and validate ordering
# Fuse path: sv.socket0.imh0.fuses.punit.sst_tf_config_*
# Per CBB fuses: sv.socket0.cbb[0].punit.sst_tf_config_*
for cbb_idx in range(2):
    # Read all sst_tf_config fuses for this CBB
    # Validate ordering rules per level, cdyn, bucket
    pass
```

### Pass Criteria
- All LP clip ratio fuses non-increasing at higher cdyn indices
- All NumCore fuses non-decreasing at higher buckets
- All TRL ratio fuses non-increasing at higher buckets AND higher cdyn
- `sst_tf` PMx fuse check passes
- `NGA_MAIN`: automate fuse read and ordering verification

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; NWP SST-TF fuse values differ from DMR; fuse ordering rules same; `NGA_MAIN` priority for automated verification**

**Priority**: High — `NGA_MAIN`, `DMR_PO`, `plc.feature.p1`; fuse ordering is a quality gate for SST-TF correctness before any frequency validation
