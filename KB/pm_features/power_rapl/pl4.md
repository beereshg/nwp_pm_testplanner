# Power/RAPL > PL4 (Power Limit 4)

> **Status**: Restructured — NWP delta enriched from MCP HAS/MAS query
> **Parent**: [Power / RAPL](power_rapl_main.md)

## Baseline (DMR)

PL4 is a **customer-programmable instantaneous power limit** that allows platform customers to cap maximum power without needing to understand IccMax fuse math or Vtrip threshold programming. PL4 sits as a software abstraction layer **on top of** the PMax hardware protection circuit.

## HW Touchpoints

<!-- TODO: Extract from Legacy content or enrich via MCP HAS query -->
| IP Block | Die | Role | Key Signals / Wires | HAS Reference |
|----------|-----|------|---------------------|---------------|
| | | | | |

## FW Touchpoints

<!-- TODO: Extract from Legacy content or enrich via MCP HAS query -->
| Agent | Location | Role | Key Functions / Handlers | Source |
|-------|----------|------|--------------------------|--------|
| | | | | |

## OS Interfaces

<!-- TODO: Extract from Legacy content or enrich via MCP HAS query -->
| Interface | ID / Address | Access | Description | Spec Reference |
|-----------|-------------|--------|-------------|----------------|
| | | | | |

## NWP Delta

**PL4 (IccMax / Power Limit 4) is supported on NWP** — reused from DMR.

- VR current limit enforcement mechanism is reused
- Register interface unchanged
- IccMax management moved from ACP/Acode to Punit/Pcode (Atom E-core has no ACP)
- FIVR LIMC throttling interface and UAT supported on Atom

### Validation Impact
- Same PL4 test cases apply
- Verify Punit/Pcode IccMax enforcement (not ACP/Acode)

## Legacy (Human-Curated Reference)

### Architecture Summary

PL4 is a **customer-programmable instantaneous power limit** that allows platform customers to cap maximum power without needing to understand IccMax fuse math or Vtrip threshold programming. PL4 sits as a software abstraction layer **on top of** the PMax hardware protection circuit.

#### PL4 vs PMax — Key Distinction

| | **PMax (MT-PMax)** | **PL4** |
|---|---|---|
| **What it is** | Hardware overcurrent protection circuit in FIVR | Customer-programmable instantaneous power limit (software interface) |
| **Set by** | Fuses at manufacturing (Vtrip thresholds) | Customer at runtime via TPMI `Power_Limit_Control4` (idx 5) |
| **Operates on** | Voltage — analog comparator senses voltage drop across loadline | Power (watts) — firmware converts PL4 watts → current (Itrip) → voltage offset (Voffset) |
| **Reaction time** | ~500ns (hardware-speed analog comparator) | Same ~500ns once programmed — PL4 modifies PMax thresholds, then PMax hardware enforces |
| **Thresholds** | 4 levels: Vtrip0 (hard), Vtrip1 (soft L1), Vtrip2 (soft L2), FDD | Single power limit that shifts all PMax Vtrip levels via offset |
| **Purpose** | Protect silicon from overcurrent damage | Let customers cap instantaneous power without IccMax/Vtrip fuse math |
| **Relationship** | The underlying enforcement mechanism | The software knob that moves PMax trip points |

**In short: PMax = the hardware guard rail. PL4 = the software knob that moves it.**

#### PL4 Mechanism

PL4 converts a power limit (watts) to a current limit (Itrip), then to a voltage offset that shifts the PMax detector trip points higher (i.e., trigger earlier at lower current):

$$P_{Vccin} = PL4 - P_{nonVccin}$$

$$I_{trip,dynamic} = \frac{-V_{boot} + \sqrt{V_{boot}^2 + 4 \times R_{LL} \times P_{Vccin}}}{2 \times R_{LL}}$$

$$V_{offset,PL4} = (IccMaxApp_{fused} - I_{cc,trip}) \times R_{LL}$$

Where $I_{cc,trip} = \min(I_{trip,dynamic}, IccMaxApp_{fused})$

#### Vtrip Reprogramming with MT-PMax Scaling

Once `Voffset_PL4` is computed, PCode (CBB leaf) combines it with any TPMI-programmed offset and applies MT-PMax scaling factors:

$$V_{offset0} = V_{offset,PL4} + V_{offset,TPMI}$$
$$V_{offset1} = V_{offset0} \times (1 - SF1/100)$$
$$V_{offset2} = V_{offset0} \times (1 - SF2/100)$$

DAC encoding (2mV resolution): $V_{Encoding} = V_{offset} / 0.002$, max encoded value `0x3F`

#### Voffset_Rll Guardband

PCode adds a loadline resistance guardband:

$$V_{offset,Rll} = |R_{LL,fused} - R_{LL,Vccin}| \times IccMaxApp_{fused}$$

#### Psafe on PL4 Update

Psafe frequency is **fixed per SKU** — not impacted by PL4 changes. PL4 frequency is derived from the P-F curve, clipped to range [Pm, P0].

---

### Execution Flow

#### PL4 Programming Flow (end-to-end)

```
Customer writes TPMI Power_Limit_Control4 (idx 5) with PL4 watts
         │
         ▼
┌─────────────────────────────────────────────────┐
│  PrimeCode Root (iMH)                           │
│  1. Read PL4 from TPMI register                 │
│  2. Compute I_trip_dynamic (quadratic equation)  │
│  3. Compute Voffset_PL4 = (IccMaxApp - Itrip)×Rll│
│  4. Send HPM PL4_CONFIG to each leaf CBB punit  │
│     (V_OFFSET in bytes 12-13 of HPM message)    │
└─────────────────────┬───────────────────────────┘
                      │ HPM PL4_CONFIG
                      ▼
┌─────────────────────────────────────────────────┐
│  PCode Leaf (CBB)                               │
│  5. Receive PL4_CONFIG, extract V_OFFSET        │
│  6. Add TPMI offset → Voffset0_pcode            │
│  7. Scale SF1 → Voffset1; Scale SF2 → Voffset2  │
│  8. DAC-encode all offsets (÷ 0.002, max 0x3F)  │
│  9. Write PMAX_CONFIG1 register                 │
│ 10. Compute freq ceilings per domain            │
│     (SSE/AVX2/AVX3/TMUL/Fabric)                 │
│ 11. Send HPM PMAX_SOFT/HARD_INST_PWR freq limit │
│ 12. Send PL4 Ack HPM back to root               │
└─────────────────────────────────────────────────┘
```

#### Step-by-step Detail

1. **Customer writes TPMI**: `Power_Limit_Control4` (idx 5) — `PWR_LIM[17:0]` in 1/8W units, `PWR_LIM_EN[62]`, `Lock[63]`
2. **Root firmware reads PL4**: PrimeCode on iMH detects TPMI change
3. **Compute I_trip**: Uses quadratic formula with Vboot, Rll, P_Vccin (after subtracting non-Vccin power)
4. **Compute Voffset**: `(IccMaxApp_fused - min(I_trip, IccMaxApp_fused)) × Rll`
5. **Send HPM PL4_CONFIG**: PM2IP message with V_OFFSET field (bytes 12-13) to each leaf CBB punit
6. **Leaf receives PL4_CONFIG**: PMax owner CBB punit processes the offset
7. **Add TPMI offset**: `Voffset0 = Voffset_PL4 + Voffset_TPMI`
8. **Scale for soft thresholds**: `Voffset1 = Voffset0 × (1 - SF1/100)`, `Voffset2 = Voffset0 × (1 - SF2/100)`
9. **DAC encode & write HW**: Divide by 0.002V (PMAX_DAC_RESOLUTION), clamp to 0x3F, write `PMAX_CONFIG1`
10. **Frequency ceilings**: Compute per-domain ceilings (SSE, AVX2, AVX3, TMUL, Fabric) from P-F curve
11. **Send freq ceiling HPMs**: `PMAX_SOFT_INST_PWR_CONTROLLED_FREQ_LIMIT` and `PMAX_HARD_INST_PWR_CONTROLLED_FREQ_LIMIT` to each CBB
12. **Ack**: Leaf sends `IP2PM PL4 Ack` (with VPD bit) back to root

---

### Key Registers & Interfaces

#### TPMI Interface (customer-facing)

| Register | Index | Key Fields | Notes |
|----------|-------|------------|-------|
| `Power_Limit_Control4` | idx 5 | `PWR_LIM[17:0]` (1/8W), `PWR_LIM_EN[62]`, `Lock[63]` | Primary PL4 programming interface |

> **MSR 0x601** (`MSR_VR_CURRENT_CONFIG`): Deprecated since GNR. TPMI is the POR interface.

#### PMax HW Registers (written by PCode)

| Register | Key Fields | Notes |
|----------|------------|-------|
| `PMAX_CONFIG1` | `VTRIP_THRESHOLD_OFFSET[0-2]` | DAC-encoded Voffset for hard/soft L1/soft L2 |
| `PMAX_CONTROL` | `PMAX_VTRIP_THRESHOLD_OFFSET` | Direct threshold offset control |

#### HPM Messages

| Message | Direction | Key Payload | Purpose |
|---------|-----------|-------------|---------|
| `PL4_CONFIG` | Root → Leaf | `V_OFFSET` (bytes 12-13) | Carry computed Voffset to leaf PMax owner |
| `PL4 Ack` | Leaf → Root | `VPD` bit | Confirm PL4 applied |
| `PMAX_SOFT_INST_PWR_CONTROLLED_FREQ_LIMIT` | Leaf → CBBs | SSE/AVX2/AVX3/TMUL/Fabric freq ceilings | Soft throttle frequency limits |
| `PMAX_HARD_INST_PWR_CONTROLLED_FREQ_LIMIT` | Leaf → CBBs | SSE/AVX2/AVX3/TMUL/Fabric freq ceilings | Hard throttle frequency limits |

#### PECI Interface

| Command | Description |
|---------|-------------|
| PECI-PCS Command 60 | PL4 read/write (18-bit power value) |

#### Observability

| Signal/Counter | Purpose |
|----------------|---------|
| `FINE_LEVEL_CLIP_CAUSE_INDEX_PLATFORM_PL4` | Bit 18 in clip cause — indicates PL4 is active limiter |
| PL4 cycle counters | Count cycles under PL4 enforcement |
| PROCHOT counters | Count PMax-triggered PROCHOT assertions |

---

### Key Fuses

| Fuse | Format | Purpose |
|------|--------|---------|
| `NON_VCCIN_POWER` | U10.3 | Non-Vccin power subtracted from PL4 to get P_Vccin |
| `PKG_ICC_MAX` | U10.0 | Package max current (absolute limit) |
| `PKG_ICC_MAX_APP` | U10.0 | Max current for realistic applications (PMax baseline) |
| `PMAX_SCALING_FACTOR_VTRIP1` | U7.0 | SF1 percentage for soft L1 threshold scaling |
| `PMAX_SCALING_FACTOR_VTRIP2` | U7.0 | SF2 percentage for soft L2 threshold scaling |
| `LOADLINE_RES` | — | Loadline resistance for Voffset computation |

---

### Collateral Links

| Type | Link | Notes |
|------|------|-------|
| HAS (GNR) | [GNR PL4 HAS](https://docs.intel.com/documents/pm_doc/src/server/GNR/Features/PL4/pl4.html) | Primary spec — PL4 mechanism, equations, flow |
| HAS (MT PMax) | See [pmax.md](pmax.md) | PMax hardware that PL4 modifies |
| HSD | 22011615872 | PL4 original HSD |
| HSD | 14016333374 | PL4 change 1 |
| HSD | 22015042858 | PL4 change 2 |
| Primecode src | `src/flow/rapl/` | PL4 power→Itrip→Voffset computation (root) |
| PCode src | CBB PMax owner | Voffset scaling, DAC encoding, PMAX_CONFIG1 write |

---

### Feature Interactions

| Feature | Interaction |
|---------|-------------|
| **PkgC6** | No impact during C6 — PL4 evaluated on C6 exit |
| **Reset/ADR** | No impact on PL4 |
| **Core C6/GV** | PL4 works alongside — independent mechanisms |
| **PMax** | PL4 modifies PMax trip points; PMax hardware enforces |

---

#### Validation Approach (from HAS)
- CTE validation with PL4 set at **40%, 60%, 80%, 100%** of Pmaxapp
- Verify Vtrip0/Vtrip1/Vtrip2 values match expected offsets at each PL4 level
- Confirm frequency ceilings applied correctly per domain

---

### Related Sightings
<!-- No NWP PL4 sightings identified yet — populate as they arise -->

---

### NWP Delta

> **Items to verify for NWP** (not yet confirmed — check NWP HAS when available):

| Area | Question | GNR/DMR Baseline |
|------|----------|------------------|
| Dual VCCIN | Does NWP have dual VCCIN like DMR-AP? PL4 scale factors per iMH? | DMR: per-iMH PL4_SCALE_FACTOR fuses |
| Per-iMH partition | Are fuses (IccMaxApp, SF1, SF2, Rll) per-iMH in NWP? | DMR: yes, per-iMH |
| HPM message format | Any changes to PL4_CONFIG or freq ceiling HPM layout? | GNR/DMR: V_OFFSET in bytes 12-13 |
| TPMI interface | Same Power_Limit_Control4 idx 5 layout? | GNR: PWR_LIM[17:0], EN[62], Lock[63] |
| PECI-PCS Cmd 60 | Still supported for PL4? | GNR: 18-bit PL4 via PCS Cmd 60 |
| DAC resolution | Still 2mV/code, max 0x3F? | GNR/DMR: PMAX_DAC_RESOLUTION = 0.002 V/code |
| Non-Vccin power | New power domains or different fuse format? | GNR: U10.3 NON_VCCIN_POWER |
