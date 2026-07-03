# Deep Analysis: [PSS] MSR 0x198 UCODE_CR_PERF_STATUS

| Field | Value |
|-------|-------|
| **HSD ID** | 16030715636 |
| **Title** | [PSS] MSR 0x198 (UCODE_CR_PERF_STATUS) |
| **Target Program** | NWP (Newport) |
| **Feature** | Pstate Stack |
| **Segment** | PSS |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify **MSR 0x198 (IA32_PERF_STATUS / UCODE_CR_PERF_STATUS)** correctness: the current executed P-state ratio is readable and reflects the actual operating frequency. PSS test — runs in simulation/emulation environment. Key assertion: MSR 0x198 upper 16 bits report current core ratio in sync with IA32_PERF_CTL requests.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| PSS environment | NWP PSS simulation/emulation available |
| P-state | Legacy P-state enabled (HWP=0) |
| MSR access | Per-core MSR read via NWP PSS infrastructure |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Write target ratio to IA32_PERF_CTL (0x199). | Write accepted | Write failure — check BIOS SpeedStep knob |
| 2 | Wait for ratio to settle; read IA32_PERF_STATUS (0x198). perf_status = rdmsr(0x198); cur_ratio = (perf_status >> 8) & 0x1F | Current ratio matches requested ratio | Ratio mismatch — P-state not achieved |
| 3 | Repeat for P0, P1, Pm ratio transitions. | All transitions complete correctly | Ratio stuck — PEGA voting issue |

---

### Pass / Fail Criteria

- **PASS**: MSR 0x198 reports correct ratio for each requested P-state in PSS.
- **FAIL**: Ratio mismatch; MSR not updating.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| IA32_PERF_STATUS | MSR 0x198 per core | Upper 16 bits = current ratio |
| IA32_PERF_CTL | MSR 0x199 per core | Write target ratio |

---

### References

- [https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PSS P-state MSR support
- Intel SDM Vol.3 — IA32_PERF_STATUS (0x198) definition

