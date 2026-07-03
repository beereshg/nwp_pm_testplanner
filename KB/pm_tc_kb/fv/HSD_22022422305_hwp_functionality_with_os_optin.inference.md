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

### Test Case Intent

Verify end-to-end **HWP Native Mode** functionality after OS optin via `IA32_PM_ENABLE.HWP_ENABLE = 1`: HWP capabilities readable, HWP request fields accepted, per-core frequency governed by HWP policy, and system stable throughout. This is the primary HWP functional validation. `plc.feature.p1` / `NGA_MAIN`. NWP: 2 CBBs x 48 cores.

---

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| HWP | Disabled initially (legacy P-state mode) |
| SV session | Per-core MSR access available |
| BIOS | HWPMEnable = Enabled |
| PMx | `python runPmx.py -x nwp.xml -p hwp -tM 60 -M 5` |

---

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|----------------------|-------------------|
| 1 | Write IA32_PM_ENABLE[0]=1 to enable HWP. `wrmsr 0x770 0x1` | IA32_PM_ENABLE[0]=1 (sticky; cannot be unset without reset) | = 0 after write — BIOS HWPMEnable not set |
| 2 | Read IA32_HWP_CAPABILITIES per core; verify highest_perf, guaranteed, efficient, lowest_perf. `rdmsr 0x771 per core` | Non-zero values; highest_perf ≥ guaranteed > efficient ≥ lowest_perf; consistent across all 96 cores | Any core returns 0 or inverted values |
| 3 | Write HWP request: min=guaranteed, max=highest, desired=0 (autonomous), EPP=128. `wrmsr 0x774 per core` | Request accepted; autonomous APS governs frequency | Frequency stuck — HWP request not being enforced |
| 4 | Write explicit desired=P0 ratio; verify frequency. | Frequency at P0 (explicit request honored) | Frequency does not reach P0 |
| 5 | Write desired=lowest_perf; verify frequency reduced. | Frequency near Pn (minimum) | Frequency stays high — minimum not enforced |
| 6 | Run PMx HWP end-to-end. `python runPmx.py -x nwp.xml -p hwp -tM 60 -M 5` | PMx PASS | PMx FAIL |

---

### Pass / Fail Criteria

- **PASS**: IA32_PM_ENABLE sticky; capabilities non-zero; HWP request governs frequency; explicit and autonomous modes work; PMx PASS.
- **FAIL**: Sticky bit fails; capabilities 0; request not governing frequency; PMx FAIL.

---

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|-------------------|
| IA32_PM_ENABLE | MSR 0x770 | [0]=1 after write; sticky |
| IA32_HWP_CAPABILITIES | MSR 0x771 per core | highest_perf ≥ guaranteed ≥ efficient ≥ lowest_perf |
| IA32_HWP_REQUEST | MSR 0x774 per core | Accepted; governs frequency |
| IA32_PERF_STATUS | MSR 0x198 per core | Reflects HWP-governed frequency |

---

### Post-Process

Collect PMx log on failure. Note: IA32_PM_ENABLE[0] is sticky — requires platform reset to return to legacy P-state mode.

---

### References

- [Core P-state HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) — IA32_PM_ENABLE; HWP_CAPABILITIES; HWP_REQUEST fields; explicit vs autonomous mode
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP HWP Native mode; 96-core topology

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
