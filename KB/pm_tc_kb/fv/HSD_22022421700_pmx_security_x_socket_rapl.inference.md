# Deep Analysis: pmx Security x Socket RAPL

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421700 |
| **Title** | pmx Security x Socket RAPL |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Socket RAPL |
| **Sub-Feature** | RAPL cross-product with SGX + TDX security features enabled |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

This test verifies **Socket RAPL energy reporting is functional while SGX and TDX are enabled** via BIOS knobs. The RAPL cross-product validates that security feature enablement does not break RAPL energy accounting.

Test approach:
1. Enable SGX + TDX via BIOS knobs (`EnableTdx`, `EnableSgx`, etc.)
2. Verify SGX/TDX active via MSR and CPUID
3. Run RAPL cross-product PMx (`cpu_rapl_cross`, `core_power`)
4. Verify RAPL energy reporting correct with security enabled

Tags: `PMSS_NWP_READINESS_CHECK` — NWP candidacy confirmed

**NWP Note on SGX/TDX availability**: If SGX or TDX is not available on NWP silicon (feature-disabled or not implemented), the BIOS knob configuration step adapts — test the RAPL portion with security features available on NWP (or with at least one of SGX/TDX if only partial support). RAPL energy accounting must be correct regardless of security feature state.

---

## Section B: NWP-Specific Test Procedure

### BIOS Knob Configuration (NWP)

| Knob | Value | Note |
|------|-------|------|
| `EnableTdxSeamldr` | 0x1 | If TDX supported on NWP |
| `DfxEnableTdxModule` | 0x1 | If TDX supported on NWP |
| `EnableTdx` | 0x1 | If TDX supported on NWP |
| `EnableSgx` | 0x1 | If SGX supported on NWP |
| `DfxPoisonEn` | 0x1 | Poison enable |
| `ControlIommu` | 0x0 | IOMMU passthrough |
| `MemCeFloodPolicy` | 0x0 | CE flood policy |
| `EccModeSel` | 0x1 | ECC mode |

### Adapted PMx Command
```
python runPmx.py -x nwp.xml -p cpu_rapl_cross -p core_power -tM 60 -M 60
```

### Adapted Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Configure BIOS knobs for security features available on NWP | Skip knobs for features not on NWP silicon |
| 2 | Verify security feature active | `msr -r -o 1401` (TDX bits 10-11); `cpuid 0x12` (SGX bits 0-1) |
| 3 | Run RAPL cross-product with core power | `python runPmx.py -x nwp.xml -p cpu_rapl_cross -p core_power -tM 60 -M 60` |
| 4 | Verify RAPL energy reporting correct with security enabled | Energy status MSRs update; limits enforced |

### NWP: 2 CBBs
- NWP: 2 CBBs × 48 cores; single `imh0`
- RAPL domain covers both CBBs
- `runPmx.py -x nwp.xml` (not `dmr.xml`)

### Pass Criteria
- RAPL energy status updates correctly while security features enabled
- RAPL power limits enforced during security feature active state
- No RAPL energy freeze or hang under SGX/TDX workload

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; verify SGX/TDX availability on NWP; adapt BIOS knobs accordingly**

1. `python runPmx.py -x nwp.xml -p cpu_rapl_cross -p core_power -tM 60 -M 60`
2. If NWP lacks SGX or TDX: skip corresponding BIOS knob; test RAPL with available security features
3. NWP: 2 CBBs, single `imh0`; RAPL domain covers full socket

**Priority**: Medium — security × RAPL interaction validation; verify NWP security feature availability before execution
