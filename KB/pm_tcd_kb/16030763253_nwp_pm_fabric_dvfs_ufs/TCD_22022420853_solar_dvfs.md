# TCD: Solar DVFS

| Field | Value |
|-------|-------|
| **TCD ID** | [22022420853](https://hsdes.intel.com/appstore/article-one/#/22022420853) |
| **Title** | Solar DVFS |
| **Status** | open (TCs rejected/ZBB) |
| **Owner** | mps |
| **Parent TP** | [16030763253 -- NWP PM Fabric DVFS (UFS)](https://hsdes.intel.com/appstore/article-one/#/16030763253) |
| **KB last updated** | 2026-06-24 |
| **Feature** | Fabric DVFS -- Solar DVFS (not applicable on NWP) |
| **NWP Disposition** | ZBB -- Solar DVFS architecture not used on NWP |

## Section 1: Architecture / Micro-architecture and Functionality

**Solar DVFS** (Solar Dynamic Voltage and Frequency Scaling) refers to a server-specific DVFS mechanism associated with the Solar die architecture. NWP (Newport) does not use the Solar die architecture -- NWP uses a different compute die topology (CSK-P / CSK-E via NIO + CBB). Solar DVFS test content is therefore **not applicable on NWP**.

### NWP Disposition

All TCs under this TCD are **ZBB (rejected) on NWP**: NWP does not include Solar die components, so Solar-specific DVFS validation cannot be executed.

### TC Coverage Map

| TC | Title | NWP Status | Reason |
|----|-------|-----------|--------|
| [22022422095 -- [Solar] DVFS-dvfs_all_random](https://hsdes.intel.com/appstore/article-one/#/22022422095) | Solar DVFS random test | **Rejected -- ZBB** | Solar die architecture not present on NWP |

### NWP Fabric DVFS Context

On NWP, Fabric DVFS (UFS -- Uniform Frequency Scaling or Uncore Frequency Scaling) operates on a different architecture:
- NWP uses **CBB (compute) die + NIO (I/O) die** topology
- CBB DVFS is managed by PCode on each CBB
- NIO (fabric / uncore) frequency scaling is managed by PrimeCode on NIO
- Solar-specific DVFS registers and flows do not exist on NWP

---

## Section 2: Interfaces and Protocols

Not applicable -- Solar DVFS architecture not present on NWP.

---

## Section 3: Reset, Power, and Clocking

Not applicable -- see feature context in Section 1.

---

## Section 4: Programming Model

Not applicable -- see feature context in Section 1.

---

## Section 5: Operational Behavior

Not applicable -- see feature context in Section 1.

---

## Section 6: Corner Cases & Error Handling

Not applicable -- see feature context in Section 1.

---

## Section 7: Security / Safety / Policy

Not applicable -- see feature context in Section 1.

---

## Section 8: References

- [NWP PM MAS](https://docs.intel.com/documents/custom-xeon/newport-docs/mas/pm/nwp_imh_soc_pm_mas.html) -- NWP compute and fabric topology
- [NWP HAS PM Features](https://docs.intel.com/documents/custom-xeon/newport-docs/has/Overview/NWP_HAS.html) -- NWP feature scope
