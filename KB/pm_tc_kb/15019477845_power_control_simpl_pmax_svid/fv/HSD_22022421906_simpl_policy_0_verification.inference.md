# Deep Analysis: SIMPL Policy 0 Verification

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421906 |
| **Title** | SIMPL Policy 0 Verification |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | SIMPL - IccMax |
| **Sub-Feature** | SIMPL Policy 0 — verify policy is active and IO/Mem fabric freq within spec |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Verifies SIMPL Policy 0 (default safe policy) is active under core-centric + light IO/Mem workload, and that IO/Mem Fabric frequency limits are within spec bounds for Policy 0.

NWP: single IMH (imh0). `sv.sockets.imhs` → `sv.socket0.imh0`. Note: source TC notes "Need to be updated for new SIMPL definition" — verify against latest NWP HAS.

Tags: `DMR_PO`, `plc.ti_gate.b0`, `NGA_MAIN`, `plc.feature.p2`, `PMSS_NWP_READINESS_CHECK`.

---

## Section B: NWP-Specific Test Procedure

### NWP Command
```bash
python runPmx.py -x nwp.xml -p simpl -tM 60
```

### Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Start core-centric workload | Heavy core compute (e.g., stress-ng CPU) |
| 2 | Start light IO/Mem fabric workload | Light memory access pattern |
| 3 | Read `current_policy` | `sv.socket0.imh0.pcudata.patch_persistent.current_policy` |
| 4 | Verify `current_policy` = 0 | Policy 0 expected for heavy core + light IO/Mem |
| 5 | Read IO and Mem Fabric Freq Limits | `sv.socket0.imh0.pcudata.simpl_*` registers |
| 6 | Verify freqs within Policy 0 bounds | Per NWP HAS SIMPL Policy 0 table |

### NWP Register Paths
```python
current = sv.socket0.imh0.pcudata.patch_persistent.current_policy
assert current == 0, f"Expected Policy 0, got {current}"

# IO/Mem fabric freq limits for Policy 0
io_freq  = sv.socket0.imh0.pcudata.simpl_max_freq_0_0  # 0xe per fuse verification
mem_freq = sv.socket0.imh0.pcudata.simpl_max_freq_1_0
print(f"IO freq limit: {io_freq}, Mem freq limit: {mem_freq}")
```

### Pass Criteria
- `current_policy` = 0 on IMH0 under specified workload
- IO/Mem Fabric freq limits within spec for Policy 0
- No `target_policy` mismatch

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; `sv.sockets.imhs` → `sv.socket0.imh0`; verify Policy 0 freq limits against NWP HAS (update if HAS has changed since TC was authored)**

**Priority**: High — `PMSS_NWP_READINESS_CHECK`; Policy 0 is the default-always-active SIMPL policy
