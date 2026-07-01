# Deep Analysis: HWP OOB Mode Turbo Disabled Request Resolution

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422337 |
| **Title** | HWP OOB Mode Turbo Disabled Request Resolution |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | HWP OOB Mode — Turbo disabled, requests clipped to P1 (guaranteed) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify **HWP request resolution when Turbo is disabled** in OOB mode: when turbo is disabled (TURBO_DISABLE bit or BIOS knob), HWP max frequency must be capped at P1 (guaranteed ratio) even if OOB or in-band HWP request asks for higher. `plc.feature.p2`.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| HWP OOB | Mode enabled |
| Turbo | Can be enabled/disabled via BIOS or MSR |
| SV session | Per-core MSR access |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Disable turbo (`IA32_MISC_ENABLES[38]=1`); send OOB HWP request with MAX=P0max. | Frequency capped at guaranteed (P1) ratio; turbo not granted | Frequency exceeds P1 — turbo disable not enforced |
| 2 | Read IA32_PERF_STATUS; verify executed ratio = guaranteed. `rdmsr 0x198` | Executed ratio = guaranteed ratio | Above guaranteed — turbo granted despite disable |
| 3 | Re-enable turbo; send same OOB MAX=P0max request. | Frequency can now reach P0 turbo | Stuck at P1 — turbo re-enable not working |
| 4 | Verify IA32_HWP_CAPABILITIES.guaranteed_perf field matches P1 when turbo disabled. | guaranteed_perf = P1 ratio when turbo off | guaranteed_perf = P0max — wrong capability reporting |

---

### Pass / Fail Criteria

- **PASS**: Turbo disabled caps HWP at P1; re-enable allows turbo; capabilities reflect correctly.
- **FAIL**: Turbo granted despite disable; stuck at P1 after re-enable; capabilities wrong.

---

### References

- [Core P-state HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) — Turbo disable in HWP OOB mode; guaranteed ratio as max when turbo off
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP turbo disable + HWP interaction

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies that when HWP OOB mode is active and Turbo is disabled (`TurboMode = 0x0`), any HWP request above the guaranteed frequency (P1) is **clipped to P1**. Requests from Pn to P1 must be resolved correctly. Requests from P1 to P0n (turbo range) must be capped at P1.

Uses `hwpm_pmx.py` to generate HWP requests in OOB mode.

On NWP, the same turbo disabled clipping logic applies. Script is adapted: `dmr.xml` → `nwp.xml`.

**Key Justification:**
- Turbo disabled + OOB mode clipping applicable on NWP
- `New Content` + `plc.feature.p2` + `NGA_MAIN` + `PMSS_NWP_READINESS_CHECK` tags

---

## Section B: NWP-Specific Test Procedure

### Test Configuration

| BIOS Knob | Value | Purpose |
|-----------|-------|---------|
| `ProcessorHWPMEnable` | 0x2 | HWP OOB mode |
| `TurboMode` | 0x0 | Disable Turbo |

### Resolution Expectation

| HWP Request Ratio | Expected Resolution |
|-------------------|---------------------|
| Pn to P1 range | Resolved as requested (within P1 floor) |
| P1 exactly | Resolved at P1 (guaranteed) |
| P0 to P0n (turbo) | **Clipped to P1** — Turbo disabled |

### Adapted Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Boot with OOB + Turbo disabled | `ProcessorHWPMEnable = 0x2`, `TurboMode = 0x0` |
| 2 | Run hwpm_oob_turbo_dis check | `python runPmx.py -x nwp.xml -p hwpm_oob_turbo_dis -tM 60` |
| 3 | Issue HWP requests from Pn to P0n via PECI | `hwpm_pmx.py` OOB request sweep |
| 4 | Verify Pn–P1 requests resolved correctly | `IA32_PERF_STATUS` per-core |
| 5 | Verify turbo requests clipped to P1 | Max observed frequency = P1 |

### NWP Pass Criteria
- All HWP requests within Pn–P1 range: resolved correctly
- HWP requests above P1 (turbo): clipped to P1
- No MCAs during OOB turbo-disabled operation
- `IA32_PERF_STATUS` shows P1 max when turbo requests issued

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; turbo clip logic same in OOB mode**

Required adaptations:
1. `python runPmx.py -x nwp.xml -p hwpm_oob_turbo_dis -tM 60`
2. NWP turbo range and P1 value may differ — verify from `IA32_TURBO_RATIO_LIMIT` and `IA32_PERF_STATUS`
3. PECI EPP delivery via `hwpm_pmx.py` OOB path

**Priority**: Medium — `NGA_MAIN` + `plc.feature.p2`; OOB mode turbo disable clip validation
