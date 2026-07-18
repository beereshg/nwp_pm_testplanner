# TCD 22022421029 -- VF Curve Fuses

| Field | Value |
|-------|-------|
| **TCD ID** | [22022421029](https://hsdes.intel.com/appstore/article-one/#/22022421029) |
| **Title** | VF curve fuses |
| **Status** | open |
| **Owner** | akurathi |
| **Parent TPF** | [16030732015 -- P-State Operating Range & Frequency Configuration](https://hsdes.intel.com/appstore/article-one/#/16030732015) |
| **Child TCs** | [22022422446](https://hsdes.intel.com/appstore/article-one/#/22022422446) -- VF curve fuses |
| **KB last updated** | 2026-07-17 |

---

## Section 1: Architecture / Micro-architecture and Functionality

The **V/F (Voltage-Frequency) Curve Fuses** define the safety envelope for core voltage at every frequency operating point. PCode constructs the V/F curve by reading fused VID anchor points (Pn, P1, P0) at boot and linearly interpolating between them to build a complete voltage-frequency table. All subsequent GV (Geyserville) transitions reference this table to determine the correct VID for any target ratio.

### Feature Overview

| Property | Detail |
|----------|--------|
| **Purpose** | Define core voltage at each frequency point; safety-critical -- prevents operating at insufficient voltage |
| **Fused Curves** | Up to 12 fused V/F curves per SoC; each curve maps ratio points to VID values |
| **Anchor Points** | Pn (lowest ratio), P1 (guaranteed), P0 (max turbo) -- VID values at each anchor |
| **Interpolation** | Linear between fused anchor points for intermediate ratios |
| **Core-to-Curve Mapping** | Per-core fuse assigns each core to a specific V/F curve |
| **GV Transition Rule** | Voltage-first upward (V before F), frequency-first downward (F before V) |
| **Adaptive Voltage** | DLVR/AVS can reduce voltage below nominal V/F curve for efficiency during light workloads |
| **SST-PP** | Can modify V/F curve per performance level (ZBB on NWP -- not applicable) |

### PCode V/F Curve Boot Flow

1. PCode reads all 12 V/F curve fuse sets from IMH die fuse bank at early init
2. For each curve: extracts VID values at Pn, P1, P0 anchor ratios
3. Builds interpolated V/F table covering the entire Pn-P0 frequency range
4. Assigns each core to its designated V/F curve via core-to-curve mapping fuses
5. FIVR initialized; V/F table ready before any frequency transition or CPL3 handoff
6. AVS/DLVR calibration may adjust operational voltage below nominal curve at runtime

### V/F Curve Mechanism

```
  Fuse Bank (IMH die)
  +------------------------------------------+
  |  12 VF Curves x 3 anchor points each    |
  |  Curve N: (Pn_VID, P1_VID, P0_VID)      |
  |  + Core-to-Curve mapping fuses           |
  +--------------------+---------------------+
                       | PCode reads at boot
                       v
  +------------------------------------------+
  |  PCode Internal V/F Table                |
  |  Linear interpolation between anchors    |
  |  Full ratio->VID mapping for each core   |
  +--------------------+---------------------+
                       |
          +------------+------------+
          v            v            v
    GV Upward     GV Downward    AVS/DLVR
    (V-first)     (F-first)     (adaptive)
          |            |            |
          v            v            v
    FIVR sets VID -> Core PLL sets ratio
          |
          v
    Observable: IA32_PERF_STATUS (0x198)
                SVID readback / voltage telemetry
```

### NWP-Specific Deltas

- V/F curve management is **fully supported on NWP** -- mechanism unchanged from DMR
- Same fuse-based VID anchor points (Pn, P1, P0); same 12-curve structure
- Same runtime V/F optimization (ITD voltage offset, Cdyn-based adjustment)
- PantherCove V/F characteristics reused from DMR
- SST-PP removed on NWP -- no per-SST-PP V/F profile variations
- NWP topology: single NIO (vs IMH0/IMH1 on DMR); PythonSV path = `sv.socket0.nio.punit.*`
- 2 CBBs (vs 4 on DMR); per-core curve mapping applies to 96 cores across 2 CBBs

---

## Section 2: Interface and Protocols

| Interface | Type | Description |
|-----------|------|-------------|
| VID fuse registers | IMH die fuse bank (RO) | Manufacturing-characterized VID anchor values at Pn, P1, P0 |
| Core-to-curve mapping fuses | IMH die fuse bank (RO) | Per-core assignment to one of 12 V/F curves |
| `IA32_PERF_STATUS` | MSR `0x198` (RO) | Current operating ratio -- corresponds to active V/F operating point |
| `PLATFORM_INFO` | MSR `0x0CE` [15:8] (RO) | P1 guaranteed ratio -- key V/F anchor point |
| FIVR control | PCode internal | Commands FIVR to target VID on GV transitions |
| DLVR/AVS | PCode internal | Adaptive voltage reduction below nominal V/F curve |
| SVID readback | Platform VR interface | Voltage verification at key ratio points |
| HPM mailbox | PCode telemetry | Access PCode internal V/F table data |

---

## Section 3: Reset / Power / Clocking

- V/F fuses are read once at PCode early init (before CPL3 handoff); no re-read after warm reset
- FIVR initialized from V/F table before any frequency transition is allowed
- Cold reset: full re-read of V/F fuses and V/F table reconstruction
- Power-on default: PCode holds core at Pn ratio until V/F table is validated and FIVR ready

---

## Section 4: Programming Model

**Read V/F curve data (PythonSV):**

```python
# NWP: use sv.socket0.nio.punit.* (not imh0/imh1 as on DMR)
# Search for VF fuse fields:
sv.socket0.nio.fuses.punit.search('vf_curve', 'f')

# Read per-curve VID anchors:
for curve_idx in range(12):
    vid_pn = sv.socket0.nio.fuses.punit.getbypath(f'vf_curve_{curve_idx}_vid_pn').read()
    vid_p1 = sv.socket0.nio.fuses.punit.getbypath(f'vf_curve_{curve_idx}_vid_p1').read()
    vid_p0 = sv.socket0.nio.fuses.punit.getbypath(f'vf_curve_{curve_idx}_vid_p0').read()

# Read PCode internal table via pcode.vars:
# sv.socket0.cbbs.pcode.vars.core.vf_curve.ats  (per-CBB)

# Current operating point:
perf_status = sv.socket0.nio.punit.ia32_perf_status.read()
current_ratio = (perf_status >> 8) & 0xFF
```

**Fuse override (pre-silicon):** Fuse override tool can inject alternate VID values for testing non-standard V/F curves.

---

## Section 5: Operational Behavior

| Scenario | Expected Behavior |
|----------|-------------------|
| Boot (cold) | PCode reads all 12 V/F curve fuses, builds interpolated table, assigns cores |
| GV upward (ratio increase) | PCode looks up target VID, commands FIVR to higher voltage **before** PLL ratio change |
| GV downward (ratio decrease) | PCode commands PLL to lower ratio **first**, then reduces FIVR voltage |
| Light workload | DLVR/AVS may adaptively reduce voltage below nominal V/F curve |
| Heavy workload (AVX) | DLVR ensures full margin voltage maintained per V/F curve |
| Fuse corruption | PCode V/F table mismatch -- test FAIL; potential voltage safety issue |
| VID inversion | Higher ratio with lower VID in fused curve -- invalid; test FAIL |

---

## Section 6: Corner Cases and Error Handling

- **Corrupt fuse**: If a VID anchor reads 0 or invalid value, PCode may MCA or use fallback
- **VID inversion**: Fused curve with non-monotonic voltage -- safety violation; should be caught at fuse programming
- **Core-to-curve mismatch**: Core assigned to non-existent curve index -- undefined behavior
- **Interpolation boundary**: Ratios exactly at anchor points vs between them -- verify both
- **AVS interaction**: V/F test should verify nominal curve **before** AVS/DLVR adjusts voltage

---

## Section 7: Security / Safety / Policy

- V/F curve defines the voltage safety envelope -- operating below curve voltage is a reliability risk
- Fuses are one-time-programmable; V/F curve set at manufacturing characterization
- VID values directly impact silicon reliability margin
- Test must verify monotonicity to prevent latent voltage-starve conditions

---

## Section 8: References

| Type | Link | Notes |
|------|------|-------|
| HAS | [CBB PM HAS VF Curve](https://docs.intel.com/documents/pm_doc/src/server/DMR/IP_PM_Features/CBB/DMR_CBB_PM.html) | 12-curve fuse format, PCode read and table construction |
| HAS | [Core P-State HAS](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_Pstates/Core_Pstate_HAS.html) | V/F curve in P-state context |
| HAS | [DMR Turbo HAS](https://docs.intel.com/documents/pm_doc/src/server/DMR/PM%20Features/DMR_Turbo.html) | Turbo V/F anchor points |
| KB | [pstate_v_f_curve.md](../../pm_features/pstate_stack/pstate_v_f_curve.md) | NWP delta, architecture, register table |
| HSD | [TC 22022422446](https://hsdes.intel.com/appstore/article-one/#/22022422446) | Child test case |
