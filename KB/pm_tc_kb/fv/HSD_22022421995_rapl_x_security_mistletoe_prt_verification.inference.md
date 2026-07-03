# Deep Analysis: RAPL x Security (Mistletoe PRT) - Verification of Energy Fuzzing

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421995 |
| **Title** | RAPL X Security (Mistletoe PRT) - Verification of Energy Fuzzing |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | Energy reporting under SGX (Mistletoe PRT / energy fuzzing countermeasure) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **RAPL Energy Reporting while SGX feature is enabled** (Mistletoe PRT — energy side-channel mitigation):
- SGX enables "energy fuzzing" to prevent side-channel attacks via energy MSR timing
- Verify energy reporting remains correct (not completely broken) with SGX and energy fuzzing active
- Intent: Verification Strategy — confirm energy with security enabled behaves per spec

Tags: `plc.feature.p2`, `pm.xproducts.security`, `PMSS_NWP_READINESS_CHECK`

**NWP SGX Note**: If SGX is not enabled on NWP, this test is not fully applicable. The PMSS_NWP_READINESS_CHECK tag indicates NWP candidacy; if SGX is available, test energy fuzzing behavior. If not, mark as platform-dependent.

---

## Section B: NWP-Specific Test Procedure

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Configure BIOS for SGX enabled (if NWP supports SGX) | `EnableSgx 0x1`, `EccModeSel 0x1`, etc. |
| 2 | Verify SGX active | `cpuid 0x12` → EAX bit 0 (SGX) |
| 3 | Run cpu_rapl PMx with security profile | `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3` |
| 4 | Run automated RAPL content with SGX enabled | Energy status MSR 0x611 under SGX workload |
| 5 | Verify energy reporting functional | Energy increments; no freeze |
| 6 | Verify Mistletoe PRT energy fuzzing active | Random noise on energy readings expected per spec |

### PMx Command
```
python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3
```

### Energy Fuzzing Behavior (expected with Mistletoe PRT)
- Small random offsets added to energy MSR per SGX security specification
- Energy reporting still increases monotonically overall
- Power limit enforcement still functional despite fuzzing

### Pass Criteria
- Energy status MSR (0x611) increments (monotonically on average) with SGX enabled
- RAPL power limits still enforced with SGX active
- Energy fuzzing noise within expected bounds per security spec
- No catastrophic RAPL failure under SGX configuration

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; verify SGX availability on NWP; if not available, mark platform-dependent**

1. `python runPmx.py -x nwp.xml -p cpu_rapl -tM 6 -M 3`
2. Enable SGX if available on NWP (check BIOS and CPUID 0x12)
3. Verify energy reporting functional with Mistletoe PRT energy fuzzing active
4. If NWP doesn't support SGX: document as platform-dependent; test energy reporting only

**Priority**: Low — security × RAPL interaction; requires SGX availability on NWP platform
