## Section 1: Architecture / Micro-architecture and Functionality

**Fast C1E autopromotion** is a hardware mechanism on NWP (PantherCove PNC) that automatically promotes OS-requested C1 (`HALT`) entries to C1E (Enhanced Halt State with voltage reduction) when the BIOS knob `C1EAutopromotion` is enabled. This allows energy savings without requiring OS changes — the hardware transparently deepens the C-state.

### C1E Autopromotion Flow

```
OS executes HALT (C1 request)
    └─► C1EAutopromotion enabled? ──YES──► Core enters C1E (FIVR voltage reduction)
                                  └─NO──► Core enters C1 (clock gate only)
```

### BIOS Knob to Register Propagation

| BIOS Knob | UEFI Variable | PCode Register | MSR / Path |
|-----------|--------------|----------------|------------|
| `C1EAutopromotion` | `PROC_C1E_ENABLE` | `MSR_POWER_CTL` bit 1 | MSR 0x1FC, bit[1] |
| Value=1 | → Enabled | → `c1e_enable=1` | HALT→C1E automatic |
| Value=0 | → Disabled | → `c1e_enable=0` | HALT→C1 only |

### MSR_POWER_CTL (0x1FC) — C1E Control

| Bit | Field | Description |
|-----|-------|-------------|
| 0 | `bi_dir_prochot_en` | Bidirectional PROCHOT enable |
| 1 | **`c1e_enable`** | **C1E autopromotion enable** |
| 14 | `disable_cstate_interrupt` | Disable C-state interrupt |


### NWP-Specific Deltas

| Aspect | DMR (Reference) | NWP (PantherCove PNC) | Impact on Test |
|--------|----------------|----------------------|----------------|
| CBB count | Up to 4 | **2** | All-core loops: `range(4)` -> `range(2)` |
| Cores per CBB | 64 | **48** | Per-CBB loops: `range(64)` -> `range(48)` |
| Total cores | 256 | **96** | Scale workload and verification accordingly |
| PkgC6 | Supported | **ZBB (Zero Bit Budget)** | `IA32_PKG_C6_RESIDENCY` (0x3F9) must stay 0 |
| Register prefix | `cbb{0..3}` | **`cbb{0,1}`** | Adjust all PythonSV paths |
| DCM count | 32 per socket | **12 per socket** | MC6 module loops: `range(32)` -> `range(12)` |
| HW Thread count | 2 per core | **2 per core** | No change |


## Section 2: Interfaces and Protocols

- BIOS programs `MSR_POWER_CTL.c1e_enable` (MSR 0x1FC bit[1]) during POST
- OS uses `HALT` instruction; hardware promotes to C1E transparently if autopromotion is on
- `cpuid.06h:ecx.bit(0)` = 1 indicates C1E autopromotion support

## Section 3: Reset, Power, and Clocking

- `MSR_POWER_CTL` is preserved across C6 exits
- FIVR voltage is reduced to C1E voltage during C1E dwell
- C1E exit is faster than C6 (<10 μs) due to pre-programmed FIVR ramp rates

## Section 4: Programming Model

```python
# Verify C1E autopromotion BIOS knob propagated to MSR 0x1FC
s = sv.socket0

# Check all cores have consistent MSR_POWER_CTL value
for c in range(2):
    for k in range(48):
        pwr_ctl = s.getbypath(f"cbb{c}.compute0.module0.core{k}.msr.msr_power_ctl").read()
        c1e_bit = (pwr_ctl >> 1) & 1
        print(f"CBB{c} core{k} C1E_enable: {c1e_bit}")
```

## Section 5: Operational Behavior

### TC Coverage Map

| TC HSD | Title | Scope |
|--------|-------|-------|
| [22022423091](https://hsdes.intel.com/appstore/article-one/#/22022423091) | CState Fast C1E: bios_knob C1E autopromotion_silicon | — |


## Section 6: Corner Cases and Error Handling

- **Inconsistent MSR across cores**: All cores in socket should have identical `c1e_enable` state after BIOS programming
- **Knob disabled but HW still promotes**: SW bug in BIOS — verify PCode correctly propagates knob-off to MSR[1]=0
- **PSS interaction**: C1E should not interfere with P-state frequency selection — verify mperf/aperf ratio unchanged during C1E promotion

## Section 7: Security / Safety / Policy

- C1E voltage reduction must not cause register state corruption — validated by the Fast C1E start/end flow TCD

## Section 8: References

- [Core C-States HAS — C1E Section](https://docs.intel.com/documents/pm_doc/src/server/Wave3_common/Core_C_States/Core_C_States_HAS.html)
- Intel SDM Vol.3 — MSR_POWER_CTL (0x1FC)
- [TCD HSD 22022421276](https://hsdes.intel.com/appstore/article-one/#/22022421276)
