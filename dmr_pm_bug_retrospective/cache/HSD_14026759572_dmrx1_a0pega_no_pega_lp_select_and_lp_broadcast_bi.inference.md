# HSD 14026759572: [DMR][X1 A0][PEGA] No PEGA LP_SELECT and LP_BROADCAST bit fields in Pcode implementation.

## Metadata

| Field | Value |
|-------|-------|
| **HSD ID** | [14026759572](https://hsdes.intel.com/appstore/article-one/#/14026759572) |
| **Status** | rejected.not_a_defect |
| **Priority** | 3-medium |
| **Owner** | egomezgo |
| **Component** | hw.power |
| **Defect Die** | compute |
| **Conclusion** | not_a_bug |

## Classification

| Dimension | Value | Confidence |
|-----------|-------|------------|
| **Root Cause Type** | **UNKNOWN** | 20% |
| **Feature** | Core C-States | 80% |
| **Sub-Feature** | C6 | — |

**Reasoning**: No strong indicators found

## Root Cause Summary

In PEGA HAS:

In PCODE repo doesnt seem to be implemented:

BIOS:  OKSDCRB1.86B.0030.D17.2512030720

Also populating different combinations in this fields doesn't seem to change much in a System:

Before: (Idle driver is disable)

Sending the follwoing command (Test 1: LP_SELECT on both cores):

C6 residency increases as expected:

Sending other combination using LP_BROADCAST (Test 2):

Not really a change. Test 3: Just 1 core:

No big difference.

## Raw HSD Text

<!-- This section provides raw HSD data for agent enrichment (Stage 3b). -->
<!-- The Copilot agent extracts root cause, fix description, code refs, and diagrams. -->

### Forum Notes
[26ww02.3]

Issue reported during a test with PEGA trying 

to wake up multiple cores simultaneously using 

multicast commands. PEGA HAS mention broadcast as a supported feature, but FV team realized that it is not implemented. Ido has agreed that this feature is needed to validate all cores wake up simultaneously for VCCin max stresssing. Currently Ido is working with Nati Abitan to support multicast and will share HSD when available

### Description
In PEGA HAS:

In PCODE repo doesnt seem to be implemented:

BIOS:  OKSDCRB1.86B.0030.D17.2512030720

Also populating different combinations in this fields doesn't seem to change much in a System:

Before: (Idle driver is disable)

Sending the follwoing command (Test 1: LP_SELECT on both cores):

C6 residency increases as expected:

Sending other combination using LP_BROADCAST (Test 2):

Not really a change. Test 3: Just 1 core:

No big difference.

### Comments (latest)
++++14614944525 egomezgo
Adding email thread:<br /><!--StartFragment--><div class="ubHDG gZ9KR THa4i pinIo" style="border: 0px; font-variant-numeric: inherit; font-variant-east-asian: inherit; font-variant-alternates: inherit; font-variant-position: inherit; font-variant-emoji: inherit; font-stretch: inherit; line-height: inherit; font-family: &quot;Segoe UI&quot;, &quot;Segoe UI Web (West European)&quot;, -apple-system, BlinkMacSystemFont, Roboto, &quot;Helvetica Neue&quot;, sans-serif; font-optical-sizing: inherit; font-size-adjust: inherit; font-kerning: inherit; font-feature-settings: inherit; font-variation-settings: inherit; font-language-override: inherit; margin: 8px 19px 8px 2px; padding: 0px; vertical-align: baseline; color: rgb(36, 36, 36); -webkit-box-flex: 0; -webkit-box-orient: horizontal; -webkit-box-direction: normal; -webkit-box-pack: justify; -webkit-box-align: center; align-items: center; box-shadow: rgba(0, 0, 0, 0.12) 0px 0px 2px 0px, rgba(0, 0, 0, 0.14) 0px 2px 4px 0px; display: flex; flex: 0 0 auto; flex-flow: row; justify-content: space-between; border-radius: 4px; min-height: 40px;"><div class="l9eF1 mJflQ allowTextSelection" role="heading" aria-level="2" style="border: 0px; font-style: inherit; font-variant: inherit; font-weight: 600; font-stretch: inherit; line-height: inherit; font-family: inherit; font-optical-sizing: inherit; font-size-adjust: inherit; font-kerning: inherit; font-feature-settings: inherit; font-variation-settings: inherit; font-language-override: inherit; margin: 0px; padding: 0px; vertical-align: middle; cursor: auto; user-select: text; display: inline; overflow: hidden; width: 1445.43px;"><div class="MshDW qmv6a" style="border: 0px; font: inherit; margin: 0px; padding: 6px 12px 6px 10px; vertical-align: baseline; color: inherit; border-radius: 4px; display: inline-block; overflow-wrap: anywhere; position: relative; white-space-collapse: preserve; width: 1445.43px; z-index: 4; min-height: 40px;"><div class="UUCdJ F0Tdc" style="border: 0px; font: inherit; margin: 0px; padding: 0px; vertical-align: middle; color: inherit; display: flex; min-height: 28px;"><div class="HlO3X" style="border: 0px; font: inherit; margin: 4px 0px; padding: 0px; vertical-align: baseline; color: inherit;"><span class="JdFsz" title="Re: PEGA questions" style="border: 0px; font: inherit; margin: 0px 8px 0px 0px; padding: 0px; vertical-align: baseline; color: inherit; display: inline;">Re: PEGA questions</span></div></div></div></div></div><div data-app-section="ItemContainer" tabindex="-1" class="Q8TCC yyYQP owaMailComposeEditorScrollContainer customScrollBar" data-is-scrollable="true" style="border: 0px; font-variant-numeric: inherit; font-variant-east-asian: inherit; font-variant-alternates: inherit; font-variant-position: inherit; font-variant-emoji: inherit; font-stretch: inherit; line-height: inherit; font-family: &quot;Segoe UI&quot;, &quot;Segoe UI Web (West European)&quot;, -apple-system, BlinkMacSystemFont, Roboto, &qu

### Tags
FV_PM,SysDebugCloned,SysDebugCloned,SysDebugCloned

### Conclusion
not_a_bug

### Component
hw.power

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
- **Sub-Feature**: C6
- **Component Path**: hw.power

## Firmware Touchpoints

- No firmware touchpoints detected in text fields

## Timeline

- **Submitted**: 2026-01-07 06:38:13
- **Root Caused**: 2026-03-03 00:17:58
- **Closed**: 2026-04-17 01:57:11
- **Days Open**: 99

## Lessons Learned

<!-- Add lessons learned after human review -->

---
*Generated by classify_sightings.py at 2026-05-28T06:39:38+00:00*
