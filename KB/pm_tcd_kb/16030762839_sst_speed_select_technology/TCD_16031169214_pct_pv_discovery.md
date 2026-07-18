# TCD 16031169214 — PCT - PV Discovery

| Field | Value |
|-------|-------|
| **TCD ID** | [16031169214](https://hsdes.intel.com/appstore/article-one/#/16031169214) |
| **Title** | PCT - PV Discovery |
| **Status** | open |
| **Owner** | bg3 |
| **Parent TPF** | [16030762939 — NWP PM PCT (Priority Core Turbo)](https://hsdes.intel.com/appstore/article-one/#/16030762939) |
| **Siblings** | [22022420855 — PCT Enabling & Discovery](https://hsdes.intel.com/appstore/article-one/#/22022420855) · [22022420862 — PCT - PV BIOS Configuration and Disable](https://hsdes.intel.com/appstore/article-one/#/22022420862) |
| **Feature** | Power / SST — PCT PV: OS-layer feature discovery, capability reporting, and 2-CBB topology enumeration |
| **KB last updated** | 2026-07-18 |

---

## Section 1: Architecture / Micro-architecture and Functionality

**PCT - PV Discovery** validates that the platform correctly reports PCT feature support status, available partition count, and HP/LP configuration through the BIOS Setup interface and the `intel-speed-select` user-space tool on Ubuntu Linux. This is distinct from sibling TCD 22022420862 which validates the partition count *configuration* paths — this TCD validates the *discovery* and *reporting* surface.

**Scope:** feature capability detection, BIOS knob visibility rules (hidden when unsupported), SST tool topology enumeration, and 2-CBB NWP topology correctness as seen from the OS.

> **Architecture overview:** See [TPF 16030762939 — NWP PM PCT](https://hsdes.intel.com/appstore/article-one/#/16030762939) §2 Design Details for boot flow, CLOS mechanism, and frequency hierarchy.

### TC Coverage Map

| TC | Title | Scope |
|----|-------|-------|
| [16030717720](https://hsdes.intel.com/appstore/article-one/#/16030717720) | [PV] SST PCT Discovery | PCT feature support status, partition count, HP/LP params via BIOS + `intel-speed-select`; knobs hidden when FEATURE_SUPPORTED=0 |

### NWP-Specific Deltas

- **SST_TF_INFO_0.FEATURE_SUPPORTED**: must = 1 on NWP PCT-capable QDF; if 0, BIOS must hide PCT partition count knob
- **2-CBB topology**: `intel-speed-select` must enumerate HP modules across both CBBs (not just CBB0); NWP-specific validation point
- **Max partitions** = `SST_TF_INFO_8.NUM_CORE_0 / MAX_LPIDS` (typically 4); BIOS must report this correctly via SST tool

---

## Section 2: Interfaces and Protocols

| Interface | Register / Path | Direction | Role |
|-----------|----------------|-----------|------|
| BIOS Setup | PCT Partition Count knob visibility | RO | Hidden if `SST_TF_INFO_0.FEATURE_SUPPORTED = 0`; visible when PCT capable |
| `intel-speed-select` | `isst perf-profile info -l 0` | RO | Reports HP module count, APIC IDs, feature enabled flag |
| `intel-speed-select` | `isst perf-profile get-config-levels` | RO | Reports max partition count |
| Linux sysfs | `/sys/bus/cpu/devices/cpuN/cpufreq/cpuinfo_max_freq` | RO | HP vs LP frequency ceiling per core — OS view of PCT capability |
| TPMI | `SST_TF_INFO_0.FEATURE_SUPPORTED` | RO | Source of truth for PCT capability gate |
| TPMI | `SST_TF_INFO_8.NUM_CORE_0` | RO | Max HP modules = max partition count |

---

## Section 3: Reset, Power, and Clocking

- **Phase 5 (PrimeCode)**: `SST_TF_INFO_0.FEATURE_SUPPORTED` set from fuses. If 0, BIOS must treat PCT as unsupported.
- **BIOS CPL3**: reads `FEATURE_SUPPORTED`; if 1, exposes PCT partition count knob in Setup menu; if 0, hides it.
- **OS boot**: `intel-speed-select` reads TPMI at boot; reports topology discovered at that point only.

---

## Section 4: Programming Model

The discovery path is read-only from the OS perspective. BIOS gates all PCT configuration on `SST_TF_INFO_0.FEATURE_SUPPORTED`. The `intel-speed-select` tool reads TPMI registers to build its topology report.

**FEATURE_SUPPORTED = 1 path:**
- BIOS exposes PCT partition count knob (0 to max)
- `intel-speed-select perf-profile info` reports HP modules, APIC IDs, frequency capabilities
- `cpuinfo_max_freq` per core reflects HP/LP ceiling

**FEATURE_SUPPORTED = 0 path:**
- BIOS hides PCT partition count knob (all SKUs on NWP are PCT-capable by design, but knob gated by fuse)
- `intel-speed-select` should report PCT as disabled / not supported
- All cores report conventional turbo `cpuinfo_max_freq`

---

## Section 5: Operational Behavior

| Scenario | Expected Behavior | TC |
|----------|-------------------|----|
| PCT capable QDF (FEATURE_SUPPORTED=1) | BIOS exposes partition count knob; `intel-speed-select` reports HP module count and APIC IDs | [16030717720](https://hsdes.intel.com/appstore/article-one/#/16030717720) |
| PCT disabled (partition count=0) | `intel-speed-select` reports no HP modules active despite CLOS_ASSOC in TPMI | [16030717720](https://hsdes.intel.com/appstore/article-one/#/16030717720) |
| 2-CBB NWP topology | `intel-speed-select` enumerates HP modules across both CBBs; APIC IDs span both | [16030717720](https://hsdes.intel.com/appstore/article-one/#/16030717720) (G7 gap) |

---

## Section 6: Corner Cases & Error Handling

| Corner Case | Description | Current Coverage | Action |
|-------------|-------------|-----------------|--------|
| **FEATURE_SUPPORTED = 0** | BIOS must hide knob; SST tool must report unsupported | TC 16030717720 tests positive path; feature-unsupported knob-hiding not covered | *(TC TBD)* |
| **2-CBB enumeration completeness** | `intel-speed-select` must report HP modules from both CBBs, not just CBB0 | TC 16030717720 does not explicitly verify cross-CBB enumeration (G7) | *(TC TBD — add step to 16030717720)* |
| **Max partition count reporting** | `isst perf-profile get-config-levels` must match `SST_TF_INFO_8.NUM_CORE_0 / MAX_LPIDS` | Not explicitly verified | Add as assertion to TC 16030717720 |

---

## Section 7: Security / Safety / Policy

- `intel-speed-select` requires root (`CAP_SYS_ADMIN`). `kayak` runs as root on validation images.
- Discovery is read-only — no security risk in this TCD.

---

## Section 8: References

- [PCT (Priority Core Turbo) HAS](https://docs.intel.com/documents/pm_doc/src/server/arch_common/PCT/PCT.html)
- [Intel SST HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/SST/Intel_SST.html)
- [NWP PM MAS — PCT section](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html)
- [CCB HSD 14026595435](https://hsdes.intel.com/appstore/article-one/#/14026595435) — NWP 8 HP cores, 4.4 GHz target
- [PCT - PV BIOS Configuration and Disable TCD 22022420862](https://hsdes.intel.com/appstore/article-one/#/22022420862)
- [PCT Enabling & Discovery TCD 22022420855](https://hsdes.intel.com/appstore/article-one/#/22022420855)
- KB: KB/pm_features/sst/pct.md
