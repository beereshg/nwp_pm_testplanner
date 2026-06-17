# HSD 16030307483: [DMR_PMSS][X4][UFS]Uncore frequency(IMH_IO) toggles between 800 and 400 when MIO not populated when the system is IDLE.

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [16030307483](https://hsdes.intel.com/appstore/article-one/#/16030307483) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | sagrawa3 |
| **Component** | fw.primecode |
| **Defect Die** | ioe |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Fabric DVFS | 52% |
| **Sub-Feature** | Uncore Freq | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

Problem Statement:

- On an x4 system with MIO not populated(no cards on IMH1), the uncore IMH IO toggles between 800 and 400, when the system is Idle.

-  A different behaviour is seen on x1 system where the frequency gets stuck at 400 even after running the workload.

Issue reproducible on: 8000099900000000

x4 system:

X1 system:

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
﻿[26ww18.1]

Sagar and Shubham will meet to discuss the data collected from the test today

﻿[26ww17.1]

Shubham explained that after disabling PkgC, the issue persisted, and Sagar had provided some responses. Shubham planned to conduct a live debug session with Sagar to determine if the behavior is expected. Shubham described the observed toggling of uncore frequency and questioned whether this was expected, referencing previous discussions with Sagar. 
Sagar advised that before proceeding with further debugging, the team should clarify the expected behavior with architects Jay and Tim to ensure alignment on test outcomes.

﻿[26ww16.4]

pending on the test result from 

Shubham

.

### Description
Problem Statement:

- On an x4 system with MIO not populated(no cards on IMH1), the uncore IMH IO toggles between 800 and 400, when the system is Idle.

-  A different behaviour is seen on x1 system where the frequency gets stuck at 400 even after running the workload.

Issue reproducible on: 8000099900000000

x4 system:

X1 system:

### Comments (latest)
++++1667428356 sagrawa3
<p>Summary:</p><p style="font-size: 14px;">- On an x4 system with MIO not populated(no cards on IMH1), the uncore frequency toggles between 800 and 400, when the system is Idle.</p><p style="font-size: 14px;">-&nbsp; A different behaviour is seen on x1 system where the frequency gets stuck at 400 even after running the workload.</p><p><br /></p><p><br /></p><p>Added the PCU data for both x1 and X4 system(in attachment).</p><p><br /></p><p><br /></p><p>---------------------------------------------------------------------------------------------------------------------------------------------------</p><p>--------&gt; ltssm.sls()</p><p>=============================================</p><p>SOCKET0</p><p>=============================================</p><p>&nbsp; &nbsp; &nbsp; &nbsp; P0 P1 P2 P3 P4 P5 P6 P7</p><p>PXP0 is x1 x1 x1 x1</p><p>PXP1 is x16 -- -- -- -- -- -- --</p><p>PXP3 is x16 -- -- -- -- -- -- --</p><p>PXP4 is x16 -- -- -- -- -- -- --</p><p>PXP8 is x4 -- -- --</p><p>PXP9 is x16 -- -- -- -- -- -- --</p><p>PXP11 is x16 -- -- -- -- -- -- --</p><p>PXP12 is x16 -- -- -- -- -- -- --</p><p>Port pxp0.port0 (PCIE-NFM) is x1 (ilw=x1) (GEN2/-6.0dB) (Rvrsd: 0) LTSSM = UP_L0</p><p>Port pxp0.port1 (PCIE-NFM) is x1 (ilw=x1) (GEN2/-6.0dB) (Rvrsd: 0) LTSSM = UPL1_L1p0</p><p>Port pxp0.port2 (PCIE-NFM) is x1 (ilw=x1) (GEN1/-3.5dB) (Rvrsd: 0) LTSSM = UPL1_L1p0</p><p>Port pxp0.port3 (PCIE-NFM) is x1 (ilw=x1) (GEN4/dP0x7/uP0x6) (Rvrsd: 0) LTSSM = UP_L0</p><p>Port pxp1.port0 (PCIE-NFM) is x-- (ilw=x--) (GEN1/-3.5dB) (Rvrsd: 0) LTSSM = DET_QUIET</p><p>Port pxp3.port0 (PCIE-NFM) is x16 (ilw=x16) (GEN4/dP0x7/uP0x6) (Rvrsd: 0) LTSSM = UP_L0</p><p>Port pxp4.port0 (PCIE-NFM) is x-- (ilw=x--) (GEN1/-3.5dB) (Rvrsd: 0) LTSSM = DET_SLEEP</p><p><span style="background-color: rgb(255, 255, 0);">Port pxp8.port0 (PCIE-NFM) is x-- (ilw=x--) (GEN1/-3.5dB) (Rvrsd: 0) LTSSM = DET_SLEEP</span></p><p><span style="background-color: rgb(255, 255, 0);">Port pxp9.port0 (PCIE-NFM) is x-- (ilw=x--) (GEN1/-3.5dB) (Rvrsd: 0) LTSSM = DET_SLEEP</span></p><p><span style="background-color: rgb(255, 255, 0);">Port pxp11.port0 (PCIE-NFM) is x-- (ilw=x--) (GEN1/-3.5dB) (Rvrsd: 0) LTSSM = DET_SLEEP</span></p><p><span style="background-color: rgb(255, 255, 0);">Port pxp12.port0 (PCIE-NFM) is x-- (ilw=x--) (GEN1/-3.5dB) (Rvrsd: 0) LTSSM = DET_SLEEP</span></p><p>----------------------------------------------------------------------------------------------------------------------------------------------------------</p><p><br /></p>

++++1667428357 bg3
<p>AI Insight:</p><p><br /></p><p style="margin:0in;font-family:&quot;Segoe UI&quot;;font-size:12.0pt"><span style="font-weight:bold">Data Summary</span></p><div style="direction:ltr">

<table border="1" cellpadding="0" cellspacing="0" valign="top" style="direction: ltr; border-color: rgb(163, 163, 163); border-width: 1pt;" title="" summary="">
 <tbody><tr>
  <td style="border-color: rgb(163, 163, 163); border-width: 1pt; background

### Conclusion
not_a_bug

### Component
fw.primecode

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

- **Primary Feature**: Fabric DVFS
- **Sub-Feature**: Uncore Freq
- **Component Path**: fw.primecode

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2026-04-13 23:47:45
- **Closed**: 2026-05-02 00:34:21
- **Days Open**: 18

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
