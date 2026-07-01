# Deep Analysis: HWP Package Level and Thread Level Cross Product

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422312 |
| **Title** | HWP_Package_level_and_thread_level_cross_product |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | HWP — Package-level vs core-level HWP request resolution |
| **NWP Disposition** | **Runnable_On_N-1** |

---

### Test Case Intent

Verify **HWP package-level vs thread-level request resolution**: when `PACKAGE_CONTROL=1` in IA32_HWP_REQUEST, the core derives its parameters from IA32_HWP_REQUEST_PKG instead of its local request. Verify priority: PECI > Package > Thread. `pm.xproducts.pm` / `NGA_MAIN`.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| HWP | Enabled (`IA32_PM_ENABLE[0]=1`) |
| SV session | Per-core and package MSR access |
| Platform | Fully booted; no prior HWP requests active |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Write EPP=0 (performance) to IA32_HWP_REQUEST_PKG (0x772). Set PACKAGE_CONTROL=1 on all cores. | All cores use package EPP=0; frequency biased toward P0 | Cores still using thread EPP — PACKAGE_CONTROL bit not working |
| 2 | Write different EPP per thread (thread EPP=200); verify package EPP=0 still dominates. | Frequency biased toward performance despite thread EPP=200 | Thread EPP overriding package — wrong priority |
| 3 | Clear PACKAGE_CONTROL bit on one core; verify it reverts to its thread EPP. | That core uses thread EPP=200; others still use package EPP=0 | Per-core PACKAGE_CONTROL toggle not working |
| 4 | Apply PECI EPP override; verify it supersedes both package and thread requests on all cores. | All cores follow PECI EPP regardless of thread/package settings | PECI not overriding — check PECI enable path |

---

### Pass / Fail Criteria

- **PASS**: PACKAGE_CONTROL=1 routes to package request; PECI overrides all; per-core toggle works.
- **FAIL**: Wrong priority order; PACKAGE_CONTROL ineffective; PECI not overriding.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| IA32_HWP_REQUEST_PKG | MSR 0x772 | Package-level EPP/desired programmed |
| IA32_HWP_REQUEST | MSR 0x774 per core | PACKAGE_CONTROL bit[42]; EPP per thread |
| IA32_PERF_STATUS | MSR 0x198 per core | Frequency reflects correct EPP source |

---

### Post-Process

Clear PACKAGE_CONTROL on all cores. Remove PECI override. Restore thread HWP requests to defaults.

---

### References

- [Core P-state HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) — PACKAGE_CONTROL bit; package vs thread request resolution; PECI override priority
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP package/thread HWP request paths

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **HWP request resolution** when cores use either package-level HWP request or individual core-level HWP requests. Resolution rule:
- **Max** of `IA32_HWP_REQUEST.Min`, `IA32_HWP_REQUEST.Max`, `IA32_HWP_REQUEST.Desired` (performance floor/ceiling/target)
- **Min** of `IA32_HWP_REQUEST.EPP` (power/performance preference)

On NWP (non-SMT), "thread-level" becomes "core-level" — each physical core can have its own `IA32_HWP_REQUEST` or subscribe to the package-level request. The resolution logic is the same.

**Key Justification:**
- Package-level HWP request (`IA32_HWP_REQUEST_PKG`) + core-level requests present on NWP
- `DMR_PO` + `plc.feature.p2` + `PMSS_NWP_READINESS_CHECK` tags
- Non-SMT simplification: no thread aggregation within a core

---

## Section B: NWP-Specific Test Procedure

### Resolution Algorithm

```
For each core:
    if IA32_HWP_REQUEST.PKG_CONTROL_ENABLE:
        base_request = IA32_HWP_REQUEST_PKG
    else:
        base_request = IA32_HWP_REQUEST (per-core)

Resolved.Min = max(base_request.Min)
Resolved.Max = max(base_request.Max)
Resolved.Desired = max(base_request.Desired)
Resolved.EPP = min(base_request.EPP)
```

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Configure package-level HWP request | Write `IA32_HWP_REQUEST_PKG` with specific min/max/desired/EPP |
| 2 | Enable some cores to use package-level request | Set `IA32_HWP_REQUEST.PKG_CONTROL_ENABLE = 1` |
| 3 | Set individual core request on other cores | `IA32_HWP_REQUEST` per-core |
| 4 | Run hwpm_check | `python runPmx.py -x nwp.xml -p hwpm_check -tM 60` |
| 5 | Verify resolved request = max(min/max/desired), min(EPP) | Per-core `IA32_PERF_STATUS` |
| 6 | Verify package-level subscribing cores follow package request | Cores with PKG_CONTROL_ENABLE use package request |

### NWP Non-SMT Note
- "Thread-level" in DMR (2 threads/core) → "core-level" on NWP (1 thread/core)
- Each core has its own `IA32_HWP_REQUEST` — no intra-core thread aggregation needed
- Package-level request (`IA32_HWP_REQUEST_PKG`) applies globally per socket

### NWP Pass Criteria
- Cores subscribing to package request correctly use `IA32_HWP_REQUEST_PKG`
- Cores with individual requests use per-core values
- Resolution: max(min, max, desired) and min(EPP) correctly applied
- Verified on all 96 NWP cores (2 CBBs × 48)

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; non-SMT simplifies core-level request handling**

HWP package/core request resolution applicable on NWP. Non-SMT eliminates thread aggregation complexity.

Required adaptations:
1. `python runPmx.py -x nwp.xml -p hwpm_check -tM 60`
2. NWP: per-physical-core `IA32_HWP_REQUEST` (no thread index)
3. 2 CBBs × 48 cores = 96 resolution points to verify

**Priority**: High — `DMR_PO` + `plc.feature.p2`; HWP package vs core request resolution
