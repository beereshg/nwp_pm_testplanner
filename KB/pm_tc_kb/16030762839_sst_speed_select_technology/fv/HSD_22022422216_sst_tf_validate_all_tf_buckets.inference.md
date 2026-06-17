# Deep Analysis: SST-TF - Validate All TF Buckets Without Power Limiting

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422216 |
| **Title** | SST-TF - Validate all TF buckets without power limiting |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SST |
| **Sub-Feature** | SST-TF — TRL bucket validation for HP and LP cores, non-power-limited condition |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test validates SST-TF turbo ratio limit (TRL) correctness across all TF buckets in non-power-limited conditions:
- HP cores (CLOS[0/1]): granted higher TRL than if TF disabled
- LP cores (CLOS[2/3]): granted lower TRL, leaving power for HP cores
- Focuses on scenarios where power headroom allows achieving TRL

SST-TF is **functional on NWP**. TRL buckets represent different active core counts.

Tags: `DMR_PO`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p sst_tf -tM 60 -M 5 --retry_count 2
```

### TF Bucket Validation Flow

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Enable SST-TF | `sst_pp_control.feature_state[1] = 1` |
| 2 | Set N cores as HP (CLOS[0]) | Sweep N across TF bucket boundaries |
| 3 | Ensure non-power-limited (no RAPL throttle) | Set PL1 high / disable RAPL |
| 4 | Apply load to N HP cores | CPU-bound workload |
| 5 | Verify HP core TRL matches `sst_tf_info TRL[bucket N]` | Per-bucket TRL lookup |
| 6 | Verify LP core TRL ≤ LP clip ratio | LP always clipped |
| 7 | Repeat for all TF bucket boundaries | Sweep all HP core counts |

### NWP TRL Buckets
```python
# NWP: TRL buckets based on number of active HP cores
# sst_tf_info_0.turbo_ratio_limit_ratios_cdyn_index{cdyn}_ratio{bucket}
# bucket boundaries defined per NWP SKU fuse values
```

### Pass Criteria
- For each bucket N: HP cores achieve TRL[N] when N HP cores active
- LP cores always clipped to LP clip ratio
- All TF buckets validated without power limiting
- `sst_tf` PMx plugin passes

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; TRL bucket counts and ratios will differ for NWP SKU; verify against NWP SST-TF fuse spec**

**Priority**: High — `DMR_PO`, `plc.feature.p1`; TRL bucket correctness is the primary SST-TF specification to validate
