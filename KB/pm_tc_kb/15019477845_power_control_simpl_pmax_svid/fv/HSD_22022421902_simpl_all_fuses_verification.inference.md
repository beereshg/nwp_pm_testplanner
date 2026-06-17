# Deep Analysis: SIMPL All Fuses Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421902 |
| **Title** | SIMPL - All Fuses Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SIMPL - IccMax |
| **Sub-Feature** | SIMPL fuse verification — all 4 policy fuse values match spec for IMH0 |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Verifies SIMPL fuse values for all 4 policies. Source TC lists both IMH0 and IMH1 — NWP has single IMH (imh0) only; only IMH0 fuses are verified.

Command: `flexconPM.py` (no NWP-specific XML change needed for fuse read; register paths updated for single IMH).

Tags: `DMR_PO`, `plc.ti_gate.b0`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP Fuse Verification
```python
# NWP: single IMH → imh0 only (no imh1)
import sv

# Policy 0 fuse
p0_fuse = sv.socket0.imh0.fuses.punit.pcode_simpl_policy_0_imh_cfcio_max_freq
p0_pcud = sv.socket0.imh0.pcudata.simpl_max_freq_0_0
assert p0_fuse == 0xe, f"Policy 0 fuse: expected 0xe, got {hex(p0_fuse)}"
assert p0_pcud == 0xe, f"Policy 0 pcudata: expected 0xe, got {hex(p0_pcud)}"

# Policy 1 fuse
p1_fuse = sv.socket0.imh0.fuses.punit.pcode_simpl_policy_1_imh_cfcio_max_freq
p1_pcud = sv.socket0.imh0.pcudata.simpl_max_freq_0_1
assert p1_fuse == 0x14
assert p1_pcud == 0x14

# Policy 2 fuse
p2_fuse = sv.socket0.imh0.fuses.punit.pcode_simpl_policy_2_imh_cfcio_max_freq
p2_pcud = sv.socket0.imh0.pcudata.simpl_max_freq_0_2
assert p2_fuse == 0x14
assert p2_pcud == 0x14

# Policy 3 fuse
p3_fuse = sv.socket0.imh0.fuses.punit.pcode_simpl_policy_3_imh_cfcio_max_freq
p3_pcud = sv.socket0.imh0.pcudata.simpl_max_freq_0_3
assert p3_fuse == 0x17
assert p3_pcud == 0x17

print("All IMH0 SIMPL fuses verified.")
# NOTE: NWP has no IMH1 — do not check imh1 registers
```

### Expected Values (from source TC)

| Policy | Fuse / PcuData Register | Expected Value |
|--------|------------------------|----------------|
| Policy 0 | `pcode_simpl_policy_0_imh_cfcio_max_freq` | `0xe` |
| Policy 1 | `pcode_simpl_policy_1_imh_cfcio_max_freq` | `0x14` |
| Policy 2 | `pcode_simpl_policy_2_imh_cfcio_max_freq` | `0x14` |
| Policy 3 | `pcode_simpl_policy_3_imh_cfcio_max_freq` | `0x17` |

### Pass Criteria
- All 4 SIMPL policy fuses match expected values on IMH0
- `fuse == pcudata` (fuse correctly loaded into PcuData)

---

## Section F: Recommendation

**Recommendation: ADOPT — Skip IMH1 checks (NWP has no IMH1); verify IMH0 fuses only; fuse path: `sv.socket0.imh0.fuses.punit.*`; expected values as specified above**

**Priority**: High — `PMSS_NWP_READINESS_CHECK`; SIMPL fuse values determine frequency limits for IO/Mem fabric — wrong values affect entire PM correctness
