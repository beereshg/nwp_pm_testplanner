# Deep Analysis: IO Trunk Clock gating — Auto Idle WP Checkout

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422992](https://hsdes.intel.com/appstore/article-one/#/22022422992) |
| **Title** | IO Trunk Clock gating_Auto Idle WP checkout |
| **Date** | 2026-06-22 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | AIPM |
| **Sub-Feature** | IO Trunk Clock Gating — Auto Idle Workpoint configuration checkout |
| **Parent TCD** | [22022421240 — MIO Trunk Clock gating Boot Time Setup](https://hsdes.intel.com/appstore/article-one/#/22022421240) |
| **NWP Disposition** | **Open — boot-time workpoint register checkout only** |
| **Status** | open |
| **Owner** | bg3 |

## NWP Scope Clarification

> **No L1, no PkgC on NWP** → trunk clock gating entry never fires at runtime.
> This TC validates **boot-time Auto Idle Workpoint (WP) programming correctness** only.
> Runtime TCG entry, residency, and L1/PkgC-triggered behavior are explicitly out of scope.

---

## Test Case Intent

Verify that PrimeCode correctly programs the **Auto Idle Workpoint** (`CR_CLK_WP_IDLE`, `CR_VR_WP_IDLE`)
for the RC_MIO during PH6 boot initialization per MAS §9.1. The idle WP defines the clock/voltage
state the RC would transition to if trunk gating ever fired — verifying it is correctly programmed
ensures NWP is ready for future silicon where L1 may be enabled.

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP validation target with MIO trunk clock-gating boot setup flow enabled |
| FW stack | PrimeCode PH6 RC workpoint programming complete; PythonSV installed |
| Automation | `runPmx.py -x nwp.xml -p trunk_clkg -tM 6` (replace `dmr.xml`) |
| Note | Boot/setup workpoint validation only; no runtime entry expected |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Boot platform; verify clean PH6 completion | No BIOS hang, MCA, or soft hang | Hang or MCA during PH6 |
| 2 | Read `CR_CLK_WP_ACTIVE` and `CR_CLK_WP_IDLE` from RC_MIO workpoint registers | Both registers readable; idle WP ≠ active WP | Unreadable or identical values |
| 3 | Read `CR_VR_WP_ACTIVE` and `CR_VR_WP_IDLE` (voltage-rail WP) | Idle voltage WP programmed to lower power state than active WP | WP not programmed or equal |
| 4 | Compare programmed WP values against LFCLK/FIVR RA-derived expected values per MAS §9.1 | WPs match RA-sourced expected values | Mismatch vs expected |
| 5 | Re-read registers after any sequencing; verify stability | Values consistent across re-reads | Read instability or drift |

### Pass / Fail Criteria

- **PASS**: Active and idle WPs programmed, distinct, match MAS §9.1 RA-derived values; registers stable; no hang/MCA
- **FAIL**: WPs not programmed, identical, mismatched vs RA values, or read instability

> **DO NOT** use "idle WP transition observed at runtime" as pass criteria — trunk gating never fires on NWP.

---

## Section A: NWP Delta

| Aspect | DMR | NWP | Impact |
|--------|-----|-----|--------|
| Runtime WP transition | ✅ Observed on TCG entry | ❌ Never triggered | Remove transition check; keep programming check |
| Boot-time WP programming | ✅ | ✅ (PH6) | Core of this TC |
| RC workpoint registers | `sv.socket0.imh0.resctrl.rc_mio_ew.*` | Same path — unchanged | No path change needed |
| Automation config | `dmr.xml` | `nwp.xml` | Config swap required |

---

## Section D: NWP Register Paths

| Register | NWP Namednodes Path | Description |
|----------|--------------------|----|
| Active clock WP | `sv.socket0.imh0.resctrl.rc_mio_ew.cr_clk_wp_active` | Active-state clock workpoint |
| Idle clock WP | `sv.socket0.imh0.resctrl.rc_mio_ew.cr_clk_wp_idle` | Idle-state clock workpoint |
| Active voltage WP | `sv.socket0.imh0.resctrl.rc_mio_ew.cr_vr_wp_active` | Active-state voltage workpoint |
| Idle voltage WP | `sv.socket0.imh0.resctrl.rc_mio_ew.cr_vr_wp_idle` | Idle-state voltage workpoint |
| QVFS enable | `sv.socket0.imh0.resctrl.rc_mio_ew.qvfs_enable` | QVFS autonomous enable bit |

### PythonSV Validation Sketch

```python
# Auto Idle WP checkout (NWP)
clk_active = sv.socket0.imh0.resctrl.rc_mio_ew.cr_clk_wp_active.read()
clk_idle   = sv.socket0.imh0.resctrl.rc_mio_ew.cr_clk_wp_idle.read()
vr_active  = sv.socket0.imh0.resctrl.rc_mio_ew.cr_vr_wp_active.read()
vr_idle    = sv.socket0.imh0.resctrl.rc_mio_ew.cr_vr_wp_idle.read()
qvfs_en    = sv.socket0.imh0.resctrl.rc_mio_ew.qvfs_enable.read()

print(f"CLK WP: active={hex(clk_active)} idle={hex(clk_idle)}")
print(f"VR  WP: active={hex(vr_active)} idle={hex(vr_idle)}")
print(f"QVFS enable={qvfs_en}  (expect 1)")
assert clk_idle != clk_active, "Idle WP must differ from active WP"
assert vr_idle  != vr_active,  "Voltage idle WP must differ from active WP"
```

---

## Section F: Recommendations

Keep open. Change automation from `dmr.xml` to `nwp.xml`. Remove any runtime WP-transition observation from pass criteria. Focus on programmed value correctness per MAS §9.1.

---

## Section G: PSS Grading

| Sl No | Dimension | Value | Rationale |
|-------|-----------|-------|-----------|
| 1 | NWP Delta | Yes | Remove runtime transition; add RA-value comparison; config swap |
| 2 | Applicable NWP | Yes (boot-time) | WP programming happens unconditionally at PH6 |
| 3 | PSS Environment | HSLE | Boot-time register state verifiable on HSLE |
| 4 | Silicon Only | No | HSLE/VP feasible |
| 5 | Test Content | DMR_M | Medium: remove runtime expectations, add NWP expected values |
| 6 | OS | sv-os | PythonSV register reads |

### References

- [AIPM KB — aipm.md](../../pm_features/pm_cross_products/aipm.md) — §9.1 RC boot-time WP programming
- [NWP PM MAS §9.1](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — RC workpoint programming
- [RC TRM HAS](https://docs.intel.com/documents/sysip_pm/resource_controller/TRM/TRM.html) — Workpoint register definitions
