# TCD: Socket RAPL Cross-products
<!-- sibling: TCD_22022420813_socket_rapl_fuse_bios_knobs.md -->

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420806](https://hsdes.intel.com/appstore/article-one/#/22022420806) |
| **Title** | Socket RAPL Cross-products |
| **Status** | open |
| **Owner** | mps |
| **Parent TP** | [15019477653 — NWP PM Socket RAPL](https://hsdes.intel.com/appstore/article-one/#/15019477653) |
| **Sibling TCD** | [22022420798 — Socket RAPL Algorithm & Functionality Verification](https://hsdes.intel.com/appstore/article-one/#/22022420798) |
| **KB last updated** | 2026-06-24 |
| **Feature** | Power / RAPL — Socket RAPL × cross-product interactions |

## Section 1: Architecture / Micro-architecture and Functionality

**Socket RAPL Cross-products** verifies the interaction of Socket RAPL with other concurrently active platform features, limiters, and state transitions. The purpose is to confirm that Socket RAPL control remains correct when another feature is simultaneously active or modifies effective performance behavior.

Socket RAPL enforces power through **RAPL_PERF_LIMIT** (PrimeCode NN-PID, distributed over HPM 0x14). Cross-product validation checks whether this limit is: correctly applied, correctly combined with other active limits, correctly re-established after state transitions, and not left stale after reset or feature transitions.

Base Socket RAPL algorithm validation is covered by **[TCD 22022420798](https://hsdes.intel.com/appstore/article-one/#/22022420798)**. This TCD covers cross-product interaction only.

**NWP product deltas**: 2 CBB topology · single NIO root path · TPMI runtime interface · legacy RAPL MSRs deprecated

### NWP Scope Constraints

- **PkgC is not supported on NWP** → RAPL × PkgC: **ZBB / not applicable**
- **RACL × Psys is not applicable on NWP** → single-NIO topology: **ZBB / not applicable**
- **UFS is ZBB on NWP** → RAPL × UFS: **ZBB / not applicable**
- **RAPL × SST** limited to supported **NWP SST / PCT path** only (reduced scope)

### Cross-product Architecture Map

| Cross-product | Interaction Mechanism | NWP Applicability |
|--------------|----------------------|------------------|
| RAPL × PkgC | Package C-state interaction — PID suspend/resume | **ZBB / not applicable** |
| RAPL × Security (Energy Fuzzing) | Energy telemetry fuzzing while RAPL remains active | **In scope** |
| RAPL × Core + IO Traffic | Mixed compute and IO load under active Socket RAPL limit | **In scope** |
| RAPL × RACL × Psys | Multi-domain power interaction (IMH-S leaf + platform) | **ZBB / not applicable** |
| RAPL × Reset | PID re-initialization and cleanup across warm reset | **In scope** |
| RAPL × UFS | Interaction with Ultra-Fast Standby | **ZBB / not applicable** |
| RAPL × Pmax | Coexistence with independent power / electrical limiter | **In scope** |
| RAPL × Prochot | Interaction with thermal / external PROCHOT# throttle | **In scope** |
| RAPL × SST | SST-TF / PCT frequency limit coexistence | **Keep, reduced scope** |

### TC Coverage Map

| TC | Cross-product | Scope | NWP Recommendation |
|----|--------------|-------|--------------------|
| [22022421992 — RAPL X Pkgc](https://hsdes.intel.com/appstore/article-one/#/22022421992) | RAPL × PkgC | Package C-state interaction | **Drop / ZBB** |
| [22022421995 — RAPL X Security](https://hsdes.intel.com/appstore/article-one/#/22022421995) | RAPL × Energy Fuzzing | Energy telemetry fuzz with active RAPL | **Keep** |
| [22022421998 — Socket RAPL x Core+IO Traffic](https://hsdes.intel.com/appstore/article-one/#/22022421998) | RAPL × Core + IO | Simultaneous core and IO activity under RAPL | **Keep** |
| [22022422001 — Socket RAPL x RACL x Psys](https://hsdes.intel.com/appstore/article-one/#/22022422001) | RAPL × RACL × Psys | Multi-domain power interaction | **Drop / ZBB** |
| [22022422003 — Socket RAPL x Reset](https://hsdes.intel.com/appstore/article-one/#/22022422003) | RAPL × Reset | Warm reset with active RAPL | **Keep** |
| [22022422008 — Socket RAPL x UFS](https://hsdes.intel.com/appstore/article-one/#/22022422008) | RAPL × UFS | UFS interaction | **Drop / ZBB** |
| [22022422010 — Socket RAPL x Pmax](https://hsdes.intel.com/appstore/article-one/#/22022422010) | RAPL × Pmax | Concurrent limiter coexistence | **Keep** |
| [22022422013 — Socket RAPL x Prochot](https://hsdes.intel.com/appstore/article-one/#/22022422013) | RAPL × Prochot | Thermal / external throttle interaction | **Keep** |
| [22022422015 — Socket RAPL x SST](https://hsdes.intel.com/appstore/article-one/#/22022422015) | RAPL × SST-TF/PCT | SST frequency limit coexistence | **Keep (reduced scope)** |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Cross-product Role |
|-----------|----------------|-------------------|
| TPMI | `PL1_CONTROL`, `PL2_CONTROL` | RAPL limits active during all cross-products |
| TPMI | `ENERGY_STATUS` | Fuzzed by MSR 0xBC in security TC; held during PkgC |
| TPMI | `PERF_STATUS` | Accumulates throttle time across all cross-products |
| MSR 0xBC | `IA32_MISC_PACKAGE_CTLS.bit0` | Energy filtering toggle (RAPL × Security TC) |
| MSR 0x19C | `IA32_THERM_STATUS.PROCHOT_STATUS` | PROCHOT# detection (RAPL × Prochot TC) |
| HPM 0x14 | `RAPL_PERF_LIMIT` | Distributed to all CBBs; must survive cross-product transitions |
| SST TPMI | `SST_CP_CONTROL.sst_cp_priority_type` | Ordered throttling mode for RAPL × SST |
| PkgC handshake | HPM / Q-channel | RAPL PID suspend/resume on PkgC entry/exit |

---

## Section 3: Reset, Power, and Clocking

- RAPL × Reset TC verifies PID re-initialization after warm reset (PH6)
- ENERGY_STATUS is **not reset** on warm reset — this is an explicit validation point for the Reset TC
- PERF_STATUS throttle counter: reset on cold reset; warm-reset retention is validated in Reset TC
- PkgC entry: RAPL PID is suspended; HPM 0x14 messages stop; CBBs hold last limit
- PkgC exit: RAPL PID resumes from last state; new limits distributed immediately

---

## Section 4: Programming Model

Cross-product test setup typically requires:
1. Configure the cross-product feature (PkgC, SST, PROCHOT, etc.)
2. Program RAPL PL1 to a value that will cause measurable throttling under workload
3. Apply load to trigger both features simultaneously
4. Observe: PERF_STATUS increment, ENERGY_STATUS accumulation, effective frequency

**UFS rejection**: TC 22022422008 is rejected because UFS (Ultra-Fast Standby) is ZBB on NWP.

---

## Section 5: Operational Behavior

**In scope on NWP** (paired feature applicable):

- **Security / Energy Fuzzing**: telemetry filtering does not prevent correct RAPL enforcement
- **Core + IO Traffic**: Socket RAPL remains correctly enforced under mixed activity
- **Reset**: Socket RAPL correctly reinitialized after warm reset; no stale limit persists
- **Pmax**: effective frequency ceiling reflects the more restrictive active limiter
- **Prochot**: thermal / external throttling coexists with Socket RAPL without invalid state
- **SST (reduced scope)**: RAPL interaction validated only for supported NWP SST / PCT path

**Out of scope / not applicable on NWP**:

- PkgC interaction (PkgC ZBB'd)
- RACL × Psys interaction (single-NIO topology, not applicable)
- UFS interaction (UFS ZBB'd)

---

## Section 6: Corner Cases & Error Handling

| Scenario | Expected Behavior |
|----------|------------------|
| Energy fuzzing enabled while RAPL active | Telemetry may be modified; enforcement remains correct |
| PROCHOT asserted while RAPL active | Combined throttling occurs without invalid state |
| Reset during active RAPL | RAPL reinitializes cleanly; no stale limit persists |
| Pmax and RAPL simultaneously at limit | More restrictive ceiling wins; no incorrect override |
| Unsupported SST mode combined with RAPL | Out of scope on NWP |
| Attempt to execute PkgC cross-product on NWP | Not applicable (PkgC ZBB'd) |
| Attempt to execute RACL × Psys cross-product on NWP | Not applicable (single-NIO topology) |
| Attempt to execute UFS cross-product on NWP | Not applicable (UFS ZBB'd) |

---

## Section 7: Security / Safety / Policy

- RAPL × Security TC validates energy fuzzing (MSR 0xBC.bit0=1) does not interfere with RAPL enforcement
- BIOS may lock RAPL registers; locks persist across cross-product state changes
- PROCHOT# is an external platform signal; RAPL does not override PROCHOT throttle

---

## Section 8: References

- [Socket RAPL KB — socket_rapl.md](../../pm_features/power_rapl/socket_rapl.md) — NN-PID architecture, HPM topology
- [TCD 22022420798 — Socket RAPL Algorithm & Functionality](https://hsdes.intel.com/appstore/article-one/#/22022420798) — base algorithm coverage
- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) — RAPL PH6 init, Prochot, reset interaction
- [Intel RAPL HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/RAPL/RAPL.html) — TPMI register definitions, cross-product behavior
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html) — SST × RAPL ordered throttling (NWP SST/PCT path only)
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html)
