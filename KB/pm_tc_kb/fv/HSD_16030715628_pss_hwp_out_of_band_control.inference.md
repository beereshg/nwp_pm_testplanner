# Deep Analysis: [PSS] HWP Out of Band Control

| Field | Value |
|-------|-------|
| **HSD ID** | [16030715628](https://hsdes.intel.com/appstore/article-one/#/16030715628) |
| **Title** | [PSS] HWP Out of Band Control |
| **Target Program** | NWP (Newport) |
| **Feature** | P-State / HWP |
| **Segment** | PSS |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Parent TCD** | [22022421006 - HWP OOB Mode](https://hsdes.intel.com/appstore/article-one/#/22022421006) |

---

### Test Case Intent

Verify **HWP Out-of-Band control** in PSS simulation environment: OOB management path (PECI/IPMI) can set HWP parameters (desired, min, max, EPP) independently of OS, and cores respond correctly. PSS validates the OOB HWP request path before silicon bring-up.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| PSS environment | NWP PSS simulation available |
| HWP OOB | OOB mode enabled in simulation |
| PECI model | PECI IP functional in PSS |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|--------------------|
| 1 | Enable HWP OOB mode in PSS; send OOB HWP desired=P0max. | Core targets P0max; OOB request received by Punit | No frequency change — OOB path not functional in PSS |
| 2 | Send OOB EPP=0 (performance); verify APS/frequency responds. | Performance-biased frequency | EPP not effective in OOB PSS mode |
| 3 | Send OOB desired=Pn (minimum); verify frequency drops. | Core at minimum frequency | Core stays at P0 — min not enforced via OOB |

---

### Pass / Fail Criteria

- **PASS**: OOB HWP requests modify core frequency in PSS; EPP effective; min/max enforced.
- **FAIL**: OOB requests ignored; frequency unresponsive; PSS OOB path broken.

---

### References

- [Core P-state HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) — HWP OOB mode; PECI HWP request path
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP OOB HWP; PSS context

---

## Section A: NWP Disposition

**Disposition: Runnable_On_N-1** — PSS baseline for OOB HWP path validation.

