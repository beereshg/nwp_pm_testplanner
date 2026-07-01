# Deep Analysis: PCT - DLCP SST_TF_INFO_10 Fuse-to-Register Verification

| Field | Value |
|-------|-------|
| **HSD ID** | [16030982833](https://hsdes.intel.com/appstore/article-one/#/16030982833) |
| **Title** | PCT - DLCP SST_TF_INFO_10 Fuse-to-Register Verification |
| **Target Program** | NWP (Newport) |
| **Feature** | SST / PCT / DLCP |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Parent TCD** | [16030982802 - PCT - DLCP (Die Level Cherry Picking)](https://hsdes.intel.com/appstore/article-one/#/16030982802) |

---

### Test Case Intent

Verify PCT_Module_Mask fuse is correctly propagated to SST_TF_INFO_10 TPMI register by PrimeCode at Reset Phase 5. This TC is the Scenario A/B gate: non-zero SST_TF_INFO_10 confirms DLCP active; zero confirms standard APIC-order PCT. Either way, this TC provides required coverage. SST_TF_INFO_10 must be RO.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | sv.socket0.imh0 and sv.socket0.cbb{0,1}.base.tpmi accessible |
| Platform S0 | Fully booted; PCT enabled (PCT Partition Count >= 1) |
| Imports | import sv |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Read PCT_Module_Mask fuse. use = sv.socket0.imh0.fuses.punit.pct_module_mask.read(); print(f'PCT_Module_Mask=0x{fuse:08X}') | Readable without error; value determines Scenario A (non-zero) or B (zero) | Read error — check fuse namednodes path |
| 2 | Read SST_TF_INFO_10 from CBB0 and CBB1. or i in [0,1]: v=sv.socket0.cbb[i].base.tpmi.sst_tf_info_10.read(); print(f'CBB{i} SST_TF_INFO_10=0x{v:08X}') | Scenario A: non-zero; matches PCT_Module_Mask per die. Scenario B: = 0 on both CBBs | Fuse != register — PrimeCode Phase 5 init failure |
| 3 | Verify RO: attempt write; read back. | Value unchanged after write attempt | Value changed — incorrectly writable |
| 4 | Run flexconPM DLCP sanity check. python flexconPM.py -i NWPSV.ini | flexconPM PASS | flexconPM FAIL — collect log |

---

### Pass / Fail Criteria

- **PASS**: SST_TF_INFO_10 readable; consistent with PCT_Module_Mask fuse; RO; flexconPM PASS.
- **FAIL**: Read error; fuse != register; register writable; flexconPM FAIL.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| PCT_Module_Mask fuse | sv.socket0.imh0.fuses.punit.pct_module_mask | Readable; determines DLCP scenario |
| SST_TF_INFO_10 CBB0 | sv.socket0.cbb0.base.tpmi.sst_tf_info_10 | Matches fuse; RO |
| SST_TF_INFO_10 CBB1 | sv.socket0.cbb1.base.tpmi.sst_tf_info_10 | Matches fuse; RO |

---

### Post-Process

No writes. Collect fuse value and SST_TF_INFO_10 for Scenario A/B record. Gate TC 2 on this result.

---

### References

- [https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — PCT_Module_Mask fuse; SST_TF_INFO_10 RO register; DLCP HP discovery
- [https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST TPMI register definitions
- [https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PCT scope; DLCP status TBD

