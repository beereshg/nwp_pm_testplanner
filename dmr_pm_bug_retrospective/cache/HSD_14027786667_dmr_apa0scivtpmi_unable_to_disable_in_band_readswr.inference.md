# HSD 14027786667: [DMR AP][A0][SCIV][TPMI] Unable to disable In Band reads/writes via IB

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14027786667](https://hsdes.intel.com/appstore/article-one/#/14027786667) |
| **Status** | open.clone |
| **Priority** | 3-medium |
| **Owner** | psiebies |
| **Component** | fw.ocode |
| **Defect Die** | ioe |
| **Conclusion** |  |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | PState Stack | 75% |
| **Sub-Feature** | TRL | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Environment
:

Platform: JC_046

UP:  80000999

Configuration: X1

 

Steps to reproduce issue:

1. Disable TPMI Lock via setting the 
TPMI Control Interface LOCK knob
 to the 
Disabled 
value

2. Boot to the uefi shell

3. Send tpmi set_state command (0x11) with payload  = 0x31 
for each non bmc-only features (each tpmi feature id except 0xD, 0xE, 0xF)

4. Send tpmi get_sate command (0x10) 
for each non bmc-only features (each tpmi feature id except 0xD, 0xE, 0xF)

Expected behavior:

Value ret

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww21.3]

offline debugging is ongoing,

The issue is currently under architectural review. The specs clearly require BIOS to lock TPMI features before OS boot, but they also preserve post-lock opt-in/opt-out behavior. The open question is whether that post-lock behavior is intended for only 

HOSTIA_BOOT_SAI

 or for broader HOSTIA usage including post-boot OS flows. Until that is clarified, it is premature to conclude whether the reported behavior is a true oCode defect or a mismatch between implementation, test expectation, and spec wording.

﻿[26ww20.3]

Vidar is contacting oCode team to support the debugging

### Description
Environment
:

Platform: JC_046

UP:  80000999

Configuration: X1

 

Steps to reproduce issue:

1. Disable TPMI Lock via setting the 
TPMI Control Interface LOCK knob
 to the 
Disabled 
value

2. Boot to the uefi shell

3. Send tpmi set_state command (0x11) with payload  = 0x31 
for each non bmc-only features (each tpmi feature id except 0xD, 0xE, 0xF)

4. Send tpmi get_sate command (0x10) 
for each non bmc-only features (each tpmi feature id except 0xD, 0xE, 0xF)

Expected behavior:

Value returned in 4th step equals to 
payload | (feature_id << 0x8)

IB_WRITE_BLOCK[4:4] bit = 0x1

IB_READ_BLOCK[5:5] bit = 0x1

RAPL get_state output = 0x31

PEM get_state output = 0x131

UFS get_state output = 0x231

PMAX get_state output = 0x331

DRC get_state output = 0x431

SST get_state output = 0x531

MISC_CTRL get_state output = 0x631

RIT get_state output = 0x831

FHM get_state output = 0xA31

PLR get_state output = 0xC31

TPMI_INFO get_state output = 0x8131

CSR_ALL get_state output = 0xFD31

CSR_COMPUTE get_state output = 0xFE31

CSR_PKG_ROOT get_state output = 0xFF31

Current behavior:

RAPL get_state output = 0x1

PEM get_state output = 0x101

UFS get_state output = 0x201

PMAX get_state output = 0x301

DRC get_state output = 0x401

SST get_state output = 0x501

MISC_CTRL get_state output = 0x601

RIT get_state output = 0x801

FHM get_state output = 0xA01

PLR get_state output = 0xC01

TPMI_INFO get_state output = 0x8101

CSR_ALL get_state output = 0xFD01

CSR_COMPUTE get_state output = 0xFE01

CSR_PKG_ROOT get_state output = 0xFF01

### Comments (latest)
++++14615390764 jbrzezin
Issue observed with UP 8000099A

++++14615390762 psiebies
Automated Message: This record has been cloned. The preceding comments are originally from the parent record 18044342233.

++++14615390766 dmbuitra
[val_agent] Fields updated by val_agent:
  component: (empty) → hw.punit
  tag: val_agent added

Note: TPMI set_state not setting IB_WRITE_BLOCK/IB_READ_BLOCK bits — TPMI is a punit-owned power management interface.

++++14615390763 jbrzezin
Issue observed with UP 9000099D

++++14615390765 hmpicosm
<p>&nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Brzezinska, Justyna</span>&nbsp;, are you able to disable IB reads/write via OOB? Is that possible?</p><p><br /></p><p>Adding &nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Dominguez, Caesar</span>&nbsp;and &nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Gonzalez, Ignacio</span>&nbsp;as Ocode experts.</p><p><br /></p><p>According to Val Agent, this might be SAI related issue, where Ocode is silently dropping the Set_State request due to requestor's SAI. Caesar, Nacho, could you please comment on this?</p><p><br /></p><p>============================================================================</p><p><i>3. ⚠️ Critical SAI Constraint — Likely Root Cause</i></p><p><i>From OOBMSM_FW_Gen4_FAS.html &sect;3.22.1.1:</i></p><p><i><br /></i></p><p><i>*&quot;For in-band request only: Ocode shall verify the TPMI_SET_STATE requestor's SAI. Changing the TPMI configuration shall only be allowed for the HOSTIA_BOOT_SAI, according to the opt-in/opt-out direction. Otherwise change at any of these bits shall be ignored and request shall be accepted with 0x40 completion code.&quot;*</i></p><p><i><br /></i></p><p><i style="background-color: rgb(255, 255, 0);">This means: if the UEFI shell command is issued with a SAI other than HOSTIA_BOOT_SAI, Ocode silently accepts the command (returns 0x40 = success) but does not apply the IB_WRITE_BLOCK/IB_READ_BLOCK changes. The test would see no error code, yet the bits remain 0. This is a strong candidate for the root cause mechanism.</i></p><p><i><br /></i></p><p><i>Debug question for jbrzezin / Ocode team: Was the TPMI set_state issued from UEFI shell with the correct HOSTIA_BOOT_SAI? Is there a regression in the Ocode SAI validation path that incorrectly gates what should be a valid in-band BOOT_SAI request?</i></p><p><br /></p><p><br /></p>

++++14615390767 jbrzezin
&nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Picos Morgan, Hector M</span>&nbsp;opt-in/opt-out mechanism is IB only. OOB mechanism to disable IB read/writes uses allow list, that in short - allow to modify only BMC only features' ib_block bits

++++14615390768 hmpicosm
Adding &nbsp;<span style="font-weight: bold; color: #007BFF;" class="intel-user">@Esparza Soto, Jesus</span>&nbsp;to provide his inputs

++++14615390770 jeesparz
<p>Hi &nbsp;<span style="font-weight: bold; color: 

### Tags
val_agent,DMR_Manageability_VV

### Component
fw.ocode

## Root Cause Description

<!-- Populated by LLM enrichment stage (Stage 3b). -->

## Fix Description

<!-- Populated by LLM enrichment stage (Stage 3b). -->

## Source Code References

<!-- Populated by LLM enrichment stage (Stage 3b). -->

## Component Interaction: Root Cause

<!-- Populated by LLM enrichment stage (Stage 3b). -->

## Component Interaction: Fix

<!-- Populated by LLM enrichment stage (Stage 3b). -->

## Feature Mapping

- **Primary Feature**: PState Stack
- **Sub-Feature**: TRL
- **Component Path**: fw.ocode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `TPMI Lock`
- `TPMI Control`
- `TPMI features`
- `TPMI set_state`
- `TPMI is`
- `TPMI configuration`
- `TPMI HAS`
- `TPMI LOCK`
- `TPMI SET`
- `TPMI doc`

## Timeline

- **Submitted**: 2026-05-04 23:17:59
- **Days Open**: 17

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
