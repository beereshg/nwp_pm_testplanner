# HSD 15019330360: [DMR][Seamless][OSPL][regression] MCA from pcode 0010410 when upgrade pcode from 22.1.31.0 to 22.1.32.0 version

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [15019330360](https://hsdes.intel.com/appstore/article-one/#/15019330360) |
| **Status** | complete.validated |
| **Priority** | 2-high |
| **Owner** | lijianzh |
| **Component** | fw.pcode |
| **Defect Die** | base |
| **Conclusion** | fw.bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **FW_PCODE** | 70% |
| **Feature** | Core C-States | 52% |
| **Sub-Feature** | C1 | — |

**Reasoning**: tag contains FIX_PATCH → FW_PCODE

## Root Cause Summary

Observation: 

[ 1255.511617] microcode: configs: loading=true, staging=true, anyrev=false

[ 1265.991193] microcode: 
Staging of patch revision 0x8000099f succeeded.

[
Mca]IERR detected, set CBB and Package error bits

[Mca]CheckMcBankErrorStatus returns TRUE

[Mca]McaDetectAndHandle start

[Mca]McaDetectAndHandle, state is 0x0

[Mca]McaDetectAndHandle, state is 0x1

[Mca]ProcessSocketMcBankError: Inside the function

S0 D0 T0 M1 C0 T0 [Mca]McBankErrorHandler: Skt = 0x0, McBank = 0x4, State = 

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww18.1]

Firmware Version Incompatibility

Lijian and Orna confirmed that the current and previous firmware versions are not backward compatible, which could impact customers if released. The incompatibility is due to changes in variable layout and address mapping between revisions.

FXT Team Engagement: Matthew emphasized the need for a firmware IP owner to engage with the FXT (Firmware Execution Team) to drive a consistent answer and milestone for all IPs regarding backward compatibility, and volunteered to start an email thread to initiate this coordination.

The group agreed that FW IP owners should not wait indefinitely for guidance and must proactively seek answers from FXT. Orna offered to provide a special revision for testing if needed, but preferred to limit such changes until absolutely necessary.

We need a pCode bug to document this incompatibility, which can then be resolved or rejected as appropriate, ensuring that the issue is tracked and addressed in the program's process.

### Description
Observation: 

[ 1255.511617] microcode: configs: loading=true, staging=true, anyrev=false

[ 1265.991193] microcode: 
Staging of patch revision 0x8000099f succeeded.

[
Mca]IERR detected, set CBB and Package error bits

[Mca]CheckMcBankErrorStatus returns TRUE

[Mca]McaDetectAndHandle start

[Mca]McaDetectAndHandle, state is 0x0

[Mca]McaDetectAndHandle, state is 0x1

[Mca]ProcessSocketMcBankError: Inside the function

S0 D0 T0 M1 C0 T0 [Mca]McBankErrorHandler: Skt = 0x0, McBank = 0x4, State = 0x1

S0 D0 T0 M1 C0 T0 [Mca]McBankErrorHandler: Skt = 0x0, McBank = 0x4, State = 0x2

S0 D0 T0 M1 C0 T0 [CpuRas]MC status 0xBE00000000010410, class FATAL

S0 D0 T0 M1 C0 T0 [Mca]McBankErrorHandler: Skt = 0x0, McBank = 0x4, State = 0x4

CreateProcessorErrorRecord addr is 0x:600BD059

Final ErrSts->EmcaProcErrorSection.ProcessorGenericErrorData.ValidFields is 0x:34F

S0 D1 T0 M0 C0 T0 [Mca]McBankErrorHandler: Skt = 0x0, McBank = 0x4, State = 0x1

S0 D1 T0 M0 C0 T0 [Mca]McBankErrorHandler: Skt = 0x0, McBank = 0x4, State = 0x2

S0 D1 T0 M0 C0 T0 [CpuRas]MC status 0xBE00000000010410, class FATAL

S0 D1 T0 M0 C0 T0 [Mca]McBankErrorHandler: Skt = 0x0, McBank = 0x4, State = 0x4

CreateProcessorErrorRecord addr is 0x:600BD059

Final ErrSts->EmcaProcErrorSection.ProcessorGenericErrorData.ValidFields is 0x:34F

S0 D2 T0 M5 C1 T0 [Mca]McBankErrorHandler: Skt = 0x0, McBank = 0x4, State = 0x1

S0 D2 T0 M5 C1 T0 [Mca]McBankErrorHandler: Skt = 0x0, McBank = 0x4, State = 0x2

S0 D2 T0 M5 C1 T0 [CpuRas]MC status 0xBE00000000010410, class FATAL

S0 D2 T0 M5 C1 T0 [Mca]McBankErrorHandler: Skt = 0x0, McBank = 0x4, State = 0x4

CreateProcessorErrorRecord addr is 0x:600BD059

Final ErrSts->EmcaProcErrorSection.ProcessorGenericErrorData.ValidFields is 0x:34F

ERROR: C00000002:V03071008 I0 1DAE3520-E041-423D-9662-2B8F53D68390 BFFA9A10

WHEA: Detected Processor Error

WHEA: Ignore Processor WHEA error now.

S0 D1 T0 M0 C0 T0 [Mca]McBankErrorHandler: Skt = 0x0, McBank = 0xB, State = 0x1

S0 D1 T0 M0 C0

### Comments (latest)
++++1566963585 lijianzh
<div data-ai-assist-notice="hsdes-ai-generated" style="border-left:3px solid #0071C5;background:#EEF5FC;padding:7px 14px;margin-bottom:16px;font-family:'Segoe UI',Arial,sans-serif;font-size:12px;color:#374151;line-height:1.5;"><span style="color:#0071C5;font-weight:700;letter-spacing:0.05em;">⚠ AI-ASSISTED</span>&nbsp;&nbsp;This comment was prepared with AI help. Verify key details before acting.</div>
<h2>Analysis Update — Rev 4 (Corrections to Rev 3)</h2>
<p>Three corrections following reviewer feedback, all verified against pcode and S3M source trees.</p>
<hr />
<h3>Item 1 — MSCOD=0x0001: Deeper Decode of <code>uc_exception</code></h3>
<p><strong>Source confirmed</strong> in <code>~/work/pcode/source/pcode/kernel/xtensa.h</code> — the <code>handle_uc_exception()</code> handler:</p>
<pre><code class="language-cpp">asm(&quot;rsr.EPC1 %0&quot; : &quot;=a&quot; (epc));         // faulting instruction address
asm(&quot;rsr.EXCCAUSE %0&quot; : &quot;=a&quot; (exccause)); // Xtensa exception cause code
asm(&quot;rsr.EXCVADDR %0&quot; : &quot;=a&quot; (excvaddr)); // virtual offending address

error_handler.issue_mca(ErrorDesc(mca_code::uc_exception),
    /*Additional Info*/ exccause,   // ← EXCCAUSE goes into MISC[63:32]
    /*IO Header*/ 0, epc, exccause, excvaddr);
</code></pre>
<p>This is a <strong>Xtensa CPU hardware exception</strong> — not a software assert (rassert=2) or deliberate MCA (codes 0x04–0x16). The Xtensa core itself faulted. Possible causes registered by pcode:</p>
<table>
<thead>
<tr>
<th>EXCCAUSE</th>
<th>Exception Type</th>
</tr>
</thead>
<tbody>
<tr>
<td>EXCCAUSE_ILLEGAL</td>
<td>Illegal instruction</td>
</tr>
<tr>
<td>EXCCAUSE_LOAD_STORE_ERROR</td>
<td>Load/store bus error</td>
</tr>
<tr>
<td>EXCCAUSE_UNALIGNED</td>
<td>Unaligned load/store</td>
</tr>
<tr>
<td>EXCCAUSE_LOAD_PROHIBITED</td>
<td>Load from prohibited address</td>
</tr>
<tr>
<td>EXCCAUSE_STORE_PROHIBITED</td>
<td>Store to prohibited address</td>
</tr>
<tr>
<td>EXCCAUSE_LOAD_STORE_ADDR_ERROR</td>
<td>Load/store address error</td>
</tr>
<tr>
<td>EXCCAUSE_PRIVILEGED</td>
<td>Privileged instruction in user mode</td>
</tr>
</tbody>
</table>
<p><strong>Where EXCCAUSE goes:</strong>
- Pcode writes EXCCAUSE → <code>IO_FIRMWARE_MCA_MISC[63:32]</code> (ADDITIONAL_INFO), SOURCE_LOCATION → <code>IO_FIRMWARE_MCA_MISC[31:0]</code>
- <strong>BUT</strong> — <code>FIRMWARE_MCA_MISC_VALID = 0</code> in the captured MCA dump (confirmed from <code>io_firmware_mca_command = 0x30001</code> with bit 25=0)
- DMR RTL (<code>pmsrvr_ras.vs</code>): when <code>FIRMWARE_MCA_MISC_VALID=0</code>, the hardware RAS unit uses the <strong>legacy format</strong> (<code>PDebugPC_F000H</code>) for <code>mc_misc</code>, NOT the pcode MISC register values
- Therefore <code>mc_misc = 0x300000000</code> = hardware-generated legacy value — <strong>EXCCAUSE is NOT present in the captured mc_misc</strong></p>
<p><strong>What MCE ADDR = 0x600BD059 actually is:</strong>
- From <code>erro

### Tags
SysDebugDccbBypass,SysDebugCloned,FIX_PATCH_DMR_AP1_A0_600009A2,FIX_IFWI_DMR_AP1_2026.20.3.04

### Conclusion
fw.bug

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

- **Primary Feature**: Core C-States
- **Sub-Feature**: C1
- **Component Path**: fw.pcode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Key Registers

- `MSR 0x79`

## Timeline

- **Submitted**: 2026-04-26 15:03:48
- **Root Caused**: 2026-04-28 21:57:45
- **Closed**: 2026-05-19 20:16:30
- **Days Open**: 23

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
