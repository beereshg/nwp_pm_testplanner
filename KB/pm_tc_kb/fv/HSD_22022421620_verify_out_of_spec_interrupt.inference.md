# Deep Analysis: [Thermal Interrupts] Verify OUT_OF_SPEC Interrupt

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421620 |
| **Title** | [Thermal Interrupts] Verify OUT_OF_SPEC Interrupt |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Segment** | FV |
| **Feature** | SoC Thermal Management |
| **Sub-Feature** | OUT_OF_SPEC thermal interrupt — package MSR 0x1b2 only (core MSR bit is ZBB'd) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

Verifies **OUT_OF_SPEC_INT_ENABLE** — interrupt for critical temperature condition. 

**Important**: The core scoped MSR (0x19b) has this bit **ZBB'd**. Only the package MSR 0x1b2 is used for OOS interrupt. This ZBB carries over to NWP.

On NWP, OOS interrupt testing only from package MSR 0x1b2.

---

## Section B: NWP-Specific Test Procedure

### OOS Interrupt Architecture

- OOS (Out-of-Spec) = critical temperature reached (above Tj_max)
- **Core MSR 0x19b OOS bit: ZBB'd on DMR and NWP** — do not enable here
- **Package MSR 0x1b2 OOS bit: Functional** — use this only

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Enable OOS_INT_ENABLE only in package MSR 0x1b2 | Core MSR OOS bit ZBB'd |
| 2 | Run thermal_interrupt PMx | `python runPmx.py -x nwp.xml -p thermal_interrupt -tM 60 -M 5` |
| 3 | Inject critical temperature condition | DFX inject or TCC override |
| 4 | Verify OOS interrupt delivered via package path | APIC interrupt from PUnit |
| 5 | Verify OOS causes aggressive throttling | Frequency drops to Pm |

### NWP Pass Criteria
- OOS interrupt from package MSR 0x1b2 functional
- Core MSR 0x19b OOS bit confirmed non-functional (ZBB'd)
- OOS triggers aggressive throttle response

---

## Section F: Recommendation

**Recommendation: ADOPT — `dmr.xml` → `nwp.xml`; OOS package-only; core OOS ZBB'd**

1. `python runPmx.py -x nwp.xml -p thermal_interrupt -tM 60 -M 5`
2. Only test OOS from package MSR 0x1b2 (core MSR OOS is ZBB'd on NWP too)

**Priority**: Medium — `plc.feature.p1`; OOS critical temperature interrupt verification
