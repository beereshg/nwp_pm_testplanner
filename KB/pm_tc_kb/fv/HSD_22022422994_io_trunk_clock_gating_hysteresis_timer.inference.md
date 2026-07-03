# Deep Analysis: IO Trunk Clock gating — Hysteresis Timer

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422994](https://hsdes.intel.com/appstore/article-one/#/22022422994) |
| **Title** | IO Trunk Clock gating_Hysterisis Timer |
| **Date** | 2026-06-22 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | AIPM |
| **Sub-Feature** | IO Trunk Clock Gating — Hysteresis timer configuration checkout |
| **Parent TCD** | [22022421240 — MIO Trunk Clock gating Boot Time Setup](https://hsdes.intel.com/appstore/article-one/#/22022421240) |
| **NWP Disposition** | **Rejected — hysteresis timer is hardware default; PrimeCode does not program it; no runtime TCG entry to validate timing** |
| **Status** | rejected |
| **Owner** | bg3 |

## NWP Scope Clarification

> **Rejected on NWP** — the hysteresis timer is a **hardware default register** that PrimeCode
> does NOT explicitly program as part of MAS §9.1. Without PrimeCode programming it, there is
> no spec-defined expected value to verify. With no L1/PkgC on NWP, the timer never fires, so
> there is no runtime behavior to observe either.
>
> **Contrast with the other 3 Boot Time Setup TCs** (which remain open):
> - 22022422990 (QCh enabling): PrimeCode explicitly writes `ENABLE_AUTO_IDLE` → verifiable
> - 22022422992 (Auto Idle WP): PrimeCode explicitly writes `CR_CLK_WP_IDLE/ACTIVE` → verifiable
> - 22022423000 (RC Capability0): hardware discovery register always meaningful → verifiable
> - **22022422994 (Hysteresis Timer)**: PrimeCode does NOT write it → no programmed value to check

---

## Test Case Intent

Verify that PrimeCode correctly programs the **RC_MIO hysteresis timer** during PH6 per MAS §9.1.
The hysteresis timer controls the delay between QCh idle detection and trunk clock gate assertion.
Even though the timer never triggers on NWP (no L1), verifying the programmed value is correct
ensures the infrastructure is ready for future silicon with L1 support.

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP validation target with MIO trunk clock-gating boot setup flow enabled |
| FW stack | PrimeCode PH6 RC workpoint programming complete; PythonSV installed |
| Automation | `runPmx.py -x nwp.xml -p trunk_clkg -tM 6` (replace `dmr.xml`) |
| Note | Boot/setup hysteresis timer configuration check only |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Boot platform; verify clean PH6 completion | No BIOS hang, MCA, or soft hang | Hang or MCA during PH6 |
| 2 | Read RC_MIO hysteresis timer configuration registers (`HYSTERESIS_TIMER` / `IDLE_HYSTERESIS_TIMEOUT`) | Registers readable; non-zero programmed value | Unreadable or zero when non-zero expected |
| 3 | Compare programmed timer value against MAS §9.1 spec-defined default or PrimeCode-programmed target | Timer value matches expected NWP configuration | Mismatch vs spec/expected |
| 4 | Re-read after any platform sequencing; verify stability | Timer value consistent across re-reads | Value changes unexpectedly |
| 5 | Check logs/telemetry for timer-related PM configuration errors | No PM infrastructure or timer programming error | Error logged indicating misconfiguration |

### Pass / Fail Criteria

- **PASS**: Hysteresis timer programmed to expected value; registers stable; no hang/MCA; no PM config error
- **FAIL**: Timer = 0 when non-zero expected; mismatch vs spec; register instability; hang/MCA

> **DO NOT** use "hysteresis timer fired" or "trunk gating delay observed" as pass criteria — timer never fires on NWP.

---

## Section A: NWP Delta

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Runtime hysteresis firing | ✅ Verified via residency timing | ❌ Never triggered | Remove timing/delay observation; keep programming check |
| Boot-time timer programming | ✅ | ✅ (PH6) | Core of this TC |
| Hysteresis timer registers | RC_MIO MMIO | Same path — unchanged | No path change |
| Automation config | `dmr.xml` | `nwp.xml` | Config swap required |

---

## Section D: NWP Register Paths

| Register | NWP Namednodes Path | Description |
|----------|--------------------|----|
| Hysteresis timer | `sv.socket0.imh0.resctrl.rc_mio_ew.resctrl_prv_idle_timer` | RC idle hysteresis timeout value |
| QCh FSM policy | `sv.socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regss` | QCh FSM policy (enable_auto_idle + timer enable) |

### PythonSV Validation Sketch

```python
# Hysteresis timer checkout (NWP)
timer_val = sv.socket0.imh0.resctrl.rc_mio_ew.resctrl_prv_idle_timer.read()
print(f"RC idle hysteresis timer = {hex(timer_val)}  (expect non-zero per MAS §9.1)")
assert timer_val != 0, "Hysteresis timer must be programmed to non-zero value"

# Re-read for stability
timer_val2 = sv.socket0.imh0.resctrl.rc_mio_ew.resctrl_prv_idle_timer.read()
assert timer_val == timer_val2, f"Timer value changed: {hex(timer_val)} -> {hex(timer_val2)}"
print("PASS: Timer value stable")
```

---

## Section F: Recommendations

Keep open. Change automation from `dmr.xml` to `nwp.xml`. Remove any "hysteresis firing observed" from pass criteria. Validate programmed value only.

---

## Section G: PSS Grading

| Sl No | Dimension | Value | Rationale |
|-------|-----------|-------|-----------|
| 1 | NWP Delta | Yes | Remove firing/timing observation; config swap |
| 2 | Applicable NWP | Yes (boot-time) | Timer programmed at PH6 unconditionally |
| 3 | PSS Environment | HSLE | Boot register state verifiable on HSLE |
| 4 | Silicon Only | No | HSLE/VP feasible |
| 5 | Test Content | DMR_M | Medium: remove runtime expectations |
| 6 | OS | sv-os | PythonSV register reads |

### References

- [AIPM KB — aipm.md](../../pm_features/pm_cross_products/aipm.md) — RC boot-time programming
- [NWP PM MAS §9.1](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — RC workpoint + timer programming
- [RC TRM HAS](https://docs.intel.com/documents/sysip_pm/resource_controller/TRM/TRM.html) — Hysteresis timer register definitions
