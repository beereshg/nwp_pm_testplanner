# Deep Analysis: SST-TF - All High Priority Cores in C6

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422212 |
| **Title** | SST-TF - All high priority cores in C6 |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SST |
| **Sub-Feature** | SST-TF — LP cores remain clipped when all HP cores are in C6 (FACT TRL invariant) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

When all HP cores are in C6, the active core count may cause the Legacy TRL to resolve higher than the FACT TRL. This tests that LP cores are still clipped to the LP limit when FACT is enabled, regardless of Legacy TRL.

SST-TF is **functional on NWP**. Core-level C6 (C6A/C6S/C6S-P) is functional on NWP.

Reference: `graniterapids.pm.sst.sst_tf.sst_tf.validate.py > validateTF.all_c6_focus()` → NWP equivalent.

Tags: `New_content`, `plc.feature.p1`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### Adapted Command (NWP)
```bash
python runPmx.py -x nwp.xml -p sst_tf -tM 60 -M 5 --retry_count 2
```

### Scenario: HP cores all in C6

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Enable SST-TF with HP/LP CLOS assignment | `sst_pp_control.feature_state[1] = 1` |
| 2 | Enable C6 on all HP cores | Core C6 functional on NWP |
| 3 | Apply load only to LP cores | Drive all LP cores active |
| 4 | With 0 HP active cores, Legacy TRL may be higher | Core count resolves higher TRL |
| 5 | Verify LP cores still clipped to LP clip ratio | FACT TRL enforced over Legacy TRL |
| 6 | Verify LP core frequency ≤ LP clip ratio | Invariant maintained |

### NWP Note
- NWP: 2 CBBs × 48 cores; HP and LP cores distributed across both CBBs
- `validateTF.all_c6_focus()` → adapt for NWP: `newport.pm.sst.sst_tf.validate.py`
- Core-level C6 (not MC6/Ring C6) is functional

### Pass Criteria
- LP cores remain clipped to LP limit when all HP cores in C6
- FACT TRL priority over Legacy TRL enforced
- `sst_tf` PMx plugin passes

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; `graniterapids.pm.sst.sst_tf.validate` → `newport.pm.sst.sst_tf.validate`; SST-TF functional on NWP**

**Priority**: Medium — `plc.feature.p1`; LP clip invariant under HP-idle scenarios is a key SST-TF correctness requirement
