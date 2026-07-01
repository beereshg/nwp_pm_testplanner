# Deep Analysis: Legacy Pstate TSC Accuracy Silicon

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422250 |
| **Title** | Legacy Pstate TSC accuracy, PCNT, ACNT, MCNT_silicon |
| **Target Program** | NWP (Newport) |
| **Feature** | Pstate Stack |
| **NWP Disposition** | **Runnable_On_N-1** (Silicon Only) |

---

### Test Case Intent

Verify **TSC (Time Stamp Counter), PCNT (P-state Count), ACNT (Actual Count), MCNT (Max Count)** accuracy on NWP silicon. Validates that APERF/MPERF-based effective frequency matches actual P-state behavior; TSC is invariant; PCNT/ACNT/MCNT ratios are consistent with requested and executed P-states. Silicon-only test requiring real hardware timing. NWP: no SMT; 2 CBBs; 48 cores/CBB.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Silicon | NWP silicon (not emulator/VP) |
| SV session | sv.socket0.imh0 and core MSR access available |
| HWP | Disabled for legacy P-state mode |
| P-state knobs | SpeedStep enabled; known P0 ratio |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Read TSC frequency at known P-state (P0). Read APERF and MPERF over a fixed time window. import time; # rdmsr APERF=0xE8, MPERF=0xE7 per core | TSC invariant; APERF/MPERF ratio = effective freq / max freq | TSC not invariant — clock issue; APERF/MPERF wrong — C-state or throttle |
| 2 | Verify effective frequency from APERF/MPERF matches expected P-state ratio. ff_ratio = aperf_delta / mperf_delta * max_ratio; assert abs(eff_ratio - requested_ratio) < 1 | Effective ratio within +-1 bin of requested ratio | Large discrepancy — execution not reaching requested ratio |
| 3 | Verify PCNT/ACNT/MCNT consistency per core across all 96 NWP cores. | All core counters self-consistent | Counter mismatch — core-level issue |
| 4 | Run flexconPM validation. python flexcon.py -i NWPSV.ini --onlyspecifiedmodules -m flexconPM | flexconPM PASS | flexconPM FAIL |

---

### Pass / Fail Criteria

- **PASS**: TSC invariant; APERF/MPERF ratio consistent with P-state; PCNT/ACNT/MCNT consistent; flexconPM PASS.
- **FAIL**: TSC drift; ratio mismatch; counter inconsistency; flexconPM FAIL.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| APERF | Per-core MSR 0xE8 | Increments at actual core freq |
| MPERF | Per-core MSR 0xE7 | Increments at max freq |
| TSC | RDTSC | Invariant across C-states |

---

### Post-Process

Collect MSR dump on failure. Verify no C-state activity during measurement window.

---

### References

- [https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP TSC; APERF/MPERF; core counter support
- Intel SDM Vol.3 — APERF (0xE8) / MPERF (0xE7) / TSC definitions

