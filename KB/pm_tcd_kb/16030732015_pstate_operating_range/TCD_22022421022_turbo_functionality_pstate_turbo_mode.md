# TCD 22022421022 -- Turbo Functionality - Pstate Turbo Mode

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421022](https://hsdes.intel.com/appstore/article-one/#/22022421022) |
| **Title** | Turbo Functionality - Pstate Turbo Mode |
| **Status** | open |
| **Owner** | akurathi |
| **Parent TPF** | [16030732015 -- P-State Operating Range & Frequency Configuration](https://hsdes.intel.com/appstore/article-one/#/16030732015) |
| **Child TCs** | [22022422395](https://hsdes.intel.com/appstore/article-one/#/22022422395) -- MSR 0xB2 TURBO_CONFIG, [22022422408](https://hsdes.intel.com/appstore/article-one/#/22022422408) -- Turbo BIOS Configurations, [22022422414](https://hsdes.intel.com/appstore/article-one/#/22022422414) -- Turbo C C6S-P, [22022422421](https://hsdes.intel.com/appstore/article-one/#/22022422421) -- Turbo X C1e, [22022422425](https://hsdes.intel.com/appstore/article-one/#/22022422425) -- Turbo X C6A, [22022422430](https://hsdes.intel.com/appstore/article-one/#/22022422430) -- Turbo X C6S, [22022422435](https://hsdes.intel.com/appstore/article-one/#/22022422435) -- Turbo configurations |
| **KB last updated** | 2026-07-17 |

---

## Section 1: Architecture / Micro-architecture and Functionality

**Pstate Turbo Mode** allows CPU cores to opportunistically boost frequency above the guaranteed P1 (base) frequency when thermal, power, and electrical headroom is available. The achievable turbo ratio is bounded by the **Turbo Ratio Limit (TRL)** table — one row per active core count — fused at manufacturing and optionally overridden downward by BIOS or OOB. PCode evaluates turbo headroom on every PEGA cycle and resolves the effective ratio as `min(TRL[N_active], RAPL_PL1/PL2, thermal_TCC, ICCP_license, EET_attenuation)`. The resolved ratio is written to the cores; **PLR (MSR 0x64F)** reports which constraint is actively limiting turbo.

### Turbo Resolution Flow

```
OS requests ratio > P1 (turbo range)
       |
       v
PCode PEGA resolves turbo ceiling each cycle:
  +----------------+  +----------------+  +---------------+
  | TRL[N_active]  |  | FACT[license]  |  | RAPL PL1/PL2  |
  | (active-core   |  | (ICCP license  |  | (power budget) |
  |  count row)    |  |  level cap)    |  |               |
  +------+----+----+  +------+----+---+  +------+---+----+
         |                   |                   |
         +-------+-----------+-------------------+
                 |
              min(all)  +  thermal TCC  +  EET attenuation
                 |
                 v
       Applied turbo ratio
       MSR 0xB2: encodes TurboMode + EETurbo active config
       PLR (MSR 0x64F): active limiting reason bitfield
```

### Key Concepts

| Concept | Description |
|---------|-------------|
| **TRL (Turbo Ratio Limit)** | Fused max turbo ratio per active core count (1..N); defines the turbo ceiling for each N-active-core scenario |
| **P1 (Base Frequency)** | Guaranteed operating frequency; turbo operates above P1 when headroom is available |
| **P0n (Max Single-Core Turbo)** | Highest achievable turbo ratio, applicable when 1 core active |
| **FACT table** | Frequency-AVX Clamp Table; limits turbo ratio for AVX-256 / AVX-512 / AMX workloads per ICCP license level |
| **ICCP license** | Intel Current Consumer Protocol license level (scalar / AVX2 / AVX512 / AMX); gates FACT-based turbo ceiling |
| **EET (Energy Efficient Turbo)** | Attenuates max turbo ratio to improve energy efficiency when enabled; affects TURBO_CONFIG MSR encoding |
| **PLR (Power Limit Reasons)** | MSR 0x64F bitfield; reports which constraint (thermal / power / ICCP / EET) is limiting turbo |
| **MSR 0xB2 TURBO_CONFIG** | Reflects active TurboMode + EETurbo configuration; written by PCode slow loop |
| **Module Turbo (1CPM)** | Sibling sub-feature (TCD 22022421019): when only 1 core per DCM module is active, higher-than-multcore TRL may be granted |

### NWP-Specific Deltas

- NWP uses **PantherCove (PNC)** BigCore; turbo algorithm reused from DMR without modification.
- **2 CBBs** (cbb0 + cbb1), up to 96 cores → different active-core TRL profile (fuse-dependent per SKU).
- **SST-PP / SST-BF removed** on NWP → no per-SST-level TRL variation; single TRL profile.
- **MasterMax removed** → no multi-die turbo coordination (NWP is monolithic single-die).
- TRL fuse values and FACT table entries differ from DMR; must use NWP-specific QDF values in tests.

### TC Coverage Map

| TC | Scope | Mechanism |
|----|-------|-----------|
| [22022422395 -- MSR 0xB2 TURBO_CONFIG](https://hsdes.intel.com/appstore/article-one/#/22022422395) | TURBO_CONFIG MSR reflects active turbo + EET config | Read MSR 0xB2; verify encoding matches TurboMode + EETurbo BIOS settings via Flexcon PM |
| [22022422408 -- Turbo BIOS Configurations](https://hsdes.intel.com/appstore/article-one/#/22022422408) | Turbo enabled via BIOS knobs; post-reboot grant confirmed | Set TurboMode BIOS knob; reboot; verify Flexcon PM shows turbo active; verify PERF_STATUS reaches P0n |
| [22022422414 -- Turbo C C6S-P](https://hsdes.intel.com/appstore/article-one/#/22022422414) | Turbo × C6S-P C-state cross-product | C6S-P entry/exit sweep; verify TRL row re-evaluated on wake; turbo grant restores within 1 PEGA cycle |
| [22022422421 -- Turbo X C1e](https://hsdes.intel.com/appstore/article-one/#/22022422421) | Turbo × C1E C-state cross-product | C1E entry/exit sweep; verify turbo headroom re-evaluated on wake; correct TRL[N_active] applied |
| [22022422425 -- Turbo X C6A](https://hsdes.intel.com/appstore/article-one/#/22022422425) | Turbo × C6A C-state cross-product | C6A entry/exit sweep; verify TRL row selected correctly as cores wake sequentially |
| [22022422430 -- Turbo X C6S](https://hsdes.intel.com/appstore/article-one/#/22022422430) | Turbo × C6S C-state cross-product | C6S entry/exit sweep; verify TRL[N_active] applied after all cores exit C6S |
| [22022422435 -- Turbo configurations](https://hsdes.intel.com/appstore/article-one/#/22022422435) | TRL accuracy vs active core count, ICCP license, power headroom, OS/HWP request | Sweep active core count (1..N); sweep ICCP license levels; sweep RAPL PL1/PL2 headroom; verify turbo ratio == min(TRL[N], FACT[license], RAPL) |

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Dir | Description |
|-----------|----------------|-----|-------------|
| MSR | `TURBO_RATIO_LIMIT` 0x1AD [63:0] | RO | Max turbo ratio for active core counts 1–8 (1 ratio/byte); fused TRL |
| MSR | `TURBO_RATIO_LIMIT_CORES` 0x1AE | RO | Extended TRL for core counts 9–16 |
| MSR | `IA32_MISC_ENABLE` 0x1A0 [38] | RW | Turbo disable bit: 1 = turbo off; 0 = turbo allowed (default) |
| MSR | `IA32_PERF_STATUS` 0x198 | RO | Current operating ratio (turbo ratio or PLR-limited value) |
| MSR | `IA32_PERF_CTL` 0x199 | RW | OS-requested P-state ratio (SW P-state override) |
| MSR | `TURBO_CONFIG` 0xB2 | RO | Active TurboMode + EETurbo configuration; written by PCode slow loop |
| MSR | `PLR` 0x64F | RO | Power Limit Reasons: bitfield reporting which constraint limits turbo |
| MSR | `PACKAGE_POWER_LIMIT` 0x610 | RW | PL1/PL2 power budget — constrains turbo headroom |
| MSR | `IA32_THERM_STATUS` 0x19C | RO | Thermal margin / TCC activation — thermal constraint for turbo |
| TPMI | TRL MMIO (OOB) | RW | OOB read/override of TRL values; BMC can lower max turbo OOB |
| PythonSV | `sv.socket0.cbb0.compute0.moduleX.coreY.threadZ.msr(0x198)` | RO | Per-core observed frequency ratio |
| PythonSV | `sv.socket0.cbb0.base.msr(0x1AD)` | RO | Package TRL readback |
| PythonSV | `sv.socket0.cbb0.base.msr(0xB2)` | RO | TURBO_CONFIG readback |
| PythonSV | `sv.socket0.cbb0.base.msr(0x64F)` | RO | PLR readback |

---

## Section 3: Reset / Power / Clocking

- **Pre-boot fuse read**: PCode reads TRL fuse values at early boot; FACT table populated from fuses.
- **PH5 / CPL3 (BIOS)**: BIOS enables turbo (`IA32_MISC_ENABLE[38]=0`); programs TRL overrides and BIOS knobs (TurboMode, EETurbo). RAPL PL1/PL2 set.
- **Runtime (each PEGA cycle)**: PCode re-evaluates turbo headroom — power, thermal, ICCP license, EET; applies TRL[N_active] constraint.
- **C-state exit**: On core wake from C1E / C6A / C6S / C6S-P, PCode re-evaluates N_active and selects the new TRL row within 1 PEGA cycle.
- **Warm reset**: Turbo mode setting preserved (MSR-backed state survives warm reset); TRL fuse re-read not required.
- **Cold reset**: Full re-initialization; BIOS must re-program TurboMode knob.
- **EET interaction**: EETurbo may reduce max turbo ratio at lower utilization levels; PCode adjusts TURBO_CONFIG and PERF_STATUS accordingly.

---

## Section 4: Programming Model

### Verify TRL readback

```python
import sys
sys.path.insert(0, '.')
# Read TRL (active core counts 1-8)
trl_msr = sv.socket0.cbb0.base.msr(0x1AD)
for n in range(1, 9):
    ratio = (trl_msr >> ((n-1)*8)) & 0xFF
    print("TRL[%d active cores] = %d (%0.1f GHz approx)" % (n, ratio, ratio*0.1))
```

### Verify TURBO_CONFIG (MSR 0xB2)

```python
turbo_cfg = sv.socket0.cbb0.base.msr(0xB2)
turbo_mode  = (turbo_cfg >> 0) & 0x1   # TurboMode active
eet_enabled = (turbo_cfg >> 1) & 0x1   # EETurbo active
print("TURBO_CONFIG: TurboMode=%d EETurbo=%d (raw=0x%X)" % (turbo_mode, eet_enabled, turbo_cfg))
```

### Verify observed turbo on a loaded core

```python
# Assumes stress workload is running on core0
perf_status = sv.socket0.cbb0.compute0.module0.core0.thread0.msr(0x198)
current_ratio = (perf_status >> 8) & 0xFF
print("Current turbo ratio on core0: %d (%.1f GHz approx)" % (current_ratio, current_ratio * 0.1))

# Cross-check against TRL[1] for single-core workload
trl_1core = sv.socket0.cbb0.base.msr(0x1AD) & 0xFF
print("TRL[1 core]: %d  -- observed should be <= TRL[1]" % trl_1core)
```

### Check PLR for turbo limiting reasons

```python
plr = sv.socket0.cbb0.base.msr(0x64F)
print("PLR = 0x%X" % plr)
# Bit interpretation: bit0=thermal, bit1=power, bit2=ICCP, bit3=EET (check NWP PLR HAS for exact mapping)
```

---

## Section 5: Operational Behavior

| Scenario | Expected Behavior |
|----------|-------------------|
| Single-core workload, turbo enabled, headroom available | Core runs at TRL[1] (P0n) — maximum single-core turbo |
| Multi-core workload (N active), headroom available | All active cores run at TRL[N]; ratio decreases as N increases |
| Turbo disabled via `IA32_MISC_ENABLE[38]=1` | All cores cap at P1; no turbo grant; PERF_STATUS ≤ P1 ratio |
| RAPL PL1 exceeded | PCode clips turbo below TRL[N]; PLR reports power limit; frequency throttled |
| Thermal TCC active | PCode clips turbo; PLR reports thermal limit; frequency ≤ thermal headroom |
| AVX-512 workload, ICCP license = AVX512 | FACT table applies; turbo ratio limited to FACT[AVX512] ceiling |
| EETurbo enabled | Max turbo attenuated at lower utilization; MSR 0xB2 [1]=1 |
| C1E exit (core wakes) | PCode re-evaluates N_active within 1 PEGA cycle; turbo grant restored |
| C6A exit (core wakes) | Same as C1E; TRL[N_active] re-applied after wakeup |
| C6S exit (all cores wake) | TRL row jumps from high-N back to lower-N; turbo increases |
| C6S-P exit | Full package exit; turbo fully re-evaluated including PL1/PL2 headroom |
| BIOS TurboMode knob = Disabled | `IA32_MISC_ENABLE[38]` set; TURBO_CONFIG [0]=0; cores stay at P1 |
| OOB TRL override (lower) | Effective TRL = min(fused, OOB_override); turbo ceiling lowered |

---

## Section 6: Corner Cases & Error Handling

- **TRL[1] vs TRL[N] boundary**: Verify TRL row switches correctly as cores enter/exit C-states; N_active counter must track accurately.
- **FACT vs TRL precedence**: Verify FACT ceiling applies only to AVX license holders; scalar cores not affected.
- **EETurbo + high utilization**: At high utilization, EET attenuation should be minimal; TURBO_CONFIG [1] can be set even when turbo ratio is near TRL[N].
- **Turbo disable persistence**: After `IA32_MISC_ENABLE[38]=1`, verify turbo does not re-enable after C-state exit or warm reset (unless BIOS re-enables).
- **OOB TRL override downward**: Verify PCode respects min(fused, OOB) and does not allow cores to exceed OOB limit.
- **PL2 short-window burst**: PL2 allows short turbo burst above PL1 budget; verify burst allowed within PL2 window, then clamped to PL1.
- **SST-PP removed**: On NWP, no per-SST-level TRL — verify no SST-PP-related turbo cross-product applies.
- **MasterMax removed**: No multi-die turbo coordination — verify single-die NWP does not reference MasterMax registers.
- **Atom die coexistence**: If atom die present on same socket, verify atom turbo logic is independent of big-core TRL.

---

## Section 7: Security / Safety / Policy

- `IA32_MISC_ENABLE[38]` (turbo disable) is OS-accessible at ring-0; no lock bit defined.
- TRL fuse is RO; BIOS/OOB can only override **downward** — cannot grant above fused ceiling.
- OOB TPMI TRL write is privileged (BMC/platform management only); not accessible from OS kernel.
- Turbo does not bypass RAPL or thermal limits — safety constraints always override turbo headroom.
- PLR reporting is read-only; no security exposure from reading MSR 0x64F.

---

## Section 8: References

- [CBB PM HAS — Turbo, TRL, FACT](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html)
- [NWP PM MAS — P-State Turbo Mode](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [PLR HAS — Power Limit Reasons MSR 0x64F](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/PLR/PLR_HAS.html)
- [Intel SDM — MSR 0x1AD TURBO_RATIO_LIMIT, MSR 0x1A0 IA32_MISC_ENABLE, MSR 0x198 PERF_STATUS](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html)
- [C-state HAS — C-state interactions with turbo](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Cstates/Cstate_HAS.html)
- [EET HAS — Energy Efficient Turbo](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/EET/EET_HAS.html)
- [TPMI HAS — OOB TRL override](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/TPMI/TPMI_HAS.html)
- [KB Feature: Pstate Turbo Mode](../../../KB/pm_features/pstate_stack/pstate_turbo_mode.md)
- [KB TCD 22022421019 — 1CPM Pstate Turbo Mode](TCD_22022421019_1cpm_pstate_turbo_mode.md)
- [Parent TPF HSD 16030732015](https://hsdes.intel.com/appstore/article-one/#/16030732015)
