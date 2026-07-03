# Deep Analysis: SIMPL Policy 0 Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421906 |
| **Title** | SIMPL Policy 0 Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SIMPL - IccMax |
| **Sub-Feature** | SIMPL Policy 0 — verify policy is active and IO/Mem fabric freq within spec |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify **SIMPL Policy 0** is selected under core-heavy + light IO/Mem workload, and that IO/Mem fabric frequency limits match Policy 0 spec values. Policy 0 = maximum IO/Mem fabric frequency (least restrictive). `ti_gate.b0` / `NGA_MAIN`. NWP: single IMH (imh0). ⚠️ SIMPL ZBB per NWP PM MAS §3; FV team Runnable_On_N-1 pending confirmation.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| SV session | `sv.socket0.imh0` reachable |
| Workload tools | stress-ng (core), MBW or memory-bandwidth tool |
| SIMPL fuses | Verified (TC 22022421902) |
| PMx | `python runPmx.py -x nwp.xml -p simpl -tM 60` |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Start heavy core workload + light IO/Mem (e.g., stress-ng CPU cores, low memory BW). `import time; # start workload; time.sleep(5)` | System under core-heavy load; minimal IO/Mem fabric demand | Workload not running |
| 2 | Read `current_policy`. `cur = sv.socket0.imh0.pcudata.patch_persistent.current_policy.read(); print(f'current_policy={cur}')` | `current_policy = 0` (core-heavy + light IO/Mem → Policy 0) | Non-zero policy — IO/Mem demand higher than expected; reduce IO workload |
| 3 | Read IO and Mem fabric freq limits for Policy 0. `io_freq=sv.socket0.imh0.pcudata.simpl_max_freq_0_0.read(); mem_freq=sv.socket0.imh0.pcudata.simpl_max_freq_1_0.read(); print(f'IO={hex(io_freq)} Mem={hex(mem_freq)}')` | Freq limits match Policy 0 fuse values (IO=0xe); non-zero | Freq limits 0 or unexpected — fuse propagation failure |
| 4 | Run PMx SIMPL test. `python runPmx.py -x nwp.xml -p simpl -tM 60` | PMx PASS | PMx FAIL |

---

### Pass / Fail Criteria

- **PASS**: `current_policy=0` under core-heavy+light-IO workload; freq limits match Policy 0 spec; PMx PASS.
- **FAIL**: Wrong policy selected; freq limits mismatch; PMx FAIL.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| current_policy | sv.socket0.imh0.pcudata.patch_persistent.current_policy | = 0 under specified workload |
| target_policy | sv.socket0.imh0.pcudata.patch_persistent.target_policy | = 0 (no pending transition) |
| simpl_max_freq_0_0 | sv.socket0.imh0.pcudata.simpl_max_freq_0_0 | Policy 0 IO freq = 0xe |

---

### Post-Process

Stop workload. Verify policy returns to 0 at idle.

---

### References

- [DMR SIMPL HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_SIMPL.html) — Policy 0 definition; workload classification; IO/Mem freq limits table
- [DMR Fabric DVFS Data](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/assets/DMR_Fabric_DVFS.xlsx) — Policy 0 freq values; BW→policy mapping
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP SIMPL status; single IMH; new voltage rails

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Verifies SIMPL Policy 0 (default safe policy) is active under core-centric + light IO/Mem workload, and that IO/Mem Fabric frequency limits are within spec bounds for Policy 0.

NWP: single IMH (imh0). `sv.sockets.imhs` → `sv.socket0.imh0`. Note: source TC notes "Need to be updated for new SIMPL definition" — verify against latest NWP HAS.

Tags: `DMR_PO`, `plc.ti_gate.b0`, `NGA_MAIN`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP Command
```bash
python runPmx.py -x nwp.xml -p simpl -tM 60
```

### Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Start core-centric workload | Heavy core compute (e.g., stress-ng CPU) |
| 2 | Start light IO/Mem fabric workload | Light memory access pattern |
| 3 | Read `current_policy` | `sv.socket0.imh0.pcudata.patch_persistent.current_policy` |
| 4 | Verify `current_policy` = 0 | Policy 0 expected for heavy core + light IO/Mem |
| 5 | Read IO and Mem Fabric Freq Limits | `sv.socket0.imh0.pcudata.simpl_*` registers |
| 6 | Verify freqs within Policy 0 bounds | Per NWP HAS SIMPL Policy 0 table |

### NWP Register Paths
```python
current = sv.socket0.imh0.pcudata.patch_persistent.current_policy
assert current == 0, f"Expected Policy 0, got {current}"

# IO/Mem fabric freq limits for Policy 0
io_freq  = sv.socket0.imh0.pcudata.simpl_max_freq_0_0  # 0xe per fuse verification
mem_freq = sv.socket0.imh0.pcudata.simpl_max_freq_1_0
print(f"IO freq limit: {io_freq}, Mem freq limit: {mem_freq}")
```

### Pass Criteria
- `current_policy` = 0 on IMH0 under specified workload
- IO/Mem Fabric freq limits within spec for Policy 0
- No `target_policy` mismatch

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; `sv.sockets.imhs` → `sv.socket0.imh0`; verify Policy 0 freq limits against NWP HAS (update if HAS has changed since TC was authored)**

**Priority**: High — `PMSS_NWP_READINESS_CHECK`; Policy 0 is the default-always-active SIMPL policy
