# TCD 22022421001 -- Guaranteed Ratio Resolving

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421001](https://hsdes.intel.com/appstore/article-one/#/22022421001) |
| **Title** | Guaranteed Ratio Resolving |
| **Status** | open |
| **Parent TPF** | [16030732015 -- P-State Operating Range & Frequency Configuration](https://hsdes.intel.com/appstore/article-one/#/16030732015) |
| **Child TCs** | [22022422293](https://hsdes.intel.com/appstore/article-one/#/22022422293) -- Avx P1 Level BIOS knob check / [22022422296](https://hsdes.intel.com/appstore/article-one/#/22022422296) -- Guaranteed Ratio resolving |
| **KB last updated** | 2026-07-17 |

---

## Section 1: Architecture / Micro-architecture and Functionality

The **Guaranteed Ratio (P1)** is the minimum frequency the platform unconditionally guarantees under any workload — it is the floor of the `IA32_HWP_CAPABILITIES.Guaranteed` field and must never be violated in normal operation.

P1 is resolved from the `IA_P1_RATIO` fuse, optionally clipped by `FlexRatio`, and further reduced for AVX workloads via the `AvxP1Level` BIOS knob. On NWP, P1 is **common across all CCPs** (both CBBs share the same guaranteed ratio, identical to DMR behavior).

### P1 Resolution Pipeline

```
Fuse: IA_P1_RATIO
      |
      v  clipped by FlexRatio (BIOS/OS override)
P1_base = min(IA_P1_RATIO, FlexRatio)
      |
      |  AVX workload active + AvxP1Level != 0?
      v
If AvxP1Level = 0x1: P1_avx = P1_base - 1 ratio step (100 MHz)
If AvxP1Level = 0x2: P1_avx = P1_base - 2 ratio steps (200 MHz)
      |
      v
IA32_HWP_CAPABILITIES.Guaranteed = effective P1
  (reported identically on all CCPs -- NWP common guaranteed ratio)

P1 is guaranteed floor:
  frequency MUST NOT drop below P1 in normal, non-error operation
```

### Key Concepts

| Concept | Description |
|---------|-------------|
| **IA_P1_RATIO** | Fuse encoding the base guaranteed ratio; one ratio step = 100 MHz |
| **FlexRatio** | BIOS/OS knob that can cap both P0 and P1 — P1 clipped to min(IA_P1_RATIO, FlexRatio) |
| **AvxP1Level** | BIOS knob (0/1/2) that demotes P1 by 1 or 2 steps when an AVX workload is active, protecting thermal envelope |
| **IA32_HWP_CAPABILITIES.Guaranteed** | MSR 0x771 bits [15:8] — reflects current effective P1 as seen by OS/CPUID |
| **Common P1** | NWP reports the same P1 on all CCPs (no per-CCP P1 differentiation, same as DMR) |

### NWP-Specific Deltas

- **2 CBBs** (cbb0 + cbb1): PCode writes the same resolved P1 to both CBBs' HWP_CAPABILITIES.Guaranteed.
- **No per-CCP P1 delta**: Unlike some earlier platforms, NWP has a single IA_P1_RATIO fuse shared across all cores.
- **AvxP1Level applies to AVX-512 and AVX2**: When an eligible AVX workload is detected, PCode applies the demotion within the same slow-loop tick.
- **FlexRatio source**: Typically set by BIOS from FLEX_RATIO_MSR_LOCK; on NWP, PCode reads it at init and caches.
- **P1 != Pn (minimum ratio)**: Pn (lowest power P-state) can be lower than P1; P1 is the *guaranteed* minimum, not the absolute minimum ratio.

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422296 -- Guaranteed Ratio resolving](https://hsdes.intel.com/appstore/article-one/#/22022422296) | Base P1 fuse → HWP_CAPABILITIES.Guaranteed; common P1 across CCPs | Read IA_P1_RATIO via PythonSV fuse path; verify IA32_HWP_CAPABILITIES.Guaranteed matches; compare across socket0 CCPs |
| [22022422293 -- Avx P1 Level BIOS knob check](https://hsdes.intel.com/appstore/article-one/#/22022422293) | AvxP1Level 0x1 and 0x2 demotion; AVX workload trigger | Set AvxP1Level via BIOS knob; run AVX workload; verify Guaranteed ratio decreases by 1/2 steps; verify non-AVX path restores base P1 |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Direction | Description |
|-----------|----------------|-----------|-------------|
| MSR | IA32_HWP_CAPABILITIES (0x771) bits [15:8] | RO | Guaranteed field — effective P1 visible to OS |
| MSR | IA32_PERF_STATUS (0x198) bits [15:8] | RO | Current frequency ratio — verify never drops below P1 |
| Fuse | IA_P1_RATIO | RO | Base guaranteed ratio from fuses |
| BIOS setup | FlexRatio knob | RW (BIOS) | Caps both P0 and P1; PCode clips IA_P1_RATIO to this value |
| BIOS setup | AvxP1Level | RW (BIOS) | 0=no demotion, 1=−1 step, 2=−2 steps for AVX workloads |
| PythonSV | sv.socket0.cbb0.compute0.module0.core0.thread0.msr(0x771) | RO | Read HWP_CAPABILITIES.Guaranteed per core |
| PythonSV | sv.socket0.cbb0.compute0.module0.core0.thread0.msr(0x198) | RO | Read current operating ratio |
| PythonSV | sv.socket0.nio0.tpmi... or fuse path | RO | Read IA_P1_RATIO from fuse or PCode-cached variable |

---

## Section 3: Reset / Power / Clocking

- **PH5 (PrimeCode init)**: PCode reads `IA_P1_RATIO` fuse and `FlexRatio`; computes `P1_base` and programs `IA32_HWP_CAPABILITIES.Guaranteed` for all CCPs.
- **CPL3 (BIOS)**: BIOS programs `AvxP1Level` knob before handing off to OS. PCode reads this at HWP init.
- **Slow loop (runtime)**: PCode monitors AVX workload activity; applies or removes AvxP1Level demotion to Guaranteed field dynamically.
- **Reset**: P1 is re-resolved from fuse at every cold/warm reset. No persistent state across power cycles.
- **FlexRatio lock**: FlexRatio MSR is typically locked by BIOS before OS handoff; PCode caches the value at init.
- **Frequency floor enforcement**: P-state requests from OS (via HWP_REQUEST or PERF_CTL) are clamped to P1 at the bottom; PCode rejects any request below Guaranteed.

---

## Section 4: Programming Model

### Read Current Guaranteed Ratio (PythonSV)

```python
# Read IA32_HWP_CAPABILITIES.Guaranteed on core0
hwp_cap = sv.socket0.cbb0.compute0.module0.core0.thread0.msr(0x771)
guaranteed = (hwp_cap >> 8) & 0xFF
print(f"Guaranteed ratio: {guaranteed} ({guaranteed * 100} MHz effective)")

# Verify common P1 across all CCPs (NWP)
for cbb in [sv.socket0.cbb0, sv.socket0.cbb1]:
    for compute in cbb.computes:
        for module in compute.modules:
            g = (module.core0.thread0.msr(0x771) >> 8) & 0xFF
            assert g == guaranteed, f"P1 mismatch on {module.target_info.path}: {g} vs {guaranteed}"
print("P1 is uniform across all CCPs")
```

### Verify P1 Matches Fuse

```python
# Read IA_P1_RATIO from fuse (path may vary by NWP stepping)
p1_fuse = sv.socket0.fuses.ia_p1_ratio  # adjust path per NWP namednodes layout

# Apply FlexRatio clip (read FlexRatio from MSR 0x194)
flex_ratio_msr = sv.socket0.cbb0.compute0.module0.core0.thread0.msr(0x194)
flex_ratio = (flex_ratio_msr >> 8) & 0xFF if (flex_ratio_msr >> 16) & 1 else 0xFF

p1_expected = min(p1_fuse, flex_ratio) if flex_ratio != 0xFF else p1_fuse
assert guaranteed == p1_expected, f"P1 mismatch: HWP={guaranteed}, expected={p1_expected}"
```

### Verify AvxP1Level Demotion

```python
import time

# Read baseline Guaranteed (no AVX load)
baseline_g = (sv.socket0.cbb0.compute0.module0.core0.thread0.msr(0x771) >> 8) & 0xFF

# Run AVX-512 workload (via stress tool or PEGA AVX injection)
# ... launch avx workload ...
time.sleep(0.1)  # wait for slow-loop tick

# Read updated Guaranteed during AVX workload
avx_g = (sv.socket0.cbb0.compute0.module0.core0.thread0.msr(0x771) >> 8) & 0xFF

# With AvxP1Level=1: expect demotion by 1 step
assert avx_g == baseline_g - 1, f"AvxP1Level=1: expected {baseline_g-1}, got {avx_g}"
```

---

## Section 5: Operational Behavior

| Scenario | Expected Behavior |
|----------|-------------------|
| Normal boot, no FlexRatio | Guaranteed = IA_P1_RATIO fuse value |
| FlexRatio < IA_P1_RATIO | Guaranteed = FlexRatio (clipped) |
| FlexRatio >= IA_P1_RATIO | Guaranteed = IA_P1_RATIO (fuse wins) |
| AvxP1Level=0, AVX workload | Guaranteed unchanged from P1_base |
| AvxP1Level=1, AVX workload | Guaranteed = P1_base - 1 step (100 MHz lower) |
| AvxP1Level=2, AVX workload | Guaranteed = P1_base - 2 steps (200 MHz lower) |
| AVX workload ends | Guaranteed restored to P1_base within 1 slow-loop tick |
| Multi-CCP query | All CCPs (cbb0 + cbb1) report same Guaranteed value |
| Frequency below P1 | Not permitted in normal operation; PCode clamps requests to P1 floor |
| Turbo disabled | P0=P1=Pn; Guaranteed still valid and correctly reported |

---

## Section 6: Corner Cases & Error Handling

- **AvxP1Level=2 with P1_base=1**: Demotion would underflow; PCode must not write Guaranteed < 1 — verify clamping at 1 (100 MHz).
- **FlexRatio=0 (disabled/not set)**: PCode should treat as no-clip — verify Guaranteed = IA_P1_RATIO when FlexRatio is 0 or unlocked.
- **Dynamic FlexRatio change at runtime**: FlexRatio is typically locked; if changed while running, verify PCode re-evaluates P1.
- **AvxP1Level demotion + Turbo disabled**: Verify Guaranteed still demotes correctly even when P0=P1.
- **HWP_REQUEST.Minimum above P1**: OS can request a higher minimum via HWP_REQUEST.Minimum_Perf; verify PCode respects the max(HWP_REQUEST.Min, Guaranteed) semantics.
- **Cross-CCP consistency check**: On NWP with 2 CBBs, an inconsistency between cbb0 and cbb1 Guaranteed fields is a PCode bug — verify no such delta appears.
- **CPUID leaf 6 vs MSR**: CPUID.6H:EAX[7] indicates HWP_CAPABILITIES support; verify Guaranteed field matches between CPUID enumeration path and MSR read.

---

## Section 7: Security / Safety / Policy

- `IA32_HWP_CAPABILITIES` is RO to software — no security concern for Guaranteed field.
- `AvxP1Level` is a BIOS knob set in pre-boot; OS cannot override it at runtime.
- P1 is a firmware-guaranteed minimum; violating P1 under normal conditions would constitute a correctness/reliability bug.
- FlexRatio MSR is typically locked by BIOS (`FLEX_RATIO_MSR_LOCK` bit) before OS boot, preventing runtime changes.

---

## Section 8: References

- [NWP PM MAS -- P-State Operating Range](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [Core P-State HAS -- Guaranteed Ratio P1](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html)
- Intel SDM Vol 3B -- IA32_HWP_CAPABILITIES MSR (0x771), Guaranteed field bits [15:8]
- Intel SDM Vol 3B -- IA32_PERF_STATUS MSR (0x198)
- [Parent TPF HSD 16030732015](https://hsdes.intel.com/appstore/article-one/#/16030732015)
