# Deep Analysis: IO Trunk Clock Gating — Late QChannel and Noise QCh Enabling

| Field | Value |
|-------|-------|
| **HSD ID** | [22022422990](https://hsdes.intel.com/appstore/article-one/#/22022422990) |
| **Title** | IO Trunk Clock Gating_Late QChannel and Noise QCh enabling |
| **Date** | 2026-06-22 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | AIPM |
| **Sub-Feature** | IO Trunk Clock Gating — QCh autonomous-idle enable configuration |
| **Parent TCD** | [22022421240 — MIO Trunk Clock gating Boot Time Setup](https://hsdes.intel.com/appstore/article-one/#/22022421240) |
| **NWP Disposition** | **Open — boot-time register config checkout only** |
| **Status** | open |
| **Owner** | bg3 |

## NWP Scope Clarification

> **No L1, no PkgC on NWP** → trunk clock gating entry never fires at runtime.
>
> This TC is applicable to NWP **only** as a **boot-time QCh autonomous-idle configuration checkout**.
> The DMR-origin framing ("trigger idle/power-state transition", "residency observed") must NOT be applied on NWP.

## Version History
- v1 (2026-06-22): New — NWP-rewritten from stale DMR content; remove runtime entry/residency expectations

---

## Test Case Intent

Verify that the **late Q-Channel and noise Q-Channel autonomous-idle enable configuration** is
programmed correctly for the MIO trunk clock-gating infrastructure after boot. PrimeCode programs
`QCH_FSM_POLICY.ENABLE_AUTO_IDLE` and strap defaults per MAS §9.1 during PH6.

**On NWP** (no L1, no PkgC): trunk clock gating never fires at runtime. This TC confirms the
**register plumbing is correct** — correct strap/policy values, no hang/MCA after setup, state
preserved across re-reads. It is explicitly **not** a runtime entry/residency test.

**Reference**: [HSD 22021621791](https://hsdes.intel.com/appstore/article-one/#/22021621791) — MIO TCG spec update for UXI link (RC autonomous-idle strap/policy definitions)

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP validation target with AIPM boot-time setup flow enabled |
| FW stack | PrimeCode PH6 RC workpoint programming complete; PythonSV installed |
| BIOS | AIPM feature not force-disabled (`pcode_aipm_mio_trunk_clock_gating_disable` = 0) |
| Automation | `runPmx.py -x nwp.xml -p trunk_clkg -tM 6` (NWP config — replace `dmr.xml`) |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|--------------------|
| 1 | Boot platform; verify no BIOS hang or MCA during PH6 RC programming | Clean boot; PrimeCode RC workpoint programming completes without error | BIOS hang, MCA, or soft hang |
| 2 | Read `QCH_FSM_POLICY.ENABLE_AUTO_IDLE` for all late QCh instances (`resctrl_prvt_idle_late_regss`) | `enable_auto_idle` = 1 for enabled stacks per MAS §9.1 | Bit = 0 on expected stacks; or register unreadable |
| 3 | Read `QCH_FSM_POLICY.ENABLE_AUTO_IDLE` for noise QCh instances (`resctrl_prvt_idle_noise_regs0`) | `enable_auto_idle` = 1 for enabled stacks per MAS §9.1 | Bit = 0 on expected stacks |
| 4 | Read late/noise QCh strap defaults (`strap_l_autonomous_idle_enable_default`, `strap_n_autonomous_idle_enable_default`) | Strap values match PrimeCode-programmed enable mask; consistent across re-reads | Strap mismatch or read instability |
| 5 | Confirm disabled stacks have AIPM skipped (CMPL_STATUS=2 path, MAS §9.2) | Disabled stacks: `ENABLE_AUTO_IDLE` = 0; PrimeCode did not program AIPM for them | Disabled stack incorrectly shows AIPM enabled |

### Pass / Fail Criteria

- **PASS**: All `ENABLE_AUTO_IDLE` bits match expected programmed values per MAS §9.1; strap defaults consistent; no hang/MCA; disabled stacks correctly skipped
- **FAIL**: Any `ENABLE_AUTO_IDLE` mismatch; BIOS hang or MCA; disabled stack incorrectly enabled; register read instability

> **DO NOT** use "residency observed" or "autonomous entry confirmed" as pass criteria on NWP — trunk gating entry never fires (no L1 trigger).

---

## Section A: NWP Delta

| Aspect | DMR | NWP | Impact on This TC |
|--------|-----|-----|-------------------|
| Runtime TCG entry | ✅ L1-triggered | ❌ No L1, no PkgC | Remove entry/residency expectations entirely |
| Boot-time QCh programming | ✅ Active | ✅ Active | Core of this TC — still valid |
| QCh FSM policy registers | `sv.socket0.imh0.resctrl.*` | Same path — unchanged | No path change needed |
| RC Gen4 lnpv variant | ✅ | ✅ | NUM_QCH_LATE=9, NUM_QCH_NOISE=9 |
| Automation config | `runPmx.py -x dmr.xml` | `runPmx.py -x nwp.xml` | **Config file swap required** |

---

## Section B: Interactions

| Step | Actor | Action |
|------|-------|--------|
| 1 | PrimeCode (PH6) | Reads LFCLK RA → programs `QCH_FSM_POLICY.ENABLE_AUTO_IDLE` per §9.1 |
| 2 | PrimeCode (PH6) | §9.2: skips disabled stacks (CMPL_STATUS=2) → does NOT enable AIPM |
| 3 | Test/PythonSV | Reads all late/noise QCh policy registers; compares to expected enable mask |

---

## Section C: Coverage

| Coverage Area | NWP Applicable | Notes |
|--------------|----------------|-------|
| Late QCh `ENABLE_AUTO_IDLE` programming | ✅ Yes | Core of TC |
| Noise QCh `ENABLE_AUTO_IDLE` programming | ✅ Yes | Core of TC |
| Strap default verification | ✅ Yes | Validate strap values post-boot |
| Disabled stack skip (CMPL_STATUS=2) | ✅ Yes | Negative correctness check |
| Runtime TCG entry/residency | ❌ No | Not applicable — no L1 on NWP |
| L1-triggered autonomous idle | ❌ No | L1 ZBB'd — no trigger available |

---

## Section D: Spec Refs & NWP Register Paths

| Register | NWP Namednodes Path | Description |
|----------|--------------------|----|
| Late QCh FSM policy | `sv.socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regss` | `ENABLE_AUTO_IDLE` bit per late QCh |
| Noise QCh FSM policy | `sv.socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_noise_regs0` | `ENABLE_AUTO_IDLE` bit for noise QCh |
| Late QCh strap default | `sv.socket0.imh0.resctrl.rc_mio_ew.strap_l_autonomous_idle_enable_default` | Default enable mask from strap |
| Noise QCh strap default | `sv.socket0.imh0.resctrl.rc_mio_ew.strap_n_autonomous_idle_enable_default` | Default enable mask from strap |
| AIPM fuse disable | `sv.sockets.imhs.fuses.punit.pcode_aipm_mio_trunk_clock_gating_disable` | Must be 0 for AIPM enabled |

### PythonSV Validation Sketch

```python
# Boot-time QCh enable verification (NWP)
# Check late QCh autonomous-idle enable programming
for ch in range(9):  # NUM_QCH_LATE = 9 (Gen4 lnpv)
    en = sv.socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_late_regss[ch].qch_fsm_policy.enable_auto_idle.read()
    print(f"Late QCh[{ch}] ENABLE_AUTO_IDLE = {en}")

# Check noise QCh autonomous-idle enable programming
for ch in range(9):  # NUM_QCH_NOISE = 9
    en = sv.socket0.imh0.resctrl.rc_mio_ew.resctrl_prvt_idle_noise_regs0[ch].i_qch_ctrl.enable_auto_idle.read()
    print(f"Noise QCh[{ch}] ENABLE_AUTO_IDLE = {en}")

# Check AIPM not globally disabled
fuse_dis = sv.sockets.imhs.fuses.punit.pcode_aipm_mio_trunk_clock_gating_disable.read()
print(f"AIPM disable fuse = {fuse_dis}  (expect 0)")
```

---

## Section E: Risk Assessment

| # | Risk | Severity | Notes |
|---|------|----------|-------|
| 1 | Automation still uses `dmr.xml` in HSD description | Medium | Must change to `nwp.xml` before execution |
| 2 | Old pass criteria reference "residency/entry" — inapplicable on NWP | High | Must be removed from TC description |
| 3 | strap default values may differ between DMR and NWP RC variant | Low | Read and compare vs MAS §9.1 expected values |

---

## Section F: Recommendations

**Keep TC open — rewrite description to remove DMR-inherited runtime entry language.**

Specific changes needed in HSD TC description:
1. **Remove**: "trigger the target idle/power-state transition" and "Target transition/residency is observed"
2. **Replace with**: boot-time register configuration checkout steps (see Test Steps above)
3. **Change automation**: `dmr.xml` → `nwp.xml`
4. **Update scope**: explicitly state "no runtime TCG entry validation on NWP — no L1"
5. **Keep references**: HSD 22021621791 (UXI TCG spec) + MAS §9.1 link

---

## Section G: PSS Grading

| Sl No | Dimension | Value | Rationale |
|-------|-----------|-------|-----------|
| 1 | NWP Delta | Yes | Remove runtime entry/residency; add §9.2 disabled-stack skip; config file swap |
| 2 | Applicable NWP | **Yes (boot-time only)** | QCh programming happens on NWP; only runtime entry is N/A |
| 3 | PSS Environment | Partial | HSLE can validate boot-time register state; cannot validate runtime TCG entry |
| 4 | Silicon Only | No | Boot-time register checkout feasible on HSLE / VP |
| 5 | Test Content | DMR_M | Medium adaptation: rewrite intent, remove entry/residency, add NWP path/config |
| 6 | OS | sv-os | PythonSV register reads under SVOS |

### Verdict

**Open — rewrite required.** Boot-time QCh autonomous-idle enable checkout is valid on NWP. Runtime entry/residency expectations must be removed. Automation config file must be updated to `nwp.xml`.
