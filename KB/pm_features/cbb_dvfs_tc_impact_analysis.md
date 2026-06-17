# NWP CBB DVFS — TC Impact Analysis Report
**Test Plan:** [16030763243 — NWP PM] Fabric DVFS (UFS)](https://hsdes.intel.com/appstore/article-one/#/16030763243)  
**Analysis Date:** 2026-06-10  
**Author:** bg3  
**Context applied:** Socket RAPL Micro-Architecture (NWP) — PL1/PL2/Fast RAPL/PLR register set

---

## 1. Executive Summary

The **[NWP PM] Fabric DVFS (UFS)** test plan covers Uncore Frequency Scaling (UFS) across three fabric domains: CBB (compute fabric), IMH Memory fabric, and IOH IO fabric. Due to NWP's single-die NIO architecture (one NIO die, 2 CBBs, single VCCIN), a large fraction of the inherited DMR test coverage is **Zero Bug Baseline (ZBB)**. Only **7 PSS TCs remain active** across 2 TCDs.

The Socket RAPL context is **directly relevant**: RAPL PID loop (PL1/PL2) is the primary power arbiter that governs whether a requested fabric frequency can be honored. When RAPL is in a constraining state, it can:
- Override PEGA-requested or TPMI-forced fabric GV ratios
- Set PLR bits that can be confused with UFS boundary-enforcement throttling
- Reduce `pkg_computed_pl1_power_budget_0`, affecting the power headroom for fabric frequency transitions

Additionally, a **critical NWP delta error** is found in all 7 active TCs: the PythonSV register paths reference `sv.socket0.imh0.*` — which does not exist on NWP. The correct path root for NWP punit access is `sv.socket0.nio.*`.

---

## 2. TP / TCD Structure and ZBB Disposition

### TP: 16030763243 — [NWP PM] Fabric DVFS (UFS)

```
TP  16030763243  [NWP PM] Fabric DVFS (UFS)
├── TPF  16030763253  [CBB DVFS]
│   ├── TCD  22022420830  Fabric DVFS RAPL/RACL Limits and ELC Mode    ← REJECTED (ZBB)
│   ├── TCD  22022420838  Fabric DVFS cross products                    ← REJECTED (3 active PSS TCs)
│   └── TCD  22022420853  Solar DVFS                                    ← REJECTED (ZBB)
├── TPF  16030763254  [IMH DVFS]
│   └── TCD  22022420849  Memory Fabric DVFS                           ← REJECTED (ZBB)
└── TPF  16030763255  [IOH DVFS]
    └── TCD  22022420842  IO Fabric DVFS                               ← REJECTED (4 active PSS TCs)
```

### ZBB Disposition Table

| TCD | Title | ZBB Reason | NWP Architectural Delta |
|-----|-------|-----------|------------------------|
| 22022420830 | RAPL/RACL Limits & ELC Mode | RACL requires dual IMH dies; NWP has single NIO die (single VCCIN) | No RACL; no ELC mode |
| 22022420853 | Solar DVFS | Non-Solar DVFS architecture on NWP | No Solar DVFS |
| 22022420849 | Memory Fabric DVFS | NWP memory mesh fixed at 2 GHz (HSD 14024876702) | IMH mesh not dynamically scalable |
| 22022420838 | Fabric DVFS cross products | Partially rejected — 6 sub-TCs ZBB (ADR, IP Disable, etc.) | 3 TPMI PSS TCs survive |
| 22022420842 | IO Fabric DVFS | Partially rejected — 9 sub-TCs ZBB | 4 PSS TCs survive |

**Active TC count: 7 PSS TCs (0 FV TCs)**

---

## 3. Active TCs — Socket RAPL Impact Analysis

### 3.1 TCD 22022420838 — Fabric DVFS cross products (CBB)

#### TC 16030715615 — [PSS] TPMI register verification - CBB

| Attribute | Detail |
|-----------|--------|
| HSD | [16030715615](https://hsdes.intel.com/appstore/article-one/#/16030715615) |
| Status | open |
| Owner | bg3 |
| Purpose | Verify default UFS TPMI register values on CBB die |

**Socket RAPL Impact:**
- **LOW direct impact** — default-value verification is a static check at boot before workload
- **Pre-condition gap:** No RAPL state pre-condition is specified. If RAPL PL1 is constraining at time of register read, `UFS_STATUS[CURRENT_RATIO]` may already be below the fused P0 value due to power throttling — causing a false fail
- **Recommended addition:** Assert `pkg_power_consumed < PL1×0.9` before reading `UFS_STATUS[CURRENT_RATIO]` to confirm RAPL is not actively throttling during baseline capture
- **Critical NWP path error:** TC references `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status` — **this path does not exist on NWP**. Correct path: `sv.socket0.nio.punit.ptpcfsms.ptpcfsms.ufs_status` (or CBB path: `sv.socket0.cbb0.base.tpmi.ufs_status`)

**PLR Interaction:**
```
PLR bit[10] = PKG_PL1_IB  → set when RAPL PL1 in-band throttling active
PLR bit[22] = RACL         → ZBB on NWP, should never be set
```
If PLR[10] is asserted during this TC, the current ratio may not match fused P0 — TC must check PLR state as part of pass/fail.

---

#### TC 16030715617 — [PSS] TPMI register verification - IMH IO

| Attribute | Detail |
|-----------|--------|
| HSD | [16030715617](https://hsdes.intel.com/appstore/article-one/#/16030715617) |
| Status | open |
| Owner | bg3 |
| Purpose | Verify default UFS TPMI register values on IMH IO domain |

**Socket RAPL Impact:**
- **Same as 16030715615** — static register check; RAPL quiescence pre-condition missing
- **NWP ZBB scope note:** IMH IO UFS on NWP — the description says "locked at static frequency" for IMH die fabrics. If IO mesh is statically fixed, the `UFS_STATUS[CURRENT_RATIO]` should always equal the fused IO min ratio — RAPL cannot change this. Low RAPL impact for IO register static check.
- **Critical NWP path error:** Same `sv.socket0.imh0.*` path issue applies — IMH does not exist as a separate die on NWP. All punit access must go through `sv.socket0.nio.*`

**Negative check gap:** TC validates `ufs_control_fabric_1` and `ufs_status_fabric_1` on CBB are unused (single-die NWP has no fabric_1). This check is NWP-correct — RAPL has no impact here.

---

#### TC 16030715619 — [PSS] TPMI register verification - IMH MEM

| Attribute | Detail |
|-----------|--------|
| HSD | [16030715619](https://hsdes.intel.com/appstore/article-one/#/16030715619) |
| Status | open |
| Owner | bg3 |
| Purpose | Verify default UFS TPMI register values on IMH MEM domain |

**Socket RAPL Impact:**
- **LOWEST impact** — Memory mesh is ZBB (fixed at 2 GHz per HSD 14024876702). RAPL has no path to alter memory fabric frequency on NWP.
- **Action:** TC description should explicitly note that Memory Fabric DVFS is ZBB and the MEM UFS registers should show locked/fixed values. The pass criterion for `UFS_STATUS[CURRENT_RATIO]` should be hardcoded to the fixed 2 GHz ratio, independent of any RAPL state.
- **Critical NWP path error:** Same `sv.socket0.imh0.*` path issue — must use `sv.socket0.nio.*`

---

### 3.2 TCD 22022420842 — IO Fabric DVFS

#### TC 16030715600 — [PSS] BIOS Configurations of DVFS settings

| Attribute | Detail |
|-----------|--------|
| HSD | [16030715600](https://hsdes.intel.com/appstore/article-one/#/16030715600) |
| Status | open |
| Owner | bg3 |
| Purpose | Verify BIOS configuration of DVFS TPMI settings and propagation into TPMI registers |

**Socket RAPL Impact: HIGH**

This TC directly intersects with Socket RAPL because DVFS throttle modes are tightly coupled to the RAPL power-limiting policy:

| BIOS Knob | TPMI Register | RAPL Intersection |
|-----------|---------------|-------------------|
| Uncore Freq Control (CBB) Mode | `UFS_CONTROL.UFS_THROTTLE_MODE[1:0]` | Mode 0 = Power Limited Ordered Throttling; Mode 1 = Power Limited Proportional Throttling — both modes respond to RAPL PL1 budget |
| Uncore Freq Ratio (CBB) | `UFS_CONTROL.MAX_RATIO[14:8]`, `MIN_RATIO[21:15]` | If RAPL PL1 constrains power budget, Pcode may enforce a ratio below `MIN_RATIO` via `pkg_computed_pl1_power_budget_0` |
| Uncore Freq Control (IMH Memory) | IMH PCU UFS_CONTROL | ZBB on NWP — skip |

**Recommendations:**
1. Add explicit RAPL state verification step: after programming each BIOS knob, read `sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control` and confirm PL1 > TDP (so RAPL is not throttling during BIOS knob propagation checks)
2. Add PLR register read at end of each knob test:
   ```python
   plr = sv.socket0.nio.punit.ptpcfsms.ptpcfsms.perf_limit_reasons.read()
   assert not (plr >> 10 & 1), "Unexpected PKG_PL1_IB throttling during DVFS BIOS config test"
   ```
3. Verify `UFS_CONTROL.MAX_RATIO` and `MIN_RATIO` independently of RAPL (disable RAPL or set PL1 >> TDP during this check)

**Key NWP delta referenced in TC description:** "Available BIOS configurations may change based on how NIO will disable Memory and IO UFS/DVFS (fuse disable, customer can disable with TPMI/BIOS, Primecode can disable...)" — this confirms NIO/Primecode has a role in DVFS disable decisions that intersects with RAPL budget calculations.

---

#### TC 16030715604 — [PSS] PEGA-driven FabricGV

| Attribute | Detail |
|-----------|--------|
| HSD | [16030715604](https://hsdes.intel.com/appstore/article-one/#/16030715604) |
| Status | open |
| Owner | bg3 |
| Purpose | Inject MeshGV through PEGA Mailbox; verify core frequency changes |

**Socket RAPL Impact: HIGH**

PEGA-requested fabric GV ratios flow through the power policy arbiter in Primecode. The RAPL PID loop output (via `pkg_computed_pl1_power_budget_0`) is an upstream constraint on fabric frequency decisions:

- If **PL1 is tight (< TDP)**: Primecode may not honor a PEGA-requested higher fabric ratio, because granting it would exceed the power budget. The expected frequency change may not occur → false fail.
- If **PL1 is unconstrained (≥ TDP+headroom)**: PEGA injection should deterministically produce the expected ratio change.

**Recommendations:**
1. **Pre-condition must set RAPL state:** Before PEGA injection, set PL1 ≥ TDP × 1.5 (or unlock power limit) to remove RAPL as a confounding throttle source
2. **Post-injection check must include PLR:**
   ```python
   # After PEGA MeshGV injection
   plr = sv.socket0.nio.punit.ptpcfsms.ptpcfsms.perf_limit_reasons.read()
   pwr = sv.socket0.nio.pcudata.pkgRAPLDomain.pkg_power_consumed.read()
   pl1_budget = sv.socket0.nio.pcudata.pkg_computed_pl1_power_budget_0.read()
   # PLR[10] (PKG_PL1_IB) should be clear if RAPL is not throttling
   assert not (plr >> 10 & 1), f"RAPL throttle active during PEGA test (power={pwr:.1f}W, budget={pl1_budget:.1f}W)"
   ```
3. **Fast RAPL (PEM):** SVID IMON is sub-1ms and can transiently reduce power before a PEGA frequency change completes. Add 100ms stabilization wait before sampling final ratio.

---

#### TC 16030715607 — [PSS] TPMI-driven FabricGV

| Attribute | Detail |
|-----------|--------|
| HSD | [16030715607](https://hsdes.intel.com/appstore/article-one/#/16030715607) |
| Status | open |
| Owner | bg3 |
| Purpose | Force fabric ratio by setting `UFS_CONTROL[MIN_RATIO] = UFS_CONTROL[MAX_RATIO]`; verify `UFS_STATUS[CURRENT_RATIO]` |

**Socket RAPL Impact: MEDIUM-HIGH**

This TC forces a static ratio by pinning MIN=MAX in `UFS_CONTROL`. Primecode must honor this, but RAPL remains active:

- If the pinned ratio corresponds to high power consumption and PL1 is constrained, Primecode may **not** achieve the requested ratio. `UFS_STATUS[CURRENT_RATIO]` would show a lower value than programmed.
- The TC currently checks only `UFS_STATUS[CURRENT_RATIO] == programmed ratio` — no RAPL state check.

**Recommended test flow enhancement:**
```python
# Step 1: Set PL1 >> TDP to remove RAPL as confounder
pl1_reg = sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control
# read current, then set high
# ...

# Step 2: Program UFS_CONTROL MIN=MAX
target_ratio = fused_P0_ratio
sv.socket0.cbb0.base.tpmi.ufs_control.min_ratio.write(target_ratio)
sv.socket0.cbb0.base.tpmi.ufs_control.max_ratio.write(target_ratio)

# Step 3: Poll for current ratio to match
import time
for _ in range(20):
    cur = sv.socket0.cbb0.base.tpmi.ufs_status.current_ratio.read()
    if cur == target_ratio:
        break
    time.sleep(0.05)

# Step 4: Verify RAPL did not intervene
plr = sv.socket0.nio.punit.ptpcfsms.ptpcfsms.perf_limit_reasons.read()
assert not (plr >> 10 & 1), "PKG_PL1_IB set — RAPL prevented ratio from being achieved"
assert cur == target_ratio, f"Ratio mismatch: got {cur}, expected {target_ratio}"
```

**NWP delta:** TC explicitly notes "IMH die fabrics will be locked at a static frequency" — this test only applies to CBB die. The test should NOT attempt to force-pin IMH IO/MEM ratios.

---

#### TC 16030715609 — [PSS] Out of Boundary Frequency Check

| Attribute | Detail |
|-----------|--------|
| HSD | [16030715609](https://hsdes.intel.com/appstore/article-one/#/16030715609) |
| Status | open |
| Owner | bg3 |
| Purpose | Verify FW enforces fused limits when out-of-boundary ratio is programmed into `UFS_CONTROL` |

**Socket RAPL Impact: MEDIUM**

This TC programs a ratio outside fused bounds (> P0 or < PM) and verifies Primecode clips it to the fused limit. The concern is distinguishing **two throttle mechanisms**:

| Throttle Source | PLR Bit | Mechanism |
|-----------------|---------|-----------|
| UFS boundary enforcement (fused clamp) | None documented — firmware enforces silently | `UFS_STATUS[CURRENT_RATIO]` = clipped value |
| RAPL PL1 throttling | PLR bit[10] = PKG_PL1_IB | Power-budget reduction reduces achievable ratio |

If RAPL is active, it may independently limit the ratio to the same clipped value — but for the **wrong reason**. The TC must differentiate:

**Recommended disambiguation:**
```python
# After programming out-of-boundary ratio:
time.sleep(0.2)

cur_ratio = sv.socket0.cbb0.base.tpmi.ufs_status.current_ratio.read()
plr       = sv.socket0.nio.punit.ptpcfsms.ptpcfsms.perf_limit_reasons.read()
pwr       = sv.socket0.nio.pcudata.pkgRAPLDomain.pkg_power_consumed.read()
pl1_ctrl  = sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control.read()
# Decode PL1 value (bits[14:0] × power_unit)
...

# UFS clamp check
assert cur_ratio == expected_clipped_ratio, f"Boundary enforcement failed: got {cur_ratio}"
# Verify RAPL was NOT the cause of limiting
assert not (plr >> 10 & 1), \
    f"PKG_PL1_IB set — RAPL may be independently limiting ratio (pwr={pwr:.1f}W)"
```

---

## 4. Critical Findings

### Finding 1 — Wrong PythonSV Namednodes Paths in All 7 Active TCs (SEVERITY: HIGH)

All 7 active TCs specify IMH punit paths that do not exist on NWP:

| Incorrect Path (DMR) | Correct Path (NWP) |
|---------------------|-------------------|
| `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status` | `sv.socket0.nio.punit.ptpcfsms.ptpcfsms.ufs_status` |
| `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.ufs_status_fabric_1` | `sv.socket0.nio.punit.ptpcfsms.ptpcfsms.ufs_status_fabric_1` |
| `sv.socket0.imh0.punit.ptpcfsms.ptpcfsms.*` | `sv.socket0.nio.punit.ptpcfsms.ptpcfsms.*` |

NWP has a single NIO die (not imh0/imh1). All punit registers are under `sv.socket0.nio.*`.  
CBB-local registers remain under `sv.socket0.cbb0.base.tpmi.*` (correct as-is).

**Action required:** Update all 7 TC descriptions to replace `sv.socket0.imh0.` with `sv.socket0.nio.` in the Configuration/PythonSV nodes section.

---

### Finding 2 — Missing RAPL State Pre-Condition in PEGA and TPMI GV TCs (SEVERITY: MEDIUM)

TCs 16030715604 (PEGA GV) and 16030715607 (TPMI GV) do not specify RAPL state as a pre-condition. If RAPL PL1 is constraining, the frequency change may be partially or fully blocked by the power arbiter, producing false fails. Pre-conditions must include:
```
Pre-condition: Socket RAPL PL1 ≥ TDP × 1.5 (or RAPL disabled)
               Verify pkg_power_consumed < PL1 at test start
```

---

### Finding 3 — PLR Bit Monitoring Missing from All Active TCs (SEVERITY: MEDIUM)

No active TC reads `perf_limit_reasons` to validate which component is causing any observed throttle. Without PLR differentiation:
- RAPL-driven throttle is indistinguishable from UFS/DVFS-driven throttle
- False passes possible: RAPL prevents the expected ratio → TC passes on wrong grounds
- False fails possible: RAPL unexpectedly throttles → TC fails but not a DVFS bug

---

### Finding 4 — No FV TCs Exist Under This TP (SEVERITY: LOW — by design for PSS TP)

All 7 active TCs are PSS. However, FV coverage gaps exist for:
- RAPL × DVFS cross-product (what happens when RAPL PL1 constrains during fabric GV)
- ELC Mode interaction (ZBB — not applicable, but should be documented explicitly)
- Reset behavior: DVFS state restore after warm/cold reset under RAPL constraint

---

### Finding 5 — RACL ZBB Not Explicitly Guarded in Active TCs (SEVERITY: LOW)

PLR bit[22] = RACL. Since RACL is ZBB on NWP, this bit should never assert. Active TCs should add:
```python
plr = sv.socket0.nio.punit.ptpcfsms.ptpcfsms.perf_limit_reasons.read()
assert not (plr >> 22 & 1), "RACL PLR bit asserted on NWP — unexpected (ZBB feature)"
```
This is a cheap guard that catches if RACL is accidentally enabled by a BIOS knob misconfiguration.

---

## 5. Gap Analysis Summary

| Gap | Impacted TCs | Recommended Action |
|-----|-------------|-------------------|
| Wrong NWP namednodes paths (`imh0` → `nio`) | All 7 active TCs | Update TC descriptions — medium effort |
| No RAPL state pre-condition | 16030715604, 16030715607 | Add pre-condition: PL1 ≥ 1.5×TDP |
| No PLR monitoring | All 7 active TCs | Add PLR read + assertion to pass/fail criteria |
| No cross-product TC: DVFS × Socket RAPL throttle | None (gap) | New TC needed: verify fabric GV under RAPL PL1 constraint |
| RACL ZBB not explicitly guarded | All active TCs | Add PLR[22] == 0 assertion |
| Memory mesh ZBB not explicitly documented in TC 16030715619 | TC 16030715619 | Add note + hardcode expected ratio = 2 GHz |
| No power consumption check during ratio verification | 16030715604, 16030715607 | Add pkg_power_consumed monitoring |

---

## 6. Recommended New TC Concept

### TC-NEW-01: Socket RAPL × CBB Fabric DVFS Cross-Product

**TCD:** 22022420838 (Fabric DVFS cross products)  
**Priority:** 2-high  
**Description:** Verify behavior of CBB fabric DVFS when Socket RAPL PL1 is set below current power consumption. Confirm that:
1. When PL1 < current power, RAPL throttles via PKG_PL1_IB (PLR bit[10])
2. The fabric GV algorithm responds by reducing CBB ratio toward min_ratio
3. When PL1 is restored to ≥ TDP, fabric ratio recovers to pre-throttle value within 5×tau convergence time
4. RACL (PLR bit[22]) never asserts (ZBB guard)

**Key registers:**
```python
# Monitor sequence
pl1_ctrl = sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control
plr      = sv.socket0.nio.punit.ptpcfsms.ptpcfsms.perf_limit_reasons
pwr      = sv.socket0.nio.pcudata.pkgRAPLDomain.pkg_power_consumed
budget   = sv.socket0.nio.pcudata.pkg_computed_pl1_power_budget_0
cbb_ratio= sv.socket0.cbb0.base.tpmi.ufs_status.current_ratio
```

---

## 7. Register Quick Reference (Socket RAPL × DVFS)

| Register | NWP Namednodes Path | Relevance to DVFS |
|----------|--------------------|--------------------|
| `socket_rapl_pl1_control` | `sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_pl1_control` | PL1 limit — primary power constraint on fabric GV |
| `socket_rapl_pl2_control` | `sv.socket0.nio.punit.ptpcfsms.ptpcfsms.socket_rapl_pl2_control` | PL2 — short-term peak; fabric may reduce ratio under PL2 burst |
| `perf_limit_reasons` | `sv.socket0.nio.punit.ptpcfsms.ptpcfsms.perf_limit_reasons` | PLR[10]=RAPL throttle, PLR[22]=RACL (should be 0) |
| `pkg_power_consumed` | `sv.socket0.nio.pcudata.pkgRAPLDomain.pkg_power_consumed` | Real-time power — pre-condition check |
| `pkg_computed_pl1_power_budget_0` | `sv.socket0.nio.pcudata.pkg_computed_pl1_power_budget_0` | Effective budget after Pcode RAPL calculation |
| `package_power_sku` | `sv.socket0.nio.punit.ptpcioregs.ptpcioregs.package_power_sku` | TDP / min / max power fuse values |
| `ufs_status` (CBB) | `sv.socket0.cbb0.base.tpmi.ufs_status` | Current fabric ratio (CBB DVFS) |
| `ufs_status` (NIO punit) | `sv.socket0.nio.punit.ptpcfsms.ptpcfsms.ufs_status` | ⚠ Verify this path exists on NWP silicon |

---

## 8. Appendix — PLR Bit Map (Relevant Bits)

| Bit | Name | Relevance to CBB DVFS |
|-----|------|----------------------|
| 9 | FAST_RAPL | Fast RAPL (PEM/SVID IMON) throttling active |
| 10 | PKG_PL1_IB | RAPL PL1 in-band throttle — most common confound |
| 11 | PKG_PL1_CSR | RAPL PL1 via legacy CSR register |
| 12 | PKG_PL1_OOB | RAPL PL1 via out-of-band (PECI/Redfish) |
| 13 | PKG_PL2_IB | Short-term PL2 throttle |
| 22 | RACL | **ZBB on NWP — should always be 0** |
| 25 | PROCHOT | Prochot thermal throttle — can co-occur with fabric frequency reduction |

---

*Report generated from live HSD data fetched 2026-06-10. TP 16030763243 has 0 FV TCs; 7 PSS TCs active across 2 TCDs.*
