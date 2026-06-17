# HSD 14025967736: [X1 A0 PO][Patch23] CBB NCU Pcode Vars transaction is 64bit only (Punit PCUData opcode), provides no byte-mask for transactions (32bit only)

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14025967736](https://hsdes.intel.com/appstore/article-one/#/14025967736) |
| **Status** | rejected.merged |
| **Priority** | 3-medium |
| **Owner** | dstonecy |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | no_root_cause.rejected |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Unknown | 20% |
| **Sub-Feature** | general | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Summary:

========

NCU Pcode Vars transaction is 64bit only (Punit PCUData opcode), provides no byte-mask for transactions, docbug from previous programs (32bit only)

No documentation of the change was provided via HAS, byte-masking is not possible, introducing byte-mask hazards for adjacent register writes

Impact:

========

VP modeling of the transaction doesn't match spec, HW Scripts will need to deviate,

Write-1-clear semantics or writes above offsets would be impossible

Details:

=====

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Description
Summary:

========

NCU Pcode Vars transaction is 64bit only (Punit PCUData opcode), provides no byte-mask for transactions, docbug from previous programs (32bit only)

No documentation of the change was provided via HAS, byte-masking is not possible, introducing byte-mask hazards for adjacent register writes

Impact:

========

VP modeling of the transaction doesn't match spec, HW Scripts will need to deviate,

Write-1-clear semantics or writes above offsets would be impossible

Details:

========

In [78]: p23.punit_mem_exclusive(0x60000004)

Out[78]: 0x33333333
34A10B73

In [80]: p23.punit_mem_exclusive(0x60000000)

Out[80]: 0x
34A10B73
130A9EA1

### Comments (latest)
++++14614654993 senthil1
&nbsp;<span class="intel-user" style="font-weight: bold; color: rgb(0, 123, 255);">@Serebryanik, Alex</span>&nbsp;&nbsp;<span class="intel-user" style="font-weight: bold; color: rgb(0, 123, 255);">@Ben-Shimon, Tamir</span>&nbsp; &nbsp;any insights?<!--EndFragment-->

++++14614654994 btamir
<p>when using pcode mailbox directly I don't see issue, you can read 32b and you can read 64b<br />Are you sure you are using correct command</p><p><br /></p><p>In [43]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_data=0x60000000</p><p><br /></p><p>In [44]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.run_busy=1</p><p><br /></p><p>In [45]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.run_busy</p><p>Out[45]: 0x0</p><p><br /></p><p>In [46]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.command=0x5</p><p>command&nbsp; &nbsp;component</p><p>In [46]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.command=0x6</p><p><br /></p><p>In [47]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.run_busy=1</p><p><br /></p><p>In [48]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.run_busy</p><p>Out[48]: 0x0</p><p><br /></p><p>In [49]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_data</p><p>Out[49]: <span style="background-color: rgb(255, 255, 0);">0x130a9ea1</span></p><p><br /></p><p>In [50]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_data=0x60000000</p><p><br /></p><p>In [51]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.command=0x5</p><p><br /></p><p>In [52]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.run_busy=1</p><p><br /></p><p>In [53]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.command=0x9</p><p><br /></p><p>In [54]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.run_busy=1</p><p><br /></p><p>In [55]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.run_busy</p><p>Out[55]: 0x0</p><p><br /></p><p>In [56]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_data</p><p>Out[56]: <span style="background-color: rgb(255, 255, 0);">0x34a10b73130a9ea1</span></p><p><br /></p><p>In [57]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_data=0x60000004</p><p><br /></p><p>In [58]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.command=0x5</p><p><br /></p><p>In [59]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.run_busy=1</p><p><br /></p><p>In [60]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.command=0x9</p><p><br /></p><p>In [61]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.run_busy=1</p><p><br /></p><p>In [62]: sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_data</p><p>Out[62]: <span style="background-color: rgb(255, 255, 0);">0x3333333334a10b73</span></p><p><br /></p><p><br /></p><p><br /></p>

++++14614654995 dstonecy
<p>pcode mailbox isn't atomic, hence the mailbox instruction leaf. the mailbox instruction is 64 bit only</p><p><br /></p>

++++14614654996 dstonecy
<p>the lack of documentation from ucode reflects a common thread in not documenting how t

### Conclusion
no_root_cause.rejected

### Component
fw.pcode

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

- **Primary Feature**: Unknown
- **Sub-Feature**: general
- **Component Path**: fw.pcode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_data`
- `sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.run_busy`
- `sv.socket0.cbb0.pcudata.ucode_pcode_mailbox_interface.command`

## Timeline

- **Submitted**: 2025-09-25 02:31:04
- **Closed**: 2025-09-26 20:07:16
- **Days Open**: 1

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
