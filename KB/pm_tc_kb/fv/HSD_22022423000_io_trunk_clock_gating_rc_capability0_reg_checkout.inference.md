# Deep Analysis: IO Trunk Clock gating — RC Capability0 Register Checkout

| Field | Value |
|-------|-------|
| **HSD ID** | [22022423000](https://hsdes.intel.com/appstore/article-one/#/22022423000) |
| **Title** | IO Trunk Clock gating_RC Capability0 reg checkout |
| **Date** | 2026-06-22 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | AIPM |
| **Sub-Feature** | IO Trunk Clock Gating — RC Capability0 register discovery checkout |
| **Parent TCD** | [22022421240 — MIO Trunk Clock gating Boot Time Setup](https://hsdes.intel.com/appstore/article-one/#/22022421240) |
| **NWP Disposition** | **Open — RC capability register checkout; validates NWP RC variant** |
| **Status** | open |
| **Owner** | bg3 |

## NWP Scope Clarification

> **No L1, no PkgC on NWP** → trunk clock gating entry never fires at runtime.
> This TC validates **RC Capability0 register contents** — confirming the NWP RC_MIO variant
> (Gen4 lnpv) is present and correctly discoverable. No runtime TCG validation implied.

---

## Test Case Intent

Verify that **RC Capability0** (`resctrl_prv_capability0`) is populated with the correct values
for the NWP RC_MIO Gen4 lnpv variant: `NUM_QCH_LATE=9`, `NUM_QCH_NOISE=9`,
`NUM_IDLE_WORKPOINTS=2`. This is a **discovery/sanity checkout** — confirming the RC IP
instance matches the expected NWP configuration and that PrimeCode boot programming is
targeting the correct variant.

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP validation target with RC_MIO accessible post-boot |
| FW stack | PrimeCode PH6 RC programming complete; PythonSV installed |
| Automation | `runPmx.py -x nwp.xml -p trunk_clkg -tM 6` (replace `dmr.xml`) |
| Note | Register capability/discovery validation only |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Boot platform; verify clean PH6 completion | No BIOS hang, MCA, or soft hang | Hang or MCA during PH6 |
| 2 | Read `resctrl_prv_capability0` register | Register readable; returns non-zero | Unreadable or zero |
| 3 | Verify `NUM_QCH_LATE` field = 9 (NWP Gen4 lnpv) | `NUM_QCH_LATE` = 9 | Wrong value (e.g., 4 for earlier variant) |
| 4 | Verify `NUM_QCH_NOISE` field = 9 | `NUM_QCH_NOISE` = 9 | Wrong value |
| 5 | Verify `NUM_IDLE_WORKPOINTS` field = 2 (active WP + idle WP) | `NUM_IDLE_WORKPOINTS` = 2 | Wrong value |
| 6 | Re-read for stability; check no PM config errors in logs | Consistent values across re-reads; no errors | Value instability or PM error |

### Pass / Fail Criteria

- **PASS**: All three fields (`NUM_QCH_LATE`=9, `NUM_QCH_NOISE`=9, `NUM_IDLE_WORKPOINTS`=2) match NWP Gen4 lnpv spec; registers stable; no hang/MCA
- **FAIL**: Any field mismatch; register unreadable; hang/MCA; PM config error

> **DO NOT** use "RC entered idle state" or "capability enabled runtime TCG" as pass criteria.

---

## Section A: NWP Delta

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| RC variant | Gen4 lnpv | Gen4 lnpv (same) | Expected values identical to DMR |
| NUM_QCH_LATE | 9 | 9 | Same |
| NUM_QCH_NOISE | 9 | 9 | Same |
| NUM_IDLE_WORKPOINTS | 2 | 2 | Same |
| Register path | `sv.socket0.imh0.resctrl.rc_mio_ew.*` | Same — unchanged | No path change |
| Automation config | `dmr.xml` | `nwp.xml` | Config swap required |

---

## Section D: NWP Register Paths

| Register | NWP Namednodes Path | Expected Value (NWP) |
|----------|--------------------|----|
| RC Capability0 | `sv.socket0.imh0.resctrl.rc_mio_ew.resctrl_prv_capability0` | See fields below |
| `NUM_QCH_LATE` | `.resctrl_prv_capability0.num_qch_late` | 9 |
| `NUM_QCH_NOISE` | `.resctrl_prv_capability0.num_qch_noise` | 9 |
| `NUM_IDLE_WORKPOINTS` | `.resctrl_prv_capability0.num_idle_workpoints` | 2 |

### PythonSV Validation Sketch

```python
# RC Capability0 checkout (NWP)
cap0 = sv.socket0.imh0.resctrl.rc_mio_ew.resctrl_prv_capability0

num_qch_late  = cap0.num_qch_late.read()
num_qch_noise = cap0.num_qch_noise.read()
num_idle_wp   = cap0.num_idle_workpoints.read()

print(f"NUM_QCH_LATE      = {num_qch_late}  (expect 9)")
print(f"NUM_QCH_NOISE     = {num_qch_noise}  (expect 9)")
print(f"NUM_IDLE_WP       = {num_idle_wp}   (expect 2)")

assert num_qch_late  == 9, f"NUM_QCH_LATE mismatch: {num_qch_late}"
assert num_qch_noise == 9, f"NUM_QCH_NOISE mismatch: {num_qch_noise}"
assert num_idle_wp   == 2, f"NUM_IDLE_WORKPOINTS mismatch: {num_idle_wp}"
print("PASS: RC Capability0 matches NWP Gen4 lnpv spec")
```

---

## Section F: Recommendations

Keep open. Change automation from `dmr.xml` to `nwp.xml`. This is the highest-value infrastructure checkout TC — if NUM_QCH_LATE or NUM_QCH_NOISE is wrong, all other AIPM TCs will be running against a misconfigured RC.

---

## Section G: PSS Grading

| Sl No | Dimension | Value | Rationale |
|-------|-----------|-------|-----------|
| 1 | NWP Delta | Yes (minor) | Expected values same; config swap; remove runtime framing |
| 2 | Applicable NWP | Yes | RC Capability0 is readable on NWP; critical infrastructure sanity |
| 3 | PSS Environment | HSLE | Register readable on HSLE; no runtime TCG needed |
| 4 | Silicon Only | No | HSLE/VP feasible |
| 5 | Test Content | DMR_L | Low adaptation: same expected values, just config swap + scope clarification |
| 6 | OS | sv-os | PythonSV register reads |

### References

- [AIPM KB — aipm.md](../../pm_features/pm_cross_products/aipm.md) — RC Gen4 lnpv variant details
- [RC TRM HAS](https://docs.intel.com/documents/sysip_pm/resource_controller/TRM/TRM.html) — Capability0 register field definitions
- [NWP PM MAS §9.1](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — RC boot programming
- [NWP MIO MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/mio/nwp_nio_mio.html) — NWP RC instance topology
