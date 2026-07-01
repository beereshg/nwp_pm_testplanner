# TCD: SIMPL Policy Verification

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420763](https://hsdes.intel.com/appstore/article-one/#/22022420763) |
| **Title** | SIMPL Policy Verification |
| **Parent TPF** | [15019477948](https://hsdes.intel.com/appstore/article-one/#/15019477948) |
| **Feature** | SIMPL / DFC |
| **NWP Disposition** | Runnable_On_N-1 |
| **KB last updated** | 2026-07-01 |

## Section 1: Architecture / Micro-architecture and Functionality

SIMPL (Simultaneous Power Limiting) selects one of 4 policies (0-3) based on IO/Mem fabric BW demand. Policy 0 = core-heavy/light-IO (max freq, IO=0xe). Policy 3 = max IO+Mem (most restrictive freq). NWP: single IMH (imh0). ZBB per NWP PM MAS para 3; FV team Runnable_On_N-1 pending confirmation.

### TC Coverage: 22022421906 Policy 0, 22022421909 Policy 1, 22022421910 Policy 2, 22022421912 Policy 3, 22022421914 Asymmetric

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Purpose |
|-----------|----------------|---------|
| current_policy | sv.socket0.imh0.pcudata.patch_persistent.current_policy | Active SIMPL policy (0-3) |
| target_policy | sv.socket0.imh0.pcudata.patch_persistent.target_policy | Policy during transition |
| simpl_max_freq | sv.socket0.imh0.pcudata.simpl_max_freq_{{domain}}_{{policy}} | Per-domain per-policy freq ceiling |
| perf_limit_reasons | sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.perf_limit_reasons | ICCMAX bit when SIMPL throttling |
| Policy fuses | sv.socket0.imh0.fuses.punit.pcode_simpl_policy_N_imh_cfcio_max_freq | Fuse values propagated to pcudata |

---

## Section 3: Reset, Power, and Clocking

- Cold reset: current_policy = target_policy = 0 (SIMPL Handshake terminates)
- PH6: PrimeCode reads SIMPL fuses and initializes simpl_max_freq registers

---

## Section 8: References

- [DMR SIMPL HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_SIMPL.html) — Policy definitions; BW thresholds; fuse structure; reset handshake; telemetry
- [DMR Fabric DVFS Data](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/assets/DMR_Fabric_DVFS.xlsx) — BW to policy table; per-policy freq values; fuse values
- [DMR PLR HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_PLR.html) — ICCMAX PLR bit; SIMPL/DFC perf-limit reason reporting
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — NWP SIMPL ZBB status; single IMH; new voltage rails

