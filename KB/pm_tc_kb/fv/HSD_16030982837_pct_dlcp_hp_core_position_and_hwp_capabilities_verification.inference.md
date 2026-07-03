# Deep Analysis: PCT - DLCP HP Core Position and HWP Capabilities Verification

| Field | Value |
|-------|-------|
| **HSD ID** | [16030982837](https://hsdes.intel.com/appstore/article-one/#/16030982837) |
| **Title** | PCT - DLCP HP Core Position and HWP Capabilities Verification |
| **Target Program** | NWP (Newport) |
| **Feature** | SST / PCT / DLCP |
| **NWP Disposition** | **Runnable_On_N-1 (conditional: requires Scenario A from TC1)** |
| **Dependency** | TC1 (16030982833) must confirm SST_TF_INFO_10 != 0 |

---

### Test Case Intent

Verify HP cores identified by SST_TF_INFO_10 mask are correctly assigned CLOS[0] in SST_CLOS_ASSOC, and that IA32_HWP_CAPABILITIES.highest_perf differs between HP (P0max) and LP (LP_CLIP) cores in DLCP mode. Skip if TC1 confirms Scenario B (SST_TF_INFO_10 = 0).

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | sv.socket0.imh0 and CBBs accessible |
| DLCP active | TC1 confirmed SST_TF_INFO_10 != 0 (Scenario A); skip if = 0 |
| HWP | Can be enabled for step 3 |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Decode HP core APIC IDs from SST_TF_INFO_10 mask. | HP core list decoded; matches architectural expectation for fused mask | Zero mask — Scenario B; skip this TC |
| 2 | Read SST_CLOS_ASSOC for all decoded HP cores; verify = 0 (CLOS[0]). or hp_core in hp_cores: assert sv.socket0.cbb_x.tpmi.sst_clos_assoc[hp_core].read() == 0 | All HP cores in CLOS[0]; all LP in CLOS[3] | Mismatch — BIOS did not honor DLCP mask |
| 3 | Enable HWP; read IA32_HWP_CAPABILITIES (0x771) for HP and LP core samples. hp_cap=rdmsr(0x771, hp_core); lp_cap=rdmsr(0x771, lp_core); assert hp_cap.highest_perf > lp_cap.highest_perf | HP: highest_perf = P0max; LP: highest_perf = LP_CLIP; values differ | HP = LP — DLCP per-core HWP differentiation absent |
| 4 | Run workload; verify HP cores reach ~4.4 GHz; LP capped at LP_CLIP. | HP at PCT target; LP at P1 clip | HP not reaching target — CLOS config or TRL issue |

---

### Pass / Fail Criteria

- **PASS**: HP cores match DLCP mask; CLOS[0]; HWP caps differ per HP/LP; HP reaches 4.4 GHz.
- **FAIL**: CLOS mismatch; HWP caps identical; HP not reaching target.

---

### References

- [https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html) — SST_TF_INFO_10; DLCP CLOS assignment; HWP_CAPABILITIES per-core
- [https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST_CLOS_ASSOC; CLOS enforcement

