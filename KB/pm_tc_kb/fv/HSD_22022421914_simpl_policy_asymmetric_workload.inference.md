# Deep Analysis: SIMPL Policy Asymmetric Workload

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421914 |
| **Title** | SIMPL Policy asymmetric workload |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SIMPL - IccMax |
| **Sub-Feature** | SIMPL asymmetric workload — different IO/Mem load per IMH to drive policy divergence |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify SIMPL policy selection under **asymmetric IO/Mem workload** on IMH0. Original intent: two IMHs with different load profiles to drive different policies. **NWP adaptation: single IMH0 only** — test verifies policy selection across varying IO/Mem BW ratios on the single IMH. `ti_gate.b0` / `NGA_MAIN`. ⚠️ SIMPL ZBB per NWP PM MAS §3.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` reachable |
| SIMPL fuses | Verified (TC 22022421902) |
| Workload tools | Asymmetric IO vs Mem bandwidth tools available |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Run IO-dominant workload (high IO BW, low Mem BW). Read `current_policy`. `cur=sv.socket0.imh0.pcudata.patch_persistent.current_policy.read(); print(f'IO-dominant policy={cur}')` | Policy selected based on IO demand (likely 1 or 2) | Unexpected policy — IO workload not driving BW above threshold |
| 2 | Switch to Mem-dominant workload (low IO BW, high Mem BW). Read `current_policy`. | Policy changes based on Mem demand | Policy unchanged — SIMPL not responding to Mem load |
| 3 | Run simultaneous heavy IO + heavy Mem (max combined). Read `current_policy`. `cur=sv.socket0.imh0.pcudata.patch_persistent.current_policy.read(); assert cur==3, f'Expected Policy 3 at max load'` | Policy 3 under max combined IO+Mem | Policy < 3 — workload not reaching Policy-3 BW threshold |
| 4 | Run PMx SIMPL test. `python runPmx.py -x nwp.xml -p simpl -tM 60` | PMx PASS | PMx FAIL |

---

### Pass / Fail Criteria

- **PASS**: Policy selection responds correctly to changing IO/Mem BW ratios; Policy 3 reached at max combined load; PMx PASS.
- **FAIL**: Policy static despite workload changes; Policy 3 not reached; PMx FAIL.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| current_policy | sv.socket0.imh0.pcudata.patch_persistent.current_policy | Changes with workload BW profile |
| target_policy | sv.socket0.imh0.pcudata.patch_persistent.target_policy | Tracks current_policy |

---

### Post-Process

Stop workload. Verify policy returns to 0 at idle.

---

### References

- [DMR SIMPL HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_SIMPL.html) — Asymmetric workload policy selection; IO vs Mem BW classification
- [DMR Fabric DVFS Data](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/assets/DMR_Fabric_DVFS.xlsx) — BW→policy threshold table; asymmetric load handling
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP: single IMH0 (no IMH1/2 per source TC); SIMPL ZBB status

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1 (with significant adaptation)**

Source TC intent: run asymmetric workloads on two separate IMHs (IMH0 heavy IO+Mem, IMH1 medium IO + heavy Mem) and verify different SIMPL policies resolve on each IMH.

**NWP critical adaptation**: NWP has **single IMH (imh0) only** — there is no IMH1. The TC's per-IMH asymmetric scenario cannot be run as designed. The adapted approach verifies SIMPL policy resolution under asymmetric IO/Mem load on the single IMH0, with varying workload ratios.

Source TC note: *"Revisit the test case with IMH2"* — NWP does not have IMH2 either.

Tags: `New_Content`, `plc.ti_gate.b0`, `NGA_MAIN`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP Adapted Command
```bash
python runPmx.py -x nwp.xml -p simpl -tM 60
```

### NWP Adaptation (Single IMH)

| Step | DMR Intent | NWP Adaptation |
|------|-----------|----------------|
| 1 | Heavy IO+Mem on IMH0 | Heavy IO + heavy Mem on `imh0` |
| 2 | Medium IO + Heavy Mem on IMH1 | **Not possible — no IMH1** |
| 3 | Verify policy 3 on both IMHs | Verify policy selection on IMH0 only |
| 4 | Check `current_policy` per IMH | `sv.socket0.imh0.pcudata.patch_persistent.current_policy` only |

### NWP Register Paths
```python
# NWP: imh0 only — no imh1
current = sv.socket0.imh0.pcudata.patch_persistent.current_policy
print(f"IMH0 SIMPL current_policy: {current}")
# Expected: highest policy achievable under max IO+Mem load
```

### Pass Criteria (NWP Adapted)
- SIMPL policy on IMH0 responds correctly to varying IO/Mem workload ratios
- Policy progression (0 → higher) observed as load increases
- No crash or MCA under asymmetric load variations

---

## Section F: Recommendation

**Recommendation: ADAPT — NWP has no IMH1; asymmetric multi-IMH test not possible; instead verify single-IMH SIMPL policy selection under varying IO/Mem load ratios; coordinate with SIMPL feature team to define NWP-specific asymmetric test vector**

**Priority**: Medium — `New_Content`; original asymmetric design requires 2 IMHs; NWP adaptation provides partial coverage of SIMPL workload-driven policy selection
