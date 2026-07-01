# Deep Analysis: PCT - Per-SST-Instance Programming Completeness (NWP 2-CBB)

| Field | Value |
|-------|-------|
| **HSD ID** | [16030982844](https://hsdes.intel.com/appstore/article-one/#/16030982844) |
| **Title** | PCT - Per-SST-Instance Programming Completeness (NWP 2-CBB) |
| **Target Program** | NWP (Newport) |
| **Feature** | SST / PCT |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify BIOS programs SST_CLOS_CONFIG, SST_CLOS_ASSOC, SST_CP_CONTROL, and SST_PP_CONTROL correctly on BOTH CBB SST TPMI instances (cbb0 and cbb1). NWP-specific: DMR had 4 CBBs; NWP has 2 larger CBBs and a different MADT structure. Partial programming on one CBB would cause HP/LP frequency policy mismatch.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | sv.socket0.cbb0.base.tpmi and sv.socket0.cbb1.base.tpmi accessible |
| PCT enabled | PCT Partition Count >= 1 in BIOS |
| Platform | Fully booted post-PCT programming |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Read SST_PP_CONTROL.feature_state[1] on both CBBs. or i in [0,1]: fst=sv.socket0.cbb[i].base.tpmi.sst_pp_control.feature_state_1.read(); print(f'CBB{i} feature_state[1]={fst}') | = 1 on both CBBs (PCT/SST-TF active) | One CBB = 0 — partial programming; PCT only active on one die |
| 2 | Read SST_CLOS_CONFIG[0].max and SST_CLOS_CONFIG[3].max on both CBBs. | Both CBBs: CLOS[0].max = HP TRL (~4.4 GHz); CLOS[3].max = LP_CLIP; non-zero and consistent | One CBB has wrong/zero values — BIOS missed a TPMI instance |
| 3 | Read SST_CP_CONTROL.sst_cp_priority_type on both CBBs. | Both = 1 (Ordered Throttling) | One CBB = 0 — LP will not be throttled first on that die |
| 4 | Read SST_CLOS_ASSOC for sample HP and LP cores on each CBB; verify CLOS assignment consistent. | CLOS consistent on both CBBs per partition algorithm | CBB discrepancy — per-instance BIOS programming incomplete |

---

### Pass / Fail Criteria

- **PASS**: feature_state[1]=1, CLOS_CONFIG correct, priority_type=1, CLOS_ASSOC consistent on BOTH CBBs.
- **FAIL**: Any mismatch between CBB0 and CBB1; partial programming.

---

### References

- [https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST TPMI per-instance programming; CLOS_CONFIG; CP_CONTROL; PP_CONTROL
- [https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP 2-CBB topology; TPMI instance layout

