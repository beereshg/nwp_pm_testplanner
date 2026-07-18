# TC Description: RAPL Cold TDP Checkout

| Field | Value |
|-------|-------|
| **HSD ID** | [22022421962](https://hsdes.intel.com/appstore/article-one/#/22022421962) |
| **Title** | RAPL Cold TDP checkout |
| **Date** | 2026-07-18 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | Cold TDP — PL1 offset applied when die temperature below fused threshold |
| **Parent TCD** | [22022420813 -- Socket RAPL Fuse and BIOS Knobs](https://hsdes.intel.com/appstore/article-one/#/22022420813) |
| **Owner** | mps |
| **Status** | open / ready_for_content_review |
| **Priority** | 2-high |
| **Tags** | `pss` |
| **Val Environment** | virtual_platform |
| **Val Framework** | os-svos, python-sv |
| **Automation** | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| **NWP Disposition** | **Runnable_On_N-1** |
| **Cache version** | 3 |

---

## Test Case Intent

Validates the **Cold TDP** scenario defined in [TCD 22022420813 -- Socket RAPL Fuse and BIOS Knobs](https://hsdes.intel.com/appstore/article-one/#/22022420813) §5, row "Cold boot defaults": "PL_INFO / default fuse initialization; PL1 default = TDP, PL2 default = 1.2xTDP." Specifically, this TC verifies Cold TDP behavior: PCode applies a fused power limit offset (cold_long_power_limit_delta) to the effective PL1 budget when DTS temperature drops below the fused cold threshold (cold_long_power_limit_temp). The effective PL1 = base_PL1 + cold_delta when cold, and reverts to base_PL1 when warm. The key observable is pkg_computed_pl1_power_budget_0 increasing by the cold delta after DFX temperature injection.

### Pre-Conditions

| Item | Requirement |
|------|-------------|
| Platform | NWP virtual platform (Simics) — DFX temperature injection required |
| OS / Driver | SVOS with PythonSV environment |
| BIOS | Default BIOS PL1 settings (PL1 = fused TDP) |
| Feature state | Cold TDP fuses programmed for SKU; cold_long_power_limit_delta non-zero |
| Tool | runPmx.py accessible; DFX temperature injection capability (dfxTemperaturesEnabled) |
| Starting state | System booted; PrimeCode PH6 init complete; die temperature above cold threshold (normal operation) |
| Cold TDP fuse paths | sv.socket0.nio.fuses.punit.cold_long_power_limit_temp, sv.socket0.nio.fuses.punit.cold_long_power_limit_delta |
| PL1 budget register | sv.socket0.nio.pcudata.pkg_computed_pl1_power_budget_0 |

### Test Steps

| # | Action | Expected Result (PASS) | Failure Indication |
|---|--------|------------------------|-------------------|
| 1 | Read Cold TDP fuse values: cold_long_power_limit_temp (threshold) and cold_long_power_limit_delta (offset). Record both. | Both fuse values readable and non-zero for this SKU. Threshold is a valid temperature (e.g., 40-60C). Delta is a valid power offset (U11.3 encoding). | Fuse reads 0 (Cold TDP not fused for this SKU — test N/A). |
| 2 | Read current die temperature via DTS. Verify system is warm (above cold threshold). | Die temperature > cold_long_power_limit_temp. System in normal (warm) operating state. | Die temperature already below threshold — cannot establish warm baseline. |
| 3 | Read baseline pkg_computed_pl1_power_budget_0. This is the effective PL1 budget PrimeCode uses for the RAPL PID. Record as baseline_pl1. | baseline_pl1 = fused TDP (base PL1, no cold offset applied). | baseline_pl1 does not match expected fused TDP. |
| 4 | Inject DFX temperature below the cold threshold: use dfxTemperaturesEnabled to set die temperature to (cold_threshold - 10C). Wait for PrimeCode to detect cold condition (~1-2 PID cycles, ~2ms). | PrimeCode detects die temperature below cold threshold and applies cold delta. | DFX temperature injection fails or PrimeCode does not respond to injected temperature. |
| 5 | Read pkg_computed_pl1_power_budget_0 after cold injection. Compare to baseline_pl1. | effective_pl1 = baseline_pl1 + cold_long_power_limit_delta. PL1 budget increased by cold offset. | PL1 budget unchanged or delta does not match fused cold_long_power_limit_delta value. |
| 6 | Verify RAPL PID uses the elevated PL1: check socket_rapl_pid_output reflects higher power ceiling. | PID output frequency ceiling is higher than warm-state ceiling (more power budget available). | PID output unchanged despite higher PL1 budget. |
| 7 | Remove cold injection: restore DFX temperature to above threshold (e.g., threshold + 10C). Wait for PrimeCode to revert. | PrimeCode detects warm condition and removes cold delta. | Cold delta remains applied after temperature recovery. |
| 8 | Read pkg_computed_pl1_power_budget_0 after warm recovery. | effective_pl1 reverts to baseline_pl1 (cold offset removed). Clean transition. No MCA or hang. | PL1 budget still elevated or system instability during transition. |

### Pass / Fail Criteria

- **PASS**: Per TCD 22022420813 §5 — pkg_computed_pl1_power_budget_0 increases by exactly cold_long_power_limit_delta when die temperature drops below cold threshold. PL1 budget reverts to baseline when temperature recovers above threshold. Transitions are clean in both directions. RAPL PID reflects elevated budget during cold. No MCA or system instability.
- **FAIL**: PL1 budget does not change when temperature crosses cold threshold. Delta mismatch (applied delta != fused delta). PL1 does not revert when temperature recovers. System instability during temperature transitions.

### Health Checks

| Register / Log | Access | Pass/Fail Criteria |
|----------------|--------|--------------------|
| cold_long_power_limit_temp (fuse) | sv.socket0.nio.fuses.punit.cold_long_power_limit_temp | Non-zero, valid temperature value |
| cold_long_power_limit_delta (fuse) | sv.socket0.nio.fuses.punit.cold_long_power_limit_delta | Non-zero, valid power offset |
| pkg_computed_pl1_power_budget_0 | sv.socket0.nio.pcudata.pkg_computed_pl1_power_budget_0 | = base_PL1 + delta when cold; = base_PL1 when warm |
| socket_rapl_pid_output | sv.socket0.nio.pcudata.raplVars.socket_rapl_pid_output | Reflects elevated PL1 ceiling during cold |
| DTS temperature | DFX injection via dfxTemperaturesEnabled | Below threshold for cold; above threshold for warm |

### Post-Process

N/A

### Notes

- Cold TDP is a SKU-specific feature — if cold fuses are 0, test is N/A for that SKU.
- This TC requires DFX temperature injection (virtual_platform only); cannot run on production silicon without DFX overrides.
- Cold TDP was moved from TCD 22022420798 (Algorithm) to TCD 22022420813 (Fuse/BIOS) per Co-Design T2 audit — it is fuse scope, not PID scope.

### References

- [TCD 22022420813 -- Socket RAPL Fuse and BIOS Knobs](https://hsdes.intel.com/appstore/article-one/#/22022420813)
- [PrimeCode RAPL DMR -- Cold TDP](https://docs.intel.com/documents/primecode/primecode_one/firmware%20architecture/ip%20drivers%20and%20libraries/rapl_dmr.html)
- [Wave 3 Common HAS -- Socket RAPL](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Socket_RAPL/Socket_RAPL.html)

---

## Section A: NWP Delta

NWP carries forward DMR Cold TDP fuse mechanism. NIO replaces IMH as root die. Cold TDP fuses are SKU-dependent.

| Aspect | DMR | NWP |
|--------|-----|-----|
| Cold TDP fuse | sv.socket0.imh0.fuses.punit.cold_* | sv.socket0.nio.fuses.punit.cold_* |
| PL1 budget register | sv.socket0.imh0.pcudata.pkg_computed_pl1_power_budget_0 | sv.socket0.nio.pcudata.pkg_computed_pl1_power_budget_0 |
| Temperature aggregation | 2 IMH dies, 4 CBBs | 1 NIO die, 2 CBBs |

## Section F: Recommendations

Recommendation: ADOPT — imh0 -> nio register paths; DFX temperature injection for cold/warm transition testing. Priority: Medium — Cold TDP is a boundary condition; validates correct fuse-driven PL1 offset on NWP.
