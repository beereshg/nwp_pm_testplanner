# Deep Analysis: [PSS] Core P-States Request Using PEGA Interface

| Field | Value |
|-------|-------|
| **HSD ID** | 16030715634 |
| **Title** | [PSS] Core P-States request using PEGA interface |
| **Target Program** | NWP (Newport) |
| **Feature** | Pstate Stack |
| **Segment** | PSS |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify **Core P-state requests via PEGA interface** in PSS (Pre-Si Simulation) environment: PEGA correctly receives per-core P-state requests; voting resolves to max-requested ratio; resolved ratio is enforced on cores. PSS-specific test validating PEGA microarchitecture behavior before silicon. NWP: 2 CBBs; 48 cores/CBB.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| PSS environment | NWP PSS simulation available |
| PEGA model | PEGA IP functional in PSS |
| Core model | Per-core P-state request mechanism present |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Issue per-core P-state requests via PEGA at various ratios. | PEGA receives requests; no interface errors | PEGA not responding — model issue |
| 2 | Verify PEGA voting: different ratios on different cores; verify max wins. | Max-requested ratio is resolved | Wrong ratio resolved — PEGA voting bug |
| 3 | Confirm resolved ratio applied to cores. | Core frequency = resolved PEGA ratio | Ratio not applied — P-state enforcement bug |

---

### Pass / Fail Criteria

- **PASS**: PEGA voting correct in PSS; resolved ratio applied to all cores.
- **FAIL**: PEGA interface error; wrong ratio resolved; ratio not applied.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| PEGA_REQ register | PSS PEGA model | Captures per-core requests |
| Resolved ratio | PEGA output | = max-requested |

---

### References

- [https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP PEGA interface; PSS P-state verification

