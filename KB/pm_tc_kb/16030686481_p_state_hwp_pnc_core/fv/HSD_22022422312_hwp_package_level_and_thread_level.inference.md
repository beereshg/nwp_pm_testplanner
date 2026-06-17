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
