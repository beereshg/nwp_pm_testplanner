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
- **Gist rule:** Derive each TCD's one-line WHAT from the **scope
  description's first paragraph**, never the title. Titles are
  placeholders ("Functionality" tells you nothing); the scope paragraph
  states the actual testable behavior.
- ≤40 lines of context — **this cap is rigid.** Titles + WHAT + **bar**
  only — no HTML, no logs. If a feature's hierarchy cannot fit in
  40 lines, that is diagnostic: the feature has grab-bag TCDs.
  **Overflow response: run T2 on the oversized TCD to decompose it,
  then re-pack.** Do not raise the cap.
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

> Use when: a TCD title is vague, two TCDs seem to overlap, a grab-bag
> TCD exceeds the Step 1a 40-line cap, or after adding new scenarios and
> wondering whether they need their own TCD.

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

Then propose a target hierarchy: if any TCD should be split, merged, or
a new TCD created, show the end-state TCD list with bars.

Answer with two tables:

**Table 1 — Diagnosis** (one row per existing TCD):
| TCD ID | Spec clause(s) backing its WHAT | Clubs multiple behaviors? (yes: list them / no) | Overlap with other TCD? (TCD ID or "none") |

**Table 2 — Target hierarchy proposal** (one row per recommended TCD in the target state):
| TCD (existing ID or NEW) | WHAT (one sentence) | Spec clause | Bar sketch (measurable, spec-cited) | Action (keep / split-from [ID] / merge-into [ID] / new) |

Hard rule: every NEW row in Table 2 MUST include a spec-cited bar sketch.
A proposed TCD without a measurable bar is over-provisioning — omit it.

No prose outside the tables except a ≤3-line summary at the top.
Use our exact TCD IDs when referring to existing artifacts.
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

### T7: Model / environment coverage check

> Use when: the TCD skill's Step 2.7 gate emits TBD-T7 cells — i.e. the
> environment verdict depends on whether the Simics/VP model or HSLE
> environment actually implements a behavior. Uses the **standard
> Step 1b** silicon routing context (unlike T6): model questions are
> NWP/DMR-scoped by nature.

Context pack addition: include the scenario list with each scenario's
Q1–Q3 verdicts and the specific behavior in question, e.g.:

```
Pending Q4 checks (feature: PCT):
- S3 "Thermal-throttle entry": needs temp-sensor injection + PROCHOT
  response. Q1=arch-visible, Q2=needs injection, Q3=no.
- S5 "Ordered throttle phase B→C": needs observation of phase
  transition ordering. Q1=arch-visible?, Q3=relative ordering.
```

Prompt body:

```
For the NWP Simics/VP model and HSLE emulation environment in your
resources: for each scenario listed, does the environment implement the
behavior required?
1. Is the behavior modeled functionally (reads/writes take effect,
   state machines transition)?
2. What injection knobs exist for the HW-side inputs named (temp,
   telemetry, fuses)? Name the knob or interface.
3. For unmodeled behaviors: does the model return defaults/stubs
   (silent) or error (loud)? This decides whether a test would
   false-pass.
4. Cite the model documentation or release notes per answer.
```

**T7 output contract** (replaces the standard Step 3 table):

```
Answer as a markdown table:
| Scenario | Environment | Modeled? (Full/Partial/None) | Injection knob (name or none) | Failure mode if unmodeled (silent-default / error) | Doc ref (verbatim) |
One row per scenario×environment asked. Unknown = `no doc access`, not
a guess. ≤3-line summary.
```

### T8: Microarch-completeness audit

> Use when: the TPF §2 Microarch→Scenario Coverage Matrix is populated
> and you want to validate completeness against spec ground truth.
> This is the bidirectional check: (1) do all microarch elements have
> a covering TCD? (2) do all TCDs trace to a documented microarch element?
> Uses the **standard Step 1b** silicon routing context.

**Context pack:** Paste the full Microarch→Scenario Coverage Matrix from
TPF §2 as-is, plus a compact list of all TCDs under the TPF with their
one-line WHAT.

```
I am a validation engineer working on NWP PM test planning.
The TPF microarch details are my oracle for scenario completeness.
Below is the Microarch→Scenario Coverage Matrix from TPF [ID] §2,
followed by all TCDs under this TPF.

[PASTE SILICON ROUTING CONTEXT — Step 1b]

=== MICROARCH→SCENARIO COVERAGE MATRIX (from TPF §2) ===

[PASTE MATRIX TABLE — all rows including GAP rows]

=== TCDs UNDER THIS TPF ===

[PASTE TCD LIST — ID, title, one-line WHAT, TC count]

Please perform a bidirectional completeness audit against the
[FEATURE] HAS/MAS in your resources:

**Direction 1 — Elements → WHATs (coverage gaps):**
For each microarch element in the matrix, does the HAS/MAS define
additional validation-relevant behaviors NOT captured by any row?
List any missing elements that should be in the matrix but aren't.

**Direction 2 — TCDs → Elements (scope creep check):**
For each TCD listed, does its WHAT trace to a documented HAS/MAS
behavior? Flag any TCD whose WHAT has no spec basis.

**Direction 3 — Bar validation (free ride):**
For each non-GAP row, is the implied WHAT consistent with the spec
behavior? Flag any row where the WHAT mischaracterizes the spec.
```

**T8 output contract** (replaces the standard Step 3 table):

```
Answer with three tables:

**Table 1 — Missing microarch elements** (elements in HAS/MAS not in the matrix):
| Element | Category (FSM/Register/Interface/Fuse/Error/Counter) | Implied WHAT | Spec ref (HAS/MAS clause) | Risk (H/M/L) |

**Table 2 — Unanchored TCDs** (TCDs with no spec-traced microarch element):
| TCD ID | WHAT | Finding (no spec basis / spec basis found but missing from matrix) |

**Table 3 — WHAT mischaracterizations** (rows where implied WHAT diverges from spec):
| Matrix row # | Current implied WHAT | Correct WHAT per spec | Spec ref |

If all three tables are empty, state: "Matrix is complete against
accessible HAS/MAS." No prose outside the tables except a ≤3-line
summary at the top. Use exact matrix row numbers and TCD IDs.
```

**T8 ingest rules:**
- **Table 1 rows (missing elements):** Add each to the TPF §2 matrix
  with Status = `⚠️ GAP` and the spec ref in a new column. Each GAP
  row is a candidate for a new TCD — but only scaffold if a spec-cited
  bar can be derived (same hard rule as T1/T2 NEW rows).
- **Table 2 rows (unanchored TCDs):** Two sub-cases:
  - `no spec basis`: Challenge the TCD — it may be scope creep, or
    the spec may have a clause Co-Design couldn't access. Check local
    KB before removing.
  - `spec basis found but missing from matrix`: Add the missing element
    to the matrix. The TCD is valid; the microarch doc was incomplete.
- **Table 3 rows (mischaracterizations):** Update the matrix row's
  "Implied WHAT" to match the spec-corrected version. If the correction
  changes the WHAT enough to affect the TCD's §5 bar, flag a bar
  change for that TCD.
- Same push gate as all templates: nothing writes to HSD without
  human confirmation.

---

## Step 3 — Append the default output contract

> **T2 and T7 define their own output contracts inline.** This default
> contract applies to T1, T3, T4, T5, and T6.

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

**T2 ingest rules (Table 2 — Target hierarchy proposal):**
- Table 2 is a **proposal**, not a directive. Each row passes the local
  WHAT-boundary check before execution. Co-Design is authoritative for
  spec; it is never authoritative for test plan structure.
- `keep` rows: no action — they confirm the TCD is well-scoped.
- `split-from [ID]` rows: validate that the split produces TCDs with
  genuinely different bars. If bars converge, reject the split.
- `new` rows: **must carry a spec-cited bar sketch** (hard rule from the
  prompt contract). A NEW row without a bar is discarded — it is exactly
  the over-provisioning the event-driven-creation rule exists to prevent.
  If the bar is present and passes WHAT-boundary check, scaffold via
  `nwp-tcd-description`.
- `merge-into [ID]` rows: verify the surviving TCD's bar subsumes both
  original bars. Update §5 bar + §6 coverage map in the surviving TCD.

**T7 ingest rules:**
- Each row resolves a TBD-T7 cell in the owning TCD's §6 Env column:
  Modeled=Full → Full; Partial → Partial with the named knob in the
  blocker note; None → None, floor rises per the Step 2.7 rubric.
- **Silent-default rows are safety findings**, not just feasibility
  data: a scenario that would false-pass on an unmodeled path gets a
  ⚠ note in §6 ("do not run on Simics — silent false-pass risk") so no
  future session schedules it there by mistake.
- Knob names go into the TC (execution detail, HOW), not the TCD.
- `no doc access` rows stay TBD; escalate to the model team manually —
  do not downgrade to a guess.

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
TCDs (gist from scope paragraph + bar):
- [FV+PSS] TCD 22022420855 "BIOS Enabling" (4 TCs): BIOS Setup interface —
  knob visibility, defaults, CLOS state. Bar: defaults correct; CLOS per partition.
- [FV] TCD 22022420858 "Functionality" (3 TCs): Runtime HP/LP enforcement —
  CLOS ceilings, LP invariant, ordered throttle. Bar: HP at TRL, LP at clip, LP first.
- [PV] TCD 22022420862 "PV BIOS Config" (2 TCs): Partition Count → CLOS from
  Ubuntu. Bar: CLOS = HP/LP split; cpuinfo_max_freq = HWP_CAP.
- [PV] TCD 16031169214 "PV Discovery" (1 TC): OS feature/capability reporting,
  2-CBB topology. Bar: intel-speed-select HP count + APIC IDs correct.
- [PV] TCD 16031169217 "PV BIOS Disable" (1 TC): Partition Count=0 → uniform
  turbo. Bar: cpuinfo_max_freq uniform, no HP/LP.
- [FV+PSS] TCD 16031169297 "TPMI Runtime Control" (4 TCs): Register correctness
  + dynamic enable/disable. Bar: TPMI=fuse; toggle → TRL in 1 slow loop.
- [FV+PSS] TCD 16031169298 "DQ Rules" (2 TCs): FlexconPM assertions, SST_TF_INFO
  per spec after PH5. Bar: assertions pass; SST-PP×PCT exclusion enforced.
- [FV] TCD 16031169308 "Negative / Boundary" (2 TCs): Invalid configs rejected.
  Bar: inputs rejected; CLOS not corrupted; no MCA.
- [FV+PSS] TCD 16031169309 "PCT × C-states" (2 TCs): All HP in C6 → LP clipped.
  Bar: LP at LP_CLIP_RATIO when all HP idle.
- [FV] TCD 16031169310 "Error Injection" (1 TC): SST-CP error + EXCURSION_TO_MIN.
  Bar: ERROR_TYPE correct; excursion handshake completes.
- [FV] TCD 16031169419 "PCT × RAPL × C-states × thermal" (TC TBD): Ordered
  throttle coherent under RAPL+C-state+thermal. Bar: LP first; assignments stable.
- [FV] TCD 16031169376 "PCT × Thermal" (TC TBD): Phase C HP throttle escalation.
  Bar: HP throttled only after LP at minimum.
NOTE: DLCP has its own TPF 16031169314. Cross-product TCDs live under PCT TPF
(PCT's bar is being tested); Cross Product TP is for multi-feature, no primary.

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
Use our exact TC/TCD IDs (e.g. TCD 22022420862, TC 16030717717) when referring
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
| Inferring model coverage from the arch spec | Spec presence ≠ model coverage; only model docs/release notes count |
| Treating silent-default behaviors as merely "None" | They are false-pass hazards — flag with ⚠ in §6, not just a None cell |
| Copying injection knob names into the TCD | Knobs are execution detail → TC only; TCD keeps Full/Partial/None + blocker clause |
| Cross-product TCD filed under wrong TP | Interaction TCDs live under the primary feature's TPF (the one whose bar is tested); Cross Product TP is for multi-feature scenarios with no single primary |
