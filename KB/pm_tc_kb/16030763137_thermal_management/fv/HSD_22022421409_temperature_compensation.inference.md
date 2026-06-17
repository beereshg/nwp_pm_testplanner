# Deep Analysis: [DDRIO] Temperature Compensation

| Field | Value |
|-------|-------|
| **HSD ID** | 22022421409 |
| **Title** | [DDRIO] Temperature Compensation |
| **Date** | 2025-07-24 |
| **Target Program** | NWP (Newport) |
| **Source Program** | DMR (Diamond Rapids) |
| **Feature** | Memory Thermal Management |
| **Sub-Feature** | DDRIO Temperature Compensation — RC pulls DTS temp via PMSB → DDRIO Resource Adapter (~10ms rate) |
| **NWP Disposition** | **Runnable_On_N-1** |

---

## Section A: NWP Disposition & Justification

**Disposition: Runnable_On_N-1**

*Note: Template content was empty for this TC. The following is based on the feature description and general NWP architecture.*

DDRIO Temperature Compensation adjusts DDRIO timing parameters based on die temperature. The Resistance-Capacitance (RC) firmware reads die DTS temperature via PMSB and passes it to the DDRIO Resource Adapter approximately every 10ms for compensation.

---

## Section B: NWP-Specific Test Procedure

### NWP Architecture

| Component | DMR | NWP |
|-----------|-----|-----|
| DTS source | `sv.sockets.imhs.*` | `sv.socket0.imh0.*` |
| PMSB path | per-socket | single socket, imh0 |
| DDRIO Resource Adapter | per-IMH | `sv.socket0.imh0.*` DDRIO adapter |

### High-Level Test Steps

| Step | Action | NWP Details |
|------|--------|-------------|
| 1 | Verify DDRIO temp compensation enabled | Check RC/BIOS config |
| 2 | Read current DTS die temperature | `sv.socket0.imh0.punit.*` DTS registers |
| 3 | Monitor DDRIO Resource Adapter temp update | ~10ms polling via PMSB |
| 4 | Vary die temperature (PROCHOT/load) | Inject thermal load |
| 5 | Verify DDRIO adapter receives updated temperature | Compensation responds |
| 6 | Verify DDRIO timing adjusts | DDRIO calibrated to new temp |

### NWP Notes
- Single `imh0` Punit services PMSB → DDRIO resource adapter
- `sv.sockets.imhs.*` → `sv.socket0.imh0.*` for all DDRIO temp paths
- RC firmware polling rate ~10ms (same on NWP)

### Pass Criteria
- DTS temp reflected in DDRIO Resource Adapter within ~10ms
- DDRIO timing compensation tracks temperature changes
- No timing violations after temperature change

---

## Section F: Recommendation

**Recommendation: ADOPT — Template was empty; implement based on NWP DDRIO Resource Adapter and PMSB architecture; `sv.sockets.imhs.*` → `sv.socket0.imh0.*`**

**Priority**: Medium — `plc.feature.p1`; DDRIO temp compensation is required for signal integrity across operating temperature range
