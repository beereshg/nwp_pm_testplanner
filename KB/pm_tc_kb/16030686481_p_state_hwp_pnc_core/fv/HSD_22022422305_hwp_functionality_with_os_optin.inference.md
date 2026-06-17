# Deep Analysis: HWP Functionality With OS Optin

| Field | Value |
|-------|-------|
| **HSD ID** | 22022422305 |
| **Title** | HWP Functionality with OS Optin |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | Pstate Stack |
| **Sub-Feature** | HWP Native Mode — OS optin via IA32_PM_ENABLE (MSR 0x770) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

In **HWP Native Mode**, the OS has the option to use HWP or legacy P-state interface. A HWP-agnostic OS uses legacy interface. When the OS opts in (writes to `IA32_PM_ENABLE` MSR 0x770, bit 0 = 1), HWP interface is enforced. The test verifies:
1. System uses legacy P-states before OS opts in
2. After OS optin (MSR 0x770), HWP interface is enforced
3. Transition from legacy to HWP mode is seamless

On NWP, same `IA32_PM_ENABLE` optin mechanism applies.

**Key Justification:**
- HWP OS optin via MSR 0x770 is architectural on NWP
- `plc.feature.p2` tag: P2 feature validation
- `PMSS_NWP_READINESS_CHECK` tag: evaluated for NWP

---

## Section B: NWP-Specific Test Procedure

### HWP Optin States

| State | IA32_PM_ENABLE[0] | P-state Interface | Effect |
|-------|-------------------|-------------------|--------|
| Before optin | 0 | Legacy (`IA32_PERF_CTL`) | HWP-agnostic OS can request ratios |
| After optin | 1 (write-once) | HWP (`IA32_HWP_REQUEST`) | Legacy writes ignored; HWP autonomous |

### Adapted Test Steps

| Step | Action | NWP Adaptation |
|------|--------|----------------|
| 1 | Boot NWP with `ProcessorHWPMEnable = 1` (native mode) | Same BIOS knob |
| 2 | Verify `IA32_PM_ENABLE[0] = 0` (before optin) | `rdmsr 0x770` per core |
| 3 | Run `hwpm_check` to exercise legacy interface | `python runPmx.py -x nwp.xml -p hwpm_check -tM 60` |
| 4 | OS opts in: write `IA32_PM_ENABLE[0] = 1` | `wrmsr 0x770 0x1` (write-once) |
| 5 | Verify optin persists (write-once bit) | `rdmsr 0x770` should return 1 |
| 6 | Verify HWP interface now enforced; legacy PERF_CTL ignored | Issue legacy P-state; HWP APS overrides |

### NWP Pass Criteria
- Before optin: legacy P-state requests via `IA32_PERF_CTL` are honored
- After optin: `IA32_PM_ENABLE[0] = 1` (write-once; cannot be cleared)
- After optin: HWP APS controls frequency autonomously
- No MCAs during mode transition

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; HWP optin mechanism is architectural MSR**

Required adaptations:
1. `python runPmx.py -x nwp.xml -p hwpm_check -tM 60`
2. NWP non-SMT: optin per physical core (96 cores; simpler than DMR multi-thread)
3. Verify `IA32_PM_ENABLE` (MSR 0x770) write-once enforcement on NWP

**Priority**: Low-Medium — no `DMR_PO`; HWP OS optin legacy→HWP transition validation
