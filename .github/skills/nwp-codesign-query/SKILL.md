---
name: nwp-codesign-query
description: >
  Generate copy-paste prompts for Intel Co-Design Chat to audit TCD/TC
  organization, coverage gaps, pass/fail bars, and tier mapping against
  spec ground truth (HAS/MAS, wikis, code). Use when the user says
  "ask co-design", "generate a prompt for co-design", "check this against
  spec", "coverage gap analysis", or wants an external spec-grounded
  review of the TCD/TC hierarchy. Also use to convert a Co-Design
  response pasted back into this session into concrete HSD/KB actions.
---

# NWP Co-Design Query Skill

Bridges two systems that don't see each other:
- **Local (this agent):** HSD hierarchy, KB cache, lint gates, coverage tables — structure, no spec ground truth
- **Co-Design Chat:** HAS/MAS, feature wikis, code repos — spec ground truth, no view of our TCD/TC organization

Every generated prompt therefore has three parts: (A) packed local context,
(B) the question, (C) a structured output contract so the answer can be
mechanically folded back into coverage tables.

---

## Step 1a — Pack feature context (per-feature)

Build a compact hierarchy snapshot for the feature in question from the KB
cache (not by pasting whole KB files):

```
Feature: PCT (Priority Core Turbo) | TPF 16030762939
TCDs and their TCs (title · one-line WHAT · pass/fail bar):
- [PV] TCD 22022420862 "PV BIOS Configuration": TCs 17717 (custom config),
  17718 (partition sweep 1..max).
  Bar: CLOS regs reflect HP/LP split; cpuinfo_max_freq aligns
       with HWP_CAP per core class (HP ≈ 4.4 GHz, LP ≈ 2.3 GHz).
- [PV] TCD 16031169217 "PV BIOS Disable": TC 17719 (count=0).
  Bar: cpuinfo_max_freq uniform across all cores (no HP/LP split);
       conventional single-bucket turbo behavior restored.
...
```

Rules:
- ≤40 lines of context. Titles + WHAT + **bar** only — no HTML, no logs.
- **Every TCD entry MUST include its pass/fail bar.** A snapshot without
  bars can only get structural answers back; bars are what enable T3-style
  bar validation to happen for free inside a T1 gap audit.
- Include tier prefixes ([PSS]/[PV]/[FV]) so tier-mapping questions work.
- Note known issues honestly (e.g. "3 duplicate Discovery TCDs pending
  cleanup") so Co-Design doesn't rediscover them as findings.
- State what is explicitly NOT covered (e.g. "no negative validation TCD")
  so Co-Design focuses on genuine gaps.
- Note previously identified gaps (e.g. "Phase C HP throttle is tracked
  as TC-TBD in TCD 22022420858 §6") to avoid duplicate findings.

---

## Step 1b — Silicon routing context (write-once, reuse)

This block is **platform truth, not feature truth**. Write it once and
reuse it verbatim across every feature's prompts — PCT, RAPL, C-states,
SST-TF, Fabric DVFS, etc. It does not change per-feature.

**Purpose:** Co-Design has 40+ spec resources spanning DMR, CWF, GNR, and
NWP. Without routing rules it will happily cite the wrong platform's HAS.
Each line below exists to prevent a specific wrong-HAS citation:

| Line | Prevents |
|------|----------|
| `IMH2 (NWP-specific)` | Citing DMR IMH1 HAS for IMH-side features |
| `CBB = PNC, DMR-SP CBB HAS applies` | Searching for a non-existent NWP CBB HAS |
| `unless NWP CBB delta HAS exists` | Missing a real NWP delta when one is published |
| `no SST-BF (ZBB)` | Flagging SST-BF gaps that don't apply to NWP |
| `max_partitions=4` | Citing GNR/DMR partition limits |
| `TPMI replaces MSR 0x610/0x638` | Citing deprecated MSR paths for RAPL PL1 |
| `HSLE XOS = cross-die required` | Claiming HSLE single-die covers cross-die bugs |

**Keep the delta list short and factual.** Each entry is there to prevent
one specific wrong citation — not to teach Co-Design about NWP.

### Block (paste into every prompt after the hierarchy snapshot)

```
Silicon context:
  Platform: NWP (Newport) — derivative of DMR (Diamond Rapids)
  IMH:  IMH2 (NWP-specific; differs from DMR IMH1)
          → Use NWP IMH2 HAS/MAS for any IMH-side content
  CBB:  Same PantherCove (PNC) core as DMR-SP
          → For CBB-level features (PCode, SST-TF, PCT, RAPL, P-state):
            DMR-SP CBB HAS applies unless a NWP CBB delta HAS exists
  PSS environments:
    VP        — Simics virtual platform (full boot, firmware validation)
    HSLE      — Single-die RTL (IMH2 alone OR CBB alone; NOT cross-die)
    HSLE XOS  — Both IMH2+CBB RTL; mandatory for cross-die (IMH↔CBB) bugs
  Key NWP delta from DMR: 96 cores (2 CBBs × 48), no SST-BF (ZBB),
  max_partitions=4 for PCT, TPMI replaces deprecated MSR 0x610/0x638.
```

**When to update this block:** Only when NWP silicon facts change (e.g. a
NWP CBB delta HAS is published, a new PSS environment is added, or a
previously-ZBB feature becomes POR). Feature-specific context goes in
Step 1a, not here.

---

## Step 2 — Pick the question template

### T1: Coverage gap audit (most common)

> Use when: reviewing a feature after initial TCD creation, before PSS/FV
> execution, or after Co-Design previously flagged gap categories informally.

```
I am a validation engineer working on NWP (Newport) PM test planning.
Below is our current TCD/TC organization for [FEATURE]. Please review
against the [FEATURE] HAS and MAS in your resources.

[PASTE HIERARCHY SNAPSHOT HERE]

Which spec-defined behaviors have no TC coverage at any tier? Consider:
- Negative/boundary validation (invalid config, out-of-range values)
- State transition coverage (enable → disable → re-enable)
- Ordered throttling completeness (Phase A/B/C, edge cases)
- Driver/tool robustness (wrong driver, missing capability flag)
- Topology corners (all-HP, all-LP, single-core partition)
- Error injection / recovery paths in spec

[PASTE OUTPUT CONTRACT]
```

### T2: Grouping / WHAT-boundary check

> Use when: a TCD title is vague, two TCDs seem to overlap, or after adding
> new scenarios and wondering whether they need their own TCD.

```
I am a validation engineer working on NWP PM test planning.
Our rule is: one TCD = one WHAT (one spec-level behavior to validate);
split into separate TCDs when the expected behavior and pass/fail bar diverge.

[PASTE HIERARCHY SNAPSHOT HERE]

For each TCD listed:
1. Which HAS/MAS clause(s) define the expected behavior it is testing?
2. Does the TCD club two or more spec-level behaviors that have different
   expected outcomes or different pass/fail criteria?
3. Is any spec clause tested by more than one TCD (overlap)?

[PASTE OUTPUT CONTRACT]
```

### T3: Bar validation

> Use when: a TCD's §5 bar was authored without citing a spec clause, or
> after a spec update and you want to check alignment.

```
I am a validation engineer working on NWP PM test planning.
For each pass/fail bar in the TCD list below, check against the
[FEATURE] HAS/MAS and tell me: is the threshold consistent with spec?

[PASTE HIERARCHY SNAPSHOT WITH BARS]

For each bar:
- Cite the HAS/MAS clause that defines the expected value or behavior.
- Flag if our bar is: (a) tighter than spec, (b) looser than spec,
  (c) not specified in spec (our choice), or (d) contradicts spec.

[PASTE OUTPUT CONTRACT]
```

### T4: Tier mapping check

> Use when: adding a new tier (e.g. PSS HSLE XOS), after a coverage matrix
> update, or validating the TPF §2 Validation-Tier Layer Claim table.

```
I am a validation engineer working on NWP PM test planning.
Our tier mapping is:
  PV  → OS/tool + policy layers (requires booted Ubuntu on NWP silicon)
  FV  → enforcement + HW layers (post-silicon NWP, PythonSV/namednodes)
  PSS → policy + FW pre-silicon:
        VP       = Simics (firmware logic, no RTL)
        HSLE     = single-die RTL (IMH2 alone OR CBB alone)
        HSLE XOS = IMH2+CBB RTL together (required for cross-die behavior)

NWP silicon context:
  NWP = DMR derivative; IMH2 (differs from DMR IMH1); CBB = same PNC
  core as DMR-SP. For CBB-level features (PCT, SST-TF, RAPL), DMR-SP
  CBB HAS applies unless a NWP CBB delta HAS exists.

[PASTE HIERARCHY SNAPSHOT WITH TIER PREFIXES]

For each spec behavior implied by the TCD titles:
- Is it being tested at the correct tier (the one that can uniquely detect
  a bug in that layer)?
- Is any behavior claimed by no tier?
- Is any behavior over-tested (same bug catchable at multiple tiers but
  only one adds unique value)?
- For PSS: is HSLE XOS required (cross-die IMH2↔CBB protocol) or is
  single-die HSLE sufficient?

[PASTE OUTPUT CONTRACT]
```

### T5: New-feature bootstrap (pre-TCD creation)

> Use when: starting a new feature and wanting spec-grounded TCD decomposition
> BEFORE creating anything in HSD. This is the highest-value use of Co-Design.

```
I am a validation engineer starting test planning for [FEATURE] on NWP.
I have not yet created any TCDs in HSD.

Silicon context:
  Platform: NWP (Newport) — derivative of DMR (Diamond Rapids)
  IMH: IMH2 (NWP-specific). CBB: same PantherCove (PNC) core as DMR-SP.
  For CBB-level features, DMR-SP CBB HAS applies unless a NWP delta exists.
  NWP key deltas from DMR: 96 cores (2×48), no SST-BF (ZBB).

Please read the [FEATURE] HAS/MAS in your resources and list the
validation-relevant behaviors, grouped by distinct WHAT. Each group
should become one TCD candidate. For each group provide:
- A one-sentence WHAT (what spec behavior is being validated)
- A spec-cited measurable pass criterion (the §5 bar)
- Which validation tier(s) can uniquely detect a bug in this behavior

Do not include behaviors that are NWP ZBB (Zero Bug Bounce) — we are only
planning test cases for behaviors that are POR on NWP.

[PASTE OUTPUT CONTRACT]
```

### T6: Feature lineage / generational history

> Use when: authoring a new TCD/TC and the feature's cross-generation history
> would sharpen the NWP-delta and disposition analysis (interface migrations,
> renamed features, scope changes across SOC generations).

**T6 overrides Step 1b.** Do NOT include the standard silicon routing
context (it narrows to NWP/DMR — exactly wrong for history). Replace it
with this scope directive:

```
SCOPE DIRECTIVE (lineage query — search wide):
- Do not restrict to NWP- or DMR-tagged sources. Search ALL collections
  available in this session — EMR, GNR, SPR, CWF, DMR, or earlier —
  because this feature may predate current project naming, and generic
  features may live in cross-project or untagged resources.
- Before searching: list known aliases and predecessor names for this
  feature (features are frequently renamed at interface migrations,
  e.g. MSR-era name vs TPMI-era name). Then search each alias per
  generation.
- Provenance is mandatory per row: name the collection/document each
  claim came from. If you have no direct source for a generation,
  write `no spec access` for that row — do not infer or interpolate
  from adjacent generations.
```

Prompt body:

```
I am a validation engineer working on NWP (Newport) PM test planning.
I am tracing the generational history of [FEATURE] to sharpen NWP-delta
and disposition analysis.

[PASTE SCOPE DIRECTIVE ABOVE — NOT Step 1b]

For feature [FEATURE] (and the aliases you identified): trace its
lineage across SOC generations up to NWP.
1. First generation where the feature (under any name) appeared.
2. Per-generation change table — interface changes (e.g. MSR→TPMI),
   register/field additions or removals, behavioral changes, scope
   changes (core counts, partition limits, per-module vs per-core).
3. Deprecations or replacements along the way, naming the replacing
   feature.
4. For each change: the validation impact — does it invalidate,
   modify, or leave intact a test written against the previous
   generation's interface?

Answer as a markdown table:
| Generation | Change (interface/behavior/scope) | Interface impact | Spec ref (doc + clause, verbatim) | Source collection | Validation impact (invalidates / adapt / unchanged) |
One row per change, oldest first. Generations with no direct source:
single row with `no spec access`. ≤3-line summary of the NWP-relevant
tail (last generation → NWP deltas) after the table. No other prose.
```

---

## Step 3 — Append the output contract (always, verbatim)

End every prompt with this block exactly as written:

```
Answer as a markdown table with these exact columns:
| Gap/Finding | Spec ref (HAS/MAS clause or section) | Current coverage (TC id or "none") | Missing tier | Risk (H/M/L) | Recommended action |

Where "Recommended action" must be one of:
  new TC [under TCD ID]
  new TCD [with suggested title]
  bar change [TCD ID §5]
  move TC [from TCD X to TCD Y]
  accepted gap [with reason]

No prose outside the table except a ≤3-line summary at the top.
Use our exact TC/TCD IDs (e.g. TCD 22022420862, TC 17717) when referring
to existing artifacts — do not paraphrase them.
```

**Why the spec-ref column is mandatory:** It is the one thing Co-Design can
provide that the local agent cannot. On ingest it becomes the FR/clause
linkage in TCD §2, satisfying Phoenix compliance requirements.

---

## Step 4 — Ingest the response (when pasted back)

When the user pastes a Co-Design table into this session:

**Parse and route each row's "Recommended action":**

| Action type | Local operation |
|---|---|
| `new TC [under TCD X]` | Add Gap row to TCD X's §6 corner-cases coverage table as `*(TC TBD)*` |
| `new TCD [title]` | Run WHAT-boundary check (T2) first; if it passes, scaffold via `nwp-tcd-description` |
| `bar change [TCD X §5]` | Update TCD X §5 bar text + regenerate preview; bar-sync lint flags child TCs |
| `move TC [from X to Y]` | Parent link update via HSD (verify M:N handling); update both TCD KB coverage maps |
| `accepted gap [reason]` | Add to TPF §5 Accepted Coverage Limitations table with spec ref as rationale |

**T6 lineage ingest rules:**
- The full lineage table lands in the **KB feature article** (its
  canonical home) — never dumped into a TCD.
- Only the NWP-relevant tail flows into HSD artifacts: 1–2 sentences of
  "introduced in {gen}; NWP-relevant deltas: {list}" into **TCD §1**,
  and interface-migration facts into **TC Section A** (NWP Delta).
- The Validation-impact column feeds the disposition tree mechanically:
  `invalidates` → Needs_Adaptation (or Skip if ZBB'd), `adapt` →
  Needs_Adaptation, `unchanged` → candidate Runnable_As-Is /
  Runnable_On_N-1.
- Rows marked `no spec access` are recorded as-is in the KB article —
  they are honest gaps, not findings to fill by inference.
- Same push gate as all templates: nothing lineage-derived writes to
  HSD without confirmation.

**Hard rules on ingest:**
1. **Never auto-push from a Co-Design finding.** Findings enter as Gap/TBD rows first. Human confirms before any HSD write (same confirmation gate as all pushes).
2. **Copy the spec ref (clause ID) into TCD §2** — this is how FR linkage gets populated. Do not discard it.
3. **Co-Design is authoritative for spec; local rules stay authoritative for structure.** If Co-Design suggests a TCD decomposition that violates the WHAT-boundary rule, flag the conflict and resolve locally.

---

## Live example: PCT T1 prompt (ready to paste)

```
I am a validation engineer working on NWP (Newport) PM test planning.
Below is our current TCD/TC organization for PCT (Priority Core Turbo).
Please review against the PCT HAS and MAS in your resources.

Silicon context:
  Platform: NWP (Newport) — derivative of DMR (Diamond Rapids)
  IMH:  IMH2 (NWP-specific; use NWP IMH2 HAS for IMH-side content)
  CBB:  same PantherCove (PNC) core as DMR-SP
          → For PCT / SST-TF / RAPL (CBB PCode features): DMR-SP CBB HAS
            applies unless a NWP CBB delta HAS exists
  PSS environments: VP (Simics), HSLE (single-die), HSLE XOS (IMH2+CBB)
  Key NWP delta: 96 cores (2×48), no SST-BF (ZBB), max_partitions=4,
  TPMI replaces deprecated MSR 0x610/0x638 for RAPL PL1.

Feature: PCT (Priority Core Turbo) | TPF 16030762939
TCDs and their TCs (title + one-line WHAT + bar):
- [PV] TCD 22022420862 "PV BIOS Configuration": TCs 17717 (custom config),
  17718 (partition sweep 1..max). Bar: CLOS regs reflect HP/LP split;
  cpuinfo_max_freq aligns with HWP_CAP per core type.
- [PV] TCD 16031169217 "PV BIOS Disable": TC 17719. Bar: cpuinfo_max_freq
  uniform (no HP/LP split), conventional turbo behavior.
- [PV] TCD 16031169214 "PV Discovery": TC 17720. Bar: intel-speed-select
  reports correct HP module count and APIC IDs.
- [FV] TCD 22022420858 "Functionality": 17 TCs. Bar: ordered throttle
  (LP reduced first via SST_CP_PRIORITY_TYPE=1), CLOS register programming
  correct (SST_CLOS_CONFIG[0/3] matches HP/LP TRL).
- [PSS] TCD 22022420855 "Enabling & Discovery": 2 TCs. Bar: feature present
  in TPMI SST_TF_INFO_* after PrimeCode Phase 5, fuse-gated correctly.
NOTE: No negative validation TCD exists (invalid partition count, conflicting
BIOS knobs). No state-transition TCD (enable → disable → re-enable).
NOTE: NWP has no SST-BF (ZBB). PCT and SST-TF are distinct features.

Which spec-defined behaviors have no TC coverage at any tier? Consider:
- Negative/boundary validation (invalid config, out-of-range values)
- State transition coverage (enable → disable → re-enable)
- Ordered throttling completeness (Phase A/B/C edge cases, Phase C HP throttle)
- Driver/tool robustness (wrong driver, missing capability flag)
- Topology corners (all-HP, all-LP, single-core partition, max partitions)
- Error injection / recovery paths defined in the PCT HAS

Answer as a markdown table with these exact columns:
| Gap/Finding | Spec ref (HAS/MAS clause or section) | Current coverage (TC id or "none") | Missing tier | Risk (H/M/L) | Recommended action |

Where "Recommended action" must be one of:
  new TC [under TCD ID]
  new TCD [with suggested title]
  bar change [TCD ID §5]
  move TC [from TCD X to TCD Y]
  accepted gap [with reason]

No prose outside the table except a ≤3-line summary at the top.
Use our exact TC/TCD IDs (e.g. TCD 22022420862, TC 17717) when referring
to existing artifacts — do not paraphrase them.
```

---

## Pitfalls

| Pitfall | Fix |
|---|---|
| Pasting raw KB/HTML files as context | Snapshot format only, ≤40 lines |
| Asking open-ended "review this" | Always one template + output contract |
| Treating Co-Design output as authoritative for OUR structure | It's authoritative for SPEC; structure decisions stay under local rules (WHAT-boundary, bar ownership) |
| Findings pushed straight to HSD | Gap rows first, confirm, then push |
| Losing the spec refs | Copy clause IDs into TCD §2 on ingest — do not discard |
| Re-running T1 without noting what was already found | Add "NOTE: previously identified gaps G1–G5 are already tracked" to Step 1a context block |
| Snapshot without bars | Every TCD entry must include its pass/fail bar — bars enable T3-style bar validation inside a T1 gap audit for free |
| Editing the silicon context per-feature | Step 1b is platform truth, not feature truth — write once, reuse verbatim; feature-specific notes go in Step 1a |
| Running T6 with the standard silicon routing block | T6 replaces Step 1b with the wide-scope directive — routing context suppresses the history you're asking for |
| Accepting lineage rows without a Source-collection value | Provenance column is mandatory; a claim without a named doc may be cross-platform bleed-through |
| Pasting the full lineage table into TCD §1 | Table → KB article; TCD gets the ≤2-sentence NWP tail only |
